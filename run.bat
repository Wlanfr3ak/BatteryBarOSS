@echo off
rem ==========================================================================
rem  BatteryBar OSS - launcher (no console window, via pythonw)
rem  Debug with console:  set PYTHONPATH=%CD%\src ^&^& python -m batterybar
rem ==========================================================================
setlocal
set "ROOT=%~dp0"
set "PYTHONPATH=%ROOT%src"
start "" /min pythonw -m batterybar
endlocal
