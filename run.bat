@echo off
cd /d "%~dp0"
py server.py
if errorlevel 1 (
  echo.
  echo If Python is installed but the py command is unavailable, try: python server.py
  pause
)
