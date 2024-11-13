from typing import Dict, List, Optional
import praw
import pymongo
from datetime import datetime
import uuid
from tqdm import tqdm

# MongoDB and Reddit Connection Setup
MONGODB_URI = "mongodb+srv://krunalpatel35538:YHFyBoSvWR1hKXkB@cluster0.lu5p4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
REDDIT_CLIENT_ID = "your_reddit_client_id"
REDDIT_CLIENT_SECRET = "your_reddit_client_secret"
REDDIT_USER_AGENT = "your_reddit_user_agent"


class EnhancedETL:
    def __init__(self):
        self.client = pymongo.MongoClient(MONGODB_URI)
        self.db = self.client['reddit_db']
        self.posts_collection = self.db['posts']
        self.searches_collection = self.db['searches']
        self.reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        
    def generate_search_id(self) -> str:
        """Generate a unique search ID."""
        return str(uuid.uuid4())
    
    def process_search_parameters(self, params: Dict) -> Dict:
        """Process and validate search parameters."""
        return {
            'subreddits': params.get('selected_buttons', []),
            'from_time': datetime.fromisoformat(params['from_time']),
            'to_time': datetime.fromisoformat(params['to_time']),
            'sort_types': params.get('option1', ['hot', 'new', 'top']),
            'post_limit': int(params.get('option2', 100)),
            'include_comments': params.get('option3', 'no') == 'yes',
            'search_text': params.get('search_text', ''),
            'comment_limit': 10
        }
    
    def save_search_record(self, search_id: str, params: Dict, post_ids: List[str]) -> None:
        """Save search record with associated post IDs."""
        search_record = {
            'search_id': search_id,
            'timestamp': datetime.utcnow(),
            'parameters': params,
            'post_ids': post_ids,
            'total_posts': len(post_ids)
        }
        self.searches_collection.insert_one(search_record)
    
    def scrape_and_store_posts(self, params: Dict) -> List[str]:
        """Scrape posts based on parameters and return list of post IDs."""
        post_ids = []
        
        for subreddit_name in params['subreddits']:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                for sort_type in params['sort_types']:
                    posts = getattr(subreddit, sort_type)(limit=params['post_limit'])
                    
                    for post in tqdm(list(posts), desc=f"Processing {sort_type} posts from r/{subreddit_name}"):
                        # Check if post is within time range
                        post_time = datetime.fromtimestamp(post.created_utc)
                        if not (params['from_time'] <= post_time <= params['to_time']):
                            continue
                        
                        # Check if post contains search text
                        if params['search_text'] and params['search_text'].lower() not in post.title.lower() and \
                           params['search_text'].lower() not in post.selftext.lower():
                            continue
                        
                        post_data = self.get_post_data(post, params['include_comments'], params['comment_limit'])
                        if post_data:
                            # Update or insert post
                            self.posts_collection.update_one(
                                {'id': post_data['id']},
                                {'$set': post_data},
                                upsert=True
                            )
                            post_ids.append(post_data['id'])
                            
            except Exception as e:
                print(f"Error processing r/{subreddit_name}: {e}")
                continue
                
        return post_ids
    
    def get_post_data(self, post, include_comments: bool, comment_limit: int) -> Optional[Dict]:
        """Extract post data with optional comments."""
        try:
            post_data = {
                'id': post.id,
                'title': post.title,
                'author': str(post.author) if post.author else '[deleted]',
                'created_utc': datetime.fromtimestamp(post.created_utc),
                'score': post.score,
                'upvote_ratio': post.upvote_ratio,
                'num_comments': post.num_comments,
                'url': post.url,
                'selftext': post.selftext,
                'subreddit': post.subreddit.display_name,
                'scraped_at': datetime.utcnow()
            }
            
            if include_comments:
                post_data['comments'] = self.get_comments(post, comment_limit)
                
            return post_data
        except Exception as e:
            print(f"Error processing post {post.id}: {e}")
            return None
    
    def get_comments(self, post, limit: int) -> List[Dict]:
        """Get comments from a post."""
        comments = []
        try:
            post.comments.replace_more(limit=limit)
            for comment in post.comments.list():
                comment_data = {
                    'id': comment.id,
                    'author': str(comment.author) if comment.author else '[deleted]',
                    'body': comment.body,
                    'created_utc': datetime.fromtimestamp(comment.created_utc),
                    'score': comment.score
                }
                comments.append(comment_data)
        except Exception as e:
            print(f"Error fetching comments: {e}")
        return comments
    
    def perform_search(self, search_params: Dict) -> Dict:
        """Perform search and return results."""
        try:
            # Generate unique search ID
            search_id = self.generate_search_id()
            
            # Process parameters
            processed_params = self.process_search_parameters(search_params)
            
            # Perform scraping and get post IDs
            post_ids = self.scrape_and_store_posts(processed_params)
            
            # Save search record
            self.save_search_record(search_id, processed_params, post_ids)
            
            # Return search summary
            return {
                "status": "success",
                "search_id": search_id,
                "total_posts": len(post_ids),
                "subreddits": processed_params['subreddits'],
                "time_range": {
                    "from": processed_params['from_time'].isoformat(),
                    "to": processed_params['to_time'].isoformat()
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }