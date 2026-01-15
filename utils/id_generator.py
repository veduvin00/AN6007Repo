import random

def generate_household_id():
    return "H" + "".join(str(random.randint(0, 9)) for _ in range(11))

