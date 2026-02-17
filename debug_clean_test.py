
# Script to test metadata cleaning logic

def clean_metadata_text(text, remove_artists=None):
    if not text: return ""
    
    # 1. Lowercase for checks (but keep original for result if needed, though usually title case is preferred)
    # Actually, let's keep original casing but standardise checks
    
    # Common Noise removal (Case Insensitive)
    noise_list = [
        "(Official Video)", "(Official Audio)", "(Official Clip)", 
        "(Lyric Video)", "(Lyrics)", 
        "[Official Video]", "[Official Audio]",
        "(Video)", "(Audio)",
        "Official Video", "Official Audio", 
        "| Official Video |",
        "HD", "HQ", "4K", 
        "(Visualizer)", "(Official Visualizer)"
    ]
    
    clean_text = text
    for noise in noise_list:
        # Case insensitive replace
        import re
        pattern = re.compile(re.escape(noise), re.IGNORECASE)
        clean_text = pattern.sub("", clean_text)
    
    # Remove leading/trailing whitespace/dashes
    clean_text = clean_text.strip(" -|")
    
    # Remove Artist from Title if present
    # e.g. "Artist - Title" -> "Title"
    if remove_artists:
        if isinstance(remove_artists, str):
            remove_artists = [remove_artists]
            
        for artist in remove_artists:
            if not artist: continue
            # Check if title starts with artist (case insensitive)
            if clean_text.lower().startswith(artist.lower()):
                # Remove it
                clean_text = clean_text[len(artist):]
                # Clean leading separator again
                clean_text = clean_text.lstrip(" -|:")
    
    return clean_text.strip()

# Test Cases
test_cases = [
    ("mor ve ötesi - Cambaz (Official Video)", "mor ve ötesi"),
    ("Cambaz (Official Audio)", "mor ve ötesi"),
    ("BLOK3 - NAPIYOSUN MESELA ? (Official Music)", "BLOK3"),
    ("Imagine Dragons - Believer", "Imagine Dragons"),
    ("Clean Bandit - Rockabye (feat. Sean Paul & Anne-Marie) [Official Video]", "Clean Bandit"),
    ("Normal Song Title", "Some Artist"),
    ("Artist - Song - Remix", "Artist")
]

print("--- Metadata Cleaning Tests ---")
for raw, artist in test_cases:
    cleaned = clean_metadata_text(raw, artist)
    print(f"Original: '{raw}'")
    print(f"Artist:   '{artist}'")
    print(f"Cleaned:  '{cleaned}'")
    print("-" * 30)
