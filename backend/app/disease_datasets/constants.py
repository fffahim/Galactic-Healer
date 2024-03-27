import json
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_species(s):
    variation = random.randint(1, 2)

    filename = f"app/disease_datasets/{s.lower()}{variation}.json"

    logger.info(f"Getting data from {filename}")

    with open(filename) as file:
        data = json.load(file)
        return dict(data)

def generate_random_star_wars_character():
    # Lists of possible first and last names
    first_names = ["Luke", "Leia", "Han", "Anakin", "Padmé", "Obi-Wan", "Rey", "Finn", "Kylo", "Ahsoka"]
    last_names = ["Skywalker", "Solo", "Kenobi", "Organa", "Calrissian", "Tano", "Dameron", "Ren", "Ventress"]

    # Dictionary of species with corresponding age ranges
    species_age_ranges = {
        "Chiss": (18, 50),
        "Miraluka": (20, 60),
        "Mirialans": (25, 70),
        "Zeltron": (22, 55)
    }

    # Randomly choose a species
    species = random.choice(list(species_age_ranges.keys()))

    # Generate a random age within the specified range for the chosen species
    min_age, max_age = species_age_ranges[species]
    age = random.randint(min_age, max_age)

    # Generate a random name
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)

    # List of possible personality traits
    personality_traits = ["stubborn", "clever", "kind-hearted", "charismatic", "shy"]

    # Choose a few random personality traits
    num_traits = random.randint(1, 3)
    traits = random.sample(personality_traits, num_traits)

    # Construct the character's full name
    full_name = f"{first_name} {last_name}"

    # Return the generated character
    return full_name, species, age, traits





