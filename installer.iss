[Setup]
; Uygulama Bilgileri
AppName=Playlister
AppVersion=1.0
DefaultDirName={autopf}\Playlister
DefaultGroupName=Playlister
UninstallDisplayIcon={app}\Playlister.exe
Compression=lzma2
SolidCompression=yes
OutputDir=..\DistBin\Setup
OutputBaseFilename=Playlister_Setup
SetupIconFile=..\Docs\Screenshots\icon.ico

[Files]
; Ana EXE dosyan (Nuitka'nın oluşturduğu klasör içindeki her şeyi alıyoruz)
Source: "..\DistBin\Playlister.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Başlat Menüsü ve Masaüstü Kısayolları
Name: "{group}\Playlister"; Filename: "{app}\Playlister.exe"
Name: "{autodesktop}\Playlister"; Filename: "{app}\Playlister.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
; Kurulum bittince uygulamayı çalıştır seçeneği
Filename: "{app}\Playlister.exe"; Description: "{cm:LaunchProgram,Playlister}"; Flags: nowait postinstall skipifsilent
