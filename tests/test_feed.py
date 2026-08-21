from tamagotchi.pet import Pet, Stage, feed


def scn_0002_a_meal_takes_the_edge_off_hunger():
    pet = Pet(name="Momo", stage=Stage.BABY, hunger=80)
    feed(pet)
    assert pet.hunger == 50


def scn_0003_a_full_belly_stays_at_zero():
    pet = Pet(name="Momo", stage=Stage.BABY, hunger=20)
    feed(pet)
    assert pet.hunger == 0
