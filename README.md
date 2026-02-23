# 🎵 Playlister

YouTube Music üzerinden sanatçı/şarkı arama, ülke top listeleri, türe göre öneri, favori yönetimi, şarkı indirme ve gömülü müzik çalar sunan bir masaüstü uygulaması.

## ✨ Özellikler

- 🔍 **Sanatçı & Şarkı Arama** — YouTube Music veritabanında detaylı arama
- 🌍 **Ülke Top Listeleri** — 60+ ülkenin güncel müzik trendleri
- 🎸 **Türe Göre Öneri** — Last.fm entegrasyonu ile tür bazlı şarkı keşfi
- ❤️ **Favori Yönetimi** — Beğendiğin şarkıları kaydet, düzenle, filtrele
- ⬇️ **Şarkı İndirme** — Yüksek kalite ses indirme (Opus formatında)
- 🎧 **Gömülü Müzik Çalar** — Uygulama içi VLC tabanlı çalar
- 📝 **Otomatik Şarkı Sözü** — LRCLIB üzerinden senkronize sözler
- 🏷️ **Akıllı Metadata** — Kapak resmi, albüm, tarih bilgisi otomatik düzenleme

## 📋 Gereksinimler

| Gereksinim | Tür | Açıklama |
|---|---|---|
| [Python 3.10+](https://www.python.org/downloads/) | Zorunlu | Uygulamanın çalışma dili |
| [VLC Media Player](https://www.videolan.org/vlc/) | Zorunlu | Uygulama içi müzik çalma |
| [FFmpeg](https://www.gyan.dev/ffmpeg/builds/) | Zorunlu | Ses dönüştürme (yt-dlp için) |
| [Last.fm API Key](https://www.last.fm/api/account/create) | Opsiyonel | Türe göre öneri özelliği için |

### Python Kütüphaneleri

| Kütüphane | Açıklama |
|---|---|
| `ytmusicapi` | YouTube Music API erişimi |
| `yt-dlp` | YouTube'dan ses indirme |
| `python-vlc` | VLC Python bağlantısı |
| `requests` | HTTP istekleri |
| `Pillow` | Kapak resmi düzenleme |
| `mutagen` | Ses dosyası metadata işleme |

---

## 🚀 Kurulum

<details>
<summary><strong>Adım 1 — Python Kurulumu</strong></summary>

### Python 3.10+ Yükleme

1. [Python İndirme Sayfası](https://www.python.org/downloads/)'na gidin
2. **"Download Python 3.x.x"** butonuna tıklayın
3. İndirilen `.exe` dosyasını çalıştırın

> ⚠️ **ÖNEMLİ:** Kurulum ekranının **en altındaki** `Add python.exe to PATH` kutucuğunu **mutlaka işaretleyin**. Bu adımı atlarsanız terminal komutları çalışmaz!

4. **"Install Now"** ile kurulumu tamamlayın
5. Kurulumu doğrulamak için terminali açıp şu komutu girin:

```bash
python --version
```

`Python 3.x.x` gibi bir çıktı görmeniz gerekir.

</details>

<details>
<summary><strong>Adım 2 — Projeyi İndirme</strong></summary>

### Seçenek A: Git ile (Önerilen)

Git yüklüyse terminalde şu komutu girin:

```bash
git clone https://github.com/lNyctophilia/Playlister.git
```

```bash
cd Playlister
```

### Seçenek B: ZIP Olarak

1. Bu sayfanın üstündeki yeşil **"Code"** butonuna tıklayın
2. **"Download ZIP"** seçin
3. ZIP dosyasını istediğiniz konuma çıkarın

</details>

<details>
<summary><strong>Adım 3 — Python Kütüphanelerini Yükleme</strong></summary>

### Tek Komutla Tüm Kütüphaneleri Yükleme

Terminali açıp proje klasörüne gidin, ardından şu komutu çalıştırın:

```bash
pip install ytmusicapi yt-dlp python-vlc requests Pillow mutagen
```

Kurulumu doğrulamak için:

```bash
pip list
```

Çıktıda yukarıdaki paketlerin hepsinin listelendiğinden emin olun.

> 💡 **İpucu:** `pip` komutu çalışmazsa `pip3` deneyin. Hâlâ çalışmıyorsa Python kurulumunda PATH ayarını kontrol edin (Adım 1).

</details>

<details>
<summary><strong>Adım 4 — VLC Media Player Kurulumu</strong></summary>

### VLC Yükleme

1. [VLC İndirme Sayfası](https://www.videolan.org/vlc/)'na gidin
2. **"Download VLC"** butonuna tıklayın
3. İndirilen `.exe` dosyasını çalıştırıp varsayılan ayarlarla kurun

> ⚠️ **ÖNEMLİ:** Sisteminiz 64-bit ise **64-bit sürümünü** indirdiğinizden emin olun. Python sürümünüz ile aynı mimari (32/64-bit) olmalıdır, aksi halde `python-vlc` kütüphanesi VLC'yi bulamaz.

Python mimarinizi kontrol etmek için:

```bash
python -c "import struct; print(struct.calcsize('P') * 8, 'bit')"
```

</details>

<details>
<summary><strong>Adım 5 — FFmpeg Kurulumu</strong></summary>

### FFmpeg Yükleme

FFmpeg, şarkı indirirken ses dönüşümü için gereklidir.

1. [FFmpeg İndirme Sayfası (gyan.dev)](https://www.gyan.dev/ffmpeg/builds/) adresine gidin
2. **"release builds"** bölümünden `ffmpeg-release-essentials.zip` dosyasını indirin
3. ZIP dosyasını bir klasöre çıkarın (örn: `C:\ffmpeg`)
4. Çıkarılan klasörün içindeki `bin` klasörünün yolunu kopyalayın (örn: `C:\ffmpeg\bin`)

### PATH'e Ekleme

5. Windows arama çubuğuna **"Ortam Değişkenlerini Düzenle"** (veya **"Environment Variables"**) yazıp açın
6. **Sistem Değişkenleri** bölümünde `Path` satırını seçip **"Düzenle"** tıklayın
7. **"Yeni"** butonuna tıklayıp kopyaladığınız yolu yapıştırın (örn: `C:\ffmpeg\bin`)
8. **"Tamam"** ile kaydedin

> ⚠️ **ÖNEMLİ:** PATH değişikliğinin geçerli olması için **açık olan tüm terminalleri kapatıp yeniden açmanız** gerekir.

9. Kurulumu doğrulamak için **yeni bir terminal** açıp şu komutu girin:

```bash
ffmpeg -version
```

`ffmpeg version x.x` gibi bir çıktı görmeniz gerekir.

</details>

<details>
<summary><strong>Adım 6 — Last.fm API Key (Opsiyonel)</strong></summary>

### Last.fm API Anahtarı Alma

Bu adım yalnızca **"Türe Göre Öneri"** özelliğini kullanmak istiyorsanız gereklidir. API key olmadan da uygulama çalışır, sadece tür bazlı öneriler devre dışı kalır.

1. [Last.fm API Hesap Oluşturma](https://www.last.fm/api/account/create) sayfasına gidin
2. Hesap oluşturun veya giriş yapın
3. API uygulaması oluşturup API key alın
4. Uygulamayı başlattıktan sonra **⚙ Ayarlar** bölümünden API key'inizi girin

> 💡 Uygulama içinde detaylı bir API key kurulum rehberi bulunmaktadır.

</details>

---

## 🎮 Kullanım

Tüm kurulum adımlarını tamamladıktan sonra uygulamayı başlatmak için:

### Seçenek A: Terminal ile

```bash
python Code/Playlister.py
```

### Seçenek B: Bat Dosyası ile

Proje klasöründeki `Playlister.bat` dosyasına çift tıklayın.

---

## 📁 Proje Yapısı

```
Playlister/
├── Code/
│   ├── Playlister.py          # Ana uygulama dosyası
│   ├── core/                   # Temel modüller (config, crypto, sabitler)
│   ├── services/               # Servis katmanı (indirme, arama motoru)
│   ├── ui/                     # Arayüz modülleri (sekmeler, tema)
│   └── utils/                  # Yardımcı fonksiyonlar
├── Config/                     # Yapılandırma dosyaları
├── Docs/                       # Proje belgeleri
├── Playlister.bat              # Hızlı başlatma
└── README.md
```

---

## 📄 Lisans

Bu proje **All Rights Reserved** lisansı altındadır. Kodun kopyalanması, dağıtılması, değiştirilmesi veya ticari amaçlarla kullanılması **yasaktır**. Detaylar için [LICENSE](LICENSE) dosyasına bakınız.
