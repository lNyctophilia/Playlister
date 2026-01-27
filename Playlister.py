import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
from ytmusicapi import YTMusic
import threading
import time
import locale
import json
import base64
import os
from tkinter import simpledialog
import webbrowser
import os

FAV_FILE = "favorites.json"
try:
    import vlc
    import yt_dlp
except ImportError:
    vlc = None
    yt_dlp = None


def parse_views(view_text):
    """
    '1.5M views', '300K plays' gibi metinleri sayıya çevirir.
    """
    if not view_text:
        return 0
    
    text = str(view_text).lower()
    for suffix in [" views", " plays", " hits", " subscribers", " abone"]:
        text = text.replace(suffix, "")
    text = text.strip()
    
    multiplier = 1
    if text.endswith("b"):
        multiplier = 1_000_000_000
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 1_000_000
        text = text[:-1]
    elif text.endswith("k"):
        multiplier = 1_000
        text = text[:-1]
        
    try:
        text = text.replace(",", ".")
        return int(float(text) * multiplier)
    except ValueError:
        return 0

# --- Simple Encryption Helper ---
# Not military grade, but prevents plain text reading
ENC_KEY = "PlaylisterAppSecretKey"

def encrypt_text(text):
    if not text: return ""
    try:
        # Simple XOR
        chars = []
        key_len = len(ENC_KEY)
        for i, char in enumerate(text):
            x = ord(char) ^ ord(ENC_KEY[i % key_len])
            chars.append(chr(x))
        return base64.b64encode("".join(chars).encode('utf-8')).decode('utf-8')
    except:
        return text

def decrypt_text(text):
    if not text: return ""
    try:
        # Decode Base64
        decoded = base64.b64decode(text.encode('utf-8')).decode('utf-8')
        chars = []
        key_len = len(ENC_KEY)
        for i, char in enumerate(decoded):
            x = ord(char) ^ ord(ENC_KEY[i % key_len])
            chars.append(chr(x))
        return "".join(chars)
    except:
        return ""


