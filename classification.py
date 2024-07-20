import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
from sklearn.decomposition import PCA
import json
from pymongo import MongoClient

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client.spotify_db
users_collection = db.users

def cluster_tracks_with_visualization(spotify_id, output_csv='tracks_with_clusters.csv', num_clusters=10):
    # Fetch track data from MongoDB using Spotify ID
    user_data = users_collection.find_one({"spotify_id": spotify_id})
    if not user_data:
        print("User not found in the database.")
        return None

    all_tracks = user_data.get('tracks')
    if not all_tracks:
        print("No tracks found for the user.")
        return None

    # Convert track data to DataFrame
    df = pd.DataFrame(all_tracks)
    print(df.columns)

    # Select features for clustering
    features = ['acousticness', 'danceability', 'energy', 'instrumentalness', 
                'liveness', 'loudness', 'speechiness', 'tempo', 'valence']

    # Fill missing values with the mean of each column
    df[features] = df[features].fillna(df[features].mean())

    # Extract the feature data
    X = df[features].values

    # Normalize the features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # One-hot encode genres
    mlb = MultiLabelBinarizer()
    genres_encoded = mlb.fit_transform(df['genres'])
    genres_encoded *= 1.2  # Adjust the weight of genre features if needed

    # Combine normalized features with one-hot encoded genres
    X_combined = np.hstack((X_scaled, genres_encoded))

    # Apply PCA for dimensionality reduction
    pca = PCA(n_components=2)  # Reduce to 2 principal components for visualization
    X_pca = pca.fit_transform(X_combined)

    # Apply KMeans with specified number of clusters
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(X_combined)

    # Get cluster labels and add them to the DataFrame
    df['cluster_label'] = kmeans.labels_

    # Count number of tracks in each cluster
    cluster_counts = df['cluster_label'].value_counts().sort_index()

    # Print number of tracks in each cluster
    print("Number of tracks in each cluster:")
    for cluster, count in cluster_counts.items():
        print(f"Cluster {cluster}: {count} tracks")

    # Print the DataFrame with cluster labels
    print("\nDataFrame with Cluster Labels:")
    print(df)

    # Save the DataFrame with cluster labels back to CSV
    df_sorted = df.sort_values(by='cluster_label', ascending=True)
    df_sorted.to_csv(output_csv, index=False)

    # Create a dictionary to store clusters
    clusters_dict = {cluster: [] for cluster in range(num_clusters)}
    for _, row in df_sorted.iterrows():
        track_info = row.to_dict()
        cluster_label = track_info.pop('cluster_label')
        clusters_dict[cluster_label].append(track_info)

    # Convert the clusters dictionary to JSON
    clusters_json = json.dumps(clusters_dict, indent=4)
    
    print(f"\nClustering completed. Results saved to {output_csv}")
    return clusters_json

# Example usage:
spotify_id = "your_spotify_id_here"  # Replace with the actual Spotify ID
clusters_json = cluster_tracks_with_visualization(spotify_id, output_csv='tracks_with_clusters.csv', num_clusters=10)
if clusters_json:
    print(clusters_json)
