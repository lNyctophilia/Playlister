import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import json
import os
from services.utils_downloader import Downloader
from core.constants import FAV_FILE
from ui import theme as T

class UiShared:
    def update_status(self, text, color=None):
        color_map = {
            "black": T.FG_PRIMARY,
            "green": "#2ed573",
            "red": "#ff4757",
            "blue": "#74b9ff",
            "orange": "#ffa502",
            "purple": "#a29bfe",
            "gray": T.FG_SECONDARY,
            None: T.FG_SECONDARY
        }
        fg = color_map.get(color, color if color else T.FG_SECONDARY)
        self.root.after(0, lambda: self.status_bar.config(text=text, fg=fg))

    def set_active_mode_button(self, mode):
        self.btn_mode_search.config(bg=T.NAV_INACTIVE, fg=T.FG_SECONDARY, relief=tk.FLAT)
        self.btn_mode_chart.config(bg=T.NAV_INACTIVE, fg=T.FG_SECONDARY, relief=tk.FLAT)
        self.btn_mode_genre.config(bg=T.NAV_INACTIVE, fg=T.FG_SECONDARY, relief=tk.FLAT)
        self.btn_mode_fav.config(bg=T.NAV_INACTIVE, fg=T.FG_SECONDARY, relief=tk.FLAT)
        
        T.apply_hover(self.btn_mode_search, T.NAV_INACTIVE, T.NAV_HOVER, T.FG_SECONDARY, T.FG_PRIMARY)
        T.apply_hover(self.btn_mode_chart, T.NAV_INACTIVE, T.NAV_HOVER, T.FG_SECONDARY, T.FG_PRIMARY)
        T.apply_hover(self.btn_mode_genre, T.NAV_INACTIVE, T.NAV_HOVER, T.FG_SECONDARY, T.FG_PRIMARY)
        T.apply_hover(self.btn_mode_fav, T.NAV_INACTIVE, T.NAV_HOVER, T.FG_SECONDARY, T.FG_PRIMARY)
        
        if mode == "search":
            self.btn_mode_search.config(bg=T.NAV_ACTIVE, fg="#ffffff", relief=tk.FLAT)
            T.apply_hover(self.btn_mode_search, T.NAV_ACTIVE, T.BTN_PRIMARY_HOVER, "#ffffff", "#ffffff")
        elif mode == "chart":
            self.btn_mode_chart.config(bg=T.NAV_ACTIVE, fg="#ffffff", relief=tk.FLAT)
            T.apply_hover(self.btn_mode_chart, T.NAV_ACTIVE, T.BTN_PRIMARY_HOVER, "#ffffff", "#ffffff")
        elif mode == "genre":
            self.btn_mode_genre.config(bg=T.NAV_ACTIVE, fg="#ffffff", relief=tk.FLAT)
            T.apply_hover(self.btn_mode_genre, T.NAV_ACTIVE, T.BTN_PRIMARY_HOVER, "#ffffff", "#ffffff")
        elif mode == "fav":
            self.btn_mode_fav.config(bg=T.NAV_ACTIVE, fg="#ffffff", relief=tk.FLAT)
            T.apply_hover(self.btn_mode_fav, T.NAV_ACTIVE, T.BTN_PRIMARY_HOVER, "#ffffff", "#ffffff")

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

    def on_song_list_click(self, event):
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
                click_relative_x = event.x - x
                
                section = w / 4
                
                vals = tree.item(item_id)['values']
                if len(vals) < 8: return

                video_id = vals[7]
                if not video_id: return

                if click_relative_x < section:
                    self.copy_link_by_id(video_id)
                elif click_relative_x < section * 2:
                    song_title = f"{vals[1]} - {vals[2]}"
                    self.play_music_start(video_id, song_title)
                elif click_relative_x < section * 3:
                    song_data = {
                        "video_id": video_id,
                        "title": vals[1],
                        "artist": vals[2],
                        "album": vals[3],
                        "views_text": vals[4],
                        "duration": vals[5]
                    }
                    
                    is_added = self.toggle_favorite(song_data)
                    
                    new_icon = "♥" if is_added else "♡"
                    
                    old_text = vals[6]
                    dl_part = old_text.split()[-1] if old_text else "📥"
                    if dl_part not in ["📥", "🗑"]: dl_part = "📥"
                    
                    new_action_text = f"🔗            ▶            {new_icon}            {dl_part}"
                    
                    tree.set(item_id, "İşlemler", new_action_text)
                    
                    if is_added:
                        self.update_status("Favorilere eklendi.", "green")
                    else:
                        self.update_status("Favorilerden çıkarıldı.", "orange")
                else:
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
                    self.update_row_dl_icon(tree, item_id, "📥")
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
        old_text = current_vals[6]
        parts = old_text.split()
        if len(parts) >= 3:
            new_text = f"{parts[0]}            {parts[1]}            {parts[2]}            {icon}"
            tree.set(item_id, "İşlemler", new_text)

    def setup_treeview_tooltip(self, tree, excluded_columns=None):
        if excluded_columns is None:
            excluded_columns = []

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

            if item != tree.last_tooltip_item or col != tree.last_tooltip_col:
                cancel_tooltip_timer()
                tree.tooltip_obj.hidetip()
                tree.last_tooltip_item = item
                tree.last_tooltip_col = col
                
                try:
                    col_idx = int(col.replace("#", "")) - 1
                    if col_idx in excluded_columns:
                        return
                except:
                    return

                try:
                    col_idx = int(col.replace("#", "")) - 1
                    values = tree.item(item, 'values')
                    
                    if 0 <= col_idx < len(values):
                        text = str(values[col_idx])
                        if text:
                            tree.tooltip_timer = tree.after(700, lambda t=text: show_tip_delayed(t))
                except:
                    pass

        def show_tip_delayed(text):
            x = tree.winfo_pointerx()
            y = tree.winfo_pointery()
            tree.tooltip_obj.showtip(text, x, y)
            tree.tooltip_timer = None
        
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
            s = str(view_text).strip().split(' ')[0]
            s_lower = s.lower()
            
            if any(x in s_lower for x in ['m', 'k', 'b']) and any(c.isdigit() for c in s_lower):
                return s.upper()

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
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text, x, y):
        if self.tipwindow or not text:
            return
        
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        
        tw.wm_geometry(f"+{x+10}+{y+20}")
        
        label = tk.Label(tw, text=text, justify=tk.LEFT,
                      background=T.TOOLTIP_BG, foreground=T.TOOLTIP_FG,
                      relief=tk.SOLID, borderwidth=1,
                      font=T.FONT_TOOLTIP)
        label.pack(ipadx=4, ipady=2)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
