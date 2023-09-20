import sys
from os.path import abspath, dirname, join
sys.path.insert(0, join(dirname(abspath(__file__)), ".."))

import decompiler.mgofetcher as mgofetcher
import decompiler.analyzer.api as api
import decompiler.tac_cfg as tac_cfg
import operator

URI = "mongodb://127.0.0.1"
COLLECTION = "ethereum"
DATABASE = "ethlogger2"
TX_HASH = "0x37085f336b5d3e588e37674544678f8cb0fc092a6de5d83bd647e20e5232897b"

fetcher = mgofetcher.MongoFetcher(URI, DATABASE, COLLECTION)

tx = fetcher.get_tx(TX_HASH)

cfg = tac_cfg.TACGraph.from_trace(tx)
api = api.OpAnalyzer(cfg)

sload = api.get_ops("SLOAD", depth=(operator.gt, 2))
jumpi = api.get_ops("JUMPI")

sload.link_ops(jumpi, call_index=operator.eq, depth=operator.eq)
sload.reduce_descendant(self_def_var=True, link_def_var=False, link_use_vi=1)

sstore = api.get_ops("SSTORE")
sload.link_ops(sstore, depth=lambda x, y: x - 2 > y, op_index=operator.lt, save_links=True)
sload.reduce_value(operator.ne, self_def_var=False, self_use_vi = 0, link_def_var=False, link_use_vi=0)

sload.reduce_address()

sload.export("./examples/output/reentrancy.csv", cached_links=True)
