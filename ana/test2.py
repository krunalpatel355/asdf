import pandas as pd
import numpy as np
from datetime import datetime
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from collections import Counter
import networkx as nx
from textblob import TextBlob
import matplotlib.pyplot as plt
import seaborn as sns

# Create dummy data
dummy_data = [
    {
        "id": "1gnd8a8",
        "author": "user_1",
        "created_utc": "2024-11-09T11:01:15.000+00:00",
        "title": "The Impact of AI on Modern Society",
        "selftext": "Let's discuss how artificial intelligence is changing our daily lives and future prospects.",
        "subreddit": "technology",
        "score": 1500,
        "upvote_ratio": 0.92,
        "num_comments": 150,
        "comments": [
            {"author": "tech_enthusiast", "body": "AI has revolutionized everything from healthcare to education!", "score": 45},
            {"author": "skeptic123", "body": "We need to be careful about AI safety though.", "score": 28},
            {"author": "optimist", "body": "The possibilities are endless with this technology.", "score": 35}
        ]
    },
    {
        "id": "1gnd8b9",
        "author": "user_2",
        "created_utc": "2024-11-09T12:30:00.000+00:00",
        "title": "Climate Change: Latest Research Findings",
        "selftext": "New studies show accelerating impact of climate change on global ecosystems.",
        "subreddit": "science",
        "score": 2000,
        "upvote_ratio": 0.88,
        "num_comments": 200,
        "comments": [
            {"author": "scientist_1", "body": "The data is concerning but there's still hope if we act now.", "score": 65},
            {"author": "environmentalist", "body": "We need immediate action on this issue!", "score": 42},
            {"author": "researcher", "body": "These findings align with previous studies.", "score": 38}
        ]
    },
    {
        "id": "1gnd8c0",
        "author": "user_3",
        "created_utc": "2024-11-09T14:15:00.000+00:00",
        "title": "Breaking: Major Policy Change Announced",
        "selftext": "Government announces new economic policies affecting multiple sectors.",
        "subreddit": "politics",
        "score": 1200,
        "upvote_ratio": 0.75,
        "num_comments": 300,
        "comments": [
            {"author": "policy_expert", "body": "This could have significant implications for the economy.", "score": 55},
            {"author": "critic", "body": "This policy seems short-sighted and problematic.", "score": -20},
            {"author": "analyst", "body": "The market will need time to adjust to these changes.", "score": 30}
        ]
    }
]

