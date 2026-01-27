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
        self.root.title("Playlister - YouTube Music")
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
        
        # Status Bar
        self.status_bar = tk.Label(root, text="Hazır", bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#f0f0f0", font=("Consolas", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.setup_search_view()
        self.setup_chart_view()
        self.setup_genre_view()
        
        # Varsayılan görünüm
        self.show_search_view()
        
        # Veri saklama
        self.song_map = {} 
        self.song_map = {} 
        self.chart_map = {} 
        # Ikon tanımları artık gerekli değil, text rengi kullanılacak
        
        # Last.fm API Init
        self.config_file = "config.json"
        
        conf = self.load_config()
        encrypted_key = conf.get("lastfm_api_key", "")
        self.lastfm_api_key = decrypt_text(encrypted_key) if encrypted_key else ""
        
        # Setup Settings Button in UI (Wait for UI logic or insert here)
        # We need to insert the settings button in __init__ nav section
        
        # Startup check trigger removed
        # self.root.after(500, self.startup_check)


        
    def update_status(self, text, color="black"):
        self.root.after(0, lambda: self.status_bar.config(text=text, fg=color))

    def set_active_mode_button(self, mode):
        # Reset all
        self.btn_mode_search.config(bg="#ddd", fg="#333", relief=tk.RAISED)
        self.btn_mode_chart.config(bg="#ddd", fg="#333", relief=tk.RAISED)
        self.btn_mode_genre.config(bg="#ddd", fg="#333", relief=tk.RAISED)
        
        if mode == "search":
            self.btn_mode_search.config(bg="#4CAF50", fg="white", relief=tk.SUNKEN)
        elif mode == "chart":
            self.btn_mode_chart.config(bg="#4CAF50", fg="white", relief=tk.SUNKEN)
        elif mode == "genre":
            self.btn_mode_genre.config(bg="#4CAF50", fg="white", relief=tk.SUNKEN)

    # ======================== GÖRÜNÜM YÖNETİMİ ========================
    def show_search_view(self):
        self.set_active_mode_button("search")
        self.chart_view.pack_forget()
        self.genre_view.pack_forget()
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
        self.genre_view.pack(fill="both", expand=True)
        self.update_status("Mod: Türe Göre (Beta) - Pop, Rock, Rap gibi türlerde popüler sanatçıları keşfedin.")

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
        
        self.btn_tab_pop = tk.Button(filter_frame, text="🔥 Popülerlik (Varsayılan)", 
                                     command=lambda: self.switch_search_tab("pop"),
                                     font=("Helvetica", 9, "bold"),
                                     bg="#e0e0e0", fg="#333", relief=tk.RAISED)
        self.btn_tab_pop.pack(side=tk.LEFT, padx=5)
        
        self.btn_tab_views = tk.Button(filter_frame, text="📈 En Çok Dinlenenler", 
                                       command=lambda: self.switch_search_tab("views"),
                                       font=("Helvetica", 9, "bold"),
                                       bg="#e0e0e0", fg="#333", relief=tk.RAISED)
        self.btn_tab_views.pack(side=tk.LEFT, padx=5)

        # Liste Alanı
        self.list_container = tk.Frame(self.search_view)
        self.list_container.pack(expand=True, fill='both', padx=10, pady=5)
        
        # İki tabloyu da oluştur ama paketleme (pack) işlemini fonksiyona bırak
        self.frame_pop, self.tree_pop = self.create_song_treeview(self.list_container)
        self.frame_views, self.tree_views = self.create_song_treeview(self.list_container)
        
        # Varsayılan: Popülerlik
        self.switch_search_tab("pop")
        
        # Context Menu (Yedek olarak kalsın veya kaldırılabilir, kullanıcı buton istedi)
        # Ancak sağ tık yine de çalışabilir.
        self.context_menu_search = tk.Menu(self.root, tearoff=0)
        self.context_menu_search.add_command(label="▶ Tarayıcıda Oynat", command=self.play_selected_song)
        self.context_menu_search.add_command(label="🔗 Linki Kopyala", command=self.copy_link_selected_song)
        
        self.tree_pop.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_pop, self.context_menu_search))
        self.tree_views.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_views, self.context_menu_search))

    def switch_search_tab(self, tab_type):
        """Tablar arası geçiş ve buton renk yönetimi"""
        # Listeleri (Frame'leri) gizle
        self.frame_pop.pack_forget()
        self.frame_views.pack_forget()
        
        if tab_type == "pop":
            self.frame_pop.pack(fill=tk.BOTH, expand=True)
            # Renk güncelleme
            self.btn_tab_pop.config(bg="#FF5722", fg="white", relief=tk.SUNKEN)
            self.btn_tab_views.config(bg="#e0e0e0", fg="#333", relief=tk.RAISED)
        else: # views
            self.frame_views.pack(fill=tk.BOTH, expand=True)
            # Renk güncelleme
            self.btn_tab_views.config(bg="#FF5722", fg="white", relief=tk.SUNKEN)
            self.btn_tab_pop.config(bg="#e0e0e0", fg="#333", relief=tk.RAISED)

    def create_song_treeview(self, parent):
        # Frame oluştur (Scrollbar + Treeview için container)
        frame = tk.Frame(parent)
        
        # 'İşlemler' kolonu eklendi (🔗  ▶)
        # "Sıra" kolonu eklendi
        columns = ("Sıra", "Şarkı", "Sanatçı", "Albüm", "Dinlenme", "Süre", "İşlemler")
        
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        for col in columns:
            tree.heading(col, text=col)
            
        tree.column("Sıra", width=40, anchor=tk.CENTER)
        tree.column("Şarkı", width=200)
        tree.column("Sanatçı", width=140)
        tree.column("Albüm", width=140)
        tree.column("Dinlenme", width=90)
        tree.column("Süre", width=60)
        tree.column("İşlemler", width=100, anchor=tk.CENTER) # Butonlar için kolon
        
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
        self.update_status(f"Hazırlanıyor... (Limit: {limit})", "blue")
        threading.Thread(target=self.search_artist_thread, args=(artist_name, limit), daemon=True).start()

    def update_search_progress_ui(self, song_data, current_count, total_count):
        def _ui():
            if song_data:
                # Görsel ikonlar (Unicode)
                action_text = "🔗      ▶" 
                
                # Gerçek satır sayısına göre renk belirle
                row_idx = len(self.tree_pop.get_children())
                tag = 'odd' if (row_idx + 1) % 2 == 1 else 'even'

                # 1. Popülerlik Tabına Ekle (Bulunan sırayla)
                iid = self.tree_pop.insert("", "end", values=(
                    str(current_count), song_data['title'], song_data['artist'], song_data['album'], 
                    song_data['views_text'], song_data['duration'], action_text
                ), tags=(tag,))
                self.song_map[iid] = song_data['video_id']
                
                # 2. Dinlenme Sayısı Tabına Ekle
                iid2 = self.tree_views.insert("", "end", values=(
                    str(current_count), song_data['title'], song_data['artist'], song_data['album'], 
                    song_data['views_text'], song_data['duration'], action_text
                ), tags=(tag,))
                self.song_map[iid2] = song_data['video_id']
                
            self.lbl_search_progress.config(text=f"Taranan: {current_count}/{total_count}")
        self.root.after(0, _ui)

    def sort_views_tab(self):
        """İşlem bitince Dinlenme tabını yeniden sıralar"""
        def _sort():
            items = []
            for child in self.tree_views.get_children():
                values = list(self.tree_views.item(child)['values'])
                # values[4] -> '1.5M views' (Sıra eklendiği için index kaydı)
                v_num = parse_views(values[4])
                items.append((v_num, values, self.song_map.get(child)))
            
            # Sırala
            items.sort(key=lambda x: x[0], reverse=True)
            
            # Yeniden çiz
            for child in self.tree_views.get_children():
                self.tree_views.delete(child)
                
            for i, (_, val, vid) in enumerate(items):
                tag = 'odd' if (i + 1) % 2 == 1 else 'even'
                # Sıra numarasını güncelle
                val[0] = str(i + 1)
                iid = self.tree_views.insert("", "end", values=val, tags=(tag,))
                self.song_map[iid] = vid
                
        self.root.after(0, _sort)

    def search_artist_thread(self, artist_name, target_count):
        try:
            self.update_status(f"Sanatçı kimliği aranıyor...", "blue")
            results = self.yt.search(query=artist_name, filter="artists")
            
            if not results:
                artist_true_name = artist_name
            else:
                match = next((r for r in results if r['artist'].lower() == artist_name.lower()), None)
                artist_true_name = match['artist'] if match else results[0]['artist']
            
            # API'den daha fazla çekip filtreleyeceğiz (Buffer)
            # Hedef * 3 kadar çekelim ama maksimum 1000 olsun (Performans için)
            fetch_limit = min(target_count * 3, 1000) 
            self.update_status(f"Hedef: {artist_true_name}. Şarkılar taranıyor... (Hedef: {target_count})")
            
            # Şarkı listesini çek
            song_results = self.yt.search(query=f"{artist_true_name}", filter="songs", limit=fetch_limit)
            
            if not song_results:
                self.update_status("Şarkı bulunamadı.", "red")
                return
            
            total_found = len(song_results)
            added_count = 0
            
            for song in song_results:
                # Hedef sayıya ulaşıldıysa dur
                if added_count >= target_count:
                    break

                artists = song.get('artists', [])
                a_names = [a['name'].lower() for a in artists]
                
                # Sanatçı filtresi
                if artist_true_name.lower() not in a_names and artist_name.lower() not in a_names:
                    continue
                    
                data = {
                    "title": song.get('title', 'Bilinmiyor'),
                    "artist": ", ".join([a['name'] for a in artists]),
                    "album": song.get('album', {}).get('name', 'Single'),
                    "views_text": song.get('views', '0'),
                    "duration": song.get('duration', ''),
                    "video_id": song.get('videoId', '')
                }
                
                added_count += 1
                self.update_search_progress_ui(data, added_count, total_found) # total_found sadece bilgi amaçlı
                time.sleep(0.05) # Animasyon efekti için kısa bekleme
            
            # İşlem bitince dinlenme tabını sırala
            self.sort_views_tab()
            self.update_status(f"Tamamlandı. {added_count} şarkı listelendi.", "green")

        except Exception as e:
            self.update_status(f"Hata: {e}", "red")
        finally:
            self.root.after(0, lambda: self.lbl_search_progress.config(text=""))
            self.root.after(0, lambda: self.btn_search.config(state=tk.NORMAL))


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
        self.update_status(f"{country_name} listeleri ve dinlenme sayıları çekiliyor... (Limit: {limit})", "blue")
        
        # Temizle
        for item in self.tree_chart.get_children():
            self.tree_chart.delete(item)
        self.chart_map.clear()
            
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
        self.update_status(f"{country_name} için {genre} listeleri taranıyor... (Limit: {limit})", "purple")
        
        for item in self.tree_genre.get_children():
            self.tree_genre.delete(item)
            
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
            self.root.after(0, lambda: self.lbl_genre_progress.config(text=""))
            

    def reset_chart_ui(self):
        def _reset():
            self.btn_chart_load.config(state=tk.NORMAL, text="Listele")
            self.lbl_chart_progress.config(text="")
        self.root.after(0, _reset)

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
                
                # Hücreyi ikiye böl: Sol taraf = Link, Sağ taraf = Play
                # Text: "🔗      ▶"
                video_id = self.song_map.get(item_id)
                if not video_id: return

                if click_relative_x < w / 2:
                    self.copy_link_by_id(video_id)
                else:
                    self.play_by_id(video_id)
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
        sel = self.get_selected_item_data(self.song_map, [self.tree_pop, self.tree_views])
        if sel: self.play_by_id(sel)

    def copy_link_selected_song(self):
        sel = self.get_selected_item_data(self.song_map, [self.tree_pop, self.tree_views])
        if sel: self.copy_link_by_id(sel)

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

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()