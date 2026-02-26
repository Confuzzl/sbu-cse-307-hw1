from typing import assert_never

from tokens import Token, TokenType

import re


class LexError(Exception):
    def __init__(self, msg: str, pos: tuple[int, int]):
        super().__init__(msg)
        self.msg = msg
        self.line, self.col = pos


TOKEN_SPECS = (
    ("COMMENT_START", r"\(\*"),
    ("COMMENT_END", r"\*\)"),
    ("WHITESPACE", r"\s+"),
    ("KEYWORD", "|".join(("let", "in", "if", "then", "else", "fun", "rec"))),
    ("BOOL", r"false|true"),
    ("INT", r"\d+"),
    ("DELIMITER", r"\(|\)"),
    ("OPERATOR", "|".join((r"not", r"->", r"<>", r"<=", r">=",
     r"<", r">", r"\+", r"-", r"\*", r"/", r"=", r"&&", r"\|\|"))),
    ("ID", r"[a-z]\w*"),
    ("UNEXPECTED", r".")
)
REGEX = "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECS)


def lex(source: str) -> list[Token]:
    out: list[Token] = []

    line = 1
    line_start = 0

    comment_depth = 0
    comment_pos = (0, 0)

    for match in re.finditer(REGEX, source):
        kind = match.lastgroup
        val = match.group()
        col = match.start() - line_start + 1

        # print(f"{kind=} {val=}")

        match kind:
            case "COMMENT_START":
                comment_depth += 1
                comment_pos = (line, col)
            case "COMMENT_END":
                comment_depth -= 1
                if comment_depth < 0:
                    raise LexError("unmatched comment close", (line, col))
            case _:
                if comment_depth == 0:
                    match kind:
                        case "WHITESPACE":
                            if (nls := val.count("\n")) != 0:
                                line += nls
                                line_start = match.end()
                        case "UNEXPECTED":
                            raise LexError(
                                f"found unexpected char {val!r}", (line, col))
                        case None:
                            assert False  # dont think this is possible
                        case _:
                            out.append(
                                Token(TokenType[kind], val, (line, col)))
                else:
                    pass

    if comment_depth != 0:
        raise LexError("unclosed comment", comment_pos)
    return out
