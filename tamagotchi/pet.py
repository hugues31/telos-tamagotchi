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
