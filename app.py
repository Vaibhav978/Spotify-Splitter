
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, abort
from dotenv import load_dotenv
import os
import base64
import requests
from datetime import datetime, timedelta
from spotify import *

app = Flask(__name__, static_url_path='/static')
SPOTIFY_REDIRECT_URI = 'http://127.0.0.1:5002/homepage'
load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

token = None  # Initialize token to None
# Global variable to store token expiration time
token_expiration = None

def token_expired():
    global token_expiration
    if token_expiration:
        return token_expiration < datetime.now()
    return True

def refresh_token():
    global token
    global token_expiration
    code = request.args.get("code")
    # Implement token refreshing logic here
    # For example, you might make a request to refresh the token using the refresh token
    # Set the new token and update the token expiration time
    token = get_token(code)  # Implement get_new_token() function
    token_expiration = calculate_token_expiration()  # Implement calculate_token_expiration() function
    return token

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
    auth_base64 = base64.b64encode(auth_bytes)
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64.decode('utf-8')}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI
    }
    result = requests.post(url, headers=headers, data=data)
    json_result = result.json()
    token = json_result.get("access_token")
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

@app.route('/login', methods=['POST'])
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
    token = get_token(code)
    if code and not token:  # If there's a code but no token in the session
        token = get_token(code)
        set_token(token)
    # Now you have the access token, you can make requests to user-specific endpoints
    if token:
        user_data = get_user_json_data(token)
        display_name = user_data.get('display_name', '')
    else:
        display_name = ""
    return render_template('user.html', display_name=display_name)
@app.route("/search_artist", methods=['POST'])
def get_artist_album():
    global token

    # Get a new token if it's not already available or if it's expired
    token = get_token_spotify()

    data = request.json
    artist_name = data.get('artist_name')
    num_albums = int(data.get('num_albums'))

    # Call your function to get the top albums for the artist
    albums = get_artist_albums_popularity(artist_name,token,num_albums)

    if albums:
        return albums
    else:
        print("There are no albums")
        return jsonify([])



@app.route("/splitter")
def render_splitter():
    code = request.args.get("code")
    token = get_token(code)
    if code and not token:  # If there's a code but no token in the session
        token = get_token(code)
        set_token(token)
    # Now you have the access token, you can make requests to user-specific endpoints
    if token:
        user_data = get_user_json_data(token)
        display_name = user_data.get('display_name', '')
    else:
        display_name = ""
    return render_template('splitter.html', display_name=display_name)
@app.route("/homepage")
def render_homepage():
    code = request.args.get("code")
    token = get_token(code)
    if code and not token:  # If there's a code but no token in the session
        token = get_token(code)
        set_token(token)
    # Now you have the access token, you can make requests to user-specific endpoints
    if token:
        user_data = get_user_json_data(token)
        display_name = user_data.get('display_name', '')
    else:
        display_name = ""
    return render_template('homepage.html', display_name=display_name)
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
