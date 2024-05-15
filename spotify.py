from flask import jsonify
from dotenv import load_dotenv
import os
import base64
import requests
from datetime import datetime, timedelta

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
    token = get_token_spotify()  # Make sure to get the token first
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
                return artists[0]['id']  # Return the ID of the first artist
            else:
                print("No artist found")
        else:
            print(f"Error: {result.status_code}")
    else:
        print("Token is not available")
        return None

def get_artist_albums(artist_name, token, num_albums):
    artist_id = get_artist_id(artist_name)
    if not artist_id:
        print("Artist not found")
        return jsonify([])

    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        'limit': num_albums,  # Limit to num_albums
        'include_groups': 'album,single',  # Only include albums and singles
    }
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        albums_json = response.json().get('items', [])        

    # Calculate popularity for each album based on the total popularity of its tracks
        for album in albums_json:
            album_id = album['id']
            album['total_popularity'] = get_album_tracks_popularity(album_id, token)
    
    # Debug print to ensure 'total_popularity' is added to each album
        for album in albums_json:
             print(album['name'], album['total_popularity'])
    
    # Sort albums by their total popularity
        sorted_albums = sorted(albums_json, key=lambda x: x.get('total_popularity', 0), reverse=True)
    
        
        # Extract only the necessary parts of each album
        return jsonify(sorted_albums)
    else:
        print(f"Error: {response.status_code}")
        return jsonify([])

    
def get_album_tracks_popularity(album_id, token):
    total_popularity = 0
    
    if not album_id:
        print("album not found")
        return 0
    else:
        url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {'market': 'US'}
        response = requests.get(url, headers=headers, params = params)
        
        if response.status_code == 200:
            tracks_json = response.json().get('items')
            for track in tracks_json:
                track_popularity = track.get('popularity', 0)
                total_popularity += track_popularity
                print(track.get('name') + ' ' + str(total_popularity))
            return total_popularity
        else:
            print("Error:", response.status_code)
            return 0



