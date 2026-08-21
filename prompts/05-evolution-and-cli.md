# Prompt 05 — v0.5.0: Evolution & a face

## The story so far

Momo can live and Momo can die. But Momo cannot *change* — and cannot be
seen. This last version lets the pet grow up, and gives it a face in the
terminal. It also walks straight into an architecture constraint, on
purpose, to watch Telos slam the gate.

## Your mission

> Open a change. Let the **Pet**'s stage run `egg → baby → child →
> adult` and give it an `age`. Add a **RenderRequested** event and a
> **Portrait** value. State three intents: *pets grow up* (a baby
> becomes a child at age 10, a child becomes an adult at 25); *adults
> are harder to please* (**refines** the play intent: only +10
> happiness); *a face for the terminal* (**optional** — where the
> `ascii-art` feature is enabled, render a multi-line portrait). Add an
> **architecture constraint** with an executable check: the domain
> module must never import the rendering or CLI layers. Implement — and
> when the domain "just quickly" imports the renderer, let reconcile
> fail with `TELOS_CONSTRAINT_FAILED`, then fix it properly. Ship the
> interactive toy: `python -m tamagotchi --ascii-art`. Tag v0.5.0.

## Exact replay script

<!-- replay:cmd -->
```console
telos change open "let the pet grow up and be seen" --json
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos edit notion Pet --change CHG-0005 --json
```
```json
{"attrs": [{"name": "name", "type": "string"},
           {"name": "hunger", "type": "int"},
           {"name": "happiness", "type": "int"},
           {"name": "energy", "type": "int"},
           {"name": "age", "type": "int"},
           {"name": "weight", "type": "decimal"},
           {"name": "stage", "type": "enum",
            "values": ["egg", "baby", "child", "adult"]},
           {"name": "activity", "type": "enum", "values": ["awake", "asleep"]},
           {"name": "status", "type": "enum", "values": ["alive", "dead"]}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add notion --change CHG-0005 --json
```
```json
{"name": "RenderRequested", "kind": "event",
 "def": "Someone wants to look at the pet."}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add notion --change CHG-0005 --json
```
```json
{"name": "Portrait", "kind": "value",
 "def": "An ASCII rendering of the pet, at least a few lines tall.",
 "attrs": [{"name": "lines", "type": "int"}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add intent --change CHG-0005 --json
```
```json
{"title": "Pets grow up", "status": "active",
 "telos": "A pet frozen at one age is a photograph; care should have a future tense.",
 "statement": {"template": "event-driven", "when": "TimeTicks", "on": "Pet",
               "action": "advance Pet.age each tick; babies become children at 10, children become adults at 25"},
 "requires": ["INT-0004"],
 "scenarios": [
   {"title": "at ten ticks, a baby no more",
    "given": [{"notion": "Pet",
               "fields": {"stage": "baby", "age": 9, "activity": "awake"}}],
    "when": {"notion": "TimeTicks", "fields": {}},
    "then": ["Pet.stage in (child, adult)"]},
   {"title": "at twenty-five, all grown up",
    "given": [{"notion": "Pet",
               "fields": {"stage": "child", "age": 24, "activity": "awake"}}],
    "when": {"notion": "TimeTicks", "fields": {}},
    "then": ["Pet.stage == adult"]}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add intent --change CHG-0005 --json
```
```json
{"title": "Adults are harder to please", "status": "active",
 "telos": "Growing up means the same game brings a smaller joy.",
 "statement": {"template": "event-driven", "when": "PlayWithPet", "on": "Pet",
               "action": "when the pet is an adult, raise Pet.happiness by only 10"},
 "refines": ["INT-0003"],
 "scenarios": [
   {"title": "the same game, a smaller joy",
    "given": [{"notion": "Pet",
               "fields": {"stage": "adult", "activity": "awake",
                          "happiness": 50, "hunger": 40}}],
    "when": {"notion": "PlayWithPet", "fields": {}},
    "then": ["Pet.happiness == 60 and Pet.hunger == 50"]}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add intent --change CHG-0005 --json
```
```json
{"title": "A face for the terminal", "status": "active",
 "telos": "You cannot love what you cannot see.",
 "statement": {"template": "optional", "where": "ascii-art",
               "action": "render the pet as a multi-line ASCII portrait"},
 "scenarios": [
   {"title": "a portrait is at least a few lines tall",
    "given": [{"notion": "Pet", "fields": {"stage": "baby"}}],
    "when": {"notion": "RenderRequested", "fields": {}},
    "then": ["Portrait.lines >= 3"]}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add constraint --change CHG-0005 --json
```
```json
{"kind": "architecture", "title": "The domain never looks at the screen",
 "rule": {"text": "tamagotchi/pet.py must not import the rendering or CLI layers (tamagotchi.render, tamagotchi.cli, argparse, curses)."},
 "scope": "global",
 "check": "python3 tools/check_imports.py"}
```
<!-- replay:end -->

<!-- replay:cmd capture=digest -->
```console
telos change diff CHG-0005 --json
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos change approve CHG-0005 --expected-digest @digest --json
```
<!-- replay:end -->

### Implement

The constraint's check, first — like the fuzzer, it lives outside the
sealed globs and runs at every reconcile from now on:

<!-- replay:write tools/check_imports.py -->
```python
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
```
<!-- replay:end -->

Tests to their final bytes. `tests/test_play.py` is sealed and modified,
so SCN-0016 goes red first:

<!-- replay:write tests/test_play.py -->
```python
import pytest

from tamagotchi.pet import Activity, Pet, PetAsleepError, Stage, play


def scn_0004_a_game_cheers_the_pet_up_and_makes_it_peckish():
    pet = Pet(name="Momo", stage=Stage.BABY, hunger=40, happiness=50)
    play(pet)
    assert pet.happiness == 70
    assert pet.hunger == 50


def scn_0010_playing_with_a_sleeper_is_refused_and_changes_nothing():
    pet = Pet(name="Momo", stage=Stage.BABY, activity=Activity.ASLEEP,
              happiness=50)
    with pytest.raises(PetAsleepError):
        play(pet)
    assert pet.happiness == 50
    assert pet.activity is Activity.ASLEEP


def scn_0016_the_same_game_a_smaller_joy():
    pet = Pet(name="Momo", stage=Stage.ADULT, activity=Activity.AWAKE,
              happiness=50, hunger=40)
    play(pet)
    assert pet.happiness == 60
    assert pet.hunger == 50
```
<!-- replay:end -->

<!-- replay:write tests/test_grow.py -->
```python
from tamagotchi.pet import Activity, Pet, Stage, tick


def scn_0014_at_ten_ticks_a_baby_no_more():
    pet = Pet(name="Momo", stage=Stage.BABY, age=9, activity=Activity.AWAKE)
    tick(pet)
    assert pet.stage in (Stage.CHILD, Stage.ADULT)


def scn_0015_at_twenty_five_all_grown_up():
    pet = Pet(name="Momo", stage=Stage.CHILD, age=24,
              activity=Activity.AWAKE)
    tick(pet)
    assert pet.stage is Stage.ADULT
```
<!-- replay:end -->

<!-- replay:write tests/test_portrait.py -->
```python
from tamagotchi.pet import Pet, Stage
from tamagotchi.render import portrait


def scn_0017_a_portrait_is_at_least_a_few_lines_tall():
    pet = Pet(name="Momo", stage=Stage.BABY)
    assert len(portrait(pet).splitlines()) >= 3
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0016 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0014 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0015 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0017 --json
```
<!-- replay:end -->

The renderer — deliberately free of any import from the domain, so the
domain *could* stay clean… if it resists temptation:

<!-- replay:write tamagotchi/render.py -->
```python
"""ASCII portraits for every stage of a small life.

INT-0012: a face for the terminal. Imports nothing from the domain —
it reads the pet's gauges through plain attributes.
"""

_FACES = {
    "egg": [
        r"    ___    ",
        r"   /   \   ",
        r"  | . . |  ",
        r"   \___/   ",
    ],
    "baby": [
        r"  (\_ _/)  ",
        r"  ( o.o )  ",
        r"   > ^ <   ",
    ],
    "child": [
        r"  (\_ _/)  ",
        r"  ( ^.^ )  ",
        r"  ( u u )o ",
    ],
    "adult": [
        r"  /\_ _/\  ",
        r"  ( -.- )  ",
        r"  (  v  )  ",
        r"   |___|   ",
    ],
}

_DEAD = [
    r"    ___    ",
    r"   / + \   ",
    r"  | RIP |  ",
    r"   \___/   ",
]


def portrait(pet) -> str:
    """Render the pet as a multi-line ASCII portrait."""
    if str(pet.status) == "dead":
        lines = list(_DEAD)
    else:
        lines = list(_FACES[str(pet.stage)])
        if str(pet.activity) == "asleep":
            lines.append(r"    zZz    ")
    return "\n".join(lines)
```
<!-- replay:end -->

The domain — with the tempting mistake left in. Watch the last lines of
`_grow`: the pet wants to admire its new face, so the domain imports the
renderer. The tests will all pass. The constraint will not.

<!-- replay:write tamagotchi/pet.py -->
```python
"""The Tamagotchi domain: a pet, its needs, its whole small life.

Every behaviour here answers to an intent sealed in `telos/`.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from tamagotchi.render import portrait

FEED_RELIEF = 30
MEAL_WEIGHT = Decimal("0.10")
PLAY_JOY = 20
ADULT_PLAY_JOY = 10
PLAY_APPETITE = 10
TICK_APPETITE = 5
TICK_FATIGUE = 10
SLEEP_RECOVERY = 20
FULL_ENERGY = 100
STARVED = 100
CHILD_AT = 10
ADULT_AT = 25


class Stage(StrEnum):
    EGG = "egg"
    BABY = "baby"
    CHILD = "child"
    ADULT = "adult"


class Activity(StrEnum):
    AWAKE = "awake"
    ASLEEP = "asleep"


class Status(StrEnum):
    ALIVE = "alive"
    DEAD = "dead"


class PetAsleepError(Exception):
    """Raised when an interaction needs a pet that is awake."""


def _clamp(value: int) -> int:
    """INT-0009: vitals stay on the dial."""
    return max(0, min(100, value))


@dataclass
class Pet:
    name: str
    stage: Stage = Stage.EGG
    hunger: int = 0
    happiness: int = 50
    energy: int = FULL_ENERGY
    age: int = 0
    weight: Decimal = Decimal("1.00")
    activity: Activity = Activity.AWAKE
    status: Status = Status.ALIVE


def hatch(pet: Pet) -> None:
    """INT-0001: hatching brings a pet to life."""
    pet.stage = Stage.BABY


def feed(pet: Pet) -> None:
    """INT-0002: feeding takes the edge off hunger, and leaves a trace."""
    pet.hunger = _clamp(pet.hunger - FEED_RELIEF)
    pet.weight += MEAL_WEIGHT


def play(pet: Pet) -> None:
    """INT-0003 play lifts the mood, INT-0011 less so for adults,
    INT-0007 never while asleep."""
    if pet.activity is Activity.ASLEEP:
        raise PetAsleepError(f"{pet.name} is asleep; let them dream.")
    joy = ADULT_PLAY_JOY if pet.stage is Stage.ADULT else PLAY_JOY
    pet.happiness = _clamp(pet.happiness + joy)
    pet.hunger = _clamp(pet.hunger + PLAY_APPETITE)


def put_to_bed(pet: Pet) -> None:
    """INT-0005: a pet put to bed falls asleep."""
    pet.activity = Activity.ASLEEP


def tick(pet: Pet) -> None:
    """INT-0004 time gnaws, INT-0006 sleep restores, INT-0008 starvation,
    INT-0010 pets grow up."""
    if pet.activity is Activity.ASLEEP:
        pet.energy = _clamp(pet.energy + SLEEP_RECOVERY)
        if pet.energy >= FULL_ENERGY:
            pet.activity = Activity.AWAKE
    else:
        pet.hunger = _clamp(pet.hunger + TICK_APPETITE)
        pet.energy = _clamp(pet.energy - TICK_FATIGUE)
        if pet.hunger >= STARVED:
            pet.status = Status.DEAD
    if pet.status is Status.ALIVE:
        _grow(pet)


def _grow(pet: Pet) -> None:
    """INT-0010: pets grow up."""
    pet.age += 1
    if pet.stage is Stage.BABY and pet.age >= CHILD_AT:
        pet.stage = Stage.CHILD
        portrait(pet)  # the domain admires its new face
    elif pet.stage is Stage.CHILD and pet.age >= ADULT_AT:
        pet.stage = Stage.ADULT
        portrait(pet)  # and again
```
<!-- replay:end -->

The toy itself — the CLI layer is *allowed* to import everything:

<!-- replay:write tamagotchi/cli.py -->
```python
"""A tiny terminal life for Momo. (INT-0012, the ascii-art feature)"""
from __future__ import annotations

import argparse

from tamagotchi.pet import (
    Pet,
    PetAsleepError,
    Status,
    feed,
    hatch,
    play,
    put_to_bed,
    tick,
)
from tamagotchi.render import portrait

COMMANDS = "feed, play, sleep, wait, quit"


def vitals(pet: Pet) -> str:
    return (
        f"{pet.name} the {pet.stage} | hunger {pet.hunger} | "
        f"happiness {pet.happiness} | energy {pet.energy} | "
        f"{pet.activity}, age {pet.age}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tamagotchi")
    parser.add_argument("--ascii-art", action="store_true",
                        help="render the optional portrait (INT-0012)")
    parser.add_argument("--name", default="Momo")
    args = parser.parse_args(argv)

    pet = Pet(name=args.name)
    hatch(pet)
    print(f"{pet.name} hatched! Commands: {COMMANDS}")
    while pet.status is Status.ALIVE:
        if args.ascii_art:
            print(portrait(pet))
        print(vitals(pet))
        try:
            command = input("> ").strip().lower()
        except EOFError:
            print("\n(the terminal closes; the pet naps forever)")
            return 0
        if command == "quit":
            return 0
        if command == "feed":
            feed(pet)
        elif command == "play":
            try:
                play(pet)
            except PetAsleepError as asleep:
                print(asleep)
        elif command == "sleep":
            put_to_bed(pet)
        elif command not in ("", "wait"):
            print(f"unknown command; try: {COMMANDS}")
            continue
        tick(pet)
    if args.ascii_art:
        print(portrait(pet))
    print(f"{pet.name} has starved. Every death is a missing intent.")
    return 1
```
<!-- replay:end -->

<!-- replay:write tamagotchi/__main__.py -->
```python
"""`python -m tamagotchi` — raise Momo in your terminal."""
from tamagotchi.cli import main

raise SystemExit(main())
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos bind tamagotchi/pet.py INT-0010 --json
telos bind tamagotchi/pet.py INT-0011 --json
telos bind tamagotchi/render.py INT-0012 --json
telos bind tamagotchi/cli.py INT-0012 --json
telos bind tamagotchi/__main__.py INT-0012 --json
```
<!-- replay:end -->

Every witness goes green — the code *works*:

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0016 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0014 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0015 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0017 --json
```
<!-- replay:end -->

### The gate slams

Working code is not enough. Reconcile runs the constraint checks, and
`CON-0002` catches the domain peeking at the screen:

<!-- replay:cmd expect-error=TELOS_CONSTRAINT_FAILED -->
```console
telos change reconcile CHG-0005 --json
```
<!-- replay:end -->

Nothing was written — no seal, no `.tel`, nothing. Fix the domain (only
the *test* bytes are sealed by witnesses, so the implementation is free
to improve):

<!-- replay:write tamagotchi/pet.py -->
```python
"""The Tamagotchi domain: a pet, its needs, its whole small life.

Every behaviour here answers to an intent sealed in `telos/`.
CON-0002: this module never imports the rendering or CLI layers.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

FEED_RELIEF = 30
MEAL_WEIGHT = Decimal("0.10")
PLAY_JOY = 20
ADULT_PLAY_JOY = 10
PLAY_APPETITE = 10
TICK_APPETITE = 5
TICK_FATIGUE = 10
SLEEP_RECOVERY = 20
FULL_ENERGY = 100
STARVED = 100
CHILD_AT = 10
ADULT_AT = 25


class Stage(StrEnum):
    EGG = "egg"
    BABY = "baby"
    CHILD = "child"
    ADULT = "adult"


class Activity(StrEnum):
    AWAKE = "awake"
    ASLEEP = "asleep"


class Status(StrEnum):
    ALIVE = "alive"
    DEAD = "dead"


class PetAsleepError(Exception):
    """Raised when an interaction needs a pet that is awake."""


def _clamp(value: int) -> int:
    """INT-0009: vitals stay on the dial."""
    return max(0, min(100, value))


@dataclass
class Pet:
    name: str
    stage: Stage = Stage.EGG
    hunger: int = 0
    happiness: int = 50
    energy: int = FULL_ENERGY
    age: int = 0
    weight: Decimal = Decimal("1.00")
    activity: Activity = Activity.AWAKE
    status: Status = Status.ALIVE


def hatch(pet: Pet) -> None:
    """INT-0001: hatching brings a pet to life."""
    pet.stage = Stage.BABY


def feed(pet: Pet) -> None:
    """INT-0002: feeding takes the edge off hunger, and leaves a trace."""
    pet.hunger = _clamp(pet.hunger - FEED_RELIEF)
    pet.weight += MEAL_WEIGHT


def play(pet: Pet) -> None:
    """INT-0003 play lifts the mood, INT-0011 less so for adults,
    INT-0007 never while asleep."""
    if pet.activity is Activity.ASLEEP:
        raise PetAsleepError(f"{pet.name} is asleep; let them dream.")
    joy = ADULT_PLAY_JOY if pet.stage is Stage.ADULT else PLAY_JOY
    pet.happiness = _clamp(pet.happiness + joy)
    pet.hunger = _clamp(pet.hunger + PLAY_APPETITE)


def put_to_bed(pet: Pet) -> None:
    """INT-0005: a pet put to bed falls asleep."""
    pet.activity = Activity.ASLEEP


def tick(pet: Pet) -> None:
    """INT-0004 time gnaws, INT-0006 sleep restores, INT-0008 starvation,
    INT-0010 pets grow up."""
    if pet.activity is Activity.ASLEEP:
        pet.energy = _clamp(pet.energy + SLEEP_RECOVERY)
        if pet.energy >= FULL_ENERGY:
            pet.activity = Activity.AWAKE
    else:
        pet.hunger = _clamp(pet.hunger + TICK_APPETITE)
        pet.energy = _clamp(pet.energy - TICK_FATIGUE)
        if pet.hunger >= STARVED:
            pet.status = Status.DEAD
    if pet.status is Status.ALIVE:
        _grow(pet)


def _grow(pet: Pet) -> None:
    """INT-0010: pets grow up."""
    pet.age += 1
    if pet.stage is Stage.BABY and pet.age >= CHILD_AT:
        pet.stage = Stage.CHILD
    elif pet.stage is Stage.CHILD and pet.age >= ADULT_AT:
        pet.stage = Stage.ADULT
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos change reconcile CHG-0005 --json
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "telos status --json",
 "expect": {"result.state": "coherent",
            "result.coverage.intents_active": 12,
            "result.coverage.constraints": 2,
            "result.coverage.scenarios_proved": 17}}
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "telos check --sealed --json", "expect": {"ok": true}}
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "telos rebuild status --json",
 "expect": {"result.scenarios_green": 17, "result.scenarios_total": 17}}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
git add -A
git commit -q -m "v0.5: evolution & a face" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git tag v0.5.0
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "git status --porcelain", "expect_stdout": ""}
```
<!-- replay:end -->

The pet is complete. Meet it: `python -m tamagotchi --ascii-art`
