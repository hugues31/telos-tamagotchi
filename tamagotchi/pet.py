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
