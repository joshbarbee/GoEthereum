from dataclasses import dataclass
from typing import List
import logging


'''
    BlockParser parses a given block number, fetching each logged tx from
    the mongodb database, then parses the optrace, functrace, and eventrace from each 
    block
'''
class BlockParser():
    def __init__(self, block: int, logs : dict) -> None:
        self.block : int = block
        self.raw = logs
        self.txs : List = []
        self.parse()
    
    def parse(self):
        if len(self.raw) < 1:
            logging.warning("No transactions in block ", self.block, ". Ensure that the mongodb logger has an entry for the block")
            return

        for tx in self.raw:
            t = TxParser()
            t.parse(tx)
            self.txs.append(t)


class TxParser():
    def __init__(self) -> None:
        self.block = 0 
        self.hash = "0x0"
        self.functrace = []
        self.optrace = []
        self.eventtrace = []
        self._from = "0x0"
        self._to = "0x0"
        self.value = 0
        self.trace = []

    '''
        parses a transaction, extracts all info from mongodb
        todo: better key checking ? keychecking at all?
    '''
    def parse(self, logs : dict) -> None:
        assert "from" in logs
        assert "to" in logs
        assert "tx" in logs
        assert "functrace" in logs
        assert "eventtrace" in logs
        assert "optrace" in logs 
        assert "value" in logs

        self._from = logs['from']
        self._to = logs['to']
        self.hash = logs['tx']
        self.value = int(logs['value'])

        self._parse_optrace(logs['optrace'])
        self._parse_functrace(logs['functrace'])
        self._parse_eventtrace(logs['eventtrace'])

    '''
        Parses a op trace for the given transaction into a python array.
        The oplogs are split on newlines, with each value of the oplog comma seperated.
        The ordering of the trace is as follows: depth, op, gas, cost, return
    '''
    def _parse_optrace(self, optrace : str) -> None:
        # drop first log, since that is specifying csv info, but we know ordering 
        for log in optrace.split("\n")[1:]:
            vals = log.split(",")
            if len(vals) < 6:
                print("Unable to process instruction, invalid number of args in optrace: ", vals)
                raise RuntimeError()
            op = Oplog(int(vals[0]), int(vals[1]), vals[2], vals[3], vals[4], vals[5])
            self.optrace.append(op)
        
    '''
        Parses the function trace for the given tx into an array of functraces. The ordering of items in
        functrace is as follows: calltype,depth,from,to,val,gas,input,output
    '''
    def _parse_functrace(self, functrace : str) -> None:
        for log in functrace.split("\n")[1:]:
            vals = log.split(",")

            if len(vals) != 10:
                print("Unable to process tx, invalid number of args in functrace", vals)
                raise RuntimeError()

            func = Funclog(int(vals[0]), vals[1], vals[2], vals[3], vals[4], vals[5], vals[6], vals[7], vals[8])
            self.functrace.append(func)

    '''
        Parses the event trace for the given tx content into an array of event traces. The event trace
        logs the following info, ordered: address,topics,data
    '''
    def _parse_eventtrace(self, eventtrace : str) -> None:
        for log in eventtrace.split("\n")[1:]:
            vals = log.split(",")

            if len(vals) != 5:
                print("Unable to process tx, invalid number of args in eventtrace", eventtrace)
                raise RuntimeError()

            event = Eventlog(vals[0], vals[1], vals[2],vals[3],vals[4])
            self.eventtrace.append(event)


@dataclass
class Oplog:
    _pc : int
    _depth : int
    _opcode : str
    _gas : int
    _cost : int
    _ret : str

@dataclass
class Funclog:
    _index: int
    _ct: str
    _depth: int
    _to: str
    _from : str
    _val: int
    _gas: int
    _input: str
    _output: str

@dataclass
class Eventlog:
    _addr: str
    _topics: List
    _data: str
    _type: str
    _function: str