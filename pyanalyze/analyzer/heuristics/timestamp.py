from memory import Memory
from heuristics.base_heuristic import BaseHeuristic
import pandas as pd


class Timestamp(BaseHeuristic):
    """
    Python implementation of the TxSpector Timestamp-dependency vulnerability.
    """

    def __init__(self, memory: Memory, path: str) -> None:
        self.memory: Memory = memory
        self.timestamp: pd.DataFrame = None

        super().__init__(path)
        pass

    """
        First we collect all timestamp opcodes occuring at depth = 1.
        Then, we find whether a JUMPI opcode branches from the TIMESTAMP
        opcode at depth = 1. If this occurs, we have a TIMESTAMP dependency
    """

    def analysis(self) -> None:
        self.timestamp = self.memory.find_instr_depth("TIMESTAMP", exact_depth=1)

        if self.timestamp is None:
            self.result = pd.DataFrame()
            return

        self.result = self.memory.reduce_instr(self.timestamp, "JUMPI")
