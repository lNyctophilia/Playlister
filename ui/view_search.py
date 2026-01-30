import tkinter as tk
from tkinter import ttk, messagebox
import threading
from difflib import SequenceMatcher
from utils import parse_views
from utils_downloader import Downloader

class ViewSearch:
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
        
        # Context Menu
        self.context_menu_search = tk.Menu(self.root, tearoff=0)
        
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
            self.btn_tab_views.config(bg="#FF5722", fg="white", relief=tk.SUNKEN)
            self.btn_tab_pop.config(bg="#e0e0e0", fg="#333", relief=tk.RAISED)
            self.btn_tab_smart.config(bg="#e0e0e0", fg="#333", relief=tk.RAISED)
        else: # smart
            self.frame_smart.pack(fill=tk.BOTH, expand=True)
            self.btn_tab_smart.config(bg="#FF5722", fg="white", relief=tk.SUNKEN)
            self.btn_tab_pop.config(bg="#e0e0e0", fg="#333", relief=tk.RAISED)
            self.btn_tab_views.config(bg="#e0e0e0", fg="#333", relief=tk.RAISED)
            
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
                dl_icon = parts[-1] if parts else "⬇"
                if dl_icon not in ["⬇", "🗑"]: dl_icon = "⬇"
                
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
                    
                    is_down = Downloader.is_downloaded(song['video_id'], song.get('artist'), song.get('title'))
                    dl_icon = "🗑" if is_down else "⬇"
                    
                    action_text = f"🔗            ▶            {fav_icon}            {dl_icon}"

                    iid = tree.insert("", "end", values=(
                        str(i + 1), song['title'], song['artist'], song['album'], 
                        song['views_text'], song['duration'], action_text, song['video_id']
                    ), tags=(tag,))
            
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
            
            # Hem Şarkıları Hem Videoları Tara (Remixler genelde video kategorisinde olabilir)
            self.update_status(f"Hedef: {artist_true_name}. Şarkılar ve Videolar taranıyor... (Geniş Tarama: {fetch_limit})")
            
            song_results = self.yt.search(query=f"{artist_true_name}", filter="songs", limit=fetch_limit)
            video_results = self.yt.search(query=f"{artist_true_name}", filter="videos", limit=fetch_limit)
            
            # Sonuçları birleştir
            combined_results = (song_results or []) + (video_results or [])
            
            if not combined_results:
                self.update_status("Şarkı bulunamadı.", "red")
                return
            
            candidates = []
            processed_count = 0
            observed_video_ids = set()
            
            # --- Phase 1: Collect Candidates ---
            for song in combined_results:
                if self.stop_listing:
                    self.update_status("Arama kullanıcı tarafından durduruldu.", "red")
                    break
                    
                artists = song.get('artists', [])
                if not artists: continue 
                
                # --- Sanatçı Doğrulama (Akıllı ve Katı Mod) ---
                raw_artists = [a['name'] for a in artists]
                expanded_song_artists = set()
                
                separators = [" ft ", " ft.", " feat ", " feat.", " featuring ", " & ", " x ", " ve ", ",", " and ", "/", " + "]
                
                for r_art in raw_artists:
                    temp_art = r_art.lower() if hasattr(r_art, 'lower') else str(r_art).lower()
                    for sep in separators:
                        temp_art = temp_art.replace(sep, "|")
                    tokens = [t.strip() for t in temp_art.split("|") if t.strip()]
                    expanded_song_artists.update(tokens)

                search_targets = set()
                user_query_parts = artist_name.lower().replace(" & ", "&").replace(" ve ", "&").replace(",", "&").split("&")
                for q in user_query_parts:
                    clean_q = q.strip()
                    if clean_q: search_targets.add(clean_q)
                
                if artist_true_name:
                    search_targets.add(artist_true_name.lower().strip())
                
                match_found = False
                for target in search_targets:
                    if target in expanded_song_artists:
                        match_found = True
                        break
                
                if not match_found:
                    continue

                processed_count += 1
                if processed_count % 10 == 0:
                     self.root.after(0, lambda c=processed_count: self.lbl_search_progress.config(text=f"İşleniyor: {c}"))
                
                vid_id = song.get('videoId', '')
                title = song.get('title', 'Bilinmiyor')
                
                # Deduplication Check (Video ID) - Ön eleme
                if vid_id in observed_video_ids:
                    continue
                observed_video_ids.add(vid_id)

                data = {
                    "title": title,
                    "artist": ", ".join([a['name'] for a in artists]),
                    "album": song.get('album', {}).get('name', 'Single'), # Videolarda albüm olmayabilir
                    "views_text": song.get('views', '0'),
                    "duration": song.get('duration', ''),
                    "video_id": vid_id
                }
                candidates.append(data)
            
            # --- Phase 2: Prioritize Albums & Fuzzy Deduplication ---
            # Albüm şarkılarını (Single olmayanları) öne al. 
            # Böylece "Aynı Şarkı" hem Albüm hem Single ise, Albüm versiyonu listeye girer.
            candidates.sort(key=lambda x: 1 if x['album'] == 'Single' else 0)
            
            all_songs = []
            observed_norm_titles = set()
            
            for song in candidates:
                norm_title = song['title'].lower().strip()
                
                # 1. Tam İsim Eşleşmesi (Exact Match)
                if norm_title in observed_norm_titles:
                    continue
                
                # 2. Benzer İsim Eşleşmesi (Sadece Single ise kontrol et)
                # Eğer bu şarkı 'Single' ise ve listemizde buna çok benzeyen (Albüm versiyonu) bir şarkı varsa ekleme.
                if song['album'] == 'Single':
                    is_fuzzy_duplicate = False
                    
                    # Temizlik Yardımcısı
                    def clean_title(t):
                        # Küçük harf
                        t = t.lower()
                        # Parantez içindeki yaygın 'noise'ları temizle
                        noise_words = [
                            "(official music)", "(official video)", "(official audio)", 
                            "(music video)", "(video)", "(audio)", "(lyric video)", "(lyrics)",
                            " official music", " official video", " official audio"
                        ]
                        for noise in noise_words:
                            t = t.replace(noise, "")
                        
                        # Sanatçı ismini baştan sil (Örn: "BLOK3 - Şarkı" -> "Şarkı")
                        # artist_true_name veya artist_name globalde var aslında ama
                        # combined_results içindeyiz.
                        if artist_name.lower() in t:
                             t = t.replace(artist_name.lower(), "").strip()
                             # Başta kalan " - " veya "- " leri temizle
                             if t.startswith("-"): t = t.lstrip("- ")
                        
                        return t.strip()

                    cleaned_current = clean_title(norm_title)

                    for existing in all_songs:
                        # Eğer karşılaştırdığımız şarkı da Single ise, ve biz zaten Single isek, 
                        # çok katı elemeyelim (belki remix vs dir).
                        # Amaç: Albüm versiyonu varken Single'ı elemek.
                        if existing['album'] == 'Single': 
                            continue

                        existing_title = existing['title'].lower().strip()
                        cleaned_existing = clean_title(existing_title)
                       
                        # Check A: Yüksek Benzerlik (Ratio)
                        if SequenceMatcher(None, cleaned_current, cleaned_existing).ratio() > 0.85:
                            is_fuzzy_duplicate = True
                            break
                        
                        # Check B: Containment (Kapsama) 
                        # Kullanıcı Sorunu: "napıyosun mesela ?" (Album) vs "BLOK3 - NAPIYOSUN MESELA ? (Official Music)" (Single/Video)
                        # Cleaned Album: "napiyosun mesela ?"
                        # Cleaned Single: "napiyosun mesela ?"
                        # Eğer kısa/temiz albüm ismi, uzun/kirli single isminin içinde geçiyorsa -> DUPLICATE
                        if cleaned_existing and cleaned_existing in cleaned_current:
                             # Çok kısa kelimelerde hatalı eşleşmeyi önle (Örn: "Aşk" vs "Aşkın Olayım")
                             if len(cleaned_existing) > 4: 
                                 is_fuzzy_duplicate = True
                                 break
                    
                    if is_fuzzy_duplicate:
                        continue
                
                observed_norm_titles.add(norm_title)
                all_songs.append(song)
                
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
            
            # Eksik varsa tamamla
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
