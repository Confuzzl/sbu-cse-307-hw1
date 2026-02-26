from dataclasses import dataclass
from enum import IntEnum


class TokenType(IntEnum):
    INT = 0
    BOOL = 1
    ID = 2
    KEYWORD = 3
    OPERATOR = 4
    DELIMITER = 5


@dataclass
class Token:
    type: TokenType
    value: str
    pos: tuple[int, int]  # (line, col)
