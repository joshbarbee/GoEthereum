import gc
import gc
from typing import Dict, List, Union
import pandas as pd
import numpy as np
import base_heuristic

from pyDatalog import pyDatalog

pyDatalog.create_terms('edge,can_reach,origin,X,Y,Z,subset_depth,subset_instr,op_edge')

'''
    Responsible for dealing with tracing variables, creating graphs between definitions of variables and usages
'''

class Variable(pyDatalog.Mixin):
    '''
        op is not type annotated due to how Variables and Ops interact. Although op should
        be an Op object.
    '''
    def __init__(self, loc : int, symbol : str, opcode : str, value : int) -> None:
        self.symbol = symbol

        super(Variable, self).__init__()

        self.origin_op = opcode
        self.origin_value = value
        self.origin_loc = loc

        self.direct_uses = []
        self.def_vars = []

    def __repr__(self) -> str:
        return self.symbol

    '''
        __str__ is very finicky with pyDatalog. Be sure to avoid infinite recursion even
        when it seems that no recursion should be possible. Recommend just leaving self.symbol
        as __str__
    '''
    def __str__(self) -> str:
        return self.symbol

    def __lt__(self, __o) -> bool:
        if type(__o) != Variable:
            raise NotImplemented
        
        if self.origin_loc < __o.origin_loc:
            return False
        
        return True

    def __hash__(self) -> int:
        return hash(self.symbol)

    def add_use(self, var) -> None:
        self.direct_uses.append(var)

    def add_def(self, var : Union[List, 'Variable']) -> None:
        if type(var) == List: 
            self.direct_uses.extend(var)
        elif type(var) == Variable:
            self.direct_uses.append(var)
        else:
            raise NotImplemented

class Op(pyDatalog.Mixin):
    ''' init consists of all info from the def.facts file, not the use.facts file'''
    def __init__(self, opcode : str, pc : int, loc : int, call_num : int, depth : int, value : int, use_variables: List[str] = [], def_variables: List[Variable] = [], memory = None) -> None:
        self.loc = loc
        self.op = opcode
        self.pc = pc
       
        self.use_vars = use_variables
        self.def_vars = def_variables

        self.call_num = call_num
        self.depth = depth
        self.value = value

        self.memory = memory
        super(Op, self).__init__()

    '''
        Whether an opcode contains another linked opcode that matches
        a certain instruction.

        Links are defined by def-use relationships. Any use will be linked
        to the def opcode
    '''
    def contains_instr(self, instr : str) -> bool:
        # from the variable, find all subchildren of the variable. Return
        # true if any children that match instruction is found

        can_reach(X,Y) <= can_reach(X,Z) & op_edge(Z,Y) & (X!=Y)
        can_reach(X,Y) <= op_edge(X,Y)

        # first get all children of the variable
        res = can_reach(self.loc,Y)

        # iterate over all children variables in res, getting origin opcode
        # from opcode dict
        for loc_tuple in res:
            loc = loc_tuple[0]
            child_op = self.memory.ops[loc]

            if child_op == instr:
                return True

        return False

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Variable):
            return self.loc == __o.loc and self.op == __o.op
        return False

    def __lt__(self, __o: object) -> bool:
        if not isinstance(__o, Variable):
            return NotImplemented
        else:
            return self.loc < __o.loc

    def __str__(self) -> str:
        return f"{self.loc}:{self.op}"

    def __hash__(self) -> int:
        return hash(self.loc)

    def __bytes__(self)-> bytes:
        return str.encode(self.symbol)

    def __repr__(self) -> str:
        return f"Op{{0x{hex(id(self))}}}: {self.loc}:{self.op}"

