"""
This file demonstrates common uses for the Python unittest module
https://docs.python.org/3/library/unittest.html
"""

import unittest
import os
from processing import Loader, IngrParser
from definitions import project_path, Ingredient


class TestRecipeLoading(unittest.TestCase):

    def test_ingredient_parser(self):

        expected_ingr_lists = [
            ['carote', 'tahina', 'aglio', 'paprika', 'erba cipollina', 'olio',
             'aceto', 'sale', 'pepe'],
            ['asparagi', 'burro', 'limone', 'sale'],
            ['merluzzo', 'pangrattato', 'vino', 'limone', 'prezzemolo',
             'salvia', 'rosmarino', 'olio', 'sale', 'pepe']
        ]
        filename = project_path + 'wtc/test-recipes-to-load.csv'

        parser = IngrParser()

        def is_ingr(ingredient: str):
            ingr_list = [Ingredient(ingr) for list_ in expected_ingr_lists
                         for ingr in list_]
            return Ingredient(ingredient) in ingr_list

        with open(filename) as f:
            lines = f.readlines()
            index = 0
        for line in lines:
            if line[0] == '#':
                continue
            else:
                ingr_list = []
                raw_ingr_list = line.split(sep=',')

                # Skip title and URL
                raw_ingr_list = raw_ingr_list[2:]
                # Process every entry for that line
                for entry in raw_ingr_list:
                    ingr_list.append(
                        parser.extract_ingredient(entry, is_ingr))

                # Compare with expected ingredients for that line
                self.assertListEqual(expected_ingr_lists[index], ingr_list)

                index += 1

    # def test_recipe_fetching(self):
    #     """
    #     Make program load known recipes, then search recipes for each
    #     ingredient present in the ones that have been loaded.
    #     Check if recipes obtained through search are the correct ones.
    #     """
    #     ...


if __name__ == '__main__':
    unittest.main()
