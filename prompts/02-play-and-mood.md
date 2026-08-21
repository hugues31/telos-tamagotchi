# Prompt 02 — v0.2.0: Play & mood

## The story so far

Momo hatched and eats well. But a pet that only eats is a stomach with
eyes. Momo needs joy — and joy, as every Owner learns, works up an
appetite.

## Your mission

> Open a change. Grow the **Pet** notion with a `happiness` gauge and a
> decimal `weight`. Add a **PlayWithPet** event and an intent: *playing
> lifts the mood and works up an appetite* (+20 happiness, +10 hunger).
> Also revisit the feeding intent: every meal should add 0.10 to the
> pet's weight — extend INT-0002 with a new scenario, keeping the two
> existing ones untouched. Approve, implement red-to-green, reconcile,
> tag v0.2.0.

Two Telos lessons live here: an `edit` replaces each field **wholesale**
(the attrs list below is the *complete* new list), and re-emitting a
scenario unchanged (same `id`) does not demand a fresh witness — only the
new scenario does.

## Exact replay script

<!-- replay:cmd -->
```console
telos change open "a pet needs joy, and joy needs appetite" --json
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos edit notion Pet --change CHG-0002 --json
```
```json
{"attrs": [{"name": "name", "type": "string"},
           {"name": "hunger", "type": "int"},
           {"name": "happiness", "type": "int"},
           {"name": "weight", "type": "decimal"},
           {"name": "stage", "type": "enum", "values": ["egg", "baby"]}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add notion --change CHG-0002 --json
```
```json
{"name": "PlayWithPet", "kind": "event",
 "def": "A game of chase-the-cursor with the pet."}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add intent --change CHG-0002 --json
```
```json
{"title": "Playing lifts the mood (and works up an appetite)",
 "status": "active",
 "telos": "Joy is the only gauge an Owner cannot refill with a spoon.",
 "statement": {"template": "event-driven", "when": "PlayWithPet", "on": "Pet",
               "action": "raise Pet.happiness by 20 and Pet.hunger by 10"},
 "requires": ["INT-0001"],
 "scenarios": [
   {"title": "a game cheers the pet up and makes it peckish",
    "given": [{"notion": "Pet",
               "fields": {"stage": "baby", "hunger": 40, "happiness": 50}}],
    "when": {"notion": "PlayWithPet", "fields": {}},
    "then": ["Pet.happiness == 70 and Pet.hunger == 50"]}]}
```
<!-- replay:end -->

Extend INT-0002: the two sealed scenarios ride along unchanged (their
`id` pins them); the third entry has no id, so the allocator mints
SCN-0005:

<!-- replay:cmd -->
```console
telos edit intent INT-0002 --change CHG-0002 --json
```
```json
{"scenarios": [
   {"id": "SCN-0002", "title": "a meal takes the edge off hunger",
    "given": [{"notion": "Pet", "fields": {"stage": "baby", "hunger": 80}}],
    "when": {"notion": "FeedPet", "fields": {}},
    "then": ["Pet.hunger == 50"]},
   {"id": "SCN-0003", "title": "a full belly stays at zero",
    "given": [{"notion": "Pet", "fields": {"stage": "baby", "hunger": 20}}],
    "when": {"notion": "FeedPet", "fields": {}},
    "then": ["Pet.hunger == 0"]},
   {"title": "every meal leaves a trace on the scale",
    "given": [{"notion": "Pet",
               "fields": {"stage": "baby", "hunger": 80, "weight": "1.20"}}],
    "when": {"notion": "FeedPet", "fields": {}},
    "then": ["Pet.hunger == 50", "Pet.weight == 1.30"]}]}
```
<!-- replay:end -->

<!-- replay:cmd capture=digest -->
```console
telos change diff CHG-0002 --json
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos change approve CHG-0002 --expected-digest @digest --json
```
<!-- replay:end -->

### Implement

`tests/test_feed.py` is sealed and this change modifies it, so its new
scenario is witnessed red *first* — the run claims the drifted file for
this change:

<!-- replay:write tests/test_feed.py -->
```python
from decimal import Decimal

from tamagotchi.pet import Pet, Stage, feed


def scn_0002_a_meal_takes_the_edge_off_hunger():
    pet = Pet(name="Momo", stage=Stage.BABY, hunger=80)
    feed(pet)
    assert pet.hunger == 50


def scn_0003_a_full_belly_stays_at_zero():
    pet = Pet(name="Momo", stage=Stage.BABY, hunger=20)
    feed(pet)
    assert pet.hunger == 0


def scn_0005_every_meal_leaves_a_trace_on_the_scale():
    pet = Pet(name="Momo", stage=Stage.BABY, hunger=80,
              weight=Decimal("1.20"))
    feed(pet)
    assert pet.hunger == 50
    assert pet.weight == Decimal("1.30")
```
<!-- replay:end -->

<!-- replay:write tests/test_play.py -->
```python
from tamagotchi.pet import Pet, Stage, play


def scn_0004_a_game_cheers_the_pet_up_and_makes_it_peckish():
    pet = Pet(name="Momo", stage=Stage.BABY, hunger=40, happiness=50)
    play(pet)
    assert pet.happiness == 70
    assert pet.hunger == 50
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0005 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0004 --json
```
<!-- replay:end -->

<!-- replay:write tamagotchi/pet.py -->
```python
"""The Tamagotchi domain: a pet, its appetites and its moods.

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


class Stage(StrEnum):
    EGG = "egg"
    BABY = "baby"


@dataclass
class Pet:
    name: str
    stage: Stage = Stage.EGG
    hunger: int = 0
    happiness: int = 50
    weight: Decimal = Decimal("1.00")


def hatch(pet: Pet) -> None:
    """INT-0001: hatching brings a pet to life."""
    pet.stage = Stage.BABY


def feed(pet: Pet) -> None:
    """INT-0002: feeding takes the edge off hunger, and leaves a trace."""
    pet.hunger = max(0, pet.hunger - FEED_RELIEF)
    pet.weight += MEAL_WEIGHT


def play(pet: Pet) -> None:
    """INT-0003: playing lifts the mood and works up an appetite."""
    pet.happiness += PLAY_JOY
    pet.hunger += PLAY_APPETITE
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos bind tamagotchi/pet.py INT-0003 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0005 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0004 --json
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos change reconcile CHG-0002 --json
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "telos status --json",
 "expect": {"result.state": "coherent",
            "result.coverage.intents_active": 3,
            "result.coverage.scenarios_proved": 5}}
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "telos rebuild status --json",
 "expect": {"result.scenarios_green": 5, "result.scenarios_total": 5}}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
git add -A
git commit -q -m "v0.2: play & mood" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git tag v0.2.0
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "git status --porcelain", "expect_stdout": ""}
```
<!-- replay:end -->
