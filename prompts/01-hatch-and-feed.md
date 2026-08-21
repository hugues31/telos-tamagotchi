# Prompt 01 — v0.1.0: Hatch & feed

## The story so far

The nest is sealed and empty. Time for an egg — and for the first hunger.

## Your mission

> Open a Telos change for Momo's first behaviours. Model the domain:
> an **Owner** (actor) who keeps a **Pet** (entity) with a name, a hunger
> gauge and a life stage; a **HatchPet** event and a **FeedPet** event.
> Then state two intents in EARS form: *hatching brings a pet to life*
> (event-driven, `set Pet.stage = baby`) and *feeding takes the edge off
> hunger* (feeding reduces hunger by 30, never below zero). Configure the
> test runner for Python (`pytest -q -k {filter}`, code under
> `tamagotchi/`, tests under `tests/`, strict TDD). Review the diff,
> approve it, then implement scenario by scenario: red witness, code,
> green witness, bind, reconcile. Tag the result v0.1.0.

Note for agents: entity ids below (CHG/INT/SCN numbers) are what a fresh
replay allocates. If you stage in a different order, *your* ids may
differ — always read them from the CLI's JSON results, never assume.

## Exact replay script

Every mutation of `telos/` lives inside a change — a reviewable
transaction:

<!-- replay:cmd -->
```console
telos change open "hatch a pet and keep it fed" --json
```
<!-- replay:end -->

### The domain, as typed notions

<!-- replay:cmd -->
```console
telos add notion --change CHG-0001 --json
```
```json
{"name": "Owner", "kind": "actor",
 "def": "The human who keeps the pet alive, mostly out of love.",
 "attrs": [{"name": "name", "type": "string"}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add notion --change CHG-0001 --json
```
```json
{"name": "Pet", "kind": "entity",
 "def": "A small creature that depends entirely on its Owner.",
 "attrs": [{"name": "name", "type": "string"},
           {"name": "hunger", "type": "int"},
           {"name": "stage", "type": "enum", "values": ["egg", "baby"]}],
 "rels": [{"name": "owned-by", "target": "Owner"}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add notion --change CHG-0001 --json
```
```json
{"name": "HatchPet", "kind": "event",
 "def": "The egg is warmed until it cracks."}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add notion --change CHG-0001 --json
```
```json
{"name": "FeedPet", "kind": "event",
 "def": "A meal is offered to the pet."}
```
<!-- replay:end -->

### The intents — behaviour in EARS form, with its *why*

<!-- replay:cmd -->
```console
telos add intent --change CHG-0001 --json
```
```json
{"title": "Hatching brings a pet to life", "status": "active",
 "telos": "An egg that never hatches is just a stone with ambitions.",
 "statement": {"template": "event-driven", "when": "HatchPet", "on": "Pet",
               "action": "set Pet.stage = baby"},
 "scenarios": [
   {"title": "a warmed egg hatches into a baby",
    "given": [{"notion": "Owner", "fields": {"name": "Hugues"}},
              {"notion": "Pet", "fields": {"name": "Momo", "stage": "egg"}}],
    "when": {"notion": "HatchPet", "fields": {}},
    "then": ["Pet.stage == baby"]}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add intent --change CHG-0001 --json
```
```json
{"title": "Feeding takes the edge off hunger", "status": "active",
 "telos": "A hungry pet cannot trust an Owner who only watches.",
 "statement": {"template": "event-driven", "when": "FeedPet", "on": "Pet",
               "action": "reduce Pet.hunger by 30, never below zero"},
 "requires": ["INT-0001"],
 "scenarios": [
   {"title": "a meal takes the edge off hunger",
    "given": [{"notion": "Pet", "fields": {"stage": "baby", "hunger": 80}}],
    "when": {"notion": "FeedPet", "fields": {}},
    "then": ["Pet.hunger == 50"]},
   {"title": "a full belly stays at zero",
    "given": [{"notion": "Pet", "fields": {"stage": "baby", "hunger": 20}}],
    "when": {"notion": "FeedPet", "fields": {}},
    "then": ["Pet.hunger == 0"]}]}
```
<!-- replay:end -->

### The runner — Python, strict TDD

