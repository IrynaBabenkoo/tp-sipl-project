from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Literal
from sipl.ast import SourceSpan

EventType = Literal[
    "BeforeStatement",
    "AfterStatement",
    "VarAssigned",
    "ConditionEvaluated",
    "Finished",
]


@dataclass(frozen=True)
class TraceEvent:
    step: int
    event: EventType
    stmt_type: str
    span: SourceSpan | None
    state: dict[str, int]
    detail: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "event": self.event,
            "stmt_type": self.stmt_type,
            "span": asdict(self.span) if self.span else None,
            "state": dict(self.state),
            "detail": dict(self.detail),
        }