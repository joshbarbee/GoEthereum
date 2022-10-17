import argparse
import logging
import sys
from os.path import abspath, dirname, join
import time

import pandas as pd
from memory import Memory

# heuristics
from heuristics.reentrancy import Reentrancy
from heuristics.suicidal import Suicidal
from heuristics.unchecked_call import UncheckedCall
from heuristics.timestamp import Timestamp
from heuristics.failed_send import FailedSend
from heuristics.unsecured_balance import UnsecuredBalance

# Prepend .. to $PATH so the project modules can be imported below
src_path = join(dirname(abspath(__file__)), "..")
sys.path.insert(0, src_path)

# Version string to display with -v
VERSION = """\
+------------------------------+
|            v0.0.3            |
|                              |
+------------------------------+\
"""

def version():
    return VERSION


parser = argparse.ArgumentParser(
    description="Rules analyzer for Go Ethereum. Uses intermediate representation"
                "from modified Vandal implementation to conduct vulnerability analysis."
                "By default, all analysis are ran. Otherwise, the analysis to run can"
                "be specified in #TODO")

parser.add_argument("path",
                nargs="?",
                type=str,
                default=sys.stdin,
                help="path to facts folder consisting of the .fact files to read")

parser.add_argument("output",
                nargs="?",
                type=str,
                default=sys.stdin,
                help="path to name of new folder to write output of tx analysis to")    

args = parser.parse_args()

log_level = logging.INFO
logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

if args.path is None:
    sys.exit(1)

if args.output is None:
    sys.exit(1)

try:
    start = time.time()
    m = Memory(args.path)
    m.load()

    re = Reentrancy(m, args.output)
    re.analysis()
    re.output()

    uc = UncheckedCall(m, args.output)
    uc.analysis()
    uc.output()

    sc = Suicidal(m, args.output)
    sc.analysis()
    sc.output()

    ts = Timestamp(m, args.output)
    ts.analysis()
    ts.output()

    fs = FailedSend(m, args.output)
    fs.analysis()
    fs.output()

    ub = UnsecuredBalance(m, args.output)
    ub.analysis()
    ub.output()

    logging.info("Analysis finished")
    print(f"Elapsed time: {round(time.time()-start,2)} seconds")
# Catch a Control-C and exit with UNIX failure status 1
except KeyboardInterrupt:
    logging.critical("\nInterrupted by user")
    sys.exit(1)
