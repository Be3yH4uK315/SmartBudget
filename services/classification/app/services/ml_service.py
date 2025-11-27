import logging
import joblib
import re
from datetime import datetime
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from lightgbm import LGBMClassifier
from app.settings import settings
from aiocache import cached

logger = logging.getLogger(__name__)

MODEL_FILE_NAME = "lgbm_model.pkl"
VECTORIZER_FILE_NAME = "tfidf_vectorizer.pkl"

def _preprocess_text(text: str) -> str:
    """Очистка текста для TF-IDF."""
    if not text or pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def _create_features_from_dict(data: dict) -> str:
    """Собирает все текстовые поля в одну строку для TF-IDF."""
    merchant = data.get('merchant', '') if not pd.isna(data.get('merchant')) else ''
    description = data.get('description', '') if not pd.isna(data.get('description')) else ''
    mcc = data.get('mcc')
    mcc_str = f"mcc_{mcc}" if mcc and not pd.isna(mcc) else ""
    
    return _preprocess_text(f"{merchant} {description} {mcc_str}")

class MLService:
    """
    Управляет обучением, сохранением и загрузкой ML-моделей.
    """

    @staticmethod
    def train_model(training_df: pd.DataFrame) -> tuple[str, dict]:
        """
        Обучает новую модель на данных обратной связи.
        """
        logger.info(f"Starting training on {len(training_df)} items from DataFrame...")
        
        df = training_df 
        
        df.fillna({'merchant': '', 'description': '', 'mcc': 0}, inplace=True)
        
        unique_classes = df['label'].nunique()
        min_classes = 2
        if unique_classes < min_classes:
            logger.error(f"Insufficient unique classes for training ({unique_classes} < {min_classes}). Aborting.")
            raise ValueError("Insufficient unique classes")

        df['features'] = df.apply(lambda row: _create_features_from_dict(row.to_dict()), axis=1)
        X = df['features']
        y = df['label']

        if len(df) < 10: 
            logger.warning("Small dataset; skipping split, metrics on train only.")
            X_train, y_train = X, y
            X_val, y_val = [], []
        else:
            X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

        vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        X_train_tfidf = vectorizer.fit_transform(X_train)
        
        model = LGBMClassifier(
            n_estimators=100,
            learning_rate=0.1,
            objective='multiclass',
            n_jobs=-1
        )
        model.fit(X_train_tfidf, y_train)

        metrics = {"dataset_size": len(df), "unique_classes": unique_classes}
        
        y_train_pred = model.predict(X_train_tfidf)
        metrics["train_accuracy"] = accuracy_score(y_train, y_train_pred)
        metrics["train_f1"] = f1_score(y_train, y_train_pred, average='macro')
        
        if len(X_val) > 0:
            X_val_tfidf = vectorizer.transform(X_val)
            y_val_pred = model.predict(X_val_tfidf)
            metrics["val_accuracy"] = accuracy_score(y_val, y_val_pred)
            metrics["val_f1"] = f1_score(y_val, y_val_pred, average='macro')
            logger.info(f"Training complete. Val accuracy: {metrics['val_accuracy']:.4f}, Val F1: {metrics['val_f1']:.4f}")
        else:
            logger.info(f"Training complete. Train accuracy: {metrics['train_accuracy']:.4f}, Train F1: {metrics['train_f1']:.4f}")

        new_version = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = f"{settings.model_path}/{new_version}_{MODEL_FILE_NAME}"
        vectorizer_path = f"{settings.model_path}/{new_version}_{VECTORIZER_FILE_NAME}"
        
        joblib.dump(model, model_path)
        joblib.dump(vectorizer, vectorizer_path)
        
        logger.info(f"Saved model to {model_path}")
        logger.info(f"Saved vectorizer to {vectorizer_path}")

        return new_version, metrics

    @staticmethod
    @cached(ttl=3600, key_builder=lambda model_version: f"ml_pipeline_{model_version}")
    async def load_prediction_pipeline(model_version: str):
        """
        Загружает конкретную версию модели и векторизатора.
        """
        logger.info(f"Cache MISS: Loading ML pipeline version {model_version}...")
        try:
            model_path = f"{settings.model_path}/{model_version}_{MODEL_FILE_NAME}"
            vectorizer_path = f"{settings.model_path}/{model_version}_{VECTORIZER_FILE_NAME}"

            model = joblib.load(model_path)
            vectorizer = joblib.load(vectorizer_path)
            
            class_labels = model.classes_
            
            logger.info(f"Successfully loaded model pipeline version: {model_version}")
            return model, vectorizer, class_labels
        except FileNotFoundError:
            logger.error(f"Failed to load model pipeline version: {model_version}. Files not found.")
            return None, None, None
        except Exception as e:
            logger.error(f"Error loading model pipeline: {e}")
            return None, None, None

    @staticmethod
    def predict(model, vectorizer, class_labels, transaction_data: dict) -> tuple[str | None, float]:
        """
        Делает предсказание для одной транзакции.
        """
        if not model or not vectorizer:
            return None, 0.0
            
        features_str = _create_features_from_dict(transaction_data)
        
        X_tfidf = vectorizer.transform([features_str])
        
        probas = model.predict_proba(X_tfidf)[0]
        
        best_proba_index = probas.argmax()
        confidence = float(probas[best_proba_index])
        
        category_id = str(class_labels[best_proba_index])
        
        return category_id, confidence