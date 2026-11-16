from __future__ import annotations
from sipl.ast import (
    Aexp,
    AssignStmt,
    Bexp,
    BinArithExpr,
    BlockStmt,
    CompareExpr,
    IfStmt,
    NegExpr,
    NumExpr,
    OrExpr,
    Program,
    SeqStmt,
    SkipStmt,
    Stmt,
    VarExpr,
    WhileStmt,
)


def aexp_to_term(expr: Aexp) -> str:
    if isinstance(expr, NumExpr):
        return f"const({expr.value})"
    if isinstance(expr, VarExpr):
        return f"var({expr.name})"
    if isinstance(expr, BinArithExpr):
        op_map = {"+": "add", "-": "sub", "*": "mult"}
        return f"{op_map[expr.op]}({aexp_to_term(expr.left)}, {aexp_to_term(expr.right)})"
    raise ValueError(f"Unknown arithmetic expression: {expr}")


def bexp_to_term(expr: Bexp) -> str:
    if isinstance(expr, CompareExpr):
        op_map = {"=": "eq", ">": "gt", "<": "lt", ">=": "ge", "<=": "le"}
        return f"{op_map[expr.op]}({aexp_to_term(expr.left)}, {aexp_to_term(expr.right)})"
    if isinstance(expr, NegExpr):
        return f"neg({bexp_to_term(expr.expr)})"
    if isinstance(expr, OrExpr):
        return f"disj({bexp_to_term(expr.left)}, {bexp_to_term(expr.right)})"
    raise ValueError(f"Unknown boolean expression: {expr}")


def stmt_to_term(stmt: Stmt) -> str:
    if isinstance(stmt, SkipStmt):
        return "skip"
    if isinstance(stmt, AssignStmt):
        return f"assign({stmt.var}, {aexp_to_term(stmt.expr)})"
    if isinstance(stmt, SeqStmt):
        return f"comp({stmt_to_term(stmt.first)}, {stmt_to_term(stmt.second)})"
    if isinstance(stmt, IfStmt):
        return (
            f"branch({bexp_to_term(stmt.cond)}, "
            f"{stmt_to_term(stmt.then_branch)}, {stmt_to_term(stmt.else_branch)})"
        )
    if isinstance(stmt, WhileStmt):
        return f"cycle({bexp_to_term(stmt.cond)}, {stmt_to_term(stmt.body)})"
    if isinstance(stmt, BlockStmt):
        return stmt_to_term(stmt.stmt)
    raise ValueError(f"Unknown statement: {stmt}")


def program_to_term(program: Program) -> str:
    return stmt_to_term(program.stmt)