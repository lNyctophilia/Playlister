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
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android', 'web'],
                }
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '192',
            }],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([f"https://music.youtube.com/watch?v={video_id}"])
            if callback: callback(True, "İndirme Tamamlandı")
        except Exception as e:
            if callback: callback(False, str(e))
