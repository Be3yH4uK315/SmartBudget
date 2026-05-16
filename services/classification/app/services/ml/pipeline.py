import asyncio
import gc
import json
import logging
import os
import re
import warnings
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from typing import Any

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

from app.core.config import settings

logger = logging.getLogger(__name__)

MODEL_FILE_NAME = "lgbm_model.pkl"
VECTORIZER_FILE_NAME = "tfidf_vectorizer.pkl"
METADATA_FILE_NAME = "metadata.json"

UNCATEGORIZED_CATEGORY_ID = 1
MIN_UNIQUE_CLASSES = 2
MIN_SAMPLES_PER_CLASS_FOR_SPLIT = 2
VALIDATION_TEST_SIZE = 0.2
RANDOM_STATE = 42
PREPROCESSING_VERSION = "tfidf_text_v1"

TFIDF_MAX_FEATURES = 10_000
TFIDF_NGRAM_RANGE = (1, 2)
TFIDF_MIN_DF = 2

LGBM_N_ESTIMATORS = 150
LGBM_LEARNING_RATE = 0.05
LGBM_NUM_LEAVES = 31
LGBM_MIN_CHILD_SAMPLES = 1
LGBM_MIN_DATA_IN_BIN = 1

FEATURE_CONFIG = {
    "text_fields": ["merchant", "description"],
    "categorical_tokens": ["mcc", "transaction_type"],
    "excluded_fields": ["amount", "user_id", "date"],
}


def _safe_text(value: Any) -> str:
    """Возвращает безопасное строковое представление скалярного признака."""
    if value is None or pd.isna(value):
        return ""

    return str(value)


def _preprocess_text(text: str) -> str:
    """Очищает текст перед TF-IDF."""
    if not text:
        return ""

    normalized = str(text).casefold().replace("ё", "е")
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized.strip()


def _create_features(data: dict[str, Any]) -> str:
    """Собирает ML-признаки транзакции в стабильную строку для TF-IDF."""
    merchant = _safe_text(data.get("merchant"))
    description = _safe_text(data.get("description"))
    mcc = data.get("mcc")
    transaction_type = _safe_text(data.get("transaction_type"))

    mcc_text = f"mcc_{mcc}" if mcc and not pd.isna(mcc) else ""
    transaction_type_text = f"type_{transaction_type}" if transaction_type else ""

    return _preprocess_text(
        f"{merchant} {description} {mcc_text} {transaction_type_text}",
    )


def _class_distribution(labels: pd.Series) -> dict[str, int]:
    """Возвращает распределение классов в json-friendly формате."""
    return {
        str(int(class_id)): int(count)
        for class_id, count in labels.value_counts().sort_index().items()
    }


def _prepare_training_frame(df: pd.DataFrame) -> tuple[pd.DataFrame | None, dict]:
    """Валидирует и фильтрует обучающий набор перед split."""
    if "label" not in df.columns:
        return None, {"error": "Training data must contain label column"}

    df = df.copy()
    df["label"] = df["label"].astype(int)

    initial_distribution = _class_distribution(df["label"])
    excluded_other_count = int((df["label"] == UNCATEGORIZED_CATEGORY_ID).sum())
    df = df[df["label"] != UNCATEGORIZED_CATEGORY_ID].copy()

    if df.empty:
        return None, {
            "error": "No training rows after excluding uncategorized category",
            "initial_class_distribution": initial_distribution,
            "excluded_categories": {
                str(UNCATEGORIZED_CATEGORY_ID): excluded_other_count,
            },
        }

    counts = df["label"].value_counts().sort_index()
    underrepresented = {
        str(int(class_id)): int(count)
        for class_id, count in counts.items()
        if count < MIN_SAMPLES_PER_CLASS_FOR_SPLIT
    }

    if underrepresented:
        df = df[~df["label"].isin({int(class_id) for class_id in underrepresented})]

    final_distribution = _class_distribution(df["label"]) if not df.empty else {}
    unique_classes = len(final_distribution)
    validation_rows = max(
        int(np.ceil(len(df) * VALIDATION_TEST_SIZE)),
        unique_classes,
    )

    validation = {
        "initial_class_distribution": initial_distribution,
        "class_distribution": final_distribution,
        "excluded_categories": {
            str(UNCATEGORIZED_CATEGORY_ID): excluded_other_count,
        },
        "underrepresented_classes": underrepresented,
        "training_rows_after_filter": int(len(df)),
        "unique_classes_after_filter": unique_classes,
        "validation_rows": int(validation_rows),
    }

    if unique_classes < MIN_UNIQUE_CLASSES:
        return None, {
            **validation,
            "error": "Insufficient unique classes after filtering",
        }

    if len(df) - validation_rows < unique_classes:
        return None, {
            **validation,
            "error": "Insufficient rows for stratified train/validation split",
        }

    return df, validation


