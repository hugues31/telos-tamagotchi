# Prompt 04 — v0.4.0: Neglect & death

## The story so far

Momo lives by the clock now — eating, playing, sleeping. Which means
Momo can also be neglected. A Tamagotchi without consequences is a
screensaver; this version gives the story stakes.

## Your mission

> Open a change. Give the **Pet** a `status` (alive or dead). State two
> intents: *starvation is not a lifestyle* (**unwanted** — if hunger ever
> reaches 100, the pet dies: `set Pet.status = dead`) and *vitals stay on
> the dial* (**ubiquitous** — hunger, happiness and energy are always
> clamped to 0..100). Then add the project's first **constraint**: a
> `quality` rule with an executable check, `python3
> tools/check_vitals.py`, a deterministic fuzzer that replays hundreds of
> random days and fails if any gauge ever leaves the dial. Reconcile runs
> that check as one of its gates. Tag v0.4.0.

A constraint bounds *every* solution, present and future — the fuzzer
will keep running at every future reconcile, long after this change is
forgotten.

## Exact replay script

<!-- replay:cmd -->
```console
telos change open "give neglect its consequences" --json
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos edit notion Pet --change CHG-0004 --json
```
```json
{"attrs": [{"name": "name", "type": "string"},
           {"name": "hunger", "type": "int"},
           {"name": "happiness", "type": "int"},
           {"name": "energy", "type": "int"},
           {"name": "weight", "type": "decimal"},
           {"name": "stage", "type": "enum", "values": ["egg", "baby"]},
           {"name": "activity", "type": "enum", "values": ["awake", "asleep"]},
           {"name": "status", "type": "enum", "values": ["alive", "dead"]}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add intent --change CHG-0004 --json
```
```json
{"title": "Starvation is not a lifestyle", "status": "active",
 "telos": "A pet that cannot die makes neglect free, and care meaningless.",
 "statement": {"template": "unwanted",
               "if": "Pet.hunger >= 100",
               "action": "set Pet.status = dead"},
 "requires": ["INT-0004"],
 "scenarios": [
   {"title": "the tick that fills the gauge is the last",
    "given": [{"notion": "Pet",
               "fields": {"stage": "baby", "status": "alive",
                          "activity": "awake", "hunger": 95, "energy": 50}}],
    "when": {"notion": "TimeTicks", "fields": {}},
    "then": ["Pet.hunger == 100", "Pet.status == dead"]}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add intent --change CHG-0004 --json
```
```json
{"title": "Vitals stay on the dial", "status": "active",
 "telos": "A gauge that reads 130 is a lie wearing a number.",
 "statement": {"template": "ubiquitous",
               "action": "clamp Pet.hunger, Pet.happiness and Pet.energy to 0..100"},
 "scenarios": [
   {"title": "joy tops out at one hundred",
    "given": [{"notion": "Pet",
               "fields": {"stage": "baby", "activity": "awake",
                          "happiness": 95, "hunger": 40}}],
    "when": {"notion": "PlayWithPet", "fields": {}},
    "then": ["Pet.happiness == 100"]},
   {"title": "weariness bottoms out at zero",
    "given": [{"notion": "Pet",
               "fields": {"stage": "baby", "activity": "awake",
                          "energy": 5}}],
    "when": {"notion": "TimeTicks", "fields": {}},
    "then": ["Pet.energy == 0"]}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add constraint --change CHG-0004 --json
```
```json
{"kind": "quality", "title": "No gauge ever leaves the dial",
 "rule": {"text": "After any sequence of events, hunger, happiness and energy read between 0 and 100."},
 "scope": "global",
 "check": "python3 tools/check_vitals.py"}
```
<!-- replay:end -->

<!-- replay:cmd capture=digest -->
```console
telos change diff CHG-0004 --json
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos change approve CHG-0004 --expected-digest @digest --json
```
<!-- replay:end -->

### Implement

The fuzzer lives in `tools/` — outside the sealed globs, invoked by the
constraint's check at every reconcile:

