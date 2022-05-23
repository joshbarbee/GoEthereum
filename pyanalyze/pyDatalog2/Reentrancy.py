from memory import Memory, Op
from pyDatalog import pyDatalog

pyDatalog.create_terms('X,Y')

class Reentrancy():
    def __init__(self, memory : Memory) -> None:
        self.memory = memory
        self.sload = None
        pass

    '''
        First step is to find all sload where the call depth is greater than 2
        and it must have the same call depth and call number as JUMPI
    '''
    def first_step(self) -> None:
        # first, get all sload where depth is greater than 2
        self.sload = self.memory.find_instr_depth("SLOAD", min_depth=3)

        # v1339 , for ex
        op = self.memory.ops[2397]

        # reduce set of sload to where JUMPI occurs in op
        self.sload = self.sload.conta
            

        
