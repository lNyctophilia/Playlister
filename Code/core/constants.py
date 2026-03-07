import os
import sys

# Uygulamanın çalıştığı dizini bul (Nuitka ile derlenmişse sys.executable, değilse __file__)
if getattr(sys, 'frozen', False) or "__compiled__" in globals():
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG_DIR = os.path.join(BASE_DIR, "Data")
os.makedirs(CONFIG_DIR, exist_ok=True)

FAV_FILE = os.path.join(CONFIG_DIR, "favorites.json")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Music", "Playlister")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
ARCHIVE_FILE = os.path.join(DOWNLOAD_DIR, "archive.txt")

APP_VERSION = "v14.5"
GITHUB_REPO_URL = "https://api.github.com/repos/lNyctophilia/Playlister/releases/latest"
GITHUB_RELEASE_URL = "https://github.com/lNyctophilia/Playlister/releases/latest"
