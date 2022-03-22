from pymongo import MongoClient
from consts import MONGOURI
from eventtrace_test import test_eventtraces
from optrace_test import test_optraces, test_txinblock
from functrace_test import test_functraces

client = MongoClient(MONGOURI)
db = client.ethereum

if __name__ == "__main__":
    #test_functraces(db, 5)
    #test_optraces(db, 5)
    #test_eventtraces(db, 5)

    #test_txinblock(db, 5)