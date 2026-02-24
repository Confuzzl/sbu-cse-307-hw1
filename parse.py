from tokens import Token
from ast_nodes import AST


class ParseError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(msg)
        self.msg = msg
        self.line = line
        self.col = col


def parse(tokens: list[Token]) -> AST:
    out = AST()

    return out
