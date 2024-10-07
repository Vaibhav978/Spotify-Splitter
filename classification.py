import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
from sklearn.model_selection import train_test_split, GridSearchCV
import json
import joblib
from pymongo import MongoClient
import os
from sklearn.preprocessing import PowerTransformer
from sklearn.metrics import pairwise_distances_argmin_min
import certifi

# MongoDB connection
uri = "mongodb+srv://vibhusingh925:e%2A%21%2AsWHJ_iWQy6*@spotifydb.vgf4v.mongodb.net/spotifydb?retryWrites=true&w=majority&tls=true"
client = MongoClient(uri, tlsCAFile=certifi.where())
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

    # Handle skewness
    pt = PowerTransformer(method='yeo-johnson', standardize=True)
    X_transformed = pt.fit_transform(X)
    X_transformed = scaler.fit_transform(X_transformed)

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
    genres_encoded *= 4  # Adjust the weight of genre features if needed

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
    artists_encoded *= 4 # Adjust the weight of artist features if needed

    # Combine normalized features with one-hot encoded genres and artists
    X_combined = np.hstack((X_transformed, genres_encoded, artists_encoded))
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

    # Initial cluster counts
    cluster_counts = df['cluster_label'].value_counts().sort_index()

    min_cluster_size = 10  # Define your threshold

    iteration = 1
    while True and iteration < 50:
        small_clusters = cluster_counts[cluster_counts < min_cluster_size].index.tolist()
        if len(small_clusters) == 0:
            break

        print(f"Iteration {iteration}: Found {len(small_clusters)} small clusters.")
        
        # Exclude small cluster centers
        large_cluster_centers = np.delete(best_kmeans.cluster_centers_, small_clusters, axis=0)

        # Compute distances of small cluster points to large cluster centers
        small_cluster_combined_features = X_combined[df['cluster_label'].isin(small_clusters)]
        distances, assignments = pairwise_distances_argmin_min(small_cluster_combined_features, large_cluster_centers)

        # Remaining valid cluster labels after excluding small clusters
        remaining_clusters = list(set(range(len(best_kmeans.cluster_centers_))) - set(small_clusters))

        # Create new labels based on assignments to the remaining clusters
        new_labels = np.array([remaining_clusters[int(new_label)] for new_label in assignments if new_label < len(remaining_clusters)])

        # Debug: Check the number of rows and the number of new labels
        print(f"Number of tracks to reassign: {len(small_cluster_combined_features)}")
        print(f"Number of new labels generated: {len(new_labels)}")

        # Handle mismatch in number of tracks and labels
        if len(small_cluster_combined_features) != len(new_labels):
            print("Error: Mismatch between number of tracks and new labels. Attempting to resolve...")
            
            # Identify how many tracks are missing labels
            missing_count = len(small_cluster_combined_features) - len(new_labels)
            print(f"Missing {missing_count} new labels. Assigning them manually.")
            
            # Recompute distances to large cluster centers for all small-cluster tracks
            assignments = pairwise_distances_argmin_min(small_cluster_combined_features, large_cluster_centers)
            
            # For the missing labels, assign them to the closest valid cluster
            missing_labels = [remaining_clusters[int(assignment)] for assignment in assignments[:missing_count]]
            
            # Append the missing labels to the new_labels array
            new_labels = np.concatenate([new_labels, missing_labels])
            
            print(f"Number of labels after filling missing values: {len(new_labels)}")

        # Now assign the updated labels back to the DataFrame
        if len(small_cluster_combined_features) == len(new_labels):
            df.loc[df['cluster_label'].isin(small_clusters), 'cluster_label'] = new_labels
            print("Successfully reassigned all small cluster tracks.")
        else:
            print("Final mismatch detected. Please review the data.")
            break

        # Recompute cluster counts
        cluster_counts = df['cluster_label'].value_counts().sort_index()

        iteration += 1

    # Print number of tracks in each cluster after all iterations
    final_cluster_counts = df['cluster_label'].value_counts().sort_index()
    print("Number of tracks in each cluster after reassignment:")
    for cluster, count in final_cluster_counts.items():
        print(f"Cluster {cluster}: {count} tracks")

    # Reassign cluster labels to be sequential
    unique_labels = sorted(df['cluster_label'].unique())
    label_map = {old_label: new_label for new_label, old_label in enumerate(unique_labels)}
    df['cluster_label'] = df['cluster_label'].map(label_map)

    # Create a dictionary to store clusters
    clusters_dict = {label_map[cluster]: [] for cluster in unique_labels}
    for _, row in df.iterrows():
        track_info = row.to_dict()
        cluster_label = track_info.pop('cluster_label')
        clusters_dict[cluster_label].append(track_info)

    # Convert the clusters dictionary to JSON
    clusters_json = json.dumps(clusters_dict, indent=4)

    # Save the DataFrame with updated cluster labels back to CSV
    df_sorted = df.sort_values(by='cluster_label', ascending=True)
    df_sorted.to_csv(output_csv, index=False)

    print(f"\nClustering completed. Results saved to {output_csv}")
    return clusters_json


def extract_top_genres_per_cluster(df, genres_encoded, mlb_genres, cluster_labels, top_n=2):
    # Create a DataFrame for genres with cluster labels
    genre_df = pd.DataFrame(genres_encoded, columns=mlb_genres.classes_)
    genre_df['cluster_label'] = cluster_labels
    
    # Dictionary to store top genres per cluster
    top_genres_per_cluster = {}

