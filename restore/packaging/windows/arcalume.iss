; Inno Setup script for the direct-download Windows installer.
; Build: iscc /DAppVersion=0.2.0 packaging\windows\arcalume.iss
; Expects dist\Arcalume\ (onedir app) and dist\arcana-restore.exe (from packaging\build.py).
#ifndef AppVersion
  #define AppVersion "0.2.0"
#endif

[Setup]
AppId={{6E0A54D2-3C1B-4B8E-9C52-1A0F7D3B5E41}
AppName=Arcalume
AppVersion={#AppVersion}
AppPublisher=Arcana-Forensics
AppPublisherURL=https://arcana-forensics.com/arcalume
DefaultDirName={autopf}\Arcalume
DefaultGroupName=Arcalume
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=Arcalume-Setup-{#AppVersion}
SetupIconFile=..\icons\icon.ico
UninstallDisplayIcon={app}\Arcalume.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Per-user install by default: no administrator prompt. The user may choose all-users.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"

[Files]
Source: "..\..\dist\Arcalume\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\dist\arcana-restore.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Arcalume"; Filename: "{app}\Arcalume.exe"
Name: "{autodesktop}\Arcalume"; Filename: "{app}\Arcalume.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Arcalume.exe"; Description: "Launch Arcalume"; Flags: nowait postinstall skipifsilent
