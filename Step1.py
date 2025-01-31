from playwright.sync_api import sync_playwright, TimeoutError
import json
import time
from datetime import datetime

def get_recipe_urls(page, page_url):
    """Get all recipe URLs from the page using specific HTML structure"""
    recipe_links = []
    try:
        # Using evaluate to get all recipe links based on the HTML structure
        links = page.evaluate('''() => {
            const articles = document.querySelectorAll('article.fusion-post-grid');
            return Array.from(articles).map(article => {
                const linkElement = article.querySelector('h2.blog-shortcode-post-title a');
                if (linkElement) {
                    return {
                        ori_title: linkElement.textContent.trim(),
                        recipe_url: linkElement.href
                    };
                }
                return null;
            }).filter(item => item !== null);
        }''')
        
        # Add page_url and empty details structure to each recipe
        formatted_data = []
        for link in links:
            recipe_data = {
                "ori_title": link["ori_title"],
                "page_url": page_url,
                "recipe_url": link["recipe_url"],
                "details": {
                    "image_url": "",
                    "masa_penyediaan": "",
                    "masa_memasak": "",
                    "jumlah_masa": "",
                    "hidangan": "",
                    "ingredients": {},
                    "instructions": {},
                    "tips_and_guides": []
                }
            }
            formatted_data.append(recipe_data)
        
        return formatted_data
        
    except Exception as e:
        print(f"Error finding links: {str(e)}")
        return []

def scrape_recipes(url, max_retries=3):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        for attempt in range(max_retries):
            try:
                print(f"\nAccessing URL: {url}")
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(2000)  # Increased wait time
                
                # Get all recipe URLs
                recipe_links = get_recipe_urls(page, url)
                print(f"Found {len(recipe_links)} recipe links")
                
                if recipe_links:
                    return recipe_links
                
                return None
                
            except TimeoutError:
                if attempt < max_retries - 1:
                    print(f"\nTimeout occurred. Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(3)
                    continue
                else:
                    print("\nMax retries reached. Could not scrape recipes.")
                    return None
                    
            except Exception as e:
                print(f"\nError occurred: {str(e)}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    time.sleep(3)
                    continue
                return None

def save_recipes(recipes_data, filename="recipes.json"):
    if recipes_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recipes_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(recipes_data, f, indent=4, ensure_ascii=False)
        
        print(f"\nSuccessfully scraped {len(recipes_data)} recipes!")
        print(f"Data saved to: {filename}")
    else:
        print("\nNo recipes to save.")

def main():
    start_time = time.time()
    
    url = "https://myresipi.com/category/resipi/page/2/"
    print("\nScraping recipes from MyResipi.com")
    print("=============================================================================================================")
    
    recipes_data = scrape_recipes(url)
    save_recipes(recipes_data)
    
    elapsed_time = time.time() - start_time
    print(f"\nScraping completed in {elapsed_time:.2f} seconds")
    print(f"Total recipes scraped: {len(recipes_data) if recipes_data else 0}")

if __name__ == "__main__":
    main()