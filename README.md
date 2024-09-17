# Spotify Playlist Splitter and Recommendation System 🎶

### Purpose

Have you ever found yourself frustrated with having all your favorite songs jumbled into a single playlist? I did too! With nearly 700 songs in my Liked Songs on Spotify, I often wanted to listen to a specific genre or mood but had to skip through unrelated tracks. The solution? This application — designed to automatically split your **Liked Songs** into multiple, sonically similar playlists using advanced machine learning and Spotify’s audio features.

### Project Overview

The **Spotify Playlist Splitter and Recommendation System** is a web-based tool that helps you analyze your Spotify music library and automatically organize your songs into personalized playlists. It clusters tracks based on their audio features, such as energy, danceability, and acousticness, as well as artists, genres, and albums. With a focus on user customization, it continuously improves playlist recommendations by integrating feedback.

### Key Features

- **Spotify OAuth 2.0 Authentication**: Secure login via Spotify’s OAuth system.
- **Music Library Analysis**: Fetches and analyzes your saved tracks using Spotify’s API.
- **Audio Feature Extraction**: Extracts detailed audio features like danceability, energy, acousticness, etc., to group similar songs together.
- **Track Clustering**: Implements a **Weighted KNN-Means algorithm** to intelligently cluster your tracks by features, genres, artists, and albums.
- **Automated Playlist Creation**: Generates new Spotify playlists directly from the app based on your clusters.
- **User Feedback Integration**: Uses feedback to continuously improve playlist creation by weighing the user's preferences over time.

### Tech Stack

- **Backend**: Python (Flask)
- **Spotify API**: Spotipy library
- **Database**: MongoDB (stores user data and track information)
- **Frontend**: HTML, CSS, JavaScript
- **Machine Learning**: Custom **Weighted KNN-Means** algorithm for clustering
- **Environment Management**: dotenv (for managing environment variables)

---

## Spotify API Integration 🎧

This project integrates with Spotify’s API using the **Spotipy** library. By logging in with Spotify’s OAuth 2.0, users can grant the app access to their music library, allowing the app to retrieve saved tracks, audio features, and artist details. These data points form the basis for analyzing and organizing the user's playlists.

---

## Data Collection & Processing 📊

After login, the app retrieves your saved tracks and extracts the following audio features:

- **Acousticness**: How acoustic the track is.
- **Danceability**: How suitable the track is for dancing.
- **Energy**: A measure of intensity and activity.
- **Valence**: The musical positiveness or happiness of a track.
- **Instrumentalness**: Whether a track is instrumental.
- **Tempo**: Speed of the track, in BPM.
- **Speechiness**: The presence of spoken words in the track.
- **Liveness**: Whether the track was recorded live.

These features, combined with artist, genre, and album data, are stored in **MongoDB** for clustering analysis.

---

## Track Clustering Algorithm 🔍

The core of this application is a **Weighted KNN-Means Algorithm**, which clusters tracks into groups based on their audio features, genres, artists, and albums. This algorithm optimizes for balance between multiple dimensions of similarity, so that playlists feel cohesive and personalized. Over time, the algorithm adjusts based on user feedback to improve accuracy and user satisfaction.

### Clustering Process:
1. **Initial Clustering**: Tracks are analyzed and grouped based on their audio features.
2. **User Feedback Loop**: The app identifies the three most prominent features contributing to each cluster. When a user selects a playlist, these features get slightly more weight in future clustering, personalizing recommendations.
3. **Playlist Updates**: New clusters are generated based on updated data, ensuring that user preferences are reflected in future playlists.

---

## Personalized Playlist Creation 🎼

Once the tracks are clustered, users can create playlists directly from the app. The app fetches track URIs from Spotify, generates a new playlist, and adds the clustered tracks to it, providing a seamless and tailored listening experience.

---

## Future Enhancements 🌱

- **Improved Clustering**: Further refinement of the algorithm to better account for nuanced user preferences.
- **Real-Time Feedback**: Enhanced user feedback integration to dynamically adjust playlists based on evolving listening habits.
- **UI Enhancements**: Improving the user interface for a more engaging experience.
- **Additional Filters**: Adding filters for moods, tempos, or release years, giving users more control over the playlists they generate.

---

## Contributing 🤝

Feel free to fork the repository, open issues, or submit pull requests. Contributions are always welcome!

---

---

Happy listening! 🎧✨
