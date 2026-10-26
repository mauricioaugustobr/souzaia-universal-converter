@echo off
chcp 65001 > nul
title SOUZAIA Universal Converter - Desktop

cd /d "%~dp0"

set PYTHON_EXE=.venv\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

echo [*] Abrindo o SOUZAIA Universal Converter Desktop...
"%PYTHON_EXE%" gui.py

