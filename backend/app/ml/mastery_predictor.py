"""
Student Topic Mastery and Risk Predictor.
Uses Scikit-learn to classify topic mastery (Strong vs At-Risk) based on multi-dimensional
performance features. Adheres strictly to scientific validation, preventing data leakage
and transparently signaling data sufficiency thresholds.
"""
import logging
from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.model_storage import ModelStorage
from app.ml.performance_analyzer import PerformanceAnalyzer

logger = logging.getLogger(__name__)

# Minimum number of topic performance observations required to train a reliable model
MIN_OBSERVATIONS_FOR_TRAINING = 8

FEATURE_COLUMNS = [
    "total_questions",
    "avg_score",
    "avg_correctness",
    "avg_completeness",
    "avg_conceptual",
    "avg_reasoning",
    "avg_application",
    "avg_time_seconds",
    "easy_ratio",
    "hard_ratio",
    "correct_ratio",
    "incorrect_ratio",
    "missing_concepts_count",
]


class MasteryPredictor:
    """
    Trains and executes a supervised Scikit-learn model to predict topic mastery
    and identify academic areas at risk of failure.
    """

    def __init__(self, storage: Optional[ModelStorage] = None):
        self.storage = storage or ModelStorage()
        self.pipeline: Optional[Pipeline] = None
        self.metrics: dict[str, Any] = {}
        self.is_trained: bool = False
        self._load_existing_model()

    def _load_existing_model(self) -> None:
        """Attempts to load a previously persisted model artifact."""
        model, meta = self.storage.load_model("mastery_predictor")
        if model is not None and meta is not None:
            self.pipeline = model
            self.metrics = meta.get("metadata", {}).get("metrics", {})
            self.is_trained = True
            logger.info("Loaded persisted MasteryPredictor model from storage.")

    def evaluate_training_feasibility(self, topic_aggregates_df: pd.DataFrame) -> dict[str, Any]:
        """
        Validates whether sufficient real data exists to train without overfitting or leakage.
        """
        total_samples = len(topic_aggregates_df)
        if total_samples < MIN_OBSERVATIONS_FOR_TRAINING:
            return {
                "feasible": False,
                "current_samples": total_samples,
                "required_samples": MIN_OBSERVATIONS_FOR_TRAINING,
                "reason": (
                    f"Insufficient historical performance records ({total_samples}/{MIN_OBSERVATIONS_FOR_TRAINING} required). "
                    "Complete more examinations across topics to calibrate the predictive ML model."
                ),
            }

        # Check class balance
        y = topic_aggregates_df["is_mastered"]
        unique_classes = y.nunique()
        if unique_classes < 2:
            return {
                "feasible": False,
                "current_samples": total_samples,
                "required_samples": MIN_OBSERVATIONS_FOR_TRAINING,
                "reason": (
                    "Single-class distribution detected (all topics currently evaluated as either all mastered "
                    "or all needing reinforcement). Requires varied performance history to learn decision boundary."
                ),
            }

        return {
            "feasible": True,
            "current_samples": total_samples,
            "required_samples": MIN_OBSERVATIONS_FOR_TRAINING,
            "reason": "Sufficient real examination data available for training and validation.",
        }

    def train(self, topic_aggregates_df: pd.DataFrame) -> dict[str, Any]:
        """
        Trains a Random Forest classifier with standard scaling on actual performance features.
        Evaluates on a held-out test split and saves the model artifact.
        """
        feasibility = self.evaluate_training_feasibility(topic_aggregates_df)
        if not feasibility["feasible"]:
            return {
                "success": False,
                "message": feasibility["reason"],
                "metrics": None,
            }

        X = topic_aggregates_df[FEATURE_COLUMNS]
        y = topic_aggregates_df["is_mastered"]

        # Stratified split when possible, otherwise standard random split
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.25, random_state=42, stratify=y
            )
        except ValueError:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.25, random_state=42
            )

        # Pipeline with Scaler + Random Forest
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", RandomForestClassifier(
                n_estimators=50,
                max_depth=4,
                min_samples_split=2,
                random_state=42,
            )),
        ])

        pipeline.fit(X_train, y_train)

        # Evaluate on unseen test data
        y_pred = pipeline.predict(X_test)
        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))

        metrics = {
            "test_accuracy": round(acc, 3),
            "precision": round(prec, 3),
            "recall": round(rec, 3),
            "f1_score": round(f1, 3),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "features_used": FEATURE_COLUMNS,
        }

        # Feature importances
        rf_model = pipeline.named_steps["classifier"]
        importances = dict(zip(FEATURE_COLUMNS, [round(float(v), 4) for v in rf_model.feature_importances_]))
        metrics["feature_importances"] = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))

        self.pipeline = pipeline
        self.metrics = metrics
        self.is_trained = True

        # Persist to disk
        self.storage.save_model("mastery_predictor", pipeline, metadata={"metrics": metrics})

        return {
            "success": True,
            "message": "Model successfully trained and validated on real examination records.",
            "metrics": metrics,
        }

    def predict_topic_risk(self, topic_feature_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Predicts mastery status and risk probability for a single topic feature vector.
        """
        if not self.is_trained or self.pipeline is None:
            return {
                "is_predictable": False,
                "reason": "Model is not yet trained. Train the model or accumulate examination records first.",
            }

        # Construct single-row DataFrame
        input_data = {col: [topic_feature_dict.get(col, 0.0)] for col in FEATURE_COLUMNS}
        df_input = pd.DataFrame(input_data)

        prediction = int(self.pipeline.predict(df_input)[0])
        probabilities = self.pipeline.predict_proba(df_input)[0]

        # probability of class 0 (At Risk) vs class 1 (Mastered)
        risk_probability = float(probabilities[0])
        mastery_probability = float(probabilities[1]) if len(probabilities) > 1 else float(1.0 - risk_probability)

        return {
            "is_predictable": True,
            "prediction": "MASTERED" if prediction == 1 else "AT_RISK",
            "risk_probability": round(risk_probability, 3),
            "mastery_probability": round(mastery_probability, 3),
            "needs_reinforcement": prediction == 0,
        }
