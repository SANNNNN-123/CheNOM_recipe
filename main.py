from playwright.async_api import async_playwright, TimeoutError
from tqdm import tqdm
import json
import time
from datetime import datetime
from urllib.parse import urljoin
import asyncio
import os
from typing import Optional, Dict
import random

async def get_total_pages(page):
    """Extract the total number of pages from the pagination section."""
    try:
        # Find the span containing page information
        page_info = await page.query_selector("span.text-sm.text-gray-600")
        if page_info:
            text = await page_info.inner_text()
            # Extract total pages from text like "Halaman 1 / 10"
            total_pages = int(text.split('/')[-1].strip())
            return total_pages
    except Exception as e:
        print(f"Error getting total pages: {str(e)}")
        return 1
    return 1

async def scrape_recipe_details(browser, url):
    """Scrape detailed information from a recipe page using JavaScript evaluation."""
    try:
        # Create a new context for each request with random viewport
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            # Add additional headers
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
        )
        
        # Enable JavaScript
        await context.route("**/*", lambda route: route.continue_())
        
        detail_page = await context.new_page()
        
        # Add random delays between actions
        await detail_page.wait_for_timeout(random.randint(100, 500))
        
        # Emulate human-like behavior
        await detail_page.goto(url, wait_until="domcontentloaded")
        await detail_page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        await detail_page.wait_for_timeout(random.randint(1000, 2000))
        
        # Scroll down slowly like a human
        await detail_page.evaluate('''() => {
            return new Promise((resolve) => {
                let totalHeight = 0;
                const distance = 100;
                const timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if(totalHeight >= document.body.scrollHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 100);
            });
        }''')
        
        await detail_page.wait_for_timeout(random.randint(1000, 2000))

        # Extract data using more human-like behavior
        data = await detail_page.evaluate('''() => {
            const result = {};
            const base_domain = "https://resepichenom.com";
            
            //================ Extract Image URL ======================
            const imgElement = document.querySelector('img[alt]');
            if(imgElement) {
                let src = imgElement.getAttribute('src');
                
                if (src.startsWith('http')) {
                    result.image_url = src;
                } else {
                    result.image_url = base_domain + (src.startsWith('/') ? src : '/' + src);
                }
            } else {
                result.image_url = null;
            }
            
            // Extract timing and serving information
            const texts = ['Masa Penyediaan', 'Masa Memasak', 'Jumlah Masa', 'Hidangan'];
            texts.forEach(text => {
                const elements = Array.from(document.querySelectorAll('p')).filter(p => 
                    p.textContent.trim() === text
                );
                if(elements.length > 0) {
                    const valueElement = elements[0].parentElement.querySelector('p.font-semibold');
                    if(valueElement) {
                        result[text.toLowerCase().replace(' ', '_')] = valueElement.textContent.trim();
                    }
                }
            });
            
            //====================== Extract ingredients sections==============================================================
            result.ingredients = {};
            
            // Find the main ingredients container with title "Bahan-bahan"
            const ingredientsSection = Array.from(document.querySelectorAll('div.font-semibold')).find(
                div => div.textContent.trim() === 'Bahan-bahan'
            );
            
            if (ingredientsSection) {
                // Get the parent container that contains all ingredients
                const ingredientsContainer = ingredientsSection.closest('div.rounded-xl');
                
                if (ingredientsContainer) {
                    // Find all h4 headers within this container
                    const headers = Array.from(ingredientsContainer.querySelectorAll('h4.font-medium'));
                    
                    headers.forEach(header => {
                        const sectionName = header.textContent.trim();
                        let ingredientsList = [];
                        
                        // Find the ul element that follows this header
                        const ul = header.nextElementSibling;
                        if (ul && ul.tagName === 'UL') {
                            ingredientsList = Array.from(ul.querySelectorAll('li')).map(li => {
                                // Get the last span which contains the ingredient text
                                const span = li.querySelector('span:last-child');
                                return span ? span.textContent.trim() : li.textContent.trim();
                            }).filter(text => text);
                        }
                        
                        if (ingredientsList.length > 0) {
                            result.ingredients[sectionName] = ingredientsList;
                        }
                    });
                }
            }
            
            //====================== Extract cooking instructions==============================================================
            result.instructions = {};
            
            // Find the main instructions container with title "Cara Memasak"
            const instructionsSection = Array.from(document.querySelectorAll('div.font-semibold')).find(
                div => div.textContent.trim() === 'Cara Memasak'
            );
            
            if (instructionsSection) {
                // Get the parent container that contains all instructions
                const instructionsContainer = instructionsSection.closest('div.rounded-xl');
                
                if (instructionsContainer) {
                    // Find all h4 headers within this container
                    const headers = Array.from(instructionsContainer.querySelectorAll('h4.font-medium'));
                    
                    headers.forEach(header => {
                        const sectionName = header.textContent.trim();
                        let instructionsList = [];
                        
                        // Find the ol element that follows this header
                        const ol = header.nextElementSibling;
                        if (ol && ol.tagName === 'OL') {
                            instructionsList = Array.from(ol.querySelectorAll('li')).map(li => {
                                // Get the last span which contains the instruction text
                                const span = li.querySelector('span.flex-1');
                                return span ? span.textContent.trim() : li.textContent.trim();
                            }).filter(text => text);
                        }
                        
                        if (instructionsList.length > 0) {
                            result.instructions[sectionName] = instructionsList;
                        }
                    });
                }
            }
            
            //====================== Extract Tips & Guides==============================================================
            result.tips_and_guides = [];
            
            // Find the tips section with title "Petua & Panduan"
            const tipsSection = Array.from(document.querySelectorAll('div.text-2xl.font-bold')).find(
                div => div.textContent.includes('Petua & Panduan')
            );
            
            if (tipsSection) {
                // Get the parent container and find the ul element
                const tipsContainer = tipsSection.closest('div.rounded-xl');
                
                if (tipsContainer) {
                    const tipsList = tipsContainer.querySelector('ul');
                    if (tipsList) {
                        result.tips_and_guides = Array.from(tipsList.querySelectorAll('li')).map(li => {
                            // Get the text content from the span with class text-gray-700
                            const tipSpan = li.querySelector('span.text-gray-700');
                            return tipSpan ? tipSpan.textContent.trim() : li.textContent.trim();
                        }).filter(text => text);
                    }
                }
            }
            
            return result;
        }''')
        
        await detail_page.close()
        await context.close()
        
        return data
        
    except Exception as e:
        print(f"\nError scraping recipe details: {str(e)}")
        return None
    
