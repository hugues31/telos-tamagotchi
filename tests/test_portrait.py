from tamagotchi.pet import Pet, Stage
from tamagotchi.render import portrait


def scn_0017_a_portrait_is_at_least_a_few_lines_tall():
    pet = Pet(name="Momo", stage=Stage.BABY)
    assert len(portrait(pet).splitlines()) >= 3
