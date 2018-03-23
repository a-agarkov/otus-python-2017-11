import datetime as dt
from pymongo import MongoClient

utcnow = dt.datetime.utcnow

CACHE_DB = 'Otus_HW4_score_cache'
SCORE_CACHE_COLLECTION = 'score_cache'
CID_INTERESTS_COLLECTION = 'cid_interests'


class CacheStore:
    client = MongoClient()

    def __init__(self, db, score_collection, cid_interests_collection):
        self.db = getattr(self.client, f'{db}')
        self.score_collection = getattr(self.db, f'{score_collection}')
        self.cid_interests_collection = getattr(self.db, f'{cid_interests_collection}')

        try:
            self.score_collection.create_index("expireAt", expireAfterSeconds=0)
        except:
            pass

    def cache_get(self, key=None, collection: str = None, target_value_name: str = None):
        """
        Get cached value. Reaches desired collection, tries to lookup for a document via provided key
        and returns certain value from that document.

        :param key: lookup key value;
        :param collection: 'score_collection', 'cid_interests_collection';
        :param target_value_name: 'score', 'interests';
        :return: Value or None.
        """
        try:
            return dict(getattr(self, f'{collection}').find_one({"_id": key}))[target_value_name]
        except Exception:
            return None

    def cache_set(self, key, value, expire_after_seconds=3600, collection: str = None, target_value_name: str = None):
        try:
            if expire_after_seconds:
                getattr(self, f'{collection}').insert_one({'_id': key,
                                                           "expireAt": utcnow() + dt.timedelta(0,
                                                                                               expire_after_seconds),
                                                           f'{target_value_name}': value})
            else:
                getattr(self, f'{collection}').insert_one({'_id': key, f'{target_value_name}': value})
        except:
            pass

    def get(self, key):
        return self.cache_get(key=key, collection='cid_interests_collection', target_value_name='interests')