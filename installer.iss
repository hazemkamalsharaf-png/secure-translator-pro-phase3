; =============================================================================
; Secure Translator Pro - Inno Setup Script
; =============================================================================
; Build with: iscc installer.iss
; Output: output\SecureTranslatorPro_Setup.exe
; =============================================================================

#define MyAppName "Secure Translator Pro"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Hazem Kamal Sharaf"
#define MyAppURL "https://github.com/hazemkamalsharaf-png/secure-translator-pro-phase3"
#define MyAppExeName "SecureTranslatorPro.exe"

[Setup]
; --- General Info ---
AppId={{A3F8B2C1-D4E5-6789-ABCD-EF0123456789}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; --- Output Settings ---
DefaultDirName={autopf}\SecureTranslatorPro
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=SecureTranslatorPro_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

; --- Binary Settings ---
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}

; --- UI Settings ---

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; --- Main Application (from PyInstaller dist) ---
Source: "dist\SecureTranslatorPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; ; --- Note: Remove the following line if you don't apply application patches ---
; Source: "output\*.patch"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Optional: Launch the application after installation
    // ShellExec('open', ExpandConstant('{app}\{#MyAppExeName}'), '', '', SW_SHOW, ewNoWait, ResultCode);
  end;
end;
