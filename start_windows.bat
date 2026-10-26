@echo off
REM CareerCollective - install Python 3.11+ first.
if not exist .venv (py -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
pause