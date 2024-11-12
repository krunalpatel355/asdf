import pandas as pd
from datetime import datetime
import json
from collections import Counter
import matplotlib.pyplot as plt
from typing import List, Dict, Any

class RedditAnalyzer:
    def __init__(self):
        self.df = None
        
    def load_data(self, data: List[Dict[Any, Any]]) -> None:
        """
        Load Reddit data into a pandas DataFrame
        """
        self.df = pd.DataFrame(data)
        # Convert timestamp columns to datetime
        timestamp_cols = ['created_utc', 'last_updated', 'scraped_at']
        for col in timestamp_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col])
                
    def basic_stats(self) -> Dict[str, Any]:
        """
        Calculate basic statistics about the dataset
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data first.")
            
        stats = {
            'total_posts': len(self.df),
            'unique_authors': self.df['author'].nunique(),
            'total_comments': self.df['num_comments'].sum(),
            'avg_score': self.df['score'].mean(),
            'avg_upvote_ratio': self.df['upvote_ratio'].mean(),
            'subreddit_distribution': dict(self.df['subreddit'].value_counts()),
            'posts_over_time': self.df.groupby(self.df['created_utc'].dt.date).size().to_dict(),
            'media_stats': {
                'videos': self.df['is_video'].sum(),
                'original_content': self.df['is_original_content'].sum()
            }
        }
        return stats
    
    def author_analysis(self) -> Dict[str, Any]:
        """
        Analyze author activity and engagement
        """
        author_stats = {
            'top_authors': dict(self.df.groupby('author')['score'].mean().nlargest(10)),
            'most_active': dict(self.df['author'].value_counts().head(10)),
            'avg_comments_per_author': self.df.groupby('author')['num_comments'].mean().mean()
        }
        return author_stats
    
    def engagement_metrics(self) -> Dict[str, Any]:
        """
        Calculate engagement metrics
        """
        metrics = {
            'high_engagement_posts': self.df[self.df['score'] > self.df['score'].mean()].shape[0],
            'comment_distribution': {
                'low': self.df[self.df['num_comments'] < 10].shape[0],
                'medium': self.df[(self.df['num_comments'] >= 10) & (self.df['num_comments'] < 50)].shape[0],
                'high': self.df[self.df['num_comments'] >= 50].shape[0]
            },
            'avg_upvote_ratio': self.df['upvote_ratio'].mean(),
            'controversial_posts': self.df[self.df['upvote_ratio'] < 0.5].shape[0]
        }
        return metrics
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive analysis report
        """
        stats = self.basic_stats()
        author_stats = self.author_analysis()
        engagement = self.engagement_metrics()
        
        report = f"""
Reddit Data Analysis Report
==========================
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Overview
--------
Total Posts Analyzed: {stats['total_posts']}
Unique Authors: {stats['unique_authors']}
Total Comments: {stats['total_comments']}

Engagement Metrics
-----------------
Average Score: {stats['avg_score']:.2f}
Average Upvote Ratio: {stats['avg_upvote_ratio']:.2f}
High Engagement Posts: {engagement['high_engagement_posts']}
Controversial Posts: {engagement['controversial_posts']}

Top Authors
-----------
"""
        for author, score in author_stats['top_authors'].items():
            report += f"{author}: {score:.2f} avg score\n"
            
        return report

    def plot_activity_over_time(self) -> None:
        """
        Create a plot showing post activity over time
        """
        activity = self.df.groupby(self.df['created_utc'].dt.date).size()
        plt.figure(figsize=(12, 6))
        activity.plot(kind='line')
        plt.title('Post Activity Over Time')
        plt.xlabel('Date')
        plt.ylabel('Number of Posts')
        plt.grid(True)
        plt.tight_layout()
        
# Example usage
if __name__ == "__main__":
    # Sample data loading
    data = [
        {
            "_id": "673038d469ed51165e62761e",
            "id": "1gnd8a8",
            "author": "optimalg",
            "comments": [],  # Array of 98 comments
            "created_utc": "2024-11-09T11:01:15.000+00:00",
            "is_original_content": False,
            "is_video": False,
            "num_comments": 100,
            "score": 35,
            "subreddit": "politics",
            "title": "Saturday Morning Political Cartoon Thread",
            "upvote_ratio": 0.82
        }
        # ... more data ...
    ]
    
    analyzer = RedditAnalyzer()
    analyzer.load_data(data)
    print(analyzer.generate_report())