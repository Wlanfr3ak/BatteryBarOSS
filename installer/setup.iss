; BatteryBar OSS - Inno Setup script
; Build: tools\build_installer.bat (injects /DAppVersion from __init__.py)
#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif

[Setup]
AppName=BatteryBar OSS
AppVersion={#AppVersion}
AppPublisher=Wlanfr3ak + contributors
AppCopyright=MIT License - generated with Devin (Cognition AI, SWE-2 High)
DefaultDirName={autopf}\BatteryBarOSS
DefaultGroupName=BatteryBar OSS
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
OutputDir=..\installer\Output
OutputBaseFilename=BatteryBarOSS-Setup-{#AppVersion}
UninstallDisplayIcon={app}\BatteryBarOSS.exe
Compression=lzma2
SolidCompression=yes

[Tasks]
Name: "autostart"; Description: "Start BatteryBar OSS with Windows"; GroupDescription: "Additional tasks:"; Flags: checkedonce

[Files]
Source: "..\dist\BatteryBarOSS.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: isreadme
Source: "..\LICENSE"; DestDir: "{app}"
Source: "..\NOTICE"; DestDir: "{app}"

[Icons]
Name: "{group}\BatteryBar OSS"; Filename: "{app}\BatteryBarOSS.exe"
Name: "{group}\Uninstall BatteryBar OSS"; Filename: "{uninstallexe}"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "BatteryBarOSS"; ValueType: string; ValueData: """{app}\BatteryBarOSS.exe"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\BatteryBarOSS.exe"; Description: "Start BatteryBar OSS now"; Flags: nowait postinstall skipifsilent
