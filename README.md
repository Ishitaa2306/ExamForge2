# ExamForge — Autonomous AI Academic Examination Platform

ExamForge is an autonomous, evidence-driven academic examination platform powered by real dual-engine AI: **Google Gemini** and **IBM Granite (via watsonx.ai)**, orchestrated with **LangGraph**, grounded in curriculum documents using **ChromaDB** vector retrieval, and enhanced with **Scikit-learn** Machine Learning for student performance and learning pattern analysis.

ExamForge is not a quiz application, chatbot, or static PDF summarizer. It acts as an astute, persistent academic examiner that deconstructs syllabi, poses targeted questions, semantically evaluates reasoning depth with IBM Granite across 5 academic criteria, adapts dynamically with Gemini follow-up probes, analyzes performance trends with Machine Learning, and compiles verified performance reports with ReportLab PDF exports.

---

## 1. Six-Agent Real AI Architecture

ExamForge maintains a strict, non-negotiable allocation across six logical AI responsibilities:

| Agent | Responsibility | Model Provider | Key Engine Role |
| :--- | :--- | :--- | :--- |
| **Agent 1** | **Document Understanding** | Google Gemini | Extracts hierarchical modules, topics, subtopics, definitions, algorithms, and formulas. |
| **Agent 2** | **Question Generation** | Google Gemini | Authors comprehensive questions across 8 cognitive categories and 3 difficulty tiers with rubrics. |
| **Agent 3** | **Autonomous Examiner** | Google Gemini | Conducts oral examination, analyzes previous answers + Granite evaluations, and formulates adaptive follow-ups. |
| **Agent 4** | **Final Report Generation** | Google Gemini | Synthesizes overall performance, knowledge gaps, and prioritized study roadmaps from stored evidence. |
| **Agent 5** | **Answer Evaluation** | IBM Granite (watsonx.ai) | Semantically evaluates answers on 5 weighted criteria: Correctness (30%), Completeness (25%), Conceptual (20%), Reasoning (15%), Application (10%). |
| **Agent 6** | **Knowledge Assessment** | IBM Granite (watsonx.ai) | Assesses cumulative topic mastery (Strong, Partially Understood, Weak, Not Assessed) from real examination evidence. |

### Architectural Model Routing

```python
AGENT_MODEL_MAPPING = {
    "document_understanding": "gemini",
    "question_generation": "gemini",
    "examination": "gemini",
    "answer_evaluation": "granite",
    "knowledge_assessment": "granite",
    "report_generation": "gemini",
}
```

---

## 2. Machine Learning Architecture (Scikit-Learn)

ExamForge integrates a dedicated **Student Performance and Learning Pattern Analysis** module (`app/ml/`):

- **Performance Analyzer (`PerformanceAnalyzer`):** Extracts longitudinal examination telemetry, calculates category-wise accuracy across 8 cognitive categories, measures time-to-answer latency, and mines frequent missing concepts.
- **Supervised Mastery Predictor (`MasteryPredictor`):** Random Forest Classifier with `StandardScaler` trained on real multi-dimensional performance features. Predicts whether a student has mastered a topic or is at risk (`MASTERED` vs `AT_RISK`). Evaluates strictly on held-out test splits without data leakage. Persists models to `storage/models/` via `joblib`.
- **Unsupervised Learning Pattern Clusterer (`LearningPatternClusterer`):** K-Means clustering on Granite's 5 evaluation criteria dimensions. Identifies student cognitive archetypes (e.g. *Theory & Definition Focused*, *Applied Pragmatist*, *Comprehensive High Performer*, *Developing Foundational*). Computes silhouette scores.
- **Data Sufficiency Guardrails:** Validates sample counts before calibration. Does not fabricate student records or generate fake accuracy scores. Displays descriptive statistics until sufficient real records are accumulated.

---

## 3. Technology Stack

- **Frontend:** Streamlit (Clean academic editorial design: Ivory, Charcoal, Terracotta, Sage, Sand)
- **Programming Language:** Python 3.11
- **Agent Orchestration:** LangGraph (StateGraph with PostgreSQL-backed state hydration)
- **Document Understanding:** Google Gemini API (`gemini-1.5-flash` / configured)
- **Answer Evaluation:** IBM Granite via IBM watsonx.ai (`ibm/granite-13b-instruct-v2` / `ibm/granite-4-h-small`)
- **Relational Database & ORM:** PostgreSQL 15+ & SQLAlchemy 2.0 (with SQLite dev fallback)
- **Database Migrations:** Alembic
- **Vector Storage & Semantic RAG:** ChromaDB & local Sentence Transformers (`all-MiniLM-L6-v2`)
- **Data Processing:** Pandas & NumPy
- **Machine Learning:** Scikit-learn (Random Forest, K-Means, StandardScaler)
- **Document Processing:** PyMuPDF & Tesseract OCR fallback
- **Report Generation & Export:** ReportLab A4 PDF Generation
- **Optional REST API:** FastAPI (retained for independent REST consumers, sharing business modules)

---

## 4. Repository Structure

