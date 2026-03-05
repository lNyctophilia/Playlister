import os

appdata_dir = os.environ.get('APPDATA') or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
CONFIG_DIR = os.path.join(appdata_dir, "Playlister")
os.makedirs(CONFIG_DIR, exist_ok=True)

FAV_FILE = os.path.join(CONFIG_DIR, "favorites.json")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Music", "Playlister")
ARCHIVE_FILE = os.path.join(DOWNLOAD_DIR, "archive.txt")

