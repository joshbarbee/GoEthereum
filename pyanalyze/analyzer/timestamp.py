from base_heuristic import BaseHeuristic
import pandas as pd

'''
    Class defining the heuristics for a timestamp-based attack,
    as defined in TxSpector
'''
class Timestamp(BaseHeuristic):
    def __init__(self, memory, facts_dir="./") -> None:
        super().__init__(memory, facts_dir)

        self.timestamp = super().load_instr("TIMESTAMP")
        self.jumpi = super().load_instr("JUMPI")

    '''
        This runs Step2 from the TimestampDependance datalog file. Since step 1 is
        just loading in each timestamp op, we only need one step
    '''
    def analysis(self):
        return self.Step2()
    
    '''
        Step 2: 
        1. Get all JUMPI where JUMPI_LOC > TIMESTAMP_LOC
        2. Check if there is a data dependency between TIMESTAMP -> JUMPI
        3. ???
    '''
    def Step2(self) -> pd.DataFrame:
        # keep all JUMPI where JUMPI after timestamp
        safe_jumpi = []
        safe_timestamp = []

        for _, row in self.jumpi.iterrows():
            possible_timestamp = self.timestamp[self.timestamp['loc'] < row['loc']]
            
            if len(possible_timestamp) == 0:
                pass
            else:
                for _, i in self.possible_timestamp.iterrows():
                    # must check if timestamp flows into JUMPI, since we cannot traverse 
                    # up trees
                    if self.memory.is_connected(row, i.v2):
                        insert_jumpi = any([row.equals(j) for j in safe_jumpi])

                        if not insert_jumpi:
                            safe_jumpi.append(row)
                        
                        insert_timestamp = any([i.equals(j) for j in safe_timestamp])

                        if not insert_timestamp:
                            safe_jumpi.append(i)

        return tuple(pd.DataFrame(safe_jumpi), pd.DataFrame(safe_timestamp))