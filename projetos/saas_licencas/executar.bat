@echo off
cd /d "%~dp0codigo"
if not exist "..\.venv" ( python -m venv ..\.venv )
call ..\.venv\Scripts\activate
if exist requirements.txt pip install -r requirements.txt -q
uvicorn main:app --reload
pause
