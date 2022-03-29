"""
This file demonstrates common uses for the Python unittest module
https://docs.python.org/3/library/unittest.html
"""

import unittest
import os
from main import IngrDbInterface, IngrProcessor
from main import Loader


class TestRecipeLoading(unittest.TestCase):
    """ This is one of potentially many TestCases """

    def setUp(self):
        self.seq = list(range(10))

    def test_ingredient_extraction(self):
        """
        """
        processor = IngrProcessor()
        expected_ingr_list = [
            ['carote', 'tahina', 'aglio', 'paprika', 'erba cipollina', 'olio',
            'aceto', 'sale', 'pepe'],
            ['asparagi', 'burro', 'limone', 'sale'],
            ['merluzzo', 'pangrattato', 'vino', 'limone', 'prezzemolo',
            'salvia', 'rosmarino', 'olio', 'sale', 'pepe']
        ]
        directory = os.path.dirname(os.path.abspath(__file__))
        filename = directory + '/test-recipes-to-load.csv'
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
                    print("$$", entry)
                    ingr_list.append(processor.extract_ingredient(entry,
                        IngrDbInterface()))
                # Compare with expected ingredients for that line
                self.assertListEqual(expected_ingr_list[index], ingr_list)

                index += 1
            


if __name__ == '__main__':
    unittest.main()