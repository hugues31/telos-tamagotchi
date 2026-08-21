#!/usr/bin/env python3
"""CON-0002: the domain must never look at the screen."""
import ast
import sys
from pathlib import Path

FORBIDDEN = ("tamagotchi.render", "tamagotchi.cli", "argparse", "curses")


def main() -> int:
    source = Path(__file__).resolve().parent.parent / "tamagotchi" / "pet.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            if any(name == f or name.startswith(f + ".") for f in FORBIDDEN):
                print(f"tamagotchi/pet.py imports `{name}`: the domain "
                      "must not know how it is drawn", file=sys.stderr)
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
