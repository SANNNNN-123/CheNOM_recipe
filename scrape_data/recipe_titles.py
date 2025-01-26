from playwright.sync_api import sync_playwright, TimeoutError
from tqdm import tqdm
import json
import time
from datetime import datetime
from urllib.parse import urljoin

def scrape_recipe_titles(url, max_retries=3):
    base_domain = "https://resepichenom.com"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1'
        })

        for attempt in range(max_retries):
            try:
                print(f"\nAccessing URL: {url}")
                page.goto(url, wait_until="networkidle")
                
                page.wait_for_timeout(1000)
                page.wait_for_selector("h2", timeout=200)
                
                titles = []
                title_elements = page.query_selector_all("h2")
                
                print(f"\nFound {len(title_elements)} recipes")
                
                for element in tqdm(title_elements, desc="Scraping recipes"):
                    try:
                        title = element.inner_text().strip()
                        
                        # Get the parent article element
                        article = element.evaluate('node => node.closest("article")')
                        
                        # Get the recipe URL
                        link = element.evaluate('node => node.closest("a")?.href')
                        
                        # Get relative image URL and convert to absolute URL
                        img_relative = page.evaluate('''(article) => {
                            const imgElement = article.querySelector('img');
                            return imgElement ? imgElement.getAttribute('src') : null;
                        }''', article) if article else None
                        
                        # Convert relative image URL to absolute URL
                        img_absolute = urljoin(base_domain, img_relative) if img_relative else None
                        
                        recipe_data = {
                            "title": title,
                            "page_url": url,
                            "recipe_url": link if link else None,
                            "image_url": img_absolute,
                            "scraped_at": datetime.now().isoformat()
                        }
                        
                        titles.append(recipe_data)
                        
                    except Exception as e:
                        print(f"\nError processing recipe: {str(e)}")
                        continue
                
                return titles
                
            except TimeoutError:
                if attempt < max_retries - 1:
                    print(f"\nTimeout occurred. Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(3)
                    continue
                else:
                    print("\nMax retries reached. Could not scrape titles.")
                    return None
                    
            except Exception as e:
                print(f"\nError occurred: {str(e)}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    time.sleep(3)
                    continue
                return None
            
        return None

def save_titles(titles_data, filename="recipe_titles.json"):
    if titles_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recipe_titles_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(titles_data, f, indent=4, ensure_ascii=False)
        
        print(f"\nSuccessfully scraped {len(titles_data)} recipes!")
        print(f"Data saved to: {filename}")
        
    else:
        print("\nNo recipe data to save.")

def main():
    start_time = time.time()
    
    base_url = "https://resepichenom.com/kategori"
    categories = ["ayam"] 
    
    all_recipes = []
    
    for category in categories:
        url = f"{base_url}/{category}"
        print(f"\nScraping category: {category}")
        print("=============================================================================================================")
        titles_data = scrape_recipe_titles(url)
        if titles_data:
            all_recipes.extend(titles_data)
    
    save_titles(all_recipes)
    
    elapsed_time = time.time() - start_time
    print(f"\nScraping completed in {elapsed_time:.2f} seconds")
    print(f"Total recipes scraped: {len(all_recipes)}")

if __name__ == "__main__":
    main()