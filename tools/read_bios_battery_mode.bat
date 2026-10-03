@echo off
rem Reads the HP BIOS battery mode (Battery Health Manager) via HP WMI.
rem Requires administrator rights - triggers a UAC prompt once.
rem Result is cached in config\hp_bios.local.json (gitignored) and shown
rem by the app in "health" display mode as "BHM: <mode>".
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -Wait -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','\"%~dp0read_bios_battery_mode.ps1\"'"
echo.
echo --- Cached result ---
type "%~dp0..\config\hp_bios.local.json" 2>nul
echo.
pause
