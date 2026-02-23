import tkinter as tk
from tkinter import ttk, messagebox
import requests
from ytmusicapi import YTMusic
import threading
import time
import locale
import json
import os
import webbrowser

try:
    import vlc
    import yt_dlp
except ImportError:
    vlc = None
    yt_dlp = None

from utils import decrypt_text, parse_views, ENC_KEY
from ui.ui_shared import UiShared
from ui.view_search import ViewSearch
from ui.view_charts import ViewCharts
from ui.view_genre import ViewGenre
from ui.view_fav import ViewFav
from ui.view_player import ViewPlayer
from ui.view_settings import ViewSettings

FAV_FILE = "Config/favorites.json"

class App(UiShared, ViewSearch, ViewCharts, ViewGenre, ViewFav, ViewPlayer, ViewSettings):
    def __init__(self, root):
        self.root = root
        self.root.title("Playlister")
        self.root.geometry("1100x700")
        
        try:
            self.yt = YTMusic()
        except Exception as e:
            messagebox.showerror("Başlatma Hatası", f"API Başlatılamadı: {e}")
            self.yt = None

        # --- Üst Navigasyon Barı (Mod Seçimi) ---
        self.nav_frame = tk.Frame(root, bg="#333", pady=5)
        self.nav_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Stil
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except:
            pass
        
        # Treeview ve Başlıklar için Stil
        style.configure("Treeview", 
                        background="white",
                        fieldbackground="white",
                        foreground="black",
                        rowheight=25)
        
        style.configure("Treeview.Heading", 
                        font=("Helvetica", 9, "bold"), 
                        background="#e1e1e1", 
                        foreground="#333",
                        relief="raised")
        
        style.map("Treeview", background=[('selected', '#4CAF50')])

        style.configure("Nav.TButton", font=("Helvetica", 11, "bold"), padding=6)
        
        self.btn_mode_search = tk.Button(self.nav_frame, text="🎵 Sanatçı & Şarkı Arama", 
                                         command=self.show_search_view, 
                                         font=("Helvetica", 10, "bold"),
                                         bg="#ddd", fg="#333", relief=tk.RAISED)
        self.btn_mode_search.pack(side=tk.LEFT, padx=(20, 5), pady=5)
        
        self.btn_mode_chart = tk.Button(self.nav_frame, text="🌍 Ülke Top Listeleri", 
                                        command=self.show_chart_view,
                                        font=("Helvetica", 10, "bold"),
                                        bg="#ddd", fg="#333", relief=tk.RAISED)
        self.btn_mode_chart.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_mode_genre = tk.Button(self.nav_frame, text="🎸 Türe Göre Öneri",
                                        command=self.show_genre_view,
                                        font=("Helvetica", 10, "bold"),
                                        bg="#ddd", fg="#333", relief=tk.RAISED)
        self.btn_mode_genre.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_mode_fav = tk.Button(self.nav_frame, text="❤ Favoriler",
                                        command=self.show_fav_view,
                                        font=("Helvetica", 10, "bold"),
                                        bg="#ddd", fg="#333", relief=tk.RAISED)
        self.btn_mode_fav.pack(side=tk.LEFT, padx=5, pady=5)

        # Ayarlar Butonu (Sağ Üst)
        self.btn_settings = tk.Button(self.nav_frame, text="⚙ Ayarlar",
                                      command=self.open_settings,
                                      font=("Helvetica", 9),
                                      bg="#555", fg="white", relief=tk.RAISED)
        self.btn_settings.pack(side=tk.RIGHT, padx=20, pady=5)


        # --- Ana Konteyner ---
        self.container = tk.Frame(root)
        self.container.pack(fill="both", expand=True, pady=5)
        
        # --- Görünümler ---
        self.search_view = tk.Frame(self.container)
        self.chart_view = tk.Frame(self.container)
        self.genre_view = tk.Frame(self.container)
        self.fav_view = tk.Frame(self.container)
        
        # Status Bar
        self.status_bar = tk.Label(root, text="Hazır", bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#f0f0f0", font=("Consolas", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Player Init
        self.vlc_instance = None
        self.player = None
        self.is_playing = False
        self.is_looping = False
        self.current_video_id = None
        self.total_duration = 0
        self.is_dragging_time = False
        
        if vlc:
            try:
                # --no-video: Video penceresini engeller (Audio-only)
                # --quiet: Konsol hatalarını azaltır
                self.vlc_instance = vlc.Instance('--no-video', '--quiet')
                self.player = self.vlc_instance.media_player_new()
            except Exception as e:
                print(f"VLC Init Error: {e}")
                
        self.setup_player_view()

        # UI Components Setup (From Mixins)
        self.setup_search_view()
        self.setup_chart_view()
        self.setup_genre_view()
        self.setup_fav_view()
        
        # Varsayılan görünüm
        self.show_search_view()
        
        # Veri saklama
        self.song_map = {} 
        self.chart_map = {} 
        self.fav_map = {} 
        self.favorites = self.load_favorites()
        
        # Last.fm API Init
        self.config_file = "Config/config.json"
        
        conf = self.load_config()
        encrypted_key = conf.get("lastfm_api_key", "")
        self.lastfm_api_key = decrypt_text(encrypted_key) if encrypted_key else ""
        
        self.stop_listing = False
        self.current_search_id = None

    def stop_current_listing(self):
        self.stop_listing = True
        self.current_search_id = None
        self.update_status("Durduruluyor...", "orange")
        
        # Arayüzü arama yapılabilir hale anında getir (Durdur -> Ara dönüşümü)
        if hasattr(self, 'btn_search'):
            self.root.after(0, lambda: self.lbl_search_progress.config(text=""))
            self.root.after(0, lambda: self.btn_search.config(text="Ara", bg="#2196F3", fg="white"))
            self.root.after(0, lambda: self.entry_artist.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.entry_search_limit.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.combo_search_mode.config(state="readonly"))

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()