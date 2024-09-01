Spotify Playlist Splitter and Recommendation System
Table of Contents
Project Overview
Features
Tech Stack
Installation and Setup
Spotify API Integration
Data Collection and Processing
Track Clustering Algorithm
Personalized Playlist Creation
Future Enhancements
License

PURPOSE: 

Whenever I use Spotify and found a song I like I simply added it to my Liked Songs. This resulted me in saving nearly 700 songs to just one playlist. However, I always was frustrated when I wanted to listen to one genre or type of music and then had a different one pop up. Since I am extremely lazy and didn't want to make my own playlists, I created this program to take all the Liked Songs in a User's Playlist, and split it into multiple sonically similar playlists.

Project Overview
The Spotify Playlist Splitter and Recommendation System is a web-based application designed to help users analyze and split their Spotify music library into personalized playlists. It uses advanced machine learning techniques to cluster tracks based on audio features, artists, genres, and albums. Additionally, it integrates user feedback to continuously improve playlist recommendations, providing an enhanced and tailored listening experience.

Features
Spotify OAuth 2.0 Authentication: Secure user login using Spotify's OAuth 2.0 system.
Music Library Analysis: Fetches and analyzes a user's saved tracks using Spotify's API.
Audio Feature Extraction: Collects audio features like acousticness, danceability, energy, and more to analyze song similarities.
Track Clustering: Implements a Weighted KNN-Means algorithm for clustering tracks into playlists based on audio features, genres, artists, and albums.
Playlist Creation: Automatically generates and updates Spotify playlists based on personalized clusters.
User Feedback Integration: Continuously improves playlist recommendations by integrating user feedback.
Tech Stack
Backend: Python (Flask)
Spotify API: Spotipy library
Database: MongoDB (for storing user data and track information)
Frontend: HTML, CSS, JavaScript
Machine Learning: Weighted KNN-Means algorithm for track clustering
Environment Management: dotenv
Installation and Setup
Clone the Repository:

bash
git clone https://github.com/yourusername/spotify-playlist-splitter.git
cd spotify-playlist-splitter
Set Up Environment Variables: Create a .env file in the root directory and add your Spotify API credentials and other required environment variables.

makefile
CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=your_spotify_client_secret
FLASK_ENV=development
Install Dependencies: Install the required Python packages using pip.

bash
pip install -r requirements.txt
Run the Application: Ensure MongoDB is running, then start the Flask application.

bash
python app.py
Access the Application: Visit http://127.0.0.1:5002 in your browser to start using the Spotify Playlist Splitter.

Spotify API Integration
This project integrates with Spotify's API using the Spotipy library. Through OAuth 2.0, users can securely log in and give the application permission to access their music library. The app fetches user tracks, audio features, and artist details to perform data analysis.

Data Collection and Processing
Upon logging in, the app retrieves a user's saved tracks and extracts audio features (e.g., acousticness, danceability, energy) using the Spotify API. These features, along with artist and genre data, are stored in MongoDB for further analysis.

Track Clustering Algorithm
The core of this project is the Weighted KNN-Means Algorithm, which groups tracks into clusters based on their audio features, artists, genres, and albums. The algorithm balances multiple dimensions of similarity, providing highly tailored recommendations. It also incorporates feedback to improve the accuracy of clustering over time.

Personalized Playlist Creation
Once tracks are clustered, users can create playlists directly from the app. The playlist creation process fetches the track URIs, creates a new playlist on Spotify, and adds the tracks to the playlist, ensuring a smooth and seamless experience.

Future Enhancements
Improved Clustering Algorithm: Further refine the algorithm to account for additional user preferences.
Real-Time Feedback Integration: Allow users to rate individual playlists to dynamically adjust future recommendations.
Expanded Data Analytics: Provide users with more detailed insights into their music habits (e.g., favorite genres over time).
License
This project is licensed under the MIT License.