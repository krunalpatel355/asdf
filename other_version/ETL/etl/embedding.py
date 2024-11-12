import numpy as np
import requests
from typing import List, Dict
from config.settings import Config
from utils.connections import ConnectionManager
import pymongo

class VectorSearch:
    def __init__(self):
        self.client = ConnectionManager.get_mongodb_connection()
        self.db = self.client['reddit_db']
        self.collection = self.db['subreddits']
        self._ensure_indexes()

    def _ensure_indexes(self):
        self.collection.create_index([("embedding", pymongo.ASCENDING)])

    def _generate_embedding(self, text: str) -> List[float]:
        response = requests.post(
            Config.EMBEDDING_URL,
            headers={"Authorization": f"Bearer {Config.HF_TOKEN}"},
            json={"inputs": text}
        )
        if response.status_code != 200:
            raise ValueError(f"Request failed: {response.text}")
        return response.json()

    def initialize_subreddits(self) -> None:
        if self.collection.count_documents({}) == 0:
            self._load_subreddits()

    def _load_subreddits(self) -> None:
        documents = []
        with open(Config.SUBREDDITS_FILE, 'r') as file:
            for line in file:
                name, subscribers = line.strip().split('\t')
                embedding = self._generate_embedding(name)
                documents.append({
                    "subreddit": name,
                    "subscribers": int(subscribers),
                    "embedding": embedding
                })
                if len(documents) >= 100:
                    self.collection.insert_many(documents)
                    documents = []
        if documents:
            self.collection.insert_many(documents)

    def find_similar_subreddits(self, query: str, limit: int = 10) -> List[Dict]:
        query_embedding = self._generate_embedding(query)
        results = []
        
        for doc in self.collection.find():
            similarity = np.dot(query_embedding, doc["embedding"]) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc["embedding"])
            )
            results.append((similarity, doc))
        
        return [doc for _, doc in sorted(results, reverse=True)[:limit]]
