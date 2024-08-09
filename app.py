from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from dotenv import load_dotenv
import os
import base64
import requests
from datetime import datetime, timedelta
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import asyncio
import time
from spotify import *
import spotipy  
import pandas as pd
from classification import *
from pymongo import MongoClient
import subprocess
import logging
import signal
from add_to_playlist import *
import certifi

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.urandom(24)
if os.getenv("FLASK_ENV") == "production":
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI_PRODUCTION", "https://spotify-helper.onrender.com/homepage")
else:
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI_LOCAL", "http://127.0.0.1:5002/homepage")

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPE = "user-read-private user-read-email user-library-read playlist-modify-public playlist-modify-private"
BASE_URL = "https://api.spotify.com/v1"
uri = "mongodb+srv://vibhusingh925:e%2A%21%2AsWHJ_iWQy6*@spotifydb.vgf4v.mongodb.net/spotifydb?retryWrites=true&w=majority&tls=true"

# MongoDB connection
client = MongoClient(uri, tlsCAFile=certifi.where())

# Access the database and collection
db = client.spotify_db
users_collection = db.users




def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE
    )

def token_expired():
    token_expiration = session.get('token_expiration')
    if token_expiration:
        return datetime.fromisoformat(token_expiration) < datetime.now()
    return True

def refresh_token():
    refresh_token = session.get('refresh_token')
    if not refresh_token:
        print("Refresh token not available")
        return None

    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": SCOPE
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        json_result = response.json()
        token = json_result.get("access_token")
        token_expiration = calculate_token_expiration()
        session['token'] = token
        session['token_expiration'] = token_expiration.isoformat()
        print("Token refreshed successfully")
        return token
    else:
        print("Failed to refresh token:", response.status_code, response.text)
        return None

def calculate_token_expiration():
    return datetime.now() + timedelta(hours=1)

def set_token(new_token):
    session['token'] = new_token

def get_token(code):
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": SCOPE
    }

    response = requests.post(url, headers=headers, data=data)
    json_result = response.json()
    token = json_result.get("access_token")
    refresh = json_result.get("refresh_token")
    session['token'] = token
    session['refresh_token'] = refresh
    session['token_expiration'] = calculate_token_expiration().isoformat()
    return token

def get_user_json_data(token):
    if token:
        url = "https://api.spotify.com/v1/me"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print("Error:", response.status_code)
            print(response.text)
    else:
        print("Error: Token not available")
        return None

async def construct_tracks_json(sp):
    print("Entered construct tracks")
    all_tracks = []
    count = 1
    user_tracks = sp.current_user_saved_tracks()
    artists_found = set()

    while user_tracks:
        track_ids = [item['track']['id'] for item in user_tracks['items']]
        batched_track_ids = [track_ids[i:i + 50] for i in range(0, len(track_ids), 50)]
        
        # Collect all artist IDs
        for item in user_tracks['items']:
            track = item['track']
            artist_ids = [artist['id'] for artist in track['artists']]
            artists_found.update(artist_ids)

        # Fetch genres for all unique artist IDs
        artist_genres_dict = await get_genres_with_retry(sp, list(artists_found))
        
        for batch in batched_track_ids:
            features = await get_audio_features_with_retry(sp, batch)
            for i, item in enumerate(user_tracks['items']):
                track = item['track']
                track_name = track['name']
                album = track['album']['name']
                artists = [artist['name'] for artist in track['artists']]
                artist_ids = [artist['id'] for artist in track['artists']]
                track_id = track['id']
                # Collect genres for the track from artist_genres_dict
                genres = set()
                for artist_id in artist_ids:
                    genres.update(artist_genres_dict.get(artist_id, []))
                
                feature = features[i]
                if feature:
                    track_info = {
                        "name": track_name,
                        "id": track_id,
                        "album": album,
                        "artists": list(artists),
                        "acousticness": feature.get('acousticness'),
                        "danceability": feature.get('danceability'),
                        "energy": feature.get('energy'),
                        "instrumentalness": feature.get('instrumentalness'),
                        "liveness": feature.get('liveness'),
                        "loudness": feature.get('loudness'),
                        "speechiness": feature.get('speechiness'),
                        "tempo": feature.get('tempo'),
                        "valence": feature.get('valence'),
                        "genres": list(genres),  # Convert set to list for JSON serialization
                    }
                    print(f"Track {count}: {track_info['name']} - Genres: {track_info['genres']}")
                    
                    count += 1
                    all_tracks.append(track_info)
        if user_tracks['next']:
            user_tracks = sp.next(user_tracks)
        else:
            break
    return all_tracks

async def get_audio_features_with_retry(sp, track_ids, retries=5, backoff_factor=2):
    for i in range(retries):
        try:
            features = sp.audio_features(track_ids)
            return features
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get('Retry-After', backoff_factor * (2 ** i)))
                print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                await asyncio.sleep(retry_after)
            else:
                raise e
    print(f"Failed to retrieve audio features for tracks {track_ids} after {retries} retries")
    return [None] * len(track_ids)


