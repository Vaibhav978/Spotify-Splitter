from flask import jsonify
from dotenv import load_dotenv
import os
import base64
import requests
import time

token = None
load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def set_token(new_token):
    global token
    token = new_token

def get_token_spotify():
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes)
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64.decode('utf-8')}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = requests.post(url, headers=headers, data=data)
    json_result = result.json()
    token = json_result.get("access_token")
    return token

def get_artist_id(artist_name):
    token = get_token_spotify()
    if token:
        url = "https://api.spotify.com/v1/search"
        params = {
            "q": artist_name,
            "type": "artist",
            "limit": 1
        }
        headers = {
            "Authorization": f"Bearer {token}"
        }
        result = requests.get(url, params=params, headers=headers)
        if result.status_code == 200:
            json_result = result.json()
            artists = json_result.get('artists', {}).get('items', [])
            if artists:
                return artists[0]['id']
            else:
                print("No artist found")
        else:
            print(f"Error: {result.status_code}")
    else:
        print("Token is not available")
        return None

def get_artist_albums_popularity(artist_name, token, num_albums):
    artist_id = get_artist_id(artist_name)
    if not artist_id:
        print("Artist not found")
        return jsonify([])

    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        'limit': num_albums,
        'include_groups': 'album',
    }
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        albums_json = response.json().get('items', [])

        # Populate total popularity for each album
        for album in albums_json:
            album_id = album['id']
            album['total_popularity'] = get_album_tracks_popularity(album_id, token)
    
        # Sort the albums by total popularity
        sorted_albums = sorted(albums_json, key=lambda x: x.get('total_popularity', 0), reverse=True)
    
        return jsonify(sorted_albums)
    else:
        print(f"Error: {response.status_code}")
        return jsonify([])

def get_album_tracks_popularity(album_id, token):
    total_popularity = 0
    
    if not album_id:
        print("Album not found")
        return 0
    else:
        url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {'market': 'US'}
        response = make_request_with_retry(url, headers, params)
        
        if response and response.status_code == 200:
            tracks_json = response.json().get('items', [])
            track_ids = [track['id'] for track in tracks_json]

            # Batch fetch track details to avoid rate limits
            batch_size = 10  # Number of tracks to fetch per batch
            for i in range(0, len(track_ids), batch_size):
                batch = track_ids[i:i + batch_size]
                track_popularities = get_tracks_popularity(batch, token)
                if track_popularities:
                    total_popularity += sum(track_popularities)

            return total_popularity
        else:
            print("Error:", response.status_code)
            return 0

def get_tracks_popularity(track_ids, token):
    popularities = []
    headers = {
        "Authorization": f"Bearer {token}"
    }
    for track_id in track_ids:
        url = f"https://api.spotify.com/v1/tracks/{track_id}"
        response = make_request_with_retry(url, headers)
        
        if response and response.status_code == 200:
            track_json = response.json()
            popularity = track_json.get('popularity', 0)
            popularities.append(popularity)
        else:
            print("Error:", response.status_code)
            popularities.append(0)  # Add 0 popularity if there's an error

    return popularities

def make_request_with_retry(url, headers, params=None, retries=5):
    delay = 1
    for i in range(retries):
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 429:  # Rate limit exceeded
            retry_after = int(response.headers.get("Retry-After", delay))
            print(f"Rate limit exceeded. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
            delay *= 2  # Exponential backoff
        else:
            return response
    return None
