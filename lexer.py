from typing import Callable

from tokens import Token, TokenType

KEYWORDS = ("let", "in", "if", "then", "else", "fun", "rec", "not")
OPERATORS = ("+", "-", "*", "/", "=", "<>", "<",
             ">", "<=", ">=", "&&", "||", "->")


class LexError(Exception):
    def __init__(self, msg: str, pos: tuple[int, int, int]):
        super().__init__(msg)
        self.msg = msg
        self.pos, self.line, self.col = pos


class EndOfCharStream(Exception):
    def __init__(self):
        super().__init__("end of charstream")


class CommentError(Exception):
    def __init__(self, msg: str, pos: tuple[int, int, int]):
        super().__init__(msg)
        self.msg = msg
        self.pos, self.line, self.col = pos


class CharStream:
    def __init__(self, src: str):
        self._source = src
        self._pos = 0

        self._line = 1
        self._col = 1

        self._nl_queued_index = 0

        self._comment_depth = 0

    def __repr__(self) -> str:
        return f"stream[{self._pos}] = {repr(self._source[self._pos])}" if self else "stream ended"

    def get_pos(self):
        return (self._pos, self._line, self._col)

    def set_pos(self, pos: tuple[int, int, int]):
        self._pos, self._line, self._col = pos

    def _get(self) -> str:
        if not self:
            raise EndOfCharStream
        curr = self._source[self._pos]
        if curr == "\n":
            self._nl_queued_index = self._pos
        if 0 < self._nl_queued_index < self._pos:
            self._line += 1
            self._col = 1
            self._nl_queued_index = 0

        self._pos += 1
        self._col += 1
        return curr

    def get(self) -> str:
        curr = self._get()
        if curr != "(":
            return curr
        if not self._has_next():
            return curr

        # next exists
        next_ = self._source[self._pos]
        if next_ != "*":
            return curr

        # comment started
        self._comment_depth = 1
        self._get()  # commit next
        while self._has_next():
            curr = next_
            next_ = self._source[self._pos]
            # print(f"{curr=} {next_=}")

            if curr == "\n":
                raise CommentError(
                    "multiline comment not supported", (self._pos - 1, self._line, self._col - 1))

            if curr + next_ != "*)":
                self._get()  # commit next
                continue

            self.get()  # commit *
            return self.get()  # commit )

        # print(f"{curr=}, {next_=}")
        assert next_ == "\n"
        raise CommentError("comment not closed",
                           (self._pos - 1, self._line, self._col - 1))

    def _has_next(self):
        return self._pos < len(self._source)

    def __bool__(self):
        return self._pos < len(self._source)

    def ff_and_get_pos(self):
        while True:
            if not self:
                raise LexError(
                    "unexpectedly encountered end of file", self.get_pos())
            if not _is_delimiter(self.get()):
                break
        self.put_back()
        return self.get_pos()

    def put_back(self):
        self._pos -= 1
        self._col -= 1


def _is_delimiter(c: str):
    return c.isspace()  # or c in OPERATORS


def _help_is_identifier(x: str) -> bool:
    if not x:
        return False
    if x in KEYWORDS:
        return False
    if not x[0].islower():
        return False
    for i in range(1, len(x)):
        if not x[i].isalnum():
            return False
    return True


def _help_parse_impl(stream: CharStream, str: str, compare: Callable[[str], bool]) -> bool:
    pos = stream.get_pos()
    for c in str:
        if stream and c != stream.get():
            stream.set_pos(pos)
            return False
    got = stream.get()
    if compare(got) or _is_delimiter(got):
        stream.put_back()
        return True
    stream.set_pos(pos)
    return False


def _help_parse_operator(stream: CharStream, str: str) -> bool:
    return _help_parse_impl(stream, str, lambda s: s.isalnum())


def _help_parse_alnum(stream: CharStream, str: str) -> bool:
    return _help_parse_impl(stream, str, lambda s: s in OPERATORS)


