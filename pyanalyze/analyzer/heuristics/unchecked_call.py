from memory import Memory
from heuristics.base_heuristic import BaseHeuristic
import pandas as pd


class UncheckedCall(BaseHeuristic):
    """
    Python implementation of the TxSpector UncheckedCall vulnerability heuristic.
    """

    def __init__(self, memory: Memory, path: str) -> None:
        self.memory: Memory = memory
        self.call: pd.DataFrame = None

        self.result: pd.DataFrame = None

        super().__init__(path)
        pass

    """
        Goes through three different steps. First, we collect all call ops at d = 1. 
        If there is not a JUMPI with a condition var dependent on the return of the call, 
        we do not have a vuln. We then return the set of calls that did NOT have a 
        JUMPI dependency
    """

    def analysis(self) -> None:
        self.call = self.memory.find_instr_depth("CALL", exact_depth=1)

        if self.call is None:
            self.result = pd.DataFrame()
            return

        checked_calls = self.memory.reduce_instr(self.call, "JUMPI", cn_shift=-1)

        self.result = pd.concat([self.call, checked_calls]).drop_duplicates(keep=False)
