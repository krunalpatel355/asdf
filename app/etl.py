import praw
import pymongo
from datetime import datetime
from typing import Dict, List, Optional
import sys
from tqdm.notebook import tqdm

# MongoDB and Reddit Connection Setup
MONGODB_URI = "mongodb+srv://krunalpatel35538:YHFyBoSvWR1hKXkB@cluster0.lu5p4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
REDDIT_CLIENT_ID = "your_reddit_client_id"
REDDIT_CLIENT_SECRET = "your_reddit_client_secret"
REDDIT_USER_AGENT = "your_reddit_user_agent"

class ConnectionManager:
    @staticmethod
    def setup_mongodb():
        """Set up MongoDB connection."""
        try:
            client = pymongo.MongoClient(MONGODB_URI)
            db = client['reddit_db']
            posts_collection = db['posts']
            
            # Test connection
            client.server_info()
            print("✅ Successfully connected to MongoDB!")
            return client, db, posts_collection
            
        except Exception as e:
            print(f"❌ MongoDB Connection Error: {e}")
            sys.exit(1)
    
    @staticmethod
    def setup_reddit():
        """Set up Reddit API connection."""
        try:
            reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent=REDDIT_USER_AGENT
            )
            print("✅ Successfully connected to Reddit API!")
            return reddit
            
        except Exception as e:
            print(f"❌ Reddit API Connection Error: {e}")
            sys.exit(1)

# Comment Data Collector
class CommentCollector:
    @staticmethod
    def get_comment_data(comment) -> Dict:
        """Extract comment data."""
        return {
            'id': comment.id,
            'author': str(comment.author) if comment.author else '[deleted]',
            'body': comment.body,
            'created_utc': datetime.fromtimestamp(comment.created_utc),
            'score': comment.score,
            'is_submitter': comment.is_submitter,
            'parent_id': comment.parent_id,
            'edited': comment.edited if hasattr(comment, 'edited') else False
        }
    
    @staticmethod
    def get_comments(post, comment_limit: int) -> List[Dict]:
        """Get comments from a post."""
        comments = []
        try:
            post.comments.replace_more(limit=comment_limit)
            for comment in post.comments.list():
                try:
                    comment_data = CommentCollector.get_comment_data(comment)
                    comments.append(comment_data)
                except Exception as e:
                    print(f"Error processing comment {comment.id}: {e}")
                    continue
        except Exception as e:
            print(f"Error fetching comments: {e}")
        return comments

# Post Data Collector
class PostCollector:
    def __init__(self, include_comments: bool = True, comment_limit: int = 10):
        self.include_comments = include_comments
        self.comment_limit = comment_limit

    def get_post_data(self, post) -> Optional[Dict]:
        """Extract post data and optionally comments."""
        try:
            post_data = {
                # Basic information
                'id': post.id,
                'title': post.title,
                'author': str(post.author) if post.author else '[deleted]',
                'created_utc': datetime.fromtimestamp(post.created_utc),
                'score': post.score,
                'upvote_ratio': post.upvote_ratio,
                'num_comments': post.num_comments,
                'url': post.url,
                'selftext': post.selftext,
                'permalink': post.permalink,
                'subreddit': post.subreddit.display_name,
                
                # Metadata
                'is_video': post.is_video if hasattr(post, 'is_video') else False,
                'is_original_content': post.is_original_content,
                'over_18': post.over_18,
                'spoiler': post.spoiler,
                'stickied': post.stickied,
                'locked': post.locked,
                'link_flair_text': post.link_flair_text,
                
                # Media
                'media': post.media if hasattr(post, 'media') else None,
                'media_metadata': post.media_metadata if hasattr(post, 'media_metadata') else None,
                
                # Timestamps
                'scraped_at': datetime.utcnow(),
                'last_updated': datetime.utcnow()
            }
            
            # Add comments if enabled
            if self.include_comments:
                post_data['comments'] = CommentCollector.get_comments(post, self.comment_limit)
                
            return post_data
            
        except Exception as e:
            print(f"Error getting post details: {e}")
            return None

# MongoDB Index Manager
class IndexManager:
    def __init__(self, collection):
        self.collection = collection
    
    def create_indexes(self):
        """Create MongoDB indexes for better query performance."""
        indexes: List[Tuple[str, int]] = [
            ('id', pymongo.ASCENDING),
            ('subreddit', pymongo.ASCENDING),
            ('created_utc', pymongo.ASCENDING)
        ]
        for field, direction in indexes:
            try:
                self.collection.create_index(
                    [(field, direction)],
                    unique=(field == 'id')
                )
            except Exception as e:
                print(f"Warning: Failed to create index for {field}: {e}")

# Main Scraper Class
class RedditScraper:
    def __init__(self, include_comments: bool = True, comment_limit: int = 10):
        """Initialize the Reddit Scraper with configurable options."""
        self.include_comments = include_comments
        self.comment_limit = comment_limit
        
        # Setup connections
        self.client, self.db, self.posts_collection = ConnectionManager.setup_mongodb()
        self.reddit = ConnectionManager.setup_reddit()
        
        # Create indexes
        index_manager = IndexManager(self.posts_collection)
        index_manager.create_indexes()
        
        # Initialize collectors
        self.post_collector = PostCollector(include_comments, comment_limit)
    
    def scrape_subreddits(self, subreddits: Optional[List[str]] = None, 
                         post_limit: Optional[int] = None,
                         sort_types: List[str] = ['hot', 'new', 'top']):
        """Scrape posts from specified subreddits."""
        if subreddits is None:
            print("\nEnter topic name (separated by comma):")
            user_input = input().strip().lower()
            subreddits = [s.strip() for s in user_input.split(',')]
        
        if post_limit is None:
            print("Enter maximum number of posts per subreddit (press Enter for no limit):")
            limit_input = input().strip()
            post_limit = int(limit_input) if limit_input else None
        
        # Comment handling moved here
        if self.include_comments:
            print("Enter maximum number of comment trees to expand (default is 10):")
            comment_input = input().strip()
            self.comment_limit = int(comment_input) if comment_input else 10
        else:
            self.comment_limit = 0
        
        posts_processed = 0
        
        for subreddit_name in subreddits:
            print(f"\nProcessing r/{subreddit_name}...")
            
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                subreddit.id  # Test if subreddit exists
                
                for sort_type in sort_types:
                    print(f"Getting {sort_type} posts...")
                    posts = getattr(subreddit, sort_type)(limit=post_limit)
                    
                    for post in tqdm(list(posts), desc=f"{sort_type} posts"):
                        try:
                            post_data = self.post_collector.get_post_data(post)
                            
                            if post_data:
                                self.posts_collection.update_one(
                                    {'id': post_data['id']},
                                    {'$set': post_data},
                                    upsert=True
                                )
                                posts_processed += 1
                                 
                        except pymongo.errors.DuplicateKeyError:
                            continue
                        except Exception as e:
                            print(f"Error processing post: {e}")
                            continue
                            
            except Exception as e:
                print(f"Error accessing r/{subreddit_name}: {e}")
                continue
        
        print(f"\n✅ Completed! Total posts processed: {posts_processed}")
        print(f"Posts are stored in the 'posts' collection of 'reddit_db' database")

def main():
    """Main function to run the scraper with user configuration."""
    print("Do you want to include comments? (yes/no):")
    include_comments = input().strip().lower() == 'yes'
    
    scraper = RedditScraper(include_comments=include_comments)
    scraper.scrape_subreddits()

if __name__ == "__main__":
    main()