async def get_genres_with_retry(sp, artist_ids, retries=5, backoff_factor=2):
    genres_dict = {}
    for i in range(retries):
        try:
            for batch in [artist_ids[i:i + 50] for i in range(0, len(artist_ids), 50)]:
                artists = sp.artists(batch)['artists']
                for artist in artists:
                    genres_dict[artist['id']] = artist.get('genres', [])
            return genres_dict
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get('Retry-After', backoff_factor * (2 ** i)))
                print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                await asyncio.sleep(retry_after)
            else:
                raise e
    print(f"Failed to retrieve genres for artists {artist_ids} after {retries} retries")
    return genres_dict

@app.route("/")
def renderWebsite():
    return render_template('index.html')

@app.route('/login')
def login():
    scopes = "user-read-private user-read-email user-library-read playlist-modify-public playlist-modify-private"
    spotify_auth_url = f"https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={SPOTIFY_REDIRECT_URI}&scope={scopes.replace(' ', '%20')}"
    return redirect(spotify_auth_url)

@app.route("/user")
def render_user_page():
    code = request.args.get("code")
    token = session.get('token')

    if code and (not token or token_expired()):
        token = get_token(code)
        session['token'] = token

    if token:
        user_data = get_user_json_data(token)
        session['spotify_id'] = user_data.get('id')
        display_name = user_data.get('display_name', '')
        session['display_name'] = display_name
    else:
        display_name = session.get('display_name', '')

    return render_template('user.html', display_name=display_name)

@app.route("/search_artist", methods=['POST'])
def get_artist_album():
    token = session.get('token')

    if not token or token_expired():
        token = refresh_token()

    data = request.json
    artist_name = data.get('artist_name')
    num_albums = int(data.get('num_albums'))

    albums = get_artist_albums_popularity(artist_name, num_albums)

    if albums:
        return albums
    else:
        print("There are no albums")
        return jsonify([])

@app.route("/splitter")
def render_splitter():
    code = request.args.get("code")
    token = session.get('token')

    if code and (not token or token_expired()):
        token = get_token(code)
        session['token'] = token

    if token:
        user_data = get_user_json_data(token)
        display_name = user_data.get('display_name', '')
        session['spotify_id'] = user_data.get('id')
        session['display_name'] = display_name
    else:
        display_name = session.get('display_name', '')

    return render_template('splitter.html', display_name=display_name)

@app.route("/homepage")
def render_homepage():
    code = request.args.get("code")
    token = session.get('token')

    if code and (not token or token_expired()):
        token = get_token(code)
        session['token'] = token

    if token:
        user_data = get_user_json_data(token)
        session['spotify_id'] = user_data.get('id')

        display_name = user_data.get('display_name', '')
        session['display_name'] = display_name
    else:
        display_name = session.get('display_name', '')

    return render_template('homepage.html', display_name=display_name)

@app.route("/gettracks", methods=['GET'])
def get_tracks():
    code = request.args.get("code")
    token = session.get('token')
    spotify_id = session.get('spotify_id')
    if code and (not token or token_expired()):
        token = get_token(code)
        session['token'] = token

    if token:
        if user_exists_in_database(session['spotify_id']):
            user_data = get_user_data(spotify_id)
            return jsonify(user_data)
        else:
            # sp = Spotify(auth=token)
            # all_tracks = asyncio.run(construct_tracks_json(sp))
            # if all_tracks:
            #     user_entry = {
            #         "spotify_id": spotify_id,
            #         "tracks": all_tracks
            #     }
            #     user_entry.pop('_id',None)
            #     # Insert the new user entry into the database
            #     users_collection.insert_one(user_entry)
            #     return jsonify(user_entry)
        
            # else:
            return jsonify({"error": "No User Found, please add tracks to the database first"})
    else:
        return jsonify({"error": "No token available or token expired"})

def user_exists_in_database(spotify_id):
    user = users_collection.find_one({"spotify_id": spotify_id})
    return user is not None

def get_user_data(spotify_id):
    user = users_collection.find_one({"spotify_id": spotify_id})
    if user:
        user.pop('_id', None)  # Remove the MongoDB ObjectId
    return user

