"""
Model Storage — safe persistence and retrieval of trained Scikit-learn models.
"""
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import joblib

logger = logging.getLogger(__name__)

DEFAULT_MODELS_DIR = "storage/models"


class ModelStorage:
    def __init__(self, models_dir: str = DEFAULT_MODELS_DIR):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def save_model(
        self,
        name: str,
        model: Any,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Path:
        """
        Persists a trained model object and its metadata dictionary.
        """
        model_path = self.models_dir / f"{name}.joblib"
        meta_path = self.models_dir / f"{name}_meta.joblib"

        record = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "model_type": type(model).__name__,
            "metadata": metadata or {},
        }

        try:
            joblib.dump(model, model_path)
            joblib.dump(record, meta_path)
            logger.info("Successfully persisted ML model to %s", model_path)
            return model_path
        except Exception as exc:
            logger.error("Failed to save ML model '%s': %s", name, exc)
            raise

    def load_model(self, name: str) -> tuple[Optional[Any], Optional[dict[str, Any]]]:
        """
        Loads a persisted model and its metadata record.
        Returns (None, None) if not found.
        """
        model_path = self.models_dir / f"{name}.joblib"
        meta_path = self.models_dir / f"{name}_meta.joblib"

        if not model_path.is_file():
            return None, None

        try:
            model = joblib.load(model_path)
            meta = joblib.load(meta_path) if meta_path.is_file() else None
            return model, meta
        except Exception as exc:
            logger.warning("Failed to load model '%s': %s", name, exc)
            return None, None

    def model_exists(self, name: str) -> bool:
        return (self.models_dir / f"{name}.joblib").is_file()
