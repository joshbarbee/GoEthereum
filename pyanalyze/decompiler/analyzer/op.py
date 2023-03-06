from typing import List, Dict, Callable, Tuple, Iterator
import copy
import pandas as pd

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
        address: str = None
    ) -> None:
        self.op_index: int = op_index
        self.call_index: int = call_index
        self.pc: int = pc
        self.op: str = op
        self.depth: int = depth
        self.use_vars: List[Variable] = use_vars
        self.def_var: Variable = def_var
        self.address: str = address

    def __repr__(self) -> str:
        return f"{self.op}:{self.op_index}"

    def __str__(self) -> str:
        fstr = f"{self.pc}: {self.op}, {self.op_index}, {self.call_index}, {self.depth}, {self.def_var.symbol if self.def_var else ''}"

        return fstr

class OpChain(List):
    def __init__(self, *args, **kwargs):
        self.cached_chain = None
        super().__init__(*args, **kwargs)

    @classmethod
    def from_chain(cls, chain : 'OpChain'):
        new = cls()
        new.cached_chain = chain.copy()

        return new

    def remove(self, __value) -> bool:
        super().remove(__value)

        return bool(len(self))


class OpView(Dict):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.first_link = True
        self.addresses: List[str] = []

    def add_op(self, op: Op) -> None:
        self[op] = OpChain()

    def link_ops(self, other: "OpView", save_links : bool = False, **kwargs: Callable):
        """Links one OpView to another OpView based on the filters
        set by kwargs. kwargs should be a 2-parameter callable that
        returns a boolean, such as operator.GT. A link will be created
        between each op in self and each op in other that satisfy the
        passed filters.

        Args:
            other (OpView): the OpView to link to.
        """

        for op1 in list(self.keys()):
            if not self.first_link and len(self[op1]) == 0:
                del self[op1]
            if save_links:
                self[op1] = OpChain.from_chain(self[op1])
            else:
                self[op1] = OpChain()

            for op2 in other:
                if all(
                    [
                        func(getattr(op1, key), getattr(op2, key))
                        for key, func in kwargs.items()
                    ]
                ):
                    self[op1].append(op2)
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
        """Filter the Op-List in-place via a comparision to a
        discrete value.

        Examples:
            self.filter(call_index=(lambda x,y: x > y, 2))
            self.filter(address=(lambda x,y: x == y, 0x000...02))
        """
        for op in list(self.keys()):
            if not all([func(getattr(op, key), value) for key, (func, value) in kwargs.items()]):
                del self[op] # will get gced later if __iter__ called again

    def reduce_links(self, **kwargs: Callable):
        """Reduces linkages between self and linked opcodes, based on the
        requirements set as filters via kwargs. Each kwargs should be a
        2-parameter callable with a name equal to an attribute in self
        and the linked attributes.
        """
        
        for op in list(self.keys()):
            for link in self[op].copy():
                if not all(
                    [
                        func(getattr(op, key), getattr(link, key))
                        for key, func in kwargs.items()
                    ]):
                    
                    if not self[op].remove(link):
                        del self[op]
                        break

    def filter_value(self, value: int):
        """Filters opcodes based on the value associated with a def_var
        created by the opcode

        Args:
            value (int): the discrete integer value to compare to
        """

        self = {op: self[op] for op in self.keys() if op.def_var.value == value}

    def reduce_value(
        self,
        self_def_var: bool = True,
        self_use_vi: int = None,
        link_def_var: bool = True,
        link_use_vi: int = None,
    ) -> None:
        """Reduces on def/used value equalities between self and linked ops.

        In the default case, each opcode in the OpView is compared to with each
        linked opcode. If the def_var of self has a value unequal to the def_var
        of a linked op, the linkage is removed.

        Other parameters modify whether a defined variable or used variable is
        analyzed for self and the linked variables.

        Args:
            self_def_var (bool, optional): Whether to check the value of defined
            variables for self opcodes. Defaults to True.
            self_use_vi (int, optional): The specific indice of the use variable
            to check if known and self_def_var is False. Defaults to None.
            link_def_var (bool, optional): Whether to check the value of a defined
            variables for linked opcodes. Defaults to True.
            link_use_vi (int, optional): The specific indice of the use variable
            to check if known and link_def_var is False. Defaults to None.
        """

        for op in list(self.keys()):
            for link in self[op].copy():
                if self_def_var and link_def_var:
                    if link.def_var.value != op.def_var.value:
                        if not self[op].remove(link):
                            del self[op]
                            break
                elif not self_def_var and link_def_var:
                    if self_use_vi is not None and op.use_vars[self_use_vi].value != link.def_var.value:
                        if not self[op].remove(link):
                            del self[op]
                            break
                    elif self_use_vi:
                        if not any(
                            usevar.value == op.def_var.value
                            for usevar in link.use_vars
                        ):
                            if not self[op].remove(link):
                                del self[op]
                                break
                elif self_def_var and not link_def_var:
                    if (
                        link_use_vi is not None
                        and op.def_var.value != link.use_vars[link_use_vi].value
                    ):
                        if not self[op].remove(link):
                            del self[op]
                            break
                    elif link_use_vi is None:
                        if not any(
                            usevar.value == op.def_var.value
                            for usevar in link.use_vars
                        ):
                            if not self[op].remove(link):
                                del self[op]
                                break
                else:
                    if (link_use_vi is not None and self_use_vi is not None):
                        if op.use_vars[self_use_vi].value != link.use_vars[link_use_vi].value:
                            if not self[op].remove(link):
                                    del self[op]
                                    break
                    elif self_use_vi is None and link_use_vi is not None:
                        if any(
                            usevar.value == link.use_vars[link_use_vi].value
                            for usevar in op.use_vars
                        ):
                            break
                        else:
                            if not self[op].remove(link):
                                del self[op]
                                break
                    elif self_use_vi is not None and link_use_vi is None:
                        if any(
                            usevar.value == op.use_vars[self_use_vi].value
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
                                usevar.value == op_usevars.value
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
        """Reduces linkages between self opcodes and linked opcodes based
        on whether a connection exists between variables defined / used by
        self and defined/used by linked variables such that the linked variables
        are descendants of variables in the self OpView

        If linked_op has a used variable that is a descendant of some defined
        variable in self, then it is a descendant, and it remains in the linkages.
            *If self_def_var=True and link_def_var = False

        Args:
            self_def_var (bool, optional): Whether to check the value of defined
            variables for self opcodes. Defaults to True.
            self_use_vi (int, optional): The specific indice of the use variable
            to check if known and self_def_var is False. Defaults to None.
            link_def_var (bool, optional): Whether to check the value of a defined
            variables for linked opcodes. Defaults to True.
            link_use_vi (int, optional): The specific indice of the use variable
            to check if known and link_def_var is False. Defaults to None.
        """

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
                    if not any(
                        [usevar in linked_vars for usevar in link.use_vars]
                    ):
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
        """Reduces linkages between self opcodes and linked opcodes based
        on whether a connection exists between variables defined / used by
        self and defined/used by linked variables such that the linked variables
        are ancestors of variables in the self OpView

        If linked_op has a used variable that is an ancesotr of some defined
        variable in self, then it is a ancestor, and it remains in the linkages.
            *If self_def_var=True and link_def_var = False

        Args:
            self_def_var (bool, optional): Whether to check the value of defined
            variables for self opcodes. Defaults to True.
            self_use_vi (int, optional): The specific indice of the use variable
            to check if known and self_def_var is False. Defaults to None.
            link_def_var (bool, optional): Whether to check the value of a defined
            variables for linked opcodes. Defaults to True.
            link_use_vi (int, optional): The specific indice of the use variable
            to check if known and link_def_var is False. Defaults to None.
        """

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
                    if not any(
                        [usevar in linked_vars for usevar in link.use_vars]
                    ):
                        if not self[op].remove(link):
                            del self[op]
                            break   

    def reduce_dominator(
        self, link_def_var: bool = True, link_use_vi: int = None
    ) -> None:
        """Reduces linkages to only the set of links where a variable
        used by a linked opcode is totally dominated by a variable
        used by a self opcode.

        Args:
            link_def_var (bool, optional): Whether to check the defined value
            of the linked variables. Defaults to True.
            link_use_vi (int, optional): The specific indice of the use variable
            to check if known and link_def_var is False. Defaults to None.
        """
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
        """Filters self to only opcodes that were created by a particular
        address

        Args:
            address (str): the address of all the opcodes that should remain
        """

        self = {op: self[op] for op in self.keys() if self.addresses[op.depth] == address}

    def reduce_address(self, both: bool = False) -> None:
        """Reduces all links to only links that originated (in address)
        at the same opcode

        If both is enabled, then both the linked opcode and the opcode in self
        is removed.

        Args:
            both (bool, optional): Whether to delete both self and linked ops
            when no match is found. Defaults to False.
        """

        for op in list(self.keys()):
            op_addr = self.addresses[op.depth]

            for link in self[op].copy():
                linked_addr = self.addresses[link.depth]
                if linked_addr != op_addr:
                    if both:
                        del self.link_ops[op]
                    else:
                        if not self[op].remove(link):
                            del self[op]
                            break

    def export_links(self, filepath=None, cached_links = False) -> None:
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
                if cached_links:
                    for clink in sorted(links.cached_chain, key=lambda c: c.op_index):
                        for link in links:
                            f.write(f"{op.op_index}, {clink.op_index}, {op.depth}, {op.call_index}, {link.op_index}, {link.depth}, {link.call_index}, {self.addresses[op.depth]}, {self.addresses[link.depth]}\n")
                else:
                    for link in links:
                        f.write(f"{op.op_index}, {op.depth}, {op.call_index}, {link.op_index}, {link.depth}, {link.call_index}, {self.addresses[op.depth]}, {self.addresses[link.depth]}\n")
