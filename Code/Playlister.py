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

from core.constants import CONFIG_FILE
from core.config_manager import load_config
from core.crypto import decrypt_text
from utils.utils import parse_views
from ui.ui_shared import UiShared
from ui.view_search import ViewSearch
from ui.view_charts import ViewCharts
from ui.view_genre import ViewGenre
from ui.view_fav import ViewFav
from ui.view_player import ViewPlayer
from ui.view_settings import ViewSettings
from ui.context_menu import ContextMenuMixin
from ui import theme as T

class App(UiShared, ContextMenuMixin, ViewSearch, ViewCharts, ViewGenre, ViewFav, ViewPlayer, ViewSettings):
    def __init__(self, root):
        self.root = root
        self.root.title("Playlister")
        self.root.geometry("1100x700")
        self.root.config(bg=T.BG_MAIN)
        
        try:
            self.yt = YTMusic()
        except Exception as e:
            messagebox.showerror("Başlatma Hatası", f"API Başlatılamadı: {e}")
            self.yt = None

        style = ttk.Style()
        T.configure_ttk_styles(style)

        self.nav_frame = tk.Frame(root, bg=T.BG_NAV, pady=5)
        self.nav_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.btn_mode_search = tk.Button(self.nav_frame, text="🎵 Sanatçı & Şarkı Arama", 
                                         command=self.show_search_view)
        T.style_button(self.btn_mode_search, bg=T.NAV_INACTIVE, hover_bg=T.NAV_HOVER)
        self.btn_mode_search.pack(side=tk.LEFT, padx=(20, 5), pady=5)
        
        self.btn_mode_chart = tk.Button(self.nav_frame, text="🌍 Ülke Top Listeleri", 
                                        command=self.show_chart_view)
        T.style_button(self.btn_mode_chart, bg=T.NAV_INACTIVE, hover_bg=T.NAV_HOVER)
        self.btn_mode_chart.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_mode_genre = tk.Button(self.nav_frame, text="🎸 Türe Göre Öneri",
                                        command=self.show_genre_view)
        T.style_button(self.btn_mode_genre, bg=T.NAV_INACTIVE, hover_bg=T.NAV_HOVER)
        self.btn_mode_genre.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_mode_fav = tk.Button(self.nav_frame, text="❤ Favoriler",
                                        command=self.show_fav_view)
        T.style_button(self.btn_mode_fav, bg=T.NAV_INACTIVE, hover_bg=T.NAV_HOVER)
        self.btn_mode_fav.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_settings = tk.Button(self.nav_frame, text="⚙ Ayarlar",
                                      command=self.open_settings)
        T.style_button(self.btn_settings, bg="#2a2f5a", hover_bg="#353b6e")
        self.btn_settings.config(font=T.FONT_BODY)
        self.btn_settings.pack(side=tk.RIGHT, padx=20, pady=5)

        self.container = tk.Frame(root, bg=T.BG_MAIN)
        self.container.pack(fill="both", expand=True, pady=5)
        
        self.search_view = tk.Frame(self.container, bg=T.BG_MAIN)
        self.chart_view = tk.Frame(self.container, bg=T.BG_MAIN)
        self.genre_view = tk.Frame(self.container, bg=T.BG_MAIN)
        self.fav_view = tk.Frame(self.container, bg=T.BG_MAIN)
        
        self.status_bar = tk.Label(root, text="Hazır", bd=0, relief=tk.FLAT, anchor=tk.W, 
                                   bg=T.BG_STATUS, fg=T.FG_SECONDARY, font=T.FONT_STATUS,
                                   padx=10, pady=4)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.vlc_instance = None
        self.player = None
        self.is_playing = False
        self.is_looping = False
        self.current_video_id = None
        self.total_duration = 0
        self.is_dragging_time = False
        
        if vlc:
            try:
                self.vlc_instance = vlc.Instance('--no-video', '--quiet')
                self.player = self.vlc_instance.media_player_new()
            except Exception as e:
                print(f"VLC Init Error: {e}")
                
        self.setup_player_view()

        self.setup_search_view()
        self.setup_chart_view()
        self.setup_genre_view()
        self.setup_fav_view()
        
        self.show_search_view()
        
        self.song_map = {} 
        self.chart_map = {} 
        self.fav_map = {} 
        self.favorites = self.load_favorites()
        
        self.config_file = CONFIG_FILE
        
        conf = load_config()
        encrypted_key = conf.get("lastfm_api_key", "")
        self.lastfm_api_key = decrypt_text(encrypted_key) if encrypted_key else ""
        
        self.stop_listing = False
        self.current_search_id = None

    def stop_current_listing(self):
        self.stop_listing = True
        self.current_search_id = None
        self.update_status("Durduruluyor...", "orange")
        
        if hasattr(self, 'btn_search'):
            self.root.after(0, lambda: self.lbl_search_progress.config(text=""))
            self.root.after(0, lambda: self.btn_search.config(text="Ara", bg=T.BTN_PRIMARY, fg=T.FG_PRIMARY))
            self.root.after(0, lambda: self.entry_artist.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.entry_search_limit.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.combo_search_mode.config(state="readonly"))

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()