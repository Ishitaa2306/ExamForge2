"""
ExamForge — Streamlit Entry Point for Local & Cloud Deployments.
Run via:
    streamlit run run_app.py
or
    streamlit run streamlit_app/app.py
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from streamlit_app.app import main

if __name__ == "__main__":
    main()
