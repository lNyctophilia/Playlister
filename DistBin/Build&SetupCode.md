Build Code

---------------------

python -m nuitka --standalone --windows-disable-console --enable-plugin=tk-inter --include-package=core --include-package=ui --include-package=utils --include-package=services --include-package-data=ytmusicapi --include-data-files=Requriements/libvlc.dll=./libvlc.dll --include-data-files=Requriements/libvlccore.dll=./libvlccore.dll --include-data-dir=Requriements/plugins=./plugins --include-data-files=Requriements/ffmpeg.exe=./ffmpeg.exe --include-data-files=Docs/Screenshots/icon.ico=./icon.ico --include-data-files=Docs/Screenshots/Playlister256x256RoundedCorner.png=./Playlister256x256RoundedCorner.png --windows-icon-from-ico=Docs/Screenshots/icon.ico --output-dir=DistBin Code/Playlister.py


Setup Code

---------------------

[Setup]
AppName=Playlister
AppVersion=v12.7
DefaultDirName={autolocalprogramming}\Playlister
DefaultGroupName=Playlister
UninstallDisplayIcon={app}\Playlister.exe
Compression=lzma2
SolidCompression=yes
OutputDir=..\DistBin\Setup
OutputBaseFilename=Playlister_Setup
SetupIconFile=..\Docs\Screenshots\icon.ico
PrivilegesRequired=lowest

[Files]
Source: "..\DistBin\Playlister.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\Requriements\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\Playlister"; Filename: "{app}\Playlister.exe"
Name: "{autodesktop}\Playlister"; Filename: "{app}\Playlister.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Visual C++ Runtime yükleniyor..."; Flags: waituntilterminated
Filename: "{app}\Playlister.exe"; Description: "{cm:LaunchProgram,Playlister}"; Flags: nowait postinstall skipifsilent
