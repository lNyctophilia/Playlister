import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
from tkinter import messagebox
from services.utils_downloader import Downloader
from core.constants import FAV_FILE, DOWNLOAD_DIR
from utils.utils import parse_views, parse_duration
from ui import theme as T



class ViewFav:
    def setup_fav_view(self):
        top_frame = tk.Frame(self.fav_view, pady=10, bg=T.BG_PANEL)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        lbl_title = tk.Label(top_frame, text="Favorilerim")
        T.style_label(lbl_title, bg=T.BG_PANEL, font=T.FONT_HEADING)
        lbl_title.pack(side=tk.LEFT, padx=10)
        
        self.btn_refresh_fav = tk.Button(top_frame, text="Yenile", command=self.load_fav_ui)
        T.style_button(self.btn_refresh_fav)
        self.btn_refresh_fav.pack(side=tk.RIGHT, padx=(5, 20))

        self.btn_download_all = tk.Button(top_frame, text="Tümünü İndir", command=self.download_all_favs)
        T.style_button(self.btn_download_all, bg=T.BTN_INFO, hover_bg=T.BTN_INFO_HOVER)
        self.btn_download_all.pack(side=tk.RIGHT, padx=5)

        self.btn_delete_all_dl = tk.Button(top_frame, text="Tüm İndirilenleri Sil", command=self.delete_all_downloads_ui)
        T.style_button(self.btn_delete_all_dl, bg=T.BTN_DANGER, hover_bg=T.BTN_DANGER_HOVER)
        self.btn_delete_all_dl.pack(side=tk.RIGHT, padx=5)

        self.btn_open_downloads = tk.Button(top_frame, text="📂 Klasörü Aç", command=self.open_downloads_folder)
        T.style_button(self.btn_open_downloads, bg=T.BTN_SECONDARY, hover_bg=T.BTN_SECONDARY_HOVER)
        self.btn_open_downloads.pack(side=tk.RIGHT, padx=5)

        cols = ("Sıra", "Şarkı", "Sanatçı", "Albüm", "Dinlenme", "Süre", "İşlemler")
        self.tree_fav = ttk.Treeview(self.fav_view, columns=cols, show='headings')
        
        for col in cols:
            if col == "Sıra":
                self.tree_fav.heading(col, text=col)
            else:
                self.tree_fav.heading(col, text=col, command=lambda c=col: self.sort_fav_column(c, False))
            
        self.tree_fav.column("Sıra", width=40, anchor=tk.CENTER)
        self.tree_fav.column("Şarkı", width=200)
        self.tree_fav.column("Sanatçı", width=140)
        self.tree_fav.column("Albüm", width=140)
        self.tree_fav.column("Dinlenme", width=90)
        self.tree_fav.column("Süre", width=60)
        self.tree_fav.column("İşlemler", width=240, anchor=tk.CENTER)
        
        sb = ttk.Scrollbar(self.fav_view, orient=tk.VERTICAL, command=self.tree_fav.yview)
        self.tree_fav.configure(yscroll=sb.set)
        
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_fav.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree_fav.bind("<ButtonRelease-1>", self.on_fav_list_click)
        self.tree_fav.tag_configure('odd', background=T.TREE_ODD, foreground=T.FG_PRIMARY)
        self.tree_fav.tag_configure('even', background=T.TREE_EVEN, foreground=T.FG_PRIMARY)
        
        self.tree_fav.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_fav, self.context_menu_search))

        self.setup_treeview_tooltip(self.tree_fav, excluded_columns=[0, 4, 5, 6])

    def show_fav_view(self):
        self.set_active_mode_button("fav")
        self.search_view.pack_forget()
        self.chart_view.pack_forget()
        self.genre_view.pack_forget()
        self.settings_view.pack_forget()
        self.fav_view.pack(fill="both", expand=True)
        self.update_status("Mod: Favoriler - Kaydettiğiniz şarkılar.")
        self.load_fav_ui()

    def load_fav_ui(self):
        for item in self.tree_fav.get_children():
            self.tree_fav.delete(item)
        self.fav_map.clear()
        
        self.favorites = self.load_favorites()
        favs = self.favorites
        
        self.refresh_action_buttons_state()

        if not favs:
            self.update_status("Favori listeniz boş.", "blue")
            return
            
        self.update_status(f"Favoriler yükleniyor... ({len(favs)} şarkı)", "blue")

        sorted_favs = sorted(favs, key=lambda x: x.get('artist', '').lower())
        dl_cache = Downloader.get_downloads_cache()
        
        items_to_insert = []
        for i, song in enumerate(sorted_favs):
             tag = 'odd' if (i + 1) % 2 == 1 else 'even'
             
             title = song.get('title', '')
             artist = song.get('artist', '')
             video_id = song.get('video_id', '')
             
             is_downloaded = Downloader.is_downloaded_cached(dl_cache, video_id, artist, title)
             dl_icon = "🗑" if is_downloaded else "📥"
             
             full_action_text = f"🔗            ▶            ♥            {dl_icon}"
             
             values = (
                 str(i + 1), 
                 song.get('title', ''), 
                 song.get('artist', ''), 
                 song.get('album', ''), 
                 song.get('views_text', ''), 
                 song.get('duration', ''), 
                 full_action_text
             )
             items_to_insert.append((values, tag, song))

        self._insert_fav_chunk(items_to_insert, 0)

    def _insert_fav_chunk(self, items, start_index):
        CHUNK_SIZE = 50
        end_index = min(start_index + CHUNK_SIZE, len(items))
        
        for i in range(start_index, end_index):
            values, tag, song = items[i]
            iid = self.tree_fav.insert("", "end", values=values, tags=(tag,))
            self.fav_map[iid] = song
            
        if end_index < len(items):
            self.root.after(10, lambda: self._insert_fav_chunk(items, end_index))
        else:
            self.update_status(f"Favoriler listelendi: {len(items)} şarkı.", "green")

    def refresh_action_buttons_state(self):
        if not hasattr(self, 'favorites') or not self.favorites:
            self.btn_download_all.config(state=tk.DISABLED)
            self.btn_delete_all_dl.config(state=tk.DISABLED)
            return

        total = len(self.favorites)
        downloaded = 0
        
        dl_cache = Downloader.get_downloads_cache()
        
        for s in self.favorites:
            if Downloader.is_downloaded_cached(dl_cache, s.get('video_id'), s.get('artist'), s.get('title')):
                downloaded += 1
        
        if downloaded == total and total > 0:
            self.btn_download_all.config(state=tk.DISABLED)
        else:
            self.btn_download_all.config(state=tk.NORMAL)
            
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
            if col == "#7":
                item_id = tree.identify_row(event.y)
                if not item_id: return
                
                bbox = tree.bbox(item_id, col)
                if not bbox: return
                x, y, w, h = bbox
                click_x = event.x - x
                
                section = w / 4
                
                song_data = self.fav_map.get(item_id)
                if not song_data: return
                video_id = song_data.get('video_id')

                if click_x < section:
                    self.copy_link_by_id(video_id)
                elif click_x < section * 2:
                    title = f"{song_data.get('title')} - {song_data.get('artist')}"
                    self.current_play_mode = "fav"
                    self.current_playlist = []
                    for child in self.tree_fav.get_children(''):
                        s_data = self.fav_map.get(child)
                        if s_data:
                            self.current_playlist.append(s_data)
                    for i, s in enumerate(self.current_playlist):
                        if s.get('video_id') == video_id:
                            self.current_playlist_index = i
                            break
                    self.set_player_mode("fav")
                    self.play_music_start(video_id, title)
                elif click_x < section * 3:
                    res = messagebox.askyesno("Onay", "Bu şarkıyı favorilerden kaldırmak istiyor musunuz?")
                    if res:
                        self.toggle_favorite(song_data)
                        self.tree_fav.delete(item_id)
                        del self.fav_map[item_id]
                        self.refresh_action_buttons_state()
                else:
                    self.handle_download_click(item_id, song_data)
                        
        except Exception as e:

            print(f"Fav Click Error: {e}")

    def sort_fav_column(self, col, reverse):
        l = [(self.tree_fav.set(k, col), k) for k in self.tree_fav.get_children('')]
        
        if col == "Dinlenme":
             l.sort(key=lambda x: parse_views(x[0]), reverse=reverse)
        elif col == "Süre":
             l.sort(key=lambda x: parse_duration(x[0]), reverse=reverse)
        elif col == "İşlemler":
             l.sort(key=lambda x: 1 if "🗑" in x[0] else 0, reverse=reverse)
        else:
             l.sort(key=lambda x: x[0].lower(), reverse=reverse)
             
        for index, (val, k) in enumerate(l):
            self.tree_fav.move(k, '', index)
            current_values = list(self.tree_fav.item(k, 'values'))
            current_values[0] = str(index + 1)
            
            tag = 'odd' if (index + 1) % 2 == 1 else 'even'
            self.tree_fav.item(k, values=current_values, tags=(tag,))
            
        self.tree_fav.heading(col, command=lambda: self.sort_fav_column(col, not reverse))

    def load_favorites(self):
        from core.favorites_manager import load_favorites
        return load_favorites()

    def save_favorites(self):
        from core.favorites_manager import save_favorites
        save_favorites(self.favorites)

    def is_favorite(self, video_id):
        from core.favorites_manager import is_favorite
        return is_favorite(self.favorites, video_id)

    def toggle_favorite(self, song_data):
        from core.favorites_manager import toggle_favorite
        return toggle_favorite(self.favorites, song_data)

    def handle_download_click(self, item_id, song_data):
        video_id = song_data.get('video_id')
        title = song_data.get('title')
        artist = song_data.get('artist')
        
        if Downloader.is_downloaded(video_id, artist, title):
            if messagebox.askyesno("Sil", f"'{title}' dosyası silinsin mi?"):
                success = Downloader.delete_content(video_id, artist, title)
                if success:
                    self.update_fav_row_icon(item_id, "📥")
                    self.update_status("Dosya silindi.", "orange")
                else:
                    messagebox.showerror("Hata", "Dosya silinemedi.")
        else:
            album = song_data.get('album')
            self.update_status(f"İndiriliyor: {title}...", "blue")
            threading.Thread(target=self.download_single_thread, args=(item_id, video_id, title, artist, album), daemon=True).start()

    def download_single_thread(self, item_id, video_id, title, artist, album):
        def cb(success, msg):
            if success:
                self.root.after(0, lambda: self.update_fav_row_icon(item_id, "🗑"))
                self.update_status(f"İndirildi: {title}", "green")
            else:
                self.update_status(f"Hata: {msg}", "red")
        
        Downloader.download_song(video_id, title, artist, album, cb)

    def update_fav_row_icon(self, item_id, dl_icon):
        if self.tree_fav.exists(item_id):
            new_text = f"🔗            ▶            ♥            {dl_icon}"
            self.tree_fav.set(item_id, "İşlemler", new_text)
            self.refresh_action_buttons_state()

    def download_all_favs(self):
        if getattr(self, '_is_downloading_all_favs', False):
            self._cancel_favs_dl = True
            self.btn_download_all.config(text="Duruyor...", state=tk.DISABLED)
            return

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
            
        self._is_downloading_all_favs = True
        self._cancel_favs_dl = False
        self.btn_download_all.config(text="Durdur", bg=T.BTN_DANGER)
        T.apply_hover(self.btn_download_all, T.BTN_DANGER, T.BTN_DANGER_HOVER)
        
        threading.Thread(target=self.download_all_thread, args=(to_download,), daemon=True).start()

    def download_all_thread(self, songs):
        total = len(songs)
        for i, s in enumerate(songs):
            if self.stop_listing or getattr(self, '_cancel_favs_dl', False):
                self.update_status("Tümünü indirme işlemi iptal edildi.", "orange")
                break
                
            self.update_status(f"İndiriliyor ({i+1}/{total}): {s['title']}...", "blue")
            
            import time
            import random
            
            Downloader.download_song(s['video_id'], s['title'], s['artist'], s.get('album'))
            
            self.root.after(0, lambda vid=s['video_id']: self.update_icon_by_videoid(vid))
            
            if i < total - 1 and not getattr(self, '_cancel_favs_dl', False):
                if (i + 1) % 3 == 0:
                    cooldown_count = (i + 1) // 3
                    
                    if cooldown_count % 2 == 1:
                        wait = random.uniform(7, 10)
                        msg = f"Soğuma (Kısa): {wait:.1f}s..."
                    else:
                        wait = random.uniform(10, 16)
                        msg = f"Soğuma (Uzun): {wait:.1f}s..."
                    
                    self.update_status(msg, "orange")
                    
                    slept = 0
                    while slept < wait:
                        if self.stop_listing or getattr(self, '_cancel_favs_dl', False):
                            break
                        time.sleep(0.5)
                        slept += 0.5
                else:
                    wait = random.uniform(1, 3)
                    slept = 0
                    while slept < wait:
                        if self.stop_listing or getattr(self, '_cancel_favs_dl', False):
                            break
                        time.sleep(0.5)
                        slept += 0.5
            
        if not getattr(self, '_cancel_favs_dl', False):
            self.update_status("Tüm indirmeler tamamlandı!", "green")
            print(f"[Toplu İndirme] Tamamlandı: {total} şarkı")
            
        self._is_downloading_all_favs = False
        self._cancel_favs_dl = False
        
        self.root.after(0, lambda: self.btn_download_all.config(
            text="Tümünü İndir", state=tk.NORMAL, bg=T.BTN_INFO
        ))
        self.root.after(0, lambda: T.apply_hover(self.btn_download_all, T.BTN_INFO, T.BTN_INFO_HOVER))
        self.root.after(0, self.load_fav_ui) 

    def update_icon_by_videoid(self, video_id):
        for iid, data in self.fav_map.items():
            if data.get('video_id') == video_id:
                self.update_fav_row_icon(iid, "🗑")
                break

    def delete_all_downloads_ui(self):
        if messagebox.askyesno("DİKKAT", "Downloads klasöründeki TÜM dosyalar silinecek!\nBu favorilerde olmayan indirilmiş dosyaları da siler.\nOnaylıyor musunuz?"):
            if Downloader.delete_all_downloads():
                self.load_fav_ui()
                self.update_status("Tüm indirilenler temizlendi.", "red")
            else:
                messagebox.showerror("Hata", "Silme işlemi başarısız.")

    def open_downloads_folder(self):
        Downloader.ensure_dir()
        path = os.path.abspath(DOWNLOAD_DIR)
        try:
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Hata", f"Klasör açılamadı: {e}")
