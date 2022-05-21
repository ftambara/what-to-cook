import re
import csv
from typing import Iterator

import db
from definitions import Ingredient, Recipe
from paths import ingredients_path, recipes_path
import logging


# TODO turn prints to logging

def _concatenate_window(list_str: str) -> Iterator[str]:
    """
    Return generetor of strings by parsing list_str through a window of
    decreasing number of words, starting from all present down to one.
    """
    for words_at_a_time in range(len(list_str), 0, -1):
        for index in range(len(list_str) - words_at_a_time + 1):
            yield ' '.join(list_str[index:words_at_a_time+index])


class IngrParser:
    """
    Extract the ingredient out of a string line, communicating with the
    ingredient database
    """

    def extract_ingredient(self, line: str, ingr_list: list[Ingredient]):
        """
        Extract the first ingredient found in line.
        Ingredients with more words have priority.
        For example if line = '100g of spring onion' would return
        'spring onion' (if present in ingredients database) instead of just
        'onion'.
        Return first found match. If no match, raise ValueError
        """

        # Tokenize line
        word_list = re.split(r'\W+', line.lower().strip())

        # Try to detect the ingredient with the most words first, so that
        # "spring onion" has precedence over "onion"
        for phrase in _concatenate_window(word_list):
            possible_ingredient = Ingredient(phrase)
            if possible_ingredient in ingr_list:
                return possible_ingredient

        raise ValueError('line did not contain any known ingredient')

    def check_chars(self, line: str) -> list[str]:
        """
        Validate line caracters to see if they are allowed.
        Return list of bools with validation result per character.
        """
        return [char.isalpha() or char == ' ' for char in line]


class RecipeLog:
    """Track the status of recipes at loading time."""

    def __init__(self):
        self._num_successful = 0
        self._num_with_unknowns = 0
        self._num_errors = 0

    def count_success(self):
        self._num_successful += 1

    def count_error(self):
        self._num_errors += 1

    def count_with_unknowns(self):
        self._num_with_unknowns += 1

    def get_counters(self) -> tuple[int, int, int]:
        """Return number of successes, unknowns, and errors"""
        return (self._num_successful,
                self._num_with_unknowns,
                self._num_errors)


