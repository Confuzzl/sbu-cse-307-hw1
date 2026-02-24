class IntLiteral:
    def __init__(self, value: int):
        self.value = value

    def __repr__(self):
        return f"IntLiteral({self.value})"


class BoolLiteral:
    def __init__(self, value: bool):
        self.value = value

    def __repr__(self):
        return f"BoolLiteral({self.value})"


class Variable:
    pass


class BinaryOp:
    def __init__(self, op: str, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"BinaryOp({self.op}, {self.left}, {self.right})"


class UnaryOp:
    def __init__(self, op: str, operand):
        self.op = op
        self.operand = operand

    def __repr__(self):
        return f"UnaryOp({self.op}, {self.operand})"


class Let:
    pass


class If:
    def __init__(self, cond, yes, no):
        self.cond = cond
        self.yes = yes
        self.no = no


class Fun:
    pass


class App:
    pass


class AST:
    def __repr__(self):
        return f"AST()"
