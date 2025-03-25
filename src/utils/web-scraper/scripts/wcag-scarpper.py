from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import csv
import os
import json
from datetime import datetime
import random
import time
import math

BASE_URL = "https://www.w3.org/WAI/WCAG22/quickref/"
OUTPUT_DIR = "wcag_data"

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def save_progress(section_id, data):
    ensure_output_dir()
    filename = f"{OUTPUT_DIR}/wcag_{section_id}_{datetime.now().strftime('%Y%m%d')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved section {section_id} to {filename}")

def combine_results():
    all_results = []
    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(OUTPUT_DIR, filename), 'r', encoding='utf-8') as f:
                all_results.extend(json.load(f))
    
    # Save combined results to CSV
    with open(f"{OUTPUT_DIR}/wcag_scraped_data.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["section", "heading", "description", "techniques", "sub_links"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_results:
            writer.writerow(row)

def human_like_mouse_movement(page):
    # Generate random destination coordinates
    x = random.randint(100, 800)
    y = random.randint(100, 600)
    
    # Create multiple points for curved movement
    steps = random.randint(10, 20)
    for i in range(steps):
        # Add some randomness to the path
        dx = int(x * (i/steps) + random.randint(-20, 20))
        dy = int(y * (i/steps) + random.randint(-20, 20))
        page.mouse.move(dx, dy)
        page.wait_for_timeout(random.uniform(0.1, 0.3)*1000)

def random_scroll(page):
    # Random scroll distance
    scroll_distance = random.randint(100, 500)
    # Random scroll direction (mostly down, sometimes up)
    direction = 1 if random.random() < 0.8 else -1
    
    steps = random.randint(5, 15)
    for i in range(steps):
        distance = int((scroll_distance / steps) + random.randint(-10, 10))
        page.mouse.wheel(0, direction * distance)
        page.wait_for_timeout(random.uniform(0.1, 0.3)*1000)

def perform_random_actions(page, min_actions=1, max_actions=5):
    """Performs a random number of random actions in random order with random delays between them"""
    actions = [
        lambda: human_like_mouse_movement(page),
        lambda: random_scroll(page),
        lambda: page.wait_for_timeout(random.uniform(0.2, 1.0)*1000),  # Quick pause
        lambda: None  # Sometimes do nothing
    ]
    
    # Randomly decide how many actions to perform
    num_actions = random.randint(min_actions, max_actions)
    
    # Perform random actions with random delays
    for _ in range(num_actions):
        # 20% chance to add an extra random delay
        if random.random() < 0.2:
            time.sleep(random.uniform(0.1, 0.5))
            
        # Randomly choose and execute an action
        random.choice(actions)()

def scrape_wcag():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set headless=True for background execution
        page = browser.new_page()
        
        # Apply stealth mode to the page
        stealth_sync(page)
        
        # Set common browser parameters to appear more human-like
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        })

        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")  # Ensure page is fully loaded

        # Step 1: Collect all sidebar links that do not have child <li>
        links = page.locator("aside li:not(:has(li)) a").all()
        
        results = []

        for link in links:
            href = link.get_attribute("href")
            if href and href.startswith("#"):  # Only process internal links
                section_id = href.lstrip("#")
                
                # Skip if already processed
                if any(f for f in os.listdir(OUTPUT_DIR) if section_id in f):
                    print(f"Skipping already processed section: {section_id}")
                    continue

                section_results = []
                perform_random_actions(page)
                link.click()
                page.wait_for_load_state("networkidle") 
                perform_random_actions(page, 2, 4)

                # Step 2: Expand collapsible section
                button_selector = f"article[id={section_id}] button[data-expanded=false]"
                if page.locator(button_selector).count() > 0:
                    perform_random_actions(page, 1, 3)
                    page.locator(button_selector).click()

                # Step 3: Extract Data
                heading = page.locator(f"article[id={section_id}] h4").text_content() or "N/A"
                description = page.locator(f"article[id={section_id}] .sc-text p").first.text_content() or "N/A"
                techniques = page.locator(f"article[id={section_id}] div[id*=techniques]").text_content() or "N/A"
                
                # Step 4: Capture additional links
                sub_links = page.locator(f"article[id={section_id}] div[id*=techniques] li a").all()
                sub_links_data = [{"text": a.text_content(), "href": a.get_attribute("href")} for a in sub_links]

                section_results.append({
                    "section": section_id,
                    "heading": heading.strip(),
                    "description": description.strip(),
                    "techniques": techniques.strip(),
                    "sub_links": sub_links_data
                })

                # Step 5: Process each sub-link
                for sub_link in sub_links:                    
                    sub_link.click()
                    page.wait_for_load_state("networkidle")
                    perform_random_actions(page, 1, 4)
                    sub_link_text = page.locator("h1").text_content() or "N/A"                  
                    technique = page.locator("#technique").text_content() or "N/A"
                    description = page.locator("#description").text_content() or "N/A"
                    examples = page.locator("#examples").text_content() or "N/A"
                    section_results.append({
                        "section": section_id,
                        "heading": sub_link_text,
                        "technique": technique.strip(),
                        "description": description.strip(),
                        "examples": examples.strip(),
                    })
                    page.go_back()
                    page.wait_for_timeout(1000)
                    perform_random_actions(page, 2, 4)
                    button_selector = f"article[id={section_id}] button[data-expanded=false]"
                    if page.locator(button_selector).count() > 0:                        
                        page.locator(button_selector).click()                    
                    page.wait_for_timeout(500)

                # After processing main section and sub-links
                save_progress(section_id, section_results)

        print("Combining all results...")
        combine_results()
        print("✅ All data combined and saved to wcag_scraped_data.csv")
        browser.close()

if __name__ == "__main__":
    ensure_output_dir()
    scrape_wcag()
