# TODO: define field and table names outside of execute statements - DRY

import logging
import sqlite3
import os

from definitions import Recipe, project_path

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

    def store_ingredient(self, ingr_name: str):
        query = 'insert into ingredients(name) '\
                + 'values (?)'
        params = (ingr_name,)
        try:
            self._executer.execute_query(query, params)
        except sqlite3.IntegrityError:
            raise ValueError('Ingredient already present')

    def store_recipe(self, recipe: Recipe):
        # TODO accept recipes with unknowns
        """
        Store recipe in database. Raise ValueError if recipe is already
        present.

        NOTE: Recipe will be stored with the ingredient names present in the
        recipe, not those in the dabase.
        """
        query = 'insert into '\
                'recipes(title, url) '\
                'values(?, ?)'
        params = (recipe.title, recipe.url)
        try:
            self._executer.execute_query(query, params)
        except sqlite3.IntegrityError:
            raise ValueError('Recipe already present')
        else:
            [[recipe_id]] = self._executer.execute_query(
                'select last_insert_rowid()')
            query = 'insert into '\
                    'recipes_ingredients(recipe_id, ingr_name) '\
                    'values(?, ?)'
            for ingr_name in recipe.ingr_names:
                params = (recipe_id, ingr_name)
                self._executer.execute_query(
                    query, params)

    def get_ingredients(self):
        query = 'select * from ingredients'
        return self._executer.execute_query(query)

    def print_recipes(self):
        query = 'select * from recipes'
        results = self._executer.execute_query(query)
        for result in results:
            print("\n")
            print(*result[1:], sep="\n")
            query = 'select ingr_name '\
                'from recipes_ingredients '\
                'where recipe_id = (?)'
            params = (result[0],)
            ingredients = self._executer.execute_query(
                query, params)
            for ingredient in ingredients:
                print("  -", *ingredient)

    def is_ingr(self, string: str):
        query = 'select name '\
                'from ingredients '\
                'where name = (?)'
        params = (string,)
        results = self._executer.execute_query(query, params)
        assert len(results) in (0, 1)
        return True if len(results) == 1 else False
