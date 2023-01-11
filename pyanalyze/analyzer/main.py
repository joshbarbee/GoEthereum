import argparse
import logging
import sys
from os.path import abspath, dirname, join
import time

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
    "be specified in #TODO"
)

parser.add_argument(
    "path",
    nargs="?",
    type=str,
    default=sys.stdin,
    help="path to facts folder consisting of the .fact files to read",
)

parser.add_argument(
    "output",
    nargs="?",
    type=str,
    default=sys.stdin,
    help="path to name of new folder to write output of tx analysis to",
)

parser.add_argument(
    "-a",
    "--all",
    action="store_false",
    help="To run every heuristic on the current .facts file",
)

parser.add_argument(
    "-re",
    "--reentrancy",
    action="store_false",
    help="To run the reentrancy heuristic on the current .facts file",
)

parser.add_argument(
    "-uc",
    "--unchecked-call",
    action="store_false",
    help="To run the unchecked-call heuristic on the current .facts file",
)

parser.add_argument(
    "-su",
    "--suicidal",
    action="store_false",
    help="To run the suicidal contract heuristic on the current .facts file",
)

parser.add_argument(
    "-ts",
    "--timestamp",
    action="store_false",
    help="To run the timestamp depedency heuristic on the current .facts file",
)

parser.add_argument(
    "-fs",
    "--failed-send",
    action="store_false",
    help="To run the failed-send heuristic on the current .facts file",
)

parser.add_argument(
    "-ub",
    "--unsecured-balance",
    action="store_false",
    help="Whether to run the unsecured balance heuristic on the current .facts file",
)

args = parser.parse_args()

log_level = logging.INFO
logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)

if args.path is None or args.output is None:
    sys.exit(1)

try:
    start = time.time()

    m = Memory(args.path)
    m.load()

    if args.all or args.reentrancy:
        re = Reentrancy(m, args.output)
        re.analysis()
        re.output()

    if args.all or args.unchecked_call:
        uc = UncheckedCall(m, args.output)
        uc.analysis()
        uc.output()

    if args.all or args.suicidal:
        sc = Suicidal(m, args.output)
        sc.analysis()
        sc.output()

    if args.all or args.timestamp:
        ts = Timestamp(m, args.output)
        ts.analysis()
        ts.output()

    if args.all or args.failed_send:
        fs = FailedSend(m, args.output)
        fs.analysis()
        fs.output()

    if args.all or args.unsecured_balance:
        ub = UnsecuredBalance(m, args.output)
        ub.analysis()
        ub.output()

    logging.info("Analysis finished")
    print(f"Elapsed time: {round(time.time()-start,2)} seconds")
# Catch a Control-C and exit with UNIX failure status 1
except KeyboardInterrupt:
    logging.critical("\nInterrupted by user")
    sys.exit(1)
