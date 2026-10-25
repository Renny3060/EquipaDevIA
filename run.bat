@echo off
cd /d "%~dp0"
if not exist venv (
  py -3.11 -m venv venv || python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt -q
start "" http://localhost:8501
streamlit run app.py