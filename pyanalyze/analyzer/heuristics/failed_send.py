from memory import Memory
from heuristics.base_heuristic import BaseHeuristic
import pandas as pd


class FailedSend(BaseHeuristic):
    """
    Python implementation of the TxSpector Failed-send vulnerability.
    """

    def __init__(self, memory: Memory, path: str) -> None:
        self.memory: Memory = memory
        self.revert: pd.DataFrame = None
        self.calls: pd.DataFrame = None
        self.jumpi: pd.DataFrame = None

        super().__init__(path)

    def analysis(self) -> None:
        """
        First we collect all REVERT opcodes. We then get all calls at depth=1
        where the value of call.v3 != 0x0 and the value of call.def == 0.

        Then, we get all JUMPI at d = 1 where JUMPI.loc > CALL.loc and
        REVERT.loc > JUMPI.loc. We then reduce on whether there is a dependency
        between a CALL and JUMPI instruction.
        """
        self.revert = self.memory.find_instr_depth("REVERT", exact_depth=1)
        self.calls = self.memory.find_instr_depth("CALL", exact_depth=1)
        self.jumpi = self.memory.find_instr_depth("JUMPI", exact_depth=1)

        if self.revert is None or self.calls is None or self.jumpi is None:
            self.result = pd.DataFrame()
            return

        self.memory.reduce_value(
            self.calls, "var3", comparator=0, invert=True, inplace=True
        )
        self.calls = self.calls[self.calls["value"] == 0]

        min_call = self.calls["loc"].min()
        max_revert = self.calls["loc"].max()

        self.jumpi = self.jumpi[self.jumpi["loc"] > min_call]
        self.jumpi = self.jumpi[self.jumpi["loc"] < max_revert]

        if len(self.jumpi) == 0:
            self.result = pd.DataFrame()
            return

        self.calls = self.memory.reduce_instr(self.calls, "JUMPI")

        self.result = self.calls
