from typing import TextIO

from lexer import lex, LexError
from parse import parse, ParseError

import argparse

BOLD_HI_RED = "\x1B[1;91m"
RED = "\x1B[0;31m"
BLUE = "\x1B[1;34m"
RESET = "\x1B[0m"


def print_error_open_file(file: str):
    print(f"{BOLD_HI_RED}ERROR: {RED}Failed to open {RESET}{file}")
    raise SystemExit


def print_error_loc(msg: str, filename: str, source: str, line: int, col: int):
    print(f"{BOLD_HI_RED}ERROR: {RED}{msg} {BLUE}at {RESET}{filename}:{line}:{col}")
    bad_line = source.splitlines()[line - 1] + " "
    indicator = ""
    for i, c in enumerate(bad_line):
        if i == col - 1:
            indicator += "^"
        elif c == "\t":
            indicator += "\t"
        else:
            indicator += " "

    print(f"{line} |\t", bad_line)
    print(f"{" " * len(str(line))} |\t", indicator)
    raise SystemExit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    args = parser.parse_args()

    try:
        f = open(args.source, "r", encoding="ascii")
    except IOError:
        print_error_open_file(args.source)
    else:
        with f:
            source = f.read() + "\n"
            try:
                tokens = lex(source)
                print(tokens)
                ast = parse(tokens)
                print(ast)
            except LexError as e:
                print_error_loc(e.msg, f.name, source, e.line, e.col)
            except ParseError as e:
                print_error_loc(e.msg, f.name, source, e.line, e.col)
            return


if __name__ == "__main__":
    main()
