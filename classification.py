import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
from sklearn.model_selection import train_test_split, GridSearchCV
import json
import joblib
from pymongo import MongoClient
import os
from scipy.stats import skew

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client.spotify_db
users_collection = db.users

def cluster_tracks_with_visualization(spotify_id, output_csv='tracks_with_clusters.csv', model_path='kmeans_model.pkl', genres_mlb_path='genres_mlb.pkl', artists_mlb_path='artists_mlb.pkl', feature_dim_path='feature_dim.pkl', load_existing_model=False):
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

    # Handle skewness
    skewness = [skew(X_scaled[:, i]) for i in range(X_scaled.shape[1])]
    for feature_idx, feature_skewness in enumerate(skewness):
        if feature_skewness > 1:  # Extremely right-skewed
            X_scaled[:, feature_idx] = np.log1p(X_scaled[:, feature_idx])
        elif feature_skewness > 0.5:  # Moderately right-skewed
            X_scaled[:, feature_idx] = np.sqrt(X_scaled[:, feature_idx])
        elif feature_skewness < -1:  # Extremely left-skewed
            X_scaled[:, feature_idx] = X_scaled[:, feature_idx] ** 3
        elif feature_skewness < -0.5:  # Moderately left-skewed
            X_scaled[:, feature_idx] = X_scaled[:, feature_idx] ** 2

    # One-hot encode genres
    if load_existing_model and os.path.exists(genres_mlb_path):
        mlb_genres = joblib.load(genres_mlb_path)
        print("Loaded existing genres MultiLabelBinarizer from disk.")
    else:
        mlb_genres = MultiLabelBinarizer()
        genres_encoded = mlb_genres.fit_transform(df['genres'])
        joblib.dump(mlb_genres, genres_mlb_path)
        print("Trained and saved new genres MultiLabelBinarizer.")

    genres_encoded = mlb_genres.transform(df['genres'])
    genres_encoded = genres_encoded.astype(float)
    genres_encoded *= 1.3  # Adjust the weight of genre features if needed

    # One-hot encode artists
    if load_existing_model and os.path.exists(artists_mlb_path):
        mlb_artists = joblib.load(artists_mlb_path)
        print("Loaded existing artists MultiLabelBinarizer from disk.")
    else:
        mlb_artists = MultiLabelBinarizer()
        artists_encoded = mlb_artists.fit_transform(df['artists'])
        joblib.dump(mlb_artists, artists_mlb_path)
        print("Trained and saved new artists MultiLabelBinarizer.")

    artists_encoded = mlb_artists.transform(df['artists'])
    artists_encoded = artists_encoded.astype(float)
    artists_encoded *= 1.3  # Adjust the weight of artist features if needed

    # Combine normalized features with one-hot encoded genres and artists
    X_combined = np.hstack((X_scaled, genres_encoded, artists_encoded))
    print(f"Shape of combined feature matrix: {X_combined.shape}")

    # Check for any remaining NaN values
    if np.isnan(X_combined).any():
        print("Data contains NaN values after preprocessing. Filling with mean values.")
        X_combined = np.nan_to_num(X_combined, nan=np.nanmean(X_combined))

    # Load the existing model if specified, otherwise train a new one
    if load_existing_model and os.path.exists(model_path):
        best_kmeans = joblib.load(model_path)
        print("Loaded existing model from disk.")
        
        # Load saved feature dimensions
        if os.path.exists(feature_dim_path):
            with open(feature_dim_path, 'r') as f:
                saved_features_dim = int(f.read().strip())
            if saved_features_dim != X_combined.shape[1]:
                print(f"Feature dimension mismatch: model expects {saved_features_dim} but got {X_combined.shape[1]}. Retraining the model.")
                retrain = True
            else:
                retrain = False
        else:
            print("Feature dimensions file not found. Retraining the model.")
            retrain = True

        if retrain:
            # Split the data into training and testing sets
            X_train, X_test = train_test_split(X_combined, test_size=0.2, random_state=42)

            # Hyperparameter tuning for KMeans (e.g., finding the best number of clusters)
            param_grid = {'n_clusters': [5, 10, 15, 20]}
            kmeans = KMeans(random_state=42)
            grid_search = GridSearchCV(kmeans, param_grid, cv=3)
            grid_search.fit(X_train)

            best_kmeans = grid_search.best_estimator_
            print(f"Best number of clusters: {best_kmeans.n_clusters}")

            # Save the trained model and encoders
            joblib.dump(best_kmeans, model_path)
            joblib.dump(mlb_genres, genres_mlb_path)
            joblib.dump(mlb_artists, artists_mlb_path)

            # Save feature dimensions
            with open(feature_dim_path, 'w') as f:
                f.write(str(X_combined.shape[1]))

    else:
        # Model was loaded successfully and dimensions match
        pass

    # Get cluster labels for the entire dataset
    df['cluster_label'] = best_kmeans.predict(X_combined)

    # Count number of tracks in each cluster
    cluster_counts = df['cluster_label'].value_counts().sort_index()

    # Print number of tracks in each cluster
    print("Number of tracks in each cluster:")
    for cluster, count in cluster_counts.items():
        print(f"Cluster {cluster}: {count} tracks")

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
    return clusters_json

# Example usage:
spotify_id = "d722jkq02u40mfghknaczltac"  # Replace with the actual Spotify ID
clusters_json = cluster_tracks_with_visualization(spotify_id, output_csv='tracks_with_clusters.csv', model_path='kmeans_model.pkl', genres_mlb_path='genres_mlb.pkl', artists_mlb_path='artists_mlb.pkl', feature_dim_path='feature_dim.pkl', load_existing_model=True)
