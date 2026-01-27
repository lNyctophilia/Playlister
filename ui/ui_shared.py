import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import json
import os

FAV_FILE = "favorites.json"

class UiShared:
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

    def show_search_view(self):
        self.set_active_mode_button("search")
        self.chart_view.pack_forget()
        self.genre_view.pack_forget()
        self.fav_view.pack_forget()
        self.search_view.pack(fill="both", expand=True)
        self.update_status("Mod: Sanatçı & Şarkı Arama - Sanatçı adı girerek şarkılarını listeleyin.")

    def show_chart_view(self):
        self.set_active_mode_button("chart")
        self.search_view.pack_forget()
        self.genre_view.pack_forget()
        self.fav_view.pack_forget()
        self.chart_view.pack(fill="both", expand=True)
        self.update_status("Mod: Ülke Listeleri - Ülke seçimi yaparak en popüler sanatçıları görün.")


    def copy_link_by_id(self, video_id):
        if video_id:
            url = f"https://music.youtube.com/watch?v={video_id}"
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            messagebox.showinfo("Bilgi", "Link kopyalandı!")

    def play_by_id(self, video_id):
        if video_id:
            webbrowser.open(f"https://music.youtube.com/watch?v={video_id}")
            
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
                    tree.set(item_id, "İşlemler", new_action_text)
                    
                    if is_added:
                        self.update_status("Favorilere eklendi.", "green")
                    else:
                        self.update_status("Favorilerden çıkarıldı.", "orange")
        except Exception as e:
            print(f"Click Error: {e}")

    def show_context_menu(self, event, tree, menu):
        item = tree.identify_row(event.y)
        if not item: return
        
        tree.selection_set(item)
        
        # Mod 1 (Arama) ve Mod 4 (Fav) için Dinamik Menü
        is_search_tree = getattr(self, 'tree_pop', None) == tree or \
                         getattr(self, 'tree_views', None) == tree or \
                         getattr(self, 'tree_smart', None) == tree
        is_fav_tree = getattr(self, 'tree_fav', None) == tree
        
        if is_search_tree or is_fav_tree:
             # Menüyü temizle ve yeniden oluştur
             menu.delete(0, tk.END)
             
             # Veriyi çek
             video_id = None
             song_title = ""
             
             if is_search_tree:
                 vals = tree.item(item)['values']
                 # values=(Sıra, Şarkı, Sanatçı, Albüm, Dinlenme, Süre, İşlemler, VideoID)
                 if len(vals) >= 8:
                     video_id = vals[7] # VideoID gizli kolon
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
             
             menu.post(event.x_root, event.y_root)
             
        else:
             # Diğer modlar (Chart/Genre) için varsayılan davranış (statik menü)
             menu.post(event.x_root, event.y_root)

    def context_toggle_fav(self, video_id, tree, item):
        # Şarkı verisini toparla
        song_data = {}
        # Identify tree type
        is_search_tree = getattr(self, 'tree_pop', None) == tree or \
                         getattr(self, 'tree_views', None) == tree or \
                         getattr(self, 'tree_smart', None) == tree
        
        if is_search_tree:
             vals = tree.item(item)['values']
             # ("Sıra", "Şarkı", "Sanatçı", "Albüm", "Dinlenme", "Süre", "İşlemler", "VideoID")
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
        
        # UI Güncelleme Logic
        if getattr(self, 'tree_fav', None) == tree:
            # Favoriler ekranındayız
            if not is_added: # Çıkarıldı
                self.tree_fav.delete(item)
                if item in self.fav_map: del self.fav_map[item]
                self.update_status("Favorilerden çıkarıldı.", "orange")
        else:
            # Arama ekranındayız, ikonu güncelle
            vals = tree.item(item)['values']
            if len(vals) >= 7:
                new_icon = "♥" if is_added else "♡"
                new_action_text = f"🔗             ▶             {new_icon}" 
                tree.set(item, "İşlemler", new_action_text)
                
            if is_added:
                self.update_status("Favorilere eklendi.", "green")
            else:
                self.update_status("Favorilerden çıkarıldı.", "orange")
