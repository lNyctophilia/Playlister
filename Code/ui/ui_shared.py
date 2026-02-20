import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import json
import os
from utils_downloader import Downloader

FAV_FILE = "Config/favorites.json"

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
        if hasattr(self, "refresh_search_icons"):
             self.refresh_search_icons()

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
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
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
                
                # Hücreyi 4'e böl: Link, Play, Fav, Download
                # Text formatı: "🔗   ▶   [♥|♡]   [⬇|🗑]"
                section = w / 4
                
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
                elif click_relative_x < section * 3:
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
                    
                    # Mevcut download ikonunu koru
                    old_text = vals[6] # "🔗    ▶    ♥    ⬇"
                    dl_part = old_text.split()[-1] if old_text else "⬇"
                    if dl_part not in ["⬇", "🗑"]: dl_part = "⬇" # Fallback
                    
                    new_action_text = f"🔗            ▶            {new_icon}            {dl_part}"
                    
                    # Update Treeview Cell
                    tree.set(item_id, "İşlemler", new_action_text)
                    
                    if is_added:
                        self.update_status("Favorilere eklendi.", "green")
                    else:
                        self.update_status("Favorilerden çıkarıldı.", "orange")
                else:
                    # Download İşlemi
                    self.handle_shared_download_click(tree, item_id, vals)
        except Exception as e:
            print(f"Click Error: {e}")

    def handle_shared_download_click(self, tree, item_id, vals):
        video_id = vals[7]
        title = vals[1]
        artist = vals[2]
        
        if Downloader.is_downloaded(video_id, artist, title):
            if messagebox.askyesno("Sil", f"'{title}' dosyası silinsin mi?"):
                if Downloader.delete_content(video_id, artist, title):
                    self.update_row_dl_icon(tree, item_id, "⬇")
                    self.update_status("Silindi.", "orange")
        else:
            album = vals[3]
            self.update_status(f"İndiriliyor: {title}...", "blue")
            import threading
            threading.Thread(target=self.shared_download_thread, args=(tree, item_id, video_id, title, artist, album), daemon=True).start()

    def shared_download_thread(self, tree, item_id, video_id, title, artist, album=None):
        def cb(success, msg):
            if success:
                self.root.after(0, lambda: self.update_row_dl_icon(tree, item_id, "🗑"))
                self.update_status(f"İndirildi: {title}", "green")
            else:
                 self.update_status(f"Hata: {msg}", "red")
        Downloader.download_song(video_id, title, artist, album, cb)

    def update_row_dl_icon(self, tree, item_id, icon):
        if not tree.exists(item_id): return
        current_vals = tree.item(item_id)['values']
        # current action text -> index 6
        old_text = current_vals[6]
        # "🔗    ▶    [♥|♡]    OLD"
        parts = old_text.split()
        if len(parts) >= 3:
            # Reconstruct with new icon
            # parts[0]=Link, parts[1]=Play, parts[2]=Fav
            new_text = f"{parts[0]}            {parts[1]}            {parts[2]}            {icon}"
            tree.set(item_id, "İşlemler", new_text)

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
                 
                 menu.add_separator()
                 menu.add_separator()
                 # İsim bazlı kontrol için artist/title'a ihtiyacımız var ama burada sadece video_id var
                 # Map üzerinden almayı deneyelim veya title string'den parse edelim
                 # Treeview ise item values'den alabiliriz
                 
                 artist_chk = ""
                 title_chk = ""
                 
                 # Basit çözüm: Treeview'den çek
                 vals = tree.item(item)['values']
                 if len(vals) >= 3:
                     # values=(Sıra, Şarkı, Sanatçı, ...)
                     title_chk = vals[1]
                     artist_chk = vals[2]
                     
                 is_down = Downloader.is_downloaded(video_id, artist_chk, title_chk)
                 if is_down:
                     menu.add_command(label="🗑 Dosyayı Sil", command=lambda v=video_id, tr=tree, it=item, t=song_title: self.context_delete_file(v, tr, it, t))
                 else:
                     menu.add_command(label="⬇ İndir", command=lambda v=video_id, tr=tree, it=item, t=song_title: self.context_download_file(v, tr, it, t))
             
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
                old_text = vals[6]
                parts = old_text.split()
                dl_part = parts[-1] if parts else "⬇"
                if dl_part not in ["⬇", "🗑"]: dl_part = "⬇"
                
                new_icon = "♥" if is_added else "♡"
                new_action_text = f"🔗            ▶            {new_icon}            {dl_part}" 
                tree.set(item, "İşlemler", new_action_text)
                
            if is_added:
                self.update_status("Favorilere eklendi.", "green")
            else:
                self.update_status("Favorilerden çıkarıldı.", "orange")

    def context_download_file(self, video_id, tree, item, title_full):
        # Title parse (Artist - Song)
        # title_full format: "Song - Artist" usually
        parts = title_full.rsplit(' - ', 1) 
        if len(parts) > 1:
            title = parts[0]
            artist = parts[1]
        else:
            title = title_full
            artist = ""
        
        # Albüm bilgisini treeview'den çekmeye çalış
        album = None
        try:
             vals = tree.item(item)['values']
             # Format: (Sıra, Şarkı, Sanatçı, Albüm, ...)
             if len(vals) > 3:
                 album = vals[3]
        except:
             pass

        self.update_status(f"İndiriliyor: {title}...", "blue")
        import threading
        threading.Thread(target=self.shared_download_thread, args=(tree, item, video_id, title, artist, album), daemon=True).start()

    def context_delete_file(self, video_id, tree, item, title_full):
        # Parse title/artist from full title string or just use what we have
        parts = title_full.rsplit(' - ', 1) 
        if len(parts) > 1:
            title = parts[0]
            artist = parts[1]
        else:
            title = title_full
            artist = ""

        if messagebox.askyesno("Sil", "Dosya silinsin mi?"):
            if Downloader.delete_content(video_id, artist, title):
                 self.root.after(0, lambda: self.update_row_dl_icon(tree, item, "⬇"))
                 self.update_status("Silindi.", "orange")

    def setup_treeview_tooltip(self, tree, excluded_columns=None):
        """
        Treeview hücreleri üzerine gelindiğinde içeriklerini tooltip 
        olarak gösteren mekanizmayı kurar.
        excluded_columns: Tooltip gösterilmemesi gereken kolon indeksleri (0-based) listesi.
        """
        if excluded_columns is None:
            excluded_columns = []

        # ToolTip instance'ını tree üzerinde saklayalım
        if not hasattr(tree, 'tooltip_obj'):
            tree.tooltip_obj = ToolTip(tree)
            
        tree.last_tooltip_item = None
        tree.last_tooltip_col = None
        tree.tooltip_timer = None

        def cancel_tooltip_timer():
            if tree.tooltip_timer:
                tree.after_cancel(tree.tooltip_timer)
                tree.tooltip_timer = None

        def on_motion(event):
            # Sadece hücre üzerindeyse
            region = tree.identify_region(event.x, event.y)
            if region != "cell":
                cancel_tooltip_timer()
                tree.tooltip_obj.hidetip()
                tree.last_tooltip_item = None
                return
            
            item = tree.identify_row(event.y)
            col = tree.identify_column(event.x)
            
            if not item:
                cancel_tooltip_timer()
                tree.tooltip_obj.hidetip()
                tree.last_tooltip_item = None
                return

            # Eğer farklı bir hücreye geçildiyse güncelle
            if item != tree.last_tooltip_item or col != tree.last_tooltip_col:
                cancel_tooltip_timer()
                tree.tooltip_obj.hidetip()
                tree.last_tooltip_item = item
                tree.last_tooltip_col = col
                
                # Kolon index kontrolü (Excluded Check)
                try:
                    col_idx = int(col.replace("#", "")) - 1
                    if col_idx in excluded_columns:
                        return # Excluded, timer başlatma
                except:
                    return

                # İçeriği al ve timer başlat
                try:
                    col_idx = int(col.replace("#", "")) - 1
                    values = tree.item(item, 'values')
                    
                    if 0 <= col_idx < len(values):
                        text = str(values[col_idx])
                        if text:
                            # 700ms Gecikmeli Gösterim
                            tree.tooltip_timer = tree.after(700, lambda t=text: show_tip_delayed(t))
                except:
                    pass

        def show_tip_delayed(text):
            # Mouse pozisyonunu al
            x = tree.winfo_pointerx()
            y = tree.winfo_pointery()
            tree.tooltip_obj.showtip(text, x, y)
            tree.tooltip_timer = None # Timer bitti
        
        def on_leave(event):
            cancel_tooltip_timer()
            tree.tooltip_obj.hidetip()
            tree.last_tooltip_item = None
            tree.last_tooltip_col = None

        tree.bind("<Motion>", on_motion)
        tree.bind("<Leave>", on_leave)

    def format_view_count(self, view_text):
        if not view_text or str(view_text).lower() in ['none', 'veri yok', 'hata', 'bulunamadı']:
            return "Veri Yok"
        
        try:
            # "1.234.567 views" -> "1.234.567"
            s = str(view_text).strip().split(' ')[0]
            s_lower = s.lower()
            
            # Halihazırda formatlı ise (1.5M, 100K vb)
            if any(x in s_lower for x in ['m', 'k', 'b']) and any(c.isdigit() for c in s_lower):
                return s.upper()

            # Sadece rakamları al
            clean_str = "".join([c for c in s if c.isdigit()])
            
            if not clean_str:
                return s 
                
            num = int(clean_str)
            
            if num >= 1_000_000_000:
                val = num / 1_000_000_000
                return f"{val:.1f}B".replace(".0B", "B")
            elif num >= 1_000_000:
                val = num / 1_000_000
                return f"{val:.1f}M".replace(".0M", "M")
            elif num >= 1_000:
                val = num / 1_000
                return f"{val:.1f}K".replace(".0K", "K")
            else:
                return str(num)
        except:
            return str(view_text)


class ToolTip:
    """
    Basit ToolTip sınıfı.
    """
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text, x, y):
        "Display text in tooltip window"
        # Halihazırda açıksa veya text yoksa çık
        if self.tipwindow or not text:
            return
        
        self.tipwindow = tw = tk.Toplevel(self.widget)
        # Pencere kenarlıklarını kaldır (Sadece text kutusu gibi görünsün)
        tw.wm_overrideredirect(True)
        
        # Mouse'un biraz sağına ve altına konumlandır (Offset)
        tw.wm_geometry(f"+{x+10}+{y+20}")
        
        label = tk.Label(tw, text=text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=2, ipady=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

