# TODO: define field and table names outside of execute statements - DRY

import sqlite3
import os

from definitions import Ingredient, Recipe

_ALLOWED_EXTRA_CHARS = ['()']

project_path = os.path.dirname(os.path.abspath(__file__))
_DB_NAME = project_path + '/recipes.db'


def _is_valid_sql(*args: str):
    for string in args:
        for c in string:
            if c.isalnum is False and c not in _ALLOWED_EXTRA_CHARS:
                return False
        return True


class Table:
    def __init__(self, table_name: str, *, fields, constraints={}) -> None:
        """
        Creates an empty table. Ignores if a table named table_name already
        exists in the database.

        - db_name = file name of the database
        - table_name = Name of the table
        - fields = non-empty dict, where keys are fields' names and values
            are fields constraints, separated by spaces.
        - constraints = string of table-level constraints, separated by spaces.

        NOTE: SQL object names can only contain alphanumeric characters. An
        exception will be raised otherwise.
        """

        global _DB_NAME
        self._table_name = table_name
        self._fields = fields
        self._constraints = constraints

        self._check_all_sql_names()

        self._con = sqlite3.connect(_DB_NAME)
        self._cur = self._con.cursor()

        # Build base query with placeholders. Title already in place.
        query = self._build_create_table_query()

        # Create table
        self._cur.execute(query)
        self._con.commit()
        print(f'\n"{self._table_name}" table created in "{_DB_NAME}"')

    def _build_create_table_query(self):
        header = f'create table if not exists {self._table_name}\n'

        field_strings = []
        for fname, fconstraints in self._fields.items():
            field_strings.append(
                f'{fname} {" ".join(fc for fc in fconstraints.split() )}')

        if self._constraints:
            constraints_string = f', {", ".join(self._constraints)}'
        else:
            constraints_string = ''

        base_query = header\
            + '('+",\n".join(field_strings)+'\n'\
            + constraints_string + '\n'\
            + ');'

        return base_query

    def _check_sql_name(self, name: str):
        if _is_valid_sql(name):
            return True
        else:
            raise ValueError('Improper SQL object name.')

    def _check_all_sql_names(self):
        self._check_sql_name(self._table_name)

        for fname, fconstraints in self._fields.items():
            self._check_sql_name(fname)
            self._check_sql_name(fconstraints)

        for constraint in self._constraints:
            self._check_sql_name(constraint)

    def execute_query(self, query: str, parameters=()):
        self._cur.execute(query, parameters)
        self._con.commit()
        return self._cur.fetchall()


class Interface:
    """
    Do not instantiate directly. Use subclasses.
    """

    def __init__(self) -> None:

        # TODO move paths to setup.py

        self._tables = {}

        tables = {
            'recipes': {
                'fields': {
                    'id': 'integer primary key autoincrement',
                    'title': 'text unique',
                    'url': 'text unique'
                    # Both should be unique, not the combination,
                    # that's why they are explicitly defined to be so.
                }
            },
            'ingredients': {
                'fields': {
                    'name': 'text primary key',
                }
            },
            'recipes_ingredients': {
                'fields': {
                    'recipe_id': 'integer',
                    'ingr_name': 'text',
                },
                'constraints': [
                    'primary key (recipe_id, ingr_name)',
                    'foreign key (recipe_id) references recipes(recipe_id)',
                    'foreign key (ingr_name) references ingredients(name)',
                ]
            }
        }

        for k, v in tables.items():
            self._tables[k] = Table(k, **v)

    def store_ingredient(self, ingr_name: str):
        query = 'insert into ingredients(name) '\
                + 'values (?);'
        params = (ingr_name,)
        try:
            self._tables['ingredients'].execute_query(query, params)
        except sqlite3.IntegrityError:
            raise ValueError('Ingredient already present')

    def store_recipe(self, recipe: Recipe):
        """
        Store recipe in database.
        Recipe will be stored with the ingredient names present in the
        recipe, not those in the dabase.
        """
        query = 'insert into '\
                'recipes(title, url) '\
                'values(?, ?)'
        params = (recipe.title, recipe.url)
        try:
            print(repr(recipe.title))
            self._tables['recipes'].execute_query(query, params)
        except sqlite3.IntegrityError:
            raise ValueError('Recipe already present')
        else:
            [[recipe_id]] = self._tables['recipes'].execute_query(
                'select last_insert_rowid();')
            query = 'insert into '\
                    'recipes_ingredients(recipe_id, ingr_name) '\
                    'values(?, ?)'
            for ingr_name in recipe.ingr_names:
                params = (recipe_id, ingr_name)
                self._tables['recipes_ingredients'].execute_query(
                    query, params)

    def get_ingredients(self):
        query = 'select * from ingredients'
        return self._tables['ingredients'].execute_query(query)

    def print_recipes(self):
        query = 'select * from recipes'
        results = self._tables['ingredients'].execute_query(query)
        for result in results:
            print("\n")
            print(*result[1:], sep="\n")
            query = 'select ingr_name '\
                'from recipes_ingredients '\
                'where recipe_id = (?)'
            params = (result[0],)
            ingredients = self._tables['ingredients'].execute_query(
                query, params)
            for ingredient in ingredients:
                print("  -", *ingredient)

    def is_ingr_in_db(self, ingr_name: str):
        query = 'select name '\
                'from ingredients '\
                'where name = (?)'
        params = (ingr_name,)
        results = self._tables['ingredients'].execute_query(query, params)
        assert len(results) in (0, 1)
        return True if len(results) == 1 else False