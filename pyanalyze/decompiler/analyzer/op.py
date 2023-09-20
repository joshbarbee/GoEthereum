from typing import List, Dict, Callable, Tuple
import copy
from decompiler.analyzer.variable import Variable


class Op:
    def __init__(
        self,
        op_index: int,
        call_index: int,
        pc: int,
        op: str,
        depth: int,
        use_vars: List[Variable] = [],
        def_var: Variable = None,
    ) -> None:
        self.op_index: int = op_index
        self.call_index: int = call_index
        self.pc: int = pc
        self.op: str = op
        self.depth: int = depth
        self.use_vars: List[Variable] = use_vars
        self.def_var: Variable = def_var

    def __repr__(self) -> str:
        return f"{self.op}:{self.op_index}"

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Op):
            if __o.op_index == self.op_index:
                return True
            return False
        raise NotImplementedError()

    def __hash__(self) -> int:
        return hash(self.op_index)

# class OpBALANCE

# class OpBLOCKHASH

# class OpCALL

# class OpCALLCODE

# class OpCOINBAASE

# class OpCREATE

# class OpDELEGATE

# class OpDIFFICULTY

# class OpEQ

# class OpEXTCODESIZE

# class OpGASLIMIT

# class OpJUMP

# class OpJUMPI

# class OpNUMBER

# class OpORIGIN

# class OpRETURN

# class OpREVERT

# class OpSELFDESTRUCT

# class OpSLOAD

# class OpSSTORE

# class OpSTATICCALL

# class OpTIMESTAMP

class OpChain(List):
    def __init__(self, *args, **kwargs):
        self.cached_chain = None
        super().__init__(*args, **kwargs)

    @classmethod
    def from_chain(cls, chain: "OpChain"):
        new = cls()
        new.cached_chain = chain.copy()

        return new

    def remove(self, __value) -> bool:
        super().remove(__value)

        return bool(len(self))


