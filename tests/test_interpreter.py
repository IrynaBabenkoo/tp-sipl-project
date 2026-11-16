from pathlib import Path
import pytest
from sipl.interpreter.evaluator import (
    SIPLInterpreter,
    SIPLRuntimeError,
    StepLimitExceededError,
)
from sipl.parser import parse_program

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def test_run_gcd() -> None:
    program = parse_program((EXAMPLES_DIR / "gcd.sipl").read_text(encoding="utf-8"))
    result = SIPLInterpreter().run(program, {"M": 48, "N": 18})
    assert result.final_state == {"M": 6, "N": 6}
    assert result.steps > 0


def test_run_power() -> None:
    program = parse_program((EXAMPLES_DIR / "power.sipl").read_text(encoding="utf-8"))
    result = SIPLInterpreter().run(program, {"X": 2, "Y": 5})
    assert result.final_state == {"X": 2, "Y": 0, "R": 32}


def test_run_div() -> None:
    program = parse_program((EXAMPLES_DIR / "div.sipl").read_text(encoding="utf-8"))
    result = SIPLInterpreter().run(program, {"X": 17, "Y": 5})
    assert result.final_state == {"X": 2, "Y": 5, "R": 3}


def test_skip_and_boolean_operators() -> None:
    code = "begin if ¬(X = 0) \\/ (Y <= 3) then skip else Z := 99 end"
    program = parse_program(code)
    res_true = SIPLInterpreter().run(program, {"X": 0, "Y": 2})
    assert res_true.final_state == {"X": 0, "Y": 2}

    res_false = SIPLInterpreter().run(program, {"X": 0, "Y": 5})
    assert res_false.final_state == {"X": 0, "Y": 5, "Z": 99}


def test_undefined_variable_error() -> None:
    program = parse_program("begin X := Y + 1 end")
    with pytest.raises(SIPLRuntimeError, match="Undefined variable 'Y'"):
        SIPLInterpreter().run(program)


def test_infinite_loop_step_limit() -> None:
    program = parse_program("begin while 1 = 1 do skip end")
    with pytest.raises(StepLimitExceededError):
        SIPLInterpreter(max_steps=50).run(program)


def test_execution_trace_events() -> None:
    program = parse_program("begin X := 1; if X > 0 then Y := X * 3 else skip end")
    result = SIPLInterpreter(record_trace=True).run(program)
    events = [ev.event for ev in result.trace]
    assert events[0] == "BeforeStatement"
    assert "VarAssigned" in events
    assert "ConditionEvaluated" in events
    assert events[-1] == "Finished"
    serialized = [ev.to_dict() for ev in result.trace]
    assert serialized[-1]["state"] == {"X": 1, "Y": 3}