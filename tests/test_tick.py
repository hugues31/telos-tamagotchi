from tamagotchi.pet import Activity, Pet, Stage, tick


def scn_0006_a_tick_makes_a_waking_pet_hungrier_and_wearier():
    pet = Pet(name="Momo", stage=Stage.BABY, activity=Activity.AWAKE,
              hunger=40, energy=50)
    tick(pet)
    assert pet.hunger == 45
    assert pet.energy == 40
