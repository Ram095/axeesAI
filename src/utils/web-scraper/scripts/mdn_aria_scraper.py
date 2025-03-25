import sys
import os

# Add the root project directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))) 

from pages.base_page import BasePage
from pages.components.panel_component import PanelComponent
from concurrent.futures import ThreadPoolExecutor

#constants
MDN_URL = "https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA"
ARIA_OUTPUT_JSON_FILE = "aria_links.json"
BASE_MDN_URL = "https://developer.mozilla.org"
ARIA_FOLDER_PATH = "scraped_data/aria"

# Clean up the folder before scraping
BasePage.clear_folder(ARIA_FOLDER_PATH)  

def scrape_aria(page):
    """Scrape ARIA content from MDN Web Docs."""
    print(f"Opening {MDN_URL}")
    base_page = BasePage(page, MDN_URL)
    base_page.open()
    side_bar = PanelComponent(page)
    aria_links = side_bar.get_aria_links(BASE_MDN_URL)

    BasePage.save_json(aria_links, ARIA_OUTPUT_JSON_FILE)

    base_page.process_links_by_group(ARIA_FOLDER_PATH, ARIA_OUTPUT_JSON_FILE, "aria_techniques")

# Run the scraper
if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(BasePage.run_playwright, scrape_aria)