def _help_parse_any_word(stream: CharStream) -> str:
    if (char := stream._source[stream._pos]).isspace():
        print(f"{repr(char)} at {stream._pos} was not space")
        raise AssertionError()

    def find():
        buf = ""
        is_alnum = False
        while stream and (curr := stream.get()) and not _is_delimiter(curr):
            if not buf:
                is_alnum = curr.isalnum()
            if curr.isalnum() != is_alnum:
                stream.put_back()
                break
            buf += curr
        return buf

    word = find()

    # if word == "(*":
    #     print("HELLO HERE")
    #     depth = 1
    #     lparen_found = False
    #     star_found = False
    #     while stream and (curr := stream.get()):
    #         new_lparen_found = curr == "("
    #         new_star_found = curr == "*"

    #         if lparen_found and new_star_found:
    #             depth += 1
    #         elif star_found and curr == ")":
    #             depth -= 1
    #         print(f"skipping {repr(curr)}")

    #         lparen_found, star_found = new_lparen_found, new_star_found
    #         if depth == 0:
    #             break

    #     print(f"now: {stream}")

    #     if depth != 0:
    #         raise LexError("unclosed comment found", stream.get_pos())
    #     word = find()
    #     print(f"new word={find()}")

    return word


def _help_expect_keyword(stream: CharStream, tokens: list[Token], kw: str):
    pos = stream.ff_and_get_pos()
    if not _help_parse_alnum(stream, kw):
        raise LexError(f"expected '{kw}' here", pos)
    tokens.append(Token(TokenType.KEYWORD, kw, pos))


def _parse_let_expr(stream: CharStream, tokens: list[Token]):
    _help_expect_keyword(stream, tokens, "let")

    rec_pos = stream.ff_and_get_pos()
    if not _help_parse_alnum(stream, "rec"):
        stream.set_pos(rec_pos)
    else:
        tokens.append(Token(TokenType.KEYWORD, "rec", rec_pos))

    iden_pos = stream.ff_and_get_pos()
    iden = _help_parse_any_word(stream)
    if not _help_is_identifier(iden):
        raise LexError("expected an identifier here", iden_pos)
    tokens.append(Token(TokenType.ID, iden, iden_pos))

    while stream:
        iden_or_assign_pos = stream.ff_and_get_pos()
        iden_or_assign = _help_parse_any_word(stream)
        if iden_or_assign == "=":
            tokens.append(Token(TokenType.OPERATOR, "=", iden_or_assign_pos))
            break
        if not _help_is_identifier(iden_or_assign):
            raise LexError("expected an identifier here", iden_or_assign_pos)
        tokens.append(Token(TokenType.ID, iden_or_assign, iden_or_assign_pos))

    a_pos = stream.ff_and_get_pos()
    try:
        _parse_expr(stream, tokens)
    except LexError as e:
        raise LexError("expected an expression here", a_pos) from e

    _help_expect_keyword(stream, tokens, "in")

    b_pos = stream.ff_and_get_pos()
    try:
        _parse_expr(stream, tokens)
    except LexError as e:
        raise LexError("expected an expression here", b_pos) from e


def _parse_if_expr(stream: CharStream, tokens: list[Token]):
    _help_expect_keyword(stream, tokens, "if")

    cond_pos = stream.ff_and_get_pos()
    try:
        _parse_expr(stream, tokens)
    except LexError as e:
        raise LexError("expected an expression here", cond_pos) from e

    _help_expect_keyword(stream, tokens, "then")

    yes_pos = stream.ff_and_get_pos()
    try:
        _parse_expr(stream, tokens)
    except LexError as e:
        raise LexError("expected an expression here", yes_pos) from e

    _help_expect_keyword(stream, tokens, "else")

    no_pos = stream.ff_and_get_pos()
    try:
        _parse_expr(stream, tokens)
    except LexError as e:
        raise LexError("expected an expression here", no_pos) from e


def _parse_fun_expr(stream: CharStream, tokens: list[Token]):
    _help_expect_keyword(stream, tokens, "fun")

    iden_pos = stream.ff_and_get_pos()
    iden = _help_parse_any_word(stream)
    if not _help_is_identifier(iden):
        raise LexError("expected an identifier here", iden_pos)
    tokens.append(Token(TokenType.ID, iden, iden_pos))

    while stream:
        iden_or_def_pos = stream.ff_and_get_pos()
        iden_or_def = _help_parse_any_word(stream)
        if iden_or_def == "->":
            tokens.append(Token(TokenType.OPERATOR, "->", iden_or_def_pos))
            break
        if not _help_is_identifier(iden_or_def):
            raise LexError("expected an identifier here", iden_or_def_pos)
        tokens.append(Token(TokenType.ID, iden_or_def, iden_or_def_pos))

    res_pos = stream.ff_and_get_pos()
    try:
        _parse_expr(stream, tokens)
    except LexError as e:
        raise LexError("expected an expression here", res_pos) from e


