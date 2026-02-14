import os
import glob
import threading
try:
    import yt_dlp
except ImportError:
    yt_dlp = None

DOWNLOAD_DIR = "Downloads"
ARCHIVE_FILE = os.path.join(DOWNLOAD_DIR, "archive.txt")

class Downloader:
    @staticmethod
    def clean_filename(s):
        """Dosya isimleri için güvenli karakter temizliği."""
        if not s: return ""
        s = str(s)
        return "".join([c for c in s if c.isalnum() or c in " -_()."]).strip()

    @staticmethod
    def ensure_dir():
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)

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
        """Dosyayı ve arşiv kaydını siler."""
        # 1. Dosyayı sil
        path = Downloader.get_file_path(video_id, artist, title)
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Silme hatası: {e}")
                return False
        
        # 2. Arşivden sil (youtube video_id)
        if os.path.exists(ARCHIVE_FILE):
            try:
                with open(ARCHIVE_FILE, "r") as f:
                    lines = f.readlines()
                with open(ARCHIVE_FILE, "w") as f:
                    for line in lines:
                        # yt-dlp arşivi genelde "provider id" formatında tutar
                        if video_id not in line:
                            f.write(line)
            except Exception as e:
                print(f"Arşiv güncelleme hatası: {e}")
        return True

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
    def download_song(video_id, title, artist, callback=None):
        """Tek bir şarkıyı indirir (Thread içinde çağrılmalı)."""
        Downloader.ensure_dir()
        if not yt_dlp:
            if callback: callback(False, "yt-dlp modülü eksik.")
            return

        # Dosya ismi formatı: Artist - Title.ext (ID YOK)
        # Karakter temizliği
        clean = Downloader.clean_filename
        
        # Video ID artık isme eklenmiyor
        fname = f"{clean(artist)} - {clean(title)}.%(ext)s"
        
        
        # Tarayıcı Deneme Sırası: Edge -> Chrome -> Firefox -> None (Cookie'siz)
        opts = {
            'format': 'bestaudio[ext=opus]/bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, fname),
            'download_archive': ARCHIVE_FILE,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'nocheckcertificate': True,
            'writethumbnail': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android', 'web'],
                }
            },
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'opus',
                    'preferredquality': '192',
                },
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                },
                # EmbedThumbnail YOK - Manuel yapacağız
            ],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            }
        }
        
        try:
            # 1. İndirme İşlemi
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([f"https://music.youtube.com/watch?v={video_id}"])
            
            # --- Manuel Kapak İşlemi (Pillow + Mutagen) ---
            try:
                from PIL import Image
                import mutagen
                from mutagen.oggopus import OggOpus
                from mutagen.flac import Picture
                
                # Temel dosya adı (uzantısız)
                base_name_full = os.path.join(DOWNLOAD_DIR, f"{clean(artist)} - {clean(title)}")
                
                # Dosyaları bul (.opus ve resim)
                audio_path = None
                image_path = None
                
                # Ses dosyasını bul
                possible_files = glob.glob(f"{glob.escape(base_name_full)}.*")
                for p in possible_files:
                    if p.endswith('.opus'):
                        audio_path = p
                    elif p.endswith('.jpg') or p.endswith('.webp') or p.endswith('.png'):
                        image_path = p
                
                if audio_path and image_path:
                    # A. Resmi Kare Kırp (Pillow)
                    img = Image.open(image_path).convert("RGB")
                    w, h = img.size
                    min_dim = min(w, h)
                    
                    # Merkezden kırp
                    left = (w - min_dim) / 2
                    top = (h - min_dim) / 2
                    right = (w + min_dim) / 2
                    bottom = (h + min_dim) / 2
                    
                    img_cropped = img.crop((left, top, right, bottom))
                    # İsteğe bağlı resize (örn: 500x500) - Şimdilik orijinal boyutta bırakalım, kalite düşmesin.
                    
                    # Geçici olarak kaydet
                    temp_thumb = audio_path.replace(".opus", "_cover.jpg")
                    img_cropped.save(temp_thumb, "JPEG", quality=90)
                    
                    # B. Metadata Göm (Mutagen OggOpus)
                    audio = OggOpus(audio_path)
                    
                    with open(temp_thumb, "rb") as f:
                        image_data = f.read()
                    
                    picture = Picture()
                    picture.data = image_data
                    picture.type = 3 # 3 = Cover (front)
                    picture.mime = u"image/jpeg"
                    picture.desc = u"Album Art"
                    picture.width = img_cropped.width
                    picture.height = img_cropped.height
                    picture.depth = 24
                    
                    # OggOpus resmi 'metadata_block_picture' tagi olarak base64 formatında tutar
                    import base64
                    picture_data = picture.write()
                    base64_picture = base64.b64encode(picture_data).decode('ascii')
                    
                    if audio.tags is None:
                        audio.add_tags()
                    
                    # Eski resimleri silip yenisini ekle
                    audio.tags['metadata_block_picture'] = [base64_picture]
                    audio.save()
                    
                    # Temizlik
                    try:
                        os.remove(image_path) # İndirilen ham resim
                        os.remove(temp_thumb) # Kırpılmış resim
                    except: pass
                    
            except Exception as e:
                print(f"Kapak işleme hatası (PIL/Mutagen): {e}")

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
            base_name = f"{clean(artist)} - {clean(title)}"
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
            
            for strat in strategies:
                try:
                    # SSL Verify False + Session
                    resp = session.get(strat["url"], params=strat["params"], timeout=15, verify=False)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        # /api/get tek obje döner, /api/search liste döner (ama biz get kullanıyoruz şu an)
                        synced = data.get("syncedLyrics", "")
                        if synced:
                            found_lyrics = synced
                            print(f"[LRC] Bulundu ({strat['name']}): {base_name}")
                            break
                    elif resp.status_code == 404:
                        continue # Diğer stratejiye geç
                        
                except Exception as e:
                    print(f"[LRC] Hata ({strat['name']}): {e}")
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
                            if abs(res_dur - duration) <= 3 and res.get("syncedLyrics"):
                                found_lyrics = res.get("syncedLyrics")
                                print(f"[LRC] Bulundu (Geniş Arama): {base_name}")
                                break
                except Exception as ex:
                    print(f"[LRC] Geniş Arama Hatası: {ex}")

            if found_lyrics:
                Downloader.ensure_dir()
                with open(lrc_path, "w", encoding="utf-8") as f:
                    f.write(found_lyrics)
                if callback: callback(True, "İndirildi")
            else:
                print(f"[LRC] Bulunamadı (Tüm Yöntemler): {base_name}")
                if callback: callback(False, "Sözler bulunamadı")
                
        except Exception as e:
            print(f"[LRC] Genel Hata: {e}")
            if callback: callback(False, str(e))

    @staticmethod
    def delete_lyrics(artist, title):
        """Şarkının .lrc dosyasını siler"""
        try:
            clean = Downloader.clean_filename
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
        base_name = f"{clean(artist)} - {clean(title)}"
        lrc_path = os.path.join(DOWNLOAD_DIR, f"{base_name}.lrc")
        return os.path.exists(lrc_path)
