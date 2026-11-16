import json
from pathlib import Path
from sipl.cli import main
from sipl.parser import parse_cst
from sipl.visualization.tree_export import cst_to_dict, cst_to_dot, cst_to_text

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def test_parse_tree_exports() -> None:
    source = "begin X := 1 + 2 end"
    cst = parse_cst(source)

    text_out = cst_to_text(cst, source)
    assert "program" in text_out
    assert "assign" in text_out

    dict_out = cst_to_dict(cst, source)
    assert dict_out["rule"] == "start"
    assert dict_out["children"][0]["rule"] == "program"

    dot_out = cst_to_dot(cst, source)
    assert dot_out.startswith("digraph ParseTree")
    assert "->" in dot_out


def test_cli_check_and_parse(capsys: object) -> None:
    gcd_path = str(EXAMPLES_DIR / "gcd.sipl")
    assert main(["check", gcd_path, "--json"]) == 0
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert json.loads(out)["status"] == "ok"

    assert main(["parse", gcd_path, "--json"]) == 0
    ast_json = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert ast_json["type"] == "Program"


def test_cli_run_and_trace(capsys: object) -> None:
    power_path = str(EXAMPLES_DIR / "power.sipl")
    assert main(["run", power_path, "--var", "X=3", "--var", "Y=4", "--json"]) == 0
    run_data = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert run_data["state"] == {"X": 3, "Y": 0, "R": 81}

    assert main(["trace", power_path, "--var", "X=2", "--var", "Y=2", "--json"]) == 0
    trace_data = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert trace_data["trace"][-1]["event"] == "Finished"


def test_cli_tree_dot_file(tmp_path: Path) -> None:
    gcd_path = str(EXAMPLES_DIR / "gcd.sipl")
    dot_file = tmp_path / "gcd.dot"
    assert main(["tree", gcd_path, "--format", "dot", "-o", str(dot_file)]) == 0
    assert "digraph ParseTree" in dot_file.read_text(encoding="utf-8")


def test_cli_syntax_error_exit_code(tmp_path: Path, capsys: object) -> None:
    bad_file = tmp_path / "bad.sipl"
    bad_file.write_text("begin X = 1 end", encoding="utf-8")
    assert main(["check", str(bad_file), "--json"]) == 1
    err_data = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert err_data["status"] == "error"