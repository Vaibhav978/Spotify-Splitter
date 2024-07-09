from flask import Flask, render_template, request, redirect, url_for, jsonify, session, abort
from dotenv import load_dotenv
import os
import base64
import requests
from datetime import datetime, timedelta
from spotify import * 

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.urandom(24)  # Add this line for session management
SPOTIFY_REDIRECT_URI = 'http://127.0.0.1:5002/homepage'
load_dotenv()
cli=ent_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

token = None  # Initialize token to None
token_expiration = None  # Global variable to store token expiration time

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
    # Set the token expiration time to 1 hour from now
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
    token = json_result.get("access_token")
    refresh_token = json_result.get("refresh_token")
    session['token'] = token
    session['refresh_token'] = refresh_token
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
            print(response.text)  # Print the response content for debugging
    else:
        print("Error: Token not available")
        return None

@app.route("/")
def renderWebsite():
    return render_template('index.html')

@app.route('/login')
def login():
    # Here you should perform authentication
    # For now, let's assume authentication is successful

    # Define the list of scopes your application needs
    scopes = "user-read-private user-read-email"

    # Construct the Spotify authorization URL with the specified scopes
    spotify_auth_url = f"https://accounts.spotify.com/authorize?client_id={client_id}&response_type=code&redirect_uri={SPOTIFY_REDIRECT_URI}&scope={scopes}"


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
        session['token'] = token  # Store token in session
        session['token_expiration'] = calculate_token_expiration().isoformat()  # Store token expiration in session

    if token:
        user_data = get_user_json_data(token)
        display_name = user_data.get('display_name', '')
        user_id = user_data.get('id', '')
        session['display_name'] = display_name  # Store display name in session
        session['user_id'] = user_id
    else:
        display_name = session.get('display_name', '')

    return render_template('user.html', display_name=display_name)

@app.route("/search_artist", methods=['POST'])
def get_artist_album():
    token = session.get('token')  # Get token from session

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
        session['token_expiration'] = calculate_token_expiration().isoformat()  # Store token expiration in session

    if token:
        user_data = get_user_json_data(token)
        display_name = user_data.get('display_name', '')
        session['display_name'] = display_name  # Store display name in session
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
        session['token'] = token  # Store token in session
        session['token_expiration'] = calculate_token_expiration().isoformat()  # Store token expiration in session

    if token:
        user_data = get_user_json_data(token)
        display_name = user_data.get('display_name', '')
        session['display_name'] = display_name  # Store display name in session
    else:
        display_name = session.get('display_name', '')

    return render_template('homepage.html', display_name=display_name)

def get_user_playlists(token):
    url = "https://api.spotify.com/v1/me/playlists"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        print("Error:", response.status_code)
        print(response.text)
        return []

def get_playlist_tracks(playlist_id, token):
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        print("Error:", response.status_code)
        print(response.text)
        return []

def get_track_features(track_id, token):
    url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.status_code)
        print(response.text)
        return {}

def get_artist_details(artist_id, token):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.status_code)
        print(response.text)
        return {}

def construct_tracks_json(token):
    playlists = get_user_playlists(token)
    print("Got user playlists")
    all_tracks = []

    for playlist in playlists:
        playlist_id = playlist['id']
        tracks = get_playlist_tracks(playlist_id, token)

        for item in tracks:
            track = item['track']
            track_id = track['id']
            track_name = track['name']
            artists = track['artists']
            album = track['album']
            genres = []
            features = get_track_features(track_id, token)

            for artist in artists:
                artist_details = get_artist_details(artist['id'], token)
                genres.extend(artist_details.get('genres', []))

            track_info = {
                'track_id': track_id,
                'track_name': track_name,
                'album': album['name'],
                'artists': [artist['name'] for artist in artists],
                'genres': list(set(genres)),  # Remove duplicates
                'features': features
            }
            all_tracks.append(track_info)

    return all_tracks


@app.route("/gettracks", methods=['GET'])
def get_tracks():
    print("GET /gettracks called")
    token = session.get('token')  # Get token from session

    if not token or token_expired():
        print("Token is missing or expired, refreshing token...")
        token = refresh_token()

    print(f"Using token: {token}")

    tracks = construct_tracks_json(token)

    print("Returning tracks:", tracks)
    return jsonify(tracks)


def get_user_tracks_json():
    if token:
        return construct_tracks_json(token)
    else:
        print("Error: Token not available")
        return []
  

@app.route('/shutdown', methods=['POST'])
def shutdown():
    if not request.remote_addr == '127.0.0.1':
        abort(403)  # Forbidden

    shutdown_server = request.environ.get('werkzeug.server.shutdown')
    if shutdown_server is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    shutdown_server()
    return 'Server shutting down...'



if __name__ == '__main__':
    app.run(port=5002, host='0.0.0.0', debug=True)
#

