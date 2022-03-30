#!/usr/bin/env python3
"""

"""

#BUG loader loads newline characters if alone (empty row in ingredients.txt)

__author__ = "Federico Tambara"
__license__ = "MIT"

import sqlite3
import os


class UserInterface(object):
    """
    Middle man between User and the rest of the program
    """
    
    def __init__(self):
        ...
    
class DbInterface(object):
    """
    Do not instantiate directly. Use subclasses.
    """
    def __init__(self) -> None:
        project_path = os.path.dirname(os.path.abspath(__file__))
        
        self.con = sqlite3.connect(project_path + '/recipes.db')
        self.cur = self.con.cursor()
        self.cur.execute('create table if not exists recipes '
            '(recipe_id integer primary key autoincrement, '
            'title text, '
            'url text unique '
            ');')

        self.cur.execute('create table if not exists ingredients'
            +'(name text primary key'
            +');')
        self.con.commit()

        self.cur.execute('create table if not exists recipes_ingredients '
            '(recipe_id integer, '
            'ingr_name text, '
            'primary key (recipe_id, ingr_name), '
            'foreign key (recipe_id) references recipes(recipe_id), '
            'foreign key (ingr_name) references ingredients(name)'
            ');')
        self.con.commit()

class IngrDbInterface(DbInterface):
    """Communicate with the ingredient database."""

    def store_ingredient(self, ingredient: str):
        """
        Load ingredient into database.
        Return True if stored, False if already present
        """ 
        return self.store_ingredients((ingredient,))[0]
    
    def store_ingredients(self, ingr_list: list[str]):
        """
        Load ingredients from ingr_list into database.
        Those already present are ignored.
        Return map of bools where element is True if corresponding
        ingredient was added to database.
        """
        added = []        
        for line in ingr_list:
            line = line.strip()
            self.cur.execute('select name from ingredients '
                                +'where name = (?)', (line,))
            if not self.cur.fetchall():
                # If ingredient was not found, store it
                self.cur.execute('insert into ingredients(name)'
                                    +'values (?);', (line,))
                self.con.commit()
                added.append(True)
            else:
                added.append(False)
        return added

        
    def is_ingr_ind_db(self, ingredient: str):
        # TODO to think about. ingredient.stem should return its stem.
        self.cur.execute('select name '
                        'from ingredients '
                        'where name = (?)',
                        (ingredient,))

        results = self.cur.fetchall()                                
        assert len(results) in (0, 1)
        return True if len(results) == 1 else False

class IngrProcessor(object):
    """
    Extract the ingredient out of a string line, communicating with the
    ingredient database
    """
    
    def __init__(self):
        ...
    
    def extract_ingredient(self, line: str, model: IngrDbInterface,
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


class RecipeDbInterface(DbInterface):
    
    def store_recipe(self, title: str, url: str, ingr_list: list[str]):
        """
        Store recipe into database.
        Raise exception if already present.
        """
        # Store recipe title and url into recipes
        did_store = False
        try:
            self.cur.execute('insert into recipes(title, url) '
                'values (?, ?);', (title, url))
            self.con.commit()
            did_store = True
        except sqlite3.IntegrityError:
            return did_store
        
        # Get the recipe autogenereted id
        self.cur.execute('select last_insert_rowid();')
        last_recipe_id = self.cur.fetchone()[0]
        
        # Associate each ingredient with the obtained recipe id
        for ingr in ingr_list:
            self.cur.execute(
                'insert into recipes_ingredients(recipe_id, ingr_name) '
                'values(?, ?);', (last_recipe_id, ingr))
            self.con.commit()
        
        return did_store

    def print_stored_recipes(self):
        self.cur.execute('select r.title, i.name '
                         'from recipes r '
                         'inner join recipes_ingredients ri '
                         '  on r.recipe_id = ri.recipe_id '
                         'inner join ingredients i '
                         '  on ri.ingr_name = i.name')
        print("\n")
        for row in self.cur.fetchall():
            print(row)

class Loader(object):
    """
    Responisble for loading recipes from a file, delegate ingredient
    extraction, and building list of doubts and errors to be handled later.
    """
    
    def __init__(self, processor: IngrProcessor,
        ingr_model: IngrDbInterface, recipe_model: RecipeDbInterface):
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
                            print('\n  Recipe ignored, URL already present.')
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
                ingr_stem = self.processor.stem_ingredient(ingr)
                if self.ingr_model.store_ingredient(ingr_stem):
                    newly_added.append((ingr_stem, ingr))

        for stem, ingr in newly_added:
            print(f'  - {stem} ({ingr})')
        if not newly_added:
            print('No newly added ingredients.')
        else:
            print(f'{len(newly_added)} new in total.')

def main():
    """ Main entry point of the app """
    ingr_db_inter = IngrDbInterface()
    recipe_db_inter = RecipeDbInterface()
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