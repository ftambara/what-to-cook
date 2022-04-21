#!/usr/bin/env python3
"""

"""

__author__ = "Federico Tambara"
__license__ = "MIT"

import os
import re
from typing import Iterator

import db
from definitions import Ingredient, Recipe


def _concatenate_window(list_str: str) -> Iterator[str]:
    """
    Return generetor of strings by parsing list_str through a window of
    decreasing number of words, starting from all present down to one.
    """
    for words_at_a_time in range(len(list_str), 0, -1):
        for index in range(len(list_str) - words_at_a_time + 1):
            yield ' '.join(list_str[index:words_at_a_time+index])


class UserInterface(object):
    """
    Middle man between User and the rest of the program
    """

    def __init__(self):
        ...


class IngrProcessor(object):
    """
    Extract the ingredient out of a string line, communicating with the
    ingredient database
    """

    def __init__(self):
        ...

    def extract_ingredient(self, line: str, interface: db.Interface):
        """
        Extract the first ingredient found in line.
        Ingredients with more words have priority.
        For example if line = '100g of spring onion' would return
        'spring onion' (if present in ingredients database) instead of just
        'onion'.
        Return first found match. If no match, raise exception
        """

        # # Tokenize line
        # #   Replace apostrophes to prepare line for splitting
        # line_list = line.replace('`', ' ')
        # line_list = line_list.replace("'", ' ')
        # #   Split cleaned up line
        # line_list = line_list.lower().split()

        # TODO Check and delete above

        # Tokenize line
        word_list = re.split(r'\W+', line.lower().strip())
        # Parse line in descending number of words at a time

        # Try to detect the longest ingredient first, so that "spring onion"
        # has precedence over "onion"

        for phrase in _concatenate_window(word_list):
            if interface.is_ingr_in_db(phrase):
                return phrase

        raise ValueError('line did not contain any known ingredient')

    def check_chars(self, line: str) -> list[str]:
        """
        Validate line caracters to see if they are allowed.
        Return list of bools with validation result per character.
        """
        return [char.isalpha() or char == ' ' for char in line]


class Loader(object):
    """
    Responisble for loading recipes from a file, delegate ingredient
    extraction, and building list of doubts and errors to be handled later.
    """

    def __init__(self, processor: IngrProcessor,
                 interface: db.Interface):

        self._processor = processor
        self._interface = interface

    def load_recipes(self):
        """
        Read the CSV file from RECIPES_TO_PROCESS_FILE_LOC
        and call the Processor to extract the ingredients out of each entry.
        Store the recipes of which it has no doubts on the database.
        Return tuple of ints (new_recipes, duplicate, doubts, errors)?
        """

        print('\nLoading recipes:')

        for line in self._read_recipe_line():
            title, url, *ingredients_raw = line.split(',')
            print('\n', end='')
            print(f'  Title: {title}')
            print(f'  URL: {url}')
            print(f'Ingredients:\n')
            for ingr in ingredients_raw:
                print(f'   - {ingr.strip()}')

            # Process ingredient list, check if all are recognized.
            ingredients_proc = []
            unrecognized_ingredient_entries = []
            for ingr in ingredients_raw:
                try:
                    ingr = self._processor.extract_ingredient(
                        ingr, self._interface)
                    ingredients_proc.append(ingr)
                except ValueError:
                    # Ingredient could not be extracted.
                    unrecognized_ingredient_entries.append(ingr)

            if not unrecognized_ingredient_entries:
                recipe = Recipe(title, url, ingredients_proc)
                try:
                    self._interface.store_recipe(recipe)
                except ValueError:
                    print('\n  Recipe ignored, title or URL already '
                          'present.')
                else:
                    print('\n  Recipe loaded successfully.')
            else:
                print('\n  Recipe not loaded. Ingredients not '
                      'recognized:\n'
                      f'{unrecognized_ingredient_entries}')
                # TODO Consult doubts to user, now or later.

    def _read_recipe_line(self):
        """Read recipes file and yield lines that aren't comments."""
        project_path = os.path.dirname(os.path.abspath(__file__))
        # TODO move paths to setup.py
        recipes_file = project_path + '/../recipes-to-load.csv'
        with open(recipes_file) as f:
            for line in f:
                if line.strip()[0] == '#':
                    continue
                else:
                    yield line

    def store_ingredients(self):
        """
        Load ingredients from ingr_list into database.
        Those already present are ignored.
        """
        project_path = os.path.dirname(os.path.abspath(__file__))
        txt_file = project_path+'/../ingredients.txt'  # TODO move paths to setup.py

        to_add = []

        print('Loading ingredients:')

        # TODO extract line-reading
        with open(txt_file, 'r+') as f:
            for line in f:
                line = line.strip()
                if line == '\n' or self._interface.is_ingr_in_db(line):
                    continue
                char_checklist = self._processor.check_chars(line)
                if all(char_checklist):
                    to_add.append(line)
                else:
                    print(f'"{ingr}" contains invalid characters '
                          f'({ingr[char_checklist.index(False)]})')

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
                        print(f'{len(to_add)} ingredients added.')
                        # TODO print 'ingredient' (no s) when it's only 1
                    case 'n':
                        print('Operation cancelled.')
                    case _:
                        continue
                break


class Searcher(object):
    def __init__(self, processor: IngrProcessor,
                 interface: db.Interface) -> None:

        self.processor = processor
        self._interface = interface

    def fetch_recipes(self, ingr_included, ingr_excluded):
        """
        Return all recipes stored in the database that contain
        ingr_included and don't contain ingr_excluded
        """


def main():
    """ Main entry point of the app """
    interface = db.Interface()
    ingr_processor = IngrProcessor()
    # ingredient = 'Pomodoro'
    # print(f'Is "{ingredient}" in the database? '
    #     f'{ingr_db_inter.is_ingr_ind_db(ingredient)}')

    loader = Loader(ingr_processor, interface)
    print("\n[DEB] Stored ingredients:")
    for ingredient in interface.get_ingredients():
        print(" -", *ingredient)
    
    loader.store_ingredients()
    
    loader.load_recipes()
    print("\n[DEB] Stored Recipes:")
    interface.print_recipes()


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()
