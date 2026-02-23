import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from core.crypto import encrypt_text
from core.config_manager import save_config
import webbrowser

class ViewSettings:
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Ayarlar")
        win.geometry("400x350")
        
        tk.Label(win, text="🔧 Uygulama Ayarları", font=("Helvetica", 14, "bold")).pack(pady=15)
        
        # Last.fm Section
        lf_frame = ttk.LabelFrame(win, text="Last.fm API", padding=10)
        lf_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        def refresh_ui():
            # Arayüzü temizle
            for widget in lf_frame.winfo_children():
                widget.destroy()
                
            if getattr(self, "lastfm_api_key", ""):
                # Key Varsa
                tk.Label(lf_frame, text="DURUM: Kayıtlı ✅", fg="green", font=("Consolas", 10, "bold")).pack(pady=(0, 10))
                
                lbl_link = tk.Label(lf_frame, text="Kayıtlı API Key'lerini görmek için Last.fm hesabına git", fg="blue", cursor="hand2", font=("Helvetica", 9, "underline"))
                lbl_link.pack(pady=5)
                lbl_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.last.fm/api/accounts"))
                
                btn_frame = tk.Frame(lf_frame)
                btn_frame.pack(pady=10)
                
                def delete_key():
                    self.lastfm_api_key = ""
                    save_config({"lastfm_api_key": ""})
                    messagebox.showinfo("Bilgi", "API Anahtarı silindi.")
                    # Eğer 3. Mod açıksa 1. moda at
                    if hasattr(self, 'genre_view') and self.genre_view.winfo_ismapped():
                        self.show_search_view()
                    refresh_ui()
                    
                def change_key():
                    # Sadece arayüzde key yokmuş gibi göstertip tutorial açıyoruz.
                    # Asıl silme işlemini kullanıcının yeni key girmesi/kaydetmesine bırakabiliriz 
                    # ya da geçiçi bir state ile yönetebiliriz. En temizi silmek ya da ekrana form getirmek.
                    self.lastfm_api_key = "" 
                    refresh_ui()

                tk.Button(btn_frame, text="Anahtarı Değiştir", command=change_key, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
                tk.Button(btn_frame, text="Anahtarı Sil", command=delete_key, bg="#F44336", fg="white").pack(side=tk.LEFT, padx=5)
                
            else:
                # Key Yoksa (Tutorial)
                tk.Label(lf_frame, text="DURUM: Kayıtlı Değil ❌", fg="red", font=("Consolas", 10, "bold")).pack(pady=(0, 10))
                
                tut_frame = tk.Frame(lf_frame)
                tut_frame.pack(fill=tk.X, pady=5)
                
                tk.Label(tut_frame, text="1. Adım:").grid(row=0, column=0, sticky="w")
                link1 = tk.Label(tut_frame, text="Hesap Aç", fg="blue", cursor="hand2", font=("Helvetica", 9, "underline"))
                link1.grid(row=0, column=1, sticky="w", padx=5)
                link1.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.last.fm/join"))
                
                tk.Label(tut_frame, text="2. Adım:").grid(row=1, column=0, sticky="w")
                link2 = tk.Label(tut_frame, text="API Key ekranına git ve başvur", fg="blue", cursor="hand2", font=("Helvetica", 9, "underline"))
                link2.grid(row=1, column=1, sticky="w", padx=5)
                link2.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.last.fm/api/account/create"))
                
                tk.Label(tut_frame, text="3. Adım: Sana verilen API Key'i kopyala ve aşağıdaki alana yapıştır.", wraplength=300, justify=tk.LEFT).grid(row=2, column=0, columnspan=2, sticky="w", pady=(5,0))
                
                input_frame = tk.Frame(lf_frame)
                input_frame.pack(pady=10)
                
                tk.Label(input_frame, text="API Key:").pack(side=tk.LEFT)
                key_entry = tk.Entry(input_frame, width=25)
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
                        
                tk.Button(input_frame, text="Kaydet", command=save_new_key, bg="#4CAF50", fg="white").pack(side=tk.LEFT)
                
        refresh_ui()
