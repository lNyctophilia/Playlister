import tkinter as tk
from tkinter import ttk, messagebox
from ytmusicapi import YTMusic
import threading
import webbrowser
import time
import locale

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

        self.btn_mode_genre = tk.Button(self.nav_frame, text="🎸 Türe Göre (Beta)",
                                        command=self.show_genre_view,
                                        font=("Helvetica", 10, "bold"),
                                        bg="#ddd", fg="#333", relief=tk.RAISED)
        self.btn_mode_genre.pack(side=tk.LEFT, padx=5, pady=5)

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
        # (Ikon tanımları artık gerekli değil, text rengi kullanılacak)
        
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

    def show_chart_view(self):
        self.set_active_mode_button("chart")
        self.search_view.pack_forget()
        self.genre_view.pack_forget()
        self.chart_view.pack(fill="both", expand=True)
        self.update_status("Mod: Ülke Listeleri - Ülke seçimi yaparak en popüler sanatçıları görün.")

    def show_genre_view(self):
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
            sys_lang = locale.getdefaultlocale()[0]
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
        
        # Buton
        self.btn_genre_load = tk.Button(ctrl_frame, text="Sanatçıları Listele", 
                                        command=self.start_genre_load, 
                                        bg="#9C27B0", fg="white", width=20)
        self.btn_genre_load.pack(side=tk.LEFT, padx=20)
        
        self.lbl_genre_progress = tk.Label(ctrl_frame, text="", fg="gray")
        self.lbl_genre_progress.pack(side=tk.LEFT)
        
        # Liste
        cols = ("Rank", "Sanatçı", "Tür", "Durum", "Ara")
        self.tree_genre = ttk.Treeview(self.genre_view, columns=cols, show='headings')
        self.tree_genre.heading("Rank", text="Sıra")
        self.tree_genre.heading("Sanatçı", text="Sanatçı")
        self.tree_genre.heading("Tür", text="Kategori")
        self.tree_genre.heading("Durum", text="Durum")
        self.tree_genre.heading("Ara", text="İşlem")
        
        self.tree_genre.column("Rank", width=50, anchor=tk.CENTER)
        self.tree_genre.column("Sanatçı", width=200)
        self.tree_genre.column("Tür", width=100)
        self.tree_genre.column("Durum", width=100)
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

    def start_genre_load(self):
        genre = self.combo_genre.get()
        country_name = self.combo_genre_country.get()
        
        self.btn_genre_load.config(state=tk.DISABLED, text="Taranıyor...")
        self.update_status(f"{country_name} için {genre} listeleri taranıyor...", "purple")
        
        for item in self.tree_genre.get_children():
            self.tree_genre.delete(item)
            
        threading.Thread(target=self.load_genre_thread, args=(genre, country_name), daemon=True).start()

    def update_genre_progress(self, text, insert_item=None):
        def _update():
            self.lbl_genre_progress.config(text=text)
            if insert_item:
                count = len(self.tree_genre.get_children())
                tag_zebra = 'odd' if (count + 1) % 2 == 1 else 'even'
                self.tree_genre.insert("", "end", values=(
                    insert_item['rank'], insert_item['artist'], insert_item['genre'], 
                    "Popüler", "🔍"
                ), tags=(tag_zebra,))
        self.root.after(0, _update)

    def load_genre_thread(self, genre, country_name):
        try:
            # 1. Arama Sorgusu Oluştur
            # Türkiye için özel sorgular, diğerleri için genel
            query = ""
            if country_name == "Türkiye":
                base_queries = [
                    f"Türkçe {genre} Top Hits",
                    f"En İyi Türkçe {genre} Şarkılar",
                    f"Popüler {genre} Türkiye"
                ]
                if genre == "Pop": base_queries = ["Türkçe Pop Top Hits", "Kral Pop En İyiler", "Power Türk Pop"]
                elif genre == "Rock": base_queries = ["Türkçe Rock Top 50", "Anadolu Rock Efsaneleri", "Türk Rock Hits"]
                elif genre == "Rap": base_queries = ["Türkçe Rap Top 50", "Hiphop Türkiye", "Türkçe Rap Hits"]
                elif genre == "Arabesk": base_queries = ["Damar Arabesk Top List", "Arabesk Klasikleri", "Kral FM Arabesk"]
                elif genre == "Halk Müziği": base_queries = ["Türk Halk Müziği Seçmeler", "Türkülerimiz", "Anadolu Türküleri"]
            else:
                # Global veya Yabancı
                c_term = "" if country_name == "Global" else country_name
                base_queries = [
                    f"Top {genre} Hits {c_term}",
                    f"Best {genre} Songs {c_term}",
                    f"{c_term} {genre} Charts"
                ]

            self.update_status(f"Birden fazla kaynaktan {genre} listeleri taranıyor...", "purple")
            
            seen_artists = set()
            unique_artists_list = []
            
            # 3 Farklı Sorgu ile Arayıp Birleştirelim (Çeşitlilik Artar)
            # Her sorgudan en iyi 1 playlisti alacağız
            playlists_to_scan = []
            
            for q in base_queries[:2]: # İlk 2 sorguyu kullan (Fazla vakit kaybetmemek için)
                s_results = self.yt.search(q, filter="playlists")
                if s_results:
                    playlists_to_scan.append(s_results[0]) # En iyi eşleşen
            
            if not playlists_to_scan:
                self.update_status("Uygun playlist bulunamadı.", "red")
                return

            total_playlists = len(playlists_to_scan)
            
            for idx, pl in enumerate(playlists_to_scan):
                pl_id = pl['browseId']
                pl_title = pl['title']
                self.update_status(f"Kaynak {idx+1}/{total_playlists}: {pl_title} inceleniyor...", "purple")
                
                try:
                    # Playlistten 50 şarkı çek
                    pl_data = self.yt.get_playlist(pl_id, limit=50)
                    tracks = pl_data.get('tracks', [])
                    
                    for track in tracks:
                        if len(unique_artists_list) >= 60: break # Toplam limit
                        
                        artists = track.get('artists', [])
                        if not artists: continue
                        
                        # Kanal isimlerini elemek için kontrol:
                        # Gerçek sanatçıların genellikle 'id'si olur ve 'id'si 24 karakterli channel ID olmaz (Genelde)
                        # Ancak en garantisi: Birden fazla şarkıda geçiyorsa o sanatçıdır (Bu karmaşık).
                        # Basit yöntem: 'id' alanı varsa sanatçı profilidir.
                        
                        main_artist_obj = artists[0]
                        art_name = main_artist_obj.get('name')
                        art_id = main_artist_obj.get('id')
                        
                        # Filtreleme Kuralları:
                        # 1. İsmi boş olmasın
                        # 2. Daha önce eklenmemiş olsun
                        # 3. ID'si olsun (Bu genellikle resmi sanatçı olduğunu gösterir, kanal değil)
                        if art_name and (art_name not in seen_artists) and art_id:
                            # Bazı "Various Artists" veya "Çeşitli Sanatçılar" gibi jenerik isimleri de eleyelim
                            if "Various" in art_name or "Çeşitli" in art_name:
                                continue
                                
                            seen_artists.add(art_name)
                            unique_artists_list.append({
                                'name': art_name, 
                                'id': art_id # İlerde profil linki için kullanılabilir
                            })
                except:
                    continue
            
            # Listeleme
            if not unique_artists_list:
                self.update_status("Sanatçı bulunamadı.", "red")
                return

            # Sonuçları listeye bas
            for i, art_data in enumerate(unique_artists_list):
                item = {
                    "rank": str(i+1),
                    "artist": art_data['name'],
                    "genre": genre
                }
                self.update_genre_progress(f"Bulundu: {art_data['name']}", insert_item=item)
                time.sleep(0.01)
                
            self.update_status(f"Tamamlandı. {len(unique_artists_list)} sanatçı, {total_playlists} farklı listeden derlendi.", "green")
            
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