@echo off
rem Builds the PyInstaller exe and the Inno Setup installer.
rem Requires: pyinstaller (pip), Inno Setup 6 (iscc on PATH or default location).
setlocal
set "ROOT=%~dp0.."
call "%~dp0build_exe.bat" || exit /b 1

for /f "usebackq delims=" %%v in (`python -c "import sys; sys.path.insert(0, r'%ROOT%\src'); import batterybar; print(batterybar.__version__)"`) do set "APPVER=%%v"
echo Building installer for v%APPVER% ...

set "ISCC=iscc"
where iscc >nul 2>nul || set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
"%ISCC%" /DAppVersion=%APPVER% "%ROOT%\installer\setup.iss"
