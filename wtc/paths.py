import os

project_path = os.path.join(os.path.dirname(__file__), "../")

# Modify these if needed
ingredients_path = project_path + 'user_files/ingredients.txt'
recipes_path = project_path + 'user_files/recipes.csv'
database_path = project_path + 'assets/database/recipes.db'

os.makedirs(os.path.dirname(ingredients_path), exist_ok=True)

if not os.path.exists(ingredients_path):
    fp = open(ingredients_path, 'x')
    fp.close()


os.makedirs(os.path.dirname(recipes_path), exist_ok=True)

if not os.path.exists(recipes_path):
    fp = open(recipes_path, 'x')
    fp.close()
