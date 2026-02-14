from ytmusicapi import YTMusic
import json

def debug_metadata():
    yt = YTMusic()
    query = "UZI - Ou"
    print(f"Searching for: {query}")
    
    results = yt.search(query, filter="songs", limit=1)
    
    if results:
        song = results[0]
        print("\n--- Metadata ---")
        print(json.dumps(song, indent=4, ensure_ascii=False))
        
        print("\n--- Fields ---")
        print(f"Title: {song.get('title')}")
        
        artists = song.get('artists', [])
        print(f"Artists: {[a.get('name') for a in artists]}")
        
        album = song.get('album', {})
        if album:
            print(f"Album Name: {album.get('name')}")
            print(f"Album ID: {album.get('id')}")
        else:
            print("Album: None")
            
    else:
        print("No results found.")

if __name__ == "__main__":
    debug_metadata()