'''
    Reads in branches of memory from the .tsv input files and then converts into graph representation (self.variables)
'''
class Memory():
    def __init__(self, path) -> None:
        self.facts = None

        self.path : str = path

        self.variables : Dict = {}
        self.ops : Dict = {} # dict consisting of mapping between opcode and all opcodes of that type
        self.max_depth : int = 0

    '''
        Loads all operations and creates connections between variables. Must load ops first
    '''
    def load(self) -> None:
        self.__load_facts()

        # force early gc 
        del self.facts

        gc.collect()

    '''
        Loads in all related .facts info from the opAll.facts file. From this, we create
        a graph depicting the relationships between variables and how those variables are used
    '''
    def __load_facts(self) -> None:
        self.facts = pd.read_csv(self.path + 'opAll.facts', sep="\t", header=None, names=["loc","pc","op","depth","call_index","value","def","#uses","var1","var2"])

        for _, row in self.facts.iterrows():
            op : str = row['op']
            pc : int = row['pc']
            loc : int = row['loc']
            depth : int= row['depth']
            index : int = row['call_index']
            value : int = int(row['value']) if not pd.isna(row['value']) else None

            def_var = None

            if depth > self.max_depth:
                self.max_depth = depth

            if loc < 2408 and loc > 2396:
                a=3
                pass

            if not pd.isna(row["def"]):
                def_var = Variable(loc, row['def'], op, value)
                self.variables[def_var.symbol] = def_var
                
            uses = []

            if not pd.isna(row["var1"]):
                use_var = row["var1"]
                uses.append(use_var)

                if def_var != None:
                    +edge(use_var, def_var.symbol)

                parent = self.variables[use_var]
                +op_edge(parent.origin_loc, loc)

            if not pd.isna(row["var2"]):
                use_var = row["var2"]
                uses.append(use_var)

                if def_var != None:
                    +edge(use_var, def_var.symbol)

                parent = self.variables[use_var]
                +op_edge(parent.origin_loc, loc)
               
            new_op = Op(op, pc, loc, index, depth, value, uses, [def_var])
            
            if def_var != None:
                +origin(new_op, def_var)

            '''if op not in self.ops:
                self.ops[loc] = [new_op]
            else:
                self.ops[loc].append(new_op)'''

            self.ops[loc] = new_op

    '''
        Checks if there is a connection between Var1 and Var2 
        where Var1 flows to Var2 eventually
    '''
    def is_connected(self, var1 : Variable, var2 : Variable) -> bool:
        can_reach(X,Y) <= can_reach(X,Z) & edge(Z,Y) & (X!=Y)
        can_reach(X,Y) <= edge(X,Y)

        res = can_reach(var1,Y)

        return True if (var2,) in res else False

    '''
        Finds all variables where the opcode of the defining variables
        matches the provided instruction. Returns a list of all instructions
    '''
    def find_instr(self, instr : str) -> list:
        ops = Op.op[Y] == instr

        # this is used elsewhere in the program. It is a quick way to convert a 
        # pyDatalog query into a list
        res = [i[0] for i in ops]
        return res

    '''
        Finds all variables matching certain an instruction and three depth parameters, 
        inclusively. Returns a list consisting of found variables
         1. the instruction to match with 
         2. (optional) the exact depth to find all instructions at
         3. (optional) the minimum depth to find instructions at
         4. (optional) the maximum depth where an instruction can be found

        TODO: Find out if it is faster to find all ops first and then check depth, or 
        check all depths first and then find ops
    '''
    def find_instr_depth(self, instr, exact_depth : int = None, min_depth : int = None, max_depth : int = None) -> pyDatalog.pyParser.Query:
        if exact_depth == None and min_depth == None and max_depth == None:
            return self.find_instr(instr)

        if exact_depth != None:
            min_depth = exact_depth
            max_depth = exact_depth
        else:
            max_depth = self.max_depth if max_depth == None else max_depth
            min_depth = 0 if min_depth == None else min_depth

        subset_depth(X) <= (Op.depth[X] < max_depth + 1) <= (Op.depth[X] >= min_depth) <= (Op.op[X] == instr)

        return subset_depth(X)