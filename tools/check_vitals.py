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
