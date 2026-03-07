--------------------------------------

1. olarak :
-core/constants.py sürüm güncellemesi yap
-Setup kodunda ve installer.iss kodunda sürüm güncellemesi yap

--------------------------------------



2. olarak (Terminale Build Code) :

--------------------------------------


python -m nuitka --standalone --windows-console-mode=disable --enable-plugin=tk-inter --enable-plugin=anti-bloat --jobs=8 --lto=no --include-package=core --include-package=ui --include-package=utils --include-package=services --follow-import-to=vlc --follow-import-to=yt_dlp --include-package-data=ytmusicapi --include-data-files=Requriements/libvlc.dll=./libvlc.dll --include-data-files=Requriements/libvlccore.dll=./libvlccore.dll --include-data-dir=Requriements/plugins=./plugins --include-data-files=Requriements/ffmpeg.exe=./ffmpeg.exe --include-data-files=Docs/Screenshots/icon.ico=./icon.ico --include-data-files=Docs/Screenshots/Playlister256x256RoundedCorner.png=./Playlister256x256RoundedCorner.png --windows-icon-from-ico=Docs/Screenshots/icon.ico --output-dir=DistBin Code/Playlister.py ; robocopy Requriements\plugins DistBin\Playlister.dist\plugins /E



3. olarak (Inno Setup Code) :

--------------------------------------


[Setup]
AppName=Playlister
AppVersion=v14.2
DefaultDirName={autopf}\Playlister
DefaultGroupName=Playlister
UninstallDisplayIcon={app}\Playlister.exe
Compression=lzma2
SolidCompression=yes
OutputDir=..\DistBin\Setup
OutputBaseFilename=Playlister_Setup
SetupIconFile=..\Docs\Screenshots\icon.ico
PrivilegesRequired=lowest

[Files]
; Derlenmiş tüm dosyalar (VLC ve FFmpeg dahil)
Source: "..\DistBin\Playlister.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Visual C++ Runtime (Gerekli bileşen)
Source: "..\Requriements\VC_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\Playlister"; Filename: "{app}\Playlister.exe"
Name: "{autodesktop}\Playlister"; Filename: "{app}\Playlister.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
; Kurulum sonrası VC++ Runtime yüklemesi
Filename: "{tmp}\VC_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Visual C++ Runtime yükleniyor..."; Flags: waituntilterminated
; Uygulamayı başlat
Filename: "{app}\Playlister.exe"; Description: "{cm:LaunchProgram,Playlister}"; Flags: nowait postinstall skipifsilent