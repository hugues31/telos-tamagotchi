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
