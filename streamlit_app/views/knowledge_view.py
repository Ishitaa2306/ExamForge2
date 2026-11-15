"""
Knowledge Profile View.
Displays cumulative curriculum mastery synthesized by IBM Granite across multiple examinations.
"""
import streamlit as st
import pandas as pd

from app.database.models import (
    Document,
    DocumentTopic,
    KnowledgeProfile,
)
from streamlit_app.state import get_current_user_id, get_db_session


def render_knowledge_view():
    user_id = get_current_user_id()
    if not user_id:
        st.warning("Please sign in to view your knowledge profile.")
        return

    st.markdown(
        """
        <div>
            <span class="badge badge-terracotta">Agent 6: Knowledge Assessment (IBM Granite)</span>
            <h1 style="font-size: 30px; margin-top: 6px; margin-bottom: 4px;">Cumulative Knowledge Profile</h1>
            <p style="color: var(--color-warmgray); font-size: 14px;">
                Longitudinal topic mastery profiles compiled across all completed examination sessions by IBM Granite.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    db = get_db_session()
    try:
        profiles = (
            db.query(KnowledgeProfile)
            .filter(KnowledgeProfile.user_id == user_id)
            .order_by(KnowledgeProfile.updated_at.desc())
            .all()
        )

        if not profiles:
            st.info("No knowledge profiles found. Complete your first examination to establish your topic mastery profile.")
            return

        for profile in profiles:
            doc = db.query(Document).filter(Document.id == profile.document_id).first()
            doc_name = doc.original_filename if doc else f"Document #{profile.document_id}"
            score_pct = round((profile.overall_score or 0.0) * 100)

            strong_count = len(profile.strong_topics or [])
            partial_count = len(profile.partial_topics or [])
            weak_count = len(profile.weak_topics or [])
            not_assessed_count = len(profile.not_assessed_topics or [])
            total_topics = strong_count + partial_count + weak_count + not_assessed_count

            st.markdown(
                f"""
                <div class="editorial-card" style="border-left: 5px solid var(--color-sage); margin-top: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span class="badge badge-sage">Mastery Profile</span>
                            <h2 style="font-size: 22px; margin: 4px 0;">{doc_name}</h2>
                            <p style="color: var(--color-warmgray); font-size: 13px; margin: 0;">
                                Aggregated across {profile.total_examinations} examination{'s' if profile.total_examinations != 1 else ''}
                            </p>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 26px; font-weight: 700; font-family: 'Cinzel', serif; color: var(--color-charcoal);">{score_pct}%</div>
                            <div style="font-size: 11px; text-transform: uppercase; color: var(--color-warmgray);">Overall Score</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 4 Summary Stats
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Strong Topics", f"{strong_count}")
            s2.metric("Partially Understood", f"{partial_count}")
            s3.metric("Weak / Gaps", f"{weak_count}")
            s4.metric("Not Assessed", f"{not_assessed_count}")

            # Topic Mastery Distribution Bar Chart
            chart_df = pd.DataFrame({
                "Mastery Classification": ["Strong", "Partially Understood", "Weak / Needs Work", "Not Assessed"],
                "Count": [strong_count, partial_count, weak_count, not_assessed_count],
            })
            st.bar_chart(chart_df.set_index("Mastery Classification"))

            # Specific Topic Breakdown
            topics = db.query(DocumentTopic).filter(DocumentTopic.document_id == profile.document_id).all()
            topic_dict = {t.id: t.name for t in topics}

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### High Mastery Topics")
                if not profile.strong_topics:
                    st.caption("None yet.")
                else:
                    for t_id in profile.strong_topics:
                        st.markdown(f"🏆 **{topic_dict.get(t_id, f'Topic #{t_id}')}**")

                st.markdown("#### Partially Mastered Topics")
                if not profile.partial_topics:
                    st.caption("None.")
                else:
                    for t_id in profile.partial_topics:
                        st.markdown(f"📘 **{topic_dict.get(t_id, f'Topic #{t_id}')}**")

            with col_b:
                st.markdown("#### High Priority Remediation Areas")
                if not profile.weak_topics:
                    st.success("No critical weakness areas detected!")
                else:
                    for t_id in profile.weak_topics:
                        st.markdown(f"🚨 **{topic_dict.get(t_id, f'Topic #{t_id}')}**")

                st.markdown("#### Unassessed Topics")
                if not profile.not_assessed_topics:
                    st.caption("All curriculum topics have been assessed.")
                else:
                    for t_id in profile.not_assessed_topics:
                        st.markdown(f"⚪ *{topic_dict.get(t_id, f'Topic #{t_id}')}*")

    finally:
        db.close()
