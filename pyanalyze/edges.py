
'''
    An edge occurs on depth changes.
    The info of an edge consists of the function info
'''

from typing import Iterable

from numpy import block

class Edge():
    def __init__(self, trace = None, prev = None, succ = None) -> None:
        self.prev = [prev]
        self.succ = [succ]
        self.trace = trace
        
        self._calltype = trace._ct
        self._depth = trace._depth
        self._from = trace._from
        self._to = trace._to
        self._val = trace._val
        self._gas = trace._gas
        self._input = trace._input
        self._output = trace._output
        self.prev = prev

    def __str__(self) -> str:
        return "Edge: Prev:" + hex(hash(self.prev)) + ", Succ: " + hex(hash(self.succ)) + ", CallType: " + self._calltype + ", Depth: " + self._depth + ", From: " + self._from + ", To: " + self._to + ", Val: " + self._val + ", Gas: " + self._gas + ", Input: " + self._input + ", Output: " + self._output

class Block():
    def __init__(self, prev = None, succ = None) -> None:
        self.prev = [prev]
        self.succ = [succ]
        self.ops = []

    def insert_op(self,op):
        self.ops.append(op)

    def __str__(self) -> str:
        ops_str = ""

        ops_str += "\n".join([str((i._opcode, i._pc, i._depth)) for i in self.ops[:min(len(self.ops), 5)]])
        
        if len(ops_str) > 10:
            ops_str += "\n...\n"
            ops_str += "\n".join([str((i._opcode, i._pc, i._depth)) for i in self.ops[-5:]])

        return "OpBody: Previous: " + hex(hash(self.prev)) + ", Successor: " + hex(hash(self.succ)) + ", \nOps: " + ops_str

def build_edges(logs):
    assert len(logs.functrace) > 0

    current_edge = Edge(None,logs.functrace[0])
    current_block = Block(current_edge)  

    current_edge.succ = current_block
    current_block.prev = current_edge

    original_edge = current_edge

    functrace_ctr = 1
    for i, op in enumerate(logs.optrace):
        if op._depth != logs.optrace[i-1]._depth:
            tempBlock = Block()
            tempBlock.prev = current_edge

            tempEdge = Edge(None, logs.functrace[functrace_ctr])
            tempEdge.prev = current_block
            tempEdge.succ = tempBlock

            current_block = tempBlock
            current_edge = tempEdge

            if (op._depth < logs.optrace[i-1]._depth):
                functrace_ctr+=1

        current_block.insert_op(op)

    return original_edge