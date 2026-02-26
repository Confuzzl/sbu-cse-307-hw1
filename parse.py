from typing import Callable

from lexer import TokenType
from tokens import Token
from ast_nodes import *


class ParseError(Exception):
    def __init__(self, msg: str, pos: tuple[int, int]):
        super().__init__(msg)
        self.msg = msg
        self.line, self.col = pos


class TokenStream:
    def __init__(self, data: list[Token]):
        self._data = data
        self._i = 0

    def __bool__(self):
        return self._i < len(self._data)

    def _raise_eof(self):
        prev = self._data[self._i - 1]
        raise ParseError("unexpected end of file encountered",
                         (prev.pos[0], prev.pos[1] + len(prev.value)))

    def peek(self):
        if not self:
            self._raise_eof()
        return self._data[self._i]

    def get(self):
        if not self:
            self._raise_eof()
        curr = self.peek()
        self._i += 1
        return curr

    def tell(self):
        if not self:
            self._raise_eof()
        return (self._i, self.peek().pos)

    def seek(self, pos: int):
        self._i = pos

    def __repr__(self) -> str:
        return f"stream at {self.peek()!r}" if self else "stream ended"


def _help_is_keyword(stream: TokenStream, val: str):
    pos, lc = stream.tell()
    tok = stream.get()
    if tok.type == TokenType.KEYWORD and tok.value == val:
        return

    stream.seek(pos)
    raise ParseError(f"expected {val!r} got {tok.value}", lc)


def _help_find_id(stream: TokenStream):
    pos, lc = stream.tell()
    tok = stream.get()
    if tok.type == TokenType.ID:
        return Variable(tok.value)

    stream.seek(pos)
    raise ParseError("expected an identifier here", lc)


def _parse_let_expr(stream: TokenStream) -> Expression | None:
    try:
        _help_is_keyword(stream, "let")
    except ParseError:
        return None

    rec = False
    try:
        _help_is_keyword(stream, "rec")
        rec = True
    except ParseError:
        pass

    name = _help_find_id(stream)
    params = []
    while True:
        pos, lc = stream.tell()
        tok = stream.get()
        if tok.type == TokenType.OPERATOR:
            if tok.value == "=":
                break
            stream.seek(pos)
            raise ParseError(f"expected '=' got {tok.value!r}", lc)
        if tok.type == TokenType.ID:
            params.append(Variable(tok.value))
        else:
            stream.seek(pos)
            raise ParseError(
                f"expected '=' or identifier but got <{tok.type.name}>", lc)

    first = _parse_expr(stream)

    _help_is_keyword(stream, "in")

    second = _parse_expr(stream)

    return Let(rec, name, params, first, second)


def _parse_if_expr(stream: TokenStream) -> Expression | None:
    try:
        _help_is_keyword(stream, "if")
    except ParseError:
        return None

    cond = _parse_expr(stream)

    _help_is_keyword(stream, "then")

    yes = _parse_expr(stream)

    _help_is_keyword(stream, "else")

    no = _parse_expr(stream)

    return If(cond, yes, no)


def _parse_fun_expr(stream: TokenStream) -> Expression | None:
    try:
        _help_is_keyword(stream, "fun")
    except ParseError:
        return None

    params = []
    first = _help_find_id(stream)
    params.append(first)
    while True:
        pos, lc = stream.tell()
        tok = stream.get()
        if tok.type == TokenType.OPERATOR:
            if tok.value == "->":
                break
            stream.seek(pos)
            raise ParseError(f"expected '->' got {repr(tok.value)}", lc)
        if tok.type == TokenType.ID:
            params.append(Variable(tok.value))
        else:
            stream.seek(pos)
            raise ParseError(
                f"expected '->' or identifier but got <{tok.type.name}>", lc)

    result = _parse_expr(stream)

    return Fun(params, result)


