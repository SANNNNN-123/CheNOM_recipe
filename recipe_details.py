from playwright.async_api import async_playwright, TimeoutError
from tqdm import tqdm
import json
import time
from datetime import datetime
from urllib.parse import urljoin
import asyncio
import os
from typing import Optional, Dict

async def scrape_recipe_details(browser, url):
    """Scrape detailed information from a recipe page using JavaScript evaluation."""
    try:
        detail_page = await browser.new_page()
        await detail_page.goto(url, wait_until="domcontentloaded")
        await detail_page.wait_for_timeout(1000)
        print(f"Scraping recipe details for: {url}")
        
        # Use JavaScript to extract data from the recipe cards
        data = await detail_page.evaluate('''() => {
            const result = {};

            // Select all recipe-card elements
            const recipeCards = document.querySelectorAll('div.recipe-card');

            recipeCards.forEach(card => {
                const label = card.querySelector('p.text-sm.text-gray-500');
                const value = card.querySelector('p.font-semibold');

                if (label && value) {
                    const key = label.textContent.trim();
                    const val = value.textContent.trim();

                    // Match specific labels to their keys
                    if (key === "Masa Penyediaan") result.masa_penyediaan = val;
                    if (key === "Masa Memasak") result.masa_memasak = val;
                    if (key === "Jumlah Masa") result.jumlah_masa = val;
                    if (key === "Hidangan") result.hidangan = val;
                }
            });

            return result;
        }''')

        await detail_page.close()
        
        print(f"Extracted data: {data}")
        return data
    except Exception as e:
        print(f"\nError scraping recipe details: {str(e)}")
        return None



async def scrape_recipe_titles(url: str) -> Optional[list]:
    base_domain = "https://resepichenom.com"

    browser_options = {
            "headless": True,
            "args": [
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                "--no-first-run",
                "--no-sandbox",
                "--no-zygote",
                "--deterministic-fetch",
                "--disable-features=IsolateOrigins",
                "--disable-site-isolation-trials",
                "--disable-features=BlockInsecurePrivateNetworkRequests"
            ]
        }

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(**browser_options)
            print("Browser launched successfully.")

            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )

            await context.route("**/*analytics*.js", lambda route: route.abort())
            await context.route("**/*tracking*.js", lambda route: route.abort())
            await context.route("**/*advertisement*.js", lambda route: route.abort())
            
            page = await context.new_page()
            
            print(f"\nAccessing URL: {url}")
            await page.goto(url, wait_until="domcontentloaded")
            
            await page.wait_for_timeout(1000)
            await page.wait_for_selector("h2", timeout=200)
            
            titles = []
            title_elements = await page.query_selector_all("h2")
            title_elements = title_elements[:1]
            
            print(f"\nFound {len(title_elements)} recipes")
            
            for element in tqdm(title_elements, desc="Scraping recipes"):
                try:
                    title = await element.inner_text()
                    title = title.strip()
                    
                    # Get the parent article element
                    article = await element.evaluate('node => node.closest("article")')
                    
                    # Get the recipe URL
                    recipe_url = await element.evaluate('node => node.closest("a")?.href')
                    
                    # Get relative image URL and convert to absolute URL
                    img_relative = await page.evaluate('''(article) => {
                        const imgElement = article.querySelector('img');
                        return imgElement ? imgElement.getAttribute('src') : null;
                    }''', article) if article else None
                    
                    # Convert relative image URL to absolute URL
                    img_absolute = urljoin(base_domain, img_relative) if img_relative else None
                    
                    # Scrape detailed recipe information if URL is available
                    recipe_details = None
                    if recipe_url:
                        print(f"\nScraping details for: {title}")
                        recipe_details = await scrape_recipe_details(browser, recipe_url)
                    
                    recipe_data = {
                        "title": title,
                        "page_url": url,
                        "recipe_url": recipe_url,
                        "image_url": img_absolute,
                        "masa_penyediaan": recipe_details["masa_penyediaan"] if recipe_details else None,
                        "masa_memasak": recipe_details["masa_memasak"] if recipe_details else None,
                        "hidangan": recipe_details["hidangan"] if recipe_details else None,
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                    titles.append(recipe_data)
                    
                except Exception as e:
                    print(f"\nError processing recipe: {str(e)}")
                    continue
            
            await context.close()
            await browser.close()

            return titles

    except Exception as e:
        print(f"An error occurred: {e}")
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

async def main():
    start_time = time.time()
    
    base_url = "https://resepichenom.com/kategori"
    categories = ["ayam"] 
    
    all_recipes = []
    
    for category in categories:
        url = f"{base_url}/{category}"
        print(f"\nScraping category: {category}")
        print("=============================================================================================================")
        titles_data = await scrape_recipe_titles(url)
        if titles_data:
            all_recipes.extend(titles_data)
    
    save_titles(all_recipes)
    
    elapsed_time = time.time() - start_time
    print(f"\nScraping completed in {elapsed_time:.2f} seconds")
    print(f"Total recipes scraped: {len(all_recipes)}")

if __name__ == "__main__":
    asyncio.run(main())