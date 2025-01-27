import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from collections import Counter

def check_main_ingredients():
   data_dir = 'data/'
   
   for filename in os.listdir(data_dir):
       if filename.endswith('.json'):
           print("=" * 50)
           print(f"Checking {filename}")
           print("=" * 50)
           
           filepath = os.path.join(data_dir, filename)
           issues_found = False
           
           with open(filepath, 'r', encoding='utf-8') as f:
               try:
                   recipes = json.load(f)
                   
                   for recipe in recipes:
                       if 'main_ingredients' in recipe['details']:
                           ingredients = recipe['details']['main_ingredients']
                           
                           if any('\n' in i for i in ingredients):
                               print(f"Found newline in: {recipe['title']}")
                               print(ingredients)
                               print()
                               issues_found = True
                               
                           if any(len(i) > 50 for i in ingredients):
                               print(f"Found long text in: {recipe['title']}")
                               print(ingredients)
                               print()
                               issues_found = True
                               
                           if any(not i for i in ingredients):
                               print(f"Found empty value in: {recipe['title']}")
                               print(ingredients)
                               print()
                               issues_found = True
                   
                   if not issues_found:
                       print("No issues found\n")
                               
               except json.JSONDecodeError:
                   print(f"Error decoding {filename}\n")
               except Exception as e:
                   print(f"Error processing {filename}: {str(e)}\n")

def check_main_ingredients_issues(data_dir='data/'):
    """
    Check for various issues in main_ingredients field of recipe data
    """
    print("Starting main_ingredients validation check...")
    
    def validate_ingredient(ingredient):
        issues = []
        if not ingredient:  # Empty string
            issues.append("Empty value")
        if '\n' in ingredient:
            issues.append("Contains newline")
        if len(ingredient) > 50:
            issues.append("Too long (>50 chars)")
        if not isinstance(ingredient, str):
            issues.append(f"Not a string type (found {type(ingredient)})")
        if ingredient.startswith((' ', '\t')):
            issues.append("Starts with whitespace")
        if ingredient.endswith((' ', '\t')):
            issues.append("Ends with whitespace")
        # Check for weird characters, now including & as allowed
        weird_chars = [char for char in ingredient if not (char.isalnum() or char in ' -/(),.&')]
        if weird_chars:
            issues.append(f"Contains weird characters: {weird_chars}")
        return issues

    issues_found = False
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(data_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    recipes = json.load(f)
                
                print(f"\nChecking {filename}:")
                print("=" * 50)
                
                for recipe in recipes:
                    recipe_title = recipe.get('title', 'Unknown Title')
                    details = recipe.get('details', {})
                    
                    # Check if main_ingredients exists
                    if 'main_ingredients' not in details:
                        print(f"❌ Missing main_ingredients in recipe: {recipe_title}")
                        issues_found = True
                        continue
                    
                    main_ingredients = details['main_ingredients']
                    
                    # Check if main_ingredients is a list
                    if not isinstance(main_ingredients, list):
                        print(f"❌ main_ingredients is not a list in recipe: {recipe_title}")
                        print(f"Type found: {type(main_ingredients)}")
                        issues_found = True
                        continue
                    
                    # Check individual ingredients
                    for idx, ingredient in enumerate(main_ingredients):
                        issues = validate_ingredient(ingredient)
                        if issues:
                            print(f"❌ Issues in recipe '{recipe_title}', ingredient #{idx + 1}: {ingredient}")
                            for issue in issues:
                                print(f"   - {issue}")
                            issues_found = True
                    
                    # Check for duplicates
                    duplicates = [item for item, count in Counter(main_ingredients).items() if count > 1]
                    if duplicates:
                        print(f"❌ Duplicate ingredients found in recipe: {recipe_title}")
                        print(f"   Duplicates: {duplicates}")
                        issues_found = True
                
            except json.JSONDecodeError:
                print(f"❌ Error decoding JSON in {filename}")
                issues_found = True
            except Exception as e:
                print(f"❌ Error processing {filename}: {str(e)}")
                issues_found = True
    
    if not issues_found:
        print("\n✅ No issues found in main_ingredients across all files")
    else:
        print("\n❌ Issues were found in main_ingredients validation")
    
    return issues_found

# Run the check
has_issues = check_main_ingredients_issues()

# Check the result
if has_issues:
    print("Please fix the issues found in main_ingredients")
else:
    print("All main_ingredients are valid")