class OpView(Dict[Op, OpChain]):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.first_link = True

        self.addresses: List[str] = []

        self.depth_max = 0
        self.call_max = 0

    def __sub__(self, other):
        nv = OpView({key: self[key] for key in set(self.keys()) - set(other.keys())})
        nv.addresses = self.addresses
        return nv

    def add_op(self, op: Op) -> None:
        self[op] = OpChain()
        self.depth_max = max(self.depth_max, op.depth)
        self.call_max = max(self.call_max, op.call_index)

    def __iter__(self):
        for op in self.keys():
            yield op

    def link_ops(self, other: "OpView", save_links: bool = False, **kwargs: Callable):
        cached_links = {}
        
        def find_bounds(filters, values, max_bound = 1024, min_bound = 0):
            bounds = {}
            
            for (key, func), bound in zip(filters.items(), values):
                if key not in bounds:
                    bounds[key] = [min_bound, max_bound]

                if not func(bounds[key][0], bound):
                    bounds[key][0] = bound
                if not func(bounds[key][1], bound):
                    bounds[key][1] = bound
            return bounds
        
        other_keys = other.get_keys(kwargs.keys())
        
        total = 0
        cached = 0

        for op1 in list(self.keys()):
            if not self.first_link and len(self[op1]) == 0:
                del self[op1]
            if save_links:
                self[op1] = OpChain.from_chain(self[op1])
            else:
                self[op1] = OpChain()

            cached_val = tuple(getattr(op1, key) for key in kwargs.keys())

            if cached_val not in cached_links:
                cached_links[cached_val] = op1
            
                for attrs in other_keys.keys():
                    if all(
                        [
                            func(getattr(op1, key), attrs[idx])
                            for idx, (key, func) in enumerate(kwargs.items())
                        ]
                    ):      
                        total += 1
                        self[op1].extend(other_keys[attrs])              
            elif len(self[op1]) != 0:
                for op in self[cached_links[cached_val]]:
                    cached += 1
                    self[op1].append(op)

            if len(self[op1]) == 0:
                del self[op1]

        self.first_link = False

    def copy(self) -> "OpView":
        return copy.deepcopy(self)

    def __str__(self) -> str:
        output = ""

        for op, links in self:
            used_vars = " ".join([str(link) for link in links])
            output += f"\n{op} Links to: {used_vars}"

        return output

    def filter(self, **kwargs: Tuple[Callable, int | str]):
        def find_bounds(filters, max_bound = 1024, min_bound = 0):
            bounds = {}
            
            for key, (func, bound) in filters.items():
                if key not in bounds:
                    bounds[key] = [min_bound, max_bound]

                if not func(bounds[key][0], bound):
                    bounds[key][0] = bound
                if not func(bounds[key][1], bound):
                    bounds[key][1] = bound
            return bounds
        bounds = find_bounds(kwargs)

        for op in list(self.keys()):
            if not all(
                [getattr(op, key) >= lower and getattr(op, key) <= upper for key, (lower, upper) in bounds.items()]
            ):
                del self[op]  # will get gced later if __iter__ called again
    
    def get_keys(self, keys : List[str]) -> Dict[Dict[str,int],Op]:
        res = {}

        for op in self:
            idx = tuple(getattr(op, key) for key in keys)
            if idx not in res:
                res[idx] = [op]
            else:
                res[idx].append(op)

        return res

    def reduce_links(self, **kwargs: Callable):
        for op in list(self.keys()):
            for link in self[op].copy():
                if not all(
                    [
                        func(getattr(op, key), getattr(link, key))
                        for key, func in kwargs.items()
                    ]
                ):
                    if not self[op].remove(link):
                        del self[op]
                        break

    def filter_value(
        self, value: int, oper: Callable, def_var: bool = True, use_vi: int = None
    ):
        if def_var:
            self = {op: self[op] for op in self.keys() if oper(op.def_var.value, value)}
        elif use_vi is not None:
            self = {
                op: self[op]
                for op in self.keys()
                if oper(op.use_vars[use_vi].value, value)
            }
        else:
            self = {
                op: self[op]
                for op in self.keys()
                for usevar in op.usevars
                if any(oper(usevar.value, value))
            }

    def reduce_value(
        self,
        oper: Callable,
        self_def_var: bool = True,
        self_use_vi: int = None,
        link_def_var: bool = True,
        link_use_vi: int = None,
    ) -> None:
        for op in list(self.keys()):
            for link in self[op].copy():
                if self_def_var and link_def_var:
                    if oper(
                        op.def_var.value,
                        link.def_var.value,
                    ):
                        if not self[op].remove(link):
                            del self[op]
                            break
                elif not self_def_var and link_def_var:
                    if self_use_vi is not None and oper(
                        op.use_vars[self_use_vi].value, link.def_var.value
                    ):
                        if not self[op].remove(link):
                            del self[op]
                            break
                    elif self_use_vi:
                        if not any(
                            oper(op.def_var.value, usevar.value)
                            for usevar in link.use_vars
                        ):
                            if not self[op].remove(link):
                                del self[op]
                                break
                elif self_def_var and not link_def_var:
                    if link_use_vi is not None and oper(
                        op.def_var.value, link.use_vars[link_use_vi].value
                    ):
                        if not self[op].remove(link):
                            del self[op]
                            break
                    elif link_use_vi is None:
                        if not any(
                            oper(op.def_var.value, usevar.value)
                            for usevar in link.use_vars
                        ):
                            if not self[op].remove(link):
                                del self[op]
                                break
                else:
                    if link_use_vi is not None and self_use_vi is not None:
                        if oper(
                            op.use_vars[self_use_vi].value,
                            link.use_vars[link_use_vi].value,
                        ):
                            if not self[op].remove(link):
                                del self[op]
                                break
                    elif self_use_vi is None and link_use_vi is not None:
                        if any(
                            oper(usevar.value, link.use_vars[link_use_vi].value)
                            for usevar in op.use_vars
                        ):
                            break
                        else:
                            if not self[op].remove(link):
                                del self[op]
                                break
                    elif self_use_vi is not None and link_use_vi is None:
                        if any(
                            oper(op.use_vars[self_use_vi].value, usevar.value)
                            for usevar in link.use_vars
                        ):
                            break
                        else:
                            if not self[op].remove(link):
                                del self[op]
                                break
                    else:
                        for op_usevars in op.use_vars:
                            if any(
                                oper(op_usevars.value, usevar.value)
                                for usevar in link.use_vars
                            ):
                                break
                            else:
                                if not self[op].remove(link):
                                    del self[op]
                                    break

    def reduce_descendant(
        self,
        self_def_var: bool = True,
        self_use_vi: int = None,
        link_def_var: bool = True,
        link_use_vi: int = None,
    ):
        for op in list(self.keys()):
            if self_def_var:
                linked_vars = op.def_var.get_descendants()
            elif self_def_var and self_use_vi is not None:
                linked_vars = op.use_vars[self_use_vi].get_descendants()
            else:
                linked_vars = [
                    var for usevar in op.use_vars for var in usevar.get_descendants()
                ]

            for link in self[op].copy():
                if link_def_var and link.def_var not in linked_vars:
                    if not self[op].remove(link):
                        del self[op]
                        break
                elif (
                    not link_def_var
                    and link_use_vi is not None
                    and link.use_vars[link_use_vi] not in linked_vars
                ):
                    if not self[op].remove(link):
                        del self[op]
                        break
                elif not link_def_var and link_use_vi is None:
                    if not any([usevar in linked_vars for usevar in link.use_vars]):
                        if not self[op].remove(link):
                            del self[op]
                            break

    def reduce_ancestor(
        self,
        self_def_var: bool = True,
        self_use_vi: int = None,
        link_def_var: bool = True,
        link_use_vi: int = None,
    ) -> None:
        for op in list(self.keys()):
            if self_def_var:
                linked_vars = op.def_var.get_ancestors()
            elif self_def_var and self_use_vi is not None:
                linked_vars = op.use_vars[self_use_vi].get_ancestors()
            else:
                linked_vars = [
                    var for usevar in op.use_vars for var in usevar.get_ancestors()
                ]

            for link in self[op].copy():
                if link_def_var and link.def_var not in linked_vars:
                    if not self[op].remove(link):
                        del self[op]
                        break
                elif (
                    not link_def_var
                    and link_use_vi is not None
                    and link.use_vars[link_use_vi] not in linked_vars
                ):
                    if not self[op].remove(link):
                        del self[op]
                        break
                elif not link_def_var and link_use_vi is None:
                    if not any([usevar in linked_vars for usevar in link.use_vars]):
                        if not self[op].remove(link):
                            del self[op]
                            break

    def reduce_dominator(
        self, link_def_var: bool = True, link_use_vi: int = None
    ) -> None:
        for op in list(self.keys()):
            op_vars = set(op.def_var.get_descendants())

            for link in self[op].copy():
                if link_def_var:
                    linked_vars = set(link.def_var.get_ancestors(op))
                    if linked_vars.intersection(op_vars) != linked_vars:
                        if not self[op].remove(link):
                            del self[op]
                            break
                elif link_use_vi is not None:
                    linked_vars = set(link.use_vars[link_use_vi].get_ancestors(op))
                    if linked_vars.intersection(op_vars) != linked_vars:
                        if not self[op].remove(link):
                            del self[op]
                            break
                else:
                    linked_vars = set(
                        ancestor
                        for usevar in link.use_vars
                        for ancestor in usevar.get_ancestors(op)
                    )
                    if linked_vars.intersection(op_vars) != linked_vars:
                        if not self[op].remove(link):
                            del self[op]
                            break

    def filter_address(self, address: str) -> None:
        self = {
            op: self[op] for op in self.keys() if self.addresses[op.depth] == address
        }

    def reduce_address(self) -> None:
        for op in list(self.keys()):
            op_addr = self.addresses[op.depth]

            for link in self[op].copy():
                linked_addr = self.addresses[link.depth]
                if linked_addr != op_addr:
                    if not self[op].remove(link):
                        del self[op]
                        break

    def export(self, filepath=None, cached_links=False) -> None:
        if filepath is None:
            for op, links in self.items():
                used_vars = " ".join([str(link) for link in links])
                print(f"\n{op} Links to: {used_vars}")
            return

        if len(self) == 0:
            print("Attempting to export with no data")
            return

        with open(filepath, "w") as f:
            for op, links in self.items():
                if len(links) == 0:
                    if op.op in {"CALL", "STATICCALL", "CALLCODE", "DELEGATECALL"}:
                        f.write(
                            f"{op.op_index}, {op.depth}, {op.call_index}, {self.addresses[op.depth+1]}\n"
                        )
                    else:
                        f.write(
                            f"{op.op_index}, {op.depth}, {op.call_index}, {self.addresses[op.depth]}\n"
                        )
                elif cached_links:
                    for clink in sorted(links.cached_chain, key=lambda c: c.op_index):
                        for link in links:
                            f.write(
                                f"{op.op_index}, {clink.op_index}, {op.depth}, {op.call_index}, {link.op_index}, {link.depth}, {link.call_index}, {self.addresses[op.depth]}, {self.addresses[link.depth]}\n"
                            )
                else:
                    for link in links:
                        f.write(
                            f"{op.op_index}, {op.depth}, {op.call_index}, {link.op_index}, {link.depth}, {link.call_index}, {self.addresses[op.depth]}, {self.addresses[link.depth]}\n"
                        )