def _parse_primary_expr(stream: CharStream, tokens: list[Token]):
    pos = stream.ff_and_get_pos()
    word = _help_parse_any_word(stream)
    if word in ("true", "false"):
        tokens.append(Token(TokenType.BOOL, word, pos))
        return
    if word.isnumeric():
        tokens.append(Token(TokenType.INT, word, pos))
        return
    if _help_is_identifier(word):
        tokens.append(Token(TokenType.ID, word, pos))
        return

    if word != "(":
        stream.set_pos(pos)
        raise LexError("expected a '(' here", pos)
    tokens.append(Token(TokenType.DELIMITER, "(", pos))

    expr_pos = stream.ff_and_get_pos()
    try:
        _parse_expr(stream, tokens)
    except LexError as e:
        stream.set_pos(expr_pos)
        raise LexError("expected an expression here", expr_pos) from e

    r_paren_pos = stream.ff_and_get_pos()
    if stream.get() != ")":
        stream.set_pos(r_paren_pos)
        raise LexError("expected a ')' here", r_paren_pos)
    tokens.append(Token(TokenType.DELIMITER, ")", r_paren_pos))


def _parse_app_expr(stream: CharStream, tokens: list[Token]):
    primary_pos = stream.get_pos()
    try:
        primary_pos = stream.ff_and_get_pos()
        _parse_primary_expr(stream, tokens)
    except LexError as e:
        stream.set_pos(primary_pos)
        raise LexError("expected a <primary_expr> here", primary_pos) from e
    while stream:
        pos = stream.get_pos()
        try:
            pos = stream.ff_and_get_pos()
            _parse_primary_expr(stream, tokens)
        except LexError:
            stream.set_pos(pos)
            break


def _parse_unary_expr(stream: CharStream, tokens: list[Token]):
    # is not or -
    pos = stream.get_pos()
    try:
        pos = stream.ff_and_get_pos()
        if (op := _help_parse_any_word(stream)) not in ("not", "-"):
            stream.set_pos(pos)
            raise LexError("unary operator not recognized", pos)
        tokens.append(Token(TokenType.OPERATOR, op, pos))

        pos = stream.ff_and_get_pos()
        _parse_app_expr(stream, tokens)
        return
    except LexError:
        stream.set_pos(pos)

    # is app_expr instead
    app_pos = stream.get_pos()
    try:
        app_pos = stream.ff_and_get_pos()
        _parse_app_expr(stream, tokens)
    except LexError as e:
        stream.set_pos(app_pos)
        raise LexError("expected a <app_expr> here", app_pos) from e


def _parse_mult_expr(stream: CharStream, tokens: list[Token]):
    unary_pos = stream.get_pos()
    try:
        unary_pos = stream.ff_and_get_pos()
        _parse_unary_expr(stream, tokens)
    except LexError as e:
        stream.set_pos(unary_pos)
        raise LexError("expected a <unary_expr> here", unary_pos) from e
    while stream:
        pos = stream.get_pos()
        try:
            pos = stream.ff_and_get_pos()
            if (op := _help_parse_any_word(stream)) not in ("*", "/"):
                stream.set_pos(pos)
                break
            tokens.append(Token(TokenType.OPERATOR, op, pos))

            pos = stream.ff_and_get_pos()
            _parse_unary_expr(stream, tokens)
        except LexError:
            stream.set_pos(pos)
            break


def _parse_add_expr(stream: CharStream, tokens: list[Token]):
    mult_pos = stream.get_pos()
    try:
        mult_pos = stream.ff_and_get_pos()
        _parse_mult_expr(stream, tokens)
    except LexError as e:
        stream.set_pos(mult_pos)
        raise LexError("expected a <mult_expr> here", mult_pos) from e
    while stream:
        pos = stream.get_pos()
        try:
            pos = stream.ff_and_get_pos()
            if (op := _help_parse_any_word(stream)) not in ("+", "-"):
                stream.set_pos(pos)
                break
            tokens.append(Token(TokenType.OPERATOR, op, pos))

            pos = stream.ff_and_get_pos()
            _parse_mult_expr(stream, tokens)
        except LexError:
            stream.set_pos(pos)
            break


