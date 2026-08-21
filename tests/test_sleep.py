from tamagotchi.pet import Activity, Pet, Stage, put_to_bed, tick


def scn_0007_tucking_in_sends_the_pet_to_sleep():
    pet = Pet(name="Momo", stage=Stage.BABY, activity=Activity.AWAKE)
    put_to_bed(pet)
    assert pet.activity is Activity.ASLEEP


def scn_0008_a_sleeping_pet_recovers_without_getting_hungrier():
    pet = Pet(name="Momo", stage=Stage.BABY, activity=Activity.ASLEEP,
              hunger=40, energy=40)
    tick(pet)
    assert pet.energy == 60
    assert pet.hunger == 40


def scn_0009_a_fully_rested_pet_wakes_by_itself():
    pet = Pet(name="Momo", stage=Stage.BABY, activity=Activity.ASLEEP,
              energy=80)
    tick(pet)
    assert pet.energy == 100
    assert pet.activity is Activity.AWAKE
