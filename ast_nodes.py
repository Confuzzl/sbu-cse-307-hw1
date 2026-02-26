from tokens import dataclass

type Expression = "IntLiteral | BoolLiteral | Variable | BinaryOp | UnaryOp | Let | If | Fun | App"


@dataclass
class IntLiteral:
    value: int

    def __repr__(self) -> str:
        return f"IntLiteral({self.value})"


@dataclass
class BoolLiteral:
    value: bool

    def __repr__(self) -> str:
        return f"BoolLiteral({self.value})"


@dataclass
class Variable:
    name: str

    def __repr__(self) -> str:
        return f"Variable({self.name!r})"


@dataclass
class BinaryOp:
    op: str
    left: Expression
    right: Expression

    def __repr__(self) -> str:
        return f"BinaryOp({self.op!r}, {self.left!r}, {self.right!r})"


@dataclass
class UnaryOp:
    op: str
    operand: Expression

    def __repr__(self) -> str:
        return f"UnaryOp({self.op!r}, {self.operand!r})"


@dataclass
class Let:
    recursive: bool
    name: Variable
    params: list[Variable]
    binding: Expression
    inside: Expression

    def __repr__(self) -> str:
        return f"Let({self.recursive}, {self.name!r}, {self.params}, {self.binding!r}, {self.inside!r})"


@dataclass
class If:
    cond: Expression
    yes: Expression
    no: Expression

    def __repr__(self) -> str:
        return f"If({self.cond!r}, {self.yes!r}, {self.no!r})"


@dataclass
class Fun:
    params: list[Variable]
    definition: Expression

    def __repr__(self) -> str:
        return f"Fun({self.params}, {self.definition!r})"


@dataclass
class App:
    name: Variable
    params: list[Expression]

    def __repr__(self) -> str:
        return f"App({self.name!r}, {self.params})"
