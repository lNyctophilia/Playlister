import json
import os
from constants import FAV_FILE

def load_favorites():
    if os.path.exists(FAV_FILE):
        try:
            with open(FAV_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_favorites(favorites):
    try:
        os.makedirs(os.path.dirname(FAV_FILE), exist_ok=True)
        with open(FAV_FILE, "w", encoding="utf-8") as f:
            json.dump(favorites, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Fav Save Error: {e}")

def is_favorite(favorites, video_id):
    return any(f['video_id'] == video_id for f in favorites)

def toggle_favorite(favorites, song_data):
    video_id = song_data.get('video_id')
    if is_favorite(favorites, video_id):
        favorites[:] = [f for f in favorites if f['video_id'] != video_id]
        save_favorites(favorites)
        return False
    else:
        saved_item = {
            "video_id": video_id,
            "title": song_data.get('title'),
            "artist": song_data.get('artist'),
            "album": song_data.get('album'),
            "views_text": song_data.get('views_text'),
            "duration": song_data.get('duration')
        }
        favorites.append(saved_item)
        save_favorites(favorites)
        return True
