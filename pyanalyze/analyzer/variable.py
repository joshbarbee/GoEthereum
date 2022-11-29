from typing import List, Union

class Op():
    def __init__(self, op : str, origin_addr : str, call_number : int , def_loc : int):
        self.op : str = op
        self.origin_addr : str = origin_addr
        self.call_num : int = call_number
        self.def_loc : int = def_loc

class Variable():
    def __init__(self, value : int, metavar : str, origin_addr : str, call_number : int, def_loc : int, *args):
        self.value = value
        self.metavar : str = metavar
        self.origin_addr : str = origin_addr
        self.def_loc : int = def_loc
        self.call_num : int = call_number

        self.def_vars : List[Variable] = []
        self.use_vars : List[Variable] = args

        self.def_ops : List[Op] = []
        self.use_ops : List[Op] = []

    def add_use(self, other : Union['Variable', Op]):
        if isinstance(other, Op):
            self.use_ops.append(other)
        elif isinstance(other, self):
            self.use_vars.append(other)
        else:
            raise NotImplemented