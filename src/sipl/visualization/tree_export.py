from __future__ import annotations
import html
import shutil
import subprocess
from pathlib import Path
from typing import Any
from lark import Token, Tree


def _extract_snippet(source: str, line: int, col: int, end_line: int, end_col: int) -> str:
    lines = source.splitlines()
    if not lines or line < 1 or line > len(lines):
        return ""
    if line == end_line:
        return lines[line - 1][max(0, col - 1) : max(0, end_col - 1)].strip()
    return lines[line - 1][max(0, col - 1) :].strip() + " ..."


def cst_to_dict(node: Tree[Token] | Token, source: str = "") -> dict[str, Any]:
    if isinstance(node, Token):
        line = node.line or 1
        col = node.column or 1
        end_line = node.end_line or line
        end_col = node.end_column or col
        return {
            "kind": "token",
            "type": node.type,
            "value": str(node),
            "span": {"line": line, "column": col, "end_line": end_line, "end_column": end_col},
            "snippet": str(node),
        }

    meta = node.meta
    line = getattr(meta, "line", 1)
    col = getattr(meta, "column", 1)
    end_line = getattr(meta, "end_line", line)
    end_col = getattr(meta, "end_column", col)
    return {
        "kind": "rule",
        "rule": str(node.data),
        "span": {"line": line, "column": col, "end_line": end_line, "end_column": end_col},
        "snippet": _extract_snippet(source, line, col, end_line, end_col) if source else "",
        "children": [cst_to_dict(child, source) for child in node.children],
    }


def cst_to_text(node: Tree[Token] | Token, source: str = "", indent: str = "", is_last: bool = True) -> str:
    branch = "└── " if is_last else "├── "
    if isinstance(node, Token):
        pos = f"{node.line}:{node.column}" if node.line else ""
        return f"{indent}{branch}{node.type}({node.value!r}) [{pos}]"

    meta = node.meta
    line = getattr(meta, "line", 1)
    col = getattr(meta, "column", 1)
    end_line = getattr(meta, "end_line", line)
    end_col = getattr(meta, "end_column", col)
    snippet = _extract_snippet(source, line, col, end_line, end_col) if source else ""
    snippet_part = f" :: {snippet!r}" if snippet else ""
    header = f"{indent}{branch}{node.data} [{line}:{col}-{end_line}:{end_col}]{snippet_part}"

    child_indent = indent + ("    " if is_last else "│   ")
    lines = [header]
    for i, child in enumerate(node.children):
        lines.append(cst_to_text(child, source, child_indent, i == len(node.children) - 1))
    return "\n".join(lines)


def cst_to_dot(tree: Tree[Token], source: str = "") -> str:
    dot_lines = [
        "digraph ParseTree {",
        '  node [shape=box, style="rounded,filled", fontname="Consolas", fontsize=10];',
    ]
    counter = 0

    def visit(node: Tree[Token] | Token) -> int:
        nonlocal counter
        node_id = counter
        counter += 1

        if isinstance(node, Token):
            label = f"{node.type}\\n{node.value}"
            escaped = html.escape(label).replace("\n", "\\n")
            dot_lines.append(f'  n{node_id} [label="{escaped}", fillcolor="#E8F5E9"];')
            return node_id

        meta = node.meta
        line = getattr(meta, "line", 1)
        col = getattr(meta, "column", 1)
        end_line = getattr(meta, "end_line", line)
        end_col = getattr(meta, "end_column", col)
        snippet = _extract_snippet(source, line, col, end_line, end_col) if source else ""
        label = f"{node.data} [{line}:{col}]" + (f"\\n{snippet}" if snippet else "")
        escaped = html.escape(label).replace("\n", "\\n")
        dot_lines.append(f'  n{node_id} [label="{escaped}", fillcolor="#E3F2FD"];')

        for child in node.children:
            child_id = visit(child)
            dot_lines.append(f"  n{node_id} -> n{child_id};")
        return node_id

    visit(tree)
    dot_lines.append("}")
    return "\n".join(dot_lines)


def export_svg(dot_source: str, output_svg: Path) -> bool:
    dot_bin = shutil.which("dot")
    if not dot_bin:
        return False
    output_svg.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [dot_bin, "-Tsvg", "-o", str(output_svg)],
        input=dot_source.encode("utf-8"),
        check=True,
    )
    return True