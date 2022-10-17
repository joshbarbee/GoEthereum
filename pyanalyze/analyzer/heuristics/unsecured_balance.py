from memory import Memory
from heuristics.base_heuristic import BaseHeuristic
import pandas as pd

class UnsecuredBalance(BaseHeuristic):
    '''
        Python implementation of the TxSpector UnsecuredBalance vulnerability heuristic.
    '''
    def __init__(self, memory : Memory, path : str) -> None:
        self.memory : Memory = memory
        self.call : pd.DataFrame = None
        self.calldataload : pd.DataFrame = None
        self.callvalue : pd.DataFrame = None

        self.result : pd.DataFrame = None

        super().__init__(path)
        pass

    '''
        First, we get all CALL and CALLDATALOAD ops at depth = 1. We then reduce the set 
        of calls to those where calldataload.var2 depends on calls.var2. Then, call.var3 != 0,
        We then determine whether a CALLVALUE opcode was used to create calls.var3.

        Then, from this set of correct calls, we subtract the set of CALLS that were 
        properly checked in the first step. This is our set of unsecured balances.
    '''
    def analysis(self) -> None:
        self.call = self.memory.find_instr_depth("CALL", exact_depth=1)
        self.calldataload = self.memory.find_instr_depth("CALLDATALOAD", exact_depth=1)
        self.callvalue = self.memory.find_instr_depth("CALLVALUE", exact_depth=1)

        if self.call is None or self.calldataload is None:
            self.result = pd.DataFrame()
            return
        
        self.calldataload = self.memory.reduce_instr(self.calldataload, instr="CALL")

        checked_calls = self.memory.reduce_value(self.call, "var3", comparator = 0, invert=True, inplace=False)
        checked_calls = self.memory.reduce_origin(checked_calls, "var3", invert=True, inplace=False)

        self.result = pd.concat([self.call,checked_calls]).drop_duplicates(keep=False)

        if len(self.result) == 0:
            self.result = pd.DataFrame()