import asyncio
import gc
import logging
import re
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

MIN_UNIQUE_CLASSES = 2
VALIDATION_TEST_SIZE = 0.2
RANDOM_STATE = 42

TFIDF_MAX_FEATURES = 10_000
TFIDF_NGRAM_RANGE = (1, 2)
TFIDF_MIN_DF = 2

LGBM_N_ESTIMATORS = 150
LGBM_LEARNING_RATE = 0.05
LGBM_NUM_LEAVES = 31


def _preprocess_text(text: str) -> str:
    """Очищает текст перед TF-IDF."""
    if not text or pd.isna(text):
        return ""

    normalized = str(text).lower()
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized.strip()


def _create_features(data: dict[str, Any]) -> str:
    """Собирает merchant, description и mcc в одну строку признаков."""
    merchant = data.get("merchant", "")
    description = data.get("description", "")
    mcc = data.get("mcc")

    merchant_text = "" if pd.isna(merchant) else str(merchant)
    description_text = "" if pd.isna(description) else str(description)
    mcc_text = f"mcc_{mcc}" if mcc and not pd.isna(mcc) else ""

    return _preprocess_text(f"{merchant_text} {description_text} {mcc_text}")


def _train_internal_process(df_dict: dict[str, list[Any]]) -> tuple[str | None, dict]:
    """Обучает модель в отдельном процессе."""
    try:
        df = pd.DataFrame(df_dict)
        df.fillna(
            {
                "merchant": "",
                "description": "",
                "mcc": 0,
            },
            inplace=True,
        )

        unique_classes = df["label"].nunique()
        if unique_classes < MIN_UNIQUE_CLASSES:
            return None, {
                "error": "Insufficient unique classes (need at least 2)",
            }

        features = df.apply(
            lambda row: _create_features(row.to_dict()),
            axis=1,
        )
        labels = df["label"].astype(int)

        train_features, val_features, train_labels, val_labels = train_test_split(
            features,
            labels,
            test_size=VALIDATION_TEST_SIZE,
            stratify=labels,
            random_state=RANDOM_STATE,
        )

        vectorizer = TfidfVectorizer(
            max_features=TFIDF_MAX_FEATURES,
            ngram_range=TFIDF_NGRAM_RANGE,
            min_df=TFIDF_MIN_DF,
        )
        train_vectors = vectorizer.fit_transform(train_features)
        val_vectors = vectorizer.transform(val_features)

        model = LGBMClassifier(
            n_estimators=LGBM_N_ESTIMATORS,
            learning_rate=LGBM_LEARNING_RATE,
            num_leaves=LGBM_NUM_LEAVES,
            objective="multiclass",
            n_jobs=1,
            verbose=-1,
            class_weight="balanced",
        )
        model.fit(train_vectors, train_labels)

        val_predictions = model.predict(val_vectors)
        report = classification_report(
            val_labels,
            val_predictions,
            output_dict=True,
            zero_division=0,
        )

        metrics = {
            "dataset_size": len(df),
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
        model_path = f"{settings.ML.MODEL_PATH}/{new_version}_{MODEL_FILE_NAME}"
        vectorizer_path = (
            f"{settings.ML.MODEL_PATH}/{new_version}_{VECTORIZER_FILE_NAME}"
        )

        joblib.dump(model, model_path)
        joblib.dump(vectorizer, vectorizer_path)

        del df, train_vectors, val_vectors, model, vectorizer
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
        """Синхронно загружает модель и vectorizer с диска."""
        try:
            model_path = f"{settings.ML.MODEL_PATH}/{version}_{MODEL_FILE_NAME}"
            vectorizer_path = (
                f"{settings.ML.MODEL_PATH}/{version}_{VECTORIZER_FILE_NAME}"
            )

            model = joblib.load(model_path)
            vectorizer = joblib.load(vectorizer_path)
            labels = list(model.classes_) if hasattr(model, "classes_") else []

            gc.collect()

            return model, vectorizer, labels

        except Exception as exc:
            logger.error(
                "Model load error for version %s: %s",
                version,
                exc,
                exc_info=True,
            )
            return None, None, None

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
