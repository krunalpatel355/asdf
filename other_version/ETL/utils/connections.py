# utils/connections.py
import praw
import pymongo
import certifi
from config.settings import Config

class ConnectionManager:
    @staticmethod
    def get_mongodb_connection():
        try:
            # Check if using localhost or Atlas URI
            if Config.MONGODB_URI.startswith('mongodb://localhost'):
                # Local connection without SSL
                client = pymongo.MongoClient(
                    Config.MONGODB_URI,
                    serverSelectionTimeoutMS=5000
                )
            else:
                # Atlas connection with SSL
                client = pymongo.MongoClient(
                    Config.MONGODB_URI,
                    tlsCAFile=certifi.where(),
                    serverSelectionTimeoutMS=5000
                )
            
            # Test connection
            client.server_info()
            print("✅ Successfully connected to MongoDB!")
            return client
            
        except Exception as e:
            print(f"❌ MongoDB Connection Error: {e}")
            # More detailed error information for debugging
            print(f"Connection URI used: {Config.MONGODB_URI[:20]}...") # Show only start of URI for security
            print(f"Error type: {type(e).__name__}")
            raise

    @staticmethod
    def get_reddit_connection():
        try:
            reddit = praw.Reddit(
                client_id=Config.REDDIT_CLIENT_ID,
                client_secret=Config.REDDIT_CLIENT_SECRET,
                user_agent=Config.REDDIT_USER_AGENT
            )
            print("✅ Successfully connected to Reddit API!")
            return reddit
        except Exception as e:
            print(f"❌ Reddit API Connection Error: {e}")
            raise