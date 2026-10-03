@echo off
rem Builds dist\BatteryBarOSS.exe via PyInstaller (dev tool, see docs/DEPENDENCIES.md).
setlocal
set "ROOT=%~dp0.."
pushd "%ROOT%"
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name BatteryBarOSS --paths "%ROOT%\src" --distpath "%ROOT%\dist" --workpath "%ROOT%\build" --specpath "%ROOT%\build" "%ROOT%\installer\entry.py"
popd
