from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Literal, Union


@dataclass(frozen=True)
class SourceSpan:
    line: int
    column: int
    end_line: int
    end_column: int


@dataclass(frozen=True)
class ASTNode:
    span: SourceSpan

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"type": self.__class__.__name__}
        for field_name, val in self.__dict__.items():
            if isinstance(val, ASTNode):
                result[field_name] = val.to_dict()
            elif isinstance(val, SourceSpan):
                result[field_name] = asdict(val)
            else:
                result[field_name] = val
        return result


@dataclass(frozen=True)
class NumExpr(ASTNode):
    value: int


@dataclass(frozen=True)
class VarExpr(ASTNode):
    name: str


@dataclass(frozen=True)
class BinArithExpr(ASTNode):
    op: Literal["+", "-", "*"]
    left: Aexp
    right: Aexp


Aexp = Union[NumExpr, VarExpr, BinArithExpr]


@dataclass(frozen=True)
class CompareExpr(ASTNode):
    op: Literal["=", ">", "<", ">=", "<="]
    left: Aexp
    right: Aexp


@dataclass(frozen=True)
class NegExpr(ASTNode):
    expr: Bexp


@dataclass(frozen=True)
class OrExpr(ASTNode):
    left: Bexp
    right: Bexp


Bexp = Union[CompareExpr, NegExpr, OrExpr]


@dataclass(frozen=True)
class SkipStmt(ASTNode):
    pass


@dataclass(frozen=True)
class AssignStmt(ASTNode):
    var: str
    expr: Aexp


@dataclass(frozen=True)
class SeqStmt(ASTNode):
    first: Stmt
    second: Stmt


@dataclass(frozen=True)
class IfStmt(ASTNode):
    cond: Bexp
    then_branch: Stmt
    else_branch: Stmt


@dataclass(frozen=True)
class WhileStmt(ASTNode):
    cond: Bexp
    body: Stmt


@dataclass(frozen=True)
class BlockStmt(ASTNode):
    stmt: Stmt


Stmt = Union[SkipStmt, AssignStmt, SeqStmt, IfStmt, WhileStmt, BlockStmt]


@dataclass(frozen=True)
class Program(ASTNode):
    stmt: Stmt