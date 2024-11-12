from datetime import datetime
from typing import Dict, List, Optional
from tqdm import tqdm

class RedditExtractor:
    def __init__(self, reddit, include_comments: bool = True, comment_limit: int = 10):
        self.reddit = reddit
        self.include_comments = include_comments
        self.comment_limit = comment_limit

    def _extract_comment_data(self, comment) -> Dict:
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

    def _extract_post_comments(self, post) -> List[Dict]:
        comments = []
        try:
            post.comments.replace_more(limit=self.comment_limit)
            for comment in post.comments.list():
                try:
                    comments.append(self._extract_comment_data(comment))
                except Exception as e:
                    print(f"Error processing comment {comment.id}: {e}")
        except Exception as e:
            print(f"Error fetching comments: {e}")
        return comments

    def extract_post_data(self, post) -> Optional[Dict]:
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
                'permalink': post.permalink,
                'subreddit': post.subreddit.display_name,
                'is_video': post.is_video if hasattr(post, 'is_video') else False,
                'is_original_content': post.is_original_content,
                'over_18': post.over_18,
                'spoiler': post.spoiler,
                'stickied': post.stickied,
                'locked': post.locked,
                'link_flair_text': post.link_flair_text,
                'media': post.media if hasattr(post, 'media') else None,
                'media_metadata': post.media_metadata if hasattr(post, 'media_metadata') else None,
                'scraped_at': datetime.utcnow()
            }

            if self.include_comments:
                post_data['comments'] = self._extract_post_comments(post)

            return post_data
        except Exception as e:
            print(f"Error extracting post data: {e}")
            return None