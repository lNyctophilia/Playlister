
import sys
import os

# Add code directory to path
sys.path.append(os.path.join(os.getcwd(), 'Code'))

from ytmusicapi import YTMusic
from utils_downloader import Downloader
import yt_dlp

def debug_metadata(query="mor ve ötesi cambaz"):
    print(f"--- Debugging Metadata for query: '{query}' ---")
    yt = YTMusic()
    
    # 1. Search like ViewSearch does
    print("\n[1] Searching YTMusic (Songs)...")
    results = yt.search(query=query, filter="songs", limit=5)
    
    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} results.")
    
    for i, res in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        title = res.get('title')
        artists = ", ".join([a['name'] for a in res.get('artists', [])])
        album = res.get('album', {}).get('name') if res.get('album') else "Single"
        video_id = res.get('videoId')
        
        print(f"YTMusic Title:  '{title}'")
        print(f"YTMusic Artist: '{artists}'")
        print(f"YTMusic Album:  '{album}'")
        print(f"Video ID:       {video_id}")
        
        # 2. Simulate what yt_dlp would see for this ID
        print(f"\n[2] Extracting Info via yt_dlp for {video_id}...")
        
        opts = {
            'quiet': True,
            'skip_download': True, # We just want info
            'noplaylist': True,
            'extract_flat': False, # Need full info
        }
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"https://music.youtube.com/watch?v={video_id}", download=False)
                
                print(f"yt_dlp 'title':      '{info.get('title')}'")
                print(f"yt_dlp 'artist':     '{info.get('artist')}'")
                print(f"yt_dlp 'album':      '{info.get('album')}'")
                print(f"yt_dlp 'track':      '{info.get('track')}'")
                print(f"yt_dlp 'uploader':   '{info.get('uploader')}'")
                print(f"yt_dlp 'alt_title':  '{info.get('alt_title')}'")
                print(f"yt_dlp 'description': (length: {len(info.get('description', ''))})")
                
                # Check for "crowded" fields
                if info.get('title') and any(x in info.get('title').lower() for x in ['official', 'video', 'clip', 'klip']):
                    print("--> WARNING: Title contains potentially unwanted text.")
                
        except Exception as e:
            print(f"yt_dlp error: {e}")

if __name__ == "__main__":
    debug_metadata()