class RedditAnalyzer:
    def __init__(self, data):
        self.data = data
        self.sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    
    def basic_statistics(self):
        """Calculate basic statistics about the posts"""
        stats = {
            'total_posts': len(self.data),
            'total_comments': sum(post['num_comments'] for post in self.data),
            'average_score': np.mean([post['score'] for post in self.data]),
            'average_upvote_ratio': np.mean([post['upvote_ratio'] for post in self.data]),
            'subreddits': Counter([post['subreddit'] for post in self.data])
        }
        return stats

    def sentiment_analysis(self):
        """Perform sentiment analysis on posts and comments"""
        results = []
        for post in self.data:
            # Analyze post title and content
            post_sentiment = self.sentiment_analyzer(post['title'] + " " + post['selftext'])[0]
            
            # Analyze comments
            comment_sentiments = [self.sentiment_analyzer(comment['body'])[0] 
                                for comment in post['comments']]
            
            results.append({
                'post_id': post['id'],
                'title_sentiment': post_sentiment,
                'comment_sentiments': comment_sentiments,
                'average_comment_sentiment': np.mean([
                    1 if s['label'] == 'POSITIVE' else 0 for s in comment_sentiments
                ])
            })
        return results

    def user_segmentation(self):
        """Segment users based on their activity patterns"""
        user_data = {}
        
        for post in self.data:
            # Collect post author data
            if post['author'] not in user_data:
                user_data[post['author']] = {
                    'posts': 0,
                    'total_score': 0,
                    'avg_upvote_ratio': []
                }
            
            user_data[post['author']]['posts'] += 1
            user_data[post['author']]['total_score'] += post['score']
            user_data[post['author']]['avg_upvote_ratio'].append(post['upvote_ratio'])
            
            # Collect comment author data
            for comment in post['comments']:
                if comment['author'] not in user_data:
                    user_data[comment['author']] = {
                        'comments': 0,
                        'comment_scores': []
                    }
                user_data[comment['author']]['comments'] = \
                    user_data[comment['author']].get('comments', 0) + 1
                user_data[comment['author']]['comment_scores'].append(comment.get('score', 0))
        
        # Create user segments
        segments = {
            'power_users': [],
            'regular_contributors': [],
            'occasional_participants': [],
            'lurkers': []
        }
        
        for user, data in user_data.items():
            total_activity = data.get('posts', 0) + data.get('comments', 0)
            avg_score = np.mean(data.get('comment_scores', [0]) + 
                              [data.get('total_score', 0)])
            
            if total_activity > 10 and avg_score > 100:
                segments['power_users'].append(user)
            elif total_activity > 5:
                segments['regular_contributors'].append(user)
            elif total_activity > 1:
                segments['occasional_participants'].append(user)
            else:
                segments['lurkers'].append(user)
                
        return segments

    def topic_modeling(self):
        """Perform basic topic modeling on posts"""
        # Combine title and selftext for analysis
        documents = [f"{post['title']} {post['selftext']}" for post in self.data]
        
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(documents)
        
        # Perform clustering
        num_clusters = min(len(documents), 3)  # Adjust based on data size
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        clusters = kmeans.fit_predict(tfidf_matrix)
        
        # Get top terms per cluster
        feature_names = vectorizer.get_feature_names_out()
        top_terms_per_cluster = []
        
        for cluster_idx in range(num_clusters):
            center = kmeans.cluster_centers_[cluster_idx]
            top_indices = center.argsort()[-5:][::-1]  # Get top 5 terms
            top_terms = [feature_names[i] for i in top_indices]
            top_terms_per_cluster.append(top_terms)
            
        return {
            'clusters': clusters,
            'top_terms_per_cluster': top_terms_per_cluster
        }

    def engagement_analysis(self):
        """Analyze user engagement patterns"""
        engagement_metrics = []
        
        for post in self.data:
            # Calculate time-based metrics
            created_time = datetime.fromisoformat(post['created_utc'].replace('Z', '+00:00'))
            
            # Calculate engagement rate
            engagement_rate = (post['num_comments'] + post['score']) / \
                            (1 + post['upvote_ratio'])  # Add 1 to avoid division by zero
            
            engagement_metrics.append({
                'post_id': post['id'],
                'time_of_day': created_time.hour,
                'engagement_rate': engagement_rate,
                'comments_to_score_ratio': post['num_comments'] / (post['score'] + 1),
                'controversy_score': 1 - post['upvote_ratio']
            })
            
        return engagement_metrics

    def generate_visualization(self):
        """Generate visualizations for the analysis"""
        # Example visualization: Engagement by time of day
        engagement_data = self.engagement_analysis()
        times = [d['time_of_day'] for d in engagement_data]
        engagement_rates = [d['engagement_rate'] for d in engagement_data]
        
        plt.figure(figsize=(10, 6))
        plt.scatter(times, engagement_rates)
        plt.xlabel('Hour of Day')
        plt.ylabel('Engagement Rate')
        plt.title('Post Engagement by Time of Day')
        
        return plt

def main():
    # Initialize analyzer
    analyzer = RedditAnalyzer(dummy_data)
    
    # Run various analyses
    print("Basic Statistics:")
    print(analyzer.basic_statistics())
    
    print("\nSentiment Analysis:")
    print(analyzer.sentiment_analysis())
    
    print("\nUser Segmentation:")
    print(analyzer.user_segmentation())
    
    print("\nTopic Modeling:")
    print(analyzer.topic_modeling())
    
    print("\nEngagement Analysis:")
    print(analyzer.engagement_analysis())
    
    # Generate and show visualization
    plt = analyzer.generate_visualization()
    plt.show()

if __name__ == "__main__":
    main()