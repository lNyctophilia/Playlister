
def parse_views(view_text):
    if not view_text:
        return 0
    
    text = str(view_text).lower()
    for suffix in [" views", " plays", " hits", " subscribers", " abone"]:
        text = text.replace(suffix, "")
    text = text.strip()
    
    multiplier = 1
    if text.endswith("b"):
        multiplier = 1_000_000_000
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 1_000_000
        text = text[:-1]
    elif text.endswith("k"):
        multiplier = 1_000
        text = text[:-1]
        
    try:
        text = text.replace(",", ".")
        return int(float(text) * multiplier)
    except ValueError:
        return 0

def clean_metadata_text(text, remove_artists=None):
    """
    Şarkı isimlerindeki fazlalıkları temizler (Official Video, Lyrics vb.)
    Ayrıca eğer başlık sanatçı adı ile başlıyorsa onu da siler.
    """
    if not text: return ""
    
    # Common Noise removal (Case Insensitive)
    noise_list = [
        "(Official Video)", "(Official Audio)", "(Official Clip)", 
        "(Lyric Video)", "(Lyrics)", 
        "[Official Video]", "[Official Audio]",
        "(Video)", "(Audio)",
        "Official Video", "Official Audio", 
        "| Official Video |",
        "HD", "HQ", "4K", 
        "(Visualizer)", "(Official Visualizer)",
        "(Live)", "(Canlı)", "Canlı Performans"
    ]
    
    clean_text = text
    import re
    
    for noise in noise_list:
        # Case insensitive replace
        pattern = re.compile(re.escape(noise), re.IGNORECASE)
        clean_text = pattern.sub("", clean_text)
    
    clean_text = re.sub(r'\s*\([^)]*\)', '', clean_text)
    clean_text = re.sub(r'\s*\[[^\]]*\]', '', clean_text)
    
    # Remove leading/trailing whitespace/dashes
    clean_text = clean_text.strip(" -|")
    
    # Remove Artist from Title if present
    # e.g. "Artist - Title" -> "Title"
    if remove_artists:
        if isinstance(remove_artists, str):
            remove_artists = [remove_artists]
            
        for artist in remove_artists:
            if not artist: continue
            if clean_text.lower().startswith(artist.lower()):
                clean_text = clean_text[len(artist):]
                clean_text = clean_text.lstrip(" -|:")

        clean_text = re.sub(r'^/\s*[^-]+\s*-\s*', '', clean_text)
    
    # Parantez içi boş kaldıysa sil () veya []
    clean_text = clean_text.replace("()", "").replace("[]", "")
    
    return clean_text.strip()

def parse_duration(time_str):
    """
    "03:45", "1:20:30" gibi süreleri saniyeye çevirir.
    Sıralama işlemleri için kullanılır.
    """
    if not time_str: return 0
    
    # "3:45" -> 225
    parts = str(time_str).split(':')
    try:
        parts = [int(p) for p in parts]
        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except ValueError:
        return 0
    return 0
