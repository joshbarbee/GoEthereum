import decompiler.cfg as cfg
import decompiler.opcodes as opcodes
import decompiler.patterns as patterns

import decompiler.tac_cfg as tac_cfg
import decompiler.opcodes as opcodes

from typing import List, Dict

import networkx as nx
import matplotlib.pyplot as plt


class Variable:
    def __init__(
        self,
        var_name: str,
        pc: int,
        depth: int,
        call_index: int,
        op: opcodes.OpCode,
        values: List[int],
    ) -> None:
        self.var_name = var_name
        self.pc = pc
        self.depth = depth
        self.call_index = call_index
        self.op = op
        self.values = values

    def __hash__(self) -> int:
        return hash(self.var_name)

    def __repr__(self) -> str:
        return self.var_name

    def value(self) -> int:
        res = ""

        for i in self.values:
            res += str(i).zfill(64)  # fill to 32 bytes

        return int(res)


class Op:
    def __init__(
        self,
        opcode: opcodes.OpCode,
        pc: int,
        call_index: int,
        depth: int,
        def_var: Variable = None,
        used_vars: List[Variable] = [],
    ) -> None:
        self.pc = pc
        self.depth = depth
        self.call_index = call_index
        self.used_vars = used_vars
        self.def_var = def_var
        self.opcode = opcode

    def __hash__(self) -> int:
        return hash((self.opcode, self.pc, self.call_index, self.depth))

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Op):
            if (
                self.pc == __o.pc
                and self.depth == __o.depth
                and self.call_index == __o.call_index
                and self.opcode == __o.opcode
            ):
                return True
            else:
                return False
        elif isinstance(__o, Dict):
            dict_repr = {
                "pc": self.pc,
                "depth": self.depth,
                "call_index": self.call_index,
                "opcode": self.opcode,
                "depth": self.depth,
            }

            intersect_keys = dict_repr.keys() & __o.keys()

            if len(intersect_keys) == 0:
                return False

            for key in intersect_keys:
                if dict_repr[key] != __o[key]:
                    return False

            return True

        raise NotImplemented

    def to_dict(self) -> Dict[str, int | str]:
        return {
            "pc": self.pc,
            "depth": self.depth,
            "call_index": self.call_index,
            "opcode": self.opcode,
            "depth": self.depth,
        }

    def get_props(self, s: set[str]) -> Dict[str, int | str]:
        try:
            return {i: getattr(self, i) for i in s}
        except AttributeError as e:
            raise e

    def __repr__(self) -> str:
        return {
            "opcode": self.opcode,
            "pc": self.pc,
            "call_index": self.call_index,
            "depth": self.depth,
        }


