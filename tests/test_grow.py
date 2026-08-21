from tamagotchi.pet import Activity, Pet, Stage, tick


def scn_0014_at_ten_ticks_a_baby_no_more():
    pet = Pet(name="Momo", stage=Stage.BABY, age=9, activity=Activity.AWAKE)
    tick(pet)
    assert pet.stage in (Stage.CHILD, Stage.ADULT)


def scn_0015_at_twenty_five_all_grown_up():
    pet = Pet(name="Momo", stage=Stage.CHILD, age=24,
              activity=Activity.AWAKE)
    tick(pet)
    assert pet.stage is Stage.ADULT
