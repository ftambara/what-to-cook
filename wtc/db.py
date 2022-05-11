# TODO: define field and table names outside of execute statements - DRY

import logging
import sqlite3
import os

from definitions import Ingredient, Recipe, project_path

_ILLEGAL_SQL_CHARS = ';'

_DB_NAME = project_path + 'wtc/recipes.db'


def _create_table_query(*, name: str, fields: dict, constraints=()):
    header = f'CREATE TABLE IF NOT EXISTS {name}\n'

    field_strings = []
    for fname, fconstraints in fields.items():
        field_strings.append(
            f'{fname} {" ".join(fc for fc in fconstraints.split() )}')

    if constraints:
        constraints_string = f', {", ".join(constraints)}'
    else:
        constraints_string = ''

    base_query = header\
        + '('+",\n".join(field_strings)+'\n'\
        + constraints_string + '\n'\
        + ')'

    return base_query


class _SqlExecuter:

    def __init__(self, db_path) -> None:
        """
        Creates an empty table. Ignores if a table named table_name already
        exists in the database.

        - db_name = file name of the database
        - table_name = Name of the table
        - fields = non-empty dict, where keys are fields' names and values
            are fields constraints, separated by spaces.
        - constraints = string of table-level constraints, separated by spaces.
        """

        self._db_path = db_path

        self._con = sqlite3.connect(db_path)
        self._cur = self._con.cursor()

    def execute_query(self, query: str, parameters=()):

        logging.debug(query)
        if not self._is_legal_sql(query):
            raise ValueError('Invalid SQL characters')

        self._cur.execute(query, parameters)
        self._con.commit()
        return self._cur.fetchall()

    def _is_legal_sql(self, query: str):
        for c in _ILLEGAL_SQL_CHARS:
            if c in query:
                return False
        return True


