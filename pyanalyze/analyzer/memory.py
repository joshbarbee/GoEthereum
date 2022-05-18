import gc
from typing import Dict, List
from numpy import var
import pandas as pd
import base_heuristic

'''
    Responsible for dealing with tracing variables, creating graphs between definitions of variables and usages
'''

class Variable():
    ''' init consists of all info from the def.facts file, not the use.facts file'''
    def __init__(self, opcode : str, loc : int, symbol : str, call_depth : int, call_num: int, value : int) -> None:
        self.def_loc = loc
        self.symbol = symbol
        self.op = opcode
        self.call_depth = call_depth
        self.call_num = call_num
        self.value = value

        self.uses =[] 
        self.children = []

    ''' adds a new Variable child to the current parent'''
    def add_child(self, child):
        self.children.append(child)

    ''' sets the operation name that defined the var'''
    def set_op(self, op):
        self.op = op

    ''' contains all instances where a variable is used'''
    def add_use(self, var, loc, op, callnumber, calldepth):
        self.uses.append((var, loc, op, callnumber, calldepth))

    ''' returns all uses from the current object, as well as any child'''
    def get_uses(self):
        res = self.uses

        for child in self.children:
            res += child.get_uses()

        return res

    ''' 
        checks itself if the node is the current one being searched for, then each child
        returns true if the searched-for node is in the tree of nodes, false otherwise
    '''
    def is_connected(self, node):
        if self == node:
            return True

        for child in self.children:
            if child == node:
                return True
            else: return False | child.is_connected(node)

        return False

    ''' returns a list consisting of all children where the instruction matches'''
    def get_children_instr(self, instr : str):
        res = []

        for child in self.children:
            if child.op == instr:
                res += child

            res += child.get_children_instr(instr)

        return res

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Variable):
            return self == __o
        elif isinstance(__o, str):
            return self.symbol == __o

        return False

    def __str__(self) -> str:
        child_str = ""

        for child in self.children:
            child_str += child.symbol + ","   

        uses_str = str(self.get_uses())         

        return f"Opcode: {self.op}, Var: {self.symbol}, Loc: {self.def_loc}, Depth: {self.call_depth}, CN: {self.call_num}, Children: {child_str}, Uses: {uses_str}"

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
                self.variables[original_var].add_child(new_var)
            else:
                self.variables[original_var].add_use(original_var, loc, op, row['CallNumber'], row["Depth"])
    ''' 
        writes a representation of the connected nodes of a variable to stdout. Goes down
        every child until no more child is found, using BFS
    '''
    def output_variable(self, start_node : str) -> None:
        node = self.variables[start_node]

        visited = []
        queue = []

        if node == None:
            return
    
        visited.append(node)
        queue.append(node)

        while (queue):
            top = queue.pop(0)

            print(top)

            for i in top.children:
                if i not in visited:
                    visited.append(i)
                    queue.append(i)
        
    def get_variable(self, var : str) -> Variable:
        if var in self.variables:
            return self.variables[var]
        else: return None
        
    ''' gets all children of a current instruction matching the specified operand in instr'''
    def get_children_instr(self, var : str, instr : str) -> List[Variable]:
        if instr == "":
            return []
        
        return self.variables[var].get_children_instr(instr)

    def get_uses(self, var : str) -> List[tuple]:
        return self.variables[var].get_uses()

    '''
        Checks if there is a connection between Var1 and Var2 
        where Var1 flows to Var2 eventually
    '''
    def is_connected(self, var1, var2) -> bool:
        return self.variables[var1].is_connected(var2)