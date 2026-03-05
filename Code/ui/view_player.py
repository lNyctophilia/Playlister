import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import webbrowser
from ui import theme as T

try:
    import vlc
    import yt_dlp
except ImportError:
    vlc = None
    yt_dlp = None

class ViewPlayer:
    def setup_player_view(self):
        self.player_frame = tk.Frame(self.root, bg=T.BG_PLAYER, height=80, bd=0, relief=tk.FLAT,
                                     highlightbackground=T.BORDER, highlightthickness=1)
        self.player_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.player_frame.columnconfigure(1, weight=1)
        
        self.player_btn_frame = tk.Frame(self.player_frame, bg=T.BG_PLAYER)
        self.player_btn_frame.grid(row=0, column=0, rowspan=2, padx=10)
        
        btn_frame = self.player_btn_frame
        
        self.btn_player_play = tk.Button(btn_frame, text="▶", font=("Segoe UI", 14), width=4, 
                                         command=self.toggle_player_state, 
                                         bg=T.BG_PLAYER, fg=T.FG_PRIMARY, bd=0, 
                                         activebackground=T.BORDER, activeforeground="#ffffff",
                                         cursor="hand2")
        self.btn_player_play.pack(side=tk.LEFT, padx=5)
        
        self.btn_player_loop = tk.Button(btn_frame, text="🔁", font=("Segoe UI", 12),
                                         command=self.toggle_player_loop,
                                         bg=T.BG_PLAYER, fg=T.FG_SECONDARY, bd=0, 
                                         activebackground=T.BORDER, activeforeground="#ffffff",
                                         cursor="hand2")
        self.btn_player_loop.pack(side=tk.LEFT, padx=5)

        self.btn_player_shuffle = tk.Button(btn_frame, text="🔀", font=("Segoe UI", 12),
                                            command=self.toggle_player_shuffle,
                                            bg=T.BG_PLAYER, fg=T.FG_SECONDARY, bd=0, 
                                            activebackground=T.BORDER, activeforeground="#ffffff",
                                            cursor="hand2")
        self.btn_player_shuffle.pack(side=tk.LEFT, padx=5)
        self.btn_player_shuffle.pack_forget()

        info_frame = tk.Frame(self.player_frame, bg=T.BG_PLAYER)
        info_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=(5,0))
        
        self.lbl_player_title = tk.Label(info_frame, text="Müzik Seçilmedi", bg=T.BG_PLAYER, fg=T.FG_PRIMARY, 
                                         font=(T.FONT_FAMILY, 10, "bold"))
        self.lbl_player_title.pack(anchor=tk.W)
        
        slider_frame = tk.Frame(self.player_frame, bg=T.BG_PLAYER)
        slider_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=(0,5))
        
        self.var_time = tk.DoubleVar()
        self.scale_time = ttk.Scale(slider_frame, from_=0, to=100, variable=self.var_time, command=self.on_seek_start)
        self.scale_time.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.scale_time.bind("<ButtonRelease-1>", self.on_seek_end)
        
        self.lbl_player_time = tk.Label(slider_frame, text="00:00 / 00:00", bg=T.BG_PLAYER, fg=T.FG_SECONDARY, 
                                        font=(T.FONT_MONO, 8))
        self.lbl_player_time.pack(side=tk.LEFT, padx=5)

        vol_frame = tk.Frame(self.player_frame, bg=T.BG_PLAYER)
        vol_frame.grid(row=0, column=2, rowspan=2, padx=10)
        
        tk.Label(vol_frame, text="🔊", bg=T.BG_PLAYER, fg=T.FG_PRIMARY).pack(side=tk.LEFT)
        
        self.scale_vol = ttk.Scale(vol_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=80, command=self.set_player_volume)
        self.scale_vol.set(70)
        self.scale_vol.pack(side=tk.LEFT, padx=5)
        
        self.update_player_loop()

    def set_player_mode(self, mode):
        self.current_play_mode = mode
        if mode == "fav":
            if hasattr(self, 'btn_player_shuffle'):
                self.btn_player_shuffle.pack(side=tk.LEFT, padx=5)
        else:
            if hasattr(self, 'btn_player_shuffle'):
                self.btn_player_shuffle.pack_forget()
            self.loop_state = 0
            self.is_looping = False
            self.btn_player_loop.config(fg=T.FG_SECONDARY, text="🔁")
            self.is_shuffling = False
            self.btn_player_shuffle.config(fg=T.FG_SECONDARY)

    def play_music_start(self, video_id, title_info="Yükleniyor..."):
        if not self.player:
            messagebox.showinfo("Player Hatası", "VLC Modülü bulunamadı. Lütfen VLC Player ve python-vlc kurulumunu yapın.\nŞarkı tarayıcıda açılıyor.")
            webbrowser.open(f"https://music.youtube.com/watch?v={video_id}")
            return
            
        self.lbl_player_title.config(text=f"Yükleniyor: {title_info}...")
        self.btn_player_play.config(text="⏳")
        
        threading.Thread(target=self.player_load_thread, args=(video_id, title_info), daemon=True).start()

    def player_load_thread(self, video_id, title_info):
        try:
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'noplaylist': True,
                'quiet': True,
                'nocheckcertificate': True,
                'ignoreerrors': True,
                'no_warnings': True,
                'cachedir': False,
                'extractor_args': {'youtube': {'player_client': ['ios', 'android', 'web']}},
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_id, download=False)
                if not info:
                     self.update_status("Video bilgisi alınamadı.", "red")
                     self.root.after(0, lambda: self.btn_player_play.config(text="▶"))
                     return

                url = info.get('url')
                duration = info.get('duration', 0)
                http_headers = info.get('http_headers', {})
                
            if url:
                self.root.after(0, lambda: self.start_vlc_stream(url, duration, title_info, http_headers))
            else:
                self.update_status("Ses linki alınamadı (URL yok).", "red")
                self.root.after(0, lambda: self.btn_player_play.config(text="▶"))
        except Exception as e:
            self.update_status(f"Oynatma hatası: {e}", "red")
            self.root.after(0, lambda: self.btn_player_play.config(text="▶"))

    def start_vlc_stream(self, url, duration, title, http_headers=None):
        self.player.stop()
        media = self.vlc_instance.media_new(url)
        
        if http_headers:
            if 'User-Agent' in http_headers:
                media.add_option(f":http-user-agent={http_headers['User-Agent']}")
            if 'Referer' in http_headers:
                media.add_option(f":http-referrer={http_headers['Referer']}")
            
        self.player.set_media(media)
        self.player.play()
        
        self.is_playing = True
        self.total_duration = duration
        self.lbl_player_title.config(text=title)
        self.btn_player_play.config(text="⏸")
        self.scale_time.config(to=duration)
        
        vol = int(self.scale_vol.get())
        self.player.audio_set_volume(vol)

    def toggle_player_state(self):
        if not self.player: return
        if self.is_playing:
            self.player.pause()
            self.btn_player_play.config(text="▶")
            self.is_playing = False
        else:
            self.player.play()
            self.btn_player_play.config(text="⏸")
            self.is_playing = True

    def toggle_player_shuffle(self):
        self.is_shuffling = not self.is_shuffling
        if self.is_shuffling:
            self.btn_player_shuffle.config(fg="#2ed573")
        else:
            self.btn_player_shuffle.config(fg=T.FG_SECONDARY)

    def toggle_player_loop(self):
        if self.current_play_mode == "fav":
            self.loop_state = (self.loop_state + 1) % 3
            if self.loop_state == 0:
                self.btn_player_loop.config(fg=T.FG_SECONDARY, text="🔁")
                self.is_looping = False
            elif self.loop_state == 1:
                self.btn_player_loop.config(fg="#2ed573", text="🔁")
                self.is_looping = False
            elif self.loop_state == 2:
                self.btn_player_loop.config(fg="#2ed573", text="🔂")
                self.is_looping = True
        else:
            self.is_looping = not self.is_looping
            if self.is_looping:
                self.btn_player_loop.config(fg="#2ed573")
            else:
                self.btn_player_loop.config(fg=T.FG_SECONDARY)

    def set_player_volume(self, val):
        if self.player:
            self.player.audio_set_volume(int(float(val)))

    def on_seek_start(self, val):
        self.is_dragging_time = True

    def on_seek_end(self, event):
        if self.player:
            time_sec = self.var_time.get()
            self.player.set_time(int(time_sec * 1000))
        self.is_dragging_time = False

    def update_player_loop(self):
        if self.player and vlc:
            state = self.player.get_state()
            
            if state == vlc.State.Ended:
                if self.is_looping:
                    self.player.stop()
                    self.player.play()
                else:
                    if self.current_play_mode == "fav":
                        self.play_next_in_playlist()
                    else:
                        self.is_playing = False
                        self.btn_player_play.config(text="▶")

            if not self.is_dragging_time and state == vlc.State.Playing:
                current_ms = self.player.get_time()
                if current_ms >= 0:
                    current_sec = current_ms / 1000
                    self.var_time.set(current_sec)
                    
                    cur_str = time.strftime('%M:%S', time.gmtime(current_sec))
                    tot_str = time.strftime('%M:%S', time.gmtime(self.total_duration))
                    self.lbl_player_time.config(text=f"{cur_str} / {tot_str}")
        
        self.root.after(500, self.update_player_loop)

    def play_next_in_playlist(self):
        if not self.current_playlist:
            self.is_playing = False
            self.btn_player_play.config(text="▶")
            return
            
        import random
        if self.is_shuffling:
            next_index = random.randint(0, len(self.current_playlist) - 1)
        else:
            next_index = self.current_playlist_index + 1
            if next_index >= len(self.current_playlist):
                if self.loop_state == 1:
                    next_index = 0
                else:
                    self.is_playing = False
                    self.btn_player_play.config(text="▶")
                    return
            
        self.current_playlist_index = next_index
        next_song = self.current_playlist[next_index]
        self.play_music_start(next_song['video_id'], f"{next_song['title']} - {next_song['artist']}")