async def scrape_recipe_titles(base_url: str) -> Optional[list]:
    base_domain = "https://resepichenom.com"
    all_titles = []

    browser_options = {
        "headless": True,
        "args": [
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-setuid-sandbox",
            "--no-first-run",
            "--no-sandbox",
            "--no-zygote",
            f"--window-size={random.randint(1024, 1920)},{random.randint(768, 1080)}",
            "--disable-notifications",
            "--disable-popup-blocking",
            "--disable-automation",
            "--disable-blink-features=AutomationControlled"
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
            
            # First, get the total number of pages
            print(f"\nAccessing initial URL: {base_url}")
            await page.goto(base_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(1000)
            
            total_pages = await get_total_pages(page)
            print(f"\nTotal pages found: {total_pages}")
            
            # Iterate through all pages
            for current_page in range(1, total_pages + 1):
                page_url = f"{base_url}?page={current_page}"
                print(f"\nProcessing page {current_page}/{total_pages}: {page_url}")
                
                try:
                    await page.goto(page_url, wait_until="domcontentloaded")
                    await page.wait_for_timeout(1000)
                    await page.wait_for_selector("h2", timeout=1000)
                    
                    title_elements = await page.query_selector_all("h2")
                    print(f"Found {len(title_elements)} recipes on page {current_page}")
                    
                    for element in tqdm(title_elements, desc=f"Scraping recipes from page {current_page}"):
                        try:
                            title = await element.inner_text()
                            title = title.strip()
                            
                            # Get the parent article element
                            article = await element.evaluate('node => node.closest("article")')
                            
                            # Get the recipe URL
                            recipe_url = await element.evaluate('node => node.closest("a")?.href')
                            
                            # Scrape detailed recipe information if URL is available
                            recipe_details = None
                            if recipe_url:
                                print(f"\nScraping details for: {title}")
                                for attempt in range(3):  # Add retries
                                    try:
                                        await page.wait_for_timeout(2000)  # Increased delay
                                        recipe_details = await scrape_recipe_details(browser, recipe_url)
                                        if recipe_details:
                                            break
                                        print(f"Attempt {attempt + 1}: Failed to get details, retrying...")
                                    except Exception as e:
                                        print(f"Error on attempt {attempt + 1}: {str(e)}")
                                        if attempt < 2:  # If not the last attempt
                                            await page.wait_for_timeout(2000)  # Wait before retry
                                        continue

                            recipe_data = {
                                "title": title,
                                "page_url": page_url,
                                "recipe_url": recipe_url,
                                "details": recipe_details if recipe_details else {}
                            }
                            
                            all_titles.append(recipe_data)
                            
                        except Exception as e:
                            print(f"\nError processing recipe: {str(e)}")
                            continue
                            
                    # Add a delay between pages to avoid overwhelming the server
                    await page.wait_for_timeout(random.randint(2000, 3000))
                    
                except Exception as e:
                    print(f"\nError processing page {current_page}: {str(e)}")
                    continue
            
            await context.close()
            await browser.close()

            return all_titles
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def save_titles(titles_data, category, filename="recipe_titles.json"):
    if titles_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # filename = f"recipe_titles_{category}_{len(titles_data)}_{timestamp}.json"
        filename = f"recipe_titles_{category}_{len(titles_data)}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(titles_data, f, indent=4, ensure_ascii=False)
        
        print(f"\nSuccessfully scraped {len(titles_data)} recipes!")
        print(f"Data saved to: {filename}")
        
    else:
        print("\nNo recipe data to save.")

async def main():
    start_time = time.time()
    
    base_url = "https://resepichenom.com/kategori"
    categories = ["roti","sarapan","sayur","seafood","snek-dan-makanan-ringan","sup","telur"] 
    
    all_recipes = []
    
    for category in categories:
        url = f"{base_url}/{category}"
        print(f"\nScraping category: {category}")
        print("=============================================================================================================")
        titles_data = await scrape_recipe_titles(url)
        if titles_data:
            all_recipes.extend(titles_data)
            save_titles(titles_data, category) 
    
    elapsed_time = time.time() - start_time
    print(f"\nScraping completed in {elapsed_time:.2f} seconds")
    print(f"Total recipes scraped: {len(all_recipes)}")


if __name__ == "__main__":
    asyncio.run(main())