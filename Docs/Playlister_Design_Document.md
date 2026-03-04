# Playlister - Design Document

## 1. Genel Bakış
**Proje Adı:** Playlister
**Amaç:** YouTube Music API üzerinden şarkı arama, listeleme, favori yönetimi, indirme ve çalma özellikli masaüstü müzik yöneticisi.
**Hedef OS:** Windows

## 2. Teknik Altyapı
- **Dil:** Python
- **UI Framework:** Tkinter (ttk ile birlikte)
- **Müzik API:** `ytmusicapi` (YouTube Music)
- **Müzik Çalar:** python-vlc (VLC bindings)
- **İndirme Motoru:** yt-dlp + FFmpeg (ses dönüştürme)
- **Kapak Resmi:** Pillow (görsel işleme)
- **Metadata Düzenleme:** mutagen (M4A/MP4 tag)
- **Şarkı Sözleri API:** LRCLIB
- **Müzik Metadata:** Last.fm API (tür bazlı öneriler için)
- **Veri Formatı:** JSON (config + favorites)
- **Şifreleme:** XOR + Base64 (API anahtarı koruma)
- **Build:** Nuitka (standalone exe)
- **Installer:** Inno Setup

## 3. Proje Mimarisi
Modüler Mixin tabanlı mimari kullanılmaktadır. `App` sınıfı tüm Mixin'leri birleştirerek tek bir uygulama nesnesi oluşturur.

### 3.1. Çekirdek Katman (`core/`)
- **`constants.py`** — Sabit dosya yolları ve değerler (FAV_FILE, CONFIG_FILE, DOWNLOAD_DIR, ARCHIVE_FILE)
- **`config_manager.py`** — JSON tabanlı konfigürasyon okuma/yazma (load_config, save_config)
- **`crypto.py`** — XOR + Base64 şifreleme/çözme (API anahtarı koruma)
- **`favorites_manager.py`** — Favori CRUD işlemleri (load, save, is_favorite, toggle)

### 3.2. Servis Katmanı (`services/`)
- **`search_engine.py`** — Arama motoru: sanatçı eşleştirme, fuzzy duplicate tespiti, filtreleme, sıralama listeleri oluşturma
- **`utils_downloader.py`** — `Downloader` sınıfı: şarkı indirme, metadata gömme (ID3 tag), kapak resmi, şarkı sözleri (.lrc), dosya yönetimi, arşiv kontrolü

### 3.3. Arayüz Katmanı (`ui/`)
- **`theme.py`** — Merkezi tema: renk paleti, font tanımları, stil fonksiyonları (style_button, style_entry, style_label, configure_ttk_styles)
- **`ui_shared.py`** — Ortak UI mantığı: durum çubuğu, view geçişleri, tooltip sistemi, indirme/silme ortak işlemleri, ToolTip sınıfı
- **`view_search.py`** — Sanatçı & Şarkı arama ekranı, 3 sekmeli sonuç listeleri (Popülerlik, Dinlenme, Karma)
- **`view_charts.py`** — Ülke top listeleri ekranı, ülke seçimi ve sanatçıya geçiş
- **`view_genre.py`** — Türe göre öneri ekranı (Last.fm API)
- **`view_fav.py`** — Favoriler ekranı: listeleme, sıralama, tekli/toplu indirme, durdurma, silme
- **`view_player.py`** — Müzik çalar: VLC stream, play/pause, loop, ses kontrolü, ilerleme çubuğu
- **`view_settings.py`** — Ayarlar penceresi: Last.fm API key yönetimi, tutorial ekranı
- **`context_menu.py`** — Sağ tık menü mixin: Oynat, Link Kopyala, Favorilere Ekle/Çıkar, İndir/Sil

### 3.4. Yardımcı Katman (`utils/`)
- **`utils.py`** — parse_views (dinlenme sayısı ayrıştırma), clean_metadata_text (başlık temizleme), parse_duration (süre dönüştürme)

## 4. UI/UX Tasarım
**Tema:** Modern Koyu Lacivert (Dark Blue)
**Renk Paleti:**
- Ana Arka Plan: `#0a0e27`
- Panel: `#141832`
- Navigasyon: `#0d1230`
- Vurgu (Primary): `#3b5bdb` / `#4c6ef5` (indigo-mavi)
- Metin: `#e8eaed` (birincil), `#8b95a5` (ikincil)
- Link: `#74b9ff`

**Font:** Segoe UI (genel), Consolas (mono/status)

**Temel Layout Elemanları:**
- **Üst Navigasyon Çubuğu:** Sanatçı & Şarkı Arama, Ülke Top Listeleri, Türe Göre Öneri, Favoriler, Ayarlar butonları
- **Merkez İçerik Alanı:** Seçilen view'e göre dinamik içerik (arama sonuçları, listeler, favoriler)
- **Alt Çalar Barı:** Play/Pause, Loop, Volume slider, İlerleme çubuğu, Şarkı bilgisi
- **Durum Çubuğu:** En altta, anlık durum mesajları
- **Sağ Tık Menüsü:** Oynat, Link Kopyala, Favorilere Ekle/Çıkar, İndir/Sil

## 5. Temel Özellikler

