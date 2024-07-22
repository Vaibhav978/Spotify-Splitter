import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split, GridSearchCV
import json
import joblib
from pymongo import MongoClient
import os

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client.spotify_db
users_collection = db.users

def cluster_tracks_with_visualization(spotify_id, output_csv='tracks_with_clusters.csv', model_path='kmeans_model.pkl', load_existing_model=False):
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
# One-hot encode genres
    mlb = MultiLabelBinarizer()
    genres_encoded = mlb.fit_transform(df['genres'])
    genres_encoded = genres_encoded.astype(float)  # Convert to float
    genres_encoded *= 1.225  # Adjust the weight of genre features if needed     

    # Combine normalized features with one-hot encoded genres
    X_combined = np.hstack((X_scaled, genres_encoded))

    # Load the existing model if specified, otherwise train a new one
    if load_existing_model and os.path.exists(model_path):
        best_kmeans = joblib.load(model_path)
        print("Loaded existing model from disk.")
    else:
        # Split the data into training and testing sets
        X_train, X_test = train_test_split(X_combined, test_size=0.2, random_state=42)

        # Hyperparameter tuning for KMeans (e.g., finding the best number of clusters)
        param_grid = {'n_clusters': [5, 10, 15, 20]}
        kmeans = KMeans(random_state=42)
        grid_search = GridSearchCV(kmeans, param_grid, cv=3)
        grid_search.fit(X_train)

        best_kmeans = grid_search.best_estimator_
        print(f"Best number of clusters: {best_kmeans.n_clusters}")

        # Save the trained model
        joblib.dump(best_kmeans, model_path)

    # Get cluster labels for the entire dataset
    df['cluster_label'] = best_kmeans.predict(X_combined)

    # Count number of tracks in each cluster
    cluster_counts = df['cluster_label'].value_counts().sort_index()

    # Print number of tracks in each cluster
    print("Number of tracks in each cluster:")
    for cluster, count in cluster_counts.items():
        print(f"Cluster {cluster}: {count} tracks")

    # Print the DataFrame with cluster labels

    # Save the DataFrame with cluster labels back to CSV
    df_sorted = df.sort_values(by='cluster_label', ascending=True)
    df_sorted.to_csv(output_csv, index=False)

    # Create a dictionary to store clusters
    clusters_dict = {cluster: [] for cluster in range(best_kmeans.n_clusters)}
    for _, row in df_sorted.iterrows():
        track_info = row.to_dict()
        cluster_label = track_info.pop('cluster_label')
        clusters_dict[cluster_label].append(track_info)

    # Convert the clusters dictionary to JSON
    clusters_json = json.dumps(clusters_dict, indent=4)
    
    print(f"\nClustering completed. Results saved to {output_csv}")
    print(len(clusters_dict))
    count = 0
    for label, tracks in clusters_dict.items():
        for track in tracks:
         count += 1

    return clusters_json

# Example usage:
spotify_id = "d722jkq02u40mfghknaczltac"  # Replace with the actual Spotify ID
clusters_json = cluster_tracks_with_visualization(spotify_id, output_csv='tracks_with_clusters.csv',  model_path='kmeans_model.pkl', load_existing_model=True)
