"""
Student Performance Analyzer.
Extracts genuine examination records, evaluation rubrics, and time telemetry
from PostgreSQL / SQLAlchemy to construct analytical datasets and ML feature matrices.
"""
import logging
from collections import Counter
from typing import Any, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.database.models import (
    AnswerEvaluation,
    DifficultyLevel,
    DocumentTopic,
    EvaluationLabel,
    Examination,
    QuestionAsked,
    QuestionCategory,
    StudentAnswer,
    TopicAssessment,
)

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """
    Extracts and transforms actual examination performance data.
    """

    def __init__(self, db: Session):
        self.db = db

    def extract_user_answer_records(self, user_id: int) -> pd.DataFrame:
        """
        Extracts all student answer records and Granite evaluations for a specific user.
        Returns a structured Pandas DataFrame.
        """
        query = (
            self.db.query(
                StudentAnswer.id.label("answer_id"),
                StudentAnswer.examination_id,
                StudentAnswer.submitted_at,
                StudentAnswer.time_taken_seconds,
                QuestionAsked.id.label("question_asked_id"),
                QuestionAsked.topic_id,
                QuestionAsked.category.label("category"),
                QuestionAsked.difficulty.label("difficulty"),
                AnswerEvaluation.evaluation_label.label("evaluation_label"),
                AnswerEvaluation.correctness_score,
                AnswerEvaluation.completeness_score,
                AnswerEvaluation.conceptual_score,
                AnswerEvaluation.reasoning_score,
                AnswerEvaluation.application_score,
                AnswerEvaluation.overall_score,
                AnswerEvaluation.missing_concepts,
                AnswerEvaluation.mistakes_identified,
                DocumentTopic.name.label("topic_name"),
            )
            .join(Examination, StudentAnswer.examination_id == Examination.id)
            .join(QuestionAsked, StudentAnswer.question_asked_id == QuestionAsked.id)
            .outerjoin(AnswerEvaluation, StudentAnswer.id == AnswerEvaluation.student_answer_id)
            .outerjoin(DocumentTopic, QuestionAsked.topic_id == DocumentTopic.id)
            .filter(Examination.user_id == user_id)
            .order_by(StudentAnswer.submitted_at.asc())
        )

        rows = query.all()
        if not rows:
            return pd.DataFrame()

        data = []
        for r in rows:
            eval_lbl = r.evaluation_label.value if hasattr(r.evaluation_label, "value") else str(r.evaluation_label or "")
            cat = r.category.value if hasattr(r.category, "value") else str(r.category or "")
            diff = r.difficulty.value if hasattr(r.difficulty, "value") else str(r.difficulty or "")

            data.append({
                "answer_id": r.answer_id,
                "examination_id": r.examination_id,
                "submitted_at": r.submitted_at,
                "time_taken_seconds": r.time_taken_seconds or 0,
                "question_asked_id": r.question_asked_id,
                "topic_id": r.topic_id,
                "topic_name": r.topic_name or "General / Uncategorized",
                "category": cat,
                "difficulty": diff,
                "evaluation_label": eval_lbl,
                "correctness_score": float(r.correctness_score or 0.0),
                "completeness_score": float(r.completeness_score or 0.0),
                "conceptual_score": float(r.conceptual_score or 0.0),
                "reasoning_score": float(r.reasoning_score or 0.0),
                "application_score": float(r.application_score or 0.0),
                "overall_score": float(r.overall_score or 0.0),
                "missing_concepts": r.missing_concepts or [],
                "mistakes_identified": r.mistakes_identified or [],
            })

        df = pd.DataFrame(data)
        return df

    def compute_topic_aggregates(self, user_id: int) -> pd.DataFrame:
        """
        Aggregates multi-dimensional performance metrics per topic.
        Produces feature vectors for predictive machine learning.
        """
        df = self.extract_user_answer_records(user_id)
        if df.empty:
            return pd.DataFrame()

        records = []
        for (topic_id, topic_name), group in df.groupby(["topic_id", "topic_name"]):
            total_questions = len(group)
            avg_score = float(group["overall_score"].mean())
            std_score = float(group["overall_score"].std()) if total_questions > 1 else 0.0
            avg_correctness = float(group["correctness_score"].mean())
            avg_completeness = float(group["completeness_score"].mean())
            avg_conceptual = float(group["conceptual_score"].mean())
            avg_reasoning = float(group["reasoning_score"].mean())
            avg_application = float(group["application_score"].mean())
            avg_time = float(group["time_taken_seconds"].mean())

            # Difficulty breakdown
            easy_count = int((group["difficulty"] == "EASY").sum())
            med_count = int((group["difficulty"] == "MEDIUM").sum())
            hard_count = int((group["difficulty"] == "HARD").sum())

            # Success ratios
            correct_count = int((group["evaluation_label"] == "CORRECT").sum())
            partial_count = int((group["evaluation_label"] == "PARTIALLY_CORRECT").sum())
            incorrect_count = int(group["evaluation_label"].isin(["INCORRECT", "INCOMPLETE", "UNCLEAR"]).sum())

            # Error metrics
            all_missing = [c for sub in group["missing_concepts"] for c in sub]
            all_mistakes = [m for sub in group["mistakes_identified"] for m in sub]

            # Label for mastery target (1 = High Mastery / 0 = Needs Reinforcement / At Risk)
            # Threshold: >= 0.75 avg score AND <= 20% incorrect
            is_mastered = 1 if (avg_score >= 0.70 and (incorrect_count / total_questions) <= 0.25) else 0

            records.append({
                "topic_id": topic_id,
                "topic_name": topic_name,
                "total_questions": total_questions,
                "avg_score": round(avg_score, 3),
                "std_score": round(std_score, 3),
                "avg_correctness": round(avg_correctness, 3),
                "avg_completeness": round(avg_completeness, 3),
                "avg_conceptual": round(avg_conceptual, 3),
                "avg_reasoning": round(avg_reasoning, 3),
                "avg_application": round(avg_application, 3),
                "avg_time_seconds": round(avg_time, 1),
                "easy_ratio": round(easy_count / total_questions, 2),
                "medium_ratio": round(med_count / total_questions, 2),
                "hard_ratio": round(hard_count / total_questions, 2),
                "correct_ratio": round(correct_count / total_questions, 2),
                "partial_ratio": round(partial_count / total_questions, 2),
                "incorrect_ratio": round(incorrect_count / total_questions, 2),
                "missing_concepts_count": len(all_missing),
                "mistakes_count": len(all_mistakes),
                "is_mastered": is_mastered,
            })

        return pd.DataFrame(records)

    def get_frequent_missing_concepts(self, user_id: int, top_n: int = 10) -> list[tuple[str, int]]:
        """
        Mines the most recurring missing conceptual elements across evaluations.
        """
        df = self.extract_user_answer_records(user_id)
        if df.empty:
            return []

        all_missing = []
        for items in df["missing_concepts"]:
            all_missing.extend(items)

        counts = Counter(all_missing)
        return counts.most_common(top_n)

    def get_category_performance_breakdown(self, user_id: int) -> dict[str, Any]:
        """
        Calculates performance metrics categorized by question type (Conceptual, Definition, Application, etc.).
        """
        df = self.extract_user_answer_records(user_id)
        if df.empty:
            return {}

        breakdown = {}
        for cat, group in df.groupby("category"):
            breakdown[cat] = {
                "count": len(group),
                "avg_score": round(float(group["overall_score"].mean()), 3),
                "correct_pct": round(float((group["evaluation_label"] == "CORRECT").mean() * 100), 1),
                "avg_time_sec": round(float(group["time_taken_seconds"].mean()), 1),
            }
        return breakdown
