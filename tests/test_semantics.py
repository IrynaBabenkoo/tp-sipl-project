import json
from pathlib import Path
from sipl.cli import main
from sipl.parser import parse_program
from sipl.semantics.term_builder import program_to_term

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def test_semantic_term_composition() -> None:
    program = parse_program("begin X := 1; if X > 0 then Y := X + 2 else skip end")
    term = program_to_term(program)
    assert term == "comp(assign(X, const(1)), branch(gt(var(X), const(0)), assign(Y, add(var(X), const(2))), skip))"


def test_semantic_term_gcd_and_cli(capsys: object) -> None:
    gcd_path = EXAMPLES_DIR / "gcd.sipl"
    program = parse_program(gcd_path.read_text(encoding="utf-8"))
    term = program_to_term(program)
    assert term.startswith("cycle(neg(eq(var(M), var(N))), branch(")

    assert main(["term", str(gcd_path), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert data["term"] == term