"""exporter.py: abstract classes for exporting decompiler state"""

import abc
import csv
from email.policy import strict
import logging
import os

import decompiler.cfg as cfg
import decompiler.opcodes as opcodes
import decompiler.patterns as patterns
import decompiler.tac_cfg as tac_cfg


class Exporter(abc.ABC):
    def __init__(self, source: object):
        """
        Args:
          source: object instance to be exported
        """
        self.source = source

    @abc.abstractmethod
    def export(self):
        """
        Exports the source object to an implementation-specific format.
        """


class CFGTsvExporter(Exporter, patterns.DynamicVisitor):
    """
    Writes logical relations of the given TAC CFG to local directory.

    Args:
      cfg: the graph to be written to logical relations.
    """

    def __init__(self, cfg: tac_cfg.TACGraph):
        """
        Generates .facts files of the given TAC CFG to local directory.

        Args:
          cfg: source TAC CFG to be exported to separate fact files.
        """
        super().__init__(cfg)

        self.defined = []
        """
        A list of pairs (op.pc, variable) that specify variable definition sites.
        """

        self.reads = []
        """
        A list of pairs (op.pc, variable) that specify all usage sites.
        """

        self.writes = []
        """
        A list of pairs (op.pc, variable) that specify all write locations.
        """

        self.__output_dir = None

    def __generate(self, filename, entries):
        path = os.path.join(self.__output_dir, filename)
        with open(path, 'w') as f:
            writer = csv.writer(f, delimiter='\t', lineterminator='\n')
            for e in entries:
                writer.writerow(e)

    def __generate_blocks_ops(self, out_opcodes):
        # Write a mapping from operation addresses to corresponding opcode names;
        # a mapping from operation addresses to the block they inhabit;
        # any specified opcode listings.
        ops = []
        op_rels = {opcode: list() for opcode in out_opcodes}

        for block in self.source.blocks:   
            for op in block.tac_ops:
                ops.append((hex(op.pc), op.opcode.name, op.op_index))
                if op.opcode.name in out_opcodes:
                    if op.has_lhs:
                        output_tuple = tuple([hex(op.pc)] +
                                            [arg.value.name for arg in op.args] + [op.lhs.name] + [op.op_index] + [op.depth] + [op.call_index])
                    else:
                        output_tuple = tuple([hex(op.pc)] +
                                            [arg.value.name for arg in op.args] + [op.op_index] + [op.depth] + [op.call_index])
                    op_rels[op.opcode.name].append(output_tuple)

        self.__generate("op.facts", ops)

        for opcode in op_rels:
            self.__generate("op_{}.facts".format(opcode), op_rels[opcode])

    def __generate_def_use_value(self):
        # Mapping from variable names to the addresses they were defined at.
        define = []
        # Mapping from variable names to the addresses they were used at.
        use = []
        # Mapping from variable names to their possible values.
        value = []
        for block in self.source.blocks:
            for op in block.tac_ops:
                # If it's an assignment op, we have a def site
                if isinstance(op, tac_cfg.TACAssignOp):
                    define.append((op.lhs.name, hex(op.pc), op.op_index, op.depth, op.call_index))

                    # And we can also find its values here.
                    if op.lhs.values.is_finite:
                        for val in op.lhs.values:
                            value.append((op.lhs.name, hex(val)))

                if op.opcode != opcodes.CONST:
                    # The args constitute use sites.
                    for i, arg in enumerate(op.args):
                        name = arg.value.name
                        
                        # relation format: use(Var, PC, ArgIndex)
                        use.append((name, hex(op.pc), i+1, op.op_index, op.depth, op.call_index))

            # Finally, note where each stack variable might have been defined,
            # and what values it can take on.
            # This includes some duplication for stack variables with multiple def
            # sites. This can be done marginally more efficiently.
            for var in block.entry_stack:
                if not var.def_sites.is_const and var.def_sites.is_finite:
                    name = block.ident() + ":" + var.name
                    for loc in var.def_sites:
                        define.append((name, hex(loc.pc), op.op_index, op.depth, op.call_index))

                    if var.values.is_finite:
                        for val in var.values:
                            value.append((name, hex(val)))

        self.__generate("def.facts", define)
        self.__generate("use.facts", use)
        self.__generate("value.facts", value)

    def __generate_sc_addr(self): 
        path = os.path.join(self.__output_dir, "sc_addr.facts")

        with open(path, 'w') as f:
            f.write(self.source.sc_addr.lower())

    '''
        Generates a simplified .facts file where all information is contained into only 
        one file. The ordering of the data is as such:
        location, pc, opcode, call_depth_, call_index, value, def, # use, use vars...
        
        The # of values should match the number of # of defined variables
    '''
    def __generate_simple(self):
        path = os.path.join(self.__output_dir, "allOps.facts")

        lines = []

        for block in self.source.blocks:
            for op in block.tac_ops:
                line = (op.op_index, hex(op.pc), op.opcode.name, op.depth, op.call_index)

                define = ()
                if isinstance(op, tac_cfg.TACAssignOp):
                    vals = ()
                    if op.lhs.values.is_finite:
                        for val in op.lhs.values:
                            vals = vals + (val,)
        
                    define = vals + (op.lhs.name, ) 
                else:
                    define = ("","") # filler data for tsv
                uses = ()
                if op.opcode != opcodes.CONST:
                    for i, arg in enumerate(op.args):
                        uses = uses + (arg.value.name, )

                line = line + define + (len(uses), ) + uses
            
                lines.append(line)

        self.__generate("opAll.facts", lines)        

    def export(self, output_dir: str = "", out_opcodes=[]):
        """
        Args:
          output_dir: location to write the output to.
          dominators: output relations specifying dominators
          out_opcodes: a list of opcode names all occurences thereof to output,
                       with the names of all argument variables.
        """
        if output_dir != "":
            os.makedirs(output_dir, exist_ok=True)
        self.__output_dir = output_dir

        self.__generate_blocks_ops(out_opcodes)
        self.__generate_sc_addr()
        self.__generate_def_use_value()
        self.__generate_simple()

class CFGStringExporter(Exporter, patterns.DynamicVisitor):
    """
    Prints a textual representation of the given CFG to stdout.

    Args:
      cfg: source CFG to be printed.
      ordered: if True (default), print BasicBlocks in order of entry.
    """

    __BLOCK_SEP = "\n\n================================\n\n"

    def __init__(self, cfg: cfg.ControlFlowGraph, ordered: bool = True):
        super().__init__(cfg)
        self.ordered = ordered
        self.blocks = []
        self.source.accept(self)

    def visit_ControlFlowGraph(self, cfg):
        """
        Visit the CFG root
        """
        pass

    def visit_BasicBlock(self, block):
        """
        Visit a BasicBlock in the CFG
        """
        self.blocks.append((block.entry, str(block)))

    def export(self):
        """
        Print a textual representation of the input CFG to stdout.
        """
        if self.ordered:
            self.blocks.sort(key=lambda n: n[0])
        blocks = self.__BLOCK_SEP.join(n[1] for n in self.blocks)
        return blocks