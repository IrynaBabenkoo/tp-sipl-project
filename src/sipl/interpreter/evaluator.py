from __future__ import annotations
from dataclasses import dataclass
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
from sipl.interpreter.trace import EventType, TraceEvent


class SIPLRuntimeError(Exception):
    pass


class StepLimitExceededError(SIPLRuntimeError):
    def __init__(self, max_steps: int) -> None:
        super().__init__(f"Execution exceeded maximum step limit ({max_steps})")
        self.max_steps = max_steps


@dataclass
class ExecutionResult:
    final_state: dict[str, int]
    steps: int
    trace: list[TraceEvent]


class SIPLInterpreter:
    def __init__(self, max_steps: int = 10_000, record_trace: bool = True) -> None:
        self.max_steps = max_steps
        self.record_trace = record_trace
        self._steps = 0
        self._trace: list[TraceEvent] = []
        self._state: dict[str, int] = {}

    def run(self, program: Program, initial_state: dict[str, int] | None = None) -> ExecutionResult:
        self._steps = 0
        self._trace = []
        self._state = dict(initial_state) if initial_state else {}

        self._exec_stmt(program.stmt)
        self._emit("Finished", "Program", program.span, {"steps": self._steps})

        return ExecutionResult(
            final_state=dict(self._state),
            steps=self._steps,
            trace=list(self._trace),
        )

    def _emit(
        self,
        event: EventType,
        stmt_type: str,
        span: object,
        detail: dict[str, object] | None = None,
    ) -> None:
        if not self.record_trace:
            return
        self._trace.append(
            TraceEvent(
                step=self._steps,
                event=event,
                stmt_type=stmt_type,
                span=span,  # type: ignore[arg-type]
                state=dict(self._state),
                detail=detail or {},
            )
        )

    def _tick(self) -> None:
        self._steps += 1
        if self._steps > self.max_steps:
            raise StepLimitExceededError(self.max_steps)

    def _eval_aexp(self, expr: Aexp) -> int:
        if isinstance(expr, NumExpr):
            return expr.value
        if isinstance(expr, VarExpr):
            if expr.name not in self._state:
                raise SIPLRuntimeError(
                    f"Undefined variable '{expr.name}' at {expr.span.line}:{expr.span.column}"
                )
            return self._state[expr.name]
        if isinstance(expr, BinArithExpr):
            left = self._eval_aexp(expr.left)
            right = self._eval_aexp(expr.right)
            if expr.op == "+":
                return left + right
            if expr.op == "-":
                return left - right
            if expr.op == "*":
                return left * right
        raise SIPLRuntimeError(f"Unsupported arithmetic expression: {expr}")

    def _eval_bexp(self, expr: Bexp) -> bool:
        if isinstance(expr, CompareExpr):
            left = self._eval_aexp(expr.left)
            right = self._eval_aexp(expr.right)
            if expr.op == "=":
                return left == right
            if expr.op == ">":
                return left > right
            if expr.op == "<":
                return left < right
            if expr.op == ">=":
                return left >= right
            if expr.op == "<=":
                return left <= right
        if isinstance(expr, NegExpr):
            return not self._eval_bexp(expr.expr)
        if isinstance(expr, OrExpr):
            return self._eval_bexp(expr.left) or self._eval_bexp(expr.right)
        raise SIPLRuntimeError(f"Unsupported boolean expression: {expr}")

    def _exec_stmt(self, stmt: Stmt) -> None:
        stmt_name = stmt.__class__.__name__

        if isinstance(stmt, SeqStmt):
            self._exec_stmt(stmt.first)
            self._exec_stmt(stmt.second)
            return

        if isinstance(stmt, BlockStmt):
            self._exec_stmt(stmt.stmt)
            return

        self._tick()
        self._emit("BeforeStatement", stmt_name, stmt.span)

        if isinstance(stmt, SkipStmt):
            pass
        elif isinstance(stmt, AssignStmt):
            old_val = self._state.get(stmt.var)
            new_val = self._eval_aexp(stmt.expr)
            self._state[stmt.var] = new_val
            self._emit(
                "VarAssigned",
                stmt_name,
                stmt.span,
                {"var": stmt.var, "old": old_val, "new": new_val},
            )
        elif isinstance(stmt, IfStmt):
            cond_val = self._eval_bexp(stmt.cond)
            self._emit("ConditionEvaluated", stmt_name, stmt.cond.span, {"result": cond_val})
            if cond_val:
                self._exec_stmt(stmt.then_branch)
            else:
                self._exec_stmt(stmt.else_branch)
        elif isinstance(stmt, WhileStmt):
            while True:
                cond_val = self._eval_bexp(stmt.cond)
                self._emit("ConditionEvaluated", stmt_name, stmt.cond.span, {"result": cond_val})
                if not cond_val:
                    break
                self._exec_stmt(stmt.body)
                self._tick()
        else:
            raise SIPLRuntimeError(f"Unsupported statement: {stmt}")

        self._emit("AfterStatement", stmt_name, stmt.span)