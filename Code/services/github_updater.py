import requests
import threading
import tkinter as tk
from tkinter import messagebox
import webbrowser

from core.constants import APP_VERSION, GITHUB_REPO_URL, GITHUB_RELEASE_URL

def check_for_updates(root):
    def update_check_thread():
        try:
            response = requests.get(GITHUB_REPO_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("tag_name", "")
                
                if latest_version and latest_version != APP_VERSION:
                    root.after(0, lambda: show_update_dialog(latest_version))
        except Exception:
            pass

    def show_update_dialog(latest_version):
        msg = f"Uygulamanın yeni bir sürümü yayınlandı!\n\nŞimdiki Sürüm: {APP_VERSION}\nYeni Sürüm: {latest_version}\n\nİndirme sayfasına gitmek ister misiniz?"
        result = messagebox.askyesno("Yeni Sürüm Var!", msg)
        if result:
            webbrowser.open(GITHUB_RELEASE_URL)
            
    threading.Thread(target=update_check_thread, daemon=True).start()