def _artifact_path(version: str, file_name: str) -> str:
    """Возвращает путь к артефакту версии модели."""
    return f"{settings.ML.MODEL_PATH}/{version}_{file_name}"


def _dump_joblib_atomic(value: Any, path: str) -> None:
    """Записывает joblib artifact через временный файл."""
    tmp_path = f"{path}.tmp"
    joblib.dump(value, tmp_path)
    os.replace(tmp_path, path)


def _dump_json_atomic(value: dict[str, Any], path: str) -> None:
    """Записывает json artifact через временный файл."""
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp_path, path)


def _load_metadata_sync(version: str) -> dict[str, Any]:
    """Загружает и валидирует metadata artifact."""
    metadata_path = _artifact_path(version, METADATA_FILE_NAME)
    with open(metadata_path, encoding="utf-8") as file:
        metadata = json.load(file)

    required_fields = {
        "model_version",
        "labels",
        "metrics",
        "threshold_accept",
        "feature_config",
        "preprocessing_version",
    }
    missing_fields = sorted(required_fields - metadata.keys())
    if missing_fields:
        raise ValueError(
            f"Metadata for model {version} is missing fields: {missing_fields}",
        )

    if metadata["model_version"] != version:
        raise ValueError(
            f"Metadata version mismatch: {metadata['model_version']} != {version}",
        )

    if not isinstance(metadata["labels"], list) or not metadata["labels"]:
        raise ValueError(f"Metadata for model {version} has empty labels")

    metadata["labels"] = [int(label) for label in metadata["labels"]]

    return metadata


