# what-to-cook

## Description

What to Cook is a small project meant to help me get ideas for what to cook next.

## Usage
To use it, you upload recipes to the 'recipes.csv' file located in 'project_folder/user_files/', launch the app, and click on 'Load recipes'.
![image](https://user-images.githubusercontent.com/98750668/169665068-806be4be-06b4-44a5-90d2-722b9659376a.png)

Once it finishes loading them, the 'Review ingredients' button will unlock. If you click on the button a pop-up will be shown, enabling you to extract each ingredient manually. The system groups words by their stem (_carota_ and _carote_ are both the same since their stem is _carot_), and for every ingredient you extract, it looks at the remaining unknowns to check if it can solve them with the word you provided.
![image](https://user-images.githubusercontent.com/98750668/169665077-25fa2480-1a0f-45bd-b238-2558599d3168.png)
![image](https://user-images.githubusercontent.com/98750668/169665082-e2a277bb-7d86-4a96-82c4-bb12682bc54d.png)

Once a recipe has all of its ingredients solved (either extracted or deleted), it will be available to be part of the search results.
To execute a search, select the ingredients you'd like the recipes to contain and then click search.
![image](https://user-images.githubusercontent.com/98750668/169665228-18b3568d-eb9e-48ce-965a-31720beff9c6.png)
![image](https://user-images.githubusercontent.com/98750668/169665235-ea83a28d-847f-415b-9cfa-b111a4a36a22.png)

## Limitations
Since the app's natural language processing capabilities are very limited, there is a frequent error it makes when automatically solving unknowns after you manually extracted an ingredient. If you extract _sale_ for example, and then another recipe contained _burro salato_ as an unknown, the app would extract _sale_ from salato, mistakingly categorizing the recipe.
Another limitation the system currently has is its practically lacking editing capabilities. As its stands, you can't edit an ingredient that the system mistakenly categorized, delete it, or take many similar actions.
The system takes the stems from Italian only since that's the language the site I use it for is in. It would be easy to support English or other Indo-European languages.
Shall you need to clear the database, please delete 'recipes.db' located at 'project_folder/assets/database/'.
