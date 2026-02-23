import tkinter as tk
from tkinter import messagebox
from services.utils_downloader import Downloader
from ui import theme as T

class ContextMenuMixin:
    def show_context_menu(self, event, tree, menu):
        item = tree.identify_row(event.y)
        if not item: return
        
        tree.selection_set(item)
        
        is_search_tree = getattr(self, 'tree_pop', None) == tree or \
                         getattr(self, 'tree_views', None) == tree or \
                         getattr(self, 'tree_smart', None) == tree
        is_fav_tree = getattr(self, 'tree_fav', None) == tree
        
        if is_search_tree or is_fav_tree:
             menu.delete(0, tk.END)
             menu.config(bg=T.MENU_BG, fg=T.MENU_FG, activebackground=T.MENU_ACTIVE_BG, 
                         activeforeground=T.MENU_ACTIVE_FG, borderwidth=0)
             
             video_id = None
             song_title = ""
             
             if is_search_tree:
                 vals = tree.item(item)['values']
                 if len(vals) >= 8:
                     video_id = vals[7]
                     song_title = f"{vals[1]} - {vals[2]}"
             elif is_fav_tree:
                 data = self.fav_map.get(item)
                 if data:
                     video_id = data.get('video_id')
                     song_title = f"{data.get('title')} - {data.get('artist')}"
            
             if video_id:
                 menu.add_command(label="▶ Müziği Oynat", command=lambda v=video_id, t=song_title: self.play_music_start(v, t))
                 menu.add_command(label="🔗 Linki Kopyala", command=lambda v=video_id: self.copy_link_by_id(v))
                 menu.add_separator()
                 
                 is_fav = self.is_favorite(video_id)
                 if is_fav:
                     menu.add_command(label="💔 Favorilerden Çıkar", command=lambda v=video_id, tr=tree, it=item: self.context_toggle_fav(v, tr, it))
                 else:
                     menu.add_command(label="❤ Favorilere Ekle", command=lambda v=video_id, tr=tree, it=item: self.context_toggle_fav(v, tr, it))
                 
                 menu.add_separator()
                 menu.add_separator()
                 
                 artist_chk = ""
                 title_chk = ""
                 
                 vals = tree.item(item)['values']
                 if len(vals) >= 3:
                     title_chk = vals[1]
                     artist_chk = vals[2]
                     
                 is_down = Downloader.is_downloaded(video_id, artist_chk, title_chk)
                 if is_down:
                     menu.add_command(label="🗑 Dosyayı Sil", command=lambda v=video_id, tr=tree, it=item, t=song_title: self.context_delete_file(v, tr, it, t))
                 else:
                     menu.add_command(label="📥 İndir", command=lambda v=video_id, tr=tree, it=item, t=song_title: self.context_download_file(v, tr, it, t))
             
             menu.post(event.x_root, event.y_root)
             
        else:
             menu.config(bg=T.MENU_BG, fg=T.MENU_FG, activebackground=T.MENU_ACTIVE_BG, 
                         activeforeground=T.MENU_ACTIVE_FG, borderwidth=0)
             menu.post(event.x_root, event.y_root)

    def context_toggle_fav(self, video_id, tree, item):
        song_data = {}
        is_search_tree = getattr(self, 'tree_pop', None) == tree or \
                         getattr(self, 'tree_views', None) == tree or \
                         getattr(self, 'tree_smart', None) == tree
        
        if is_search_tree:
             vals = tree.item(item)['values']
             song_data = {
                 "video_id": video_id,
                 "title": vals[1],
                 "artist": vals[2],
                 "album": vals[3],
                 "views_text": vals[4],
                 "duration": vals[5]
             }
        elif getattr(self, 'tree_fav', None) == tree:
             song_data = self.fav_map.get(item)
             
        is_added = self.toggle_favorite(song_data)
        
        if getattr(self, 'tree_fav', None) == tree:
            if not is_added:
                self.tree_fav.delete(item)
                if item in self.fav_map: del self.fav_map[item]
                self.update_status("Favorilerden çıkarıldı.", "orange")
        else:
            vals = tree.item(item)['values']
            if len(vals) >= 7:
                new_icon = "♥" if is_added else "♡"
                old_text = vals[6]
                parts = old_text.split()
                dl_part = parts[-1] if parts else "📥"
                if dl_part not in ["📥", "🗑"]: dl_part = "📥"
                
                new_icon = "♥" if is_added else "♡"
                new_action_text = f"🔗            ▶            {new_icon}            {dl_part}" 
                tree.set(item, "İşlemler", new_action_text)
                
            if is_added:
                self.update_status("Favorilere eklendi.", "green")
            else:
                self.update_status("Favorilerden çıkarıldı.", "orange")

    def context_download_file(self, video_id, tree, item, title_full):
        parts = title_full.rsplit(' - ', 1) 
        if len(parts) > 1:
            title = parts[0]
            artist = parts[1]
        else:
            title = title_full
            artist = ""
        
        album = None
        try:
             vals = tree.item(item)['values']
             if len(vals) > 3:
                 album = vals[3]
        except:
             pass

        self.update_status(f"İndiriliyor: {title}...", "blue")
        import threading
        threading.Thread(target=self.shared_download_thread, args=(tree, item, video_id, title, artist, album), daemon=True).start()

    def context_delete_file(self, video_id, tree, item, title_full):
        parts = title_full.rsplit(' - ', 1) 
        if len(parts) > 1:
            title = parts[0]
            artist = parts[1]
        else:
            title = title_full
            artist = ""

        if messagebox.askyesno("Sil", "Dosya silinsin mi?"):
            if Downloader.delete_content(video_id, artist, title):
                 self.root.after(0, lambda: self.update_row_dl_icon(tree, item, "📥"))
                 self.update_status("Silindi.", "orange")
