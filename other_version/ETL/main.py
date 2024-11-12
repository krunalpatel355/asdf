from config.settings import Config
from utils.connections import ConnectionManager
from etl.embedding import VectorSearch
from etl.extract import RedditExtractor
from etl.load import MongoLoader
from tqdm.notebook import tqdm

def get_user_preferences():
    print("Do you want to include comments? (yes/no):")
    include_comments = input().strip().lower() == 'yes'
    
    comment_limit = 0
    if include_comments:
        print("Enter maximum number of comment trees (default: 10):")
        comment_input = input().strip()
        comment_limit = int(comment_input) if comment_input else 10
    
    return include_comments, comment_limit

def main():
    try:
        # Initialize vector search
        vector_search = VectorSearch()
        vector_search.initialize_subreddits()
        
        # Get user query and similar subreddits
        query = input("\nEnter your search query: ")
        similar_subreddits = vector_search.find_similar_subreddits(query)
        
        # Get user preferences
        include_comments, comment_limit = get_user_preferences()
        
        # Setup connections and ETL components
        reddit = ConnectionManager.get_reddit_connection()
        mongo_client = ConnectionManager.get_mongodb_connection()
        posts_collection = mongo_client['reddit_db']['posts']
        
        extractor = RedditExtractor(reddit, include_comments, comment_limit)
        loader = MongoLoader(posts_collection)
        
        # Process each subreddit
        for subreddit_data in similar_subreddits:
            subreddit_name = subreddit_data['subreddit']
            print(f"\nProcessing r/{subreddit_name}...")
            
            try:
                subreddit = reddit.subreddit(subreddit_name)
                for sort_type in ['hot', 'new', 'top']:
                    print(f"Getting {sort_type} posts...")
                    posts = getattr(subreddit, sort_type)(limit=None)
                    
                    for post in tqdm(list(posts)):
                        post_data = extractor.extract_post_data(post)
                        if post_data:
                            loader.load_post(post_data)
                            
            except Exception as e:
                print(f"Error processing r/{subreddit_name}: {e}")
                continue

        print("\n✅ ETL process completed successfully!")
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()