# enhanced_etl.py
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import praw
import pymongo
from tqdm import tqdm

@dataclass
class SearchParameters:
    topics: List[str]
    from_time: datetime
    to_time: datetime
    post_types: List[str]
    post_limit: int
    include_comments: bool
    search_text: Optional[str] = None

class EnhancedETL:
    def __init__(self, mongodb_uri: str, reddit_credentials: Dict):
        self.client = pymongo.MongoClient(mongodb_uri)
        self.db = self.client['reddit_db']
        self.posts_collection = self.db['posts']
        self.search_history_collection = self.db['search_history']
        
        self.reddit = praw.Reddit(
            client_id=reddit_credentials['client_id'],
            client_secret=reddit_credentials['client_secret'],
            user_agent=reddit_credentials['user_agent']
        )
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create necessary indexes for better query performance."""
        self.posts_collection.create_index([('search_id', pymongo.ASCENDING)])
        self.posts_collection.create_index([('created_utc', pymongo.ASCENDING)])
        self.posts_collection.create_index([('subreddit', pymongo.ASCENDING)])
        self.search_history_collection.create_index([('search_id', pymongo.ASCENDING)], unique=True)
    
    def perform_search(self, params: SearchParameters) -> str:
        """Perform search and ETL process based on user parameters."""
        # Generate unique search ID
        search_id = str(uuid.uuid4())
        
        # Record search parameters
        self._record_search(search_id, params)
        
        posts_processed = 0
        for subreddit_name in params.topics:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                for sort_type in params.post_types:
                    posts = getattr(subreddit, sort_type)(limit=params.post_limit)
                    
                    for post in tqdm(list(posts), desc=f"Processing {sort_type} posts from r/{subreddit_name}"):
                        if self._should_process_post(post, params):
                            post_data = self._process_post(post, search_id, params.include_comments)
                            if post_data:
                                self._save_post(post_data)
                                posts_processed += 1
                                
            except Exception as e:
                print(f"Error processing r/{subreddit_name}: {e}")
                continue
        
        # Update search record with results
        self._update_search_record(search_id, posts_processed)
        
        return search_id
    
    def _should_process_post(self, post, params: SearchParameters) -> bool:
        """Check if post meets search criteria."""
        post_time = datetime.fromtimestamp(post.created_utc)
        
        # Check time range
        if not (params.from_time <= post_time <= params.to_time):
            return False
        
        # Check search text if provided
        if params.search_text:
            search_text = params.search_text.lower()
            if search_text not in post.title.lower() and search_text not in post.selftext.lower():
                return False
                
        return True
    
    def _process_post(self, post, search_id: str, include_comments: bool) -> Optional[Dict]:
        """Process post data and optionally include comments."""
        try:
            post_data = {
                'search_id': search_id,
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
                post_data['comments'] = self._get_comments(post)
                
            return post_data
            
        except Exception as e:
            print(f"Error processing post {post.id}: {e}")
            return None
    
    def _get_comments(self, post, limit: int = 10) -> List[Dict]:
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
    
    def _save_post(self, post_data: Dict):
        """Save post data to MongoDB."""
        try:
            self.posts_collection.update_one(
                {'id': post_data['id'], 'search_id': post_data['search_id']},
                {'$set': post_data},
                upsert=True
            )
        except Exception as e:
            print(f"Error saving post: {e}")
    
    def _record_search(self, search_id: str, params: SearchParameters):
        """Record search parameters and metadata."""
        search_record = {
            'search_id': search_id,
            'timestamp': datetime.utcnow(),
            'parameters': {
                'topics': params.topics,
                'from_time': params.from_time,
                'to_time': params.to_time,
                'post_types': params.post_types,
                'post_limit': params.post_limit,
                'include_comments': params.include_comments,
                'search_text': params.search_text
            },
            'status': 'in_progress'
        }
        self.search_history_collection.insert_one(search_record)
    
    def _update_search_record(self, search_id: str, posts_processed: int):
        """Update search record with results."""
        self.search_history_collection.update_one(
            {'search_id': search_id},
            {
                '$set': {
                    'status': 'completed',
                    'posts_processed': posts_processed,
                    'completed_at': datetime.utcnow()
                }
            }
        )
    
    def get_search_results(self, search_id: str) -> Dict:
        """Get results for a specific search."""
        search_record = self.search_history_collection.find_one({'search_id': search_id})
        posts = list(self.posts_collection.find({'search_id': search_id}))
        
        return {
            'search_metadata': search_record,
            'posts': posts
        }