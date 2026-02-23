from difflib import SequenceMatcher
from utils.utils import parse_views


def expand_artist_names(raw_artists):
    separators = [" ft ", " ft.", " feat ", " feat.", " featuring ", " & ", " x ", " ve ", ",", " and ", "/", " + "]
    expanded = set()
    for r_art in raw_artists:
        temp = r_art.lower() if hasattr(r_art, 'lower') else str(r_art).lower()
        for sep in separators:
            temp = temp.replace(sep, "|")
        tokens = [t.strip() for t in temp.split("|") if t.strip()]
        expanded.update(tokens)
    return expanded


def build_search_targets(user_query, artist_true_name=None):
    targets = set()
    parts = user_query.lower().replace(" & ", "&").replace(" ve ", "&").replace(",", "&").split("&")
    for q in parts:
        clean_q = q.strip()
        if clean_q:
            targets.add(clean_q)
    if artist_true_name:
        targets.add(artist_true_name.lower().strip())
    return targets


def is_artist_match(song_artists, search_targets):
    expanded = expand_artist_names(song_artists)
    for target in search_targets:
        if target in expanded:
            return True
    return False


def clean_title_for_dedup(title, artist_name=""):
    t = title.lower()
    noise_words = [
        "(official music)", "(official video)", "(official audio)",
        "(music video)", "(video)", "(audio)", "(lyric video)", "(lyrics)",
        " official music", " official video", " official audio", "!", "(Canlı)",
        "Canlı", "(Canlı Senfonik)", "canlı senfonik", "(Live)", "Live"
    ]
    for noise in noise_words:
        t = t.replace(noise, "")

    if artist_name.lower() in t:
        t = t.replace(artist_name.lower(), "").strip()
        if t.startswith("-"):
            t = t.lstrip("- ")

    return t.strip()


def is_fuzzy_duplicate(song, existing_songs, artist_name=""):
    cleaned_current = clean_title_for_dedup(song['title'], artist_name)

    for existing in existing_songs:
        if existing['album'] == 'Single':
            continue

        cleaned_existing = clean_title_for_dedup(existing['title'], artist_name)

        if SequenceMatcher(None, cleaned_current, cleaned_existing).ratio() > 0.85:
            return True

        if cleaned_existing and cleaned_existing in cleaned_current:
            if len(cleaned_existing) > 4:
                return True
    return False


def filter_candidates(combined_results, user_query, artist_true_name, stop_check=None):
    search_targets = build_search_targets(user_query, artist_true_name)
    candidates = []
    observed_video_ids = set()

    for song in combined_results:
        if stop_check and stop_check():
            return None

        artists = song.get('artists', [])
        if not artists:
            continue

        raw_artists = [a['name'] for a in artists]
        if not is_artist_match(raw_artists, search_targets):
            continue

        vid_id = song.get('videoId', '')
        if vid_id in observed_video_ids:
            continue
        observed_video_ids.add(vid_id)

        data = {
            "title": song.get('title', 'Bilinmiyor'),
            "artist": ", ".join(raw_artists),
            "album": (song.get('album') or {}).get('name', 'Single'),
            "views_text": song.get('views', 'Veri Yok'),
            "duration": song.get('duration', ''),
            "video_id": vid_id
        }
        candidates.append(data)

    return candidates


def deduplicate_candidates(candidates, target_count, artist_name="", stop_check=None):
    candidates.sort(key=lambda x: 1 if x['album'] == 'Single' else 0)

    all_songs = []
    observed_norm_titles = set()

    for song in candidates:
        if stop_check and stop_check():
            return None

        if len(all_songs) >= target_count * 3:
            break

        norm_title = song['title'].lower().strip()
        if norm_title in observed_norm_titles:
            continue

        if song['album'] == 'Single':
            if is_fuzzy_duplicate(song, all_songs, artist_name):
                continue

        observed_norm_titles.add(norm_title)
        all_songs.append(song)

    return all_songs


def generate_lists(all_songs, target_count):
    pop_list = all_songs[:target_count]

    for s in all_songs:
        s['_views_num'] = parse_views(s['views_text'])

    sorted_by_views = sorted(all_songs, key=lambda x: x['_views_num'], reverse=True)
    views_list = sorted_by_views[:target_count]

    views_ids = set(s['video_id'] for s in views_list)
    intersection = [s for s in pop_list if s['video_id'] in views_ids]
    intersection.sort(key=lambda x: x['_views_num'], reverse=True)

    intersection_ids = set(s['video_id'] for s in intersection)
    unique_pop = [s for s in pop_list if s['video_id'] not in intersection_ids]
    unique_views = [s for s in views_list if s['video_id'] not in intersection_ids]

    smart_list = list(intersection)

    p_idx, v_idx = 0, 0
    while len(smart_list) < target_count and (p_idx < len(unique_pop) or v_idx < len(unique_views)):
        if p_idx < len(unique_pop) and len(smart_list) < target_count:
            smart_list.append(unique_pop[p_idx])
            p_idx += 1
        if v_idx < len(unique_views) and len(smart_list) < target_count:
            smart_list.append(unique_views[v_idx])
            v_idx += 1

    if len(smart_list) < target_count:
        extra_needed = target_count - len(smart_list)
        used_ids = set(s['video_id'] for s in smart_list)
        extras = [s for s in sorted_by_views if s['video_id'] not in used_ids]
        smart_list.extend(extras[:extra_needed])

    return pop_list, views_list, smart_list
