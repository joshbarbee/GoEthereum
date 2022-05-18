from more_itertools import first
from memory import Memory
from base_heuristic import BaseHeuristic
import pandas as pd

'''
    Class defining heuristics for the reentrancy attack first defined in
    TxSpector.
'''
class Reentrant(BaseHeuristic):
    def __init__(self, path, memory) -> None:
        super().__init__(path, memory)

        # four dependencies are all calls, sstore, sload, jumpi
        self.calls = super().load_calls()
        self.sstore = super().load_instr("SSTORE")
        self.sload = super().load_instr("SLOAD")
        self.jumpi = super().load_instr("JUMPI")

    def analysis(self) -> None:
        first_step_res = self.first_step()
        second_step_res = self.second_step(first_step_res)
        third_step_res = self.third_step(second_step_res)
        
        print(third_step_res)

    '''
        First step is to find all sload where the call depth is greater than 2
        and it must have the same call depth and call number as JUMPI
    '''
    def step1(self) -> pd.DataFrame:
        res = []

        # depth is stored at v4 for sload
        self.sload = self.sload[self.sload.v4 > 2]

        # for each sload, check if there exists a JUMPI instruction in its trace
        for _, row in self.sload.iterrows():
            sload_var = row.v2

            uses = self.memory.get_uses(sload_var)

            if len(uses) > 0:
                for use in uses:
                    var, _, op, cn, d = use

                    if d != row.v4 and cn != row.v5:
                        continue

                    if op != "JUMPI" and not self.memory.is_connected(sload_var, var):
                        continue

                    insert_sload = any([row.equals(j) for j in res])
                    if not insert_sload:
                        res.append(row)

                    break

        return pd.DataFrame(res)

    '''
        Second step: collect all sstore ops. Sstore call depth must be less than
        sload call depth 
    '''
    def step2(self, first_step : pd.DataFrame) -> pd.DataFrame: 
        res = []
        valid_sloads = []

        # check each SLOAD in first step, make sure that sload >= sstore_depth + 1
        # that sstore_loc > sload_loc, shared values, etc
        for _, row in self.sstore.iterrows():
            sstore_depth = row.v4

            possible_sloads = first_step.copy()

            # location check with any remaining sload. Sload -> sstore
            possible_sloads = possible_sloads[possible_sloads['loc'] < row['loc']]

            # depth check with any sload
            possible_sloads = possible_sloads[possible_sloads.v4 >= sstore_depth + 1]  
           
            # check that sstore and sload variable values are the same
            sstore_val = self.memory.get_variable(row['v2']).value
            
            for _, i in possible_sloads.iterrows():
                sload_val = self.memory.get_variable(i['v2']).value

                if sload_val == sstore_val:
                    insert_sload = any([i.equals(j) for j in valid_sloads])

                    if not insert_sload:
                        valid_sloads.append(i)

                    insert_sstore = any([row.equals(j) for j in res])

                    if not insert_sstore:
                        res.append(row)
                    break
        
        self.sload = pd.DataFrame(valid_sloads)
        self.sstore = pd.DataFrame(res)

        return pd.DataFrame(res)

    '''
        Third step, check that the following conditions are met:
        pre: get the sc_addr - the source address of the contract being executed on
        1. when sstore_depth != 1, get the Call op where addr=sc_addr, 
        depth = sstore depth - 1.
        2. Check that the call number of the call is >= than the call number of sstore
        3. Get calls for sload where sstore_sc_addr, depth = sload_depth - 1)
            check that the call number is >= sload call number
        4. check sstore_sc_addr = sload_sc_addr???
    '''
    def step3(self, second_step : pd.DataFrame = None) -> pd.DataFrame:
        # second step is now sstore 
        if second_step != None:
            second_step = self.sstore
        
        # get the sc_addr from facts file
        sc_addr = super().load_instr("sc_addr.facts")['loc']

        # 1st condition / 2nd condition
        for _, row in second_step.iterrows():
            potential_calls = self.calls.copy()

            potential_calls = potential_calls[potential_calls]



        
    

    