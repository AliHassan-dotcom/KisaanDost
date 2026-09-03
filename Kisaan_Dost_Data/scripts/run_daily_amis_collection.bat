@echo off
REM Scheduled Daily AMIS Price Collection Task
cd /d "%~dp0\..\.."
python Kisaan_Dost_Data\scripts\run_daily_amis_collection.py
exit /b %ERRORLEVEL%
