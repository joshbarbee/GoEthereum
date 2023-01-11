from memory import Memory
from heuristics.base_heuristic import BaseHeuristic
import pandas as pd


class Suicidal(BaseHeuristic):
    """
    Python implementation of the TxSpector Unintended Suicidal heuristic. Interfaces
    with memory to reduce on set on selfdestruct instrs. See self.analysis()
    """

    def __init__(self, memory: Memory, path: str) -> None:
        self.memory: Memory = memory
        self.selfdestruct: pd.DataFrame = None
        self.jumpi: pd.DataFrame = None
        self.caller: pd.DataFrame = None
        self.result: pd.DataFrame = None

        super().__init__(path)
        pass

    """
        First we collect all SELFDESTRUCT opcodes at d=1.We then get all CALLER opcodes 
        and JUMPI instructions at d=1. 
        
        Initially, we find the set of valid SELFDESTRUCTS:
        We compare such that the JUMPI occur after CALLER
        and the SELDESTRUCT occurs after JUMPI. Then, if 
        there is a dependency between CALLER and a JUMPI 
        instruction, the SELFDESTRUCT is valid

        We then filter the set of all selfdestructs by the set of invalid self destructs.
        All Suicidal contracts are those such that there is an invalid SELFDESTRUCT 

    """

    def analysis(self) -> None:
        self.selfdestruct = self.memory.find_instr_depth("SELFDESTRUCT", exact_depth=1)

        if self.selfdestruct is None:
            self.result = pd.DataFrame()
            return

        self.jumpi = self.memory.find_instr_depth("JUMPI", exact_depth=1)
        self.caller = self.memory.find_instr_depth("CALLER", exact_depth=1)

        min_caller = self.caller["loc"].min()

        self.jumpi = self.jumpi[self.jumpi["loc"] > min_caller]
        min_jumpi = self.jumpi["loc"].min()

        checked_selfdestructs = self.selfdestruct[self.selfdestruct["loc"] > min_jumpi]
        checked_selfdestructs = self.memory.reduce_instr(checked_selfdestructs, "JUMPI")

        self.result = pd.concat(
            [self.selfdestruct, checked_selfdestructs]
        ).drop_duplicates(keep=False)
