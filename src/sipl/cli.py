from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from sipl.interpreter.evaluator import SIPLInterpreter, SIPLRuntimeError
from sipl.parser import SIPLSyntaxError, parse_cst, parse_program
from sipl.visualization.tree_export import cst_to_dict, cst_to_dot, cst_to_text, export_svg


def _parse_state(pairs: list[str] | None) -> dict[str, int]:
    state: dict[str, int] = {}
    if not pairs:
        return state
    for item in pairs:
        if "=" not in item:
            raise ValueError(f"Invalid variable assignment '{item}', expected VAR=INT")
        key, raw_val = item.split("=", 1)
        state[key.strip()] = int(raw_val.strip())
    return state


def _read_source(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sipl", description="SIPL Language Toolkit CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="Validate SIPL syntax")
    p_check.add_argument("file", help="Path to .sipl file")
    p_check.add_argument("--json", action="store_true", help="Output JSON")

    p_parse = sub.add_parser("parse", help="Parse SIPL file to AST")
    p_parse.add_argument("file", help="Path to .sipl file")
    p_parse.add_argument("--json", action="store_true", help="Output JSON")

    p_run = sub.add_parser("run", help="Execute SIPL program")
    p_run.add_argument("file", help="Path to .sipl file")
    p_run.add_argument("--var", action="append", help="Initial variable VAR=INT")
    p_run.add_argument("--max-steps", type=int, default=10_000, help="Max execution steps")
    p_run.add_argument("--json", action="store_true", help="Output JSON")

    p_trace = sub.add_parser("trace", help="Execute SIPL program with event trace")
    p_trace.add_argument("file", help="Path to .sipl file")
    p_trace.add_argument("--var", action="append", help="Initial variable VAR=INT")
    p_trace.add_argument("--max-steps", type=int, default=10_000, help="Max execution steps")
    p_trace.add_argument("--json", action="store_true", help="Output JSON")

    p_tree = sub.add_parser("tree", help="Export parse tree (text, json, dot, svg)")
    p_tree.add_argument("file", help="Path to .sipl file")
    p_tree.add_argument("--format", choices=["text", "json", "dot", "svg"], default="text")
    p_tree.add_argument("-o", "--output", help="Output file path (required for svg)")

    args = parser.parse_args(argv)

    try:
        source = _read_source(args.file)

        if args.command == "check":
            parse_program(source)
            if args.json:
                print(json.dumps({"status": "ok", "file": args.file}, ensure_ascii=False))
            else:
                print(f"OK: {args.file}")
            return 0

        if args.command == "parse":
            ast = parse_program(source)
            if args.json:
                print(json.dumps(ast.to_dict(), indent=2, ensure_ascii=False))
            else:
                print(ast)
            return 0

        if args.command in ("run", "trace"):
            program = parse_program(source)
            init_state = _parse_state(args.var)
            res = SIPLInterpreter(
                max_steps=args.max_steps,
                record_trace=(args.command == "trace"),
            ).run(program, init_state)

            if args.command == "run":
                if args.json:
                    print(
                        json.dumps(
                            {"status": "ok", "steps": res.steps, "state": res.final_state},
                            indent=2,
                            ensure_ascii=False,
                        )
                    )
                else:
                    print(f"Steps: {res.steps}")
                    print(f"Final state: {res.final_state}")
            else:
                events = [e.to_dict() for e in res.trace]
                if args.json:
                    print(
                        json.dumps(
                            {
                                "status": "ok",
                                "steps": res.steps,
                                "state": res.final_state,
                                "trace": events,
                            },
                            indent=2,
                            ensure_ascii=False,
                        )
                    )
                else:
                    for ev in res.trace:
                        print(f"[{ev.step}] {ev.event} ({ev.stmt_type}) -> {ev.state}")
            return 0

        if args.command == "tree":
            cst = parse_cst(source)
            if args.format == "text":
                rendered = cst_to_text(cst, source)
            elif args.format == "json":
                rendered = json.dumps(cst_to_dict(cst, source), indent=2, ensure_ascii=False)
            elif args.format == "dot":
                rendered = cst_to_dot(cst, source)
            else:
                if not args.output:
                    print("Error: --output is required for svg format", file=sys.stderr)
                    return 2
                dot_src = cst_to_dot(cst, source)
                if not export_svg(dot_src, Path(args.output)):
                    print("Error: Graphviz 'dot' binary not found in PATH", file=sys.stderr)
                    return 2
                print(f"SVG written to {args.output}")
                return 0

            if args.output:
                Path(args.output).write_text(rendered, encoding="utf-8")
                print(f"Written to {args.output}")
            else:
                print(rendered)
            return 0

    except (OSError, ValueError, SIPLSyntaxError, SIPLRuntimeError) as exc:
        if getattr(args, "json", False):
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())