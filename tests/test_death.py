from tamagotchi.pet import Activity, Pet, Stage, Status, tick


def scn_0011_the_tick_that_fills_the_gauge_is_the_last():
    pet = Pet(name="Momo", stage=Stage.BABY, status=Status.ALIVE,
              activity=Activity.AWAKE, hunger=95, energy=50)
    tick(pet)
    assert pet.hunger == 100
    assert pet.status is Status.DEAD