def _parse_primary_expr(stream: TokenStream) -> Expression:
    pos, lc = stream.tell()
    first = stream.get()
    match first.type:
        case TokenType.INT:
            return IntLiteral(int(first.value))
        case TokenType.BOOL:
            return BoolLiteral(True if first.value == "true" else False)
        case TokenType.ID:
            return Variable(first.value)
        case TokenType.DELIMITER:
            if first.value != "(":
                stream.seek(pos)
                raise ParseError(f"expected '(' got {repr(first.value)}", lc)
            expr = _parse_expr(stream)
            pos, lc = stream.tell()
            rparen = stream.get()
            if rparen.type != TokenType.DELIMITER:
                raise ParseError(f"expected ')' got <{rparen.type.name}>", lc)
            if rparen.value != ")":
                raise ParseError(f"expected '() got {repr(rparen.value)}", lc)
            return expr
    stream.seek(pos)
    raise ParseError(
        f"expected <primary_expr> got <{first.type.name}>", lc)


def _parse_app_expr(stream: TokenStream) -> Expression:
    fpos, flc = stream.tell()
    first = _parse_primary_expr(stream)
    app_expr: None | App = None

    while stream:
        pos, lc = stream.tell()
        try:
            expr = _parse_primary_expr(stream)
        except ParseError:
            stream.seek(pos)
            return first if app_expr is None else app_expr
        if not isinstance(first, Variable):
            raise ParseError(
                "function application must start with identifier", flc)
        if app_expr is None:
            app_expr = App(first, [expr])
        else:
            app_expr.params.append(expr)
    return first if app_expr is None else app_expr


def _parse_unary_expr(stream: TokenStream) -> Expression:
    pos, lc = stream.tell()
    first = stream.get()
    if first.type == TokenType.OPERATOR:
        if first.value not in ("not", "-"):
            stream.seek(pos)
            raise ParseError(
                f"expected 'not' or '-' got {repr(first.value)}", lc)
        try:
            operand = _parse_unary_expr(stream)
            return UnaryOp(first.value, operand)
        except ParseError as e:
            raise ParseError("expected <unary_expr>", lc) from e
    stream.seek(pos)
    return _parse_app_expr(stream)


def _help_parse_bin_expr(stream: TokenStream, parse_sub_expr: Callable[[TokenStream], Expression], op_list: tuple[str, ...]):
    first = parse_sub_expr(stream)
    bin_expr: None | BinaryOp = None

    while stream:
        pos, lc = stream.tell()
        op = stream.get()
        if op.type != TokenType.OPERATOR or op.value not in op_list:
            stream.seek(pos)
            return first if bin_expr is None else bin_expr

        second = parse_sub_expr(stream)
        if bin_expr is None:
            bin_expr = BinaryOp(op.value, first, second)
        else:
            bin_expr = BinaryOp(op.value, bin_expr, second)
    return first if bin_expr is None else bin_expr


def _parse_mult_expr(stream: TokenStream) -> Expression:
    return _help_parse_bin_expr(stream, _parse_unary_expr, ("*", "/"))


def _parse_add_expr(stream: TokenStream) -> Expression:
    return _help_parse_bin_expr(stream, _parse_mult_expr, ("+", "-"))


def _parse_comp_expr(stream: TokenStream) -> Expression:
    return _help_parse_bin_expr(stream, _parse_add_expr, ("=", "<>", "<", ">", "<=", ">="))


def _parse_and_expr(stream: TokenStream) -> Expression:
    return _help_parse_bin_expr(stream, _parse_comp_expr, ("&&",))


def _parse_or_expr(stream: TokenStream) -> Expression:
    return _help_parse_bin_expr(stream, _parse_and_expr, ("||",))


def _parse_expr(stream: TokenStream) -> Expression:
    for f in (_parse_let_expr, _parse_if_expr, _parse_fun_expr):
        if res := f(stream):
            return res

    return _parse_or_expr(stream)


def parse(tokens: list[Token]):
    if not tokens:
        return None
    stream = TokenStream(tokens)
    out = _parse_expr(stream)
    if stream:
        raise ParseError("encountered unexpected extra token",
                         stream.peek().pos)
    return out
