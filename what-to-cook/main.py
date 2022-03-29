#!/usr/bin/env python3
"""

"""

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
    

class IngrDbInterface(object):
    """Communicate with the ingredient database."""

    def __init__(self):
        project_path = os.path.dirname(os.path.abspath(__file__))
        
        self.con = sqlite3.connect(project_path + '/recipes.db')
        self.cur = self.con.cursor()
        self.cur.execute('create table if not exists ingredients'
            +'(name text primary key'
            +');')
        self.con.commit()

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
    
    def load_test_data(self):
        try: 
            self.cur.execute('''CREATE TABLE stocks
               (date text, trans text, symbol text, qty real, price real)''')
        except sqlite3.OperationalError:
            return
        self.cur.execute("INSERT INTO stocks VALUES ('2006-01-05','BUY','RHAT',50,35.14)")
        self.con.commit()

    def retrieve_test_data(self):
        for row in self.cur.execute('SELECT * FROM stocks ORDER BY price'):
            print(row)
    

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
        import re
        
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
            if model.is_ingr_ind_db(self._stem_ingredient(word)):
                found_match = True
                break
        
        # Return first found match
        if found_match:
            if stemmed:
                return self._stem_ingredient(word)
            else:
                return word
        # If no match, raise exception
        else:
            raise ValueError('line did not contain any known ingredient')

    def _stem_ingredient(self, ingr: str):
        """Always save ingredients' stems into the database, not full word."""
        return self._stem_ingredients([ingr])[0]
    
    def _stem_ingredients(self, ingr_list: list[str]):
        """Always save ingredients' stems into the database, not full word."""
        import snowballstemmer as sb

        stemmer = sb.stemmer('italian')
        return stemmer.stemWords(ingr_list)


class RecipeDbInterface(object):
    def __init__(self) -> None:
        # TODO base DbInterface class, make ingr and recipe subclasses
        # put database creation in DbInterface constructor, 
        project_path = os.path.dirname(os.path.abspath(__file__))
        
        self.con = sqlite3.connect(project_path + '/recipes.db')
        self.cur = self.con.cursor()
        self.cur.execute('create table if not exists recipes '
            '(recipe_id integer primary key autoincrement, '
            'title text, '
            'url text unique '
            ');')
        self.con.commit()
        
        self.cur.execute('create table if not exists recipes_ingredients '
            '(recipe_id integer, '
            'ingr_name text, '
            'primary key (recipe_id, ingr_name), '
            'foreign key (recipe_id) references recipes(recipe_id), '
            'foreign key (ingr_name) references ingredients(name)'
            ');')
        self.con.commit()
    
    def store_recipe(self, title: str, url: str, ingr_list: list[str]):
        """
        Store recipe into database.
        Raise exception if already present.
        """
        self.cur.execute('insert into recipes(title, url) '
            'values (?, ?);', (title, url))
        self.con.commit()
        self.cur.execute('select last_insert_rowid();')
        last_recipe_id = self.cur.fetchone()
        for ingr in ingr_list:
            self.cur.execute(
                'insert into recipes_ingredients(recipe_id, ingr_name) '
                'values(?, ?);', (last_recipe_id, ingr))

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
        with open(recipes_file) as f:
            for line in f:
                # Ignore lines starting with '#' character.
                if line.strip()[0] == '#':
                    continue
                else:
                    title, url, *ingredients_raw = line.split(',')
                    print(f"Title: {title}")
                    print(f"URL: {url}")
                    for ingr in ingredients_raw:
                        print(f" - {ingr}")
                    print("\n")
                    ingredients_proc = []
                    for ingr in ingredients_raw:
                        try:
                            ingredients_proc.append(
                                self.processor.extract_ingredient(
                                    ingr, self.ingr_model, stemmed=True))
                        except ValueError:
                            ingredients_proc.append(None)
                    
                    # If all ingredients were recognized
                    if None not in ingredients_proc:
                        self.recipe_model.store_recipe(title, url, 
                            ingredients_proc)
                    else:
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
            for line in f:
                line = line.strip()
                if self.ingr_model.store_ingredient(line):
                    newly_added.append(line)

        for ingr in newly_added:
            print(f'  - {ingr}')
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
    #loader.read_recipes()

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()