
'''
    An edge occurs on depth changes.
    The info of an edge consists of the function info
'''
from ast import Dict
from sre_constants import SUCCESS
from typing import Iterable, List
from xml.etree.ElementPath import ops

from dasm import Funclog

class Edge():
    def __init__(self, trace : Funclog = None ) -> None:
        self.trace = trace
        self._calltype = trace._ct
        self._depth = trace._depth
        self._from = trace._from
        self._to = trace._to
        self._val = trace._val
        self._gas = trace._gas
        self._input = trace._input
        self._output = trace._output
    def __str__(self) -> str:
        return "Edge{CallType: " + self._calltype + ", Depth: " + self._depth + ", From: " + self._from + ", To: " + self._to + ", Val: " + self._val + ", Gas: " + self._gas + ", Input: " + self._input + ", Output: " + self._output + "}"

class Block():
    def __init__(self, functrace : Dict = None, prev : 'Block' = None, succ : 'Block' = None) -> None:
        self.prev = prev
        self.succ = succ
        self.ops = []
        self.functrace = Edge(functrace)
        self.prev = prev

    def insert_op(self,op):
        self.ops.append(op)

    def __str__(self, debug = 0) -> str:
        builder = lambda x,y,z: f"OpBody ({hex(hash(self))}): Previous: " + x + ", Successors: " + y + ", Context: " + str(z)

        prev =  hex(hash(self.prev))
        succ = hex(hash(self.succ))

        if not debug:
            return builder(prev, succ, self.functrace)

        ops_str = ""

        if debug:
            ops_str += "\n".join([str((i._opcode, i._pc, i._depth)) for i in self.ops[:min(len(self.ops), 5)]])
            
            if len(ops_str) > 10:
                ops_str += "\n...\n"
                ops_str += "\n".join([str((i._opcode, i._pc, i._depth)) for i in self.ops[-5:]])

        return builder(prev, succ, self.functrace) + ", Oplogs: " + ops_str

def build_blocks(logs):
    assert len(logs.functrace) > 0

    functrace_ctr = 0
    original_block = Block(logs.functrace[functrace_ctr])
    current_block = original_block
    
    current_block.insert_op(logs.optrace[0])
    functrace_ctr += 1

    for i, op in enumerate(logs.optrace[1:]):
        # signifies call into external contract if pc == 0
        if op._pc == 0:
            
            temp_block = Block(logs.functrace[functrace_ctr])
            temp_block.prev = current_block
            current_block.succ = temp_block
            current_block = temp_block
            
            functrace_ctr += 1

        # if depth change downwards, we returned from a call. create new block in case, dont increment func ctf
        # opcode is actually logs[i=1], so we can just check whether log[i] depth is diff, not log[i-1]
        if op._depth < logs.optrace[i]._depth:
            temp_block = Block(logs.functrace[functrace_ctr-1])
            temp_block.prev = current_block
            current_block.succ = temp_block
            current_block = temp_block

        current_block.insert_op(op)


    return original_block