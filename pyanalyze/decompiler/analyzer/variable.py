from typing import List


class Variable:
    """Representation of Metavariable. Maintains digraph data structure to compute
    relationships between variables like def/use. 
    """
    def __init__(self, symbol: str, value: int, preds: List["Variable"] = []) -> None:
        self.symbol = symbol
        self.value = value
        self.succs = []
        self.preds = preds

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Variable):
            if self.symbol == __o.symbol:
                return True
            return False
        elif isinstance(__o, str):
            if self.symbol == __o:
                return True
            return False

        raise NotImplementedError()

    def is_parent(self, parent_vars: List["Variable"] | "Variable") -> bool:
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

    def is_child(self, child_vars: List["Variable"] | "Variable") -> bool:
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
            queue.extend(node.succs)

        return False

    def get_descendants(self) -> List["Variable"]:
        """Returns all children and any descendants
        of self's children as a list

        Returns:
            List['Variable]: all Variable descendants of self
        """

        descendants = []

        for var in self.succs:
            descendants.append(var)
            descendants.extend(var.get_descendants())

        return descendants

    def get_ancestors(self, stop: "Variable" = None):
        if stop is None:
            return self.preds + [i for var in self.preds for i in var.get_ancestors()]

        if self == stop:
            return []

        return self.preds + [
            i for var in self.preds for i in var.get_ancestors(stop=stop)
        ]
