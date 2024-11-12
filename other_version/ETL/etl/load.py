from typing import Dict
import pymongo

class MongoLoader:
    def __init__(self, collection):
        self.collection = collection
        self._ensure_indexes()

    def _ensure_indexes(self):
        indexes = [
            ('id', pymongo.ASCENDING),
            ('subreddit', pymongo.ASCENDING),
            ('created_utc', pymongo.ASCENDING)
        ]
        for field, direction in indexes:
            self.collection.create_index(
                [(field, direction)],
                unique=(field == 'id')
            )

    def load_post(self, post_data: Dict) -> bool:
        try:
            self.collection.update_one(
                {'id': post_data['id']},
                {'$set': post_data},
                upsert=True
            )
            return True
        except pymongo.errors.DuplicateKeyError:
            return False
        except Exception as e:
            print(f"Error loading post: {e}")
            return False