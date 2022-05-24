import os
import pandas as pd

class BaseHeuristic:
    def __init__(self) -> None:
        pass

    def output(self) -> None:
        variables = vars(self)
        for k,v in variables.items():
            if type(v) == pd.DataFrame:
                print(f"{k}:\n{v}")