@app.route("/updatetracks", methods=['GET'])
def update_tracks():
    try:
        print("Entered update_tracks")
        code = request.args.get("code")
        token = session.get('token')
        spotify_id = session.get('spotify_id')

        if code and (not token or token_expired()):
            token = get_token(code)
            session['token'] = token

        if token:
            sp = Spotify(auth=token)
            all_tracks = asyncio.run(construct_tracks_json(sp))
        
            if all_tracks:
                user_entry = {
                    "spotify_id": spotify_id,
                    "tracks": all_tracks
                }
                user_entry.pop('_id', None)

            # Update or insert (upsert=True) the document
                result = users_collection.update_one(
                    {"spotify_id": spotify_id},
                    {"$set": user_entry},
                    upsert=True
                )

                if result.upserted_id:
                    user_entry["_id"] = str(result.upserted_id)
                else:
                    user_entry.pop("_id", None)
            
                return jsonify(user_entry)

            else:
                return jsonify({"error": "No tracks found"})
    
        else:
            return jsonify({"error": "No token available or token expired"})
    except Exception:
        return jsonify('error: Your network was too slow, please try again')

    
    
def delete_user_by_spotify_id_from_database(spotify_id):
    users_collection.delete_one({"spotify_id": spotify_id})


@app.route("/splittracks", methods = ['GET'])
def split_tracks():
        spotify_id = session.get('spotify_id')

        print("Entered split tracks")
        code = request.args.get("code")
        token = session.get('token')

        if code and (not token or token_expired()):
            token = get_token(code)
            session['token'] = token
        if token:
            classified_playlists = cluster_tracks_with_visualization(spotify_id, load_existing_model=True)
            return classified_playlists

@app.route('/createplaylist', methods=['POST'])
def create_playlist():
    code = request.args.get("code")
    token = session.get('token')
    spotify_id = session.get('spotify_id')
    data = request.json
    session['token'] = token
    playlist_name = data.get('playlistName')
    cluster_number = data.get('clusterNumber')
    clusters_data = data.get('clusters')

    if code and (not token or token_expired()):
        token = get_token(code)
    else:
        if token_expired():
            token = refresh_token()
            session['token'] = token

    if token:
        cluster = clusters_data.get(cluster_number)
        if not cluster:
            return jsonify({"error": "Invalid cluster number or cluster not found"})
        spotify_name_list = [track.get('name')for track in cluster if track.get('name')]
        #print(spotify_name_list)
        spotify_id_list = [track.get('id') for track in cluster if track.get('id')]
        if not spotify_id_list:
            return jsonify({"error": "No valid tracks found in the cluster"})

        sp = spotipy.Spotify(auth=token)
        spotify_ids_uris = [f'spotify:track:{track_id}' for track_id in spotify_id_list]
        # Remove duplicates
        spotify_ids_uris = list(set(spotify_ids_uris))

        # Create the playlist
        playlist = sp.user_playlist_create(user=spotify_id, name=playlist_name, public=True)
        playlist_id = playlist['id']
        print(playlist_id)
        logging.debug(f"Created playlist with ID: {playlist_id}")
        time.sleep(4)
        add_tracks_to_playlist(spotify_ids_uris, playlist_id)

        # Verify playlist contents

        return jsonify({"success": "Playlist created and tracks added successfully", "playlistId": playlist_id, "token": token })
    else:
        return jsonify({"error": "No token available or token expired"})



def add_tracks_to_playlist( playlist_id, tracks):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=SPOTIFY_REDIRECT_URI,
                                                   scope='playlist-modify-public'))
    print(len(tracks))
    try:
        # Add tracks to playlist
        for i in range(0, len(tracks), 100):
            response = sp.playlist_add_items(playlist_id, tracks[i:i+100],)
            print(f"Added {len(tracks[i:i+100])} tracks to playlist. Response: {response}")
            time.sleep(1)  # To avoid hitting rate limits

        # Fetch current tracks in playlist
        playlist_content = sp.playlist_tracks(playlist_id)
        print(playlist_content)

    except spotipy.SpotifyException as e:
        print(f"Spotify exception occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

#this gives an error due to the fact the add isn't working correctly.
def verify_playlist_contents(token, playlist_id):
    sp = Spotify(auth=token)
    fields = "items(track(name, uri)), total"
    playlist_tracks = sp.playlist_tracks(playlist_id, fields=fields, limit=100, offset=0, market=None)
    print(f"Current tracks in playlist {playlist_id}:")
    print(playlist_tracks)
    for item in playlist_tracks['items']:
        track = item['track']
        print(f"Track Name: {track['track']}, Track URI: {track['uri']}")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('renderWebsite'))

def kill_process_on_port(port):
    """Kills any processes running on the specified port."""
    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}"], capture_output=True, text=True
        )
        lines = result.stdout.splitlines()
        for line in lines[1:]:  # Skip the header line
            pid = int(line.split()[1])
            try:
                os.kill(pid, signal.SIGKILL)
                print(f"Killed process with PID {pid} on port {port}")
            except ProcessLookupError:
                pass  # Process may have already terminated
    except subprocess.CalledProcessError:
        print(f"No processes found on port {port}")
if __name__ == '__main__':
    kill_process_on_port(5002)
    time.sleep(2)
    app.run(port=5002)