import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from utils import encrypt_text

class ViewSettings:
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Ayarlar")
        win.geometry("400x250")
        
        tk.Label(win, text="🔧 Uygulama Ayarları", font=("Helvetica", 14, "bold")).pack(pady=15)
        
        # Last.fm Section
        lf_frame = ttk.LabelFrame(win, text="Last.fm API", padding=10)

        lf_frame.pack(fill=tk.X, padx=20, pady=10)
        
        status_text = "DURUM: Kayıtlı ✅" if self.lastfm_api_key else "DURUM: Kayıtlı Değil ❌"
        lbl_status = tk.Label(lf_frame, text=status_text, fg="green" if self.lastfm_api_key else "red", font=("Consolas", 10, "bold"))
        lbl_status.pack()
        
        btn_frame = tk.Frame(lf_frame)
        btn_frame.pack(pady=10)
        
        def delete_key():
            self.lastfm_api_key = ""
            self.save_config({"lastfm_api_key": ""})
            lbl_status.config(text="DURUM: Silindi ❌", fg="red")
            messagebox.showinfo("Bilgi", "API Anahtarı silindi.")
            win.destroy()
            # Eğer 3. Mod açıksa 1. moda at
            if self.genre_view.winfo_ismapped():
                self.show_search_view()
            
        def new_key():
            key = simpledialog.askstring("API Key", "Yeni API Key Girin:", parent=win)
            if key:
                self.lastfm_api_key = key.strip()
                enc = encrypt_text(self.lastfm_api_key)
                self.save_config({"lastfm_api_key": enc}) # Save encrypted
                lbl_status.config(text="DURUM: Güncellendi ✅", fg="green")
                messagebox.showinfo("Bilgi", "API Anahtarı güncellendi.")
                win.destroy()

        tk.Button(btn_frame, text="Yeni Gir", command=new_key, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Anahtarı Sil", command=delete_key, bg="#F44336", fg="white").pack(side=tk.LEFT, padx=5)
