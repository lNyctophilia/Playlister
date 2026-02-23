import tkinter as tk
from tkinter import ttk, messagebox
import threading
from utils import parse_views
from utils_downloader import Downloader
from search_engine import filter_candidates, deduplicate_candidates, generate_lists

class ViewSearch:
    def setup_search_view(self):
        # Arama kutusu paneli
        top_frame = tk.Frame(self.search_view, pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(top_frame, text="Sanatçı Adı:").pack(side=tk.LEFT, padx=10)
        
        self.entry_artist = tk.Entry(top_frame, width=40)
        self.entry_artist.pack(side=tk.LEFT, padx=10)
        self.entry_artist.bind("<Return>", lambda e: self.start_search())
        
        self.btn_search = tk.Button(top_frame, text="Ara", command=self.start_search, bg="#2196F3", fg="white")
        self.btn_search.pack(side=tk.LEFT, padx=10)
        
        # Arama Modu (Sanatçı / Şarkı)
        tk.Label(top_frame, text="Mod:").pack(side=tk.LEFT, padx=(10, 2))
        self.search_mode_var = tk.StringVar(value="Sanatçı")
        self.combo_search_mode = ttk.Combobox(top_frame, textvariable=self.search_mode_var, values=["Sanatçı", "Şarkı"], state="readonly", width=10)
        self.combo_search_mode.pack(side=tk.LEFT, padx=2)
        
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
        
        tk.Label(filter_frame, text="Liste Türü:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Dropdown (Combobox) ile tab seçimi
        self.tab_mode_var = tk.StringVar(value="🔥 Popülerlik")
        self.combo_tabs = ttk.Combobox(filter_frame, textvariable=self.tab_mode_var, 
                                       values=["🔥 Popülerlik", "📈 En Çok Dinlenenler", "✨ Karma Liste"], 
                                       state="readonly", width=25)
        self.combo_tabs.pack(side=tk.LEFT, padx=5)
        self.combo_tabs.bind("<<ComboboxSelected>>", self.on_tab_combobox_selected)

        # Liste Alanı
        self.list_container = tk.Frame(self.search_view)
        self.list_container.pack(expand=True, fill='both', padx=10, pady=5)
        
        # İki tabloyu da oluştur ama paketleme (pack) işlemini fonksiyona bırak
        self.frame_pop, self.tree_pop = self.create_song_treeview(self.list_container)
        self.frame_views, self.tree_views = self.create_song_treeview(self.list_container)
        self.frame_smart, self.tree_smart = self.create_song_treeview(self.list_container)
        
        # Varsayılan: Popülerlik
        self.switch_search_tab("pop")
        
        # Context Menu
        self.context_menu_search = tk.Menu(self.root, tearoff=0)
        
        self.tree_pop.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_pop, self.context_menu_search))
        self.tree_views.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_views, self.context_menu_search))
        self.tree_smart.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_smart, self.context_menu_search))

    def on_tab_combobox_selected(self, event=None):
        val = self.tab_mode_var.get()
        if "Popülerlik" in val:
            self.switch_search_tab("pop")
        elif "En Çok" in val:
            self.switch_search_tab("views")
        else:
            self.switch_search_tab("smart")

    def switch_search_tab(self, tab_type):
        """Tablar arası geçiş (Dropdown üzerinden)"""
        # Listeleri (Frame'leri) gizle
        self.frame_pop.pack_forget()
        self.frame_views.pack_forget()
        self.frame_smart.pack_forget()
        
        if tab_type == "pop":
            self.frame_pop.pack(fill=tk.BOTH, expand=True)
            self.tab_mode_var.set("🔥 Popülerlik")
        elif tab_type == "views":
            self.frame_views.pack(fill=tk.BOTH, expand=True)
            self.tab_mode_var.set("📈 En Çok Dinlenenler")
        else: # smart
            self.frame_smart.pack(fill=tk.BOTH, expand=True)
            self.tab_mode_var.set("✨ Karma Liste")
            
        # Geçişte ikonları tazele
        self.refresh_search_icons()

    def refresh_search_icons(self):
        """Tüm arama listelerindeki favori ikonlarını güncel durumla senkronize eder."""
        def _refresh(tree):
            if tree is None: return
            for item in tree.get_children():
                vals = tree.item(item)['values']
                if not vals or len(vals) < 8: continue
                
                video_id = vals[7]
                is_fav = self.is_favorite(video_id)
                new_icon = "♥" if is_fav else "♡"
                
                old_text = vals[6]
                parts = old_text.split()
                dl_icon = parts[-1] if parts else "📥"
                if dl_icon not in ["📥", "🗑"]: dl_icon = "📥"
                
                new_text = f"🔗            ▶            {new_icon}            {dl_icon}"
                
                # Sadece değişiklik varsa set et (Performans)
                if old_text != new_text:
                    tree.set(item, "İşlemler", new_text)

        _refresh(getattr(self, 'tree_pop', None))
        _refresh(getattr(self, 'tree_views', None))
        _refresh(getattr(self, 'tree_smart', None))

    def create_song_treeview(self, parent):
        # Frame oluştur (Scrollbar + Treeview için container)
        frame = tk.Frame(parent)
        
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
        tree.column("İşlemler", width=240, anchor=tk.CENTER) # Butonlar için kolon (Link, Play, Fav, DL)
        
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

        # Tooltip Özelliğini Aktif Et (UiShared'dan gelir)
        # Exclude: Sıra(0), Dinlenme(4), Süre(5), İşlemler(6)
        self.setup_treeview_tooltip(tree, excluded_columns=[0, 4, 5, 6])

        return frame, tree

    def start_search(self):
        if self.btn_search['text'] == "Durdur":
            self.stop_current_listing()
            return

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
            
        self.btn_search.config(text="Durdur", bg="#F44336", fg="white")
        self.entry_artist.config(state=tk.DISABLED)
        self.entry_search_limit.config(state=tk.DISABLED)
        self.combo_search_mode.config(state=tk.DISABLED)
        
        import time
        self.stop_listing = False
        self.current_search_id = time.time()  # Benzersiz arama kimliği
        search_token = self.current_search_id
        
        mode = self.search_mode_var.get()
        if mode == "Sanatçı":
            self.update_status(f"Sanatçı Hazırlanıyor... (Limit: {limit})", "blue")
            threading.Thread(target=self.search_artist_thread, args=(artist_name, limit, search_token), daemon=True).start()
        else:
            self.update_status(f"Şarkı Hazırlanıyor... (Limit: {limit})", "blue")
            threading.Thread(target=self.search_song_thread, args=(artist_name, limit, search_token), daemon=True).start()

    def populate_tabs(self, pop_list, views_list, smart_list):
        def _job():
            # Cache'i bir kere al
            dl_cache = Downloader.get_downloads_cache()
            
            def insert_to_tree(tree, data_list):
                 for i, song in enumerate(data_list):
                    tag = 'odd' if (i + 1) % 2 == 1 else 'even'
                    
                    is_fav = self.is_favorite(song['video_id'])
                    fav_icon = "♥" if is_fav else "♡"
                    
                    # Cache ile kontrol
                    is_down = Downloader.is_downloaded_cached(dl_cache, song['video_id'], song.get('artist'), song.get('title'))
                    dl_icon = "🗑" if is_down else "📥"
                    
                    action_text = f"🔗            ▶            {fav_icon}            {dl_icon}"

                    iid = tree.insert("", "end", values=(
                        str(i + 1), song['title'], song['artist'], song['album'], 
                        song['views_text'], song['duration'], action_text, song['video_id']
                    ), tags=(tag,))
            
            insert_to_tree(self.tree_pop, pop_list)
            insert_to_tree(self.tree_views, views_list)
            insert_to_tree(self.tree_smart, smart_list)
            
        self.root.after(0, _job)

    def search_artist_thread(self, artist_name, target_count, search_token):
        try:
            def stop_check():
                return self.stop_listing or self.current_search_id != search_token

            if stop_check(): return
            self.update_status(f"Sanatçı kimliği aranıyor...", "blue")
            results = self.yt.search(query=artist_name, filter="artists")
            
            if stop_check(): return
            if not results:
                artist_true_name = artist_name
            else:
                match = next((r for r in results if r['artist'].lower() == artist_name.lower()), None)
                artist_true_name = match['artist'] if match else results[0]['artist']
            
            self.update_status(f"Hedef: {artist_true_name}. Aşamalı tarama başlatılıyor...", "orange")
            
            fetch_limit = min(target_count * 4, 800) 
            self.update_status(f"API Sorgusu Bekleniyor... (Havuz: {fetch_limit*2})", "orange")
            song_results = self.yt.search(query=f"{artist_true_name}", filter="songs", limit=fetch_limit)
            
            if stop_check(): return
            video_results = self.yt.search(query=f"{artist_true_name}", filter="videos", limit=fetch_limit)
            
            if stop_check(): return
            combined_results = (song_results or []) + (video_results or [])
            
            if not combined_results:
                self.update_status("Şarkı bulunamadı.", "red")
                return
            
            candidates = filter_candidates(combined_results, artist_name, artist_true_name, stop_check)
            if candidates is None: return
            
            if stop_check(): return
            
            all_songs = deduplicate_candidates(candidates, target_count, artist_name, stop_check)
            if all_songs is None: return
            
            if stop_check(): return
            
            total_found = len(all_songs)
            self.update_status(f"{total_found} aday şarkı bulundu. Listeler oluşturuluyor...", "orange")

            pop_list, views_list, smart_list = generate_lists(all_songs, target_count)

            if stop_check(): return
            
            self.populate_tabs(pop_list, views_list, smart_list)
            self.update_status(f"Tamamlandı. {len(all_songs)} şarkı havuzundan {target_count} şarkılık 3 liste oluşturuldu.", "green")

        except Exception as e:
            if not self.stop_listing and self.current_search_id == search_token:
                self.update_status(f"Hata: {e}", "red")
        finally:
            if self.current_search_id == search_token:
                self.root.after(0, lambda: self.lbl_search_progress.config(text=""))
                self.root.after(0, lambda: self.btn_search.config(text="Ara", bg="#2196F3", fg="white"))
                self.root.after(0, lambda: self.entry_artist.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.entry_search_limit.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.combo_search_mode.config(state="readonly"))

    def search_song_thread(self, query, target_count, search_token):
        """Doğrudan şarkı arama modu (Youtube Style)"""
        try:
            if self.stop_listing or self.current_search_id != search_token: return
            self.update_status(f"Şarkı aranıyor: {query}...", "blue")
            
            # Şarkıları ara
            results = self.yt.search(query=query, filter="songs", limit=target_count)
            
            if self.stop_listing or self.current_search_id != search_token: return
            if not results:
                self.update_status("Sonuç bulunamadı.", "red")
                return

            song_list = []
            
            for i, song in enumerate(results):
                # Her iterasyonda kontrol
                if self.stop_listing or self.current_search_id != search_token:
                    return
                    
                video_id = song.get('videoId')
                if not video_id: continue
                
                artists = song.get('artists', [])
                artist_text = ", ".join([a['name'] for a in artists])
                
                data = {
                    "title": song.get('title', 'Bilinmiyor'),
                    "artist": artist_text,
                    "album": song.get('album', {}).get('name', 'Single'),
                    "views_text": song.get('views', 'Veri Yok'),
                    "duration": song.get('duration', ''),
                    "video_id": video_id
                }
                song_list.append(data)
                
            if self.stop_listing or self.current_search_id != search_token: return
            
            self.populate_tabs(song_list, song_list, song_list)
            self.update_status(f"Tamamlandı. {len(song_list)} sonuç bulundu.", "green")
            
        except Exception as e:
            if not self.stop_listing and self.current_search_id == search_token:
                self.update_status(f"Hata: {e}", "red")
        finally:
            if self.current_search_id == search_token:
                self.root.after(0, lambda: self.lbl_search_progress.config(text=""))
                self.root.after(0, lambda: self.btn_search.config(text="Ara", bg="#2196F3", fg="white"))
                self.root.after(0, lambda: self.entry_artist.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.entry_search_limit.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.combo_search_mode.config(state="readonly"))
