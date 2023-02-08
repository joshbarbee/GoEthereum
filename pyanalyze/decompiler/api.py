import decompiler.opcodes as opcodes
import decompiler.tac_cfg as tac_cfg
import decompiler.opcodes as opcodes

from typing import List, Dict

import networkx as nx
import matplotlib.pyplot as plt

import pandas as pd
import numpy as np

DF_COLS = {
    "loc": int(),
    "pc": int(),
    "op": str(),
    "depth": int(),
    "callindex": int(),
    "value": int(),
    "defvar": int(),
    "usevars": list(),
}

class Variable():
    def __init__(self, symbol : str, value : int, preds : List['Variable'] = []) -> None:
        self.symbol = symbol
        self.value = value
        self.succ = []
        self.preds = preds

    def is_parent(self, parent_vars : List['Variable'] | 'Variable') -> bool:
        """Return true if any Variable instance in parent_vars is a parent
        of the Variable instance. Uses BFS for searching

        Args:
            parent_vars (List[Variable;] | Variable): A List of variables or a
            single variable that should be a parent of `self`.

        Returns:
            bool: whether any of the Variables in parent_vars are a parent of 
            `self`
        """      

        if not isinstance(parent_vars, list):
            parent_vars = [parent_vars]

        queue = [self]
        visited = set()
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            if node in parent_vars:
                return True
            queue.extend(node.preds)

        return False
        
    def is_child(self, child_vars : List['Variable'] | 'Variable') -> bool:
        """Return true if any Variable instance in child_vars is a child
        of the Variable instance. Uses BFS for searching

        Args:
            child_vars (List[Variable;] | Variable): A List of variables or a
            single variable that should be a child of `self`.

        Returns:
            bool: whether any of the Variables in child_vars are a child of 
            `self`
        """ 
        if not isinstance(child_vars, list):
            child_vars = [child_vars]

        queue = [self]
        visited = set()
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            if node in child_vars:
                return True
            queue.extend(node.succ)

        return False

    def get_descendants(self) -> List['Variable']:
        """Returns all children and any descendants 
        of self's children as a list

        Returns:
            List['Variable]: all Variable descendants of self
        """        

        return self.succ + [i for var in self.succ for i in var.get_descendants()]
