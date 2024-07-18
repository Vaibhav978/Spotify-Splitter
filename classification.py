import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
from sklearn.decomposition import PCA
import json

def cluster_tracks_with_visualization(input_csv='tracks.csv', output_csv='tracks_with_clusters.csv', num_clusters=10):
    # Load track data from CSV file
    df = pd.read_csv(input_csv)
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
    genres_encoded = mlb.fit_transform(df['genres'].apply(eval))
    genres_encoded * 1.2
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
    df_sorted = df.sort_values(by = 'cluster_label', ascending= True)
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
clusters_json = cluster_tracks_with_visualization(input_csv='tracks.csv', output_csv='tracks_with_clusters.csv', num_clusters=10)
