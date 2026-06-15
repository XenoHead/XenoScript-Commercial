; ============================================================
;  XenoScript - Inno Setup Installer Script
;  Produces: XenoScript_Setup.exe
;
;  Requirements:
;    - Inno Setup 6.x (https://jrsoftware.org/isinfo.php)
;    - Run build.bat first to produce dist\xenoscript.exe
;
;  To compile:
;    Open this file in the Inno Setup Compiler and click Build,
;    or run: ISCC.exe installer.iss
; ============================================================

#define AppName        "XenoScript"
#define AppVersion     "7.0.2"
#define AppPublisher   "XenoHead"
#define AppURL         "https://github.com/XenoHead/XenoScript-Commercial"
#define AppCopyright   "Copyright (C) 2026 XenoHead"
#define AppExeName     "XenoScript.exe"
#define AppDescription "Professional Screenplay Editor"

[Setup]
; Basic identity
AppId={{A3F1C2D4-7E8B-4F2A-9C1D-5B6E7F8A9B0C}
AppName={#AppName}
AppVersion={#AppVersion}
AppMutex=XenoScriptMutex
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppCopyright={#AppCopyright}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases

; Installation target
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes

; Output
OutputDir=dist
OutputBaseFilename=XenoScript_Setup
SetupIconFile=movie-icon.ico
WizardStyle=modern

; Compression
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; Privileges — request admin so we can write to Program Files
; and register file associations system-wide
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Minimum Windows version (Windows 10)
MinVersion=10.0

; Uninstaller
UninstallDisplayName={#AppName} {#AppVersion}
UninstallDisplayIcon={app}\{#AppExeName}

; Misc
ShowLanguageDialog=no
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Create a &desktop shortcut";              GroupDescription: "Additional shortcuts:"; Flags: checkedonce
Name: "startmenuicon";  Description: "Create a &Start Menu shortcut";           GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
; Main executable (built by PyInstaller via build.bat)
Source: "dist\xenoscript.exe"; DestDir: "{app}"; DestName: "{#AppExeName}"; Flags: ignoreversion
Source: "dist\XenoScriptUpdater.exe"; DestDir: "{app}"; Flags: ignoreversion

; App icon (for file association thumbnails)
Source: "movie-icon.ico";      DestDir: "{app}"; Flags: ignoreversion
Source: "movie-icon.png";      DestDir: "{app}"; Flags: ignoreversion

; Version manifest (update checker reads this)
Source: "version.json";        DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "writers_guide.html";    DestDir: "{app}"; Flags: ignoreversion
Source: "writer_guide_hero.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "writer_guide_blueprint.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "screenshot.png";            DestDir: "{app}"; Flags: ignoreversion
Source: "ai_assistant.png";      DestDir: "{app}"; Flags: ignoreversion
Source: "collaboration.png";     DestDir: "{app}"; Flags: ignoreversion
Source: "backups_sync.png";      DestDir: "{app}"; Flags: ignoreversion
Source: "xenohead_logo.png";     DestDir: "{app}"; Flags: ignoreversion

; Sample project (optional — ships with the installer)
Source: "SampleProject.xsp"; DestDir: "{userdocs}\XenoScript\Samples"; Flags: ignoreversion skipifsourcedoesntexist

[Dirs]
; Create the user's backup/settings folder on install
Name: "{userdocs}\XenoScript"

[Icons]
; Start Menu
Name: "{group}\{#AppName}";      Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\movie-icon.ico"; Comment: "{#AppDescription}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

; Desktop
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\movie-icon.ico"; Comment: "{#AppDescription}"; Tasks: desktopicon

[Registry]
; ── .xsp file association ──────────────────────────────────
Root: HKLM; Subkey: "Software\Classes\.xsp";                     ValueType: string; ValueName: ""; ValueData: "XenoScriptProject"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "Software\Classes\.xsp";                     ValueType: string; ValueName: "Content Type"; ValueData: "application/x-xenoscript"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "Software\Classes\XenoScriptProject";        ValueType: string; ValueName: ""; ValueData: "XenoScript Project"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Classes\XenoScriptProject\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExeName},0"
Root: HKLM; Subkey: "Software\Classes\XenoScriptProject\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""

; ── .ksp legacy file association ───────────────────────────
Root: HKLM; Subkey: "Software\Classes\.ksp";                     ValueType: string; ValueName: ""; ValueData: "XenoScriptProject"; Flags: uninsdeletevalue

; ── App registration (Add/Remove Programs extras) ──────────
Root: HKLM; Subkey: "Software\{#AppPublisher}\{#AppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\{#AppPublisher}\{#AppName}"; ValueType: string; ValueName: "Version";     ValueData: "{#AppVersion}"

[Run]
; Offer to launch XenoScript after install
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName} now"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Nothing extra needed — Inno handles registry + files automatically

[Code]
// Notify Windows that file associations changed so Explorer refreshes icons
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    RegWriteStringValue(HKEY_LOCAL_MACHINE,
      'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.xsp',
      'Application', '{app}\{#AppExeName}');
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Optionally prompt to keep user data
    if MsgBox('Would you like to delete your XenoScript settings and backups?' + #13#10 +
              '(' + ExpandConstant('{userdocs}\XenoScript') + ')',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      DelTree(ExpandConstant('{userdocs}\XenoScript'), True, True, True);
    end;
  end;
end;
