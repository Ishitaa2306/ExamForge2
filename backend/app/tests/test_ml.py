"""
Unit and integration tests for the ExamForge Machine Learning module.
Tests data extraction, feature matrix construction, data sufficiency guards,
Scikit-learn model training, test split evaluation, model persistence, and unsupervised clustering.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock

from app.ml.model_storage import ModelStorage
from app.ml.performance_analyzer import PerformanceAnalyzer
from app.ml.mastery_predictor import MasteryPredictor, FEATURE_COLUMNS
from app.ml.pattern_clustering import LearningPatternClusterer, CRITERIA_FEATURES


def test_model_storage_save_load(tmp_path):
    """Verify safe joblib model persistence and loading."""
    storage = ModelStorage(models_dir=str(tmp_path))
    dummy_model = {"weights": [1.0, 2.0], "type": "dummy"}
    metadata = {"metrics": {"accuracy": 0.85}}

    storage.save_model("test_model", dummy_model, metadata=metadata)
    assert storage.model_exists("test_model")

    loaded_model, loaded_meta = storage.load_model("test_model")
    assert loaded_model == dummy_model
    assert loaded_meta["metadata"]["metrics"]["accuracy"] == 0.85


def test_mastery_predictor_insufficient_data():
    """Predictor must refuse to train on insufficient real records."""
    predictor = MasteryPredictor()
    
    # 3 samples (below MIN_OBSERVATIONS_FOR_TRAINING = 8)
    small_df = pd.DataFrame([
        {col: 0.5 for col in FEATURE_COLUMNS} | {"is_mastered": 1},
        {col: 0.3 for col in FEATURE_COLUMNS} | {"is_mastered": 0},
        {col: 0.8 for col in FEATURE_COLUMNS} | {"is_mastered": 1},
    ])

    feasibility = predictor.evaluate_training_feasibility(small_df)
    assert feasibility["feasible"] is False
    assert "Insufficient historical performance records" in feasibility["reason"]

    result = predictor.train(small_df)
    assert result["success"] is False
    assert result["metrics"] is None


def test_mastery_predictor_train_and_predict(tmp_path):
    """Predictor should train with train_test_split and evaluate genuine metrics on sufficient data."""
    storage = ModelStorage(models_dir=str(tmp_path))
    predictor = MasteryPredictor(storage=storage)

    # Construct synthetic feature matrix with distinct classes to test pipeline
    np.random.seed(42)
    records = []
    for i in range(20):
        is_mastered = 1 if i % 2 == 0 else 0
        base_score = 0.85 if is_mastered == 1 else 0.45
        records.append({
            "total_questions": 10 + i,
            "avg_score": base_score + np.random.normal(0, 0.05),
            "avg_correctness": base_score,
            "avg_completeness": base_score,
            "avg_conceptual": base_score,
            "avg_reasoning": base_score,
            "avg_application": base_score,
            "avg_time_seconds": 30.0 + i,
            "easy_ratio": 0.3,
            "hard_ratio": 0.2,
            "correct_ratio": 0.7 if is_mastered else 0.3,
            "incorrect_ratio": 0.1 if is_mastered else 0.5,
            "missing_concepts_count": 1 if is_mastered else 5,
            "is_mastered": is_mastered,
        })
    df = pd.DataFrame(records)

    feasibility = predictor.evaluate_training_feasibility(df)
    assert feasibility["feasible"] is True

    result = predictor.train(df)
    assert result["success"] is True
    assert "test_accuracy" in result["metrics"]
    assert "feature_importances" in result["metrics"]
    assert predictor.is_trained is True

    # Test prediction on high-scoring feature vector
    pred_mastered = predictor.predict_topic_risk({
        "total_questions": 15,
        "avg_score": 0.90,
        "avg_correctness": 0.90,
        "avg_completeness": 0.85,
        "avg_conceptual": 0.90,
        "avg_reasoning": 0.85,
        "avg_application": 0.80,
        "avg_time_seconds": 25.0,
        "easy_ratio": 0.2,
        "hard_ratio": 0.3,
        "correct_ratio": 0.85,
        "incorrect_ratio": 0.05,
        "missing_concepts_count": 0,
    })
    assert pred_mastered["is_predictable"] is True
    assert pred_mastered["prediction"] == "MASTERED"
    assert pred_mastered["needs_reinforcement"] is False


def test_learning_pattern_clustering_insufficient_data():
    """Clusterer must reject clustering when fewer than minimum samples exist."""
    clusterer = LearningPatternClusterer()
    empty_df = pd.DataFrame()
    res = clusterer.analyze_patterns(empty_df)
    assert res["feasible"] is False
    assert "Insufficient answer evaluations" in res["reason"]


def test_learning_pattern_clustering_valid_data():
    """Clusterer should find clusters and assign archetypes when data is sufficient."""
    clusterer = LearningPatternClusterer(n_clusters=2)
    data = []
    # Cluster 1: High performers
    for _ in range(5):
        data.append({
            "correctness_score": 0.9,
            "completeness_score": 0.85,
            "conceptual_score": 0.9,
            "reasoning_score": 0.88,
            "application_score": 0.85,
        })
    # Cluster 2: Developing foundational
    for _ in range(5):
        data.append({
            "correctness_score": 0.3,
            "completeness_score": 0.35,
            "conceptual_score": 0.4,
            "reasoning_score": 0.3,
            "application_score": 0.25,
        })
    df = pd.DataFrame(data)

    res = clusterer.analyze_patterns(df)
    assert res["feasible"] is True
    assert res["clusters_count"] == 2
    assert len(res["profiles"]) == 2
    assert "labeled_data" in res
    assert "archetype_label" in res["labeled_data"].columns
