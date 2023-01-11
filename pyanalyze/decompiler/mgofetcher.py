from typing import Iterable
from pymongo import MongoClient, CursorType

"""
    Class to interface with mongodb to extract tx info based on 
    block number
"""


class MongoFetcher:
    def __init__(self, mongoURI: str, db: str, collection: str) -> None:
        self.client = MongoClient(mongoURI)
        self.database = getattr(self.client, db)
        self.collection = getattr(self.database, collection)

        self.block: int = 1

    """
        Gets all transactions in the mongodb at a certain index 
        N is an optional argument that ifnot specified, we will read
        in the next block 
    """

    def get_block(self, n: int = None) -> None:
        if n == None:
            n = self.block

        txs = self.collection.find({"block": str(n)})

        self.block = n + 1

        return txs

    def get_tx(self, tx: str = "") -> Iterable[CursorType]:
        if tx == "":
            return list(self.collection.aggregate([{"$sample": {"size": 1}}]))[0]
        return self.collection.find_one({"tx": tx})
