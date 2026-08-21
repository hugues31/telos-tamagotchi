# Prompt 07 — Your turn

*(No replay blocks in this file — from here on, the story is yours.)*

## The loose thread

Run the toy and watch closely:

```console
python -m tamagotchi --ascii-art
```

Let Momo starve (it takes about twenty ignored ticks). The portrait says
RIP… and yet `feed` still lowers the hunger of a corpse, and `play`
still cheers it up. **The dead are not beyond events** — because no
intent ever said they should be.

That is not a bug in the code. The code does exactly what the sealed
spec demands, and all 17 scenarios are green. It is a *hole in the
spec* — and in spec-driven development, that is where work begins.

## The challenge

State it, prove it, seal it:

> **A dead pet ignores every event.** Feeding, playing, tucking in —
> nothing moves a gauge anymore. Death is the one state no event can
> reach into.

Suggested path (the `telos-challenger` and `telos-implementer` skills
installed in `.claude/skills/` know this dance):

1. `telos status --json` — always first.
2. `telos change open "the dead are beyond events" --json`
3. `telos impact Pet --json` — see what your change will ripple through.
4. Stage an **unwanted** intent (`if Pet.status == dead`), with one
   scenario per event you silence. Decide for yourself: does the clock
   still tick for the dead? Does `age` freeze too?
5. `telos change diff` → `approve --expected-digest` — read before you
   sign.
6. Red witnesses, minimal code, green witnesses, `bind`, `reconcile`.
7. `git commit`, and if you are proud of it, `git tag v0.6.0`.

If you get stuck: every command answers `--json`, and `telos status`
always tells you the next legal move in `next_actions`.

## Beyond

- A `sick` state between `alive` and `dead`, cured by a new event?
- A `quality` constraint with an executable check that a dead pet's
  gauges never move again — fuzzer included?
- `telos view --port 3000` — watch your new intent appear in the graph,
  wired to everything it touches.

The spec is the pet's soul. Take good care of both.
