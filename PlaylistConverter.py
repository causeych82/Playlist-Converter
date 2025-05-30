import spotipy
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import urllib.parse
import time
import re
import json
import os
import sys

# === CONFIG ===
SPOTIFY_CREDENTIALS_FILE = 'spotify_credentials.json'
YOUTUBE_CLIENT_SECRETS_FILE = 'client_secrets.json'
CACHE_FILE = '.yt_cache.json'

# === CONFIG CHECK ===
def check_config_files():
    missing_files = []
    for path in [YOUTUBE_CLIENT_SECRETS_FILE, SPOTIFY_CREDENTIALS_FILE]:
        if not os.path.isfile(path):
            missing_files.append(path)
    if missing_files:
        print(f"❌ Missing config files: {', '.join(missing_files)}")
        print("Please copy the example config files and rename them without the '.example' extension.")
        sys.exit(1)
    with open(SPOTIFY_CREDENTIALS_FILE, 'r') as f:
        spotify_config = json.load(f)
    with open(YOUTUBE_CLIENT_SECRETS_FILE, 'r') as f:
        youtube_config = json.load(f)
    # Check for placeholder text, adjust keys if needed
    if 'YOUR_CLIENT_ID' in spotify_config.get('client_id', '') or \
       'YOUR_CLIENT_SECRET' in spotify_config.get('client_secret', ''):
        print("❌ Please update spotify_credentials.json with your actual Spotify API keys.")
        sys.exit(1)
    if 'YOUR_CLIENT_ID' in youtube_config.get('installed', {}).get('client_id', ''):
        print("❌ Please update client_secrets.json with your actual YouTube API credentials.")
        sys.exit(1)

# Run config check before anything else
check_config_files()

# === SPOTIFY AUTH ===
with open(SPOTIFY_CREDENTIALS_FILE) as f:
    spotify_creds = json.load(f)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=spotify_creds['client_id'],
    client_secret=spotify_creds['client_secret'],
    redirect_uri=spotify_creds['redirect_uri'],
    scope='playlist-read-private playlist-modify-private playlist-modify-public'
))

# === YOUTUBE AUTH ===
def youtube_authenticate():
    flow = InstalledAppFlow.from_client_secrets_file(
        YOUTUBE_CLIENT_SECRETS_FILE,
        scopes=["https://www.googleapis.com/auth/youtube"]
    )
    credentials = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=credentials)

youtube = youtube_authenticate()

# === CACHE ===
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

cache = load_cache()

# === CLEAN YOUTUBE TITLES ===
def clean_youtube_title(title):
    title = re.sub(r'\(.*?\)|\[.*?\]', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\b(official|lyrics|video|hd|live|remastered|audio|visualizer|performance)\b', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s+', ' ', title)
    return title.strip()

# === GET SPOTIFY TRACKS ===
def get_spotify_tracks(playlist_url):
    playlist_id = playlist_url.split("/")[-1].split("?")[0]
    results = sp.playlist_items(playlist_id)
    tracks = []
    for item in results['items']:
        track = item['track']
        title = track['name']
        artist = track['artists'][0]['name']
        search_term = f"{title} {artist}"
        tracks.append(search_term)
    return tracks

# === CREATE YOUTUBE PLAYLIST ===
def create_youtube_playlist(youtube, title, description="Converted from Spotify"):
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title, "description": description},
            "status": {"privacyStatus": "private"}
        }
    )
    response = request.execute()
    return response["id"]

# === ADD TRACKS TO YOUTUBE WITH CACHE ===
def add_tracks_to_youtube(youtube, playlist_id, track_names):
    global cache
    for query in track_names:
        print(f"Searching YouTube for: {query}")
        if query in cache:
            video_id = cache[query]
            print(f"⚡ Cache hit: {video_id}")
        else:
            try:
                search = youtube.search().list(
                    part="snippet",
                    q=query,
                    maxResults=1,
                    type="video"
                ).execute()

                items = search.get("items")
                if not items:
                    print(f"❌ Not found: {query}")
                    continue

                video_id = items[0]["id"]["videoId"]
                cache[query] = video_id
                save_cache(cache)
            except Exception as e:
                print(f"❌ API Error: {e}")
                continue

        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            ).execute()
            print(f"✅ Added: {query}")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Add Error: {e}")
            continue

