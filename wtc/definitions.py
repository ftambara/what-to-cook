"""Recipe class definition"""

import os

project_path = os.path.join(os.path.dirname(__file__), "../")


class Recipe(object):
    """
    Group information and actions relevant to a recipe.
    title: The title of the recipe.
    url: The URL of the recipe. Include https:// part
    ingredients: List of ingredients the recipe contains."""

    def __init__(self, title: str = None, url: str = None,
                 ingr_known: list[str] = [], ingr_unknown: list[str] = []):
        self._title = title
        self._url = url
        self._ingr_known = ingr_known
        self._ingr_unknown = ingr_unknown

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url):
        self._url = url

    @property
    def ingr_names(self):
        return self._ingr_known

    @ingr_names.setter
    def ingr_names(self, ingr_names: list):
        self._ingr_known = list(ingr_names)

    def __str__(self):
        return f'{self.title}\n'\
            + f'{self.url}\n'\
            + f'{", ".join(self.ingr_names)}'


class Ingredient:
    """
    Ingredients are stored by name but compared by stem, to avoid saying
    "onion" and "onions" are different ingredients.
    """

    def __init__(self, name: str) -> None:
        """
        Create an ingredient instance.
        name should be a singular noun, preferrably one word only.
        """
        import snowballstemmer as sb

        self._name = name

        stemmer = sb.stemmer('italian')
        self._stem = stemmer.stemWord(name)

    @property
    def name(self):
        return self._name

    def __eq__(self, other) -> bool:
        return self._stem == other._stem

    def __repr__(self) -> str:
        return f'Ingredient({self.name})'

    def __str__(self) -> str:
        return self.name
