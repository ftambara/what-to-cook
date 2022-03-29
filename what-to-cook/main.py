#!/usr/bin/env python3
"""

"""

__author__ = "Federico Tambara"
__license__ = "MIT"

import sqlite3


class UserInterface(object):
    """
    Middle man between User and the rest of the program
    """
    
    def __init__(self):
        ...

class Loader(object):
    """
    Responisble for loading recipes from a file, delegate ingredient
    extraction, and building list of doubts and errors to be handled later.
    """
    
    def __init__(self):
        self.ingr_to_load = []
    
    def read_recipes(self, recipe_list):
        """
        Read the CSV file from RECIPES_TO_PROCESS_FILE_LOC
        and call the Processor to extract the ingredients out of each entry.
        Store the recipes of which it has no doubts on the database.
        Return tuple of ints (new_recipes, duplicate, doubts, errors)?
        """
        ...
    

class IngrProcessor(object):
    """
    Extract the ingredient out of a string line, communicating with the
    ingredient database
    """
    
    def __init__(self):
        ...
    
    def extract_ingredient(self, line: str):
        """
        Extract the first ingredient found in line.
        Ingredients have priority by the number of words they contain
        for example 'spring onion' has priority over 'onion'
        Return extracted ingredient
        """
        ... # get longest ingr
        ... # parse line in descending length window
        ... # return first found match
        ... # if no match, raise exception

class IngrDbInterface(object):
    """Communicate with the ingredient database."""

    def __init__(self):
        import os

        project_path = os.path.dirname(os.path.abspath(__file__))
        
        self.con = sqlite3.connect(project_path + '/ingredients.db')
        self.cur = self.con.cursor()
        self.cur.execute('create table if not exists ingredients'
            +'(name text primary key'
            +');')
        self.con.commit()

    def load_ingredients(self):
        """
        Load ingredients from ingr_list.
        Those already present are ignored.
        """
        import os
        

        project_path = os.path.dirname(os.path.abspath(__file__))
        txt_file = project_path+'/../ingredients.txt'

        newly_added = []

        print('Loading ingredients:')

        with open(txt_file, 'r+') as f:
            for line in f:
                line = line.strip()
                line_striped = self._stem_ingredient(line)
                self.cur.execute('select name from ingredients '
                                 +'where name = (?)', (line_striped,))
                if not self.cur.fetchall():
                    self.cur.execute('insert into ingredients(name)'
                                     +'values (?);', (line_striped,))
                    self.con.commit()
                    newly_added.append(f'{line_striped} ({line})')
        
        for ingr in newly_added:
            print(f'  - {ingr}')
        if not newly_added:
            print('No newly added ingredients.')
        else:
            print(f'{len(newly_added)} new in total.')
        
    def is_ingr_ind_db(self, ingredient: str):
        # TODO to think about. ingredient.stem should return its stem.
        ingredient = self._stem_ingredient(ingredient)
        _ = self.cur.execute('select name '
                                'from ingredients '
                                'where name = (?)',
                                (ingredient,))

        results = self.cur.fetchall()                                
        assert len(results) in (0, 1)
        for result in results:
            print(result)
        print(len(results))
        return True if len(results) == 1 else False

        

    def _stem_ingredient(self, ingr: str):
        """Always save ingredients' stems into the database, not full word."""
        return self._stem_ingredients([ingr])[0]
    
    def _stem_ingredients(self, ingr_list: list[str]):
        """Always save ingredients' stems into the database, not full word."""
        import snowballstemmer as sb

        stemmer = sb.stemmer('italian')
        return stemmer.stemWords(ingr_list)
    
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
    

def main():
    """ Main entry point of the app """
    ingr_db_inter = IngrDbInterface()
    ingr_db_inter.load_ingredients()
    ingredient = 'Pomodoro'
    print(f'Is "{ingredient}" in the database? '
        f'{ingr_db_inter.is_ingr_ind_db(ingredient)}')

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()