from concurrent.futures import ThreadPoolExecutor
import sys
import os

# Add the root project directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))) 
from pages.base_page import BasePage 
from pages.components.panel_component import PanelComponent

# Constants
WCAG_WEBSITE_URL = "http://localhost:3000"
WCAG_UNDERSTANDING_WEBSITE_URL = "http://localhost:3000/understanding/"
WCAG_TECHNIQUE_WEBSITE_URL = "http://localhost:3000/techniques/"
WCAG_LINKS_JSON_FILE = "wcag_links.json"
TECHNIQUES_LINKS_JSON_FILE = "technique_links.json"
CATEGORIZED_TECHNIQUES_JSON_FILE = "categorized_techniques.json"
SCRAPED_CONTENT_JSON_FILE = "scraped_content.json"
WCAG_FOLDER_PATH = "scraped_data/wcag"
WCAG_TECHNIQUE_FOLDER_PATH = "scraped_data/wcag_techniques"

# Clear WCAG folders before running the script
BasePage.clear_folder(WCAG_FOLDER_PATH)
BasePage.clear_folder(WCAG_TECHNIQUE_FOLDER_PATH)

def scrape_wcag(page):
    """Scrape WCAG Understanding content."""
    print(f"Opening {WCAG_UNDERSTANDING_WEBSITE_URL}")
    base_page = BasePage(page, WCAG_UNDERSTANDING_WEBSITE_URL)
    base_page.open()
    main_section = PanelComponent(page)
    main_section_links = main_section.get_all_parent_links(WCAG_UNDERSTANDING_WEBSITE_URL)

    BasePage.save_json({"main_section_links": main_section_links}, WCAG_LINKS_JSON_FILE)

    base_page.navigate_and_get_content_and_links(WCAG_FOLDER_PATH, WCAG_LINKS_JSON_FILE, TECHNIQUES_LINKS_JSON_FILE, WCAG_WEBSITE_URL, "principle")

def scrap_wcag_techniques(page):
    """Scrape WCAG Techniques categorized by technique type."""
    print(f"Opening {WCAG_TECHNIQUE_WEBSITE_URL}")
    base_page = BasePage(page, WCAG_TECHNIQUE_WEBSITE_URL)
    base_page.open()
    main_section = PanelComponent(page)
    techniques_data = main_section.get_all_technique_links(WCAG_TECHNIQUE_WEBSITE_URL)

    BasePage.save_json(techniques_data, CATEGORIZED_TECHNIQUES_JSON_FILE)

    base_page.process_links_by_group(WCAG_TECHNIQUE_FOLDER_PATH, CATEGORIZED_TECHNIQUES_JSON_FILE, "techniques", WCAG_TECHNIQUE_WEBSITE_URL)

# Run the scraper
if __name__ == "__main__":
    # Run both functions in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(BasePage.run_playwright, scrape_wcag)
        executor.submit(BasePage.run_playwright, scrap_wcag_techniques)