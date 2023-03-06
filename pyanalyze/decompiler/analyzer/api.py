import decompiler.opcodes as opcodes
import decompiler.tac_cfg as tac_cfg
import decompiler.opcodes as opcodes

from typing import List, Dict, Callable

from decompiler.analyzer.variable import Variable
from decompiler.analyzer.op import Op, OpView


class OpAnalyzer:
    def __init__(self, source: tac_cfg.TACGraph) -> None:
        """Representation of Vandal Datalog instructions
        as Python / PyDatalog

        Args:
            source (object): the CFG object to be analyzed
        """

        self.source = source

        # allows selecting operator dataframes by opcode
        self.ops: Dict[str, OpView] = {}

        # associates variables with discrete values
        self.variables: Dict[str, Variable] = {}

        self.__load__()

    def __load__(self):
        """Loads data from the source tac_cfg into ops and Variables"""
        addresses = {0: self.source.sc_addr.lower()}

        for i, block in enumerate(self.source.blocks):
            for op in block.tac_ops:
                if op.opcode.name not in self.ops:
                    self.ops[op.opcode.name] = OpView()

                # determine any variables used in calculating opcode
                if op.opcode != opcodes.CONST:
                    used_vars = [arg.value.name for arg in op.args]
                else:
                    used_vars = []

                if op.opcode.is_call():
                    addresses[op.depth + 1] = hex(next(iter(op.args[1].value.value))).lower()
                    
                # determine any newly defined variables from opcode
                if isinstance(op, tac_cfg.TACAssignOp):
                    def_var = op.lhs.name

                    if op.lhs.values.is_finite:
                        # iterate through backwards to preserve bigendian-ness
                        value = int(str(op.lhs.values.const_value))
                else:
                    def_var = None
                    value = None

                new_op = Op(op.op_index, op.call_index, op.pc, op.opcode.name, op.depth)

                # add edges between def and use Vars in NetworkX, with the edges being
                # the opcodes, and the nodes being Variables
                if def_var is not None:
                    used_vars = [self.variables.get(var) for var in used_vars]
                    self.variables[def_var] = Variable(def_var, value, used_vars)

                    for var in used_vars:
                        var.succs.append(self.variables[def_var])

                    new_op.use_vars = used_vars
                    new_op.def_var = self.variables[def_var]
                else:
                    used_vars = [self.variables.get(var) for var in used_vars]
                    new_op.use_vars = used_vars

                self.ops[op.opcode.name].add_op(new_op)                

        for op in self.ops.values():
            op.addresses = addresses  
    @classmethod
    def load_from_dump(cls, tx: Dict[str, int | str | Dict]) -> "OpAnalyzer":
        """Abstracts the process of CFG creation away from the user, so only a
        string dump of the transaction logs is needed

        Args:
            tx (Dict[str, int  |  str  |  Dict]): the transaction logs

        Returns:
            OpAnalyzer: the new class instance instantiated on the cfg
        """
        cfg = tac_cfg.TACGraph.from_trace(tx)

        return cls(cfg)

    def get_ops(self, opcode: str, **kwargs: Dict[str, tuple[Callable, str]]) -> OpView:
        """Get a OpView of opcodes matching kwargs. Kwargs should be a named value
        matched with a 2-tuple of a comparison function and the discrete value
        to compare to. The comparision function should accept two parameters
        that allow comparision (such as an int).

        Examples:
            sload = api.get_ops('SLOAD', callindex=(lambda x, y: x>y, 2))
            jumpi = api.get_ops('JUMPI', callindex=(lambda x, y: x<=y, 3))

        Args:
            opcode (str): the opcode to get the OpView of

        Returns:
            OpView: a copy of the OpView matching the filters placed by kwargs
        """
        ops = self.ops[opcode].copy()

        ops.filter(**kwargs)

        return ops
