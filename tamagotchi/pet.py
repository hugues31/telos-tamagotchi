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
