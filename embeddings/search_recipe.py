import os
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
supabase_client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def get_embedding(ingredients: str) -> List[float]:
    """Get embedding for ingredients string."""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=ingredients
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {str(e)}")
        raise

def search_recipes(
    ingredients: str,
    limit: int = 5,
    similarity_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Search for recipes based on ingredients.
    
    Args:
        ingredients: Comma-separated string of ingredients
        limit: Maximum number of results to return
        similarity_threshold: Minimum similarity score (0-1)
    """
    try:
        # Get embedding for the ingredients
        query_embedding = get_embedding(ingredients)
        
        # Search for similar recipes using HNSW index
        query = supabase_client.rpc(
            'match_recipes_by_ingredients',
            {
                'query_embedding': query_embedding,
                'match_threshold': similarity_threshold,
                'match_count': limit
            }
        ).execute()
        
        return query.data
    
    except Exception as e:
        print(f"Error searching recipes: {str(e)}")
        return []

def print_recipe_results(results: List[Dict[str, Any]], query: str) -> None:
    """Print search results in a formatted way."""
    print(f"\nSearch results for ingredients: {query}")
    print("-" * 50)
    
    if not results:
        print("No matching recipes found.")
        return
    
    for idx, result in enumerate(results, 1):
        print(f"\n{idx}. {result['title']}")
        print(f"Similarity Score: {result['similarity']:.2%}")
        print("Main Ingredients:", ", ".join(result['main_ingredients']))

def main():
    # Get ingredients from user input
    ingredients = input("\nEnter ingredients (comma-separated, e.g., 'telur, bawang, cili'): ").strip()
    
    if not ingredients:
        print("Please enter some ingredients to search for.")
        return
    
    try:
        # Search for recipes
        results = search_recipes(
            ingredients=ingredients,
            limit=3,
            similarity_threshold=0.5
        )
        
        # Print results
        print_recipe_results(results, ingredients)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()