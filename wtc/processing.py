import re
from typing import Iterator, Callable

import db
from definitions import Recipe, project_path
import logging


def _concatenate_window(list_str: str) -> Iterator[str]:
    """
    Return generetor of strings by parsing list_str through a window of
    decreasing number of words, starting from all present down to one.
    """
    for words_at_a_time in range(len(list_str), 0, -1):
        for index in range(len(list_str) - words_at_a_time + 1):
            yield ' '.join(list_str[index:words_at_a_time+index])

# TODO turn prints to logging


class IngrParser:
    """
    Extract the ingredient out of a string line, communicating with the
    ingredient database
    """

    def extract_ingredient(self, line: str,
                           is_ingr: Callable[[str], bool]):
        """
        Extract the first ingredient found in line.
        Ingredients with more words have priority.
        For example if line = '100g of spring onion' would return
        'spring onion' (if present in ingredients database) instead of just
        'onion'.
        Return first found match. If no match, raise exception
        """

        # Tokenize line
        word_list = re.split(r'\W+', line.lower().strip())

        # Try to detect the ingredient with the most words first, so that
        # "spring onion" has precedence over "onion"
        for phrase in _concatenate_window(word_list):
            if is_ingr(phrase):
                return phrase

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
    Handles everything that makes ingredients and recipes go into the database,
    from where the user interface leaves off.
    """
    # TODO recipe update and deletion features

    def __init__(self):

        self._interface = db.Interface()
        self._parser = IngrParser()

    def load_recipes(self):
        """
        Read the CSV file from RECIPES_TO_PROCESS_FILE_LOC
        and call the Parser to extract the ingredients out of each entry.
        Store on the database those recipes for which the parser detected one
        ingredient for every line.

        Return tuple of ints (num_loaded, num_not_loaded, num_errors)
        """

        logging.info('Loading recipes')

        recipe_log = RecipeLog()

        for line in self._read_recipe_line():

            title, url, *ingredients_raw = line.split(',')

            print(f'\n\nTitle: {title}')
            print(f'URL: {url}')
            print(f'Ingredients:\n')
            for ingr in ingredients_raw:
                print(f'   - {ingr.strip()}')

            # Parse ingredient list, check if all are recognized.
            known_ingredients = []
            unknown_ingredients = []
            for ingr in ingredients_raw:
                try:
                    ingr = self._parser.extract_ingredient(
                        ingr, self._interface.is_ingr)
                except ValueError:
                    unknown_ingredients.append(ingr)
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
        return recipe_log.get_counters()

    @property
    def num_new_recipes(self):
        raise NotImplementedError

    @property
    def num_pending_review(self):
        return self._interface.num_unknowns

    def next_pending_review(self):
        return self._interface.get_next_unknown()

    def make_known(self, recipe_id, text_with_unkown, extracted_ingredient):
        self._interface.make_known(
            recipe_id, text_with_unkown, extracted_ingredient)

    def _read_recipe_line(self):
        """Read recipes file and yield lines that aren't comments."""
        recipes_file = project_path + 'recipes-to-load.csv'
        with open(recipes_file) as f:
            for line in f:
                if line.strip()[0] == '#':
                    continue
                else:
                    yield line

    def _read_ingredient_line(self):
        """Read ingredients file and yield lines which aren't whitespaces."""
        txt_file = project_path+'ingredients.txt'  # TODO move paths to setup.py

        with open(txt_file, 'r+') as f:
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
            if self._interface.is_ingr(line):
                continue
            char_checklist = self._parser.check_chars(line)
            if all(char_checklist):
                to_add.append(line)
            else:
                print(f'"{ingr}" contains invalid characters '
                      f'({ingr[char_checklist.index(False)]})')

        # TODO ask confirmation through user interface
        if not to_add:
            print('No new ingredients to add.\n')
        else:
            print("Ingredients to add:")
            for ingr in to_add:
                print(f'  - {ingr}')
            while(True):
                opt = input(
                    'Add all of the above to database? [y/n]: ')

                match opt.lower():
                    case 'y':
                        for ingr in to_add:
                            self._interface.store_ingredient(ingr)
                        print(
                            f'{len(to_add)} ingredient'
                            f'{"s" if len(to_add) != 1 else ""} added.')
                    case 'n':
                        print('Operation cancelled.')
                    case _:
                        continue
                break


class Searcher:
    def __init__(self) -> None:

        self._interface = db.Interface()
        self.parser = IngrParser()

    def fetch_recipes(self, ingr_included, ingr_excluded):
        """
        Return all recipes stored in the database that contain
        ingr_included and don't contain ingr_excluded
        """

    def get_ingredients(self):
        """
        Return list of all stored ingredients.
        """
        return self._interface.get_ingredients()