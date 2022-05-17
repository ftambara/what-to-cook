"""Recipe class definition"""

import os

project_path = os.path.join(os.path.dirname(__file__), "../")


class Ingredient:
    """
    Ingredients are stored by name but compared by stem, to avoid saying
    "onion" and "onions" are different ingredients.

    TODO configure ingredient language. Right now supports italian only.
    """

    def __init__(self, name: str) -> None:
        """
        Create an ingredient instance.
        name should be a singular noun, preferrably one word only.
        """
        import snowballstemmer as sb

        self._name = name.lower().strip()

        stemmer = sb.stemmer('italian')
        self._stem = stemmer.stemWord(self._name)

    @property
    def name(self):
        return self._name

    def __eq__(self, other) -> bool:
        return self._stem == other._stem

    def __repr__(self) -> str:
        return f'Ingredient({self.name})'

    def __str__(self) -> str:
        return self.name


class Recipe(object):
    """
    Group information and actions relevant to a recipe.
    title: The title of the recipe.
    url: The URL of the recipe.
    ingredients: List of ingredients the recipe contains."""

    def __init__(self, title: str = None, url: str = None,
                 ingredients_known: list[Ingredient] = [],
                 ingredients_unknown: list[str] = []):
        self._title = title
        self._url = url
        self._ingredients_known = ingredients_known
        self._ingredients_unknown = ingredients_unknown

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
    def ingredients_known(self):
        return self._ingredients_known

    @ingredients_known.setter
    def ingredients_known(self, ingr_names: list):
        self._ingredients_known = list(ingr_names)

    @property
    def ingredients_unknown(self):
        return self._ingredients_unknown

    @ingredients_unknown.setter
    def ingredients_unknown(self, ingr_names: list):
        self._ingredients_unknown = list(ingr_names)

    def has_unknowns(self):
        return (True if self.ingredients_unknown else False)

    def __str__(self):
        return f'{self.title}\n'\
            + f'{self.url}\n'\
            + f'{", ".join(str(i) for i in self.ingredients_known)}'

    def __eq__(self, __o: object) -> bool:
        return (
            self.title == __o.title
            and self.url == __o.url
            and len(self.ingredients_known) == len(__o.ingredients_known)
            and all(True if ingr in self.ingredients_known else False
                    for ingr in self.ingredients_known)
            and len(self.ingredients_unknown) == len(__o.ingredients_unknown)
            and all(True if ingr in self.ingredients_unknown else False
                    for ingr in self.ingredients_unknown)
        )
