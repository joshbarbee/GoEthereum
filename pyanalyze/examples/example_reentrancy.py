import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import decompiler.mgofetcher as mgofetcher
import decompiler.analyzer.api as api
import operator

URI = "mongodb://127.0.0.1"
COLLECTION = "ethereum"
DATABASE = "ethlogger2"
TX_HASH = "0x37085f336b5d3e588e37674544678f8cb0fc092a6de5d83bd647e20e5232897b"

fetcher = mgofetcher.MongoFetcher(URI, DATABASE, COLLECTION)

tx = fetcher.get_tx(TX_HASH)

api = api.OpAnalyzer.load_from_dump(tx)

# zeroth step - get opcodes
sload = api.get_ops("SLOAD", depth=(operator.gt, 2))
jumpi = api.get_ops("JUMPI")
sstore = api.get_ops("SSTORE")
sload.link_ops(jumpi, call_index=operator.eq, depth=operator.eq)

# first step - check sload, w call index > 2, and same call depth, call number as jumpi
# which depends on sload
sload.reduce_descendant(self_def_var=True, link_def_var=False, link_use_vi=1)

# second step - get sstore less than sload call depth, with same addr_var_value
sload.link_ops(sstore, depth=lambda x, y: x - 2 > y, op_index=operator.lt, save_links=True)
sload.reduce_value(self_def_var=False, self_use_vi = 0, link_def_var=False, link_use_vi=0)

# third step - make sure sload and sstore and from same contract
sload.reduce_address()

sload.export_links("./output/reentrancy.csv", cached_links=True)
