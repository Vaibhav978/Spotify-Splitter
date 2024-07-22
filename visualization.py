import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import skew
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split, GridSearchCV
import json
import joblib
from pymongo import MongoClient
import os



def visualize_data(spotify_id):
    client = MongoClient('mongodb://localhost:27017/')
    db = client.spotify_db
    users_collection = db.users
    user_data = users_collection.find_one({"spotify_id": spotify_id})
    if not user_data:
        print("User not found in the database.")
        return None

    all_tracks = user_data.get('tracks')
    if not all_tracks:
        print("No tracks found for the user.")
        return None

# MongoDB connection
    client = MongoClient('mongodb://localhost:27017/')
    db = client.spotify_db
    users_collection = db.users
# Sample data (replace with your actual data)
    data = pd.DataFrame(all_tracks)
    feature = 'speechiness'

# Check skewness
    skewness = skew(data[feature])
    print(feature)
    print(f"Skewness: {skewness}")  

# Plot histogram
    plt.hist(data[feature], bins=10, alpha=0.5)
    plt.title('Histogram of Feature1')
    plt.xlabel('Value')
    plt.ylabel('Frequency')

# Plot KDE
    sns.kdeplot(data[feature])
    plt.title('KDE Plot of Feature1')
    plt.xlabel('Value')
    plt.ylabel('Density')

    plt.show()
spotify_id = "d722jkq02u40mfghknaczltac"  # Replace with the actual Spotify ID
visualize_data(spotify_id)