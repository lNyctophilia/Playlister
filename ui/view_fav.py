import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

FAV_FILE = "favorites.json"

class ViewFav:
    def setup_fav_view(self):
        # Üst Panel
        top_frame = tk.Frame(self.fav_view, pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(top_frame, text="Favorilerim", font=("Helvetica", 12, "bold")).pack(side=tk.LEFT, padx=10)
        
        self.btn_refresh_fav = tk.Button(top_frame, text="Yenile", command=self.load_fav_ui, bg="#2196F3", fg="white")
        self.btn_refresh_fav.pack(side=tk.RIGHT, padx=10)

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
        self.tree_fav.column("İşlemler", width=120, anchor=tk.CENTER)
        
        sb = ttk.Scrollbar(self.fav_view, orient=tk.VERTICAL, command=self.tree_fav.yview)
        self.tree_fav.configure(yscroll=sb.set)
        
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_fav.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree_fav.bind("<ButtonRelease-1>", self.on_fav_list_click)
        self.tree_fav.tag_configure('odd', background='#f9f9f9')
        self.tree_fav.tag_configure('even', background='white')
        
        self.tree_fav.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_fav, self.context_menu_search))

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
        favs = self.load_favorites()
        if not favs:
            self.update_status("Favori listeniz boş.", "blue")
            return
            
        # Sanatçı ismiyle sırala
        sorted_favs = sorted(favs, key=lambda x: x.get('artist', '').lower())
        
        action_text = "🔗             ▶             ♥" 
        
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
