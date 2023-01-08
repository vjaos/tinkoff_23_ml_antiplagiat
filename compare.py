import argparse
from ast import NodeTransformer, Name, FunctionDef, Import, ImportFrom, parse, unparse, Str, Expr, get_docstring
from typing import Any

AST_EMPTY_STR = Str('')
AST_EMPTY_STR_EXPR = Expr(AST_EMPTY_STR)


def edit_distance(s, t):
    h, w = len(s), len(t)
    dp = [[0 for _ in range(w + 1)] for _ in range(h + 1)]

    for i in range(h + 1):
        dp[i][0] = i

    for j in range(w + 1):
        dp[0][j] = j

    for i in range(h):
        for j in range(w):
            if s[i] == t[j]:
                dp[i + 1][j + 1] = dp[i][j]
            else:
                dp[i + 1][j + 1] = 1 + min(dp[i][j + 1], dp[i + 1][j], dp[i][j])

    return dp[-1][-1] / max(h, w)


class Normalizer(NodeTransformer):

    def __init__(self):
        self._methods_count = 0
        self._vars_count = 0

    def visit_Name(self, node: Name) -> Any:
        # Changing variable name
        node.id = 'var_{}'.format(self._vars_count)
        self._vars_count += 1
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        node.name = 'method_{}'.format(self._methods_count)

        # Convert docstring to an empty string
        docstring = get_docstring(node)

        if docstring:
            node.body[0] = AST_EMPTY_STR_EXPR
        else:
            node.body.insert(0, AST_EMPTY_STR_EXPR)

        # Remove annotations and the return type
        if node.args.args:
            for arg in node.args.args:
                arg.annotation = None

        node.returns = None

        self._methods_count += 1
        self.generic_visit(node)
        return node

    def visit_Import(self, node: Import) -> Any:
        # Removing the typing module
        node.names = [n for n in node.names if n.name != 'typing']
        self.generic_visit(node)
        return node if node.names else None

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        # Removing the typing module
        self.generic_visit(node)
        return node if node.module != 'typing' else None


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='Path to a file containing path pairs to files to check')
    parser.add_argument('output', help='Path to a file for storing the results of the program')

    args = parser.parse_args()

    edit_distances = []

    with open(args.input, 'r') as inpt:
        for line in inpt.readlines():
            print(line)
            src_path, trg_path = line.split()

            src_opened = open(src_path, 'r')
            trg_opened = open(trg_path, 'r')

            src_parsed = parse(src_opened.read())
            trg_parsed = parse(trg_opened.read())

            src_normalized = Normalizer().visit(src_parsed)
            trg_normalized = Normalizer().visit(trg_parsed)

            edit_distances.append(str(edit_distance(unparse(src_normalized), unparse(trg_normalized))))

            src_opened.close()
            trg_opened.close()

    with open(args.output, 'w+') as out:
        out.writelines(edit_distances)
