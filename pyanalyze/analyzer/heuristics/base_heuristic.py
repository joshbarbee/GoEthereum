import os
import pandas as pd
from pathlib import Path
import os

class BaseHeuristic:
    def __init__(self, path) -> None:
        self.path = path
        pass

    def output(self) -> None:
        if self.result is not None and isinstance(self.result, pd.DataFrame):
            Path(self.path).mkdir(parents=False, exist_ok=True)

            title = type(self).__name__
            
            self.result.to_csv(f"{self.path}/{title}.csv", sep='\t', na_rep="", index=False)
            return

        variables = vars(self)
        for k,v in variables.items():
            if type(v) == pd.DataFrame:
                print(f"{k}:\n{v}")


