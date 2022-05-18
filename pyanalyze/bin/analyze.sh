#!/bin/bash
if [ "$#" -ne 1 ]; then
    echo "Usage: analyze.sh datalog_file"
    exit
fi
set -x
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
rm -rf facts-tmp
python3.6 $DIR/decompile -o --tsv=./facts-tmp --opcodes CREATE BALANCE CALLER CALLVALUE STOP RETURN REVERT ORIGIN CALLDATALOAD EQ TIMESTAMP NUMBER DIFFICULTY COINBASE BLOCKHASH GASLIMIT EXTCODESIZE SELFDESTRUCT JUMPI JUMP JUMPDEST SSTORE SLOAD CALL DELEGATE CALLCODE STATICCALL -n

../../souffle/build/bin/souffle -s python -F facts-tmp $1