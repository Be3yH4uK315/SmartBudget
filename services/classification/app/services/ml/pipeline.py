import logging
import joblib
import re
import asyncio
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from typing import Tuple

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from lightgbm import LGBMClassifier

from app.core.config import settings

logger = logging.getLogger(__name__)

MODEL_FILE_NAME = "lgbm_model.pkl"
VECTORIZER_FILE_NAME = "tfidf_vectorizer.pkl"

def _preprocess_text(text: str) -> str:
    """Очистка текста для TF-IDF."""
    if not text or pd.isna(text): return ""
    text = str(text).lower()
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def _create_features(data: dict) -> str:
    """Собирает все текстовые поля в одну строку для TF-IDF."""
    merchant = data.get('merchant', '') if not pd.isna(data.get('merchant')) else ''
    desc = data.get('description', '') if not pd.isna(data.get('description')) else ''
    mcc = data.get('mcc')
    mcc_str = f"mcc_{mcc}" if mcc and not pd.isna(mcc) else ""
    return _preprocess_text(f"{merchant} {desc} {mcc_str}")

def _train_internal_process(df_dict: dict) -> Tuple[str | None, dict]:
    """Внутренний процесс обучения модели в отдельном процессе."""
    try:
        df = pd.DataFrame(df_dict)
        df.fillna({'merchant': '', 'description': '', 'mcc': 0}, inplace=True)
        uniqueClasses = df['label'].nunique()
        
        if uniqueClasses < 2:
            return None, {"error": "Insufficient unique classes (need at least 2)"}

        if len(df) < 50:
            return None, {"error": "Insufficient data size (< 50 samples). Overfitting risk."}

        df['features'] = df.apply(lambda row: _create_features(row.to_dict()), axis=1)
        X = df['features']
        y = df['label'].astype(int)

        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

        vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        X_train_tfidf = vectorizer.fit_transform(X_train)

        model = LGBMClassifier(n_estimators=100, learning_rate=0.1, objective='multiclass', n_jobs=1, verbose=-1)
        model.fit(X_train_tfidf, y_train)

        metrics = {"dataset_size": len(df), "uniqueClasses": int(uniqueClasses)}
        y_train_pred = model.predict(X_train_tfidf)
        metrics["train_accuracy"] = accuracy_score(y_train, y_train_pred)
        metrics["train_f1"] = f1_score(y_train, y_train_pred, average='macro')
        
        X_val_tfidf = vectorizer.transform(X_val)
        y_val_pred = model.predict(X_val_tfidf)
        metrics["val_accuracy"] = accuracy_score(y_val, y_val_pred)
        metrics["val_f1"] = f1_score(y_val, y_val_pred, average='macro')
        
        new_version = datetime.now().strftime("%Y%m%d_%H%M%S")
        modelPath = f"{settings.ML.MODEL_PATH}/{new_version}_{MODEL_FILE_NAME}"
        vectorizerPath = f"{settings.ML.MODEL_PATH}/{new_version}_{VECTORIZER_FILE_NAME}"

        joblib.dump(model, modelPath)
        joblib.dump(vectorizer, vectorizerPath)
        
        return new_version, metrics
    except Exception as e:
        return None, {"error": str(e)}

class MLPipeline:
    @staticmethod
    async def train_model(training_df: pd.DataFrame) -> Tuple[str, dict]:
        """Асинхронная обертка для обучения модели."""
        loop = asyncio.get_running_loop()
        df_data = training_df.to_dict(orient='list')
        with ProcessPoolExecutor(max_workers=1) as pool:
            result = await loop.run_in_executor(pool, _train_internal_process, df_data)
        
        if result[0] is None:
            raise ValueError(result[1].get("error"))
        return result

    @staticmethod
    def load_model_sync(version: str):
        """Синхронная загрузка модели с диска."""
        try:
            m_path = f"{settings.ML.MODEL_PATH}/{version}_{MODEL_FILE_NAME}"
            v_path = f"{settings.ML.MODEL_PATH}/{version}_{VECTORIZER_FILE_NAME}"
            model = joblib.load(m_path)
            vec = joblib.load(v_path)
            labels = list(range(model.n_classes_)) if hasattr(model, 'n_classes_') else None
            return model, vec, labels
        except Exception as e:
            logger.error(f"Load error {version}: {e}")
            return None, None, None

    @staticmethod
    async def predict_async(model, vectorizer, class_labels, data: dict) -> Tuple[int, float]:
        """Асинхронный прогноз с использованием загруженной модели."""
        if not model: return 0, 0.0
        
        def _predict():
            text = _create_features(data)
            vec = vectorizer.transform([text])
            proba = model.predict_proba(vec)[0]
            pred_idx = np.argmax(proba)
            conf = float(proba[pred_idx])
            label = class_labels[pred_idx] if class_labels else pred_idx
            return int(label), conf

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _predict)