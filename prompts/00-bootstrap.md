# Prompt 00 — Bootstrap: an empty nest

## The story so far

Nothing exists yet. You are about to raise a Tamagotchi called **Momo** —
but this pet will be *spec-first*: before a single line of Python is
written, every behaviour will be captured as a typed intent in
[Telos](https://github.com/hugues31/telos-sdd), sealed by hash, and proven
by red-then-green test witnesses. The code is just one possible solution
of the spec; the spec is the pet's soul.

You need two tools on your PATH:

- `telos` — a single self-contained binary, no Rust toolchain needed:

  ```console
  curl -fsSL https://raw.githubusercontent.com/hugues31/telos-sdd/main/install.sh | TELOS_VERSION=v0.7.1 sh
  ```

  (The script verifies the release's SHA-256 checksum and installs to
  `~/.local/bin`. This story was sealed with v0.7.1 — pinning the
  version keeps your replay byte-identical.)
- `pytest` — `python3 -m venv .venv && .venv/bin/pip install pytest`, then
  put `.venv/bin` on your PATH (Telos will invoke `pytest` to seal test
  verdicts).

## Your mission

> Initialize an empty git repository as a Telos workspace, with the Claude
> Code agent skills and the GitHub CI gate installed. Commit the sealed
> empty spec as version v0.0.0 — the nest, before the egg.

If you are a coding agent: after `telos init --agents claude` the
`.claude/skills/` directory tells you exactly how to behave from now on.
Start every future session with `telos status --json`.

## Exact replay script

The `.gitignore` first, so no cache ever pollutes a version commit:

<!-- replay:write .gitignore -->
```text
__pycache__/
.pytest_cache/
.venv/
site/
```
<!-- replay:end -->

A Telos workspace *is* a git repository — the seal stores git blob OIDs:

<!-- replay:cmd -->
```console
git init
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos init --agents claude --ci github --json
```
<!-- replay:end -->

The project is born `coherent`: an empty spec, already sealed.

<!-- replay:check -->
```json
{"run": "telos status --json",
 "expect": {"ok": true, "result.state": "coherent"}}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
git add -A
git commit -q -m "v0.0: the nest, before the egg" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git tag v0.0.0
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "git status --porcelain", "expect_stdout": ""}
```
<!-- replay:end -->
