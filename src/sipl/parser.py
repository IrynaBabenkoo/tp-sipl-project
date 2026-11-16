from __future__ import annotations
from pathlib import Path
from lark import Lark, LarkError, Token, Transformer, Tree, UnexpectedInput, v_args
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
    SourceSpan,
    Stmt,
    VarExpr,
    WhileStmt
)

GRAMMAR_PATH = Path(__file__).resolve().parent.parent.parent / "grammar" / "sipl.lark"


class SIPLSyntaxError(Exception):
    def __init__(self, message: str, line: int = 1, column: int = 1) -> None:
        super().__init__(f"Syntax error at {line}:{column}: {message}")
        self.message = message
        self.line = line
        self.column = column


def _span_from_meta(meta: object) -> SourceSpan:
    return SourceSpan(
        line=getattr(meta, "line", 1),
        column=getattr(meta, "column", 1),
        end_line=getattr(meta, "end_line", 1),
        end_column=getattr(meta, "end_column", 1),
    )


def _merge_spans(start: SourceSpan, end: SourceSpan) -> SourceSpan:
    return SourceSpan(
        line=start.line,
        column=start.column,
        end_line=end.end_line,
        end_column=end.end_column,
    )


@v_args(meta=True)
class _ASTBuilder(Transformer[Token, Program]):
    def start(self, meta: object, items: list[Program]) -> Program:
        return items[0]

    def program(self, meta: object, items: list[Stmt]) -> Program:
        return Program(span=_span_from_meta(meta), stmt=items[0])

    def seq(self, meta: object, items: list[Stmt]) -> SeqStmt:
        return SeqStmt(span=_span_from_meta(meta), first=items[0], second=items[1])

    def assign(self, meta: object, items: list[Token | Aexp]) -> AssignStmt:
        var_tok, expr = items[0], items[1]
        assert isinstance(var_tok, Token)
        return AssignStmt(span=_span_from_meta(meta), var=str(var_tok), expr=expr)  # type: ignore[arg-type]

    def if_stmt(self, meta: object, items: list[Bexp | Stmt]) -> IfStmt:
        return IfStmt(
            span=_span_from_meta(meta),
            cond=items[0],  # type: ignore[arg-type]
            then_branch=items[1],  # type: ignore[arg-type]
            else_branch=items[2],  # type: ignore[arg-type]
        )

    def while_stmt(self, meta: object, items: list[Bexp | Stmt]) -> WhileStmt:
        return WhileStmt(
            span=_span_from_meta(meta),
            cond=items[0],  # type: ignore[arg-type]
            body=items[1],  # type: ignore[arg-type]
        )

    def block(self, meta: object, items: list[Stmt]) -> BlockStmt:
        return BlockStmt(span=_span_from_meta(meta), stmt=items[0])

    def skip(self, meta: object, items: list[object]) -> SkipStmt:
        return SkipStmt(span=_span_from_meta(meta))

    def num(self, meta: object, items: list[Token]) -> NumExpr:
        return NumExpr(span=_span_from_meta(meta), value=int(items[0]))

    def var(self, meta: object, items: list[Token]) -> VarExpr:
        return VarExpr(span=_span_from_meta(meta), name=str(items[0]))

    def paren_aexp(self, meta: object, items: list[Aexp]) -> Aexp:
        return items[0]

    def add(self, meta: object, items: list[Aexp]) -> BinArithExpr:
        return BinArithExpr(span=_span_from_meta(meta), op="+", left=items[0], right=items[1])

    def sub(self, meta: object, items: list[Aexp]) -> BinArithExpr:
        return BinArithExpr(span=_span_from_meta(meta), op="-", left=items[0], right=items[1])

    def mult(self, meta: object, items: list[Aexp]) -> BinArithExpr:
        return BinArithExpr(span=_span_from_meta(meta), op="*", left=items[0], right=items[1])

    def eq_expr(self, meta: object, items: list[Aexp]) -> CompareExpr:
        return CompareExpr(span=_span_from_meta(meta), op="=", left=items[0], right=items[1])

    def gt_expr(self, meta: object, items: list[Aexp]) -> CompareExpr:
        return CompareExpr(span=_span_from_meta(meta), op=">", left=items[0], right=items[1])

    def lt_expr(self, meta: object, items: list[Aexp]) -> CompareExpr:
        return CompareExpr(span=_span_from_meta(meta), op="<", left=items[0], right=items[1])

    def ge_expr(self, meta: object, items: list[Aexp]) -> CompareExpr:
        return CompareExpr(span=_span_from_meta(meta), op=">=", left=items[0], right=items[1])

    def le_expr(self, meta: object, items: list[Aexp]) -> CompareExpr:
        return CompareExpr(span=_span_from_meta(meta), op="<=", left=items[0], right=items[1])

    def neg_expr(self, meta: object, items: list[Token | Bexp]) -> NegExpr:
        tok, expr = items[0], items[1]
        assert isinstance(tok, Token)
        tok_span = SourceSpan(
            line=tok.line or 1,
            column=tok.column or 1,
            end_line=tok.end_line or tok.line or 1,
            end_column=tok.end_column or tok.column or 1,
        )
        return NegExpr(span=_merge_spans(tok_span, expr.span), expr=expr)  # type: ignore[arg-type, union-attr]

    def or_expr(self, meta: object, items: list[Bexp | Token]) -> OrExpr:
        left, _, right = items[0], items[1], items[2]
        return OrExpr(
            span=_merge_spans(left.span, right.span),  # type: ignore[union-attr]
            left=left,  # type: ignore[arg-type]
            right=right,  # type: ignore[arg-type]
        )

    def paren_bexp(self, meta: object, items: list[Bexp]) -> Bexp:
        return items[0]


_LARK_PARSER = Lark(
    GRAMMAR_PATH.read_text(encoding="utf-8"),
    start="start",
    parser="lalr",
    propagate_positions=True,
)


def parse_cst(source: str) -> Tree[Token]:
    try:
        return _LARK_PARSER.parse(source)
    except UnexpectedInput as exc:
        line = getattr(exc, "line", 1)
        col = getattr(exc, "column", 1)
        context = exc.get_context(source, span=40).strip()
        raise SIPLSyntaxError(f"Unexpected input near:\n{context}", line=line, column=col) from exc
    except LarkError as exc:
        raise SIPLSyntaxError(str(exc)) from exc


def parse_program(source: str) -> Program:
    cst = parse_cst(source)
    return _ASTBuilder().transform(cst)