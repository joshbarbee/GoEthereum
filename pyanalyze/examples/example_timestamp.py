import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(abspath(__file__)), ".."))

import decompiler.mgofetcher as mgofetcher
import decompiler.analyzer.api as api
import operator

URI = "mongodb://127.0.0.1"
COLLECTION = "ethereum"
DATABASE = "ethlogger2"
TX_HASH = "0x37085f336b5d3e588e37674544678f8cb0fc092a6de5d83bd647e20e5232897b"

fetcher = mgofetcher.MongoFetcher(URI, DATABASE, COLLECTION)

tx = fetcher.get_tx(TX_HASH)

api = api.OpAnalyzer.load_from_mongo(tx)

# step 1 - get all timestamps
timestamp = api.get_ops("TIMESTAMP", depth=(operator.eq, 1))
jumpi = api.get_ops("JUMPI", depth=(operator.eq, 1))

timestamp.link_ops(jumpi, op_index=operator.lt)
timestamp.reduce_descendant(self_def_var=True, link_def_var=False, link_use_vi=1)

timestamp.export("./examples/output/timestamp.csv")
