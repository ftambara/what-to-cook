from kivy.lang import Builder

from processing import Loader, Searcher 

Builder.load_file('gui.kv')

def start_app(loader: Loader, searcher: Searcher):
    raise

if __name__ == '__main__':
    start_app()