```text
ExamForge/
├── streamlit_app/            # Streamlit Frontend Application
│   ├── app.py                # Main Streamlit application router & sidebar
│   ├── state.py              # Persistent session state & auth management
│   ├── styles.py             # Editorial design system & typography CSS
│   └── views/                # Dedicated page views:
│       ├── auth_view.py          # Sign-in & registration
│       ├── dashboard_view.py     # Metrics, active exam resume card, history
│       ├── documents_view.py     # PDF upload, ChromaDB RAG, Knowledge Map
│       ├── question_bank_view.py # Grounded question bank with rubrics
│       ├── examination_view.py   # Live exam room, timer, adaptive probing
│       ├── reports_view.py       # Academic reports & ReportLab PDF export
│       ├── knowledge_view.py     # Cumulative topic mastery profiling
│       ├── ml_analytics_view.py  # ML performance trends & clustering
│       └── settings_view.py      # System health & live AI provider testing
├── backend/
│   ├── app/
│   │   ├── agents/           # Six dedicated AI agent modules (Gemini & Granite)
│   │   ├── api/              # FastAPI REST endpoints (retained for REST clients)
│   │   ├── core/             # Configuration, security, dependencies
│   │   ├── database/         # Connection engine & 14 SQLAlchemy models
│   │   ├── llm/              # Live Gemini and Granite clients & router
│   │   ├── ml/               # Machine learning module (analyzer, predictor, clusterer)
│   │   ├── prompts/          # Six prompt modules for each agent responsibility
│   │   ├── schemas/          # Pydantic request & response schemas
│   │   ├── services/         # PDF, embedding, examination & report services
│   │   ├── workflows/        # LangGraph StateGraph, nodes & checkpoints
│   │   └── tests/            # Automated pytest suite (36 tests)
│   ├── alembic/              # Database migration environment & versions
│   └── requirements.txt
├── storage/
│   ├── uploads/              # Uploaded PDF files
│   ├── chroma/               # ChromaDB vector index
│   └── models/               # Persisted Scikit-learn ML models (.joblib)
├── _backup_original/         # Complete preserved backup of original codebase
├── run_app.py                # Root launcher for Streamlit
├── requirements.txt          # Unified requirements for deployment
├── .env.example              # Documented environment template
└── README.md
```

---

## 5. Prerequisites & Quickstart

### Prerequisites
- **Python 3.11** (`python --version`)
- **PostgreSQL 15+** (optional: running locally or hosted on Neon/Supabase; SQLite dev fallback is supported)
- **PowerShell 5.1+ / bash**

### Step 1: Clone & Configure Environment

```powershell
# Copy template to .env
Copy-Item .env.example .env
```

Edit `.env` with your API credentials:

```env
AI_PROVIDER_MODE=live
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL_ID=gemini-1.5-flash
WATSONX_API_KEY=your_actual_watsonx_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/examforge
JWT_SECRET_KEY=super-secure-random-secret-key-for-jwt-tokens
```

### Step 2: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 3: Run the Streamlit Application

```powershell
streamlit run run_app.py
```

The Streamlit UI will open in your browser at:
`http://localhost:8501`

*(Alternative startup command: `streamlit run streamlit_app/app.py`)*

### Step 4 (Optional): Run FastAPI Backend

If independent REST consumers or legacy clients need access:

```powershell
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 6. Running Automated Tests

Run the full automated test suite (36 tests):

```powershell
pytest backend/app/tests/ -v
```

The test suite validates:
1. **Agent Routing & Prompts (`test_agents.py`):** Model mapping for all 6 agents, error validation, prompt builders.
2. **Authentication (`test_auth.py`):** Registration, password hashing, login, duplicate detection, JWT generation.
3. **Documents (`test_documents.py`):** Document listing, retrieval, and status tracking.
4. **Examinations (`test_examinations.py`):** Session initialization, difficulty tracking, settings endpoints.
5. **Machine Learning (`test_ml.py`):** Model persistence, data sufficiency guards, Random Forest training on test split, feature importances, and K-Means clustering.
6. **Integration Suite (`test_migration_integration.py`):** Full end-to-end relational schema, LangGraph state hydration, and ReportLab PDF compilation.

---

## 7. Streamlit Community Cloud Deployment

1. Push the repository to GitHub.
2. Log into [Streamlit Community Cloud](https://share.streamlit.io).
3. Create a **New App**:
   - **Repository:** `<your-repo>/ExamForge`
   - **Branch:** `main` (or `migration/streamlit-ml`)
   - **Main file path:** `run_app.py` (or `streamlit_app/app.py`)
4. In **App Settings ➔ Secrets**, paste your `.env` variables:
   ```toml
   AI_PROVIDER_MODE = "live"
   GEMINI_API_KEY = "your_actual_key"
   GEMINI_MODEL_ID = "gemini-1.5-flash"
   WATSONX_API_KEY = "your_actual_watsonx_key"
   WATSONX_PROJECT_ID = "your_project_id"
   WATSONX_URL = "https://us-south.ml.cloud.ibm.com"
   GRANITE_MODEL_ID = "ibm/granite-13b-instruct-v2"
   DATABASE_URL = "postgresql://user:pass@ep-xyz.aws.neon.tech/examforge?sslmode=require"
   JWT_SECRET_KEY = "secure-random-jwt-key"
   ```
5. Click **Deploy**. Streamlit Cloud will install `requirements.txt` and run the application.
