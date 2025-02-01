from playwright.sync_api import sync_playwright, TimeoutError
import json
import time
import random
from datetime import datetime
from tqdm import tqdm
import argparse
import os

def scrape_recipe_details(context, recipe_url):
    """Scrape details for a single recipe URL using human-like behavior"""
    try:
        # Create a new page with the existing context
        page = context.new_page()
        print(f"\nScraping details from: {recipe_url}")
        
        # Add reduced random delay before navigation
        page.wait_for_timeout(random.randint(200, 500))
        
        # Navigate to the page with human-like behavior
        page.goto(recipe_url, wait_until="domcontentloaded")
        page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        page.wait_for_timeout(random.randint(200, 500))
        
        # Scroll down slowly like a human (with reduced interval)
        page.evaluate('''() => {
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
                }, 50);
            });
        }''')
        
        page.wait_for_timeout(random.randint(200, 500))

        # Extract all data using JavaScript evaluation
        details = page.evaluate('''() => {
            const result = {};
            const contentDiv = document.querySelector('div.fusion-content-tb');
            if (!contentDiv) return result;

            // Get the title
            const titleElement = contentDiv.querySelector('h3');
            result.title = titleElement ? titleElement.textContent.trim() : '';

            // Get the image URL from the p tag after h3 title
            const h3Element = contentDiv.querySelector('h3');
            if (h3Element) {
                const pElement = h3Element.nextElementSibling;
                if (pElement && pElement.tagName === 'P') {
                    const imgElement = pElement.querySelector('img[srcset]');
                    if (imgElement) {
                        const srcset = imgElement.getAttribute('srcset');
                        // Get the highest resolution image URL (last one in srcset)
                        const urls = srcset.split(',').map(s => s.trim().split(' ')[0]);
                        result.image_url = urls[urls.length - 1];
                    }
                }
            }

            // Get ingredients
            result.ingredients = {};
            let currentElement = contentDiv.querySelector('h3').nextElementSibling;
            while (currentElement) {
                // Stop if we reach the instructions section
                if (currentElement.tagName === 'P' && currentElement.querySelector('strong') && 
                    currentElement.querySelector('strong').textContent.trim().toLowerCase().startsWith('cara')) {
                    break;
                }

                // Check if the current element is a strong tag with "Bahan-bahan"
                if (currentElement.tagName === 'P' && currentElement.querySelector('strong')) {
                    const header = currentElement.querySelector('strong').textContent.trim();
                    if (header.toLowerCase().includes('bahan')) {
                        const ingredients = [];
                        let nextElement = currentElement.nextElementSibling;

                        // Collect all ingredients from ul/ol lists
                        while (nextElement && (nextElement.tagName === 'UL' || nextElement.tagName === 'OL')) {
                            ingredients.push(...Array.from(nextElement.querySelectorAll('li')).map(
                                li => li.textContent.trim()
                            ));
                            nextElement = nextElement.nextElementSibling;
                        }

                        // Add ingredients to the result
                        if (ingredients.length > 0) {
                            result.ingredients[header] = ingredients;
                        }
                    }
                }

                currentElement = currentElement.nextElementSibling;
            }

            // Get instructions
            const instructions = [];
            const instructionsHeaders = Array.from(contentDiv.querySelectorAll('p strong')).filter(
                el => el.textContent.trim().toLowerCase().startsWith('cara')
            );
            if (instructionsHeaders.length > 0) {
                for (const header of instructionsHeaders) {
                    let currentElement = header.closest('p').nextElementSibling;
                    while (currentElement) {
                        if (currentElement.tagName === 'OL' || currentElement.tagName === 'UL') {
                            // Append all steps from the list
                            instructions.push(...Array.from(currentElement.querySelectorAll('li')).map(
                                li => li.textContent.trim()
                            ));
                        } else if (currentElement.tagName === 'P' && /\\d+\\./.test(currentElement.textContent.trim())) {
                            // Append steps from p tags containing numbers (e.g., "1.", "2.")
                            instructions.push(currentElement.textContent.trim());
                        }
                        currentElement = currentElement.nextElementSibling;
                    }
                }
            }

            // Case 2: Instructions in p tags containing numbers (e.g., "1.", "2.")
            if (instructions.length === 0) {
                const instructionElements = contentDiv.querySelectorAll('p');
                instructionElements.forEach(el => {
                    const text = el.textContent.trim();
                    if (/\\d+\\./.test(text)) {  // Check if the text contains a number followed by a dot
                        instructions.push(text);
                    }
                });
            }

            result.instructions = instructions;

            return result;
        }''')

        # Update the recipe data with all scraped details
        recipe_data = {
            "recipe_url": recipe_url,
            "details": details
        }
        
        page.close()
        return recipe_data
        
    except Exception as e:
        print(f"Error scraping recipe details: {str(e)}")
        return {"recipe_url": recipe_url, "details": {}}

def scrape_single_recipe(url, max_retries=3):
    """Scrape a single recipe from a given URL"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Upgrade-Insecure-Requests': '1',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
        )

        recipe_data = None
        for attempt in range(max_retries):
            try:
                recipe_data = scrape_recipe_details(context, url)
                break
            except TimeoutError:
                if attempt < max_retries - 1:
                    print(f"\nTimeout occurred. Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(3)
                    continue
                else:
                    print("\nMax retries reached. Could not scrape recipe.")
                    recipe_data = {"recipe_url": url, "details": {}}
            except Exception as e:
                print(f"\nError occurred: {str(e)}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    time.sleep(3)
                    continue
                recipe_data = {"recipe_url": url, "details": {}}

        context.close()
        browser.close()
        return recipe_data

def save_recipe(recipe_data, filename):
    """Save recipe data to a file, appending if the file exists"""
    if recipe_data:
        existing_data = []
        
        # If file exists, load existing data
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
            except json.JSONDecodeError:
                print(f"Warning: Existing file {filename} is not valid JSON. Creating new file.")
                existing_data = []
            
        # Append new recipe data
        if isinstance(recipe_data, list):
            existing_data.extend(recipe_data)
        else:
            existing_data.append(recipe_data)
        
        # Save combined data
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=4, ensure_ascii=False)
        
        print(f"\nSuccessfully scraped recipe!")
        print(f"Data {'appended to' if os.path.exists(filename) else 'saved to'}: {filename}")
    else:
        print("\nNo recipe to save.")

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Scrape recipe details from MyResipi.com")
    parser.add_argument("url", help="URL of the recipe to scrape")
    parser.add_argument("filename", nargs="?", default=None, help="Optional: Name of the file to save/append the recipe data")
    args = parser.parse_args()

    # If no filename is provided, create one with timestamp
    if args.filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.filename = f"recipe_{timestamp}.json"

    start_time = time.time()
    
    print("\nScraping recipe from MyResipi.com")
    print("=============================================================================================================")
    
    # Scrape the single recipe
    recipe_data = scrape_single_recipe(args.url)
    save_recipe(recipe_data, args.filename)
    
    elapsed_time = time.time() - start_time
    print(f"\nScraping completed in {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()