__author__ = "Federico Tambara"
__license__ = "MIT"

import gui
from processing import Loader, Searcher


def main():
    """ Main entry point of the app """
    loader = Loader()
    searcher = Searcher()
    loader.store_ingredients() #TODO call through GUI when user requires.
    gui.start_app(loader, searcher)


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()
    