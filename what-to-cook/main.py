#!/usr/bin/env python3
"""

"""

__author__ = "Federico Tambara"
__license__ = "MIT"

import os
import dbInterface


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
    
    def extract_ingredient(self, line: str, model: dbInterface.Ingredients,
    stemmed=False):
        """
        Extract the first ingredient found in line.
        Ingredients have priority by the number of words they contain
        for example 'spring onion' has priority over 'onion'
        Return extracted ingredient

        If stemmed is true, return stem of found ingredient
        """
        
        # Tokenize line
        #   Replace apostrophes to prepare line for splitting
        line_list = line.replace('`', ' ')
        line_list = line_list.replace("'", ' ')
        #   Split cleaned up line
        line_list = line_list.lower().split()
        
        # Parse line in descending number of words at a time
        from typing import Iterator
        def window_composition(list_str: str) -> Iterator[str]:
            """
            Return generator composing list into generator of strings.
            Each returned string is made from joining list items without
            changing its order. Starts from longest to shortest, left to right.
            """
            for words_at_a_time in range(len(list_str), 0, -1):
                for index in range(len(list_str) - words_at_a_time +1):
                    yield ' '.join(list_str[index:words_at_a_time+index])

        found_match = False
        for word in window_composition(line_list):
            if model.is_ingr_ind_db(self.stem_ingredient(word)):
                found_match = True
                break
        
        # Return first found match
        if found_match:
            if stemmed:
                return self.stem_ingredient(word)
            else:
                return word
        # If no match, raise exception
        else:
            raise ValueError('line did not contain any known ingredient')

    def stem_ingredient(self, ingr: str):
        """Return stem of ingr"""
        return self.stem_ingredients([ingr.strip()])[0]
    
    def stem_ingredients(self, ingr_list: list[str]):
        """
        Return list of stems of the elements of ingr_list.
        Make sure ingredients are striped.
        """
        import snowballstemmer as sb

        stemmer = sb.stemmer('italian')
        return stemmer.stemWords(ingr_list)

    def check_chars(self, line: str) -> list[str]:
        return [char.isalpha() or char == ' ' for char in line]


class Loader(object):
    """
    Responisble for loading recipes from a file, delegate ingredient
    extraction, and building list of doubts and errors to be handled later.
    """
    
    def __init__(self, processor: IngrProcessor,
        ingr_model: dbInterface.Ingredients, recipe_model: dbInterface.Recipes):
        self.processor = processor
        self.ingr_model = ingr_model
        self.recipe_model = recipe_model
    
    def read_recipes(self):
        """
        Read the CSV file from RECIPES_TO_PROCESS_FILE_LOC
        and call the Processor to extract the ingredients out of each entry.
        Store the recipes of which it has no doubts on the database.
        Return tuple of ints (new_recipes, duplicate, doubts, errors)?
        """
        project_path = os.path.dirname(os.path.abspath(__file__))
        recipes_file = project_path + '/../recipes-to-load.csv'
        
        print('\nLoading recipes:')
        with open(recipes_file) as f:
            for line in f:
                # Ignore lines starting with '#' character.
                if line.strip()[0] == '#':
                    continue
                else:
                    title, url, *ingredients_raw = line.split(',')
                    print('\n', end='')
                    print(f'  Title: {title}')
                    print(f'  URL: {url}')
                    for ingr in ingredients_raw:
                        print(f'   - {ingr.strip()}')
                        #print(f'   - \{self.processor.extract_ingredient(ingr, self.ingr_model)}')
                    ingredients_proc = []
                    ingredients_not_loaded = []
                    for ingr in ingredients_raw:
                        try:
                            ingr = self.processor.extract_ingredient(
                                    ingr, self.ingr_model, stemmed=True)
                            ingredients_proc.append(ingr)
                        except ValueError:
                            # Ingredient could not be extracted.
                            ingredients_proc.append(None)
                            ingredients_not_loaded.append(ingr)

                    # If all ingredients were recognized
                    if None not in ingredients_proc:
                        did_store = self.recipe_model.store_recipe(title, url, 
                            ingredients_proc)
                        if did_store:
                            print('\n  Recipe loaded successfully.')
                        else:
                            print('\n  Recipe ignored, title or URL already '
                                'present.')
                    else:
                        print('\n  Recipe not loaded. Ingredients not '
                            'recognized:\n'
                            f'{ingredients_not_loaded}')
                        ... # TODO Stack up doubts to be consulted to the user.

    def store_ingredients(self):
        """
        Load ingredients from ingr_list into database.
        Those already present are ignored.
        """
        project_path = os.path.dirname(os.path.abspath(__file__))
        txt_file = project_path+'/../ingredients.txt'

        newly_added = []

        print('Loading ingredients:')

        with open(txt_file, 'r+') as f:
            for ingr in f:
                ingr = ingr.strip()
                if len(ingr.split()) == 0:
                    continue
                char_checklist = self.processor.check_chars(ingr)
                if all(char_checklist):
                    ingr_stem = self.processor.stem_ingredient(ingr)
                    if self.ingr_model.store_ingredient(ingr_stem):
                        newly_added.append((ingr_stem, ingr))
                else:
                    print(f'"{ingr}" contains invalid characters '
                    f'({ingr[char_checklist.index(False)]})')

        for stem, ingr in newly_added:
            print(f'  - {stem} ({ingr})')
        if not newly_added:
            print('No newly added ingredients.')
        else:
            print(f'{len(newly_added)} new in total.')

def main():
    """ Main entry point of the app """
    ingr_db_inter = dbInterface.Ingredients()
    recipe_db_inter = dbInterface.Recipes()
    ingr_processor = IngrProcessor()
    # ingredient = 'Pomodoro'
    # print(f'Is "{ingredient}" in the database? '
    #     f'{ingr_db_inter.is_ingr_ind_db(ingredient)}')

    loader = Loader(ingr_processor, ingr_db_inter, recipe_db_inter)
    loader.store_ingredients()
    loader.read_recipes()
    recipe_db_inter.print_stored_recipes()

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()