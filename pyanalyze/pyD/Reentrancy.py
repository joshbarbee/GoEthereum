from memory import Memory
from pyDatalog import pyDatalog
from base_heuristic import BaseHeuristic
import pandas as pd

pyDatalog.create_terms('X,Y,Z,W,A,B,op,can_reach,op_edge,subset_instr')

class Reentrancy(BaseHeuristic):
    def __init__(self, memory : Memory) -> None:
        self.memory : Memory = memory
        self.sload : pd.DataFrame = None
        self.sstore : pd.DataFrame = None
        pass

    '''
        First step is to find all sload where the call depth is greater than 2
        and it must have the same call depth and call number as JUMPI
    '''
    def first_step(self) -> None:
        # first, get all sload where depth is greater than 2
        self.sload = self.memory.find_instr_depth("SLOAD", min_depth=3)

        # reduce on set of instructions that are linked to a JUMPI opcode
        self.sload = self.memory.reduce_instr(self.sload, "JUMPI")


    '''
        Second step: find all sload instructions where the minimum depth is
        greater than the min sload depth by 1. Then, reduce to all sstore that
        occur after sload. Last, ensure that the value of sload equals the value
        of sstore
    '''
    def second_step(self) -> None:
        # get the minimum depth of all SLOAD instructions, then find all SSTOREs
        # at >= depth - 1
        depth = self.sload['depth'].min()

        self.sstore = self.memory.find_instr_depth("SSTORE", min_depth = depth - 1)

        # find the minimum location of any sloads, ensure that the min sstore occurs after
        min_loc = self.sload['loc'].min()
        self.sstore = self.sstore[self.sstore['loc'] > min_loc]

        # compare the value of all sloads and sstores, make sure that all sstores have
        # a sload that uses the same value. The loc of the sstore is appended to the sload df
        # first comparator is var1, since that is sstore_addr_var, and second is also var1
        # since that is sload_addr_var_val
        self.sstore = self.memory.reduce_value(self.sstore, self.sload, 'var1', 'var1')

        
    '''
        Third step: 
        
        1. Reduce on any instructions where the execution address is different between 
        all sloads and sstores. Result into sstore
    '''
    def third_step(self) -> None:
        self.sstore = self.memory.reduce_addr(self.sstore, self.sload)   

        super().output()         

        
