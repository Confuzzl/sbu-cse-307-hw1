from enum import IntEnum


class TokenType(IntEnum):
    INT = 0
    BOOL = 1
    ID = 2
    KEYWORD = 3
    OPERATOR = 4
    DELIMITER = 5


class Token:
    def __init__(self, type: TokenType, value: str, pos: tuple[int, int, int]):
        self.type = type
        self.value = value
        self.pos, self.line, self.column = pos

    def __repr__(self) -> str:
        return f"Token({self.type.name}, '{self.value}', [{self.line}:{self.column}])"
