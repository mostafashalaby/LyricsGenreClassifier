import spotipy
from lyricsgenius import Genius
import sys
import os
import csv
import time
import re

from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8') # Set the standard output encoding to UTF-8
load_dotenv() # Load environment variables from .env file

SPOTIPY_CLIENT_ID = ''
SPOTIPY_CLIENT_SECRET = ''

def init():
    """
    Function that initializes the Spotify and Genius API clients using the credentials stored in the .env file.
    """
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


def read_from_csv(csv_file, songs_data):
    """
    Function that reads the data from the specified CSV file and stores it in the songs_data dictionary.

    Purpose is to read from the csv file first, to only add entries that do not have lyrics later on.
    """
    if not os.path.exists(csv_file):
        print(f"File '{csv_file}' does not exist. Skipping read operation.")
        return

    with open(csv_file, mode='r', encoding="utf-8") as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip the header row
        for row in csv_reader:
            artist_name, track_name, genre, lyrics = row
            songs_data[(artist_name, track_name)] = [genre, lyrics]

def get_playlist_artist_and_track(sp, playlist_id, genre, songs_data):
    """
    Function that retrieves the artists and track names from a Spotify playlist
    """
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
                track_lyrics = song.lyrics.encode('utf-8', 'ignore').decode('utf-8')
            else:
                print(f"Lyrics not found for song: {track} by {artist}. Skipping...\n")
                track_lyrics = None
        
        except Exception as e:
            print(f"An error occurred for song: {track} by {artist}: {e}. Skipping...\n")
            track_lyrics = None
            break

        # Update the lyrics dictionary and songs_data dictionary with the lyrics
        if songs_data[(artist, track)][1] is None:
            track_lyrics = track_lyrics.split("\n")
            track_lyrics = " ".join(track_lyrics)
            lyrics[(artist, track)] = track_lyrics.strip()
            songs_data[(artist, track)][0] = genre
            songs_data[(artist, track)][1] = track_lyrics
        else:
            print(f"Lyrics already exist for song: {track} by {artist}. Skipping...\n")

    return lyrics

def write_to_csv(songs_data, csv_file):
    with open(csv_file, mode='a', encoding="utf-8", newline='') as file:
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

    # read from csv file first, to only add entried that do not have lyrics
    read_from_csv(csv_file, songs_data)
    #for key, value in songs_data.items():2w
    #    if value[1] is None:
    #        print(key, value)

    
    for genre, playlist_id in genres.items():
        tracks = get_playlist_artist_and_track(sp, playlist_id, genre, songs_data)
        lyrics = get_lyrics_category(genius, tracks, genre, songs_data)
        
        # Store the results in dictionaries
        tracks_by_genre[genre] = tracks
        lyrics_by_genre[genre] = lyrics

    #for key, value in songs_data.items():
    #    print(key, value)
    #print(lyrics_by_genre)
    
    write_to_csv(songs_data, csv_file)