#!/usr/bin/env python3
"""Replay the Tamagotchi story from the prompt files.

Every ``prompts/NN-*.md`` file mixes prose (for humans and coding agents)
with machine-readable blocks. This driver executes those blocks, in file
order, against a target directory, and proves that the story reproduces
bit-for-bit. Three directives exist, each closed by ``<!-- replay:end -->``:

  <!-- replay:cmd [capture=digest|token] [expect-witness=red|green]
       [expect-error=CODE] -->
    One fenced ``console`` block, one command per line, split with shlex
    and executed directly (never through a shell). An optional second
    fenced ``json`` block is piped to stdin (single-command blocks only).
    ``@digest`` and ``@token`` argv elements are replaced by the last
    captured values.

  <!-- replay:write <path> -->
    The fenced block becomes the complete content of <path> (plus a final
    newline), replacing whatever was there.

  <!-- replay:check -->
    A fenced ``json`` spec: {"run": "...", "expect": {"result.x": 1}} to
    assert dotted paths of the command's JSON envelope, or
    {"run": "...", "expect_stdout": "..."} to assert trimmed stdout.

Requirements on PATH: ``telos`` (or pass --telos) and ``pytest``.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

OPEN_RE = re.compile(r"^<!--\s*replay:(cmd|write|check)(.*?)-->\s*$")
END_RE = re.compile(r"^<!--\s*replay:end\s*-->\s*$")
FENCE_RE = re.compile(r"^```")
SHELL_OPERATORS = {"|", "||", "&&", ";", "&", ">", ">>", "<", "<<"}
EXPECTED_TAGS = ["v0.0.0", "v0.1.0", "v0.2.0", "v0.3.0", "v0.4.0", "v0.5.0"]
COMPARE_SKIP = {".git", "__pycache__", ".pytest_cache", ".venv", "site"}


@dataclass
class Block:
    source: str
    line: int
    directive: str
    attrs: dict[str, str] = field(default_factory=dict)
    path: str | None = None
    fences: list[str] = field(default_factory=list)

    def where(self) -> str:
        return f"{self.source}:{self.line}"


def parse_prompt(path: Path) -> list[Block]:
    blocks: list[Block] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        match = OPEN_RE.match(lines[i])
        if not match:
            if END_RE.match(lines[i]):
                raise SystemExit(f"{path.name}:{i + 1}: replay:end without an open block")
            i += 1
            continue
        directive, rest = match.group(1), match.group(2).strip()
        block = Block(source=path.name, line=i + 1, directive=directive)
        if directive == "write":
            if not rest or "=" in rest:
                raise SystemExit(f"{block.where()}: replay:write needs a file path")
            block.path = rest
        else:
            for word in rest.split():
                if "=" not in word:
                    raise SystemExit(f"{block.where()}: bad attribute `{word}`")
                key, value = word.split("=", 1)
                block.attrs[key] = value
        i += 1
        fence: list[str] | None = None
        while i < len(lines) and not END_RE.match(lines[i]):
            if OPEN_RE.match(lines[i]):
                raise SystemExit(f"{block.where()}: block is never closed")
            if FENCE_RE.match(lines[i]):
                if fence is None:
                    fence = []
                else:
                    block.fences.append("\n".join(fence))
                    fence = None
            elif fence is not None:
                fence.append(lines[i])
            i += 1
        if i == len(lines):
            raise SystemExit(f"{block.where()}: block is never closed")
        if fence is not None:
            raise SystemExit(f"{block.where()}: unterminated code fence")
        i += 1
        if not block.fences:
            raise SystemExit(f"{block.where()}: block has no fenced content")
        blocks.append(block)
    return blocks


class Replay:
    def __init__(self, target: Path, telos: str | None):
        self.target = target
        self.telos = telos
        self.captures: dict[str, str] = {}

    def argv(self, line: str, where: str) -> list[str]:
        argv = shlex.split(line)
        for word in argv:
            if word in SHELL_OPERATORS or "$(" in word or "`" in word:
                raise SystemExit(
                    f"{where}: `{word}` looks like shell syntax; commands run "
                    "without a shell, one argv per line"
                )
        argv = [self.captures[w[1:]] if w in ("@digest", "@token") else w for w in argv]
        if self.telos and argv and argv[0] == "telos":
            argv[0] = self.telos
        return argv

    def run(self, argv: list[str], stdin: str | None) -> subprocess.CompletedProcess:
        return subprocess.run(
            argv,
            cwd=self.target,
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
        )

    def fail(self, where: str, argv: list[str], proc: subprocess.CompletedProcess, why: str):
        print(f"\nFAIL {where}: {why}", file=sys.stderr)
        print(f"  command: {shlex.join(argv)}", file=sys.stderr)
        print(f"  exit:    {proc.returncode}", file=sys.stderr)
        if proc.stdout:
            print(f"  stdout:  {proc.stdout.rstrip()}", file=sys.stderr)
        if proc.stderr:
            print(f"  stderr:  {proc.stderr.rstrip()}", file=sys.stderr)
        raise SystemExit(1)

    def envelope(self, where, argv, proc) -> dict:
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            self.fail(where, argv, proc, "stdout is not a JSON envelope")

    def exec_cmd(self, block: Block):
        commands = [l for l in block.fences[0].splitlines() if l.strip()]
        stdin = block.fences[1] if len(block.fences) > 1 else None
        if stdin is not None and len(commands) != 1:
            raise SystemExit(f"{block.where()}: a stdin payload needs exactly one command")
        for line in commands:
            argv = self.argv(line, block.where())
            proc = self.run(argv, stdin)
            wants_json = "--json" in argv
            note = ""
            if "expect-error" in block.attrs:
                code = block.attrs["expect-error"]
                if proc.returncode == 0:
                    self.fail(block.where(), argv, proc, f"expected {code}, got success")
                got = self.envelope(block.where(), argv, proc)["error"] or {}
                if got.get("code") != code:
                    self.fail(block.where(), argv, proc, f"expected {code}, got {got.get('code')}")
                note = f"error={code} as scripted"
            elif proc.returncode != 0:
                self.fail(block.where(), argv, proc, "command failed")
            elif wants_json:
                result = self.envelope(block.where(), argv, proc).get("result") or {}
                if "expect-witness" in block.attrs:
                    want = block.attrs["expect-witness"]
                    if result.get("witness") != want:
                        self.fail(
                            block.where(), argv, proc,
                            f"expected witness={want}, got {result.get('witness')}",
                        )
                    note = f"witness={want}"
                if "capture" in block.attrs:
                    name = block.attrs["capture"]
                    value = result.get("digest") if name == "digest" else (
                        (result.get("drift") or {}).get("token")
                    )
                    if not value:
                        self.fail(block.where(), argv, proc, f"nothing to capture as @{name}")
                    self.captures[name] = value
                    note = f"captured @{name}"
            print(f"  $ {line}" + (f"  ..{note}" if note else ""))

    def exec_write(self, block: Block):
        path = self.target / block.path
        if not path.resolve().is_relative_to(self.target.resolve()):
            raise SystemExit(f"{block.where()}: path escapes the target")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(block.fences[0] + "\n", encoding="utf-8")
        print(f"  wrote {block.path}")

    def exec_check(self, block: Block):
        spec = json.loads(block.fences[0])
        argv = self.argv(spec["run"], block.where())
        proc = self.run(argv, None)
        if proc.returncode != 0:
            self.fail(block.where(), argv, proc, "check command failed")
        if "expect_stdout" in spec:
            if proc.stdout.strip() != spec["expect_stdout"].strip():
                self.fail(block.where(), argv, proc, "stdout does not match")
        for dotted, want in spec.get("expect", {}).items():
            node = self.envelope(block.where(), argv, proc)
            for part in dotted.split("."):
                node = node.get(part) if isinstance(node, dict) else None
            if node != want:
                self.fail(block.where(), argv, proc, f"{dotted} is {node!r}, expected {want!r}")
        checked = ", ".join(spec.get("expect", {})) or "stdout"
        print(f"  ✓ {spec['run']}  ({checked})")

    def exec_block(self, block: Block):
        {"cmd": self.exec_cmd, "write": self.exec_write, "check": self.exec_check}[
            block.directive
        ](block)


def compare(target: Path, source: Path):
    print(f"\n[compare] target {target} against {source}")
    mismatches = []
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(target)
        if any(part in COMPARE_SKIP for part in rel.parts):
            continue
        twin = source / rel
        if not twin.is_file():
            mismatches.append(f"only in replay: {rel}")
        elif twin.read_bytes() != path.read_bytes():
            mismatches.append(f"differs: {rel}")
    lock = target / "telos" / "telos.lock"
    if not lock.is_file():
        mismatches.append("missing: telos/telos.lock")
    tags = subprocess.run(
        ["git", "tag", "--list"], cwd=target, capture_output=True, text=True, check=True
    ).stdout.split()
    if sorted(tags) != EXPECTED_TAGS:
        mismatches.append(f"tags are {sorted(tags)}, expected {EXPECTED_TAGS}")
    if mismatches:
        for line in mismatches:
            print(f"  ✗ {line}", file=sys.stderr)
        raise SystemExit(1)
    print(f"  ✓ every replayed file matches, tags {', '.join(EXPECTED_TAGS)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", help="directory to replay into (default: a temp dir)")
    parser.add_argument("--through", metavar="NN", help="stop after the prompt numbered NN")
    parser.add_argument(
        "--in-place", action="store_true",
        help="replay into this repository itself (canonical build)",
    )
    parser.add_argument("--compare", action="store_true",
                        help="after the replay, require the target to match this repository")
    parser.add_argument("--telos", help="path to the telos binary (default: from PATH)")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    prompts = sorted((root / "prompts").glob("[0-9][0-9]-*.md"))
    if args.through:
        prompts = [p for p in prompts if p.name[:2] <= args.through]
    if args.in_place:
        target = root
    elif args.target:
        target = Path(args.target).resolve()
        target.mkdir(parents=True, exist_ok=True)
    else:
        target = Path(tempfile.mkdtemp(prefix="tamagotchi-replay-"))
    replay = Replay(target, args.telos)

    print(f"replaying {len(prompts)} prompt(s) into {target}")
    for prompt in prompts:
        print(f"\n[{prompt.stem}]")
        for block in parse_prompt(prompt):
            replay.exec_block(block)
    if args.compare:
        compare(target, root)
    print("\nreplay complete")


if __name__ == "__main__":
    main()
