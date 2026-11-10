#define AppVersion GetEnv("FMCC_VERSION")

[Setup]
AppName=FMCC
AppVersion={#AppVersion}
AppPublisher=From Underdog Podcasts
DefaultDirName={autopf}\FMCC
DefaultGroupName=FMCC
OutputDir=..\dist-installer
OutputBaseFilename=FMCC-Setup
SetupIconFile=fmcc.ico
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Files]
Source: "..\dist\FMCC\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\FMCC"; Filename: "{app}\FMCC.exe"
Name: "{autodesktop}\FMCC"; Filename: "{app}\FMCC.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"

[Run]
Filename: "{app}\FMCC.exe"; Description: "Open FMCC"; Flags: nowait postinstall skipifsilent
Filename: "{app}\FMCC.exe"; Flags: nowait; Check: WizardSilent
