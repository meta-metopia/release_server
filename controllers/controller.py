from pymongo import MongoClient
from pymongo.collection import Collection


class Controller:
    client: MongoClient
    collection: Collection

    def __init__(self, client: MongoClient):
        self.client = client
        self.db = self.client["kongshum-release"]
        self.collection: Collection = self.db["releases"]