### 5.1. Sanatçı Arama
- Sanatçı ismiyle YouTube Music üzerinden arama
- Progressive Search algoritması (batch'ler halinde sonuç getirme, UI donmasını engelleme)
- Search ID ile race condition önleme
- 3 farklı sıralama listesi: Popülerlik, En Çok Dinlenen, Karma Öneri
- Fuzzy duplicate tespiti (SequenceMatcher, %85 eşik)
- Çok sanatçılı sorgu desteği (ft, feat, &, ve, x, +, / ayrıştırma)

### 5.2. Şarkı Arama
- Şarkı ismiyle doğrudan YouTube Music araması
- Dropdown ile arama modu seçimi (Sanatçı / Şarkı)

### 5.3. Ülke Top Listeleri
- YouTube Music charts verilerini çekme
- Ülke seçimi (dropdown)
- Listeden sanatçıya geçiş özelliği

### 5.4. Türe Göre Öneri
- Last.fm API ile müzik türüne göre şarkı önerileri
- API key gerektiren özellik (Ayarlar'dan yönetilir)
- Ülke ve tür seçimi

### 5.5. Favoriler
- Şarkı kaydetme ve listeleme
- Sütun bazında sıralama
- Tekli indirme/silme (satır bazında butonlar)
- Toplu indirme (Tümünü İndir / Durdur toggle)
- İndirme durumu ikonları ile anlık gösterim
- İndirme klasörünü açma

### 5.6. Müzik Çalar
- VLC tabanlı HTTP stream çalma
- Play/Pause, tekrar (loop) modu
- Ses kontrolü (volume slider)
- İlerleme çubuğu (sürükleme ile konum değiştirme)
- Şarkı bilgisi gösterimi

### 5.7. Müzik İndirme
- yt-dlp ile yüksek kalitede AAC (M4A) indirme
- Gömülü FFmpeg desteği: exe yanındaki `ffmpeg.exe` otomatik kullanılır, PATH'e gerek yok
- Metadata gömme: başlık, sanatçı, albüm, tarih, kapak resmi (mutagen MP4)
- Kapak resmi: kare kırpma, kalite optimizasyonu (Pillow)
- Şarkı sözleri otomatik indirme (.lrc, senkronize veya düz metin)
- Dosya isimlendirme: `Sanatçı - Şarkı.ext` formatı
- Arşiv sistemi: tekrar indirmeyi önleme, silinen dosyaları arşivden otomatik kaldırma

### 5.8. Şarkı Sözleri
- LRCLIB API üzerinden senkronize şarkı sözleri (.lrc)
- Senkronize bulunamazsa düz metin (plaintext) indirme
- Şarkı silindiğinde .lrc dosyası da otomatik silinir

### 5.9. Ayarlar
- Last.fm API key yönetimi: kaydetme, değiştirme, silme
- API key yoksa adım adım tutorial ekranı (hesap açma, başvuru, yapıştırma)
- Tüm linkler tıklanabilir

## 6. Veri Yönetimi
- **Konfigürasyon:** `Config/config.json` — Last.fm API key (XOR + Base64 ile şifreli)
- **Favoriler:** `Config/favorites.json` — Şarkı listesi (JSON array, video_id, title, artist, album, views_text, duration)
- **İndirme Dizini:** `~/Music/Playlister/`
- **Arşiv Dosyası:** `~/Music/Playlister/archive.txt` — yt-dlp indirme geçmişi

## 7. Dosya Yapısı
```
Playlister/
├── Code/
│   ├── Playlister.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── config_manager.py
│   │   ├── crypto.py
│   │   └── favorites_manager.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── search_engine.py
│   │   └── utils_downloader.py
│   ├── ui/
│   │   ├── theme.py
│   │   ├── ui_shared.py
│   │   ├── view_search.py
│   │   ├── view_charts.py
│   │   ├── view_genre.py
│   │   ├── view_fav.py
│   │   ├── view_player.py
│   │   ├── view_settings.py
│   │   └── context_menu.py
│   └── utils/
│       ├── __init__.py
│       └── utils.py
├── Config/
│   ├── config.json
│   └── favorites.json
├── Docs/
│   ├── Playlister_Design_Document.md
│   └── Screenshots/
├── Requriements/
│   └── GEREKLI_DOSYALAR.txt
├── Build&SetupCode.md
├── installer.iss
├── .gitignore
└── README.md
```

## 8. Bağımlılıklar

### Python Kütüphaneleri
- `ytmusicapi` — YouTube Music API erişimi
- `python-vlc` — VLC medya çalar bağlantısı
- `yt-dlp` — YouTube içerik indirme
- `requests` — HTTP istekleri (Last.fm, LRCLIB)
- `mutagen` — Ses dosyası metadata düzenleme (MP4 tag)
- `Pillow` — Kapak resmi işleme (kırpma, dönüştürme)
- `tkinter` — Standart kütüphane (GUI)

### Harici Bağımlılıklar (Build'e Gömülü)
- `ffmpeg.exe` — Ses dönüştürme (yt-dlp postprocessor)
- `libvlc.dll` + `libvlccore.dll` + `plugins/` — VLC medya çalar
- `VC_redist.x64.exe` — Visual C++ Runtime (setup ile otomatik kurulur)

## 9. Dağıtım
- **Build:** Nuitka `--standalone` ile tek klasör halinde derleme
- **Installer:** Inno Setup ile `Playlister_Setup.exe` oluşturma
- **Gömülü Bağımlılıklar:** VLC DLL'leri, FFmpeg ve VC++ Runtime setup içinde
- **Dağıtım Kanalı:** GitHub Releases üzerinden setup dosyası paylaşımı
- **Hedef:** Kullanıcının Python, VLC veya FFmpeg kurmasına gerek kalmadan çalışma
