from kivy.lang import Builder
from kivy.app import App

from kivy.uix.button import Button
from kivy.uix.label import Label

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.relativelayout import RelativeLayout

from kivy.uix.recycleview import RecycleView
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition

from kivy.properties import ListProperty, AliasProperty, StringProperty

from processing import Loader, Searcher

Builder.load_file('gui.kv')


class SidePanel(BoxLayout):
    pass


class AvailableIngrItem(Button):
    ingr_name = StringProperty()


class AvailableIngrRV(RecycleView):
    pass


class SelectedIngrItem(Button):
    ingr_name = StringProperty()


class SearchBox(RecycleView):
    pass


class SearchHeader(BoxLayout):
    pass


class SearchScreen(Screen):

    data = ListProperty()

    def get_data(self) -> list[dict]:
        return [{
            'ingr_name': item['ingr_name'],
            'selected': item['selected']
        }
            for item in self.data]

    def get_selected_ingredients(self) -> list[str]:
        return [{'ingr_name': item['ingr_name']}
                for item in self.get_data()
                if item['selected']]

    def get_available_ingredients(self) -> list[str]:
        return [{'ingr_name': item['ingr_name']}
                for item in self.get_data()
                if not item['selected']]

    data_selected = AliasProperty(get_selected_ingredients, bind=['data'])
    data_available = AliasProperty(get_available_ingredients, bind=['data'])


class Manager(ScreenManager):
    pass


class ResultsScreen(Screen):
    pass


class MainBoard(RelativeLayout):
    pass


class WtcApp(App):

    def __init__(self, loader: Loader, searcher: Searcher, **kwargs):
        self.loader = loader
        self.searcher = searcher
        super(WtcApp, self).__init__(**kwargs)

    def build(self):
        self.search_screen = SearchScreen(name='search_screen')

        self.transition = FadeTransition(duration=0.3)
        self.manager = Manager(transition=self.transition)
        self.manager.add_widget(self.search_screen)

        self.main_board = MainBoard()
        self.main_board.add_widget(self.manager)

        self.panel = SidePanel()

        root = BoxLayout()
        root.add_widget(self.panel)
        root.add_widget(self.main_board)

        self.load_ingredients(self.searcher.get_ingredients())

        return root

    def load_ingredients(self, ingr_list: list[str]):
        from random import choice
        self.search_screen.data = [{
            'ingr_name': ingr_name,
            'selected': choice((False, True))
        }
            for ingr_name in ingr_list]

    def refresh_search_data(self):
        data = self.search_screen.data
        self.search_screen.data = []
        self.search_screen.data = data


    def select_ingr(self, ingr_name: str):
        for index, item in enumerate(self.search_screen.data):
            if item['ingr_name'] == ingr_name:
                self.search_screen.data[index]['selected'] = True
                self.refresh_search_data()
                return

    def deselect_ingr(self, ingr_name: str):
        for index, item in enumerate(self.search_screen.data):
            if item['ingr_name'] == ingr_name:
                self.search_screen.data[index]['selected'] = False
                self.refresh_search_data()
                return


def start_app(loader: Loader, searcher: Searcher):
    WtcApp(loader, searcher).run()
