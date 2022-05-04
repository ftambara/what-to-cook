import re
from typing import Iterator

import db
from definitions import Recipe, project_path


def _concatenate_window(list_str: str) -> Iterator[str]:
    """
    Return generetor of strings by parsing list_str through a window of
    decreasing number of words, starting from all present down to one.
    """
    for words_at_a_time in range(len(list_str), 0, -1):
        for index in range(len(list_str) - words_at_a_time + 1):
            yield ' '.join(list_str[index:words_at_a_time+index])

# TODO delegate message printing to user interface
# TODO ask user to parse unknown ingredients manually


class IngrParser:
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

        # Tokenize line
        word_list = re.split(r'\W+', line.lower().strip())

        # Try to detect the ingredient with the most words first, so that
        # "spring onion" has precedence over "onion"
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


class Loader:
    """
    Responisble for loading recipes from a file, delegate ingredient
    extraction, and building list of doubts and errors to be handled later.
    """

    def __init__(self):

        self._parser = IngrParser()
        self._interface = db.Interface()

    def load_recipes(self):
        """
        Read the CSV file from RECIPES_TO_PROCESS_FILE_LOC
        and call the Parser to extract the ingredients out of each entry.
        Store on the database those recipes for which the parser detected one
        ingredient for every line.
        
        Return tuple of ints (num_loaded, not_loaded)
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

            # Parse ingredient list, check if all are recognized.
            ingredients_proc = []
            unrecognized_ingredient_entries = []
            for ingr in ingredients_raw:
                try:
                    ingr = self._parser.extract_ingredient(
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

    def _read_recipe_line(self):
        """Read recipes file and yield lines that aren't comments."""
        # TODO move paths to setup.py
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
            if self._interface.is_ingr_in_db(line):
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
    def __init__(self, parser: IngrParser,
                 interface: db.Interface) -> None:

        self.parser = parser
        self._interface = interface

    def fetch_recipes(self, ingr_included, ingr_excluded):
        """
        Return all recipes stored in the database that contain
        ingr_included and don't contain ingr_excluded
        """
