import logging
import webbrowser

from kivy.lang import Builder
from kivy.app import App
from kivy.clock import Clock

from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.relativelayout import RelativeLayout

from kivy.uix.recycleview import RecycleView
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition

from kivy.uix.behaviors import ButtonBehavior

from kivy.properties import (
    ListProperty, AliasProperty, StringProperty, NumericProperty)

from processing import Loader, Searcher
from definitions import Ingredient

Builder.load_file('gui.kv')


class ChooseFilePopup(Popup):
    file_kind = StringProperty()


class SettingsPopup(Popup):
    pass


class IngrReviewPopup(Popup):
    recipe_id = NumericProperty()
    recipe_title = StringProperty()
    text_with_unknown = StringProperty()

    def populate(self, data):
        self.recipe_id = data['recipe_id']
        self.recipe_title = data['recipe_title']
        self.text_with_unknown = data['text_with_unknown']

    def alert_wrong(self):
        saved_title = self.title
        saved_title_color = self.title_color
        self.title = 'Verification failure, try a different word.'
        self.title_color = (0.8, 0.2, 0.1)
        Clock.schedule_once(lambda dt: scheduled(
            saved_title, saved_title_color), 3)

        def scheduled(saved_title, saved_title_color):
            self.title = saved_title
            self.title_color = saved_title_color


class SidePanel(BoxLayout):
    num_pending_ingredients = NumericProperty()

    def __init__(self, **kwargs):
        super(SidePanel, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.on_num_pending_ingredients(
            self, self.num_pending_ingredients), 0)

    def on_num_pending_ingredients(self, instance, value):
        if value == 0:
            self.ids.review_button.disabled = True
        else:
            self.ids.review_button.disabled = False

    def update_load_label(self, num_new_recipes):
        if num_new_recipes == 0:
            self.ids.load_label.text = 'No new recipes were loaded.'
        else:
            self.ids.load_label.text = f'{num_new_recipes} '\
                'new recipes loaded.'

        Clock.schedule_once(lambda dt: self.clear_load_label(), 3)

    def clear_load_label(self):
        self.ids.load_label.text = 'Load recipes from file: '


class RecipeCard(ButtonBehavior, BoxLayout):
    recipe_id = NumericProperty()
    recipe_title = StringProperty()
    recipe_url = StringProperty()
    ingredients = ListProperty()


class ResultsScreen(Screen):
    data = ListProperty()


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

    def get_selected_ingredients(self) -> list[str]:
        return [{'ingr_name': item['ingr_name']}
                for item in self.data
                if item['selected']]

    def get_available_ingredients(self) -> list[str]:
        return [{'ingr_name': item['ingr_name']}
                for item in self.data
                if not item['selected']]

    data_selected = AliasProperty(get_selected_ingredients, bind=['data'])
    data_available = AliasProperty(get_available_ingredients, bind=['data'])


class Manager(ScreenManager):
    pass


class MainBoard(RelativeLayout):
    pass


class WtcApp(App):

    def __init__(self, loader: Loader, searcher: Searcher, **kwargs):
        super(WtcApp, self).__init__(**kwargs)
        self.loader = loader
        self.searcher = searcher

    def build(self):
        self.search_screen = SearchScreen(name='search_screen')
        self.results_screen = ResultsScreen(name='results_screen')

        self.transition = SlideTransition(duration=0.2, direction='left')
        self.manager = Manager(transition=self.transition)
        self.manager.add_widget(self.search_screen)
        self.manager.add_widget(self.results_screen)

        self.main_board = MainBoard()
        self.main_board.add_widget(self.manager)

        self.panel = SidePanel()
        self.update_num_pending_ingredients()
        # Clock.schedule_interval(
        #     lambda dt: self.update_num_pending_ingredients(), 2)

        root = BoxLayout()
        root.add_widget(self.panel)
        root.add_widget(self.main_board)

        self.load_ingredients()

        self.review_popup = IngrReviewPopup()

        return root

    def load_ingredients(self):
        ordered_ingr_names = sorted(ingr.name.capitalize()
                                    for ingr in self.searcher.get_ingredients())

        self.search_screen.data = [{
            'ingr_name': ingr_name,
            'selected': False
        }
            for ingr_name in ordered_ingr_names]
        logging.info(f'Loaded {len(self.search_screen.data)} ingredient/s.')

    def update_num_pending_ingredients(self):
        num = self.loader.num_pending_review
        self.panel.num_pending_ingredients = num

    def review_next_ingr(self):
        if self.loader.num_pending_review:
            id, title, _, text = self.loader.next_pending_review()
            self.review_popup.populate(
                {
                    'recipe_id': id,
                    'recipe_title': title,
                    'text_with_unknown': text
                }
            )
            self.review_popup.open()
            Clock.schedule_once(lambda dt: scheduled(), 0.1)

            def scheduled():
                self.review_popup.ids.ingredient_textinput.focus = True
        else:
            self.review_popup.dismiss()

    def save_ingr_review(self, recipe_id, text_with_unknown, ingr_name):
        try:
            self.loader.solve_unknown(
                recipe_id, text_with_unknown, Ingredient(ingr_name))
        except ValueError:
            self.review_popup.alert_wrong()

        self.load_ingredients()
        self.refresh_search_data()
        self.update_num_pending_ingredients()
        self.review_next_ingr()

    def delete_unknown(self, text_with_unknown):
        self.loader.delete_unknown(text_with_unknown)
        self.refresh_search_data()
        self.update_num_pending_ingredients()
        self.review_next_ingr()

    def load_recipes(self):
        successes, *_ = self.loader.load_recipes()
        self.panel.update_load_label(successes)
        self.update_num_pending_ingredients()

    def delete_recipe(self, recipe_id):
        self.loader.delete_recipe(recipe_id)
        for index, dict in enumerate(self.results_screen.data):
            if dict['recipe_id'] == recipe_id:
                del self.results_screen.data[index]
                return

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

    def search_recipes(self) -> dict:
        """Return dict of recipes containing currently selected ingredients."""
        ingr_included = [item['ingr_name']
                         for item in self.search_screen.get_selected_ingredients()]
        self.results_screen.data = [
            {
                'recipe_id': self.searcher.get_recipe_id(recipe.title, recipe.url),
                'recipe_title': recipe.title,
                'recipe_url': recipe.url,
                'ingredients': recipe.ingredients_known
            }
            for recipe in self.searcher.get_recipes(ingr_included)
        ]
        self.refresh_search_data()
        self.transition.direction = 'left'
        self.manager.current = 'results_screen'

    def go_back_from_results(self):
        self.transition.direction = 'right'
        self.manager.current = 'search_screen'

    def open_url(self, url):
        webbrowser.open(url)


def start_app(loader: Loader, searcher: Searcher):
    WtcApp(loader, searcher).run()
