# import pandas as pd
# import matplotlib.pyplot as plt
# from scipy.stats import skew
# import numpy as np
# from sklearn.preprocessing import StandardScaler
# from pymongo import MongoClient
# from sklearn.preprocessing import PowerTransformer



# def visualize_data(spotify_id):
#     # Connect to MongoDB
#     client = MongoClient('mongodb://localhost:27017/')
#     db = client.spotify_db
#     users_collection = db.users
    
#     # Retrieve user data
#     user_data = users_collection.find_one({"spotify_id": spotify_id})
#     if not user_data:
#         print("User not found in the database.")
#         return None

#     all_tracks = user_data.get('tracks')
#     if not all_tracks:
#         print("No tracks found for the user.")
#         return None

#     # Convert data to DataFrame
#     df = pd.DataFrame(all_tracks)

#     # Select features for clustering
#     features = ['acousticness', 'danceability', 'energy', 'instrumentalness', 
#                 'liveness', 'loudness', 'speechiness', 'tempo', 'valence']

#     # Fill missing values with the mean of each column
#     df[features] = df[features].fillna(df[features].mean())

#     # Print skewness of each feature before transformation
#     print("SKEWNESS BEFORE TRANSFORMATION")
#     for feature in features:
#         feature_skewness = skew(df[feature])
#         print(f'Skewness of {feature}: {feature_skewness}')

#     # Extract the feature data
#     X = df[features].values

#     # Normalize the features
#     scaler = StandardScaler()
#     pt = PowerTransformer(method='yeo-johnson', standardize=True)
#     X_transformed = pt.fit_transform(X)
#     X_transformed = scaler.fit_transform(X_transformed)

#     # # Handle skewness
#     # for feature_idx in range(X_scaled.shape[1]):
#     #     feature_skewness = skew(X_scaled[:, feature_idx])
#     #     X_scaled[:, features.index(feature)] = winsorize(X_scaled[:, features.index(feature)], limits=[0.20, 0.20])  # Winsorize at 5% and 95%

#     #     max_iterations = 25
#     #     iteration = 0
#     #     while abs(feature_skewness) > 0.5 and iteration < max_iterations:
#     #         min_value = X_scaled[:, feature_idx].min()
#     #         if min_value <= 0:
#     #             X_scaled[:, feature_idx] -= min_value - 1
            
#     #         if feature_skewness > 1:  # Extremely right-skewed
#     #             X_scaled[:, feature_idx] = np.log1p(X_scaled[:, feature_idx])
#     #         elif feature_skewness > 0.5:  # Moderately right-skewed
#     #             X_scaled[:, feature_idx] = np.sqrt(X_scaled[:, feature_idx])
#     #         elif feature_skewness < -1:  # Extremely left-skewed
#     #             X_scaled[:, feature_idx] = (X_scaled[:, feature_idx] + 1) ** 3
#     #         elif feature_skewness < -0.5:  # Moderately left-skewed
#     #             X_scaled[:, feature_idx] = np.square(X_scaled[:, feature_idx])

#     #         feature_skewness = skew(X_scaled[:, feature_idx])
#     #         iteration += 1

#     # Print skewness of each feature after transformation
#     print("SKEWNESS AFTER TRANSFORMATION")
#     for feature_idx in range(X_transformed.shape[1]):
#         feature_skewness = skew(X_transformed[:, feature_idx])
#         feature_name = features[feature_idx]
#         print(f'Skewness of {feature_name}: {feature_skewness}')

#     feature_to_plot = 'instrumentalness'
#     #Plot histogram and KDE for one feature to visualize
#     plt.hist(df[feature_to_plot], bins=10, alpha=0.5)
#     plt.title(f'Histogram of {feature_to_plot}')
#     plt.xlabel('Value')
#     plt.ylabel('Frequency')
#     plt.show()

#     sns.kdeplot(df[feature_to_plot])
#     plt.title(f'KDE Plot of {feature_to_plot}')
#     plt.xlabel('Value')
#     plt.ylabel('Density')
#     plt.show()

# # Replace with the actual Spotify ID
# spotify_id = "d722jkq02u40mfghknaczltac"
# visualize_data(spotify_id)