class API:
    def __init__(self, source: tac_cfg.TACGraph) -> None:
        """Representation of Vandal Datalog instructions
        as Python / PyDatalog

        Args:
            source (object): the CFG object to be analyzed
        """

        self.source = source

        # allows selecting operators by opcode
        self.op_map = {}

        # allows selecting variables by variable name (V1, V2, V1337, etc.)
        self.var_map = {}

        # graph representation of variables used through execution, with a graph
        # maintained for each call
        self.graphs: List[nx.DiGraph] = []

        # each call number is a different address, n-th index is call # n
        self.addresses = []

        # maps Variable object to the immediate dominators of the variable
        self.dominators = {}

        self.__load_graph__()

    def __load_graph__(self):
        self.addresses.append(self.source.sc_addr.lower())

        for block in self.source.blocks:
            for op in block.tac_ops:
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
                    used_vars = [self.var_map[arg.value.name] for arg in op.args]
                else:
                    used_vars = []

                # determine any newly defined variablesfrom opcode
                if isinstance(op, tac_cfg.TACAssignOp):
                    if op.lhs.values.is_finite:
                        vals = [val for val in op.lhs.values]

                    new_var = Variable(
                        op.lhs.name,
                        op.pc,
                        op.depth,
                        op.call_index,
                        op.opcode.name,
                        vals,
                    )
                    self.var_map[op.lhs.name] = new_var
                else:
                    new_var = None

                # create new Op, add to mapping of all opcodes
                new_op = Op(
                    op.opcode, op.pc, op.call_index, op.depth, new_var, used_vars
                )

                if op.opcode.name not in self.op_map:
                    self.op_map[op.opcode.name] = [new_op]
                else:
                    self.op_map[op.opcode.name].append(new_op)

                # add edges between def and use Vars in NetworkX, with the edges being
                # the opcodes, and the nodes being Variables
                if new_var:
                    self.graphs[op.call_index].add_node(new_var)
                    for use_var in used_vars:
                        self.graphs[op.call_index].add_edge(
                            use_var, new_op, data=new_op
                        )
                else:
                    self.graphs[op.call_index].add_node(new_op)
                    for use_var in used_vars:
                        self.graphs[op.call_index].add_edge(use_var, new_op, data=new_op)

    def get_ops(
        self, opcode: opcodes.OpCode, min_ci: int = 0, min_depth: int = 0
    ) -> List[Op]:
        """Gets all opcodes matching a particular Opcode instance

        Args:
            opcode (opcodes.OpCode): the opcode to get all opcodes collected for
            min_ci (int, optional): minimum call index of opcode. Defaults to 0.
            min_depth (int, optional): minimum depth of opcode when used. Defaults to 0.

        Returns:
            List[Op]: List of all opcodes matching the min_c and min_depth with the opcode name
            matching the provided opcode
        """

        if min_ci == min_depth == 0:
            return self.op_map[opcode.name]

        ops = self.op_map[opcode.name]
        res = []

        for op in ops:
            if op.call_index >= min_ci and op.depth >= min_depth:
                res.append(op)

        return res

    def get_ops_by_ops(
        self, opcode: opcodes.OpCode, ops: List[Op], props: set[str]
    ) -> List[Op]:
        """Gets all opcodes that share common attributes with a list of already-collected Op
        variables.

        Args:
            opcode (opcodes.OpCode): the specific type of op to collect
            ops (List[Op]): the list of Ops that the returned operators should share matching
            properties with
            props (set[str]): a set of strings that correspond to properties defined within
            the Op variable. Example is {'call_index', 'depth'}
        Returns:
            List[Op]: a list of opcodes that are the same opcode type as opcode and match the same
            properties as defined in props with SOME op in ops.
        """

        req_values = []

        for op in ops:
            req_values.append(op.get_props(props))

        req_values = [dict(p) for p in set(tuple(i.items()) for i in req_values)]
        temp = self.op_map[opcode.name]

        res = []
        for op in temp:
            if op in req_values:
                res.append(op)

        return res

    def __create_potential_matches(
        self, ops1: List[Op], ops2: List[Op], props: set[str]
    ) -> Dict[Op, List[Op]]:
        res = {}

        if len(props) == 0:
            return {op1: ops2 for op1 in ops1}

        for op1 in ops1:
            res[op1] = []
            op1_props = op1.get_props(props)

            for op2 in ops2:
                if op2.get_props(props) == op1_props:
                    res[op1].append(op2)

        return res

    def filter_props(self, ops : List[Op], props: Dict[str, int | str]) -> List[Op]:
        """Filters a list of ops based on particular properties. props is a dict
        between Op properties (call_index, depth, pc, etc.) and discrete values. 
        For example: props={"call_index":2, "depth":3}

        Args:
            ops (List[Op]): List of ops to filter based on property values
            props (Dict[str, int  |  str]): Dict of properties to filter by

        Returns:
            List[Op]: Filtered list of ops
        """        
        res = []
        
        for op in ops:
            if op == props:
                res.append(op)

        return res


    def reduce_props(self, ops1: List[Op], ops2: List[Op], props: set[str]) -> List[Op]:
        """Reduces the list ops1 by the list ops2 where properties of the Op variables in ops1 does not
        match any of the Ops in ops2.

        Args:
            ops1 (List[Op]): list of opcodes to check for properties, and then return
            ops2 (List[Op]): list of opcodes to source property values from
            props (set[str]): a set of strings that correspond to properties defined within
            the Op variable. Example is {'call_index', 'depth'}

        Returns:
            List[Op]: A list of opcodes from ops1 that match similar properties
            to ops2
        """
        for op in ops2:
            req_values.append(op.get_props(props))

        req_values = [dict(p) for p in set(tuple(i.items()) for i in req_values)]

        res = []

        for op in ops1:
            if op in req_values:
                res.append(op)

        return res

    def reduce_value(self, ops: List[Op], value: int) -> List[Op]:
        """Reduce a list of opcodes based on a discrete value, and
        if the opcodes created a variable with that value

        Args:
            ops (List[Op]): list of opcodes to iterate over
            value (int): discrete value for op to define

        Returns:
            List[Op]: list of opcodes that define a value matching
            value
        """
        res = []

        for op in ops:
            if op.def_var is not None:
                for v in op.def_var.values:
                    if v == value:
                        res.append(op)

        return res

    def reduce_values(
        self,
        ops1: List[Op],
        ops2: List[Op],
        ops1_def: bool = True,
        ops2_def: bool = True,
        props : set[str] = {}
    ) -> List[Op]:
        """Reduces ops1 by the relation between values defined or used in ops1 and ops2.

        If ops1_def is left True, then values will be collected from the defined variable for each op in
        ops1. If this matches any value in ops2_vals, then add to the returned list. If ops1_def is instead
        set to False, the value of used variables of ops1 are analyzed, instead of the value of the defined variables.

        If ops2_def is left True, the the defined variables from the list of ops2 will be used for analysis. These must then
        match the defined / used variable values in ops1. If ops2_def is set False, then the used variabled will be analyzed
        instead.

        Args:
            ops1 (List[Op]): list of first set of opcodes to check values for. This is the set of opcdoes that the return
            value modifies
            ops2 (List[Op]): list of second set of opcodes to compare values to
            ops1_def (bool, optional): Whether to use the defined variables of ops1, or the used variables.
                Defaults to True (def vars).
            ops2_def (bool, optional): Whether to use the defined variables of ops1, or the used variables.
                Defaults to True (def vars).

        Returns:
            List[Op]: a list of Op instances from ops1 that have a def/use var with the same value as a
            def/use var from ops2
        """
        # if ops2_def:
        #     op2_vals = [op.def_var.value() for op in ops2]
        # else:
        #     op2_vals = [var.value() for op in ops2 for var in op.used_vars]

        possible_links = self.__create_potential_matches(ops1, ops2, props)

        res = []

        for op, linked_ops in possible_links.items():
            vals = [op.def_var.value()] if ops1_def else op.used_vars

            found = False
            for linked_op in linked_ops:
                if found: break

                if ops2_def is True and linked_op.def_var.value() in vals:
                    res.append(op)
                    found = True
                elif ops2_def is False:
                    for use_var in op.used_vars:
                       if use_var.value() in vals:
                            res.append(op)
                            found = True

        return res

    def reduce_use(
        self,
        ops1: List[Op],
        ops2: List[Op],
        op2_vi: int = None,
        reverse: bool = False,
        props: set[str] = {},
    ) -> List[Op]:
        """Reduces ops1 by removing any Op variable that is not linked to any Op variable
        used in ops2. Relation between Ops is a DAG, so ops2 should use the value
        defined by op1.

        Args:
            ops1 (List[Op]): the list of Ops that should define a variable, which
            ops2 (List[Op]): the list of Ops that should use a variable defined by ops1
            op2_vi (int, optional): a specific variable index for ops2, if the index of the
            used variable to be analyzed is specifically known. Reduces search time and also
            potential of false positives
            reverse (bool, optional): flips ops1 and ops2, such that ops2 is the list that
            return values are calculated from (thus returning Ops that use defined vars from ops1)

        Returns:
            List[Op]: a list of ops from ops1 that define a variable used by ops2
        """
        res = []

        possible_uses = self.__create_potential_matches(ops1, ops2, props)

        for op, links in possible_uses.items():
            if len(res) == len(ops1):
                break  # early return if all results true

            if op.def_var is None:
                continue

            for op2 in links:
                if op2_vi == None:
                    for var in op2.used_vars:
                        if (
                            self.graphs[op.call_index].has_node(var)
                            and nx.has_path(
                                self.graphs[op.call_index], op.def_var, var
                            )
                        ):
                            res.append(op) if not reverse else res.append(var)
                else:
                    if (
                        self.graphs[op.call_index].has_node(op2.used_vars[op2_vi])
                        and nx.node_connectivity(
                            self.graphs[op.call_index],
                            s=op.def_var,
                            t=op2.used_vars[op2_vi],
                        )
                        > 0
                    ):
                        res.append(op) if not reverse else res.append(
                            op2.used_vars[op2_vi]
                        )

        return res

    def reduce_origin(self, ops: List[Op], addr: str | int) -> List[Op]:
        """Reduces a list of opcodes based on the address that executed the opcode.

        Args:
            ops (List[Op]): the list of ops to iterate over
            addr (str | int): a string or integer representation of the address that
            executed the specific opcode

        Returns:
            List[Op]: all opcodes that were executed under the defined address
        """
        res = []

        addr = hex(addr) if isinstance(addr, int) else addr

        for op in ops:
            if self.addresses[op.call_index].lower() == addr.lower():
                res.append(op)

        return res

    def reduce_origins(self, ops1: List[Op], ops2 : List[Op]) -> List[Op]:
        res = []

        addrs = {self.addresses[op.call_index] for op in ops2}

        for op in ops1:
            if self.addresses[op.call_index] in addrs:
                res.append(op)

        return res

    def reduce_dominators(self, ops1: List[Op], ops2: List[Op], props : set[str] = {}) -> List[Op]:
        def is_total_dominator(opList, matchOp, callIndex):
            if len(opList) == 0:
                return False
            elif len(opList) == 1 & opList == matchOp:
                return True

            for child in opList:
                return True & is_total_dominator(
                    self.graphs[callIndex].successors(child), matchOp, callIndex
                )

        res = []

        possible_links = self.__create_potential_matches(ops1, ops2, props)

        for op, links in possible_links.keys():
            if op.def_var is None:
                continue

            # get all predecessors
            for otherOp in links:
                if is_total_dominator([otherOp], op, op.call_index):
                    res.append(op)
                    break

        return res

    def reduce_reaches(self, ops1 : List[Op], ops2 : List[Op], props : set[str] = {}) -> List[Op]:
        possible_links = self.__create_potential_matches(ops1, ops2, props)

        res = []

        for op, links in possible_links.items():
            if op.def_var is None:
                continue

            isFound = False
            for link in links:
                if isFound: break

                for use_var in link.used_vars:
                    if nx.has_path(self.graphs[op.call_index], op.def_var, use_var):
                        res.append(op)
                        isFound = True


