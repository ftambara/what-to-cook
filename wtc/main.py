__author__ = "Federico Tambara"
__license__ = "MIT"

import gui
from processing import Loader, Searcher
from db import Interface


def main():
    """ Main entry point of the app """
    loader = Loader()
    searcher = Searcher()
    loader.store_ingredients() #TODO create startup routine
    loaded, not_loaded, errors = loader.load_recipes()
    print(f'{loaded=}, {not_loaded=}, {errors=}')
    Interface().print_recipes() #DEBUG
    print("\n\n\n\n")
    gui.start_app(loader, searcher)


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()
    