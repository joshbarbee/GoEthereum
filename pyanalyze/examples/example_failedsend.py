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

# get revert, call
revert = api.get_ops("REVERT", depth=(operator.eq, 1))
call = api.get_ops("CALL", depth=(operator.eq, 1))
jumpi = api.get_ops("JUMPI", depth=(operator.eq, 1))

# step 2, get call where use_vi[0] (value var) is not 0 and def var is 0
call.filter_value(0, operator.ne, def_var=False, use_vi=2)
call.filter_value(0, operator.eq, def_var=True)

# step 3 - get call where jumpi occurs before revert and after call
# and jumpi depends on call
jumpi.link_ops(revert, op_index=operator.lt)
jumpi.link_ops(call, op_index=operator.gt)
jumpi.reduce_ancestor(self_def_var=False, self_use_vi=1, link_def_var=True)

jumpi.export("./examples/output/failed_send.csv")