class App:
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
        
        # Treeview ve Başlıklar için Stil (Sütun çizgileri belirginleşsin)
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
                self.vlc_instance = vlc.Instance()
                self.player = self.vlc_instance.media_player_new()
            except Exception as e:
                print(f"VLC Init Error: {e}")
                
        self.setup_player_view()

        self.setup_search_view()
        self.setup_chart_view()
        self.setup_genre_view()
        self.setup_fav_view()
        
        # Varsayılan görünüm
        self.show_search_view()
        
        # Veri saklama
        self.song_map = {} 
        self.song_map = {} 
        self.chart_map = {} 
        self.fav_map = {} # Mode 4 map
        self.favorites = self.load_favorites()
        # Ikon tanımları artık gerekli değil, text rengi kullanılacak
        
        # Last.fm API Init
        self.config_file = "config.json"
        
        conf = self.load_config()
        encrypted_key = conf.get("lastfm_api_key", "")
        self.lastfm_api_key = decrypt_text(encrypted_key) if encrypted_key else ""
        
        # Setup Settings Button in UI (Wait for UI logic or insert here)
        # We need to insert the settings button in __init__ nav section
        
        # Startup check trigger removed
        
        self.stop_listing = False
        
    def stop_current_listing(self):
        self.stop_listing = True
        self.update_status("Durduruluyor...", "orange")
        
    def load_favorites(self):
        if os.path.exists(FAV_FILE):
             try:
                 with open(FAV_FILE, "r", encoding="utf-8") as f:
                     return json.load(f)
             except:
                 return []
        return []

    def save_favorites(self):
        try:
            with open(FAV_FILE, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Fav Save Error: {e}")

    def is_favorite(self, video_id):
        return any(f['video_id'] == video_id for f in self.favorites)

    def toggle_favorite(self, song_data):
        video_id = song_data.get('video_id')
        if self.is_favorite(video_id):
            # Remove
            self.favorites = [f for f in self.favorites if f['video_id'] != video_id]
            self.save_favorites()
            return False # Removed
        else:
            # Add
            # Minimize data to save
            saved_item = {
                "video_id": video_id,
                "title": song_data.get('title'),
                "artist": song_data.get('artist'),
                "album": song_data.get('album'),
                "views_text": song_data.get('views_text'),
                "duration": song_data.get('duration')
            }
            self.favorites.append(saved_item)
            self.save_favorites()
            return True # Added


        
    def update_status(self, text, color="black"):
        self.root.after(0, lambda: self.status_bar.config(text=text, fg=color))

    def set_active_mode_button(self, mode):
        # Reset all
        self.btn_mode_search.config(bg="#ddd", fg="#333", relief=tk.RAISED)
        self.btn_mode_chart.config(bg="#ddd", fg="#333", relief=tk.RAISED)
        self.btn_mode_genre.config(bg="#ddd", fg="#333", relief=tk.RAISED)
        self.btn_mode_fav.config(bg="#ddd", fg="#333", relief=tk.RAISED)
        
        if mode == "search":
            self.btn_mode_search.config(bg="#4CAF50", fg="white", relief=tk.SUNKEN)
        elif mode == "chart":
            self.btn_mode_chart.config(bg="#4CAF50", fg="white", relief=tk.SUNKEN)
        elif mode == "genre":
            self.btn_mode_genre.config(bg="#4CAF50", fg="white", relief=tk.SUNKEN)
        elif mode == "fav":
            self.btn_mode_fav.config(bg="#4CAF50", fg="white", relief=tk.SUNKEN)

    # ======================== GÖRÜNÜM YÖNETİMİ ========================
    def show_search_view(self):
        self.set_active_mode_button("search")
        self.chart_view.pack_forget()
        self.genre_view.pack_forget()
        self.fav_view.pack_forget()
        self.search_view.pack(fill="both", expand=True)
        self.update_status("Mod: Sanatçı & Şarkı Arama - Sanatçı adı girerek şarkılarını listeleyin.")

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Ayarlar")
        win.geometry("400x250")
        
        tk.Label(win, text="🔧 Uygulama Ayarları", font=("Helvetica", 14, "bold")).pack(pady=15)
        
        # Last.fm Section
        # ttk.LabelFrame 'padding' destekler
        lf_frame = ttk.LabelFrame(win, text="Last.fm API", padding=10)

        lf_frame.pack(fill=tk.X, padx=20, pady=10)
        
        status_text = "DURUM: Kayıtlı ✅" if self.lastfm_api_key else "DURUM: Kayıtlı Değil ❌"
        lbl_status = tk.Label(lf_frame, text=status_text, fg="green" if self.lastfm_api_key else "red", font=("Consolas", 10, "bold"))
        lbl_status.pack()
        
        btn_frame = tk.Frame(lf_frame)
        btn_frame.pack(pady=10)
        
        def delete_key():
            self.lastfm_api_key = ""
            self.save_config({"lastfm_api_key": ""})
            lbl_status.config(text="DURUM: Silindi ❌", fg="red")
            messagebox.showinfo("Bilgi", "API Anahtarı silindi.")
            win.destroy()
            # Eğer 3. Mod açıksa 1. moda at
            if self.genre_view.winfo_ismapped():
                self.show_search_view()
            
        def new_key():
            key = simpledialog.askstring("API Key", "Yeni API Key Girin:", parent=win)
            if key:
                self.lastfm_api_key = key.strip()
                enc = encrypt_text(self.lastfm_api_key)
                self.save_config({"lastfm_api_key": enc}) # Save encrypted
                lbl_status.config(text="DURUM: Güncellendi ✅", fg="green")
                messagebox.showinfo("Bilgi", "API Anahtarı güncellendi.")
                win.destroy()

        tk.Button(btn_frame, text="Yeni Gir", command=new_key, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Anahtarı Sil", command=delete_key, bg="#F44336", fg="white").pack(side=tk.LEFT, padx=5)

    # startup_check remove/deprecated




    def show_chart_view(self):
        self.set_active_mode_button("chart")
        self.search_view.pack_forget()
        self.genre_view.pack_forget()
        self.fav_view.pack_forget()
        self.chart_view.pack(fill="both", expand=True)
        self.update_status("Mod: Ülke Listeleri - Ülke seçimi yaparak en popüler sanatçıları görün.")

    def show_genre_view(self):
        # Mod 3'e girerken API Key Kontrolü
        if not self.lastfm_api_key:
            key = simpledialog.askstring("Zorunlu Kurulum", "Playlister Mod 3 Özellikleri için\nLütfen Last.fm API Anahtarınızı Giriniz:", parent=self.root)
            if key:
                self.lastfm_api_key = key.strip()
                enc = encrypt_text(self.lastfm_api_key)
                self.save_config({"lastfm_api_key": enc})
                messagebox.showinfo("Başarılı", "Anahtar şifrelenerek kaydedildi.")
            else:
                # Anahtar girilmezse moda geçiş yapma
                return

        self.set_active_mode_button("genre")
        self.search_view.pack_forget()
        self.chart_view.pack_forget()
        self.fav_view.pack_forget()
        self.genre_view.pack(fill="both", expand=True)
        self.update_status("Mod: Türe Göre (Beta) - Pop, Rock, Rap gibi türlerde popüler sanatçıları keşfedin.")

    def show_fav_view(self):
        self.set_active_mode_button("fav")
        self.search_view.pack_forget()
        self.chart_view.pack_forget()
        self.genre_view.pack_forget()
        self.fav_view.pack(fill="both", expand=True)
        self.update_status("Mod: Favoriler - Kaydettiğiniz şarkılar.")
        self.load_fav_ui()

    # ======================== PLAYER GÖRÜNÜMÜ ========================
    def setup_player_view(self):
        self.player_frame = tk.Frame(self.root, bg="#202020", height=80, bd=1, relief=tk.RAISED)
        self.player_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Grid Layout
        self.player_frame.columnconfigure(1, weight=1)
        
        # Sol: Play/Pause ve Kontroller
        btn_frame = tk.Frame(self.player_frame, bg="#202020")
        btn_frame.grid(row=0, column=0, rowspan=2, padx=10)
        
        self.btn_player_play = tk.Button(btn_frame, text="▶", font=("Arial", 14), width=4, 
                                         command=self.toggle_player_state, 
                                         bg="#202020", fg="white", bd=0, activebackground="#404040", activeforeground="white")
        self.btn_player_play.pack(side=tk.LEFT, padx=5)
        
        self.btn_player_loop = tk.Button(btn_frame, text="🔁", font=("Arial", 12),
                                         command=self.toggle_player_loop,
                                         bg="#202020", fg="gray", bd=0, activebackground="#404040", activeforeground="white")
        self.btn_player_loop.pack(side=tk.LEFT, padx=5)

        # Orta: Bilgi ve Slider
        info_frame = tk.Frame(self.player_frame, bg="#202020")
        info_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=(5,0))
        
        self.lbl_player_title = tk.Label(info_frame, text="Müzik Seçilmedi", bg="#202020", fg="white", font=("Helvetica", 10, "bold"))
        self.lbl_player_title.pack(anchor=tk.W)
        
        slider_frame = tk.Frame(self.player_frame, bg="#202020")
        slider_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=(0,5))
        
        self.var_time = tk.DoubleVar()
        self.scale_time = ttk.Scale(slider_frame, from_=0, to=100, variable=self.var_time, command=self.on_seek_start)
        self.scale_time.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Bind release event (ttk.Scale doesn't support built-in command for release, using bind)
        self.scale_time.bind("<ButtonRelease-1>", self.on_seek_end)
        
        self.lbl_player_time = tk.Label(slider_frame, text="00:00 / 00:00", bg="#202020", fg="#aaa", font=("Consolas", 8))
        self.lbl_player_time.pack(side=tk.LEFT, padx=5)

        # Sağ: Ses
        vol_frame = tk.Frame(self.player_frame, bg="#202020")
        vol_frame.grid(row=0, column=2, rowspan=2, padx=10)
        
        tk.Label(vol_frame, text="🔊", bg="#202020", fg="white").pack(side=tk.LEFT)
        
        self.scale_vol = ttk.Scale(vol_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=80, command=self.set_player_volume)
        self.scale_vol.set(70) # Default val
        self.scale_vol.pack(side=tk.LEFT, padx=5)
        
        # Timer Loop başlat
        self.update_player_loop()

    # ======================== ARAMA GÖRÜNÜMÜ ========================
    def setup_search_view(self):
        # Arama kutusu paneli
        top_frame = tk.Frame(self.search_view, pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(top_frame, text="Sanatçı Adı:").pack(side=tk.LEFT, padx=10)
        
        self.entry_artist = tk.Entry(top_frame, width=40)
        self.entry_artist.pack(side=tk.LEFT, padx=10)
        self.entry_artist.bind("<Return>", lambda e: self.start_search())
        
        self.btn_search = tk.Button(top_frame, text="Şarkıları Ara", command=self.start_search, bg="#2196F3", fg="white")
        self.btn_search.pack(side=tk.LEFT, padx=10)

        self.btn_search_stop = tk.Button(top_frame, text="Durdur", command=self.stop_current_listing, bg="#F44336", fg="white", state=tk.DISABLED)
        self.btn_search_stop.pack(side=tk.LEFT, padx=2)
        
        # Limit Seçimi
        tk.Label(top_frame, text="Limit:").pack(side=tk.LEFT, padx=(10, 2))
        self.entry_search_limit = tk.Entry(top_frame, width=5)
        self.entry_search_limit.insert(0, "30") # Varsayılan 30
        self.entry_search_limit.pack(side=tk.LEFT, padx=2)
        self.entry_search_limit.bind("<Return>", lambda e: self.start_search())

        # İlerleme Label
        self.lbl_search_progress = tk.Label(top_frame, text="", fg="gray")
        self.lbl_search_progress.pack(side=tk.LEFT, padx=10)
        
        # Filtre Butonları (Tab yerine)
        filter_frame = tk.Frame(self.search_view)
        filter_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        self.btn_tab_pop = tk.Button(filter_frame, text="🔥 Popülerlik", 
                                     command=lambda: self.switch_search_tab("pop"),
                                     font=("Helvetica", 9, "bold"),
                                     bg="#e0e0e0", fg="#333", relief=tk.RAISED)
        self.btn_tab_pop.pack(side=tk.LEFT, padx=5)
        
        self.btn_tab_views = tk.Button(filter_frame, text="📈 En Çok Dinlenenler", 
                                       command=lambda: self.switch_search_tab("views"),
                                       font=("Helvetica", 9, "bold"),
                                       bg="#e0e0e0", fg="#333", relief=tk.RAISED)
        self.btn_tab_views.pack(side=tk.LEFT, padx=5)

        self.btn_tab_smart = tk.Button(filter_frame, text="✨ Karma Liste", 
                                       command=lambda: self.switch_search_tab("smart"),
                                       font=("Helvetica", 9, "bold"),
                                       bg="#e0e0e0", fg="#333", relief=tk.RAISED)
        self.btn_tab_smart.pack(side=tk.LEFT, padx=5)

        # Liste Alanı
        self.list_container = tk.Frame(self.search_view)
        self.list_container.pack(expand=True, fill='both', padx=10, pady=5)
        
        # İki tabloyu da oluştur ama paketleme (pack) işlemini fonksiyona bırak
        self.frame_pop, self.tree_pop = self.create_song_treeview(self.list_container)
        self.frame_views, self.tree_views = self.create_song_treeview(self.list_container)
        self.frame_smart, self.tree_smart = self.create_song_treeview(self.list_container)
        
        # Varsayılan: Popülerlik
        self.switch_search_tab("pop")
        
        # Context Menu (Yedek olarak kalsın veya kaldırılabilir, kullanıcı buton istedi)
        # Ancak sağ tık yine de çalışabilir.
        
        self.context_menu_search = tk.Menu(self.root, tearoff=0)
        self.context_menu_search.add_command(label="▶ Müziği Oynat", command=self.play_selected_song)
        self.context_menu_search.add_command(label="🔗 Linki Kopyala", command=self.copy_link_selected_song)
        
        self.tree_pop.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_pop, self.context_menu_search))
        self.tree_views.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_views, self.context_menu_search))
        self.tree_smart.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_smart, self.context_menu_search))

    def switch_search_tab(self, tab_type):
        """Tablar arası geçiş ve buton renk yönetimi"""
        # Listeleri (Frame'leri) gizle
        self.frame_pop.pack_forget()
        self.frame_views.pack_forget()
        self.frame_smart.pack_forget()
        

        if tab_type == "pop":
            self.frame_pop.pack(fill=tk.BOTH, expand=True)
            # Renk güncelleme
            self.btn_tab_pop.config(bg="#FF5722", fg="white", relief=tk.SUNKEN)
            self.btn_tab_views.config(bg="#e0e0e0", fg="#333", relief=tk.RAISED)
            self.btn_tab_smart.config(bg="#e0e0e0", fg="#333", relief=tk.RAISED)
        elif tab_type == "views":
            self.frame_views.pack(fill=tk.BOTH, expand=True)
            # Renk güncelleme
            self.btn_tab_views.config(bg="#FF5722", fg="white", relief=tk.SUNKEN)
            self.btn_tab_pop.config(bg="#e0e0e0", fg="#333", relief=tk.RAISED)
            self.btn_tab_smart.config(bg="#e0e0e0", fg="#333", relief=tk.RAISED)
        else: # smart
            self.frame_smart.pack(fill=tk.BOTH, expand=True)
            self.btn_tab_smart.config(bg="#FF5722", fg="white", relief=tk.SUNKEN)
            self.btn_tab_pop.config(bg="#e0e0e0", fg="#333", relief=tk.RAISED)
            self.btn_tab_views.config(bg="#e0e0e0", fg="#333", relief=tk.RAISED)

    def create_song_treeview(self, parent):
        # Frame oluştur (Scrollbar + Treeview için container)
        frame = tk.Frame(parent)
        
        # 'İşlemler' kolonu eklendi (🔗  ▶)
        # "Sıra" kolonu eklendi
        # VideoID hidden column added
        columns = ("Sıra", "Şarkı", "Sanatçı", "Albüm", "Dinlenme", "Süre", "İşlemler", "VideoID")
        
        tree = ttk.Treeview(frame, columns=columns, show='headings', displaycolumns=("Sıra", "Şarkı", "Sanatçı", "Albüm", "Dinlenme", "Süre", "İşlemler"))
        for col in columns:
            tree.heading(col, text=col)
            
        tree.column("Sıra", width=40, anchor=tk.CENTER)
        tree.column("Şarkı", width=200)
        tree.column("Sanatçı", width=140)
        tree.column("Albüm", width=140)
        tree.column("Dinlenme", width=90)
        tree.column("Süre", width=60)
        tree.column("İşlemler", width=120, anchor=tk.CENTER) # Butonlar için kolon (Link, Play, Fav)
        
        # Scrollbar Ekle
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=sb.set)
        
        # Yerleşim
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Tıklama algılama (Sol tık)
        tree.bind("<ButtonRelease-1>", self.on_song_list_click)

        # Satır Renkleri (Zebra Efekti)
        tree.tag_configure('odd', background='#f9f9f9')
        tree.tag_configure('even', background='white')

        return frame, tree

    def start_search(self):
        artist_name = self.entry_artist.get()
        if not artist_name:
            messagebox.showwarning("Uyarı", "Lütfen bir sanatçı adı girin.")
            return
        
        # Eski verileri temizle
        for t in self.tree_pop.get_children(): self.tree_pop.delete(t)
        for t in self.tree_views.get_children(): self.tree_views.delete(t)
        for t in self.tree_smart.get_children(): self.tree_smart.delete(t)
        self.song_map.clear()
        
        try:
            limit = int(self.entry_search_limit.get())
            if limit < 20:
                limit = 20
                self.entry_search_limit.delete(0, tk.END)
                self.entry_search_limit.insert(0, "20")
            elif limit > 1000:
                limit = 1000
                self.entry_search_limit.delete(0, tk.END)
                self.entry_search_limit.insert(0, "1000")
        except:
            limit = 50
            self.entry_search_limit.delete(0, tk.END)
            self.entry_search_limit.insert(0, "50")
            
        self.btn_search.config(state=tk.DISABLED)
        self.entry_artist.config(state=tk.DISABLED)
        self.entry_search_limit.config(state=tk.DISABLED)
        self.stop_listing = False
        self.btn_search_stop.config(state=tk.NORMAL)
        self.update_status(f"Hazırlanıyor... (Limit: {limit})", "blue")
        threading.Thread(target=self.search_artist_thread, args=(artist_name, limit), daemon=True).start()

    def populate_tabs(self, pop_list, views_list, smart_list):
        def _job():

            
            def insert_to_tree(tree, data_list):
                 for i, song in enumerate(data_list):
                    tag = 'odd' if (i + 1) % 2 == 1 else 'even'
                    
                    is_fav = self.is_favorite(song['video_id'])
                    fav_icon = "♥" if is_fav else "♡"
                    action_text = f"🔗             ▶             {fav_icon}"

                    iid = tree.insert("", "end", values=(
                        str(i + 1), song['title'], song['artist'], song['album'], 
                        song['views_text'], song['duration'], action_text, song['video_id']
                    ), tags=(tag,))
                    # self.song_map[iid] = song['video_id'] # Removed shared map logic
            
            insert_to_tree(self.tree_pop, pop_list)
            insert_to_tree(self.tree_views, views_list)
            insert_to_tree(self.tree_smart, smart_list)
            
        self.root.after(0, _job)

    def search_artist_thread(self, artist_name, target_count):
        try:
            self.update_status(f"Sanatçı kimliği aranıyor...", "blue")
            results = self.yt.search(query=artist_name, filter="artists")
            
            if not results:
                artist_true_name = artist_name
            else:
                match = next((r for r in results if r['artist'].lower() == artist_name.lower()), None)
                artist_true_name = match['artist'] if match else results[0]['artist']
            
            # Daha geniş bir havuz çek (Target * 4)
            fetch_limit = min(target_count * 4, 1500) 
            self.update_status(f"Hedef: {artist_true_name}. Şarkılar taranıyor... (Geniş Tarama: {fetch_limit})")
            
            song_results = self.yt.search(query=f"{artist_true_name}", filter="songs", limit=fetch_limit)
            
            if not song_results:
                self.update_status("Şarkı bulunamadı.", "red")
                return
            
            all_songs = []
            processed_count = 0
            observed_video_ids = set()
            observed_titles = set()
            
            for song in song_results:
                if self.stop_listing:
                    self.update_status("Arama kullanıcı tarafından durduruldu.", "red")
                    break
                    
                artists = song.get('artists', [])
                a_names = [a['name'].lower() for a in artists]
                
                # Sanatçı doğrulama
                if artist_true_name.lower() not in a_names and artist_name.lower() not in a_names:
                    continue

                processed_count += 1
                if processed_count % 10 == 0:
                     self.root.after(0, lambda c=processed_count: self.lbl_search_progress.config(text=f"İşleniyor: {c}"))
                
                vid_id = song.get('videoId', '')
                title = song.get('title', 'Bilinmiyor')
                
                # Deduplication Check (Video ID)
                if vid_id in observed_video_ids:
                    continue
                
                # Deduplication Check (Title - fuzzy)
                # Keep the logic simple: if exact title exists, skip. 
                # Ideally, we want the most popular version, which comes first in search results.
                # Normalizing title: removing case
                norm_title = title.lower().strip()
                if norm_title in observed_titles:
                   continue
                
                observed_video_ids.add(vid_id)
                observed_titles.add(norm_title)

                data = {
                    "title": title,
                    "artist": ", ".join([a['name'] for a in artists]),
                    "album": song.get('album', {}).get('name', 'Single'),
                    "views_text": song.get('views', '0'),
                    "duration": song.get('duration', ''),
                    "video_id": vid_id
                }
                all_songs.append(data)
                
            total_found = len(all_songs)
            self.update_status(f"{total_found} aday şarkı bulundu. Listeler oluşturuluyor...", "orange")

            # --- List Generation Phase ---
            
            # 1. Popülerlik Listesi (API Sırası)
            pop_list = all_songs[:target_count]
            
            # 2. En Çok Dinlenenler (Views Sırası)
            for s in all_songs:
                s['_views_num'] = parse_views(s['views_text'])
            
            sorted_by_views = sorted(all_songs, key=lambda x: x['_views_num'], reverse=True)
            views_list = sorted_by_views[:target_count]
            
            # 3. Karma Liste (Smart Logic)
            views_ids = set(s['video_id'] for s in views_list)
            # Kesişim (Popülerlik sırasına göre)
            intersection = [s for s in pop_list if s['video_id'] in views_ids]
            
            needed = target_count - len(intersection)
            if needed < 0: needed = 0
            
            intersection_ids = set(s['video_id'] for s in intersection)
            unique_pop = [s for s in pop_list if s['video_id'] not in intersection_ids]
            unique_views = [s for s in views_list if s['video_id'] not in intersection_ids]
            
            count_pop = (needed + 1) // 2
            count_views = needed - count_pop
            
            smart_list = intersection + unique_pop[:count_pop] + unique_views[:count_views]
            
            # Eksik varsa tamamla (Havuzdan sıradaki en çok dinlenenlerden)
            if len(smart_list) < target_count:
                extra_needed = target_count - len(smart_list)
                used_ids = set(s['video_id'] for s in smart_list)
                extras = [s for s in sorted_by_views if s['video_id'] not in used_ids]
                smart_list.extend(extras[:extra_needed])

            self.populate_tabs(pop_list, views_list, smart_list)
            self.update_status(f"Tamamlandı. {target_count} şarki listelendi.", "green")

        except Exception as e:
            self.update_status(f"Hata: {e}", "red")
        finally:
            self.root.after(0, lambda: self.lbl_search_progress.config(text=""))
            self.root.after(0, lambda: self.btn_search.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_search_stop.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.entry_artist.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.entry_search_limit.config(state=tk.NORMAL))


    # ======================== CHART GÖRÜNÜMÜ ========================
    def setup_chart_view(self):
        ctrl_frame = tk.Frame(self.chart_view, pady=10)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(ctrl_frame, text="Ülke Seç:").pack(side=tk.LEFT, padx=10)
        
        # Geniş Kapsamlı Ülke Listesi
        self.countries = {
            "Global": "ZZ", "Türkiye": "TR", "ABD": "US", "İngiltere": "GB", "Almanya": "DE", 
            "Fransa": "FR", "Japonya": "JP", "Güney Kore": "KR", "Brezilya": "BR", "Hindistan": "IN",
            "Meksika": "MX", "Rusya": "RU", "İtalya": "IT", "İspanya": "ES", "Kanada": "CA",
            "Avustralya": "AU", "Hollanda": "NL", "Arjantin": "AR", "Polonya": "PL", "İsveç": "SE",
            "Tayland": "TH", "Endonezya": "ID", "Vietnam": "VN", "Filipinler": "PH", "Şili": "CL",
            "Kolombiya": "CO", "Peru": "PE", "Ukrayna": "UA", "Güney Afrika": "ZA", "Mısır": "EG",
            "Suudi Arabistan": "SA", "Birleşik Arap Emirlikleri": "AE", "Yunanistan": "GR", 
            "Portekiz": "PT", "Macaristan": "HU", "Çekya": "CZ", "Romanya": "RO", "İsrail": "IL",
            "İsviçre": "CH", "Avusturya": "AT", "Belçika": "BE", "Danimarka": "DK", "Finlandiya": "FI",
            "Norveç": "NO", "İrlanda": "IE", "Yeni Zelanda": "NZ", "Singapur": "SG", "Malezya": "MY",
            "Pakistan": "PK", "Nijerya": "NG", "Kenya": "KE", "Fas": "MA", "Cezayir": "DZ",
            "Irak": "IQ", "Sırbistan": "RS", "Hırvatistan": "HR", "Slovakya": "SK", "Bulgaristan": "BG",
            "Azerbaycan": "AZ", "Kazakistan": "KZ", "Özbekistan": "UZ", "Beyaz Rusya": "BY",
            "Lübnan": "LB", "Ürdün": "JO", "Kuveyt": "KW", "Katar": "QA", "Umman": "OM",
            "Tunus": "TN", "Slovenya": "SI", "Litvanya": "LT", "Letonya": "LV", "Estonya": "EE",
            "İzlanda": "IS", "Lüksemburg": "LU", "Kıbrıs": "CY", "Malta": "MT"
        }

        # Sistem dilini/ülkesini otomatik algıla
        local_name = "Türkiye" # Varsayılan
        try:
            locale.setlocale(locale.LC_ALL, '')
            sys_lang = locale.getlocale()[0]
            if sys_lang:
                local_code = sys_lang.split('_')[-1].upper()
                # Sözlükten ismini bul
                found_name = next((k for k, v in self.countries.items() if v == local_code), None)
                if found_name:
                    local_name = found_name
        except:
            pass
            
        # Listeyi Hazırla: [Lokal] -> [---] -> [Global] -> [Diğerleri Alfabetik]
        other_countries = [k for k in self.countries.keys() if k != local_name and k != "Global"]
        other_countries.sort() # Alfabetik sırala
        
        display_values = [local_name, "-------------------", "Global"] + other_countries

        self.combo_country = ttk.Combobox(ctrl_frame, values=display_values, state="readonly")
        self.combo_country.current(0) # İlk sıradaki (Lokal) seçili
        self.combo_country.pack(side=tk.LEFT, padx=10)

        # Limit Seçimi
        tk.Label(ctrl_frame, text="Limit:").pack(side=tk.LEFT, padx=(10, 2))
        self.entry_chart_limit = tk.Entry(ctrl_frame, width=5)
        self.entry_chart_limit.insert(0, "40") # Varsayılan 40
        self.entry_chart_limit.pack(side=tk.LEFT, padx=2)
        self.entry_chart_limit.bind("<Return>", lambda e: self.start_chart_load())
        
        self.btn_chart_load = tk.Button(ctrl_frame, text="Listele", command=self.start_chart_load, bg="#FF9800", fg="white", width=25)
        self.btn_chart_load.pack(side=tk.LEFT, padx=20)
        
        self.btn_chart_stop = tk.Button(ctrl_frame, text="Durdur", command=self.stop_current_listing, bg="#F44336", fg="white", width=10, state=tk.DISABLED)
        self.btn_chart_stop.pack(side=tk.LEFT, padx=5)
        
        self.lbl_chart_progress = tk.Label(ctrl_frame, text="", fg="gray")
        self.lbl_chart_progress.pack(side=tk.LEFT)
        
        # Sonuç Tablosu
        cols = ("Rank", "Sanatçı", "Toplam Dinlenme", "Trend", "Ara")
        self.tree_chart = ttk.Treeview(self.chart_view, columns=cols, show='headings')
        self.tree_chart.heading("Rank", text="Sıra")
        self.tree_chart.heading("Sanatçı", text="Sanatçı")
        self.tree_chart.heading("Toplam Dinlenme", text="Toplam Dinlenme (Views)")
        self.tree_chart.heading("Trend", text="Durum")
        self.tree_chart.heading("Ara", text="İşlem")
        
        self.tree_chart.column("Rank", width=50, anchor=tk.CENTER)
        self.tree_chart.column("Sanatçı", width=200)
        self.tree_chart.column("Toplam Dinlenme", width=150)
        self.tree_chart.column("Trend", width=100)
        self.tree_chart.column("Ara", width=60, anchor=tk.CENTER)
        
        sb = ttk.Scrollbar(self.chart_view, orient=tk.VERTICAL, command=self.tree_chart.yview)
        self.tree_chart.configure(yscroll=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_chart.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree_chart.bind("<ButtonRelease-1>", self.on_chart_list_click)

        # Zebra
        self.tree_chart.tag_configure('odd', background='#f9f9f9')
        self.tree_chart.tag_configure('even', background='white')

        self.context_menu_chart = tk.Menu(self.root, tearoff=0)
        self.context_menu_chart.add_command(label="Bu Sanatçıyı Ara", command=self.switch_to_artist_from_chart)
        self.tree_chart.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_chart, self.context_menu_chart))

    def _on_canvas_configure(self, event):
        # Canvas genişliği değiştikçe içteki frame'i de genişlet
        pass # Removed: self.canvas.itemconfig(self.canvas_frame_id, width=event.width)

    def _on_frame_configure(self, event):
        # İçerik boyutu değiştikçe scroll alanını güncelle
        pass # Removed: self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        pass # Removed: if self.chart_view.winfo_ismapped(): self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
    def direct_search_artist(self, artist_name):
        self.show_search_view()
        self.entry_artist.delete(0, tk.END)
        self.entry_artist.insert(0, artist_name)
        self.start_search()

    def start_chart_load(self):
        country_name = self.combo_country.get()
        
        if "---" in country_name:
            messagebox.showwarning("Seçim Hatası", "Lütfen listeden geçerli bir ülke seçiniz (Çizgiye tıklamayınız).")
            return

        country_code = self.countries.get(country_name, "TR")
        
        # Limit
        try:
            limit = int(self.entry_chart_limit.get())
            if limit > 40: 
                limit = 40
                self.entry_chart_limit.delete(0, tk.END)
                self.entry_chart_limit.insert(0, "40")
        except:
            limit = 40
            self.entry_chart_limit.delete(0, tk.END)
            self.entry_chart_limit.insert(0, "40")

        self.btn_chart_load.config(state=tk.DISABLED, text="Veriler Çekiliyor...")
        self.combo_country.config(state=tk.DISABLED)
        self.entry_chart_limit.config(state=tk.DISABLED)
        self.update_status(f"{country_name} listeleri ve dinlenme sayıları çekiliyor... (Limit: {limit})", "blue")
        
        # Temizle
        for item in self.tree_chart.get_children():
            self.tree_chart.delete(item)
        self.chart_map.clear()
            
        self.chart_map.clear()
        
        self.stop_listing = False
        self.btn_chart_stop.config(state=tk.NORMAL)
        threading.Thread(target=self.load_charts_thread, args=(country_code, limit), daemon=True).start()

    def update_chart_progress(self, text, insert_item=None):
        def _update():
            self.lbl_chart_progress.config(text=text)
            if insert_item:
                count = len(self.tree_chart.get_children())
                tag_zebra = 'odd' if (count + 1) % 2 == 1 else 'even'

                iid = self.tree_chart.insert("", "end", values=(
                    insert_item['rank'], insert_item['title'], insert_item['views_text'], insert_item['trend'], "🔍"
                ), tags=(tag_zebra,))
                self.chart_map[iid] = insert_item['title']
                # self.tree_chart.see(iid) # Otomatik kaydır iptal edildi
        self.root.after(0, _update)

    def reset_chart_ui(self):
        def _reset():
            self.btn_chart_load.config(state=tk.NORMAL, text="Listele")
            self.lbl_chart_progress.config(text="")
            self.combo_country.config(state="readonly")
            self.entry_chart_limit.config(state=tk.NORMAL)
            self.btn_chart_stop.config(state=tk.DISABLED)
        self.root.after(0, _reset)

    def load_charts_thread(self, country_code, limit):
        try:
            charts = self.yt.get_charts(country=country_code)
            
            artist_data = charts.get('artists')
            artists = []
            if isinstance(artist_data, dict):
                artists = artist_data.get('items', [])
            elif isinstance(artist_data, list):
                artists = artist_data
            
            if not artists:
                self.update_status("Liste bulunamadı.", "red")
                self.reset_chart_ui()
                return

            # Limiti uygula
            if limit > 0:
                artists = artists[:limit]

            total_artists = len(artists)
            self.update_status(f"Toplam {total_artists} sanatçı bulundu. Detaylı dinlenme verileri çekiliyor...", "orange")

            for idx, art in enumerate(artists):
                if self.stop_listing:
                    self.update_status("Listeleme durduruldu.", "red")
                    break

                browse_id = art.get('browseId')
                name = art.get('title', 'Bilinmiyor')
                views_text = "..."
                
                # İlerleme bilgisi
                progress_msg = f"İşleniyor ({idx+1}/{total_artists}): {name}"
                
                if browse_id:
                    try:
                        # Dinlenme sayısı için profil detayı
                        details = self.yt.get_artist(browse_id)
                        v_val = details.get('views')
                        # 'None' string veya None tipi kontrolü
                        if not v_val or str(v_val).lower() == 'none':
                             views_text = 'Veri Yok'
                        else:
                             views_text = v_val
                    except:
                        views_text = "Hata"
                
                # Trend çevirisi
                raw_trend = art.get('trend', 'neutral')
                trend_map = {
                    "up": "Artış",
                    "down": "Azalış",
                    "neutral": "Sabit"
                }
                trend_display = trend_map.get(str(raw_trend).lower(), raw_trend)
                if isinstance(trend_display, str):
                    trend_display = trend_display.capitalize()

                item_data = {
                    "rank": art.get('rank', str(idx+1)),
                    "title": name,
                    "views_text": views_text,
                    "trend": trend_display
                }
                
                # Her satırı anında ekle (Canlı akış)
                self.update_chart_progress(progress_msg, insert_item=item_data)

            self.update_status(f"Tamamlandı! {total_artists} sanatçı listelendi.", "green")
            
        except Exception as e:
            self.update_status(f"Hata: {e}", "red")
        finally:
            self.reset_chart_ui()

    # ======================== GENRE GÖRÜNÜMÜ (BETA) ========================
    def setup_genre_view(self):
        ctrl_frame = tk.Frame(self.genre_view, pady=10)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Tür Seçimi
        tk.Label(ctrl_frame, text="Tür Seç:").pack(side=tk.LEFT, padx=10)
        self.combo_genre = ttk.Combobox(ctrl_frame, values=[
            "Rock", "Pop", "Rap", "Arabesk", "Elektronik", "Indie", "Metal", "Jazz", "Hip Hop", "Klasik", "Halk Müziği"
        ], state="readonly", width=15)
        self.combo_genre.current(1) # Pop varsayılan
        self.combo_genre.pack(side=tk.LEFT, padx=5)
        
        # Ülke Seçimi (Mevcut 'countries' sözlüğünü kullanacağız, ama combo_genre için ayrı bir combo)
        tk.Label(ctrl_frame, text="Ülke:").pack(side=tk.LEFT, padx=10)
        
        # Chart view'daki listeyi kopyalayalım veya yeniden üretelim
        # self.countries zaten init içinde tanımlı
        local_name = "Türkiye"
        other_countries = [k for k in self.countries.keys() if k != local_name and k != "Global"]
        other_countries.sort()
        display_values = [local_name, "Global"] + other_countries
        
        self.combo_genre_country = ttk.Combobox(ctrl_frame, values=display_values, state="readonly", width=15)
        self.combo_genre_country.current(0) # Türkiye
        self.combo_genre_country.pack(side=tk.LEFT, padx=5)

        # Limit Seçimi
        tk.Label(ctrl_frame, text="Limit:").pack(side=tk.LEFT, padx=(10, 2))
        self.entry_genre_limit = tk.Entry(ctrl_frame, width=5)
        self.entry_genre_limit.insert(0, "50") # Varsayılan 50
        self.entry_genre_limit.pack(side=tk.LEFT, padx=2)
        self.entry_genre_limit.bind("<Return>", lambda e: self.start_genre_load())
        
        # Buton
        self.btn_genre_load = tk.Button(ctrl_frame, text="Sanatçıları Listele (Last.fm)", 
                                        command=self.start_genre_load, 
                                        bg="#b90000", fg="white", width=25)
        self.btn_genre_load.pack(side=tk.LEFT, padx=10)

        self.btn_genre_stop = tk.Button(ctrl_frame, text="Durdur", command=self.stop_current_listing, bg="#F44336", fg="white", width=10, state=tk.DISABLED)
        self.btn_genre_stop.pack(side=tk.LEFT, padx=5)
        
        self.lbl_genre_progress = tk.Label(ctrl_frame, text="", fg="gray")
        self.lbl_genre_progress.pack(side=tk.LEFT)

        
        # Liste
        cols = ("Rank", "Sanatçı", "Tür", "Toplam Dinlenme", "Ara")
        self.tree_genre = ttk.Treeview(self.genre_view, columns=cols, show='headings')
        self.tree_genre.heading("Rank", text="Sıra")
        self.tree_genre.heading("Sanatçı", text="Sanatçı")
        self.tree_genre.heading("Tür", text="Kategori")
        self.tree_genre.heading("Toplam Dinlenme", text="Toplam Dinlenme")
        self.tree_genre.heading("Ara", text="İşlem")
        
        self.tree_genre.column("Rank", width=50, anchor=tk.CENTER)
        self.tree_genre.column("Sanatçı", width=200)
        self.tree_genre.column("Tür", width=100)
        self.tree_genre.column("Toplam Dinlenme", width=150)
        self.tree_genre.column("Ara", width=60, anchor=tk.CENTER)
        
        sb = ttk.Scrollbar(self.genre_view, orient=tk.VERTICAL, command=self.tree_genre.yview)
        self.tree_genre.configure(yscroll=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_genre.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Tıklama ve Context
        self.tree_genre.bind("<ButtonRelease-1>", self.on_genre_list_click)
        self.tree_genre.tag_configure('odd', background='#f9f9f9')
        self.tree_genre.tag_configure('even', background='white')
        
        # Sağ tık aynı menüyü kullanabilir (Chart ile benzer)
        self.tree_genre.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_genre, self.context_menu_chart))

    def on_genre_list_click(self, event):
        """Genre listesindeki arama butonuna tıklamayı algılar"""
        try:
            tree = event.widget
            region = tree.identify_region(event.x, event.y)
            if region != "cell": return
            
            # Kolon kontrolü (#5 'Ara' kolonu mu?)
            col = tree.identify_column(event.x)
            if col == "#5":
                item_id = tree.identify_row(event.y)
                if not item_id: return
                self.switch_to_artist_from_genre(override_item_id=item_id)
        except:
            pass
            
    def switch_to_artist_from_genre(self, override_item_id=None):
        if override_item_id:
            item_id = override_item_id
        else:
            sel = self.tree_genre.selection()
            if not sel: return
            item_id = sel[0]
            
        # Chart map ile aynı mantıkta tek bir map kullansak da olur ama karışmasın
        # Item values'dan alalım: values=(Rank, Artist, ...)
        val = self.tree_genre.item(item_id)['values']
        artist_name = val[1] # 2. kolon Sanatçı
        
        if artist_name:
            self.show_search_view()
            self.entry_artist.delete(0, tk.END)
            self.entry_artist.insert(0, artist_name)
            self.start_search()

    def set_lastfm_key(self):
        self.open_settings()
        
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_config(self, data):
        try:
            # Mevcut configi koru, üzerine yaz
            current = self.load_config()
            current.update(data)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=4)
        except Exception as e:
            print(f"Config save error: {e}")


    def start_genre_load(self):
        genre = self.combo_genre.get()
        country_name = self.combo_genre_country.get()

        try:
            limit = int(self.entry_genre_limit.get())
            if limit < 10:
                limit = 10
                self.entry_genre_limit.delete(0, tk.END)
                self.entry_genre_limit.insert(0, "10")
            elif limit > 200:
                limit = 200
                self.entry_genre_limit.delete(0, tk.END)
                self.entry_genre_limit.insert(0, "200")
        except:
            limit = 50
            self.entry_genre_limit.delete(0, tk.END)
            self.entry_genre_limit.insert(0, "50")
        
        self.btn_genre_load.config(state=tk.DISABLED, text="Taranıyor...")
        self.combo_genre.config(state=tk.DISABLED)
        self.combo_genre_country.config(state=tk.DISABLED)
        self.entry_genre_limit.config(state=tk.DISABLED)
        self.update_status(f"{country_name} için {genre} listeleri taranıyor... (Limit: {limit})", "purple")
        
        for item in self.tree_genre.get_children():
            self.tree_genre.delete(item)
            
        self.stop_listing = False
        self.btn_genre_stop.config(state=tk.NORMAL)
        threading.Thread(target=self.load_genre_thread, args=(genre, country_name, limit), daemon=True).start()

    def update_genre_progress(self, text, insert_item=None):
        def _update():
            self.lbl_genre_progress.config(text=text)
            if insert_item:
                count = len(self.tree_genre.get_children())
                tag_zebra = 'odd' if (count + 1) % 2 == 1 else 'even'
                self.tree_genre.insert("", "end", values=(
                    insert_item['rank'], insert_item['artist'], insert_item['genre'], 
                    insert_item['views_text'], "🔍"
                ), tags=(tag_zebra,))
        self.root.after(0, _update)

    def load_genre_thread(self, genre, country_name, limit):
        try:
            # 1. API Anahtarı Kontrolü
            if not getattr(self, 'lastfm_api_key', None):
                self.update_status("Hata: API Anahtarı eksik! Ayarlar'dan ekleyin.", "red")
                return


            # Tag Belirleme
            tag_query = genre.lower()
            if country_name == "Türkiye":
                # Özel Mappings
                mapping = {
                    "Pop": "turkish pop",
                    "Rock": "turkish rock",
                    "Rap": "turkish rap",
                    "Arabesk": "arabesk",
                    "Elektronik": "turkish electronic",
                    "Indie": "turkish indie",
                    "Metal": "turkish metal",
                    "Jazz": "turkish jazz",
                    "Hip Hop": "turkish hip hop",
                    "Halk Müziği": "turkish folk",
                    "Klasik": "turkish classical"
                }
                tag_query = mapping.get(genre, "turkish " + genre.lower())
            
            self.update_status(f"Last.fm üzerinden '{tag_query}' etiketi taranıyor...", "purple")
            
            # API İsteği
            # API Key buraya girilmeli
            API_KEY = getattr(self, 'lastfm_api_key', '') 
            
            if not API_KEY:
                # Varsayılan deneme (Eğer kullanıcı kod içine yazdıysa)
                # self.lastfm_api_key = "YOUR_API_KEY"
                # Eğer hala yoksa:
                self.update_status("Hata: Last.fm API Key girilmedi. Ayarlardan tanımlayın.", "red")
                return

            url = "http://ws.audioscrobbler.com/2.0/"
            params = {
                'method': 'tag.gettopartists',
                'tag': tag_query,
                'api_key': API_KEY,
                'format': 'json',
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'error' in data:
                self.update_status(f"Last.fm Hatası: {data.get('message')}", "red")
                return
                
            artists = data.get('topartists', {}).get('artist', [])
            
            if not artists:
                self.update_status("Bu türde sanatçı bulunamadı.", "red")
                return

            self.update_status(f"{len(artists)} sanatçı bulundu. Listeleniyor...", "orange")
            
            for i, art in enumerate(artists):
                if self.stop_listing:
                    self.update_status("Tür taraması durduruldu.", "red")
                    break
                    
                name = art.get('name')
                if not name: continue

                # YouTube Music'ten Analiz
                views_text = "..."
                try:
                    # 1. İsmi Ara (YT Music Artist ID bulmak için)
                    search_res = self.yt.search(name, filter="artists", limit=1)
                    if search_res:
                        b_id = search_res[0]['browseId']
                        # 2. Detay Çek
                        details = self.yt.get_artist(b_id)
                        v_val = details.get('views')
                        
                        if not v_val or str(v_val).lower() == 'none':
                             views_text = 'Veri Yok'
                        else:
                             views_text = v_val
                    else:
                        views_text = "Bulunamadı"
                except Exception as e:
                    views_text = "Hata"

                item = {
                    "rank": str(i+1),
                    "artist": name,
                    "genre": genre,
                    "views_text": views_text
                }
                
                self.update_genre_progress(f"Eklendi ({i+1}/{len(artists)}): {name}", insert_item=item)
                # API limitine takılmamak ve UI donmasını engellemek için biraz bekle
                # Her sorgu 2 request yaptığı için biraz yavaş olabilir.
                pass
                
            self.update_status(f"Tamamlandı. {len(artists)} sanatçı başarıyla çekildi.", "green")

        except Exception as e:
            self.update_status(f"Hata: {e}", "red")
        finally:
            self.root.after(0, lambda: self.btn_genre_load.config(state=tk.NORMAL, text="Sanatçıları Listele"))
            self.root.after(0, lambda: self.btn_genre_stop.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.lbl_genre_progress.config(text=""))
            self.root.after(0, lambda: self.combo_genre.config(state="readonly"))
            self.root.after(0, lambda: self.combo_genre_country.config(state="readonly"))
            self.root.after(0, lambda: self.entry_genre_limit.config(state=tk.NORMAL))
            

            
    
    # ======================== FAV GÖRÜNÜMÜ ========================
    def setup_fav_view(self):
        # Üst Panel
        top_frame = tk.Frame(self.fav_view, pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(top_frame, text="Favorilerim", font=("Helvetica", 12, "bold")).pack(side=tk.LEFT, padx=10)
        
        self.btn_refresh_fav = tk.Button(top_frame, text="Yenile", command=self.load_fav_ui, bg="#2196F3", fg="white")
        self.btn_refresh_fav.pack(side=tk.RIGHT, padx=10)

        # Liste
        # Mod 1 ile aynı kolonlar
        cols = ("Sıra", "Şarkı", "Sanatçı", "Albüm", "Dinlenme", "Süre", "İşlemler")
        self.tree_fav = ttk.Treeview(self.fav_view, columns=cols, show='headings')
        
        for col in cols:
            self.tree_fav.heading(col, text=col)
            
        self.tree_fav.column("Sıra", width=40, anchor=tk.CENTER)
        self.tree_fav.column("Şarkı", width=200)
        self.tree_fav.column("Sanatçı", width=140)
        self.tree_fav.column("Albüm", width=140)
        self.tree_fav.column("Dinlenme", width=90)
        self.tree_fav.column("Süre", width=60)
        self.tree_fav.column("İşlemler", width=120, anchor=tk.CENTER)
        
        sb = ttk.Scrollbar(self.fav_view, orient=tk.VERTICAL, command=self.tree_fav.yview)
        self.tree_fav.configure(yscroll=sb.set)
        
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_fav.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree_fav.bind("<ButtonRelease-1>", self.on_fav_list_click)
        self.tree_fav.tag_configure('odd', background='#f9f9f9')
        self.tree_fav.tag_configure('even', background='white')
        
    def load_fav_ui(self):
        # Temizle
        for item in self.tree_fav.get_children():
            self.tree_fav.delete(item)
        self.fav_map.clear()
        
        # Verileri al ve sırala (Sanatçıya göre A-Z)
        favs = self.load_favorites()
        if not favs:
            self.update_status("Favori listeniz boş.", "blue")
            return
            
        # Sanatçı ismiyle sırala
        sorted_favs = sorted(favs, key=lambda x: x.get('artist', '').lower())
        
        action_text = "🔗             ▶             ♥" # Favoriler listesinde zaten favori olduğu için dolu kalp
        
        for i, song in enumerate(sorted_favs):
             tag = 'odd' if (i + 1) % 2 == 1 else 'even'
             iid = self.tree_fav.insert("", "end", values=(
                 str(i + 1), 
                 song.get('title', ''), 
                 song.get('artist', ''), 
                 song.get('album', ''), 
                 song.get('views_text', ''), 
                 song.get('duration', ''), 
                 action_text
             ), tags=(tag,))
             self.fav_map[iid] = song 
             # Map stores full object to allow easy access

        self.update_status(f"Favoriler listelendi: {len(favs)} şarkı.", "green")

    def on_fav_list_click(self, event):
        try:
            tree = event.widget
            region = tree.identify_region(event.x, event.y)
            if region != "cell": return
            
            col = tree.identify_column(event.x)
            # #7 -> İşlemler
            if col == "#7":
                item_id = tree.identify_row(event.y)
                if not item_id: return
                
                bbox = tree.bbox(item_id, col)
                if not bbox: return
                x, y, w, h = bbox
                click_x = event.x - x
                
                # 3 Buton: [Link] [Play] [Fav]
                # Yaklaşık 3'e böl
                section = w / 3
                
                song_data = self.fav_map.get(item_id)
                if not song_data: return
                video_id = song_data.get('video_id')

                if click_x < section:
                    # Link
                    self.copy_link_by_id(video_id)
                elif click_x < section * 2:
                    # Play
                    title = f"{song_data.get('title')} - {song_data.get('artist')}"
                    self.play_music_start(video_id, title)
                else:
                    # Remove Fav
                    res = messagebox.askyesno("Onay", "Bu şarkıyı favorilerden kaldırmak istiyor musunuz?")
                    if res:
                        self.toggle_favorite(song_data)
                        self.tree_fav.delete(item_id)
                        del self.fav_map[item_id]
                        # Refresh visual indexes logic implied but not strictly necessary for simple remove
                        
        except Exception as e:
            print(f"Fav Click Error: {e}")



    # ======================== ORTAK ========================
    # ======================== TIKLAMA VE AKSİYONLAR ========================
    def on_song_list_click(self, event):
        """Şarkı listesindeki ikonlara tıklamayı algılar"""
        try:
            tree = event.widget
            region = tree.identify_region(event.x, event.y)
            if region != "cell": return
            
            # Kolon kontrolü (#7 'İşlemler' kolonu mu?)
            col = tree.identify_column(event.x)
            if col == "#7":
                item_id = tree.identify_row(event.y)
                if not item_id: return
                
                # Koordinat hesapla
                bbox = tree.bbox(item_id, col)
                if not bbox: return
                
                # bbox -> (x, y, w, h)
                x, y, w, h = bbox
                click_relative_x = event.x - x
                
                # Hücreyi üçe böl: Link, Play, Fav
                # Text: "🔗   ▶   ♥"
                section = w / 3
                
                vals = tree.item(item_id)['values']
                # Make sure we have enough values
                if len(vals) < 8: return

                video_id = vals[7] # Hidden column
                if not video_id: return

                if click_relative_x < section:
                    self.copy_link_by_id(video_id)
                elif click_relative_x < section * 2:
                    # Play
                    song_title = f"{vals[1]} - {vals[2]}"
                    self.play_music_start(video_id, song_title)
                else:
                    # Fav Toggle
                    # Mevcut veriyi al
                    # Construct song data based on columns
                    # ("Sıra", "Şarkı", "Sanatçı", "Albüm", "Dinlenme", "Süre", "İşlemler", "VideoID")
                    song_data = {
                        "video_id": video_id,
                        "title": vals[1],
                        "artist": vals[2],
                        "album": vals[3],
                        "views_text": vals[4],
                        "duration": vals[5]
                    }
                    
                    is_added = self.toggle_favorite(song_data)
                    
                    # UI güncelle
                    new_icon = "♥" if is_added else "♡"
                    new_action_text = f"🔗             ▶             {new_icon}"
                    
                    # Update Treeview Cell
                    # Treeview set metodu: item, column_id, value
                    tree.set(item_id, "İşlemler", new_action_text)
                    
                    if is_added:
                        self.update_status("Favorilere eklendi.", "green")
                    else:
                        self.update_status("Favorilerden çıkarıldı.", "orange")
        except Exception as e:
            print(f"Click Error: {e}")

    def on_chart_list_click(self, event):
        """Chart listesindeki arama butonuna tıklamayı algılar"""
        try:
            tree = event.widget
            region = tree.identify_region(event.x, event.y)
            if region != "cell": return
            
            # Kolon kontrolü (#5 'Ara' kolonu mu?)
            col = tree.identify_column(event.x)
            if col == "#5":
                item_id = tree.identify_row(event.y)
                if not item_id: return
                self.switch_to_artist_from_chart(override_item_id=item_id)
        except:
            pass

    def show_context_menu(self, event, tree, menu):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            menu.post(event.x_root, event.y_root)

    def play_by_id(self, video_id):
        if video_id:
            webbrowser.open(f"https://music.youtube.com/watch?v={video_id}")

    def copy_link_by_id(self, video_id):
        if video_id:
            url = f"https://music.youtube.com/watch?v={video_id}"
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            messagebox.showinfo("Bilgi", "Link kopyalandı!")

    def play_selected_song(self):
        for tree in [self.tree_pop, self.tree_views, self.tree_smart]:
             sel_ids = tree.selection()
             if sel_ids:
                 vals = tree.item(sel_ids[0])['values']
                 if len(vals) >= 8:
                     title = f"{vals[1]} - {vals[2]}"
                     video_id = vals[7]
                     if video_id:
                         self.play_music_start(video_id, title)
                 return

    def copy_link_selected_song(self):
        for tree in [self.tree_pop, self.tree_views, self.tree_smart]:
            sel = tree.selection()
            if sel:
                vals = tree.item(sel[0])['values']
                if len(vals) >= 8:
                    self.copy_link_by_id(vals[7])
                return

    def switch_to_artist_from_chart(self, override_item_id=None):
        if override_item_id:
            item_id = override_item_id
        else:
            sel = self.tree_chart.selection()
            if not sel: return
            item_id = sel[0]
            
        artist_name = self.chart_map.get(item_id)
        if artist_name:
            self.show_search_view()
            self.entry_artist.delete(0, tk.END)
            self.entry_artist.insert(0, artist_name)
            self.start_search()

    def get_selected_item_data(self, map_data, trees):
        for tree in trees:
            sel = tree.selection()
            if sel: return map_data.get(sel[0])
        return None

    # ======================== PLAYER MANTIK ========================
    def play_music_start(self, video_id, title_info="Yükleniyor..."):
        if not self.player:
            # VLC yoksa tarayıcıda aç
            messagebox.showinfo("Player Hatası", "VLC Modülü bulunamadı. Lütfen VLC Player ve python-vlc kurulumunu yapın.\nŞarkı tarayıcıda açılıyor.")
            webbrowser.open(f"https://music.youtube.com/watch?v={video_id}")
            return
            
        self.lbl_player_title.config(text=f"Yükleniyor: {title_info}...")
        self.btn_player_play.config(text="⏳")
        
        threading.Thread(target=self.player_load_thread, args=(video_id, title_info), daemon=True).start()

    def player_load_thread(self, video_id, title_info):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'noplaylist': True,
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_id, download=False)
                url = info.get('url')
                duration = info.get('duration', 0)
                
            if url:
                self.root.after(0, lambda: self.start_vlc_stream(url, duration, title_info))
            else:
                self.update_status("Ses linki alınamadı.", "red")
        except Exception as e:
            self.update_status(f"Oynatma hatası: {e}", "red")
            self.root.after(0, lambda: self.btn_player_play.config(text="▶"))

    def start_vlc_stream(self, url, duration, title):
        self.player.stop()
        media = self.vlc_instance.media_new(url)
        self.player.set_media(media)
        self.player.play()
        
        self.is_playing = True
        self.total_duration = duration
        self.lbl_player_title.config(text=title)
        self.btn_player_play.config(text="⏸")
        self.scale_time.config(to=duration)
        
        # Volume set (VLC bazen resetler)
        vol = int(self.scale_vol.get())
        self.player.audio_set_volume(vol)

    def toggle_player_state(self):
        if not self.player: return
        if self.is_playing:
            self.player.pause()
            self.btn_player_play.config(text="▶")
            self.is_playing = False
        else:
            self.player.play()
            self.btn_player_play.config(text="⏸")
            self.is_playing = True

    def toggle_player_loop(self):
        self.is_looping = not self.is_looping
        if self.is_looping:
            self.btn_player_loop.config(fg="#4CAF50") # Yeşil
        else:
            self.btn_player_loop.config(fg="gray")

    def set_player_volume(self, val):
        if self.player:
            self.player.audio_set_volume(int(float(val)))

    def on_seek_start(self, val):
        self.is_dragging_time = True

    def on_seek_end(self, event):
        if self.player:
            time_sec = self.var_time.get()
            self.player.set_time(int(time_sec * 1000))
        self.is_dragging_time = False

    def update_player_loop(self):
        if self.player:
            # Durum kontrol
            state = self.player.get_state()
            
            # Müzik bitti mi?
            if state == vlc.State.Ended:
                if self.is_looping:
                    self.player.stop()
                    self.player.play()
                else:
                    self.is_playing = False
                    self.btn_player_play.config(text="▶")
                    # self.player.stop() # Stop yapınca siyah ekran/boşluk olabilir, pause daha iyi?
                    # VLC'de Stop yapınca süre 0'a döner, pause olduğu yerde kalır.
                    # Bittiği için stop mantıklı.

            # Süre güncelle (Sadece kullanıcı kaydırmıyorsa ve oynuyorsa)
            if not self.is_dragging_time and state == vlc.State.Playing:
                # VLC milliseconds döner
                current_ms = self.player.get_time()
                if current_ms >= 0:
                    current_sec = current_ms / 1000
                    self.var_time.set(current_sec)
                    
                    # Label güncelle
                    cur_str = time.strftime('%M:%S', time.gmtime(current_sec))
                    tot_str = time.strftime('%M:%S', time.gmtime(self.total_duration))
                    self.lbl_player_time.config(text=f"{cur_str} / {tot_str}")
        
        self.root.after(500, self.update_player_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()