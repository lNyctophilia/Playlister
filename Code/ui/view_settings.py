import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from core.crypto import encrypt_text
from core.config_manager import save_config
import webbrowser
from ui import theme as T

class ViewSettings:
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Ayarlar")
        win.geometry("420x370")
        win.config(bg=T.BG_MAIN)
        
        lbl_title = tk.Label(win, text="🔧 Uygulama Ayarları")
        T.style_label(lbl_title, bg=T.BG_MAIN, font=T.FONT_HEADING)
        lbl_title.pack(pady=15)
        
        lf_frame = ttk.LabelFrame(win, text="Last.fm API", padding=10)
        lf_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        def refresh_ui():
            for widget in lf_frame.winfo_children():
                widget.destroy()
                
            if getattr(self, "lastfm_api_key", ""):
                lbl_status = tk.Label(lf_frame, text="DURUM: Kayıtlı ✅", fg="#2ed573", 
                                      font=(T.FONT_MONO, 10, "bold"))
                T.style_label(lbl_status, fg="#2ed573", bg=T.BG_PANEL, font=(T.FONT_MONO, 10, "bold"))
                lbl_status.pack(pady=(0, 10))
                
                lbl_link = tk.Label(lf_frame, text="Kayıtlı API Key'lerini görmek için Last.fm hesabına git", 
                                    fg=T.FG_LINK, cursor="hand2", bg=T.BG_PANEL,
                                    font=(T.FONT_FAMILY, 9, "underline"))
                lbl_link.pack(pady=5)
                lbl_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.last.fm/api/accounts"))
                
                btn_frame = tk.Frame(lf_frame, bg=T.BG_PANEL)
                btn_frame.pack(pady=10)
                
                def delete_key():
                    self.lastfm_api_key = ""
                    save_config({"lastfm_api_key": ""})
                    messagebox.showinfo("Bilgi", "API Anahtarı silindi.")
                    if hasattr(self, 'genre_view') and self.genre_view.winfo_ismapped():
                        self.show_search_view()
                    refresh_ui()
                    
                def change_key():
                    self.lastfm_api_key = "" 
                    refresh_ui()

                btn_change = tk.Button(btn_frame, text="Anahtarı Değiştir", command=change_key)
                T.style_button(btn_change)
                btn_change.pack(side=tk.LEFT, padx=5)

                btn_delete = tk.Button(btn_frame, text="Anahtarı Sil", command=delete_key)
                T.style_button(btn_delete, bg=T.BTN_DANGER, hover_bg=T.BTN_DANGER_HOVER)
                btn_delete.pack(side=tk.LEFT, padx=5)
                
            else:
                lbl_status = tk.Label(lf_frame, text="DURUM: Kayıtlı Değil ❌", fg="#ff4757", 
                                      font=(T.FONT_MONO, 10, "bold"))
                T.style_label(lbl_status, fg="#ff4757", bg=T.BG_PANEL, font=(T.FONT_MONO, 10, "bold"))
                lbl_status.pack(pady=(0, 10))
                
                tut_frame = tk.Frame(lf_frame, bg=T.BG_PANEL)
                tut_frame.pack(fill=tk.X, pady=5)
                
                lbl_s1 = tk.Label(tut_frame, text="1. Adım:")
                T.style_label(lbl_s1, bg=T.BG_PANEL)
                lbl_s1.grid(row=0, column=0, sticky="w")
                link1 = tk.Label(tut_frame, text="Hesap Aç", fg=T.FG_LINK, cursor="hand2", bg=T.BG_PANEL,
                                 font=(T.FONT_FAMILY, 9, "underline"))
                link1.grid(row=0, column=1, sticky="w", padx=5)
                link1.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.last.fm/join"))
                
                lbl_s2 = tk.Label(tut_frame, text="2. Adım:")
                T.style_label(lbl_s2, bg=T.BG_PANEL)
                lbl_s2.grid(row=1, column=0, sticky="w")
                link2 = tk.Label(tut_frame, text="API Key ekranına git ve başvur", fg=T.FG_LINK, cursor="hand2", bg=T.BG_PANEL,
                                 font=(T.FONT_FAMILY, 9, "underline"))
                link2.grid(row=1, column=1, sticky="w", padx=5)
                link2.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.last.fm/api/account/create"))
                
                lbl_s3 = tk.Label(tut_frame, text="3. Adım: Sana verilen API Key'i kopyala ve aşağıdaki alana yapıştır.", 
                                  wraplength=300, justify=tk.LEFT)
                T.style_label(lbl_s3, bg=T.BG_PANEL)
                lbl_s3.grid(row=2, column=0, columnspan=2, sticky="w", pady=(5,0))
                
                input_frame = tk.Frame(lf_frame, bg=T.BG_PANEL)
                input_frame.pack(pady=10)
                
                lbl_key = tk.Label(input_frame, text="API Key:")
                T.style_label(lbl_key, bg=T.BG_PANEL)
                lbl_key.pack(side=tk.LEFT)
                key_entry = tk.Entry(input_frame, width=25)
                T.style_entry(key_entry)
                key_entry.pack(side=tk.LEFT, padx=5)
                
                def save_new_key():
                    key = key_entry.get().strip()
                    if key:
                        self.lastfm_api_key = key
                        enc = encrypt_text(self.lastfm_api_key)
                        save_config({"lastfm_api_key": enc})
                        messagebox.showinfo("Bilgi", "API Anahtarı başarıyla güncellendi.")
                        win.destroy()
                    else:
                        messagebox.showerror("Hata", "Lütfen geçerli bir API Key girin.")

                btn_save = tk.Button(input_frame, text="Kaydet", command=save_new_key)
                T.style_button(btn_save, bg=T.BTN_SUCCESS, hover_bg=T.BTN_SUCCESS_HOVER)
                btn_save.pack(side=tk.LEFT)
                
        refresh_ui()
