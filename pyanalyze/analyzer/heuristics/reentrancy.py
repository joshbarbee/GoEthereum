from memory import Memory
from pyDatalog import pyDatalog
from heuristics.base_heuristic import BaseHeuristic
import pandas as pd


class Reentrancy(BaseHeuristic):
    '''
        Reentrancy heuristic represented in Python as defined
        in TxSpector. 
    '''
    def __init__(self, memory : Memory, path : str) -> None:
        self.memory : Memory = memory
        self.sload : pd.DataFrame = None
        self.sstore : pd.DataFrame = None

        super().__init__(path)

    def analysis(self) -> None:
        self.first_step()

    def first_step(self) -> None:
        '''
            First step is to find all sload where the call depth is greater than 2
            and it must have the same call depth and call number as JUMPI
        '''
        # first, get all sload where depth is greater than 2
        self.sload = self.memory.find_instr_depth("SLOAD", min_depth=3)

        if (self.sload is None):
            self.result = pd.DataFrame()
            return

        # reduce on set of instructions that are linked to a JUMPI opcode
        self.sload = self.memory.reduce_instr(self.sload, "JUMPI")

        self.second_step()

    def second_step(self) -> None:
        '''
            Second step: find all sload instructions where the minimum depth is
            greater than the min sload depth by 1. Then, reduce to all sstore that
            occur after sload. Last, ensure that the value of sload equals the value
            of sstore
        '''

        depth = self.sload['depth'].min()
        self.sstore = self.memory.find_instr_depth("SSTORE", min_depth = depth - 1)

        # find the minimum location of any sloads, ensure that the min sstore occurs after
        min_loc = self.sload['loc'].min()
        self.sstore = self.sstore[self.sstore['loc'] > min_loc]

        self.memory.reduce_value(self.sload, 'var1', self.sstore, 'var1')

        self.third_step()


    def third_step(self) -> None:
        '''
        Reduce on any instructions where the execution address is different between 
        all sloads and sstores. Creates self.result output.
        '''
        self.memory.reduce_addr(self.sload, self.sstore)

        # then take all locs from the two addr_matches and val_matches cols of the 
        # self.sload dataframe. Find all matches between the two. If the length
        # equals 0, do not include the row in the final result
    
        def format(row) -> list:
            matches = []

            for i in row["addr_matches"]:
                if i in row["val_matches"]:
                    matches.append(i)

            return matches

        self.sload.loc[:,'sstores'] = self.sload.apply(lambda row: format(row), axis=1)
        self.sload = self.sload[self.sload['sstores'].astype(bool)]
        self.sload.drop(['val_matches','addr_matches'], axis=1, inplace=True)

        self.result = self.sload
        