class Interface:
    """
    Handles communication with the database.
    """

    def __init__(self) -> None:
        self._executer = _SqlExecuter(_DB_NAME)
        queries = []

        tables = (
            {
                'name': 'recipes',
                'fields': {
                    'recipe_id': 'integer primary key autoincrement',
                    'title': 'text unique',
                    'url': 'text unique',
                    # Both should be unique, not their combination.
                }
            },
            {
                'name': 'ingredients',
                'fields': {
                    'name': 'text primary key',
                }
            },
            {
                'name': 'recipes_ingredients',
                'fields': {
                    'recipe_id': 'integer',
                    'ingr_name': 'text',
                },
                'constraints': [
                    'primary key (recipe_id, ingr_name)',
                    'foreign key (recipe_id) references recipes(recipe_id)',
                    'foreign key (ingr_name) references ingredients(name)',
                ]
            },
            {
                'name': 'ingr_unknowns',
                'fields': {
                    'recipe_id': 'integer',
                    'text_containing_ingr': 'text',
                },
                'constraints': (
                    'foreign key (recipe_id) references recipes(recipe_id)',
                )
            },
        )
        queries.extend(_create_table_query(**table) for table in tables)

        queries.append('''
        CREATE VIEW IF NOT EXISTS recipes_with_unknowns
        AS
            SELECT *
            FROM
                (SELECT recipe_id, title, count(*) AS num_unkonwn_ingr
                FROM ingr_unkowns
                JOIN recipes using(recipe_id))
        ''')

        for query in queries:
            self._executer.execute_query(query)
        logging.info('Interface initialized.')

    def store_recipe(self, recipe: Recipe):
        """
        Store recipe in database. Raise ValueError if recipe is already
        present.

        NOTE: Recipe will be stored with the ingredient names present in the
        recipe, not those in the dabase.
        """
        query = '''
            INSERT INTO recipes(title, url)
            values(?, ?)
            '''
        params = (recipe.title, recipe.url)

        try:
            self._executer.execute_query(query, params)
        except sqlite3.IntegrityError:
            raise ValueError('Recipe already present')
        else:
            [[recipe_id]] = self._executer.execute_query(
                'select last_insert_rowid()')

            # Load any text with unknown ingredients in its corresponding table
            query = '''
                INSERT INTO ingr_unknowns(recipe_id, text_containing_ingr)
                VALUES(?, ?)
                '''
            for text in recipe.ingredients_unknown:
                params = (recipe_id, text)
                self._executer.execute_query(query, params)

            # Associate all known ingredients to recipe
            for ingr_name in recipe.ingredients_known:
                self.add_ingr_to_recipe(ingr_name, recipe_id)

    def get_recipes(self, ingr_included: list[Ingredient] = []) -> list[Recipe]:

        # Omit recipes containing unknown ingredients
        to_omit_ids = {id for id, _ in self.get_unknowns().items()}

        # Get all recipes
        query = '''
        SELECT recipe_id, title, url
        FROM recipes
        '''
        recipes = {
            recipe_id: Recipe(title, url, self.get_ingredients(recipe_id))
            for [recipe_id, title, url] in self._executer.execute_query(query)
        }

        result = []
        for recipe_id, recipe in recipes.items():
            if recipe_id in to_omit_ids:
                continue
            if all(ingr in recipe.ingredients_known for ingr in ingr_included):
                result.append(recipe)

        return result

    def store_ingredient(self, ingr_name: str):
        """Store ingredient into database."""
        query = '''
        INSERT INTO ingredients(name)
        VALUES (?)
        '''
        params = (ingr_name,)
        try:
            self._executer.execute_query(query, params)
        except sqlite3.IntegrityError:
            raise ValueError('Ingredient already present')

    def get_ingredient_names(self, recipe_id: int = None) -> list[str]:
        """Return sorted list of ingredient names"""
        if recipe_id:
            query = '''
            SELECT ingr_name
            FROM recipes_ingredients
            WHERE recipe_id = (?)
            '''
            params = (recipe_id,)
        else:
            query = 'SELECT name FROM ingredients'
            params = ()

        ingr_list = [ingr.capitalize()
                     for [ingr] in self._executer.execute_query(query, params)]
        ingr_list.sort()
        return ingr_list

    def get_ingredients(self, recipe_id: int = None) -> list[Ingredient]:
        return [Ingredient(ingr_name)
                for ingr_name in self.get_ingredient_names(recipe_id)]

    def print_recipes(self):
        query = 'select * from recipes'
        results = self._executer.execute_query(query)
        for result in results:
            print("\n")
            print(*result, sep="\n")
            query = 'select ingr_name '\
                'from recipes_ingredients '\
                'where recipe_id = (?)'
            params = (result[0],)
            ingredients = self._executer.execute_query(
                query, params)
            for ingredient in ingredients:
                print("  -", *ingredient)

    @property
    def num_unknowns(self):
        """Number of unknowns to review. Read-only."""
        query = '''
            SELECT count(*)
            FROM recipes r
            JOIN ingr_unknowns iu
            USING(recipe_id)
        '''
        [[count]] = self._executer.execute_query(query)
        return count

    def get_unknowns(self) -> dict[str: list[Ingredient]]:
        """
        Return dict 
            {recipe_id: ingredients_list}
        containing all entries from which an ingredient could not be extracted.
        """
        query = '''
            SELECT r.recipe_id, iu.text_containing_ingr
            FROM recipes r
            JOIN ingr_unknowns iu
            USING(recipe_id)
        '''
        results = {}
        for id, text_with_unknowns in self._executer.execute_query(query):
            results.setdefault(id, []).append(text_with_unknowns)
        return results

    def get_next_unknown(self) -> tuple:
        """
        Return one unknown as a tuple:
            (recipe_id, recipe_title, recipe_url, text_with_unknown)
        """
        # Search is executed each time to refresh the list of results after
        # a new ingredient has been added to the database.
        query = '''
            SELECT r.recipe_id, r.title, r.url, iu.text_containing_ingr
            FROM recipes r
            JOIN ingr_unknowns iu
            USING(recipe_id)
            LIMIT 1
        '''
        [result] = self._executer.execute_query(query)
        return result

    def make_known(self, recipe_id, text_with_unkown, extracted_ingredient):
        """
        Add extracted ingredient to database, update unknowns accordingly,
        keeping the link with the original recipe.
        """
        # Delete text from ingr_unknowns table
        query = '''
            DELETE FROM ingr_unknowns
            WHERE text_containing_ingr = (?)
            LIMIT 1
            '''
        params = (text_with_unkown,)
        self._executer.execute_query(query, params)

        # Store the extracted ingredient in the ingredients table
        self.store_ingredient(extracted_ingredient)

        self.add_ingr_to_recipe(extracted_ingredient, recipe_id)

        logging.info(f'Extracted "{extracted_ingredient}" \
            from "{text_with_unkown}"')

    def add_ingr_to_recipe(self, ingr_name, recipe_id):
        """Associate ingredient to corresponding recipe"""
        query = '''
            INSERT INTO recipes_ingredients(recipe_id, ingr_name)
            VALUES(?, ?)
            '''
        params = (recipe_id, ingr_name)
        self._executer.execute_query(query, params)

    def is_ingr(self, string: str) -> bool:
        """
        Check if string is a kown ingredient.
        """
        query = 'select name '\
                'from ingredients '\
                'where name = (?)'
        params = (string,)
        results = self._executer.execute_query(query, params)
        assert len(results) in (0, 1)
        return True if len(results) == 1 else False
