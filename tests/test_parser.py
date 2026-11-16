from pathlib import Path
import pytest
from sipl.ast import (
    AssignStmt,
    BinArithExpr,
    BlockStmt,
    CompareExpr,
    IfStmt,
    NegExpr,
    NumExpr,
    Program,
    SeqStmt,
    VarExpr,
    WhileStmt,
)
from sipl.parser import SIPLSyntaxError, parse_program

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def test_parse_precedence_and_associativity() -> None:
    ast = parse_program("begin R := X - Y - Z * 2 end")
    assert isinstance(ast, Program)
    assert isinstance(ast.stmt, AssignStmt)
    assert ast.stmt.var == "R"
    expr = ast.stmt.expr
    assert isinstance(expr, BinArithExpr) and expr.op == "-"
    assert isinstance(expr.left, BinArithExpr) and expr.left.op == "-"
    assert isinstance(expr.right, BinArithExpr) and expr.right.op == "*"


def test_parse_gcd_example() -> None:
    code = (EXAMPLES_DIR / "gcd.sipl").read_text(encoding="utf-8")
    ast = parse_program(code)
    assert isinstance(ast.stmt, WhileStmt)
    assert isinstance(ast.stmt.cond, NegExpr)
    assert isinstance(ast.stmt.cond.expr, CompareExpr)
    assert isinstance(ast.stmt.body, IfStmt)


def test_parse_power_example_spans() -> None:
    code = (EXAMPLES_DIR / "power.sipl").read_text(encoding="utf-8")
    ast = parse_program(code)
    assert ast.span.line == 1
    assert ast.span.column == 1
    assert ast.span.end_line == 8
    assert isinstance(ast.stmt, SeqStmt)
    assert isinstance(ast.stmt.first, AssignStmt)
    assert isinstance(ast.stmt.second, WhileStmt)
    assert isinstance(ast.stmt.second.body, BlockStmt)


def test_syntax_error_diagnostics() -> None:
    bad_code = "begin\n  X := 1;\n  Y = 2\nend"
    with pytest.raises(SIPLSyntaxError) as exc_info:
        parse_program(bad_code)
    err = exc_info.value
    assert err.line == 3
    assert err.column == 5
    assert "3:5" in str(err)


def test_ast_to_dict() -> None:
    ast = parse_program("begin X := 10 end")
    data = ast.to_dict()
    assert data["type"] == "Program"
    assert data["stmt"]["type"] == "AssignStmt"
    assert data["stmt"]["expr"] == {
        "type": "NumExpr",
        "value": 10,
        "span": {"line": 1, "column": 12, "end_line": 1, "end_column": 14},
    }
    assert isinstance(ast.stmt, AssignStmt)
    assert isinstance(ast.stmt.expr, NumExpr)
    assert isinstance(VarExpr(ast.span, "X"), VarExpr)
    pytest