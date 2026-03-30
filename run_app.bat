@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "APP_ENTRY=%PROJECT_ROOT%app\main.py"

set "PYTHON_EXE=%PROJECT_ROOT%.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
  set "PYTHON_EXE=%PROJECT_ROOT%venv\Scripts\python.exe"
)

if not exist "%APP_ENTRY%" (
  echo [ERRO] Arquivo nao encontrado: %APP_ENTRY%
  exit /b 1
)

if not exist "%PYTHON_EXE%" (
  echo [ERRO] Python do ambiente virtual nao encontrado em .venv\Scripts\python.exe nem venv\Scripts\python.exe
  exit /b 1
)

set "PYTHONPATH=%PROJECT_ROOT%"
"%PYTHON_EXE%" -m streamlit run "%APP_ENTRY%"