`telos/telos.toml` is sealed spec too, so even configuration goes through
the change:

<!-- replay:cmd -->
```console
telos config --change CHG-0001 --json
```
```json
{"code": {"globs": ["pytest.ini", "tamagotchi/**/*.py"]},
 "tests": {"globs": ["tests/**/*.py"]},
 "test": {"cmd": "pytest -q -k {filter}"},
 "policy": {"tdd": "strict"},
 "agents": {"hosts": ["claude"]}}
```
<!-- replay:end -->

### Review and approve

The approval is pinned to the digest of the staged operations — nobody
can slip an edit under an approval:

<!-- replay:cmd capture=digest -->
```console
telos change diff CHG-0001 --json
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos change approve CHG-0001 --expected-digest @digest --json
```
<!-- replay:end -->

### Implement — red first, always

Write the tests to their final bytes *before* any implementation. Telos
seals the red verdict against the test file's exact content; changing the
test after its red witness voids the proof.

<!-- replay:write pytest.ini -->
```ini
[pytest]
python_functions = scn_* test_*
pythonpath = .
testpaths = tests
addopts = -q
```
<!-- replay:end -->

<!-- replay:write tamagotchi/__init__.py -->
```python
"""Momo, a Tamagotchi raised spec-first with Telos."""
```
<!-- replay:end -->

<!-- replay:write tests/test_hatch.py -->
```python
from tamagotchi.pet import Pet, Stage, hatch


def scn_0001_a_warmed_egg_hatches_into_a_baby():
    pet = Pet(name="Momo", stage=Stage.EGG)
    hatch(pet)
    assert pet.stage is Stage.BABY
```
<!-- replay:end -->

<!-- replay:write tests/test_feed.py -->
```python
from tamagotchi.pet import Pet, Stage, feed


def scn_0002_a_meal_takes_the_edge_off_hunger():
    pet = Pet(name="Momo", stage=Stage.BABY, hunger=80)
    feed(pet)
    assert pet.hunger == 50


def scn_0003_a_full_belly_stays_at_zero():
    pet = Pet(name="Momo", stage=Stage.BABY, hunger=20)
    feed(pet)
    assert pet.hunger == 0
```
<!-- replay:end -->

Three red witnesses — the tests fail because `tamagotchi.pet` does not
exist yet, and Telos seals that fact:

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0001 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0002 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0003 --json
```
<!-- replay:end -->

Now, and only now, the implementation:

<!-- replay:write tamagotchi/pet.py -->
```python
"""The Tamagotchi domain: a pet and its appetites.

Every behaviour here answers to an intent sealed in `telos/`.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

FEED_RELIEF = 30


class Stage(StrEnum):
    EGG = "egg"
    BABY = "baby"


@dataclass
class Pet:
    name: str
    stage: Stage = Stage.EGG
    hunger: int = 0


def hatch(pet: Pet) -> None:
    """INT-0001: hatching brings a pet to life."""
    pet.stage = Stage.BABY


def feed(pet: Pet) -> None:
    """INT-0002: feeding takes the edge off hunger."""
    pet.hunger = max(0, pet.hunger - FEED_RELIEF)
```
<!-- replay:end -->

Bind the files to the intents they implement, then collect the greens:

<!-- replay:cmd -->
```console
telos bind pytest.ini INT-0001 --json
telos bind tamagotchi/__init__.py INT-0001 --json
telos bind tamagotchi/pet.py INT-0001 --json
telos bind tamagotchi/pet.py INT-0002 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0001 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0002 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0003 --json
```
<!-- replay:end -->

### Reconcile — the eleven gates

Reconcile re-verifies everything (drift, digest, witnesses, coverage,
tests), applies the delta atomically and re-seals the project:

<!-- replay:cmd -->
```console
telos change reconcile CHG-0001 --json
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "telos status --json",
 "expect": {"result.state": "coherent",
            "result.coverage.intents_active": 2,
            "result.coverage.scenarios_proved": 3}}
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
 "expect": {"result.scenarios_green": 3, "result.scenarios_total": 3}}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
git add -A
git commit -q -m "v0.1: hatch & feed" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git tag v0.1.0
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "git status --porcelain", "expect_stdout": ""}
```
<!-- replay:end -->
