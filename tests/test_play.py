import pytest

from tamagotchi.pet import Activity, Pet, PetAsleepError, Stage, play


def scn_0004_a_game_cheers_the_pet_up_and_makes_it_peckish():
    pet = Pet(name="Momo", stage=Stage.BABY, hunger=40, happiness=50)
    play(pet)
    assert pet.happiness == 70
    assert pet.hunger == 50


def scn_0010_playing_with_a_sleeper_is_refused_and_changes_nothing():
    pet = Pet(name="Momo", stage=Stage.BABY, activity=Activity.ASLEEP,
              happiness=50)
    with pytest.raises(PetAsleepError):
        play(pet)
    assert pet.happiness == 50
    assert pet.activity is Activity.ASLEEP
