import os
import sys

# Add current directory to path so we can import utils_downloader
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from utils_downloader import DOWNLOAD_DIR, Downloader

print(f"Old Download Dir variable: {DOWNLOAD_DIR}")

# Check if directory creation works
try:
    Downloader.ensure_dir()
    if os.path.exists(DOWNLOAD_DIR):
        print(f"Verified: Directory exists at {DOWNLOAD_DIR}")
    else:
        print(f"Error: Directory does not exist at {DOWNLOAD_DIR}")
except Exception as e:
    print(f"Error creating directory: {e}")
