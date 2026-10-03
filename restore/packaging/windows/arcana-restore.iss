; Inno Setup script. Build: iscc /DAppVersion=0.1.0 packaging\windows\arcana-restore.iss
; Expects dist\ArcanaRestore.exe and dist\arcana-restore.exe (from packaging\build.py).
#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppId={{6E0A54D2-3C1B-4B8E-9C52-1A0F7D3B5E41}
AppName=Arcana Restore
AppVersion={#AppVersion}
AppPublisher=Arcana Forensics
AppPublisherURL=https://arcana-forensics.com
DefaultDirName={autopf}\Arcana Restore
DefaultGroupName=Arcana Restore
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=ArcanaRestore-Setup-{#AppVersion}
SetupIconFile=..\icons\icon.ico
UninstallDisplayIcon={app}\ArcanaRestore.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Per-user install by default: no administrator prompt. The user may choose all-users.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"

[Files]
Source: "..\..\dist\ArcanaRestore.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\dist\arcana-restore.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Arcana Restore"; Filename: "{app}\ArcanaRestore.exe"
Name: "{autodesktop}\Arcana Restore"; Filename: "{app}\ArcanaRestore.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\ArcanaRestore.exe"; Description: "Launch Arcana Restore"; Flags: nowait postinstall skipifsilent
