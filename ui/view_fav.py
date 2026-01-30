import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
from tkinter import messagebox
from utils_downloader import Downloader

FAV_FILE = "favorites.json"

class ViewFav:
    def setup_fav_view(self):
        # Üst Panel
        top_frame = tk.Frame(self.fav_view, pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(top_frame, text="Favorilerim", font=("Helvetica", 12, "bold")).pack(side=tk.LEFT, padx=10)
        
        self.btn_refresh_fav = tk.Button(top_frame, text="Yenile", command=self.load_fav_ui, bg="#2196F3", fg="white")
        self.btn_refresh_fav.pack(side=tk.RIGHT, padx=(5, 20))

        self.btn_download_all = tk.Button(top_frame, text="Tümünü İndir", command=self.download_all_favs, bg="#FF9800", fg="white")
        self.btn_download_all.pack(side=tk.RIGHT, padx=5)

        self.btn_delete_all_dl = tk.Button(top_frame, text="Tüm İndirilenleri Sil", command=self.delete_all_downloads_ui, bg="red", fg="white")
        self.btn_delete_all_dl.pack(side=tk.RIGHT, padx=5)

        # Liste
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
        self.tree_fav.column("İşlemler", width=240, anchor=tk.CENTER) # Genişletildi
        
        sb = ttk.Scrollbar(self.fav_view, orient=tk.VERTICAL, command=self.tree_fav.yview)
        self.tree_fav.configure(yscroll=sb.set)
        
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_fav.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree_fav.bind("<ButtonRelease-1>", self.on_fav_list_click)
        self.tree_fav.tag_configure('odd', background='#f9f9f9')
        self.tree_fav.tag_configure('even', background='white')
        
        self.tree_fav.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_fav, self.context_menu_search))

        # Tooltip
        # Exclude: Sıra(0), Dinlenme(4), Süre(5), İşlemler(6)
        self.setup_treeview_tooltip(self.tree_fav, excluded_columns=[0, 4, 5, 6])

    def show_fav_view(self):
        self.set_active_mode_button("fav")
        self.search_view.pack_forget()
        self.chart_view.pack_forget()
        self.genre_view.pack_forget()
        self.fav_view.pack(fill="both", expand=True)
        self.update_status("Mod: Favoriler - Kaydettiğiniz şarkılar.")
        self.load_fav_ui()

    def load_fav_ui(self):
        # Temizle
        for item in self.tree_fav.get_children():
            self.tree_fav.delete(item)
        self.fav_map.clear()
        
        # Verileri al ve sırala
        self.favorites = self.load_favorites()
        favs = self.favorites
        
        self.refresh_action_buttons_state()

        if not favs:
            self.update_status("Favori listeniz boş.", "blue")
            return
            
        # Sanatçı ismiyle sırala
        sorted_favs = sorted(favs, key=lambda x: x.get('artist', '').lower())

        # OPTIMIZASYON: Dosya listesini tek seferde al (Cache)
        dl_cache = Downloader.get_downloads_cache()
        
        for i, song in enumerate(sorted_favs):
             tag = 'odd' if (i + 1) % 2 == 1 else 'even'
             
             title = song.get('title', '')
             artist = song.get('artist', '')
             video_id = song.get('video_id', '')
             
             # Cache kullanarak kontrol et (Disk I/O yok)
             is_downloaded = Downloader.is_downloaded_cached(dl_cache, video_id, artist, title)
             dl_icon = "🗑" if is_downloaded else "⬇"
             
             # Action text: Link | Play | Fav | Download
             full_action_text = f"🔗            ▶            ♥            {dl_icon}"
             
             iid = self.tree_fav.insert("", "end", values=(
                 str(i + 1), 
                 song.get('title', ''), 
                 song.get('artist', ''), 
                 song.get('album', ''), 
                 song.get('views_text', ''), 
                 song.get('duration', ''), 
                 full_action_text
             ), tags=(tag,))
             self.fav_map[iid] = song 

        self.update_status(f"Favoriler listelendi: {len(favs)} şarkı.", "green")

    def refresh_action_buttons_state(self):
        """
        Favori listesindeki indirilme durumuna göre butonları
        aktif veya pasif yapar.
        """
        if not hasattr(self, 'favorites') or not self.favorites:
            self.btn_download_all.config(state=tk.DISABLED)
            self.btn_delete_all_dl.config(state=tk.DISABLED)
            return

        total = len(self.favorites)
        downloaded = 0
        
        # Optimize edilmiş kontrol
        dl_cache = Downloader.get_downloads_cache()
        
        for s in self.favorites:
            if Downloader.is_downloaded_cached(dl_cache, s.get('video_id'), s.get('artist'), s.get('title')):
                downloaded += 1
        
        # Tümü indirilmişse -> İndir butonu pasif
        if downloaded == total and total > 0:
            self.btn_download_all.config(state=tk.DISABLED)
        else:
            self.btn_download_all.config(state=tk.NORMAL)
            
        # Hiçbiri indirilmemişse -> Sil butonu pasif
        if downloaded == 0:
            self.btn_delete_all_dl.config(state=tk.DISABLED)
        else:
            self.btn_delete_all_dl.config(state=tk.NORMAL)

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
                
                # 4 butona boluyoruz
                section = w / 4
                
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
                elif click_x < section * 3:
                     # Remove Fav (Buton 3)
                    res = messagebox.askyesno("Onay", "Bu şarkıyı favorilerden kaldırmak istiyor musunuz?")
                    if res:
                        self.toggle_favorite(song_data)
                        self.tree_fav.delete(item_id)
                        del self.fav_map[item_id]
                        self.refresh_action_buttons_state()
                else:
                    # Download / Delete (Buton 4)
                    self.handle_download_click(item_id, song_data)
                        
        except Exception as e:
            print(f"Fav Click Error: {e}")

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

    def handle_download_click(self, item_id, song_data):
        video_id = song_data.get('video_id')
        title = song_data.get('title')
        artist = song_data.get('artist')
        
        if Downloader.is_downloaded(video_id, artist, title):
            # Silme işlemi
            if messagebox.askyesno("Sil", f"'{title}' dosyası silinsin mi?"):
                success = Downloader.delete_content(video_id, artist, title)
                if success:
                    self.update_fav_row_icon(item_id, "⬇")
                    self.update_status("Dosya silindi.", "orange")
                else:
                    messagebox.showerror("Hata", "Dosya silinemedi.")
        else:
            # İndirme işlemi
            self.update_status(f"İndiriliyor: {title}...", "blue")
            threading.Thread(target=self.download_single_thread, args=(item_id, video_id, title, artist), daemon=True).start()

    def download_single_thread(self, item_id, video_id, title, artist):
        def cb(success, msg):
            if success:
                self.root.after(0, lambda: self.update_fav_row_icon(item_id, "🗑"))
                self.update_status(f"İndirildi: {title}", "green")
            else:
                self.update_status(f"Hata: {msg}", "red")
        
        Downloader.download_song(video_id, title, artist, cb)

    def update_fav_row_icon(self, item_id, dl_icon):
        if self.tree_fav.exists(item_id):
            # Mevcut texti alıp son ikonu güncelle
            # Text format: "🔗    ▶    ♥    ICON"
            new_text = f"🔗            ▶            ♥            {dl_icon}"
            self.tree_fav.set(item_id, "İşlemler", new_text)
            self.refresh_action_buttons_state()

    def download_all_favs(self):
        favs = self.load_favorites()
        if not favs:
            messagebox.showinfo("Bilgi", "Favori listeniz boş.")
            return

        to_download = []
        dl_cache = Downloader.get_downloads_cache()
        
        for s in favs:
            if not Downloader.is_downloaded_cached(dl_cache, s['video_id'], s.get('artist'), s.get('title')):
                to_download.append(s)
        
        if not to_download:
            messagebox.showinfo("Bilgi", "Tüm favoriler zaten indirilmiş.")
            return
            
        count = len(to_download)
        if not messagebox.askyesno("İndir", f"{count} adet şarkı indirilecek. Onaylıyor musunuz?"):
            return
            
        self.btn_download_all.config(state=tk.DISABLED)
        threading.Thread(target=self.download_all_thread, args=(to_download,), daemon=True).start()

    def download_all_thread(self, songs):
        total = len(songs)
        for i, s in enumerate(songs):
            if self.stop_listing: break
            self.update_status(f"İndiriliyor ({i+1}/{total}): {s['title']}...", "blue")
            
            # Senkron indirme (sırayla)
            # 403 Hatasını önlemek için bekleme
            import time
            import random
            
            # Hata kontrolü için callback'li yapıya geçebiliriz ama şimdilik direkt çağırıp
            # utils içinde exception logluyoruz.
            # Downloader.download_song senkron olduğu için bitmesini bekler.
            
            Downloader.download_song(s['video_id'], s['title'], s['artist'])
            
            # UI güncelle (listedeki ilgili satırı bulup ikonunu güncelle)
            self.root.after(0, lambda vid=s['video_id']: self.update_icon_by_videoid(vid))
            
            # Burst Logic:
            # - Her şarkı arası 1 sn bekle
            # - Her 3 şarkıda bir 10 sn dinlen (Cooldown)
            
            if i < total - 1:
                # 3. şarkıdan sonra uzun dinlenme
                # i+1 çünkü i 0'dan başlıyor. (i+1) % 3 == 0 ise 3, 6, 9...
                if (i + 1) % 3 == 0:
                    cooldown_count = (i + 1) // 3
                    
                    # Tek sayılarda (1, 3, 5...): 7-10 sn
                    # Çift sayılarda (2, 4, 6...): 10-16 sn
                    if cooldown_count % 2 == 1:
                        wait = random.uniform(7, 10)
                        msg = f"Soğuma (Kısa): {wait:.1f}s..."
                    else:
                        wait = random.uniform(10, 16)
                        msg = f"Soğuma (Uzun): {wait:.1f}s..."
                    
                    self.update_status(msg, "orange")
                    time.sleep(wait)
                else:
                    # 1-3 sn arası rastgele
                    time.sleep(random.uniform(1, 3))
            
        self.update_status("Tüm indirmeler tamamlandı!", "green")
        self.root.after(0, lambda: self.btn_download_all.config(state=tk.NORMAL))
        self.root.after(0, self.load_fav_ui) 

    def update_icon_by_videoid(self, video_id):
        # find item with video_id in fav_map
        for iid, data in self.fav_map.items():
            if data.get('video_id') == video_id:
                self.update_fav_row_icon(iid, "🗑")
                break

    def delete_all_downloads_ui(self):
        if messagebox.askyesno("DİKKAT", "Downloads klasöründeki TÜM dosyalar silinecek!\nBu favorilerde olmayan indirilmiş dosyaları da siler.\nOnaylıyor musunuz?"):
            if Downloader.delete_all_downloads():
                self.load_fav_ui() # Listeyi yenile ikonları güncelle
                self.update_status("Tüm indirilenler temizlendi.", "red")
            else:
                messagebox.showerror("Hata", "Silme işlemi başarısız.")
