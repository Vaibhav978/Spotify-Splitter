from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from dotenv import load_dotenv
import os
import base64
import requests
from datetime import datetime, timedelta
import certifi
import ssl
from aiohttp import ClientSession
import asyncio
import logging
from spotify import *
app = Flask(__name__, static_url_path='/static')
app.secret_key = os.urandom(24)
SPOTIFY_REDIRECT_URI = 'http://127.0.0.1:5002/homepage'
load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
token = None
token_expiration = None
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

def token_expired():
    global token_expiration
    if token_expiration:
        return token_expiration < datetime.now()
    return True

def refresh_token():
    global token
    global token_expiration

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
    print("Attempting to refresh token")
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
    global token
    token = new_token

def get_token(code):
    global token
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
    set_token(token)
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
    token_expiration = session.get('token_expiration')

    if token and token_expiration:
        token_expiration = datetime.fromisoformat(token_expiration)
    if code and (not token or token_expired()):
        token = get_token(code)
        set_token(token)
        session['token'] = token
        session['token_expiration'] = calculate_token_expiration().isoformat()

    if token:
        user_data = get_user_json_data(token)
        display_name = user_data.get('display_name', '')
        user_id = user_data.get('id', '')
        session['display_name'] = display_name
        session['user_id'] = user_id
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
    token_expiration = session.get('token_expiration')

    if token and token_expiration:
        token_expiration = datetime.fromisoformat(token_expiration)
    if code and (not token or token_expired()):
        token = get_token(code)
        set_token(token)
        session['token'] = token
        session['token_expiration'] = calculate_token_expiration().isoformat()

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
    token_expiration = session.get('token_expiration')

    if token and token_expiration:
        token_expiration = datetime.fromisoformat(token_expiration)
    if code and (not token or token_expired()):
        token = get_token(code)
        set_token(token)
        session['token'] = token
        session['token_expiration'] = calculate_token_expiration().isoformat()

    if token:
        user_data = get_user_json_data(token)
        display_name = user_data.get('display_name', '')
        session['display_name'] = display_name
    else:
        display_name = session.get('display_name', '')

    return render_template('homepage.html', display_name=display_name)

async def fetch(session, url, headers, params=None, max_retries=3):
    for attempt in range(max_retries):
        async with session.get(url, headers=headers, params=params, ssl=SSL_CONTEXT) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                logging.warning(f"Rate limited. Retrying after {retry_after} seconds (Attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(retry_after)
            else:
                logging.error(f"Request failed with status {response.status}: {await response.text()}")
                return None
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    logging.error(f"Max retries reached for {url}")
    return None

async def get_user_tracks(token, limit=50, offset=0):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    all_tracks = []
    async with ClientSession() as session:
        while True:
            url = 'https://api.spotify.com/v1/me/tracks'
            params = {'limit': limit, 'offset': offset}
            response_json = await fetch(session, url, headers, params)
            if not response_json:
                break
            all_tracks.extend(response_json.get('items', []))
            if len(response_json.get('items', [])) < limit:
                break
            offset += limit
            await asyncio.sleep(0.5)
    return all_tracks

async def get_track_features(track_id, token, session, max_retries=3):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    url = f'https://api.spotify.com/v1/audio-features/{track_id}'
    for attempt in range(max_retries):
        async with session.get(url, headers=headers, ssl=SSL_CONTEXT) as response:
            if response.status == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                logging.warning(f"Rate limited by Spotify API. Retrying after {retry_after} seconds (Attempt {attempt + 1}/{max_retries}).")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            elif response.status == 401:
                logging.error("Unauthorized access - token may be expired.")
                return None
            elif response.status != 200:
                logging.error(f"Failed to fetch track features, status code: {response.status}")
                return None
            return await response.json()
    logging.error(f"Failed to fetch track features for track {track_id} after multiple retries.")
    return None

async def get_artist_details(artist_id, token, session):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = {"Authorization": f"Bearer {token}"}
    return await fetch(session, url, headers)

async def construct_tracks_json(token):
    all_tracks = []
    user_tracks = await get_user_tracks(token)
    if not user_tracks:
        return []
    async with ClientSession() as session:
        for item in user_tracks:
            track = item['track']
            track_id = track['id']
            track_name = track['name']
            album = track['album']['name']
            artist = track['artists'][0]['name']
            popularity = track.get('popularity')
            features = await get_track_features(track_id, token, session)
            if features:
                track_info = {
                    "name": track_name,
                    "album": album,
                    "artist": artist,
                    "popularity": popularity,
                    "acousticness": features.get('acousticness'),
                    "danceability": features.get('danceability'),
                    "energy": features.get('energy'),
                    "instrumentalness": features.get('instrumentalness'),
                    "liveness": features.get('liveness'),
                    "loudness": features.get('loudness'),
                    "speechiness": features.get('speechiness'),
                    "tempo": features.get('tempo'),
                    "valence": features.get('valence'),
                }
                all_tracks.append(track_info)
    return all_tracks

@app.route("/gettracks", methods=['GET'])
async def get_tracks():
    token = session.get('token')  # Get token from session
    if not token or token_expired():
        token = refresh_token()
    tracks = await construct_tracks_json(token)
    return jsonify(tracks)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=True)