# === GET YOUTUBE VIDEO TITLES ===
def get_youtube_video_titles(youtube, playlist_id):
    titles = []
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=playlist_id,
        maxResults=50
    )
    while request:
        response = request.execute()
        for item in response["items"]:
            titles.append(item["snippet"]["title"])
        request = youtube.playlistItems().list_next(request, response)
    return titles

# === CREATE SPOTIFY PLAYLIST ===
def create_spotify_playlist(name, description="Converted from YouTube"):
    user_id = sp.me()["id"]
    playlist = sp.user_playlist_create(user=user_id, name=name, description=description)
    return playlist["id"]

# === ADD TRACKS TO SPOTIFY WITH CLEANING ===
def add_tracks_to_spotify(track_names, playlist_id):
    track_uris = []
    for original in track_names:
        cleaned = clean_youtube_title(original)
        print(f"🎯 Searching for: '{cleaned}'")

        try:
            results = sp.search(q=cleaned, type="track", limit=1)
            items = results["tracks"]["items"]

            if items:
                uri = items[0]["uri"]
                name = items[0]["name"]
                artist = items[0]["artists"][0]["name"]
                track_uris.append(uri)
                print(f"✅ Added: {name} — {artist}")
            else:
                print(f"❌ Not found on Spotify: {original}")
        except Exception as e:
            print(f"❌ Spotify search error: {e}")

        time.sleep(1)

    if track_uris:
        sp.playlist_add_items(playlist_id, track_uris)
        print(f"\n✅ Added {len(track_uris)} tracks to your Spotify playlist.")
    else:
        print("\n⚠️ No matches found to add.")

# === MAIN ===
def main():
    print("Convert direction:")
    print("1. Spotify → YouTube")
    print("2. YouTube → Spotify")
    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        spotify_url = input("Enter the Spotify playlist URL: ").strip()
        yt_playlist_name = input("Enter a name for the new YouTube playlist: ").strip()

        print("\n🔄 Fetching Spotify playlist...")
        track_names = get_spotify_tracks(spotify_url)
        print(f"🎵 Found {len(track_names)} tracks.")

        print("\n📺 Creating YouTube playlist...")
        yt_playlist_id = create_youtube_playlist(youtube, yt_playlist_name)

        print("\n➡️ Adding songs to YouTube...")
        add_tracks_to_youtube(youtube, yt_playlist_id, track_names)

        print("\n✅ Done! Your YouTube playlist has been created.")

    elif choice == "2":
        yt_url = input("Enter the YouTube playlist URL: ").strip()
        parsed_url = urllib.parse.urlparse(yt_url)
        query = urllib.parse.parse_qs(parsed_url.query)
        yt_playlist_id = query.get("list", [""])[0]

        if not yt_playlist_id:
            print("❌ Invalid YouTube playlist URL. Please make sure it contains '?list=...'")
            return

        spotify_playlist_name = input("Enter a name for the new Spotify playlist: ").strip()

        print("\n🔄 Fetching YouTube video titles...")
        titles = get_youtube_video_titles(youtube, yt_playlist_id)
        print(f"📺 Found {len(titles)} videos.")

        print("\n🎵 Creating Spotify playlist...")
        sp_playlist_id = create_spotify_playlist(spotify_playlist_name)

        print("\n➡️ Adding songs to Spotify...")
        add_tracks_to_spotify(titles, sp_playlist_id)

        print("\n✅ Done! Your Spotify playlist has been created.")

    else:
        print("Invalid choice. Please run again and enter 1 or 2.")

# === RUN SCRIPT ===
if __name__ == "__main__":
    main()
