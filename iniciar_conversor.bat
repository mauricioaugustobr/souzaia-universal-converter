@echo off
chcp 65001 > nul
title SOUZAIA Universal Converter - Alta Fidelidade

:: Garante que o diretório de trabalho é o diretório deste script
cd /d "%~dp0"

echo =======================================================
echo          SOUZAIA UNIVERSAL CONVERTER v1.0
echo   Conversor de Documento, Foto, Audio e Video
echo =======================================================
echo.

set PYTHON_EXE=.venv\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

echo [*] Iniciando servidor do conversor...
echo [*] O navegador abrira automaticamente quando o sistema estiver pronto.
echo.

"%PYTHON_EXE%" server.py

echo.
echo [!] Servidor encerrado.
pause
