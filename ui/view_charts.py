import tkinter as tk
from tkinter import ttk, messagebox
import threading
import locale
import json

class ViewCharts:
    def setup_chart_view(self):
        ctrl_frame = tk.Frame(self.chart_view, pady=10)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(ctrl_frame, text="Ülke Seç:").pack(side=tk.LEFT, padx=10)
        
        # Geniş Kapsamlı Ülke Listesi
        self.countries = {
            "Global": "ZZ", "Türkiye": "TR", "ABD": "US", "İngiltere": "GB", "Almanya": "DE", 
            "Fransa": "FR", "Japonya": "JP", "Güney Kore": "KR", "Brezilya": "BR", "Hindistan": "IN",
            "Meksika": "MX", "Rusya": "RU", "İtalya": "IT", "İspanya": "ES", "Kanada": "CA",
            "Avustralya": "AU", "Hollanda": "NL", "Arjantin": "AR", "Polonya": "PL", "İsveç": "SE",
            "Tayland": "TH", "Endonezya": "ID", "Vietnam": "VN", "Filipinler": "PH", "Şili": "CL",
            "Kolombiya": "CO", "Peru": "PE", "Ukrayna": "UA", "Güney Afrika": "ZA", "Mısır": "EG",
            "Suudi Arabistan": "SA", "Birleşik Arap Emirlikleri": "AE", "Yunanistan": "GR", 
            "Portekiz": "PT", "Macaristan": "HU", "Çekya": "CZ", "Romanya": "RO", "İsrail": "IL",
            "İsviçre": "CH", "Avusturya": "AT", "Belçika": "BE", "Danimarka": "DK", "Finlandiya": "FI",
            "Norveç": "NO", "İrlanda": "IE", "Yeni Zelanda": "NZ", "Singapur": "SG", "Malezya": "MY",
            "Pakistan": "PK", "Nijerya": "NG", "Kenya": "KE", "Fas": "MA", "Cezayir": "DZ",
            "Irak": "IQ", "Sırbistan": "RS", "Hırvatistan": "HR", "Slovakya": "SK", "Bulgaristan": "BG",
            "Azerbaycan": "AZ", "Kazakistan": "KZ", "Özbekistan": "UZ", "Beyaz Rusya": "BY",
            "Lübnan": "LB", "Ürdün": "JO", "Kuveyt": "KW", "Katar": "QA", "Umman": "OM",
            "Tunus": "TN", "Slovenya": "SI", "Litvanya": "LT", "Letonya": "LV", "Estonya": "EE",
            "İzlanda": "IS", "Lüksemburg": "LU", "Kıbrıs": "CY", "Malta": "MT"
        }

        # Sistem dilini/ülkesini otomatik algıla
        local_name = "Türkiye" # Varsayılan
        try:
            locale.setlocale(locale.LC_ALL, '')
            sys_lang = locale.getlocale()[0]
            if sys_lang:
                local_code = sys_lang.split('_')[-1].upper()
                # Sözlükten ismini bul
                found_name = next((k for k, v in self.countries.items() if v == local_code), None)
                if found_name:
                    local_name = found_name
        except:
            pass
            
        # Listeyi Hazırla
        other_countries = [k for k in self.countries.keys() if k != local_name and k != "Global"]
        other_countries.sort() # Alfabetik sırala
        
        display_values = [local_name, "-------------------", "Global"] + other_countries

        self.combo_country = ttk.Combobox(ctrl_frame, values=display_values, state="readonly")
        self.combo_country.current(0) # İlk sıradaki (Lokal) seçili
        self.combo_country.pack(side=tk.LEFT, padx=10)
        
        # Limit Seçimi
        tk.Label(ctrl_frame, text="Limit:").pack(side=tk.LEFT, padx=(10, 2))
        self.entry_chart_limit = tk.Entry(ctrl_frame, width=5)
        self.entry_chart_limit.insert(0, "40") # Varsayılan 40
        self.entry_chart_limit.pack(side=tk.LEFT, padx=2)
        self.entry_chart_limit.bind("<Return>", lambda e: self.start_chart_load())
        
        self.btn_chart_load = tk.Button(ctrl_frame, text="Listele", command=self.start_chart_load, bg="#FF9800", fg="white", width=25)
        self.btn_chart_load.pack(side=tk.LEFT, padx=20)
        
        self.btn_chart_stop = tk.Button(ctrl_frame, text="Durdur", command=self.stop_current_listing, bg="#F44336", fg="white", width=10, state=tk.DISABLED)
        self.btn_chart_stop.pack(side=tk.LEFT, padx=5)
        
        self.lbl_chart_progress = tk.Label(ctrl_frame, text="", fg="gray")
        self.lbl_chart_progress.pack(side=tk.LEFT)
        
        # Sonuç Tablosu
        cols = ("Rank", "Sanatçı", "Toplam Dinlenme", "Trend", "Ara")
        self.tree_chart = ttk.Treeview(self.chart_view, columns=cols, show='headings')
        self.tree_chart.heading("Rank", text="Sıra")
        self.tree_chart.heading("Sanatçı", text="Sanatçı")
        self.tree_chart.heading("Toplam Dinlenme", text="Toplam Dinlenme (Views)")
        self.tree_chart.heading("Trend", text="Durum")
        self.tree_chart.heading("Ara", text="İşlem")
        
        self.tree_chart.column("Rank", width=50, anchor=tk.CENTER)
        self.tree_chart.column("Sanatçı", width=200)
        self.tree_chart.column("Toplam Dinlenme", width=150)
        self.tree_chart.column("Trend", width=100)
        self.tree_chart.column("Ara", width=60, anchor=tk.CENTER)
        
        sb = ttk.Scrollbar(self.chart_view, orient=tk.VERTICAL, command=self.tree_chart.yview)
        self.tree_chart.configure(yscroll=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_chart.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tree_chart.bind("<ButtonRelease-1>", self.on_chart_list_click)

        # Zebra
        self.tree_chart.tag_configure('odd', background='#f9f9f9')
        self.tree_chart.tag_configure('even', background='white')

        self.context_menu_chart = tk.Menu(self.root, tearoff=0)
        self.context_menu_chart.add_command(label="Bu Sanatçıyı Ara", command=self.switch_to_artist_from_chart)
        self.tree_chart.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_chart, self.context_menu_chart))
        
        # Tooltip
        # Exclude: Rank(0), Toplam Dinlenme(2), Trend(3), Ara(4)
        self.setup_treeview_tooltip(self.tree_chart, excluded_columns=[0, 2, 3, 4])

    def direct_search_artist(self, artist_name):
        self.show_search_view()
        self.entry_artist.delete(0, tk.END)
        self.entry_artist.insert(0, artist_name)
        self.start_search()

    def start_chart_load(self):
        country_name = self.combo_country.get()
        
        if "---" in country_name:
            messagebox.showwarning("Seçim Hatası", "Lütfen listeden geçerli bir ülke seçiniz (Çizgiye tıklamayınız).")
            return

        country_code = self.countries.get(country_name, "TR")
        
        # Limit
        try:
            limit = int(self.entry_chart_limit.get())
            if limit > 40: 
                limit = 40
                self.entry_chart_limit.delete(0, tk.END)
                self.entry_chart_limit.insert(0, "40")
        except:
            limit = 40
            self.entry_chart_limit.delete(0, tk.END)
            self.entry_chart_limit.insert(0, "40")

        self.btn_chart_load.config(state=tk.DISABLED, text="Veriler Çekiliyor...")
        self.combo_country.config(state=tk.DISABLED)
        self.entry_chart_limit.config(state=tk.DISABLED)
        self.update_status(f"{country_name} listeleri ve dinlenme sayıları çekiliyor... (Limit: {limit})", "blue")
        
        # Temizle
        for item in self.tree_chart.get_children():
            self.tree_chart.delete(item)
        self.chart_map.clear()
            
        self.chart_map.clear()
        
        self.stop_listing = False
        self.btn_chart_stop.config(state=tk.NORMAL)
        threading.Thread(target=self.load_charts_thread, args=(country_code, limit), daemon=True).start()

    def update_chart_progress(self, text, insert_item=None):
        def _update():
            self.lbl_chart_progress.config(text=text)
            if insert_item:
                count = len(self.tree_chart.get_children())
                tag_zebra = 'odd' if (count + 1) % 2 == 1 else 'even'

                iid = self.tree_chart.insert("", "end", values=(
                    insert_item['rank'], insert_item['title'], insert_item['views_text'], insert_item['trend'], "🔍"
                ), tags=(tag_zebra,))
                self.chart_map[iid] = insert_item['title']
        self.root.after(0, _update)

    def reset_chart_ui(self):
        def _reset():
            self.btn_chart_load.config(state=tk.NORMAL, text="Listele")
            self.lbl_chart_progress.config(text="")
            self.combo_country.config(state="readonly")
            self.entry_chart_limit.config(state=tk.NORMAL)
            self.btn_chart_stop.config(state=tk.DISABLED)
        self.root.after(0, _reset)

    def load_charts_thread(self, country_code, limit):
        try:
            charts = self.yt.get_charts(country=country_code)
            
            artist_data = charts.get('artists')
            artists = []
            if isinstance(artist_data, dict):
                artists = artist_data.get('items', [])
            elif isinstance(artist_data, list):
                artists = artist_data
            
            if not artists:
                self.update_status("Liste bulunamadı.", "red")
                self.reset_chart_ui()
                return

            # Limiti uygula
            if limit > 0:
                artists = artists[:limit]

            total_artists = len(artists)
            self.update_status(f"Toplam {total_artists} sanatçı bulundu. Detaylı dinlenme verileri çekiliyor...", "orange")

            for idx, art in enumerate(artists):
                if self.stop_listing:
                    self.update_status("Listeleme durduruldu.", "red")
                    break

                browse_id = art.get('browseId')
                name = art.get('title', 'Bilinmiyor')
                views_text = "..."
                
                progress_msg = f"İşleniyor ({idx+1}/{total_artists}): {name}"
                
                if browse_id:
                    try:
                        # Dinlenme sayısı için profil detayı
                        details = self.yt.get_artist(browse_id)
                        v_val = details.get('views')
                        if not v_val or str(v_val).lower() == 'none':
                             views_text = 'Veri Yok'
                        else:
                             views_text = v_val
                    except:
                        views_text = "Hata"
                
                raw_trend = art.get('trend', 'neutral')
                trend_map = {
                    "up": "Artış",
                    "down": "Azalış",
                    "neutral": "Sabit"
                }
                trend_display = trend_map.get(str(raw_trend).lower(), raw_trend)
                if isinstance(trend_display, str):
                    trend_display = trend_display.capitalize()

                item_data = {
                    "rank": art.get('rank', str(idx+1)),
                    "title": name,
                    "views_text": views_text,
                    "trend": trend_display
                }
                
                self.update_chart_progress(progress_msg, insert_item=item_data)

            self.update_status(f"Tamamlandı! {total_artists} sanatçı listelendi.", "green")
            
        except Exception as e:
            self.update_status(f"Hata: {e}", "red")
        finally:
            self.reset_chart_ui()

    def on_chart_list_click(self, event):
        """Chart listesindeki arama butonuna tıklamayı algılar"""
        try:
            tree = event.widget
            region = tree.identify_region(event.x, event.y)
            if region != "cell": return
            
            col = tree.identify_column(event.x)
            if col == "#5":
                item_id = tree.identify_row(event.y)
                if not item_id: return
                self.switch_to_artist_from_chart(override_item_id=item_id)
        except:
            pass

    def switch_to_artist_from_chart(self, override_item_id=None):
        if override_item_id:
            item_id = override_item_id
        else:
            sel = self.tree_chart.selection()
            if not sel: return
            item_id = sel[0]
            
        artist_name = self.chart_map.get(item_id)
        if artist_name:
            self.show_search_view()
            self.entry_artist.delete(0, tk.END)
            self.entry_artist.insert(0, artist_name)
            self.start_search()