class Loader:
    """
    Handles operations that modify the database.
    """
    # TODO recipe update and deletion features

    def __init__(self):

        self.ingredients_file_path = ingredients_path
        self.recipes_file_path = recipes_path
        self._interface = db.Interface()
        self._parser = IngrParser()

    def set_ingr_path(self, path):
        self.ingredients_file_path = path

    def set_recipes_path(self, path):
        self.recipes_file_path = path

    def load_recipes(self):
        """
        Read the CSV file from RECIPES_TO_PROCESS_FILE_LOC
        and call the Parser to extract the ingredients out of each entry.
        Store on the database those recipes for which the parser detected one
        ingredient for every line.

        Return tuple of ints (num_loaded, num_with_unknowns, num_errors)
        """

        logging.info('Loading recipes')

        recipe_log = RecipeLog()

        for title, url, *ingredients_raw in self._read_recipe_line(self.recipes_file_path):

            # Parse ingredient list, check if all are recognized.
            known_ingredients = []
            unknown_ingredients = []
            for ingr_name in ingredients_raw:
                try:
                    ingr = self._parser.extract_ingredient(
                        ingr_name, self._interface.get_ingredients())
                except ValueError:
                    unknown_ingredients.append(ingr_name)
                else:
                    known_ingredients.append(ingr)

                recipe = Recipe(title,
                                url,
                                ingredients_known=known_ingredients,
                                ingredients_unknown=unknown_ingredients)

            try:
                self._interface.store_recipe(recipe)

            except ValueError:
                logging.info('Recipe ignored, title or URL already '
                             'present.')
                # No counters for duplicated recipes.
            else:
                if not unknown_ingredients:
                    logging.info('Recipe loaded successfully.')
                    recipe_log.count_success()
                else:
                    logging.warning('Recipe loaded with some ingredients not '
                                    'recognized:')
                    print(f'{unknown_ingredients}')
                    recipe_log.count_with_unknowns()

        logging.info('Recipes EOF')
        num_new_ok, num_with_unknowns, num_errors = recipe_log.get_counters()
        logging.info(
            f'Loaded {num_new_ok} new recipes. '
            + f'{num_with_unknowns} had unknown ingredients.')
        if num_errors:
            logging.error(
                f'{num_errors} recipes had errors while loading recipes.')
        return recipe_log.get_counters()

    @property
    def num_new_recipes(self):
        raise NotImplementedError

    @property
    def num_pending_review(self):
        return self._interface.num_unknowns

    def delete_recipe(self, recipe_id):
        self._interface.delete_recipe(recipe_id)

    def get_pending_review(self) -> dict:
        """
        Return all unknowns as a dictionary:
            {id: (recipe_title, recipe_url, unknowns_list)}
        """

        result = {}
        for id, title, url, text in self._interface.get_unknowns():
            result.setdefault(id, (title, url, []))[-1].append(text)
        return result

    def next_pending_review(self):
        """
        Return one ingredient pending review as a tuple:
            (recipe_id, recipe_title, recipe_url, text_with_unknown)

        NOTE: Call self.get_same_solution_candidates to get a dictionary
        containing all other unkowns that could be solved using the same
        extracted ingredient.
        """
        [result] = self._interface.get_unknowns(limit=1)
        return result

    def solve_unknown(self, recipe_id: int,
                      text_with_unknown: str,
                      extracted_ingr: Ingredient):

        # Assert that ingredient extraction works for given data.
        self._parser.extract_ingredient(
            text_with_unknown, [extracted_ingr])

        # If everything is ok, solve the unknown in the database
        self._interface.store_ingredient(extracted_ingr)
        self._interface.solve_unknown(
            recipe_id, text_with_unknown, extracted_ingr)

    def delete_unknown(self, text_with_unknown):
        self._interface.delete_unknown(text_with_unknown)

    def get_same_solution_candidates(self, extracted_ingr: Ingredient):

        candidates = {}
        # Check if other unknowns are solved with the same ingredient
        for id, (title, url, unknowns) in self.get_pending_review().items():
            for unknown in unknowns:
                try:
                    self._parser.extract_ingredient(
                        unknown, [extracted_ingr])
                except ValueError:
                    pass
                else:
                    candidates.setdefault(id, (title, url, []))[-1]\
                        .append(unknown)
        return candidates

    def _read_recipe_line(self, recipes_file):
        """Read recipes file and yield lines that aren't comments."""
        with open(recipes_file) as fp:
            csv_reader = csv.reader(fp, dialect='unix')
            for line in csv_reader:
                if not line or line[0].strip("' ").startswith('#'):
                    continue
                else:
                    yield line

    def _read_ingredient_line(self):
        """Read ingredients file and yield lines which aren't whitespaces."""
        with open(self.ingredients_file_path, 'r+') as f:
            for line in f:
                if line != '\n':
                    yield line

    def store_ingredients(self):
        """
        Load ingredients from ingr_list into database.
        Those already present are ignored.
        """

        print('Loading ingredients:')

        # Get new ingredients
        to_add = []
        for line in self._read_ingredient_line():
            line = line.strip().lower()
            # Skip if the line represents an ingredient already present
            if Ingredient(line) in self._interface.get_ingredients():
                continue
            char_checklist = self._parser.check_chars(line)
            if all(char_checklist):
                to_add.append(line)
            else:
                logging.warning(f'"{line}" contains invalid characters '
                                f'({line[char_checklist.index(False)]})')

        # TODO ask confirmation through GUI
        if not to_add:
            logging.info('No new ingredients to add.\n')
        else:
            logging.info("Ingredients to add:")
            for ingr in to_add:
                self._interface.store_ingredient(Ingredient(ingr))
            print(
                f'{len(to_add)} ingredient'
                f'{"s" if len(to_add) != 1 else ""} added.')


class Searcher:
    def __init__(self) -> None:

        self._interface = db.Interface()
        self.parser = IngrParser()

    def get_recipes(self, ingr_included: list[str] = []) -> list[Recipe]:
        """
        Return all recipes stored in the database that contain
        ingr_included. If ingr_included is [], get all recipes in the database.
        """
        filter = [Ingredient(ingr) for ingr in ingr_included]
        return self._interface.get_recipes(filter)

    def get_ingredients(self) -> list[Ingredient]:
        """
        Return unordered list of all stored ingredients.
        """
        return self._interface.get_ingredients()

    def get_recipe_id(self, title, url) -> int:
        return self._interface.get_recipe_id(title, url)
