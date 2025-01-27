import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
from typing import Dict, Any, List
import time

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
supabase_client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def get_embedding(text: str) -> List[float]:
    """Get embedding from OpenAI API with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(1)  # Wait before retrying

def format_recipe_data(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Format recipe data for the recipes table."""
    return {
        'title': recipe['title'],
        'recipe_url': recipe['recipe_url'],
        'preparation_time': recipe['details'].get('masa_penyediaan'),
        'cooking_time': recipe['details'].get('masa_memasak'),
        'total_time': recipe['details'].get('jumlah_masa'),
        'servings': recipe['details'].get('hidangan'),
        'ingredients': recipe['details']['ingredients'],
        'instructions': recipe['details']['instructions'],
        'tips': recipe['details'].get('tips_and_guides', []),
        'image_url': recipe['details'].get('image_url')
    }

def create_ingredients_embedding(main_ingredients: List[str]) -> List[float]:
    """Create embedding for the main ingredients."""
    ingredients_text = ", ".join(main_ingredients)
    return get_embedding(ingredients_text)

def store_recipe(recipe: Dict[str, Any]) -> None:
    """Store a single recipe and its embeddings in Supabase."""
    try:
        # Format recipe data
        recipe_data = format_recipe_data(recipe)
        
        # Insert recipe and get the ID
        recipe_response = supabase_client.table('recipes').insert(recipe_data).execute()
        recipe_id = recipe_response.data[0]['id']
        
        # Get main ingredients and create embedding
        main_ingredients = recipe['details'].get('main_ingredients', [])
        embedding = create_ingredients_embedding(main_ingredients)
        
        # Store embedding data
        embedding_data = {
            'recipe_id': recipe_id,
            'main_ingredients': main_ingredients,
            'ingredients_embedding': embedding
        }
        
        supabase_client.table('recipe_embeddings').insert(embedding_data).execute()
        
        print(f"✓ Successfully stored recipe: {recipe['title']}")
        
    except Exception as e:
        print(f"✗ Error storing recipe {recipe['title']}: {str(e)}")

def main():
    # Read the JSON file
    try:
        with open('data/seafood_43.json', 'r', encoding='utf-8') as f:
            recipes = json.load(f)
        
        print(f"Found {len(recipes)} recipes to process")
        
        # Process each recipe
        for i, recipe in enumerate(recipes, 1):
            print(f"\nProcessing recipe {i}/{len(recipes)}")
            store_recipe(recipe)
            time.sleep(0.1)  # Small delay to avoid rate limits
        
        print("\nFinished processing all recipes")
        
    except FileNotFoundError:
        print("Error: telur_11.json file not found")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in telur_11.json")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()