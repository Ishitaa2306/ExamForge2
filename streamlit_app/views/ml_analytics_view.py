"""
Machine Learning — Student Performance & Learning Pattern Analysis View.
Applies Scikit-learn predictive modeling (MasteryPredictor) and unsupervised
learning (LearningPatternClusterer) to real student examination telemetry.
"""
import streamlit as st
import pandas as pd
import numpy as np

from app.ml.mastery_predictor import MasteryPredictor
from app.ml.pattern_clustering import LearningPatternClusterer
from app.ml.performance_analyzer import PerformanceAnalyzer
from streamlit_app.state import get_current_user_id, get_db_session


def render_ml_analytics_view():
    user_id = get_current_user_id()
    if not user_id:
        st.warning("Please sign in to view machine learning analytics.")
        return

    st.markdown(
        """
        <div>
            <span class="badge badge-terracotta">Scikit-Learn Machine Learning Engine</span>
            <h1 style="font-size: 30px; margin-top: 6px; margin-bottom: 4px;">Student Performance & Learning Pattern Analysis</h1>
            <p style="color: var(--color-warmgray); font-size: 14px;">
                Advanced machine learning models analyzing longitudinal answer telemetry, identifying cognitive archetypes, and predicting curriculum mastery.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    db = get_db_session()
    try:
        analyzer = PerformanceAnalyzer(db)
        answers_df = analyzer.extract_user_answer_records(user_id)
        topic_df = analyzer.compute_topic_aggregates(user_id)
        category_breakdown = analyzer.get_category_performance_breakdown(user_id)
        frequent_missing = analyzer.get_frequent_missing_concepts(user_id, top_n=8)
    finally:
        db.close()

    if answers_df.empty:
        st.info(
            "No historical examination answers recorded yet. "
            "Complete an examination to populate real performance data for machine learning analysis."
        )
        return

    tab_overview, tab_predictor, tab_clusters, tab_gaps = st.tabs([
        "Performance Trends",
        "Mastery Predictor (ML)",
        "Learning Archetypes (Clustering)",
        "Error Pattern Mining",
    ])

    # ── TAB 1: PERFORMANCE TRENDS ─────────────────────────────────────────────
    with tab_overview:
        st.markdown("### Historical Performance Trajectory")
        total_answers = len(answers_df)
        avg_score = round(float(answers_df["overall_score"].mean()) * 100, 1)
        avg_time = round(float(answers_df["time_taken_seconds"].mean()), 1)

        c1, c2, c3 = st.columns(3)
        c1.metric("Evaluated Answers", f"{total_answers}")
        c2.metric("Mean Performance", f"{avg_score}%")
        c3.metric("Avg Response Time", f"{avg_time}s")

        # Score trajectory line chart
        chart_df = answers_df[["submitted_at", "overall_score"]].copy()
        chart_df["Score (%)"] = chart_df["overall_score"] * 100
        chart_df["Attempt"] = range(1, len(chart_df) + 1)
        st.line_chart(chart_df.set_index("Attempt")["Score (%)"])

        # Cognitive Category Breakdown
        st.markdown("### Performance Across 8 Cognitive Categories")
        if category_breakdown:
            cat_table = []
            for cat, metrics in category_breakdown.items():
                cat_table.append({
                    "Cognitive Category": cat,
                    "Questions": metrics["count"],
                    "Avg Score (%)": round(metrics["avg_score"] * 100, 1),
                    "Accuracy (%)": metrics["correct_pct"],
                    "Avg Time (s)": metrics["avg_time_sec"],
                })
            st.dataframe(pd.DataFrame(cat_table), use_container_width=True)

    # ── TAB 2: MASTERY PREDICTOR (SUPERVISED ML) ──────────────────────────────
    with tab_predictor:
        st.markdown("### Scikit-Learn Topic Mastery & Risk Classification")
        st.caption(
            "Trained with Random Forest classification and StandardScaler on multi-dimensional performance vectors "
            "(accuracy, latency, difficulty distribution, error rates). Evaluated strictly on held-out test splits."
        )

        predictor = MasteryPredictor()
        feasibility = predictor.evaluate_training_feasibility(topic_df)

        if not feasibility["feasible"]:
            st.warning(f"⚠️ Model Calibration Status: {feasibility['reason']}")
            st.progress(min(feasibility["current_samples"] / feasibility["required_samples"], 1.0))
            st.markdown(
                f"""
                <div class="editorial-card">
                    <h4>Current Topic Observations: {feasibility['current_samples']} / {feasibility['required_samples']} Required</h4>
                    <p style="color: var(--color-warmgray); font-size: 13px; margin: 0;">
                        In accordance with scientific ML standards, ExamForge does not generate fake accuracy scores or hardcoded predictions. 
                        As you take examinations across curriculum topics, genuine feature vectors are compiled to train the model.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            col_train, col_status = st.columns([1, 2])
            with col_train:
                if st.button("Train / Re-Calibrate Model", type="primary"):
                    with st.spinner("Training Random Forest Classifier on historical examination telemetry..."):
                        train_result = predictor.train(topic_df)
                        if train_result["success"]:
                            st.success("Model successfully trained and persisted!")
                            st.rerun()
                        else:
                            st.error(train_result["message"])

            with col_status:
                if predictor.is_trained:
                    st.success("Model Status: **Trained & Active**")
                else:
                    st.info("Sufficient data available. Click to train model.")

            if predictor.is_trained and predictor.metrics:
                m = predictor.metrics
                st.markdown("#### Model Validation Metrics (Unseen Test Data)")
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                col_m1.metric("Test Accuracy", f"{round(m.get('test_accuracy', 0)*100, 1)}%")
                col_m2.metric("Precision", f"{round(m.get('precision', 0)*100, 1)}%")
                col_m3.metric("Recall", f"{round(m.get('recall', 0)*100, 1)}%")
                col_m4.metric("F1 Score", f"{round(m.get('f1_score', 0)*100, 1)}%")

                st.caption(f"Trained on {m.get('train_samples')} training samples • Validated on {m.get('test_samples')} test samples.")

                # Feature Importances
                if "feature_importances" in m:
                    st.markdown("#### Feature Importances")
                    imp_df = pd.DataFrame([
                        {"Feature": k.replace("_", " ").title(), "Importance": v}
                        for k, v in m["feature_importances"].items()
                    ])
                    st.bar_chart(imp_df.set_index("Feature")["Importance"])

                # Topic Risk Inference Interactive Tool
                st.markdown("#### Real-Time Topic Risk Prediction")
                if not topic_df.empty:
                    topic_choice = st.selectbox(
                        "Select Topic to Predict Mastery & Risk",
                        options=topic_df["topic_name"].tolist(),
                    )
                    selected_row = topic_df[topic_df["topic_name"] == topic_choice].iloc[0].to_dict()
                    prediction = predictor.predict_topic_risk(selected_row)

                    if prediction.get("is_predictable"):
                        badge = "badge-sage" if prediction["prediction"] == "MASTERED" else "badge-terracotta"
                        st.markdown(
                            f"""
                            <div class="stat-card" style="margin-top: 10px;">
                                <span class="badge {badge}">ML Classification: {prediction['prediction']}</span>
                                <div style="font-size: 16px; font-weight: 600; margin-top: 8px;">
                                    Mastery Probability: {round(prediction['mastery_probability']*100, 1)}% • Risk of Failure: {round(prediction['risk_probability']*100, 1)}%
                                </div>
                                <div style="color: var(--color-warmgray); font-size: 12px; margin-top: 4px;">
                                    {'⚠️ Academic reinforcement strongly advised before advancing.' if prediction['needs_reinforcement'] else '✅ Consistent mastery demonstrated across criteria.'}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

    # ── TAB 3: LEARNING ARCHETYPES (CLUSTERING) ───────────────────────────────
    with tab_clusters:
        st.markdown("### Unsupervised Cognitive Pattern Clustering")
        st.caption(
            "K-Means clustering on Granite's 5 evaluation dimensions (Correctness, Completeness, Conceptual, Reasoning, Application). "
            "Identifies recurring learning tendencies and cognitive archetypes."
        )

        clusterer = LearningPatternClusterer(n_clusters=3)
        res = clusterer.analyze_patterns(answers_df)

        if not res["feasible"]:
            st.warning(f"⚠️ Clustering Feasibility: {res['reason']}")
            st.progress(min(res["current_samples"] / res["required_samples"], 1.0))
        else:
            if res.get("silhouette_score") is not None:
                st.metric("Cluster Silhouette Score", f"{res['silhouette_score']}")

            st.markdown("#### Identified Cognitive Archetypes")
            for idx, profile in res["profiles"].items():
                st.markdown(
                    f"""
                    <div class="editorial-card" style="margin-bottom: 12px; border-left: 4px solid var(--color-olive);">
                        <div style="display: flex; justify-content: space-between;">
                            <span class="badge badge-sand">Archetype #{idx + 1} ({profile['percentage']}%)</span>
                            <span class="badge badge-olive">{profile['sample_count']} Responses</span>
                        </div>
                        <h4 style="margin: 6px 0;">{profile['archetype_label']}</h4>
                        <div style="font-size: 12px; color: var(--color-warmgray);">
                            Correctness: {profile['centroid_scores']['correctness_score']} •
                            Completeness: {profile['centroid_scores']['completeness_score']} •
                            Conceptual: {profile['centroid_scores']['conceptual_score']} •
                            Reasoning: {profile['centroid_scores']['reasoning_score']} •
                            Application: {profile['centroid_scores']['application_score']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ── TAB 4: ERROR PATTERN MINING ───────────────────────────────────────────
    with tab_gaps:
        st.markdown("### Error Pattern & Missing Concept Mining")
        st.caption("Identifies the most frequently missed concepts across all examinations to guide targeted revision.")

        if not frequent_missing:
            st.success("No recurring missing concepts detected.")
        else:
            missing_df = pd.DataFrame(frequent_missing, columns=["Concept Element", "Miss Frequency"])
            st.dataframe(missing_df, use_container_width=True)
            st.bar_chart(missing_df.set_index("Concept Element")["Miss Frequency"])
