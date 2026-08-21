"""ASCII portraits for every stage of a small life.

INT-0012: a face for the terminal. Imports nothing from the domain —
it reads the pet's gauges through plain attributes.
"""

_FACES = {
    "egg": [
        r"    ___    ",
        r"   /   \   ",
        r"  | . . |  ",
        r"   \___/   ",
    ],
    "baby": [
        r"  (\_ _/)  ",
        r"  ( o.o )  ",
        r"   > ^ <   ",
    ],
    "child": [
        r"  (\_ _/)  ",
        r"  ( ^.^ )  ",
        r"  ( u u )o ",
    ],
    "adult": [
        r"  /\_ _/\  ",
        r"  ( -.- )  ",
        r"  (  v  )  ",
        r"   |___|   ",
    ],
}

_DEAD = [
    r"    ___    ",
    r"   / + \   ",
    r"  | RIP |  ",
    r"   \___/   ",
]


def portrait(pet) -> str:
    """Render the pet as a multi-line ASCII portrait."""
    if str(pet.status) == "dead":
        lines = list(_DEAD)
    else:
        lines = list(_FACES[str(pet.stage)])
        if str(pet.activity) == "asleep":
            lines.append(r"    zZz    ")
    return "\n".join(lines)
