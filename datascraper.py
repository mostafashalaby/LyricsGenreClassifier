import spotipy
from lyricsgenius import Genius
import sys
import os
import csv
import time
import re

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
        artist_name= track['track']['artists'][0]['name']
        track_name_unfiltered = track['track']['name']
        track_name = re.sub(r'\s*-.*$', '', track_name_unfiltered).strip()
        
        artist_track_list.append((artist_name, track_name))
        
        # Append song data dictionary with the genre and lyrics
        songs_data[(artist_name, track_name)] = [genre, None]

    return artist_track_list

def get_lyrics_category(genius, artist_track_list, genre, songs_data):
    lyrics = {}
    for artist, track in artist_track_list:
        try:
            time.sleep(1) # Sleep for 1 second to avoid rate limiting
            song = genius.search_song(track, artist)
            if song.lyrics:
                track_lyrics = song.lyrics
                print("Lyrics: ", song.lyrics)
            else:
                print(f"Lyrics not found for song: {track} by {artist}. Skipping...")
                track_lyrics = None

        except Exception as e:
            print(f"An error occurred for song: {track} by {artist}: {e}. Skipping...")
            track_lyrics = None
            break

        # Update the lyrics dictionary and songs_data dictionary with the lyrics
        lyrics[(artist, track)] = track_lyrics
        songs_data[(artist, track)][0] = genre
        songs_data[(artist, track)][1] = track_lyrics

    return lyrics

def write_to_csv(songs_data, csv_file):
    with open(csv_file, mode='a', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(['artist_name', 'track_name', 'genre', 'lyrics'])
        for (artist, track), [genre, lyrics] in songs_data.items():
            writer.writerow([artist, track, genre, lyrics])

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

    csv_file = 'songs_data.csv'     
    tracks_by_genre = {} # format: {genre: [artist_name, track_name]}
    lyrics_by_genre = {} # format: {genre: [(artist_name, track_name), lyrics]}
    songs_data = {} # format: {(artist_name, track_name): [genre, lyrics]}

    for genre, playlist_id in genres.items():
        tracks = get_playlist_artist_and_track(sp, playlist_id, genre, songs_data)
        lyrics = get_lyrics_category(genius, tracks, genre, songs_data)
        
        # Store the results in dictionaries
        tracks_by_genre[genre] = tracks
        lyrics_by_genre[genre] = lyrics

    #print(tracks_by_genre)
    #print(lyrics_by_genre)
    
    write_to_csv(songs_data, csv_file)