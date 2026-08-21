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
