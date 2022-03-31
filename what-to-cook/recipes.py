"""Recipe class definition"""

class Recipe(object):
    """
    Group information and actions relevant to a recipe.
    title: The title of the recipe.
    url: The URL of the recipe. Include https:// part
    ingredients: List of ingredients the recipe contains."""
    def __init__(self, title: str, url: str, ingredients: list[str]):
        self.title = title
        self.url = url
        self.ingredients = ingredients

    def set_ingredients(self, ingredients: list[str]):
        self.ingredients = ingredients

    def __str__(self):
        return f'{self.title}\n'\
            +f'{self.url}\n'\
            +f'{", ".join(self.ingredients)}'