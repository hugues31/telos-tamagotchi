# Prompt 06 — The drift incident

## The story so far

Momo is complete, sealed, tagged v0.5.0. Then one evening, someone —
a tired human, an overeager agent, a merge gone sideways — edits a spec
file *by hand*, bypassing the change protocol entirely.

This prompt does it on purpose, to show what Telos does about it. The
final state of the repository is unchanged: this incident leaves no
trace except understanding.

## Your mission

> Vandalize `telos/notions/Pet.tel` directly on disk. Watch `telos
> status` flip to `drifted` and every mutating command refuse to run.
> Then choose one of the two exits — `telos adopt` (capture the edit as
> a reviewable change) or `telos revert` (restore the sealed bytes) —
> and prove the project is coherent again.

Here we take `revert`: the edit was noise, not intent. If it had been a
genuine improvement, `telos adopt` would stage it into a change for
review — out-of-protocol bytes get sealed by the change that reviews
them, or not at all.

## Exact replay script

The vandalism — a hand edit that softens the pet's definition
(`depends entirely on` becomes `mildly tolerates`):

<!-- replay:write telos/notions/Pet.tel -->
```text
notion Pet entity {
  def  "A small creature that mildly tolerates its Owner."
  attr name      string
  attr hunger    int
  attr happiness int
  attr energy    int
  attr age       int
  attr weight    decimal
  attr stage     enum(egg, baby, child, adult)
  attr activity  enum(awake, asleep)
  attr status    enum(alive, dead)
  rel  owned-by -> Owner
}
```
<!-- replay:end -->

The seal notices immediately — the file's git blob OID no longer matches
the lock. The drift token authenticates exactly *this* drift:

<!-- replay:cmd capture=token -->
```console
telos status --json
```
<!-- replay:end -->

While drifted, the workflow is frozen — you cannot even open a change:

<!-- replay:cmd expect-error=TELOS_DRIFT_DETECTED -->
```console
telos change open "sneak something in while nobody looks" --json
```
<!-- replay:end -->

The exit we choose: throw the edit away. `--expected-state` pins the
revert to the exact drift we saw — if anything else moved meanwhile, the
command refuses:

<!-- replay:cmd -->
```console
telos revert --expected-state @token --json
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "telos status --json", "expect": {"result.state": "coherent"}}
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "telos check --sealed --json", "expect": {"ok": true}}
```
<!-- replay:end -->

The sealed bytes came back from git's object store, so the working tree
matches the last commit exactly — the incident never happened:

<!-- replay:check -->
```json
{"run": "git status --porcelain", "expect_stdout": ""}
```
<!-- replay:end -->
