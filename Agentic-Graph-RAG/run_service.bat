@echo off
REM CogniVox Graph RAG Service Launcher
REM This script runs the service using the virtual environment Python

echo Starting CogniVox Graph RAG Service...
.\.venv\Scripts\python.exe .\run.py %*
