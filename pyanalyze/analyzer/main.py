import argparse
import logging
import sys
from os.path import abspath, dirname, join
import pandas as pd
from memory import Memory
from reentrancy import Reentrant
from timestamp import Timestamp

# Prepend .. to $PATH so the project modules can be imported below
src_path = join(dirname(abspath(__file__)), "..")
sys.path.insert(0, src_path)

# Version string to display with -v
VERSION = """\
+------------------------------+
|                       v0.0.1 |
|                              |
+------------------------------+\
"""

def version():
    return VERSION


parser = argparse.ArgumentParser(
    description="Rules analyzer for Go Ethereum. Uses intermediate representation"
                "from modified Vandal implementation to conduct vulnerability analysis")

parser.add_argument("path",
                nargs="?",
                type=str,
                default=sys.stdin,
                help="path to facts folder consisting of the .fact files to read")
         
args = parser.parse_args()

log_level = logging.WARNING
logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

if args.path is None:
    sys.exit(1)

try:
    m = Memory(args.path)
    m.load()

    #re = Reentrant(m, args.path)
    #step1 = re.first_step()
    #step2 = re.second_step(step1)

    t = Timestamp(m, args.path)
    t.analysis()

    logging.info("Analysis finished")
# Catch a Control-C and exit with UNIX failure status 1
except KeyboardInterrupt:
    logging.critical("\nInterrupted by user")
    sys.exit(1)
