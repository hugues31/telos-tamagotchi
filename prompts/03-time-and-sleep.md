# Prompt 03 — v0.3.0: Time & sleep

## The story so far

Momo eats, Momo plays. But nothing ever *happens* to Momo — no clock
ticks, no evening comes. Time enters the story, and with it, fatigue.

## Your mission

> Open a change. Give the **Pet** an `energy` gauge and an `activity`
> state (awake or asleep). Add two events: **TimeTicks** (the world's
> heartbeat) and **PutPetToBed**. State four intents: *time gnaws at a
> waking pet* (event-driven: each tick adds 5 hunger, drains 10 energy);
> *a pet put to bed falls asleep* (event-driven, `set Pet.activity =
> asleep`); *sleep restores what the day spent* (**state-driven** — while
> the pet is asleep, a tick restores 20 energy and leaves hunger alone,
> and a fully rested pet wakes); *no games with a sleeping pet*
> (**unwanted** — playing while asleep is rejected and changes nothing).
> Approve, implement red-to-green, reconcile, tag v0.3.0.

Two of the five EARS templates appear here: `while Pet.activity == asleep`
(state-driven) and `if Pet.activity == asleep` (unwanted behaviour).

## Exact replay script

<!-- replay:cmd -->
```console
telos change open "let time pass, let the pet rest" --json
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos edit notion Pet --change CHG-0003 --json
```
```json
{"attrs": [{"name": "name", "type": "string"},
           {"name": "hunger", "type": "int"},
           {"name": "happiness", "type": "int"},
           {"name": "energy", "type": "int"},
           {"name": "weight", "type": "decimal"},
           {"name": "stage", "type": "enum", "values": ["egg", "baby"]},
           {"name": "activity", "type": "enum", "values": ["awake", "asleep"]}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add notion --change CHG-0003 --json
```
```json
{"name": "TimeTicks", "kind": "event",
 "def": "The world's heartbeat; everything ages by one beat."}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add notion --change CHG-0003 --json
```
```json
{"name": "PutPetToBed", "kind": "event",
 "def": "The Owner dims the lights and tucks the pet in."}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add intent --change CHG-0003 --json
```
```json
{"title": "Time gnaws at a waking pet", "status": "active",
 "telos": "A pet no clock can touch is a paperweight, not a companion.",
 "statement": {"template": "event-driven", "when": "TimeTicks", "on": "Pet",
               "action": "raise Pet.hunger by 5 and drain Pet.energy by 10 while awake"},
 "requires": ["INT-0001"],
 "scenarios": [
   {"title": "a tick makes a waking pet hungrier and wearier",
    "given": [{"notion": "Pet",
               "fields": {"stage": "baby", "activity": "awake",
                          "hunger": 40, "energy": 50}}],
    "when": {"notion": "TimeTicks", "fields": {}},
    "then": ["Pet.hunger == 45 and Pet.energy == 40"]}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add intent --change CHG-0003 --json
```
```json
{"title": "A pet put to bed falls asleep", "status": "active",
 "telos": "Rest must be a gift the Owner can give.",
 "statement": {"template": "event-driven", "when": "PutPetToBed", "on": "Pet",
               "action": "set Pet.activity = asleep"},
 "requires": ["INT-0001"],
 "scenarios": [
   {"title": "tucking in sends the pet to sleep",
    "given": [{"notion": "Pet",
               "fields": {"stage": "baby", "activity": "awake"}}],
    "when": {"notion": "PutPetToBed", "fields": {}},
    "then": ["Pet.activity == asleep"]}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add intent --change CHG-0003 --json
```
```json
{"title": "Sleep restores what the day spent", "status": "active",
 "telos": "Sleep is the one meal hunger cannot interrupt.",
 "statement": {"template": "state-driven",
               "while": "Pet.activity == asleep",
               "action": "each tick restores 20 energy, leaves hunger alone, and wakes the pet at 100"},
 "requires": ["INT-0005"],
 "scenarios": [
   {"title": "a sleeping pet recovers without getting hungrier",
    "given": [{"notion": "Pet",
               "fields": {"stage": "baby", "activity": "asleep",
                          "hunger": 40, "energy": 40}}],
    "when": {"notion": "TimeTicks", "fields": {}},
    "then": ["Pet.energy == 60", "Pet.hunger == 40"]},
   {"title": "a fully rested pet wakes by itself",
    "given": [{"notion": "Pet",
               "fields": {"stage": "baby", "activity": "asleep",
                          "energy": 80}}],
    "when": {"notion": "TimeTicks", "fields": {}},
    "then": ["Pet.energy == 100 and Pet.activity == awake"]}]}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos add intent --change CHG-0003 --json
```
```json
{"title": "No games with a sleeping pet", "status": "active",
 "telos": "An Owner who wakes a pet for fun teaches it to fear the night.",
 "statement": {"template": "unwanted",
               "if": "Pet.activity == asleep",
               "action": "reject PlayWithPet and leave the pet untouched"},
 "requires": ["INT-0005"],
 "scenarios": [
   {"title": "playing with a sleeper is refused and changes nothing",
    "given": [{"notion": "Pet",
               "fields": {"stage": "baby", "activity": "asleep",
                          "happiness": 50}}],
    "when": {"notion": "PlayWithPet", "fields": {}},
    "then": ["Pet.happiness == 50 and Pet.activity == asleep"]}]}
```
<!-- replay:end -->