def _parse_comp_expr(stream: CharStream, tokens: list[Token]):
    add_pos = stream.get_pos()
    try:
        add_pos = stream.ff_and_get_pos()
        _parse_add_expr(stream, tokens)
    except LexError as e:
        stream.set_pos(add_pos)
        raise LexError("expected a <add_expr> here", add_pos) from e
    while stream:
        pos = stream.get_pos()
        try:
            pos = stream.ff_and_get_pos()
            if (op := _help_parse_any_word(stream)) not in ("=", "<>", "<", ">", "<=", ">="):
                stream.set_pos(pos)
                break
            tokens.append(Token(TokenType.OPERATOR, op, pos))

            pos = stream.ff_and_get_pos()
            _parse_add_expr(stream, tokens)
        except LexError:
            stream.set_pos(pos)
            break


def _help_parse_bin_bool_expr(stream: CharStream, tokens: list[Token], parse_sub_expr: Callable[[CharStream, list[Token]], None], sub_name: str, op_str: str):
    sub_pos = stream.get_pos()
    try:
        sub_pos = stream.ff_and_get_pos()
        parse_sub_expr(stream, tokens)
    except LexError as e:
        stream.set_pos(sub_pos)
        raise LexError(f"expected a <{sub_name}_expr> here", sub_pos) from e
    while stream:
        pos = stream.get_pos()
        try:
            pos = stream.ff_and_get_pos()
            if not _help_parse_operator(stream, op_str):
                stream.set_pos(pos)
                break
            tokens.append(Token(TokenType.OPERATOR, op_str, pos))

            pos = stream.ff_and_get_pos()
            parse_sub_expr(stream, tokens)
        except LexError:
            stream.set_pos(pos)
            break


def _parse_and_expr(stream: CharStream, tokens: list[Token]):
    _help_parse_bin_bool_expr(stream, tokens, _parse_comp_expr, "comp", "&&")

    # comp_pos = stream.get_pos()
    # try:
    #     comp_pos = stream.ff_and_get_pos()
    #     _parse_comp_expr(stream, tokens)
    # except LexError as e:
    #     stream.set_pos(comp_pos)
    #     raise LexError("expected a <comp_expr> here", comp_pos) from e
    # while stream:
    #     pos = stream.get_pos()
    #     try:
    #         pos = stream.ff_and_get_pos()
    #         if not _help_parse_operator(stream, "&&"):
    #             stream.set_pos(pos)
    #             break
    #         tokens.append(Token(TokenType.OPERATOR, "&&", pos))

    #         pos = stream.ff_and_get_pos()
    #         _parse_comp_expr(stream, tokens)
    #     except LexError:
    #         stream.set_pos(pos)
    #         break


def _parse_or_expr(stream: CharStream, tokens: list[Token]):
    _help_parse_bin_bool_expr(stream, tokens, _parse_and_expr, "and", "||")
    # and_pos = stream.get_pos()
    # try:
    #     and_pos = stream.ff_and_get_pos()
    #     _parse_and_expr(stream, tokens)
    # except LexError as e:
    #     stream.set_pos(and_pos)
    #     raise LexError("expected a <and_expr> here", and_pos) from e
    # while stream:
    #     pos = stream.get_pos()
    #     try:
    #         pos = stream.ff_and_get_pos()
    #         if not _help_parse_operator(stream, "||"):
    #             stream.set_pos(pos)
    #             break
    #         tokens.append(Token(TokenType.OPERATOR, "||", pos))

    #         pos = stream.ff_and_get_pos()
    #         _parse_and_expr(stream, tokens)
    #     except LexError:
    #         stream.set_pos(pos)
    #         break


def _parse_expr(stream: CharStream, tokens: list[Token]):
    pos = stream.ff_and_get_pos()
    for f in (_parse_let_expr, _parse_if_expr, _parse_fun_expr):
        try:
            f(stream, tokens)
            return
        except LexError:
            pass
        stream.set_pos(pos)

    try:
        _parse_or_expr(stream, tokens)
    except LexError as e:
        stream.set_pos(pos)
        raise LexError("expected a <or_expr> here", pos) from e


def lex(source: str) -> list[Token]:
    out: list[Token] = []
    try:
        stream = CharStream(source)
        _parse_expr(stream, out)
        while stream:
            # if stream only has whitespace then ignore
            if not _is_delimiter(stream.get()):
                raise LexError("unable to lex entire text", stream.get_pos())
    except LexError as e:
        if len(out) == 0:  # empty tokens isnt error
            return []
        raise e
    except CommentError as c:
        raise LexError(c.msg, (c.pos, c.line, c.col)) from c

    return out