<!-- replay:write tools/check_vitals.py -->
```python
#!/usr/bin/env python3
"""CON-0001: replay hundreds of random days; no gauge may leave 0..100."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tamagotchi.pet import Pet, PetAsleepError, feed, hatch, play, put_to_bed, tick

ACTIONS = ("feed", "play", "sleep", "tick")
DAYS = 500
BEATS = 40


def main() -> int:
    rng = random.Random(0)
    for day in range(DAYS):
        pet = Pet(name="Fuzz")
        hatch(pet)
        for beat in range(BEATS):
            action = rng.choice(ACTIONS)
            try:
                if action == "feed":
                    feed(pet)
                elif action == "play":
                    play(pet)
                elif action == "sleep":
                    put_to_bed(pet)
                else:
                    tick(pet)
            except PetAsleepError:
                pass
            for gauge in ("hunger", "happiness", "energy"):
                value = getattr(pet, gauge)
                if not 0 <= value <= 100:
                    print(f"day {day}, beat {beat}: after {action}, "
                          f"{gauge} reads {value}", file=sys.stderr)
                    return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
<!-- replay:end -->

<!-- replay:write tests/test_death.py -->
```python
from tamagotchi.pet import Activity, Pet, Stage, Status, tick


def scn_0011_the_tick_that_fills_the_gauge_is_the_last():
    pet = Pet(name="Momo", stage=Stage.BABY, status=Status.ALIVE,
              activity=Activity.AWAKE, hunger=95, energy=50)
    tick(pet)
    assert pet.hunger == 100
    assert pet.status is Status.DEAD
```
<!-- replay:end -->

<!-- replay:write tests/test_vitals.py -->
```python
from tamagotchi.pet import Activity, Pet, Stage, play, tick


def scn_0012_joy_tops_out_at_one_hundred():
    pet = Pet(name="Momo", stage=Stage.BABY, activity=Activity.AWAKE,
              happiness=95, hunger=40)
    play(pet)
    assert pet.happiness == 100


def scn_0013_weariness_bottoms_out_at_zero():
    pet = Pet(name="Momo", stage=Stage.BABY, activity=Activity.AWAKE,
              energy=5)
    tick(pet)
    assert pet.energy == 0
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0011 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0012 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0013 --json
```
<!-- replay:end -->

<!-- replay:write tamagotchi/pet.py -->
```python
"""The Tamagotchi domain: a pet, its needs, and the price of neglect.

Every behaviour here answers to an intent sealed in `telos/`.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

FEED_RELIEF = 30
MEAL_WEIGHT = Decimal("0.10")
PLAY_JOY = 20
PLAY_APPETITE = 10
TICK_APPETITE = 5
TICK_FATIGUE = 10
SLEEP_RECOVERY = 20
FULL_ENERGY = 100
STARVED = 100


class Stage(StrEnum):
    EGG = "egg"
    BABY = "baby"


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
    """INT-0003: playing lifts the mood. INT-0007: never while asleep."""
    if pet.activity is Activity.ASLEEP:
        raise PetAsleepError(f"{pet.name} is asleep; let them dream.")
    pet.happiness = _clamp(pet.happiness + PLAY_JOY)
    pet.hunger = _clamp(pet.hunger + PLAY_APPETITE)


def put_to_bed(pet: Pet) -> None:
    """INT-0005: a pet put to bed falls asleep."""
    pet.activity = Activity.ASLEEP


def tick(pet: Pet) -> None:
    """INT-0004 time gnaws, INT-0006 sleep restores, INT-0008 starvation."""
    if pet.activity is Activity.ASLEEP:
        pet.energy = _clamp(pet.energy + SLEEP_RECOVERY)
        if pet.energy >= FULL_ENERGY:
            pet.activity = Activity.AWAKE
    else:
        pet.hunger = _clamp(pet.hunger + TICK_APPETITE)
        pet.energy = _clamp(pet.energy - TICK_FATIGUE)
        if pet.hunger >= STARVED:
            pet.status = Status.DEAD
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos bind tamagotchi/pet.py INT-0008 --json
telos bind tamagotchi/pet.py INT-0009 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0011 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0012 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0013 --json
```
<!-- replay:end -->

Reconcile now runs the fuzzer too — gate 10, before the test suite:

<!-- replay:cmd -->
```console
telos change reconcile CHG-0004 --json
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "telos status --json",
 "expect": {"result.state": "coherent",
            "result.coverage.constraints": 1,
            "result.coverage.scenarios_proved": 13}}
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "telos rebuild status --json",
 "expect": {"result.scenarios_green": 13, "result.scenarios_total": 13}}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
git add -A
git commit -q -m "v0.4: neglect & death" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git tag v0.4.0
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "git status --porcelain", "expect_stdout": ""}
```
<!-- replay:end -->