<!-- replay:cmd capture=digest -->
```console
telos change diff CHG-0003 --json
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos change approve CHG-0003 --expected-digest @digest --json
```
<!-- replay:end -->

### Implement

`tests/test_play.py` is sealed and gains a scenario, so SCN-0010 goes
red first:

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
```
<!-- replay:end -->

<!-- replay:write tests/test_tick.py -->
```python
from tamagotchi.pet import Activity, Pet, Stage, tick


def scn_0006_a_tick_makes_a_waking_pet_hungrier_and_wearier():
    pet = Pet(name="Momo", stage=Stage.BABY, activity=Activity.AWAKE,
              hunger=40, energy=50)
    tick(pet)
    assert pet.hunger == 45
    assert pet.energy == 40
```
<!-- replay:end -->

<!-- replay:write tests/test_sleep.py -->
```python
from tamagotchi.pet import Activity, Pet, Stage, put_to_bed, tick


def scn_0007_tucking_in_sends_the_pet_to_sleep():
    pet = Pet(name="Momo", stage=Stage.BABY, activity=Activity.AWAKE)
    put_to_bed(pet)
    assert pet.activity is Activity.ASLEEP


def scn_0008_a_sleeping_pet_recovers_without_getting_hungrier():
    pet = Pet(name="Momo", stage=Stage.BABY, activity=Activity.ASLEEP,
              hunger=40, energy=40)
    tick(pet)
    assert pet.energy == 60
    assert pet.hunger == 40


def scn_0009_a_fully_rested_pet_wakes_by_itself():
    pet = Pet(name="Momo", stage=Stage.BABY, activity=Activity.ASLEEP,
              energy=80)
    tick(pet)
    assert pet.energy == 100
    assert pet.activity is Activity.AWAKE
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0010 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0006 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0007 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0008 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=red -->
```console
telos test SCN-0009 --json
```
<!-- replay:end -->

<!-- replay:write tamagotchi/pet.py -->
```python
"""The Tamagotchi domain: a pet, its appetites, its moods, its nights.

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


class Stage(StrEnum):
    EGG = "egg"
    BABY = "baby"


class Activity(StrEnum):
    AWAKE = "awake"
    ASLEEP = "asleep"


class PetAsleepError(Exception):
    """Raised when an interaction needs a pet that is awake."""


@dataclass
class Pet:
    name: str
    stage: Stage = Stage.EGG
    hunger: int = 0
    happiness: int = 50
    energy: int = FULL_ENERGY
    weight: Decimal = Decimal("1.00")
    activity: Activity = Activity.AWAKE


def hatch(pet: Pet) -> None:
    """INT-0001: hatching brings a pet to life."""
    pet.stage = Stage.BABY


def feed(pet: Pet) -> None:
    """INT-0002: feeding takes the edge off hunger, and leaves a trace."""
    pet.hunger = max(0, pet.hunger - FEED_RELIEF)
    pet.weight += MEAL_WEIGHT


def play(pet: Pet) -> None:
    """INT-0003: playing lifts the mood. INT-0007: never while asleep."""
    if pet.activity is Activity.ASLEEP:
        raise PetAsleepError(f"{pet.name} is asleep; let them dream.")
    pet.happiness += PLAY_JOY
    pet.hunger += PLAY_APPETITE


def put_to_bed(pet: Pet) -> None:
    """INT-0005: a pet put to bed falls asleep."""
    pet.activity = Activity.ASLEEP


def tick(pet: Pet) -> None:
    """INT-0004: time gnaws at a waking pet. INT-0006: sleep restores."""
    if pet.activity is Activity.ASLEEP:
        pet.energy = min(FULL_ENERGY, pet.energy + SLEEP_RECOVERY)
        if pet.energy >= FULL_ENERGY:
            pet.activity = Activity.AWAKE
    else:
        pet.hunger += TICK_APPETITE
        pet.energy -= TICK_FATIGUE
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos bind tamagotchi/pet.py INT-0004 --json
telos bind tamagotchi/pet.py INT-0005 --json
telos bind tamagotchi/pet.py INT-0006 --json
telos bind tamagotchi/pet.py INT-0007 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0010 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0006 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0007 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0008 --json
```
<!-- replay:end -->

<!-- replay:cmd expect-witness=green -->
```console
telos test SCN-0009 --json
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
telos change reconcile CHG-0003 --json
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "telos status --json",
 "expect": {"result.state": "coherent",
            "result.coverage.intents_active": 7,
            "result.coverage.scenarios_proved": 10}}
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "telos rebuild status --json",
 "expect": {"result.scenarios_green": 10, "result.scenarios_total": 10}}
```
<!-- replay:end -->

<!-- replay:cmd -->
```console
git add -A
git commit -q -m "v0.3: time & sleep" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git tag v0.3.0
```
<!-- replay:end -->

<!-- replay:check -->
```json
{"run": "git status --porcelain", "expect_stdout": ""}
```
<!-- replay:end -->
