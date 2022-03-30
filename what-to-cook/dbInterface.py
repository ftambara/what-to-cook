import sqlite3
import os

class Base(object):
    """
    Do not instantiate directly. Use subclasses.
    """
    def __init__(self) -> None:
        project_path = os.path.dirname(os.path.abspath(__file__))
        
        self.con = sqlite3.connect(project_path + '/recipes.db')
        self.cur = self.con.cursor()
        self.cur.execute('create table if not exists recipes '
            '(recipe_id integer primary key autoincrement, '
            'title text unique, '
            'url text unique'
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

class Ingredients(Base):
    """Communicate with the ingredients table."""

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

class Recipes(Base):
    """Communicate with recipes and recipes_ingredients tables."""
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