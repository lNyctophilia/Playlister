import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import requests
from utils import encrypt_text, parse_views

class ViewGenre:
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
        
        # Ülke Seçimi
        tk.Label(ctrl_frame, text="Ülke:").pack(side=tk.LEFT, padx=10)
        
        # Use existing countries dict if available, otherwise just use a hardcoded list or assume it's inherited
        # Since this is a mixin, we can rely on self.countries being init in App or ViewCharts
        # But safest is to reuse the logic if we can or just access self.countries
        # self.countries is init in ViewCharts, so we need to make sure ViewCharts init happens or we init it here too.
        # Ideally App inits it.
        # I'll rely on self.countries. If not, I'll defined a small fallback list.
        local_name = "Türkiye"
        if hasattr(self, 'countries'):
             keys = [k for k in self.countries.keys() if k != local_name and k != "Global"]
             keys.sort()
             display_values = [local_name, "Global"] + keys
        else:
             display_values = [local_name, "Global"]
        
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
        self.tree_genre.heading("Sanatçı", text="Sanatçı", command=lambda: self.sort_genre_column("Sanatçı", False))
        self.tree_genre.heading("Tür", text="Kategori")
        self.tree_genre.heading("Toplam Dinlenme", text="Toplam Dinlenme", command=lambda: self.sort_genre_column("Toplam Dinlenme", False))
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
        
        # Sağ tık -> ViewShared handles this or ViewCharts. But the menu is context_menu_chart.
        # We need to ensure context_menu_chart exists.
        # ViewCharts creates it. So ViewGenre depends on ViewCharts being setup or own menu.
        # I'll create one here just in case or use self.context_menu_genre
        self.context_menu_genre = tk.Menu(self.root, tearoff=0)
        self.context_menu_genre.add_command(label="Bu Sanatçıyı Ara", command=lambda: self.switch_to_artist_from_genre())
        
        self.tree_genre.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_genre, self.context_menu_genre))
        
        # Tooltip
        # Exclude: Rank(0), Tür(2), Toplam Dinlenme(3), Ara(4)
        self.setup_treeview_tooltip(self.tree_genre, excluded_columns=[0, 2, 3, 4])

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
                return

        self.set_active_mode_button("genre")
        self.search_view.pack_forget()
        self.chart_view.pack_forget()
        self.fav_view.pack_forget()
        self.genre_view.pack(fill="both", expand=True)
        self.update_status("Mod: Türe Göre (Beta) - Pop, Rock, Rap gibi türlerde popüler sanatçıları keşfedin.")

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
            
        val = self.tree_genre.item(item_id)['values']
        artist_name = val[1] # 2. kolon Sanatçı
        
        if artist_name:
            self.show_search_view()
            self.entry_artist.delete(0, tk.END)
            self.entry_artist.insert(0, artist_name)
            self.entry_artist.insert(0, artist_name)
            self.start_search()

    def sort_genre_column(self, col, reverse):
        """Genre listesini belirtilen kolona göre sıralar ve Sıra no günceller"""
        l = [(self.tree_genre.set(k, col), k) for k in self.tree_genre.get_children('')]
        
        # Sıralama mantığı
        if col == "Toplam Dinlenme":
            # parse_views fonksiyonu ile sayıya çevir
            l.sort(key=lambda x: parse_views(x[0]), reverse=reverse)
        else:
            # Alfabetik sıralama
            l.sort(key=lambda x: x[0].lower(), reverse=reverse)
            
        for index, (val, k) in enumerate(l):
            self.tree_genre.move(k, '', index)
            # Sıra numarasını (Rank) güncelle (index+1)
            # Rank sütunu index 0'da
            current_values = list(self.tree_genre.item(k, 'values'))
            current_values[0] = str(index + 1)
            
            # Zebra çizgilerini güncelle
            tag = 'odd' if (index + 1) % 2 == 1 else 'even'
            self.tree_genre.item(k, values=current_values, tags=(tag,))
            
        # Sonraki tıklama için yönü tersine çevir
        self.tree_genre.heading(col, command=lambda: self.sort_genre_column(col, not reverse))

    def set_lastfm_key(self):
        self.open_settings()
        
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
            API_KEY = getattr(self, 'lastfm_api_key', '') 
            
            if not API_KEY:
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
                        
                        views_text = self.format_view_count(v_val)
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
