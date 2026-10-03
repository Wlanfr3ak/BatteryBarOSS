@echo off
rem ==========================================================================
rem  BatteryBar OSS - Starter (ohne Konsolenfenster via pythonw)
rem  Debug mit Konsole:  set PYTHONPATH=%CD%\src ^&^& python -m batterybar
rem ==========================================================================
setlocal
set "ROOT=%~dp0"
set "PYTHONPATH=%ROOT%src"
start "" /min pythonw -m batterybar
endlocal
