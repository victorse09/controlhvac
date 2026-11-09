[Setup]
AppId={{D37B75A1-9456-42C4-8551-A59B0B7C6DE4}
AppName=ControlHVAC
AppVersion=1.0.0
AppPublisher=HVAC Systems
AppPublisherURL=https://github.com/
AppSupportURL=https://github.com/
AppUpdatesURL=https://github.com/
DefaultDirName={autopf}\ControlHVAC
DefaultGroupName=ControlHVAC
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=ControlHVAC_Setup_v1.0.0
SetupIconFile=assets\icons\app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\ControlHVAC\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ControlHVAC"; Filename: "{app}\ControlHVAC.exe"; IconFilename: "{app}\assets\icons\app_icon.ico"
Name: "{group}\{cm:UninstallProgram,ControlHVAC}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\ControlHVAC"; Filename: "{app}\ControlHVAC.exe"; IconFilename: "{app}\assets\icons\app_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\ControlHVAC.exe"; Description: "{cm:LaunchProgram,ControlHVAC}"; Flags: nowait postinstall skipifsilent