def _train_internal_process(df_dict: dict[str, list[Any]]) -> tuple[str | None, dict]:
    """Обучает модель в отдельном процессе."""
    try:
        df = pd.DataFrame(df_dict)
        for column, default_value in {
            "merchant": "",
            "description": "",
            "transaction_type": "",
            "mcc": 0,
        }.items():
            if column not in df.columns:
                df[column] = default_value

        df.fillna(
            {
                "merchant": "",
                "description": "",
                "transaction_type": "",
                "mcc": 0,
            },
            inplace=True,
        )

        training_df, validation_metrics = _prepare_training_frame(df)
        if training_df is None:
            return None, validation_metrics

        features = training_df.apply(
            lambda row: _create_features(row.to_dict()),
            axis=1,
        )
        labels = training_df["label"].astype(int)

        unique_classes = labels.nunique()
        validation_rows = validation_metrics["validation_rows"]
        test_size = validation_rows / len(labels)

        train_features, val_features, train_labels, val_labels = train_test_split(
            features,
            labels,
            test_size=test_size,
            stratify=labels,
            random_state=RANDOM_STATE,
        )

        min_df = min(TFIDF_MIN_DF, max(1, len(train_features) // 2))
        vectorizer = TfidfVectorizer(
            max_features=TFIDF_MAX_FEATURES,
            ngram_range=TFIDF_NGRAM_RANGE,
            min_df=min_df,
        )
        train_vectors = vectorizer.fit_transform(train_features)
        val_vectors = vectorizer.transform(val_features)

        model = LGBMClassifier(
            n_estimators=LGBM_N_ESTIMATORS,
            learning_rate=LGBM_LEARNING_RATE,
            num_leaves=min(LGBM_NUM_LEAVES, max(2, len(train_labels) // 2)),
            min_child_samples=LGBM_MIN_CHILD_SAMPLES,
            min_data_in_bin=LGBM_MIN_DATA_IN_BIN,
            objective="multiclass",
            n_jobs=1,
            verbose=-1,
            class_weight="balanced",
        )
        model.fit(train_vectors, train_labels)

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="X does not have valid feature names",
                category=UserWarning,
            )
            val_predictions = model.predict(val_vectors)
        report = classification_report(
            val_labels,
            val_predictions,
            output_dict=True,
            zero_division=0,
        )

        metrics = {
            **validation_metrics,
            "dataset_size": len(training_df),
            "unique_classes": int(unique_classes),
            "val_accuracy": float(accuracy_score(val_labels, val_predictions)),
            "val_f1_macro": float(
                f1_score(val_labels, val_predictions, average="macro"),
            ),
            "val_f1_weighted": float(
                f1_score(val_labels, val_predictions, average="weighted"),
            ),
            "per_class_metrics": {
                class_name: values
                for class_name, values in report.items()
                if str(class_name).isdigit()
            },
        }

        new_version = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(settings.ML.MODEL_PATH, exist_ok=True)

        model_path = _artifact_path(new_version, MODEL_FILE_NAME)
        vectorizer_path = _artifact_path(new_version, VECTORIZER_FILE_NAME)
        metadata_path = _artifact_path(new_version, METADATA_FILE_NAME)
        metadata = {
            "model_version": new_version,
            "labels": [int(label) for label in model.classes_],
            "threshold_accept": settings.ML.ML_CONFIDENCE_THRESHOLD_ACCEPT,
            "metrics": metrics,
            "trained_at": datetime.now().isoformat(),
            "trained_by": "classification_arq",
            "feature_config": FEATURE_CONFIG,
            "preprocessing_version": PREPROCESSING_VERSION,
            "excluded_categories": [UNCATEGORIZED_CATEGORY_ID],
        }

        _dump_joblib_atomic(model, model_path)
        _dump_joblib_atomic(vectorizer, vectorizer_path)
        _dump_json_atomic(metadata, metadata_path)

        del df, training_df, train_vectors, val_vectors, model, vectorizer
        gc.collect()

        return new_version, metrics

    except Exception as exc:
        return None, {"error": str(exc)}


class MLPipeline:
    """ML pipeline для обучения и применения модели классификации."""

    @staticmethod
    async def train_model(training_df: pd.DataFrame) -> tuple[str, dict]:
        """Обучает модель асинхронно через отдельный процесс."""
        loop = asyncio.get_running_loop()
        df_data = training_df.to_dict(orient="list")

        with ProcessPoolExecutor(max_workers=1) as pool:
            version, metrics = await loop.run_in_executor(
                pool,
                _train_internal_process,
                df_data,
            )

        if version is None:
            raise ValueError(metrics.get("error"))

        return version, metrics

    @staticmethod
    def load_model_sync(version: str):
        """Синхронно загружает модель, vectorizer и metadata с диска."""
        try:
            model_path = _artifact_path(version, MODEL_FILE_NAME)
            vectorizer_path = _artifact_path(version, VECTORIZER_FILE_NAME)

            metadata = _load_metadata_sync(version)
            model = joblib.load(model_path)
            vectorizer = joblib.load(vectorizer_path)
            labels = metadata["labels"] or (
                list(model.classes_) if hasattr(model, "classes_") else []
            )

            gc.collect()

            return model, vectorizer, labels, metadata

        except Exception as exc:
            logger.error(
                "Model load error for version %s: %s",
                version,
                exc,
                exc_info=True,
            )
            return None, None, None, None

    @staticmethod
    def validate_artifacts_sync(version: str) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Проверяет наличие model/vectorizer/metadata artifacts без загрузки модели."""
        artifact_paths = {
            "model": _artifact_path(version, MODEL_FILE_NAME),
            "vectorizer": _artifact_path(version, VECTORIZER_FILE_NAME),
            "metadata": _artifact_path(version, METADATA_FILE_NAME),
        }

        missing = [
            artifact_name
            for artifact_name, artifact_path in artifact_paths.items()
            if not os.path.exists(artifact_path)
        ]
        if missing:
            return False, f"Missing artifacts for model {version}: {missing}", None

        try:
            metadata = _load_metadata_sync(version)
        except Exception as exc:
            return False, f"Invalid metadata for model {version}: {exc}", None

        return True, None, metadata

    @staticmethod
    async def predict_async(
        model,
        vectorizer,
        class_labels: list[int],
        data: dict[str, Any],
    ) -> tuple[int, float]:
        """Асинхронно предсказывает категорию и confidence."""
        if not model:
            return 0, 0.0

        def predict() -> tuple[int, float]:
            text = _create_features(data)
            features = vectorizer.transform([text])
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message="X does not have valid feature names",
                    category=UserWarning,
                )
                probabilities = model.predict_proba(features)[0]

            predicted_index = int(np.argmax(probabilities))
            confidence = float(probabilities[predicted_index])
            label = (
                class_labels[predicted_index]
                if class_labels and predicted_index < len(class_labels)
                else predicted_index
            )

            return int(label), confidence

        loop = asyncio.get_running_loop()

        return await loop.run_in_executor(None, predict)
