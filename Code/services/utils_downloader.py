import os
import sys
import glob
import threading
import re
import subprocess
import shutil
try:
    import yt_dlp
except ImportError:
    yt_dlp = None

from core.constants import DOWNLOAD_DIR, ARCHIVE_FILE

class Downloader:
    @staticmethod
    def clean_filename(s):
        """Dosya isimleri için güvenli karakter temizliği."""
        if not s: return ""
        s = str(s)
        return "".join([c for c in s if c.isalnum() or c in " -_()."]).strip()

    @staticmethod
    def strip_parentheses(s):
        if not s: return ""
        s = re.sub(r'\s*\([^)]*\)', '', str(s))
        s = re.sub(r'\s*\[[^\]]*\]', '', s)
        s = re.sub(r'\s+', ' ', s)
        return s.strip()

    @staticmethod
    def ensure_dir():
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)
            
    # Import Helper
    @staticmethod
    def _clean_meta(text, remove_artists=None):
        from utils.utils import clean_metadata_text
        return clean_metadata_text(text, remove_artists)

    @staticmethod
    def get_file_path(video_id=None, artist=None, title=None):
        """
        Dosyayı bulmaya çalışır. 
        Eskiden: [video_id] ile arıyorduk.
        Şimdi: 'Artist - Title.ext' formatı öncelikli.
        Geriye dönük uyumluluk için [video_id] araması opsiyonel tutulabilir ama 
        kullanıcı artık isimlerde ID istemiyor.
        """
        Downloader.ensure_dir()
        
        # Helper clean -> Artık statik metod: Downloader.clean_filename
        clean = Downloader.clean_filename

        # 1. Yeni Format Kontrolü: "Artist - Title.mp3 / .webm / .m4a"
        if artist and title:
            title = Downloader.strip_parentheses(title)
            base_name = f"{clean(artist)} - {clean(title)}"
            # Uzantı ne olabilir bilmiyoruz, glob ile bakalım
            pattern = os.path.join(DOWNLOAD_DIR, f"{base_name}.*")
            files = glob.glob(pattern)
            # En az bir tane varsa (mp3, webm vs) dön
            # Tam eşleşme olmasına dikkat et (prefix hatası olmasın)
            for f in files:
                # Dosya adını uzantısız al
                fname = os.path.splitext(os.path.basename(f))[0]
                if fname == base_name:
                    return f

        # 2. Eski Format (ID içeren) - Eğer ID verildiyse
        if video_id:
            search_pattern = os.path.join(DOWNLOAD_DIR, f"*[[]{video_id}[]]*")
            files = glob.glob(search_pattern)
            if files: return files[0]
            
        return None

    @staticmethod
    def is_downloaded(video_id=None, artist=None, title=None):
        return Downloader.get_file_path(video_id, artist, title) is not None

    @staticmethod
    def get_downloads_cache():
        """
        Klasördeki dosyaları tek seferde okuyup hafızaya alır.
        Dönüş: (set_of_basenames, list_of_all_filenames)
        """
        Downloader.ensure_dir()
        try:
            all_files = os.listdir(DOWNLOAD_DIR)
            # Uzantısız isim seti (Hızlı erişim için)
            basenames = {os.path.splitext(f)[0] for f in all_files}
            return basenames, all_files
        except:
            return set(), []

    @staticmethod
    def is_downloaded_cached(cache_data, video_id=None, artist=None, title=None):
        """
        Disk I/O yapmadan verilen cache üzerinden kontrol sağlar.
        """
        if not cache_data:
            return False
            
        basenames, all_files = cache_data
        
        # 1. İsim ile kontrol (Hızlı - O(1))
        if artist and title:
            title = Downloader.strip_parentheses(title)
            base_name = f"{Downloader.clean_filename(artist)} - {Downloader.clean_filename(title)}"
            if base_name in basenames:
                return True
                
        # 2. ID ile kontrol (Fallback - Cache üzerinde döngü)
        if video_id:
             id_tag = f"[{video_id}]"
             for f in all_files:
                 if id_tag in f:
                     return True
        
        return False

    @staticmethod
    def delete_content(video_id=None, artist=None, title=None):
        """Dosyayı, .lrc dosyasını, varsa kapak resmini ve arşiv kaydını siler."""
        
        # Dosya yolunu bul (Uzantılı)
        path = Downloader.get_file_path(video_id, artist, title)
        
        # Base name'i bul (Uzantısız)
        base_name_full = None
        if path:
             base_name_full = os.path.splitext(path)[0]
        elif artist and title:
             clean = Downloader.clean_filename
             title = Downloader.strip_parentheses(title)
             base_name_full = os.path.join(DOWNLOAD_DIR, f"{clean(artist)} - {clean(title)}")
        
        deleted_any = False

        # 1. Ana Dosyayı (Audio) Sil
        if path and os.path.exists(path):
            try:
                os.remove(path)
                deleted_any = True
                print(f"Silindi: {path}")
            except Exception as e:
                print(f"Ses Dosyası Silme hatası: {e}")
        
        # 2. Yan Dosyaları Sil (.lrc, .jpg, .webp, .png, .json vb)
        if base_name_full:
            # Glob ile aynı isimdeki tüm uzantıları bul
            # escape yapıyoruz ki köşeli parantez varsa glob bozulmasın
            pattern = f"{glob.escape(base_name_full)}.*"
            related_files = glob.glob(pattern)
            
            for f in related_files:
                # Ana dosyayı zaten sildik veya yukarıda denedik, diğerlerini silelim
                # (Path zaten silindiyse exists False döner sorun olmaz)
                if f != path and os.path.exists(f):
                    try:
                        os.remove(f)
                        print(f"Yan dosya silindi: {f}")
                    except Exception as e:
                        print(f"Yan Dosya ({f}) silme hatası: {e}")

        # 3. Arşivden sil (youtube video_id)
        if video_id:
             Downloader.remove_from_archive(video_id)
                 
        return True # Her zaman True dönüyoruz ki UI güncellensin (Dosya yoksa bile listeden düşsün)

    @staticmethod
    def remove_from_archive(video_id):
        """Verilen video_id'yi yt-dlp arşividen siler (Kullanıcı manuel sildiyse tekrar indirebilmesi için)."""
        if video_id and os.path.exists(ARCHIVE_FILE):
             try:
                 with open(ARCHIVE_FILE, "r") as f:
                     lines = f.readlines()
                 
                 # Eğer satırlarda yoksa hiç yazma işlemi yapıp vakit kaybetme
                 if not any(video_id in line for line in lines):
                     return

                 with open(ARCHIVE_FILE, "w") as f:
                     for line in lines:
                         if video_id not in line:
                             f.write(line)
             except Exception as e:
                 print(f"Arşiv güncelleme hatası: {e}")

    @staticmethod
    def delete_all_downloads():
        """Downloads klasöründeki her şeyi ve arşiv dosyasını siler."""
        Downloader.ensure_dir()
        try:
            # Klasördeki tüm dosyaları sil
            for f in os.listdir(DOWNLOAD_DIR):
                full_path = os.path.join(DOWNLOAD_DIR, f)
                if os.path.isfile(full_path):
                    os.remove(full_path)
            return True
        except Exception as e:
            print(f"Toplu silme hatası: {e}")
            return False

    @staticmethod
    def _fetch_best_cover(info_dict, base_name_full):
        import requests as req
        from PIL import Image
        from io import BytesIO

        song_label = os.path.basename(base_name_full)
        thumbnails = info_dict.get('thumbnails', [])
        if not thumbnails:
            print(f"[Kapak] Bulunamadı: {song_label}")
            return None, 0, 0

        square_thumbs = []
        other_thumbs = []

        for t in thumbnails:
            url = t.get('url', '')
            w = t.get('width', 0) or 0
            h = t.get('height', 0) or 0

            if not url:
                continue

            if w > 0 and h > 0 and w == h:
                square_thumbs.append(t)
            else:
                other_thumbs.append(t)

        square_thumbs.sort(key=lambda x: (x.get('width', 0) or 0), reverse=True)
        other_thumbs.sort(key=lambda x: (x.get('width', 0) or 0), reverse=True)

        ordered_urls = [t['url'] for t in square_thumbs] + [t['url'] for t in other_thumbs]

        for i, url in enumerate(ordered_urls):
            try:
                resp = req.get(url, timeout=10)
                if resp.status_code != 200:
                    continue

                if len(resp.content) < 1000:
                    continue

                img = Image.open(BytesIO(resp.content)).convert("RGB")
                w, h = img.size

                if w != h:
                    min_dim = min(w, h)
                    left = (w - min_dim) / 2
                    top = (h - min_dim) / 2
                    right = (w + min_dim) / 2
                    bottom = (h + min_dim) / 2
                    img = img.crop((left, top, right, bottom))

                buf = BytesIO()
                img.save(buf, "JPEG", quality=90)
                image_data = buf.getvalue()

                final_w, final_h = img.size
                img.close()

                print(f"[Kapak] İndirildi: {song_label}")
                return image_data, final_w, final_h

            except Exception:
                continue

        print(f"[Kapak] Bulunamadı: {song_label}")
        return None, 0, 0

    @staticmethod
    def download_song(video_id, title, artist, album=None, callback=None):
        """Tek bir şarkıyı indirir (Thread içinde çağrılmalı)."""
        Downloader.ensure_dir()
        if not yt_dlp:
            if callback: callback(False, "yt-dlp modülü eksik.")
            return

        # Kullanıcı butona bastıysa tekrar indirmek istiyordur (yerelden silmiş olabilir)
        # O yüzden yt-dlp'nin "zaten indirildi" dememesi için video_id'yi archive'den çıkar.
        Downloader.remove_from_archive(video_id)

        clean = Downloader.clean_filename
        file_title = Downloader.strip_parentheses(title)
        
        fname = f"{clean(artist)} - {clean(file_title)}.%(ext)s"
        
        
        # Tarayıcı Deneme Sırası: Edge -> Chrome -> Firefox -> None (Cookie'siz)
        exe_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]))
        ffmpeg_path = os.path.join(exe_dir, 'ffmpeg.exe')

        opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, fname),
            'download_archive': ARCHIVE_FILE,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'nocheckcertificate': True,
            'writethumbnail': False,
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android', 'web'],
                }
            },
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                    'preferredquality': '192',
                },
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                },
            ],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            }
        }

        if os.path.exists(ffmpeg_path):
            opts['ffmpeg_location'] = exe_dir
        
        try:
            # 1. İndirme İşlemi ve Bilgi Çekimi (Tarih formatı için)
            song_date = None
            info_dict = None
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                try:
                    info_dict = ydl.extract_info(f"https://music.youtube.com/watch?v={video_id}", download=True)
                except Exception as dl_err:

                    # Hata alırsak "Sanatçı - Şarkı Adı" ile arama yap ve ilk çıkanı indir
                    search_query = f"ytsearch1:{artist} {title} audio"
                    info_dict = ydl.extract_info(search_query, download=True)
                    
                    # Eğer search üzerinden bir id dönüyorsa onu baz al
                    if 'entries' in info_dict and len(info_dict['entries']) > 0:
                        info_dict = info_dict['entries'][0]

                if not info_dict:
                     raise Exception("Video veya alternatif arama bulunamadı.")
                
                # Tarih objesini al: öncelik release_date, olmazsa upload_date (Gelen format genelde '20260326')
                raw_date = info_dict.get('release_date') or info_dict.get('upload_date')
                if raw_date and len(raw_date) == 8 and raw_date.isdigit():
                    # YYYYMMDD -> YYYY-MM-DD Dönüşümü
                    song_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
                elif raw_date and len(raw_date) == 4 and raw_date.isdigit():
                    # Sadece YYYY geldiyse
                    song_date = raw_date

            # İndirme sonrası dosya kontrolü
            base_name_full = os.path.join(DOWNLOAD_DIR, f"{clean(artist)} - {clean(file_title)}")
            possible_files = glob.glob(f"{glob.escape(base_name_full)}.*")
            audio_found = any(p.endswith('.m4a') for p in possible_files)

            if not audio_found:
                 raise Exception("İndirme işlemi tamamlandı görünüyor ancak dosya oluşmadı.")
            
            # --- Manuel Kapak ve Metadata İşlemi (Pillow + Mutagen) ---
            try:
                from PIL import Image
                import requests as req
                from mutagen.mp4 import MP4, MP4Cover

                base_name_full = os.path.join(DOWNLOAD_DIR, f"{clean(artist)} - {clean(file_title)}")
                
                audio_path = None
                possible_files = glob.glob(f"{glob.escape(base_name_full)}.*")
                for p in possible_files:
                    if p.endswith('.m4a'):
                        audio_path = p
                
                if audio_path:
                    audio = MP4(audio_path)

                    clean_title = Downloader._clean_meta(title, remove_artists=[artist])
                    clean_artist = Downloader._clean_meta(artist)

                    final_album = str(album) if album else None
                    if not final_album or \
                       not final_album.strip() or \
                       final_album.strip().lower() in ["unknown album", "single"]:
                        clean_album = clean_title
                    else:
                        clean_album = Downloader._clean_meta(final_album)

                    audio.tags['\xa9nam'] = [clean_title]
                    audio.tags['\xa9ART'] = [clean_artist]
                    audio.tags['aART'] = [clean_artist]
                    audio.tags['\xa9wrt'] = [clean_artist]
                    audio.tags['\xa9alb'] = [clean_album]
                    
                    if song_date:
                        audio.tags['\xa9day'] = [song_date]

                    cover_image_data = None
                    cover_width = 0
                    cover_height = 0

                    if info_dict:
                        cover_image_data, cover_width, cover_height = Downloader._fetch_best_cover(
                            info_dict, base_name_full
                        )

                    if cover_image_data:
                        audio.tags['covr'] = [
                            MP4Cover(cover_image_data, imageformat=MP4Cover.FORMAT_JPEG)
                        ]

                    audio.save()
                    
                    # --- FastStart Metadatasını Başa Al ---
                    try:
                        ffmpeg_cmd_path = ffmpeg_path if os.path.exists(ffmpeg_path) else 'ffmpeg'
                        temp_audio = audio_path + ".tmp.m4a"
                        subprocess.run([
                            ffmpeg_cmd_path, "-y", "-i", audio_path,
                            "-c", "copy", "-movflags", "+faststart",
                            temp_audio
                        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                        
                        if os.path.exists(temp_audio) and os.path.getsize(temp_audio) > 0:
                            shutil.move(temp_audio, audio_path)
                    except Exception as fe:
                        print(f"[FastStart] Hata: {fe}")
                    # --------------------------------------
                    
            except Exception as e:
                print(f"[Kapak] HATA: {clean(artist)} - {clean(file_title)} - {e}")

            # --- Otomatik Şarkı Sözü İndirme ---
            try:
                # Süreyi dosyadan okumaya çalış (en doğrusu budur)
                duration_sec = 0
                if audio_path:
                    try:
                        audio_info = MP4(audio_path)
                        duration_sec = audio_info.info.length
                    except: pass
                
                # Eğer dosyadan okuyamazsak 0 göndeririz, download_lyrics API'si idare eder.
                # Arka planda sessizce indirsin, kullanıcıyı bekletmesin veya log kirliliği yapmasın
                # Ancak 'callback' vermezsek hata durumunda sessiz kalır, bu istenen bir durum.
                # Şarkı başarılı indiği için callback(True) döneceğiz, sözler ekstra.

                threading.Thread(target=Downloader.download_lyrics, args=(title, artist, final_album, duration_sec), daemon=True).start()
                
            except Exception as e:
                print(f"[LRC] HATA: {clean(artist)} - {clean(file_title)} - {e}")

            print(f"[Şarkı] İndirildi: {clean(artist)} - {clean(file_title)}")
            if callback: callback(True, "İndirme Tamamlandı")
        except Exception as e:
            if callback: callback(False, str(e))

    @staticmethod
    def _get_session():
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        return session

    @staticmethod
    def download_lyrics(title, artist, album, duration, callback=None):
        """LRCLIB API üzerinden şarkı sözlerini indirir (.lrc)"""
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            clean = Downloader.clean_filename
            file_title = Downloader.strip_parentheses(title)
            base_name = f"{clean(artist)} - {clean(file_title)}"
            lrc_filename = f"{base_name}.lrc"
            lrc_path = os.path.join(DOWNLOAD_DIR, lrc_filename)
            
            if os.path.exists(lrc_path):
                print(f"[LRC] Zaten mevcut: {base_name}")

                if callback: callback(True, "Zaten mevcut")
                return

            session = Downloader._get_session()
            url_get = "https://lrclib.net/api/get"
            url_search = "https://lrclib.net/api/search"
            
            # Stratejiler
            strategies = []
            
            # 1. Tam Eşleşme
            strategies.append({
                "name": "Tam Eşleşme",
                "url": url_get,
                "params": {"artist_name": artist, "track_name": title, "album_name": album, "duration": duration}
            })
            
            # 2. Albümsüz
            strategies.append({
                 "name": "Albümsüz Deneme",
                 "url": url_get,
                 "params": {"artist_name": artist, "track_name": title, "duration": duration}
            })
            
            # 3. İlk Sanatçı (Eğer birden fazlaysa)
            # "Lvbel C5, AKDO, ALIZADE" -> "Lvbel C5"
            primary_artist = artist.split(',')[0].split('&')[0].split(' ft.')[0].split(' feat.')[0].strip()
            if primary_artist != artist:
                strategies.append({
                    "name": f"İlk Sanatçı ({primary_artist})",
                    "url": url_get,
                    "params": {"artist_name": primary_artist, "track_name": title, "duration": duration}
                })

            found_lyrics = None
            found_plain_lyrics = None
            
            for strat in strategies:
                try:
                    # SSL Verify False + Session
                    resp = session.get(strat["url"], params=strat["params"], timeout=15, verify=False)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        # /api/get tek obje döner, /api/search liste döner (ama biz get kullanıyoruz şu an)
                        synced = data.get("syncedLyrics", "")
                        plain = data.get("plainLyrics", "")

                        if synced:
                            found_lyrics = synced
                            break
                        elif plain and not found_plain_lyrics:
                             found_plain_lyrics = plain

                    elif resp.status_code == 404:
                        continue # Diğer stratejiye geç
                        
                except Exception as e:

                    continue

            # Eğer hala bulunamadıysa Search API deneyelim (Daha geniş arama)
            if not found_lyrics:
                try:
                    search_params = {"q": f"{artist} {title}"}
                    resp = session.get(url_search, params=search_params, timeout=15, verify=False)
                    if resp.status_code == 200:
                        results = resp.json() # Liste döner
                        # Süreye en yakın olanı seç (+- 3 sn)
                        for res in results:
                            res_dur = res.get("duration", 0)
                            if abs(res_dur - duration) <= 3:
                                if res.get("syncedLyrics"):
                                    found_lyrics = res.get("syncedLyrics")
                                    break
                                elif res.get("plainLyrics") and not found_plain_lyrics:
                                    found_plain_lyrics = res.get("plainLyrics")

                except Exception:
                    pass

            if found_lyrics:
                Downloader.ensure_dir()
                with open(lrc_path, "w", encoding="utf-8") as f:
                    f.write(found_lyrics)
                print(f"[LRC] Synced indirildi: {base_name}")
                if callback: callback(True, "İndirildi")
            elif found_plain_lyrics:
                try:
                    from mutagen.mp4 import MP4
                    audio_file = Downloader.get_file_path(artist=artist, title=title)
                    if audio_file and audio_file.endswith('.m4a'):
                        audio = MP4(audio_file)
                        audio.tags['\xa9lyr'] = [found_plain_lyrics]
                        audio.save()
                        print(f"[LRC] Plain text gömüldü: {base_name}")
                        if callback: callback(True, "Sözler (Düz Metin) Gömüldü")
                    else:
                        print(f"[LRC] HATA: Ses dosyası bulunamadı - {base_name}")
                        if callback: callback(False, "Ses dosyası bulunamadı")
                except Exception as embed_err:
                    print(f"[LRC] HATA: {base_name} - {embed_err}")
                    if callback: callback(False, str(embed_err))
            else:
                print(f"[LRC] Bulunamadı: {base_name}")
                if callback: callback(False, "Sözler bulunamadı")
                
        except Exception as e:
            print(f"[LRC] HATA: {e}")
            if callback: callback(False, str(e))

    @staticmethod
    def delete_lyrics(artist, title):
        """Şarkının .lrc dosyasını siler"""
        try:
            clean = Downloader.clean_filename
            title = Downloader.strip_parentheses(title)
            base_name = f"{clean(artist)} - {clean(title)}"
            lrc_path = os.path.join(DOWNLOAD_DIR, f"{base_name}.lrc")
            
            if os.path.exists(lrc_path):
                os.remove(lrc_path)
                return True
            return False
        except Exception as e:
            print(f"LRC Silme Hatası: {e}")
            return False

    @staticmethod
    def is_lrc_downloaded(artist, title):
        clean = Downloader.clean_filename
        title = Downloader.strip_parentheses(title)
        base_name = f"{clean(artist)} - {clean(title)}"
        lrc_path = os.path.join(DOWNLOAD_DIR, f"{base_name}.lrc")
        return os.path.exists(lrc_path)
