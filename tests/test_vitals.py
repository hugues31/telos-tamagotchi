from tamagotchi.pet import Activity, Pet, Stage, play, tick


def scn_0012_joy_tops_out_at_one_hundred():
    pet = Pet(name="Momo", stage=Stage.BABY, activity=Activity.AWAKE,
              happiness=95, hunger=40)
    play(pet)
    assert pet.happiness == 100


def scn_0013_weariness_bottoms_out_at_zero():
    pet = Pet(name="Momo", stage=Stage.BABY, activity=Activity.AWAKE,
              energy=5)
    tick(pet)
    assert pet.energy == 0