class API:
    def __init__(self, source: tac_cfg.TACGraph) -> None:
        """Representation of Vandal Datalog instructions
        as Python / PyDatalog

        Args:
            source (object): the CFG object to be analyzed
        """

        self.source = source

        # allows selecting operator dataframes by opcode
        self.ops: Dict[str, pd.DataFrame] = {}

        # graph representation of variables used through execution, with a graph
        # maintained for each call
        self.graphs: List[nx.DiGraph] = []

        # each call number is a different address, n-th index is call # n
        self.addresses : List[str] = []

        # associates variables with discrete values
        self.variables : Dict[str, Variable] = {}   

        self.__load__()

    def __load__(self):
        self.addresses.append(self.source.sc_addr.lower())

        # load ops into dict first for faster conversion w/ pandas
        ops = {}

        for block in self.source.blocks:
            for op in block.tac_ops:
                # create dataframe for opcode if dataframe does not exist
                if op.opcode.name not in ops:
                    ops[op.opcode.name] = []

                # initialize graph for cn if not present
                while len(self.graphs) - 1 < op.call_index:
                    self.graphs.append(nx.DiGraph())

                # if call, determine current address of execution
                if op.opcode.is_call():
                    self.addresses.append(
                        hex(next(iter(op.args[1].value.value))).lower()
                    )

                # determine any variables used in calculating opcode
                if op.opcode != opcodes.CONST:
                    used_vars = [arg.value.name for arg in op.args]
                else:
                    used_vars = []

                # determine any newly defined variables from opcode
                if isinstance(op, tac_cfg.TACAssignOp):
                    def_var = op.lhs.name

                    if op.lhs.values.is_finite:
                        # iterate through backwards to preserve bigendian-ness
                        value = int(str(op.lhs.values.const_value))
                else:
                    def_var = None
                    value = None

                ops[op.opcode.name].append(
                    [
                        op.op_index,
                        op.pc,
                        op.opcode.name,
                        op.depth,
                        op.call_index,
                        value,
                        def_var,
                        used_vars,
                    ]
                )

                # add edges between def and use Vars in NetworkX, with the edges being
                # the opcodes, and the nodes being Variables
                if def_var is not None:
                    used_vars = [self.variables.get(var) for var in used_vars]

                    self.variables[def_var] = Variable(def_var, value, used_vars)

                    for var in used_vars:
                        var.succ.append(self.variables[def_var])

        # load each op into separate dataframe
        for k in ops.keys():
            self.ops[k] = pd.DataFrame(ops[k], columns=DF_COLS)

    def get_ops(self, opcode: str, **kwargs: Dict[str, tuple[str, str]]) -> pd.DataFrame:
        """get_ops returns a copy of a dataframe of a particular opcode. **kwargs
        keys are columns of the opcode dataframe, as those listed in DF_COLS. The
        values should be 2-tuples of the comparator (<,>,==,!=,...) as a string
        and the discrete value to compare to.

        This will always copy from the original dataframe

        Examples::

            get_ops('JUMPI', callindex=('<', 2))
            get_ops('CONST', depth=('!=', 3), value=('==', 2))

        Args:
            opcode (str): the opcode  name (in uppercase) to get the df of
            **kwargs (dict[str, 2-tuple]): keyed arguments to control what
            rows of the df to return
        Returns:
            pd.DataFrame: the dataframe matching the properties specified by **kwargs,
            or just a copy of the dataframe if no kwargs.
        """
        if len(kwargs) == 0:
            return self.ops[opcode].copy()

        return self.ops[opcode].query(
            " and ".join(f"{k}{v[0]}{v[1]}" for k, v in kwargs.items()),
            inplace=False,
        )

    def filter_ops(
        self, ops: pd.DataFrame, copy=True, deep=False, **kwargs : Dict[str, tuple[str, str]]) -> pd.DataFrame | None:
        """filter_ops filters a Dataframe of ops based on 2-tupled kwargs, 
        returning either a view or copy **kwargs keys are columns of the 
        opcode dataframe, as those listed in DF_COLS. The values should 
        be 2-tuples of the comparator (<,>,==,!=,...) as a string and 
        the discrete value to compare to. If copy is False, then 
        modifications are made in place, and nothing is returned

        Examples::

            filter_ops(ops, copy=True, callindex=('<',2))

        Args:
            ops (pd.DataFrame): the Dataframe of opcodes to filter
            copy (bool, optional): Whether to return a copy, or instead. Defaults to True.
            deep (bool, optional): Whether to perform a deep copy or shallow. Defaults to False.
            **kwargs (dict[str, 2-tuple]): keyed arguments to control what
            rows of the df to return
        Returns:
            pd.DataFrame: the dataframe view or copy matching the pased filters
        """  
        if len(kwargs) == 0:
            return ops if not copy else ops.copy(deep=deep)

        return ops.query(
            " and ".join(f"\`{k}\`{v[0]}{v[1]}" for k, v in kwargs.items()),
            inplace=not copy
        )

    def get_ops_by_ops(
        self, opcode: str, ops: pd.DataFrame, **kwargs: Dict[str,bool]) -> pd.DataFrame:
        """Gets all opcodes that share common attributes with a dataframe of
        already-collected operators. Returns a dataframe consisting of all
        operators with that have some matching value in a kwarg-defined column
        with some op in ops. ONLY **kwargs that are defined as equal to True
        will be used when filtering (i.e depth=True). Will always make a copy

        Examples::

            get_ops_by_ops("JUMPI", sload, callindex=True, depth=True)

        Args:
            opcode (opcodes.OpCode): the specific type of op to collect
            ops (pd.DataFrame): the list of Ops that the returned operators should share matching
            properties with
            **kwargs (dict[str, bool]): keyed arguments to control what
            rows of the df to return, in the format column=True/False
        Returns:
            pd.DataFrame: a list of opcodes that are the same opcode type as opcode and match the same
            properties as defined in props with SOME op in ops.
        """

        cols = [k for k, v in kwargs.items() if v]

        if len(cols) == 0:
            return self.get_ops(opcode)
        
        df = self.ops[opcode].merge(
            ops, 
            on=cols, 
            how='inner',
            suffixes=(None, "_y"))

        df = df.loc[:,~df.columns.str.endswith('_y')]
        return df[~df.astype(str).duplicated()].copy()


    def reduce_props(self, ops1: pd.DataFrame, ops2: pd.DataFrame, copy : bool = True, **kwargs: Dict[str,bool]) -> pd.DataFrame:
        """Reduces the Dataframe ops1 by ops2 where a value in a particular kwarg-denoted
          column is the same. 

          *If only reducing by one column, this will be slower than doing the manipulation
          yourself. This is meant for multi-column reductions

        Examples::

            reduce_props(ops1, ops2, callindex=True, depth=True)

        Args:
            ops1 (pd.DataFrame): list of opcodes to check for properties, and then return
            ops2 (pd.DataFrame): list of opcodes to source property values from
            copy (bool) : whether to copy the returned dataframe or just return a view
            **kwargs (dict[str, bool]): keyed arguments to control what
            rows of the df to return, in the format column=True/False
        Returns:
            pd.DataFrame: A list of opcodes from ops1 that match similar properties
            to ops2
        """

        cols = [k for k, v in kwargs.items() if v]

        if len(cols) == 0:
            return ops1  
        
        df = ops1.merge(
            ops2, 
            on=cols, 
            how='inner',
            suffixes=(None, "_y"))
        df = df.loc[:,~df.columns.str.endswith('_y')]
        df = df[~df.astype(str).duplicated()]
        return df if not copy else df.copy

    def reduce_value(self, ops: pd.DataFrame, value: int, var_index : int = None, copy : bool = True) -> pd.DataFrame:
        """Reduces ops based on whether a used variable by an op is equal to the 
        discrete value passed by value. If var_index is passed, only the n-th 
        use-var is checked, rather than all of them. 

        Args:
            ops (pd.DataFrame): the dataframe of opcodes to reduce
            value (int): the discrete integer value a usevar should reference
            var_index (int, optional): the indice of the used variable in the usevars column. Defaults to None.
            copy (bool, optional): Whether to return a view or copy of the dataframe. Defaults to True.

        Returns:
            pd.DataFrame: a Dataframe of all ops where a use_var is equal to a discrete value
        """         

        if var_index is None:
            df = ops[[any(self.variables.get(var).value == value for var in usevars) for usevars in ops['usevars']]]
            return df if not copy else df.copy()

        df = ops[[self.variables.get(usevars[var_index]).value == value for usevars in ops['usevars']]]
        return df if not copy else df.copy()


    def reduce_values(
        self,
        ops1: pd.DataFrame,
        ops2: pd.DataFrame,
        ops1_def: bool = True,
        ops2_def: bool = True,
        ops1_use_vi: int = None,
        ops2_use_vi: int = None,
        copy: bool = True,
        **kwargs: Dict[str,bool],
    ) -> pd.DataFrame:
        """Reduces the ops1 Dataframe by discrete values from the ops2 dataframe. 

        A copy is always made is ops1_def is False

        If ops1_def is left True, then values will be collected from the defined variable 
        for each op in ops1. If ops1_def is instead set to False, the value of used variables 
        of ops1 are analyzed, instead of the value of the defined variables.

        If ops2_def is left True, the the defined variables from the dataframe of ops2 will be 
        used for analysis. These must then match the defined / used variable values in ops1. 
        If ops2_def is set False, then the used variabled will be analyzed instead.

        **kwargs defines additional properties that must match when making the value linkage,
        as boolean values.

        For example, kwargs can be :obj:`callindex=True, depth=True`

        Args:
            ops1 (pd.DataFrame): Dataframe of ops to modify
            ops2 (pd.DataFrame): Dataframe of ops to compare to
            ops1_def (bool, optional): Whether to use the defined variables of ops1, or the used variables.
                Defaults to True (def vars).
            ops2_def (bool, optional): Whether to use the defined variables of ops1, or the used variables.
                Defaults to True (def vars).
            ops1_use_vi (int, optional): The indice of the use var to analyze if ops1_def is False
            ops2_use_vi (int, optional): The indice of the use var to analyze if ops2_def is False
            **kwargs (dict[str, bool]): keyed arguments to control additional matching properties
            required for linkage, such as having the same call index
        Returns:
            pd.DataFrame: a list of Op instances from ops1 that have a def/use var with the same value as a
            def/use var from ops2
        """

        cols = [k for k, v in kwargs.items() if v]

        if ops2_def and len(cols) > 0:
            req_val_tuples = list(zip(*(
                ops2[col] for col in cols), 
                tuple(self.variables.get(defvar).value for defvar in ops2['defvar'])
            ))
        elif ops2_def and len(cols) == 0:
            req_val_tuples = tuple(self.variables.get(defvar).value for defvar in ops2['defvar'])
        elif ops2_use_vi is not None:
            if len(cols) > 0:
                req_val_tuples = list(zip(*(
                    ops2[col] for col in cols), 
                    set(self.variables.get(usevars[ops2_use_vi]).value for usevars in ops2['usevars'])
                ))
            else:
                req_val_tuples = tuple(self.variables.get(usevars[ops2_use_vi]).value for usevars in ops2['usevars'])
        else:
            if len(cols) > 0:
                req_cols = (ops2[col] for col in cols)
                req_val_tuples = list(zip(*req_cols, 
                    set(self.variables.get(var).value for usevars in ops2['usevars'] for var in usevars)
                ))
            else:
                req_val_tuples = [self.variables.get(var).value for usevars in ops2['usevars'] for var in usevars]

        if ops1_def:
            cols.append('defvar')
            df = ops1[(ops1[cols].values[:,None] == req_val_tuples).all(len(cols)).any(1)]
            return df if not copy else df.copy()
        elif ops1_use_vi is not None:
            cols.append('usevar')
            ops1 = ops1.copy()
            ops1['usevar'] = [self.variables[var[ops1_use_vi]].value for var in ops1['usevars']]            
            df = ops1[(ops1[cols].values[:,None] == req_val_tuples).all(len(cols)).any(1)]

            return df.drop('usevar', axis=1)
        pass

    def reduce_parent(
        self,
        ops1: pd.DataFrame,
        ops2: pd.DataFrame,
        ops1_vi: pd.DataFrame,
        copy : bool = True,
        **kwargs : dict[str, bool]
    ) -> pd.DataFrame:
        """Reduces ops1 by removing all ops that do not use a variable that is connected
        to a variable defined by ops2. Uses BFS to determine linkages between variables

        For example, if ops2 has a Op that defines V3, which is then used as an argument
        to the definition of V4, and then V4 is used as the argument to V5, then if ops1
        has a Op that defines v5, it will be included in the returned dataframe

        Examples::

            reduce_parent(ops1, ops2, 1, callindex=True, depth=True)

        Args:
            ops1 (pd.DataFrame): the Dataframe of Ops that should use a variable, and is being
            modified. ops1 should use a variable.
            ops2 (pd.DataFrame): the Dataframe of Ops that should define a variable linked
            to an op in ops2.
            op1_vi (int, optional): a specific variable index for ops1, if the index of the
            used variable to be analyzed is specifically known. Reduces search time and also
            potential of false positives
            copy (bool, optional): whether to copy or return the same dataframe. Defaults to true.
            **kwargs (dict[str, bool]): keyed arguments to control additional matching properties
            required for linkage, such as having the same call index
        Returns:
            pd.DataFrame: a list of ops from ops1 that define a variable used by ops2
        """
        
        cols = [k for k, v in kwargs.items() if v]
        req_cols = [ops2[col] for col in cols]
        req_vars = set(self.variables.get(defvar) for defvar in ops2['defvar'])
        
        if len(req_cols) > 0:
            ops1 = ops1[(ops1[cols].values[:,None] == req_cols).all(len(cols)).any(1)]

        if ops1_vi:
            ops1_vars = set(usevars[ops1_vi] for usevars in ops1['usevars'])

        child_vars = set(i.symbol for var in req_vars for i in var.get_descendants())
        matched_vars = ops1_vars.intersection(child_vars)

        mask = ops1['usevars'].apply(lambda usevars: any(var for var in matched_vars if var in usevars))
        
        if copy:
            new_df = ops1.copy(deep=True)
            return new_df[mask]

        return ops1[mask]


    def reduce_origin(self, ops: pd.DataFrame, addr: str | List[str], copy = True) -> pd.DataFrame:
        """Reduces a Dataframe of opcodes based on the address that executed the opcode.

        Args:
            ops (pd.DataFrame): the list of ops to iterate over
            addr (str | List[str]): a string or  list of strings that are the addresses 
            that should have executed the opcode
            copy (bool, Optional): whether to copy or modify in-place the result dataframe.
            Defaults to True.
        Returns:
            pd.DataFrame: all opcodes that were executed under the defined address
        """
        
        res = ops[[self.addresses[ci] in addr for ci in ops['callindex']]]
        return res.copy() if copy else res

    def reduce_origins(self, ops1: pd.DataFrame, ops2 : pd.DataFrame, copy : bool = True, **kwargs : dict[str,bool]) -> pd.DataFrame:
        """Reduces the first dataframe ops1 by the second dataframe ops2 based on the address
        used to execute the opcodes in ops2.

        Args:
            ops1 (pd.DataFrame): the Dataframe of opcodes to reduce
            ops2 (pd.DataFrame): the Dataframe of opcodes to reduce by
            copy (bool, Optional): whether to copy or modify the dataframe in-place. Defaults
            to True
            **kwargs (dict[str, bool]): keyed arguments to control additional matching properties
            required for linkage, such as having the same call index
        Returns:
            pd.DataFrame: The ops1 dataframe reduced by the originating opcode of the dataframe
        """ 

        cols = [k for k, v in kwargs.items() if v]

        if len(cols) == 0:
            req_val_tuples = tuple(self.addresses[ci] for ci in ops2['callindex'])
        else:
            req_val_tuples = list(zip(*(
                ops2[col] for col in cols), 
                tuple(self.addresses[ci] for ci in ops2['callindex'])
            ))       

         

    # def reduce_dominators(self, ops1: pd.DataFrame, ops2: pd.DataFrame, props : set[str] = {}) -> pd.DataFrame:
    #     pass

    # def reduce_reaches(self, ops1 : pd.DataFrame, ops2 : pd.DataFrame, props : set[str] = {}) -> pd.DataFrame:
    #     pass
