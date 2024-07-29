import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

# Define your Spotify credentials and playlist ID
CLIENT_ID = '64453869c608479c957d4d9e24cba22e'
CLIENT_SECRET = 'fc4c65b49a644ed8bd808fdf10e14c43'
REDIRECT_URI = 'http://localhost:8888/callback'
PLAYLIST_ID = '244IMeUr2Jtz0NDSvn87qV'
SCOPE = 'playlist-modify-public'

def authenticate_spotify():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI,
                                                   scope=SCOPE))
    return sp

def add_tracks_to_playlist(sp, playlist_id, tracks):
    try:
        # Add tracks to playlist
        for i in range(0, len(tracks), 100):
            response = sp.playlist_add_items(playlist_id, tracks[i:i+100])
            print(f"Added {len(tracks[i:i+100])} tracks to playlist. Response: {response}")
            time.sleep(1)  # To avoid hitting rate limits

        # Fetch current tracks in playlist
        playlist_content = sp.playlist_tracks(playlist_id)
        #print(playlist_content)

    except spotipy.SpotifyException as e:
        print(f"Spotify exception occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # List of track URIs to add
    tracks_to_add = [
        'spotify:track:6sy3LkhNFjJWlaeSMNwQ62', 'spotify:track:7BKLCZ1jbUBVqRi2FVlTVw', 'spotify:track:6DCZcSspjsKoFjzjrWoCdn',
        'spotify:track:7EQGXaVSyEDsCWKmUcfpLk', 'spotify:track:69uxyAqqPIsUyTO8txoP2M','spotify:track:12WCXE6DlRcCn2rEShNepL',
        'spotify:track:06HL4z0CvFAxyc27GXpf02','spotify:track:0rZp7G3gIH6WkyeXbrZnGi',
        # Add more tracks as needed
    ]

    sp = authenticate_spotify()
    add_tracks_to_playlist(sp, PLAYLIST_ID, tracks_to_add)
