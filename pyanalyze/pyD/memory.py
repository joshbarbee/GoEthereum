from typing import Dict, List
import pandas as pd
import numpy as np
from pyDatalog import pyDatalog

pyDatalog.create_terms('edge,can_reach,value,addr,W,X,Y,Z')

class Memory():
    '''
    Reads in .facts files and converts into intermediate representation, conducting data analysis
    using Pandas and pyDatalog
    '''
    def __init__(self, path) -> None:
        self.path : str = path

        self.ops : Dict[str, pd.DataFrame] = {} # dict of mapping between opcode and pandas dataframe of opcode
        self.ops_df : pd.DataFrame = None
        self.max_depth : int = 0

    def load(self) -> None:
        '''
        Loads all operations and creates connections between variables. Must load ops first
        '''
        self.__load_facts()

        # format all of the ops from lists to dataframes
        for k,v in self.ops.items():
            self.ops[k] = pd.DataFrame(data=v, columns=self.ops_df.columns)

    def __load_facts(self) -> None:
        '''
        Loads in all related .facts info from the opAll.facts file. From this, we create
        a graph depicting the relationships between variables and how those variables are used.
        Opcode information is saved into the self.ops dict, and self.ops_df dataframe.

        A graph edge is created in one of two cases:
        1. If a new variable is defined from a previously defined variable, an edge is created
        from the used variable to the defined variable
        2. An edge will always be created between a use variable and any opcode that uses the variable

        We are then able to find whether an instruction is connected to another instruction by checking
        this graph relationship via pydatalog

        At this state self.ops consists of a dict of lists, not a dict of dataframes, as it 
        is in the next step of load()
        '''
        self.ops_df = pd.read_csv(self.path + 'opAll.facts', sep="\t", header=None, names=["loc","pc","op","depth","cn","value","def","#uses","var1","var2",'var3','var4','var5','var6','var7'])

        all_ops = self.ops_df['op'].unique().tolist()
        self.ops = dict.fromkeys(all_ops, None)

        prev_cn = self.ops_df.iloc[0]['cn']
        prev_depth = self.ops_df.iloc[0]['depth'] 

        for index, op in self.ops_df.iterrows():
            opcode = op['op']
            depth = op['depth']

            if depth > self.max_depth:
                self.max_depth = depth

            if not pd.isna(op['var1']):
                if not pd.isna(op['def']):
                    +edge(op['var1'], op['def'])
                
                +edge(op['var2'], (opcode, op['cn']))

            if not pd.isna(op['var2']):
                if not pd.isna(op['def']):
                    +edge(op['var2'], op['def'])
            
                +edge(op['var2'], (opcode, op['cn']))

            if not pd.isna(op['def']):
                +value(op['def'], op['value'])

            if self.ops[opcode] == None:
                self.ops[opcode] = [op]
            else:
                self.ops[opcode].append(op)

            # if this occured, we had a depth change, and we can get the address of
            # the previous smart contract via var2
            if prev_cn != op['cn']:
                if opcode in ["CALL", "CALLCODE", "STATTICCALL","DELEGATECALL"]:
                    prev_addr = opcode["var2"]
                    +addr((prev_cn,prev_depth), prev_addr)

            prev_cn = op['cn']
            prev_depth = op['depth']

    def contains_instr(self, var : str, instr : str, call_num):
        '''
            Deteremines whether a specified opcode is able to be reached via
            a defined variable. Checks whether the call number of the variable 
            matches 

            Links are defined by def-use relationships. Any use will be linked
            to the def opcode

            TODO: figure out if i need to do checks for depth and callnum here?
            or maybe just callnum. Currently just callnum checked
        '''
        can_reach(X,Y) <= can_reach(X,Z) & edge(Z,Y) & (X!=Y)
        can_reach(X,Y) <= edge(X,Y)

        res = can_reach(var, Y)
        return True if ((instr, call_num),) in can_reach(var, Y) else False
    

    def reduce_instr(self, df : pd.DataFrame, instr : str) -> pd.DataFrame:
        '''
            Reduces a dataframe based on whether a defined variable in the dataframe
            contains a linked opcode (via def-use relationship). If the opcode does not
            define any new variables, it will not be included in the result. 

            Returns the reduced dataframe
        '''

        def parse_row(var1 : str, var2: str, cn : int):
            if not pd.isna(var1):
                if self.contains_instr(var1, instr, cn):
                    return True
            elif not pd.isna(var2):
                if self.contains_instr(var2, instr, cn):
                    return True
            return False

        df.loc[:,'contains_instr'] = df.apply(lambda row: parse_row(row['var1'], row['var2'], row['cn']), axis=1)

        res = df.loc[df['contains_instr'] == True].copy()

        res.drop('contains_instr', axis=1, inplace=True)

        return res

    def find_instr(self, instr : str) -> pd.DataFrame:
        '''
            Finds all variables where the opcode of the defining variables
            matches the provided instruction. Returns a list of all instructions
        '''
        return self.ops[instr]


    def find_instr_depth(self, instr, exact_depth : int = None, min_depth : int = None, max_depth : int = None) -> pd.DataFrame:
        '''
            Finds all variables matching certain an instruction and three depth parameters, 
            inclusively. Returns a list consisting of found variables
                1. the instruction to match with 
                2. (optional) the exact depth to find all instructions at
                3. (optional) the minimum depth to find instructions at
                4. (optional) the maximum depth where an instruction can be found
        '''
        if exact_depth == None and min_depth == None and max_depth == None:
            return self.find_instr(instr)

        if exact_depth != None:
            min_depth = exact_depth
            max_depth = exact_depth
        else:
            max_depth = self.max_depth if max_depth == None else max_depth
            min_depth = 0 if min_depth == None else min_depth

        all_instrs = self.ops[instr]

        bounded_instrs = all_instrs[all_instrs['depth'].between(min_depth, max_depth, inclusive=True)]

        return bounded_instrs.copy() # we create a copy so that any reductions can be safely made on the data

    def reduce_value(self, df1 : pd.DataFrame, df2: pd.DataFrame, df1_comparator : str, df2_comparator : str) -> pd.DataFrame:
        '''
            Compares two dataframes to determine if there exists a link between the value column
            of dataframes. Any row with a value from the first dataframe that does not have a 
            corresponding value in the second dataframe will be omitted in the return result.

            The df_1_comparator variable is a string used to determine what column to get the value 
            for from the dataframe, and similar for df_2. They should be a Variable row in the dataframe,
            so either a def_var or one of the use_vars...
            
            We only check one variable at a time rather than all possible variables because 
            we know specifically what variable should be analyzed.

            After the value is found, we use pandas logic to determine any shared values. In this,
            we make the assumption that all values 
        '''

        def locate_variable(var) -> int:
            if not pd.isna(var):
                return value(var,Y).v()[0]
            else:
                raise ValueError

        res : List = []

        df1.loc[:,'use_val'] = df1.apply(lambda row: locate_variable(row[df1_comparator]), axis=1)
        
        df2.loc[:,'use_val'] = df2.apply(lambda row: locate_variable(row[df2_comparator]), axis=1)

        res = df1[df1['use_val'].isin(df2['use_val'])].copy()

        df1.drop('use_val', axis=1, inplace=True)
        df2.drop('use_val', axis=1, inplace=True)

        return res
    
    def reduce_addr(self, df1 : pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        '''
            Reduces the first dataframe by determining the smart contract executing the opcode.
            If the smart contract matches any smart contract that is executed in the second dataframe,
            then it is added to the result.

            The addresses are resolved based on the call number of the row in the dataframe 
        '''

        def locate_addr(cn,d) -> int:
            if not pd.isna(cn,d):
                return addr((cn,d),Y).v()[0]
            else:
                raise ValueError

        df1.loc[:,'addr'] = df1.apply(lambda row: locate_addr(row['cn'],row['depth']), axis=1)
    
        df2.loc[:,'addr'] = df2.apply(lambda row: locate_addr(row['cn'], row['depth']), axis=1)

        res = df1[df1['addr'].isin(df2['addr'])].copy()

        df1.drop('addr', axis=1, inplace=True)
        df2.drop('addr', axis=1, inplace=True)

        return res.copy()