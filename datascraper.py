import spotipy
from lyricsgenius import Genius
import sys
import os
import csv

from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

SPOTIPY_CLIENT_ID = ''
SPOTIPY_CLIENT_SECRET = ''

def init():
    global SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, GENIUS_CLIENT_ACCESS_TOKEN
    
    SPOTIPY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    GENIUS_CLIENT_ACCESS_TOKEN = os.getenv('GENIUS_CLIENT_ACCESS_TOKEN')

    if not (SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET and GENIUS_CLIENT_ACCESS_TOKEN):
        print('Error: Spotify or Genius API credentials not found. Did you add them to the .env file?')
        sys.exit(1)

    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET))
    genius = Genius(GENIUS_CLIENT_ACCESS_TOKEN)

    return sp, genius

def get_playlist_artist_and_track(sp, playlist_id, genre, songs_data):
    playlist = sp.playlist(playlist_id)
    tracks = playlist['tracks']['items']
    artist_track_list = []
    for track in tracks:
        artist_name = track['track']['artists'][0]['name']
        track_name = track['track']['name']
        
        artist_track_list.append((artist_name, track_name))
        
        # Append song data entry with placeholder for lyrics
        songs_data.append({"genre": genre, "artist": artist_name, "song": track_name, "lyrics": None})

    return artist_track_list

def get_lyrics_category(genius, artist_track_list, genre, songs_data):
    lyrics = {}
    for artist, track in artist_track_list:
        try:
            song = genius.search_song(track, artist)
            track_lyrics = song.lyrics if song else None
        except Exception as e:
            print(f"An error occurred for song: {track} by {artist}: {e}. Skipping...")
            track_lyrics = None

        # Update the lyrics dictionary and songs_data list with the fetched lyrics
        lyrics[track] = track_lyrics
        
        for entry in songs_data:
            if entry["genre"] == genre and entry["artist"] == artist and entry["song"] == track:
                entry["lyrics"] = track_lyrics
                break  # Stop searching once the correct entry is updated
    return lyrics

def write_to_csv(songs_data):
    with open('songs_data.csv', mode='w') as file:
        fieldnames = ['genre', 'artist', 'song', 'lyrics']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        for entry in songs_data:
            writer.writerow(entry)

    print("Data written to songs_data.csv")
    
if __name__ == "__main__":
    sp, genius = init()

    # Dictionary of genre names and corresponding Spotify playlist IDs
    genres = {
        "rock": '61jNo7WKLOIQkahju8i0hw',        # 100 Greatest Rock Songs
        "jazz": '2oVMMLSwywY25Eq9CFxjnC',         # The Jazz100
        "pop": '2OFfgjs6kj0eA6FNayhAAJ',          # 100 Greatest Pop Songs Ever
        "hip_hop": '37i9dQZF1DXb8wplbC2YhV',      # 100 Greatest Hip-Hop Songs of the Streaming Era
        "country": '1ebpJj6czDz3RYuhPjElsA'       # COUNTRY HITS TOP 100
    }

    tracks_by_genre = {}
    lyrics_by_genre = {}
    songs_data = [] # data to be stored in a csv file

    for genre, playlist_id in genres.items():
        tracks = get_playlist_artist_and_track(sp, playlist_id, genre, songs_data)
        lyrics = get_lyrics_category(genius, tracks, genre, songs_data)
        
        # Store the results in dictionaries
        tracks_by_genre[genre] = tracks
        lyrics_by_genre[genre] = lyrics

    print(tracks_by_genre)
    print(lyrics_by_genre)
    
    write_to_csv(songs_data)