import gc
from typing import Dict, List
import gc
from typing import Dict, List
import pandas as pd
import base_heuristic

from pyDatalog import pyDatalog

pyDatalog.create_terms('edge,can_reach,X,Y,Z')

'''
    Responsible for dealing with tracing variables, creating graphs between definitions of variables and usages
'''

class Variable(pyDatalog.Mixin):
    ''' init consists of all info from the def.facts file, not the use.facts file'''
    def __init__(self, opcode : str, loc : int, symbol : str, call_depth : int, call_num: int, value : int, is_use = False) -> None:
        self.def_loc = loc
        self.symbol = symbol

        self.call_depth = call_depth
        self.call_num = call_num
        self.is_use = False # true when variable is being used and no new variable is created

        super(Variable, self).__init__()

        self.value = value
        self.op = opcode

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Variable):
            return self.symbol == __o.symbol
        elif isinstance(__o, str):
            # we run into infinite stack recursion if we do not take care to compare select values
            return self.symbol == __o

        return False

    def __lt__(self, __o: object) -> bool:
        if not isinstance(__o, Variable):
            return NotImplemented
        else:
            return self.def_loc < __o.def_loc

    def __str__(self) -> str:
        return f"{self.symbol}: {{def: {self.def_loc}, op: {self.op}, value: {self.value}, depth: {self.call_depth}, index: {self.call_num}}}"

    def __hash__(self) -> int:
        return hash(self.symbol)

    def __bytes__(self)-> bytes:
        return str.encode(self.symbol)

    def __repr__(self) -> str:
        return self.symbol

'''
    Reads in branches of memory from the .tsv input files and then converts into graph representation (self.variables)
'''
class Memory():
    def __init__(self, path) -> None:
        self.def_facts = None
        self.use_facts = None
        self.op_facts = None
        self.value_facts = None

        self.path = path

        self.variables : Dict = {}

    '''
        Loads all operations and creates connections between variables. Must load ops first
    '''
    def load(self) -> None:
        self.__load_ops()
        self.__load_values()
        self.__load_variables()
        self.__load_use()

        # force early gc 
        del self.def_facts
        del self.use_facts
        del self.op_facts
        del self.value_facts

        gc.collect()

    ''' 
        loads in all ops from the op.facts file, then populates each use with the opcode when
        loc matches
    '''
    def __load_ops(self) -> None :
        self.op_facts =  pd.DataFrame(base_heuristic.read_tsv(self.path + "op.facts")).iloc[:,:3]
        self.op_facts.columns = ["Pc", 'Op', 'Loc']
        self.op_facts.astype({"Loc": "int32"})

    ''' 
        loads in all value information from the value.facts input file
    '''
    def __load_values(self) -> None:
        self.value_facts =  pd.DataFrame(base_heuristic.read_tsv(self.path + "value.facts")).iloc[:,:2]
        self.value_facts.columns = ["Var", "Value"]
        self.value_facts.Value.apply(int, base=16)

    ''' 
        creates a Variable instance for each row in the def.facts dataframe. Then assigns to dictionary 
        of variables based on symbol (V1992, V1133, etc.)
    '''
    def __load_variables(self) -> None:
        self.def_facts = pd.DataFrame(base_heuristic.read_tsv(self.path + "def.facts")).iloc[:,:5] 
        self.def_facts.columns = ["Var","Pc","Loc","Depth","CallNumber"]
        self.def_facts.astype({"Depth":"int32", "CallNumber": "int32", "Loc": "int32"})
        self.def_facts.Pc.apply(int, base=16)

        for _, row in self.def_facts.iterrows():
            # get the opcode name from op facts
            op = self.op_facts.loc[self.op_facts.Loc == row.Loc].iloc[0].Op

            # get the value associated with the variable from value facts
            value = self.value_facts[self.value_facts.Var == row.Var].iloc[0].Value

            var = Variable(op, row["Loc"], row["Var"], row["Depth"], row["CallNumber"], value)

            self.variables[var.symbol] = var
        
    '''
        Loads in all instances of a variable being used. When a variable is used, check whether 
        there is an existing .def for the same loc. If there is, we have a child
    '''
    def __load_use(self) -> None:
        self.use_facts = pd.DataFrame(base_heuristic.read_tsv(self.path + "use.facts")).iloc[:,:6] # 6 args in use.facts tsv
        self.use_facts.columns = ["Var","Pc","i","Loc","Depth","CallNumber"]    
        self.use_facts.astype({"Depth":"int32", "CallNumber": "int32", "Loc": "int32", "i": "int32"})
        self.use_facts.Pc.apply(int, base=16)

        for _, row in self.use_facts.iterrows():
            # get the loc, used var from the row
            loc = row['Loc']
            original_var = row['Var']

            # get the opcode name from op facts
            op = self.op_facts.loc[self.op_facts.Loc == row.Loc].iloc[0].Op

            # check if loc exists in def.facts
            df = self.def_facts[self.def_facts['Loc'] == loc]

            if len(df.index) > 0:
                new_var = self.variables[df.iloc[0]['Var']]

                +edge(self.variables[original_var], new_var)
            else:
                # we have an opcode that does not define a variable, but uses one
                # we do not need to save this in list of memory variables, but do need
                # to create edge for pyDatalog
                # IN FACT, we intentionaly do not add to list of variables, since will overwrite

                new_var = Variable(op, loc, original_var, row['Depth'], row['CallNumber'], 0, True)
                +edge(self.variables[original_var], new_var)            

                self.variables[original_var + f"|U:{loc}"] = new_var

    '''
        Checks if there is a connection between Var1 and Var2 
        where Var1 flows to Var2 eventually
    '''
    def is_connected(self, var1, var2) -> bool:

        can_reach(X,Y) <= can_reach(X,Z) & edge(Z,Y) & (X!=Y)
        can_reach(X,Y) <= edge(X,Y)

        v1 = self.variables[var1]

        v2 = self.variables[var2]

        v = (v2,) in can_reach(v1,Y)

        return True if v else False

    '''
        Finds all variables where the opcode of the defining variables
        matches instr
    '''
    def find_instr(self, instr : str) -> list:
        res = (Variable.op[Y] == instr)

        print(res)
        print(X)
