@echo off
chcp 65001 >nul
cd /d %~dp0
"C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe" run_gui.py 2>error.log
if errorlevel 1 (
    echo.
    echo Launch failed. See error.log for details.
    pause
)
