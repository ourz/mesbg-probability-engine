from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import solve_combat
from .errors import MESBGProbabilityError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Exact MESBG combat probability solver")
    parser.add_argument("command", choices=["solve", "validate"])
    parser.add_argument("input", type=Path, help="combat-input-v1 JSON file")
    parser.add_argument("--output", type=Path, help="write JSON output to this file")
    parser.add_argument("--indent", type=int, default=2)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        result = solve_combat(raw)
        if args.command == "validate":
            result = {
                "valid": True,
                "schema_version": result["schema_version"],
                "engine_version": result["engine_version"],
                "input_sha256": result["input_sha256"],
            }
        text = json.dumps(result, indent=args.indent, ensure_ascii=False, sort_keys=True)
        if args.output:
            args.output.write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
        return 0
    except (OSError, json.JSONDecodeError, MESBGProbabilityError, KeyError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
