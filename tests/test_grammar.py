from pathlib import Path
import pytest
from lark import Lark, LarkError

GRAMMAR_PATH = Path(__file__).resolve().parent.parent / "grammar" / "sipl.lark"


@pytest.fixture(scope="module")
def parser() -> Lark:
    grammar_text = GRAMMAR_PATH.read_text(encoding="utf-8")
    return Lark(grammar_text, start="start", parser="lalr")


VALID_PROGRAMS = [
    "begin skip end",
    "begin X := 42 end",
    "begin X := -5 end",
    "begin X := 1; Y := 2; Z := X + Y end",
    "begin R := (X + Y) * Z - 3 end",
    "begin if X > 0 then Y := 1 else Y := 0 end",
    """
    begin
      R := 1;
      while Y > 0 do
        begin
          R := R * X;
          Y := Y - 1
        end
    end
    """,
    """
    begin
      while !(M = N) do
        if M > N then M := M - N else N := N - M
    end
    """,
    "begin if ¬(X = 0) \\/ (Y > 10) then Z := 1 else skip end",
    """
    begin
      F := 1;
      begin
        while N > 1 do
          begin
            F := F * N;
            N := N - 1
          end
      end
    end
    """,
]

INVALID_PROGRAMS = [
    "",
    "X := 1",
    "begin X := 1; end",
    "begin if X > 0 then Y := 1 end",
    "begin X = 1 end",
    "begin 5 := X end",
    "begin while X > 0 X := X - 1 end",
    "begin X := (1 + 2 end",
    "begin if X + 1 then Y := 2 else Y := 3 end",
    "begin begin X := 1 end",
]


@pytest.mark.parametrize("code", VALID_PROGRAMS)
def test_valid_sipl_programs(parser: Lark, code: str) -> None:
    tree = parser.parse(code)
    assert tree.data == "start"


@pytest.mark.parametrize("code", INVALID_PROGRAMS)
def test_invalid_sipl_programs(parser: Lark, code: str) -> None:
    with pytest.raises(LarkError):
        parser.parse(code)