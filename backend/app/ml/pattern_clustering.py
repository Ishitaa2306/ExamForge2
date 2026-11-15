"""
Student Learning Pattern Clusterer.
Applies unsupervised machine learning (K-Means Clustering) via Scikit-learn
to identify distinct cognitive learning patterns and examination tendencies from
Granite's 5-criterion semantic evaluation scores.
"""
import logging
from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

MIN_ANSWERS_FOR_CLUSTERING = 5

CRITERIA_FEATURES = [
    "correctness_score",
    "completeness_score",
    "conceptual_score",
    "reasoning_score",
    "application_score",
]


class LearningPatternClusterer:
    """
    Groups student answers and topic responses into explainable learning patterns.
    """

    def __init__(self, n_clusters: int = 3):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.kmeans: Optional[KMeans] = None
        self.cluster_profiles: dict[int, dict[str, Any]] = {}
        self.silhouette: Optional[float] = None

    def analyze_patterns(self, answers_df: pd.DataFrame) -> dict[str, Any]:
        """
        Runs clustering on Granite evaluation scores.
        """
        if answers_df.empty or len(answers_df) < MIN_ANSWERS_FOR_CLUSTERING:
            return {
                "feasible": False,
                "current_samples": len(answers_df),
                "required_samples": MIN_ANSWERS_FOR_CLUSTERING,
                "reason": (
                    f"Insufficient answer evaluations ({len(answers_df)}/{MIN_ANSWERS_FOR_CLUSTERING} required). "
                    "Complete more examination questions to identify cognitive learning patterns."
                ),
            }

        X = answers_df[CRITERIA_FEATURES].copy().fillna(0.0)

        # Ensure we do not request more clusters than unique points
        k = min(self.n_clusters, len(X) - 1)
        if k < 2:
            return {
                "feasible": False,
                "current_samples": len(answers_df),
                "required_samples": MIN_ANSWERS_FOR_CLUSTERING,
                "reason": "Not enough variance across answers to form multiple clusters.",
            }

        X_scaled = self.scaler.fit_transform(X)
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        self.kmeans = kmeans

        # Calculate silhouette if possible
        sil = None
        if len(set(labels)) > 1 and len(X) > k:
            try:
                sil = float(silhouette_score(X_scaled, labels))
            except Exception:
                sil = None
        self.silhouette = sil

        # Profile centroids
        centroids = self.scaler.inverse_transform(kmeans.cluster_centers_)
        profiles = {}
        for idx, center in enumerate(centroids):
            center_dict = dict(zip(CRITERIA_FEATURES, [round(float(v), 3) for v in center]))
            
            # Archetype labeling based on criteria weights
            label_name = self._interpret_archetype(center_dict)
            count = int((labels == idx).sum())

            profiles[idx] = {
                "cluster_index": idx,
                "archetype_label": label_name,
                "sample_count": count,
                "percentage": round(count / len(X) * 100, 1),
                "centroid_scores": center_dict,
            }

        self.cluster_profiles = profiles

        # Attach cluster labels to DataFrame copy
        labeled_df = answers_df.copy()
        labeled_df["cluster_index"] = labels
        labeled_df["archetype_label"] = [profiles[lbl]["archetype_label"] for lbl in labels]

        return {
            "feasible": True,
            "clusters_count": k,
            "silhouette_score": round(sil, 3) if sil is not None else None,
            "profiles": profiles,
            "labeled_data": labeled_df,
        }

    @staticmethod
    def _interpret_archetype(scores: dict[str, float]) -> str:
        """
        Provides human-readable, pedagogically sound interpretations of evaluation centroids.
        """
        avg = sum(scores.values()) / len(scores)
        conceptual = scores.get("conceptual_score", 0.0)
        app = scores.get("application_score", 0.0)
        comp = scores.get("completeness_score", 0.0)
        corr = scores.get("correctness_score", 0.0)
        reas = scores.get("reasoning_score", 0.0)

        if avg >= 0.75:
            return "Comprehensive High Performer (Consistent Across Theory & Application)"
        elif conceptual > app + 0.15:
            return "Theory & Definition Focused (Strong Conceptual, Needs Practical Application)"
        elif app > conceptual + 0.15 or reas > comp + 0.15:
            return "Applied Pragmatist (Strong Intuition & Application, Needs Formal Definitions)"
        elif comp < 0.45 or corr < 0.45:
            return "Developing Foundational (Gaps in Core Correctness and Completeness)"
        else:
            return "Balanced Intermediate (Steady Moderate Performance Across Dimensions)"
