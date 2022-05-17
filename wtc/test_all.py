"""
This file demonstrates common uses for the Python unittest module
https://docs.python.org/3/library/unittest.html
"""

import unittest
import os

import pytest

from processing import Loader, IngrParser, Searcher
from definitions import project_path, Ingredient, Recipe


@pytest.fixture
def clean_setup(scope="function"):
    import os
    os.remove(project_path+'/wtc/recipes.db')
    loader = Loader()


@pytest.fixture
def recipes_test_set() -> list[Recipe]:
    return [
        Recipe(
            'Hummus di carote',
            'https://www.cucchiaio.it/ricetta/hummus-carote/',
            (
                Ingredient('carote'),
                Ingredient('tahina'),
                Ingredient('aglio'),
                Ingredient('paprika'),
                Ingredient('erba cipollina'),
                Ingredient('olio'),
                Ingredient('aceto'),
                Ingredient('sale'),
                Ingredient('pepe')
            )
        ),
        Recipe(
            'Asparagi con burro salato profumati al limone',
            'https://www.cucchiaio.it/ricetta/ricetta-asparagi-burro-profumato-limone/',
            (
                Ingredient('asparagi'),
                Ingredient('burro'),
                Ingredient('limone'),
                Ingredient('sale')
            )
        ),
        Recipe(
            'Merluzzo gratinato',
            'https://www.cucchiaio.it/ricetta/merluzzo-gratinato/',
            (
                Ingredient('merluzzo'),
                Ingredient('pangrattato'),
                Ingredient('vino'),
                Ingredient('limone'),
                Ingredient('prezzemolo'),
                Ingredient('salvia'),
                Ingredient('rosmarino'),
                Ingredient('olio'),
                Ingredient('sale'),
                Ingredient('pepe')
            )
        ),
        Recipe(
            'Trifle di panna cotta',
            'https://www.cucchiaio.it/ricetta/ricetta-trifle-panna-cotta/',
            (
                Ingredient('panna'),
                Ingredient('ananas'),
                Ingredient('kiwi'),
                Ingredient('amaretti'),
                Ingredient('latte'),
                Ingredient('zucchero'),
                Ingredient('arancia'),
                Ingredient('gelatina')
            )
        ),
    ]


@pytest.fixture
def ingredients_test_set(recipes_test_set):
    unique_ingredients = []
    for recipe in recipes_test_set:
        for ingredient in recipe.ingredients_known:
            if ingredient not in unique_ingredients:
                unique_ingredients.append(ingredient)
    return unique_ingredients


@pytest.fixture
def fill_ingredients_file_full(ingredients_test_set):
    os.rename(project_path+'ingredients.txt',
              project_path+'ingredients-backup.txt')

    with open(project_path+'ingredients.txt', 'w') as fp:
        for ingredient in ingredients_test_set:
            fp.write(ingredient.name + '\n')
    yield

    os.remove(project_path+'ingredients.txt')
    os.rename(project_path+'ingredients-backup.txt',
              project_path+'ingredients.txt')


class TestApp:

    # @pytest.fixture
    # def expected_recipes_dict_list(expected_recipes, scope="session"):
    #     result = []
    #     for recipe in expected_recipes:
    #         result.append({
    #             'title': recipe.title,
    #             'url': recipe.url,
    #             'unknowns': recipe.unknown_ingredients
    #         })

    #     return result

    def test_no_known_ingredients(self,
                                  clean_setup,
                                  recipes_test_set):
        """
        Test recipe loading without any ingredients in the database.
        """

        loader = Loader()
        # TODO let loader load recipes from arbitrary file or from a dict,
        # delegating file processing to another function.
        loader.load_recipes()

        pending_review = loader.get_pending_review()
        assert len(pending_review) == len(recipes_test_set)

        searcher = Searcher()
        assert searcher.get_ingredients() == []

        assert not searcher.get_recipes()

        assert loader.num_pending_review == 31

        id = searcher.get_recipe_id(
            'Hummus di carote',
            'https://www.cucchiaio.it/ricetta/hummus-carote/')

        loader.solve_unknown(id, '500 g di carote', 'Carota')
        assert loader.num_pending_review == 30

        loader.solve_unknown(
            id, '5 cucchiai di olio extravergine di oliva', 'olio')
        assert loader.num_pending_review == 28

        known_ingredients = searcher.get_ingredients()
        assert len(known_ingredients) == 2
        for ingr in known_ingredients:
            assert ingr in [Ingredient('carote'), Ingredient('Olio')]

    def test_no_unknown_ingredients(self,
                                    clean_setup,
                                    fill_ingredients_file_full,
                                    recipes_test_set: list[Recipe],
                                    ingredients_test_set):
        """
        Test recipe loading by first loading in the database the ingredients
        present in the recipes file.
        """
        loader = Loader()
        # TODO let loader load recipes and ingredients from arbitrary file or
        # from a dict, delegating file processing to another function.

        loader.store_ingredients()
        loader.load_recipes()

        pending_review = loader.get_pending_review()
        assert not pending_review

        searcher = Searcher()
        ingredients = searcher.get_ingredients()
        assert len(ingredients) == len(ingredients_test_set)
        for ingredient in ingredients:
            assert ingredient in ingredients_test_set

        recipes = searcher.get_recipes()
        assert len(recipes) == len(recipes_test_set)
        for recipe in recipes:
            assert recipe in recipes_test_set

        assert recipes_test_set[:1] == searcher.get_recipes(['carota'])
        assert recipes_test_set[:1] == searcher.get_recipes(['Carote'])
        assert recipes_test_set[:3:2] == searcher.get_recipes(['Olio'])
        assert recipes_test_set[1:2] \
            == searcher.get_recipes(['Asparago', 'burro'])


if __name__ == '__main__':
    pytest.main()
