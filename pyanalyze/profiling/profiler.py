import sys
from os.path import abspath, dirname, join
import tracemalloc
import timeit

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

def tracing_start():
    tracemalloc.stop()
    tracemalloc.start()

def tracing_mem():
    first_size, first_peak = tracemalloc.get_traced_memory()
    return first_peak/(1024*1024)

def run_reentrancy(tests):
    mem_avgs = []
    time_avgs = []

    for i, tx in enumerate(fetcher.get_random_txs(tests)):
        print("On iteration ", i)

        cfg = tac_cfg.TACGraph.from_trace(tx)
        tracing_start()
        start_time = timeit.default_timer()
        _api = api.OpAnalyzer(cfg)

        # zeroth step - get opcodes
        sload = _api.get_ops("SLOAD", depth=(operator.gt, 2))
        jumpi = _api.get_ops("JUMPI")

        sload.link_ops(jumpi, call_index=operator.eq, depth=operator.eq)
        sload.reduce_descendant(self_def_var=True, link_def_var=False, link_use_vi=1)

        sstore = _api.get_ops("SSTORE")
        sload.link_ops(sstore, depth=lambda x, y: x - 2 > y, op_index=operator.lt, save_links=True)
        sload.reduce_value(operator.ne, self_def_var=False, self_use_vi = 0, link_def_var=False, link_use_vi=0)
        sload.reduce_address()

        mem_avgs.append(tracing_mem())
        time_avgs.append(timeit.default_timer() - start_time)


    return (sum(mem_avgs) / tests, sum(time_avgs) / tests)

tests = int(sys.argv[1])

reentrancy_results = run_reentrancy(tests)

print(f"Reentrancy Average ({tests}): Memory: {reentrancy_results[0]} MB Time: {reentrancy_results[1]:.3f}s")