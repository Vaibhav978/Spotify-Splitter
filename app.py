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

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.urandom(24)
SPOTIFY_REDIRECT_URI = 'http://127.0.0.1:5002/homepage'
load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
scope = "user-library-read user-read-private user-read-email"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=scope
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

    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
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
    auth_string = f"{client_id}:{client_secret}"
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
        "redirect_uri": SPOTIFY_REDIRECT_URI
    }

    response = requests.post(url, headers=headers, data=data)
    json_result = response.json()
    print(json_result)
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
    while user_tracks:
        track_ids = [item['track']['id'] for item in user_tracks['items']]
        batched_track_ids = [track_ids[i:i + 50] for i in range(0, len(track_ids), 50)]
        
        for batch in batched_track_ids:
            features = await get_audio_features_with_retry(sp, batch)
            for i, item in enumerate(user_tracks['items']):
                track = item['track']
                track_name = track['name']
                album = track['album']['name']
                artist = track['artists'][0]['name']
                popularity = track.get('popularity')
                feature = features[i]
                if feature:
                    track_info = {
                        "name": track_name,
                        "album": album,
                        "artist": artist,
                        "popularity": popularity,
                        "acousticness": feature.get('acousticness'),
                        "danceability": feature.get('danceability'),
                        "energy": feature.get('energy'),
                        "instrumentalness": feature.get('instrumentalness'),
                        "liveness": feature.get('liveness'),
                        "loudness": feature.get('loudness'),
                        "speechiness": feature.get('speechiness'),
                        "tempo": feature.get('tempo'),
                        "valence": feature.get('valence'),
                    }
                    print(f"Track {count}: {track_info['name']} - Danceability: {track_info['danceability']}")

                    count += 1
                    all_tracks.append(track_info)
        if user_tracks['next']:
            user_tracks = sp.next(user_tracks)
        else:
            break
    return all_tracks


async def get_genres_with_retry(sp, artist_ids, retries=5, backoff_factor=2):
    genres = set()
    for i in range(retries):
        try:
            for batch in [artist_ids[i:i + 50] for i in range(0, len(artist_ids), 50)]:
                artists = sp.artists(batch)['artists']
                for artist in artists:
                    genres.update(artist['genres'])
            return genres
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get('Retry-After', backoff_factor * (2 ** i)))
                print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                await asyncio.sleep(retry_after)
            else:
                raise e
    print(f"Failed to retrieve genres for artists {artist_ids} after {retries} retries")
    return genres

@app.route("/")
def renderWebsite():
    return render_template('index.html')

@app.route('/login')
def login():
    scopes = "user-read-private user-read-email user-library-read"
    spotify_auth_url = f"https://accounts.spotify.com/authorize?client_id={client_id}&response_type=code&redirect_uri={SPOTIFY_REDIRECT_URI}&scope={scopes.replace(' ', '%20')}"
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
        display_name = user_data.get('display_name', '')
        session['display_name'] = display_name
    else:
        display_name = session.get('display_name', '')

    return render_template('homepage.html', display_name=display_name)

@app.route("/gettracks", methods=['GET'])
def get_tracks():
    print("Entered get_tracks")
    code = request.args.get("code")
    token = session.get('token')

    if code and (not token or token_expired()):
        token = get_token(code)
        session['token'] = token

    if token:
        user_data = get_user_json_data(token)
        sp = Spotify(auth=token)
        all_tracks = asyncio.run(construct_tracks_json(sp))
        if all_tracks:
            return jsonify(all_tracks)
        else:
            return jsonify({"error": "No tracks found"})
    else:
        return jsonify({"error": "No token available or token expired"})

if __name__ == '__main__':
    app.run(port=5002)
