import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

load_dotenv()
client = OpenAI(api_key=os.getenv('openai_api_key'))

def get_main_ingredients(ingredients_dict):
   all_ingredients = []
   for category in ingredients_dict.values():
       all_ingredients.extend(category)
   
   response = client.chat.completions.create(
       model="gpt-3.5-turbo",
       messages=[
           {
               "role": "system",
               "content": "Extract only the main ingredient names without quantities or measurements."
           },
           {
               "role": "user",
               "content": f"List main ingredients: {', '.join(all_ingredients)}"
           }
       ]
   )
   
   return response.choices[0].message.content.split(', ')

def process_recipe_file(input_filename):
   base_name = os.path.basename(input_filename)
   category_name = base_name.replace('recipe_titles_', '').replace('.json', '')
   output_filename = f"data/{category_name}.json"
   
   with open(input_filename, 'r') as file:
       recipes = json.load(file)

   for recipe in tqdm(recipes, desc="Processing recipes"):
       print(f"Processing: {recipe['title']}")
       recipe['details']['main_ingredients'] = get_main_ingredients(recipe['details']['ingredients'])

   with open(output_filename, 'w') as file:
       json.dump(recipes, file, indent=4)

process_recipe_file('data/recipe_titles_ayam_115.json')