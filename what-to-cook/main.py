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
        ...
    
    def read_recipes(recipe_list):
        """
        Read the CSV file from RECIPES_TO_PROCESS_FILE_LOC
        and call the Processor to extract the ingredients out of each entry.
        Store the recipes of which it has no doubts on the database.
        Return tuple of ints (new_recipes, duplicate, doubts, errors)?
        """
        ...

class IngredientProcessor(object):
    """
    Extract the ingredient out of a string line, communicating with the
    ingredient database
    """
    
    def __init__(self):
        ...
    
    def extract_ingredient(line: str):
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

    def get_longest_ingr(self):
        """Return number of words in the longest ingredient stored"""
        ...
    
    def is_ingr_in_db(self, string):
        """
        Consults database to see if string is present in the database
        """
        ...
