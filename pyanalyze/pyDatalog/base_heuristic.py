import os
import pandas as pd

read_tsv = lambda path : pd.read_csv(path, sep="\t", header=None, names=["pc","v1","v2","v3","v4","v5","v6","v7","v8","v9","v10","v11"])

class BaseHeuristic:
    def __init__(self, memory, facts_dir = "./") -> None:
        self.facts_dir = facts_dir
        self.memory = memory
        return

    '''
        Loads all call operators, then merges into one dataframe
    '''
    def load_calls(self) -> pd.DataFrame:
        call = self.__format_df("CALL")
        static = self.__format_df("STATICCALL")
        delegate = self.__format_df("DELEGATECALL")
        callcode = self.__format_df("CALLCODE")

        df = pd.concat([call,static,delegate,callcode], axis=0)

        return df.sort_values(by=["loc"]).reset_index()

    def load_instr(self, instr : str = "") -> pd.DataFrame:
        if instr == "":
            return None
    
        return self.__format_df(instr)

    def __format_df(self, instr : str) -> pd.DataFrame:
        df = read_tsv(self.facts_dir + f"op_{instr}.facts")
        df = df.dropna(axis=1)
        df = df.rename(columns={df.columns[-1]:"call_number", df.columns[-2]:"depth", df.columns[-3]:"loc"})
        
        return df.assign(op=instr)

