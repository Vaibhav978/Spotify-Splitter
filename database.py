import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def test_mongo_connection(uri):
    try:
        # Create the MongoClient with the tlsCAFile parameter pointing to the certifi CA bundle
        client = MongoClient(uri, tlsCAFile=certifi.where())
        
        # Perform a server status command to check the connection
        client.admin.command('ping')
        print("MongoDB connection successful!")
    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {e}")

if __name__ == "__main__":
    # Define the MongoDB connection URI
    uri = "mongodb+srv://vibhusingh925:e*!*sWHJ_iWQy6*@spotifydb.vgf4v.mongodb.net/?retryWrites=true&w=majority"
    
    # Test the connection
    test_mongo_connection(uri)
