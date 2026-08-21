from tamagotchi.pet import Pet, Stage, play


def scn_0004_a_game_cheers_the_pet_up_and_makes_it_peckish():
    pet = Pet(name="Momo", stage=Stage.BABY, hunger=40, happiness=50)
    play(pet)
    assert pet.happiness == 70
    assert pet.hunger == 50
