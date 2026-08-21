from tamagotchi.pet import Pet, Stage, hatch


def scn_0001_a_warmed_egg_hatches_into_a_baby():
    pet = Pet(name="Momo", stage=Stage.EGG)
    hatch(pet)
    assert pet.stage is Stage.BABY
