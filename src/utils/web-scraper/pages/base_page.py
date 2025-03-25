import sys
import os
import json
import shutil
from playwright.sync_api import Page, sync_playwright, Error, TimeoutError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pages.components.panel_component import PanelComponent

class BasePage:
    """BasePage class provides a set of methods to interact with the web page and extract content."""
    
    def __init__(self, page: Page, url: str):
        """Constructor to initialize the Playwright Page instance and URL."""
        self.page = page
        self.url = url

    def open(self):
        """Function to open the specified URL."""
        self.page.goto(self.url)

    def navigate_and_click_buttons(self, input_json_file, output_json_file):
        """Iterate through sidebar_links.json, click on each link, and interact with buttons."""
        
        # Load sidebar links from JSON
        with open(input_json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        sidebar_links = data.get("sidebar_links", [])

        for entry in sidebar_links:
            link = entry["link"]
            text = entry["text"]
            title = entry["title"]
            
            print(f"Navigating to: {link}")
            self.page.goto(link)  # Navigate to the page
            
            # Wait for the page to load
            self.page.wait_for_load_state("load")
            
            # Find all buttons with an href attribute but exclude buttons with "Close" text
            button_locator = f"{text} button:not(:has-text('Close'))"
            buttons = self.page.locator(button_locator).all()
            
            print(f"Found {len(buttons)} buttons on {link}")
            
            for button in buttons:
                    print(f"Clicking button: {button.inner_text()}")
                    button.click()
                    self.page.wait_for_timeout(1000)  # Adjust as needed
                    panel = PanelComponent(self.page)
                    titles = panel.extract_panel_links(text, title, output_json_file)
                    print(f"The list of titles are {titles}")
        return titles
    
    def extract_page_content(self, title: str, main_heading: str, url: str, output_json_file: str):
        """Scrape Description, Examples, and Procedure from a page and save in JSON format."""
        self.url = url
        self.open()
        # Extract the main heading (guideline title)
        second_main_heading = self.page.locator("h1").first.inner_text().strip()
        # Extract Description
        description_locator = self.page.locator("#description")
        description = description_locator.text_content().strip() if description_locator.count() > 0 else "No description available"
        # Extract Procedure
        procedure_locator = self.page.locator("#procedure")
        procedure = procedure_locator.text_content().strip() if procedure_locator.count() > 0 else "No procedure available"
        # Extract Examples
        examples_data = []
        examples_section = self.page.locator("#examples")
        if examples_section.count() > 0:
            example_headers = self.page.locator("#examples h3 | #examples li").all()  # Get all example subheaders
            for example in example_headers:
                example_title = example.inner_text().strip()
                example_content = example.evaluate("node => node.nextElementSibling?.innerText") or "No details available"
                examples_data.append({example_title: example_content.strip()})
        # Structure the extracted content
        extracted_data = {
            title: [{
                main_heading: {
                    "Description": description,
                    "Examples": examples_data if examples_data else "No examples available",
                    "Procedure": procedure
                }
            }]
        }
        # Load existing data (if any) to append new data
        try:
            with open(output_json_file, "r", encoding="utf-8") as json_file:
                existing_data = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = {}
        # Merge new data into existing JSON
        if title in existing_data:
            existing_data[title].append(*extracted_data[title])
        else:
            existing_data.update(extracted_data)
        # Save data to JSON file
        with open(output_json_file, "w", encoding="utf-8") as json_file:
            json.dump(existing_data, json_file, indent=4, ensure_ascii=False)
        print(f"Data saved to {output_json_file}")
        return main_heading

    def navigate_and_get_content_and_links(self, folder_path, input_json_file, output_json_file, base_url, mode):
        """Iterate through main_section_links.json, click on each link, and fetch the content."""
        
        # Load sidebar links from JSON
        with open(input_json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        main_section_links = data.get("main_section_links", [])

        for entry in main_section_links:
            link = entry["link"]
            title = entry["title"]
            print(f"Navigating to: {link}")
            self.url = link
            self.open()
            # Wait for the page to load
            self.page.wait_for_load_state("load")
            panel = PanelComponent(self.page)
            panel.extract_panel_content(title, folder_path, output_json_file,mode, base_url)

    def process_links_by_group(self, folder_path, input_json_file, mode, base_url = None):
        """
        Processes links by group from a JSON file and performs actions on each link.
        Args:
            input_json_file (str): The path to the input JSON file containing groups of links.
            base_url (str): The base URL to be used for processing links.
            mode (str): The mode in which the links should be processed.
        Raises:
            FileNotFoundError: If the input JSON file does not exist.
            json.JSONDecodeError: If the input JSON file is not a valid JSON.
        Example:
            input_json_file = "links.json"
            base_url = "https://example.com"
            mode = "default"
            process_links_by_group(input_json_file, base_url, mode)
        """
        with open(input_json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        for group in data:
            group_name = group.get(mode)
            links = group.get("links", [])

            for link in links:
                url = link.get("url")
                text = link.get("text")
                print(f"Navigating to: {url}")
                self.url = url
                self.open()
                self.page.wait_for_load_state("load")
                panel = PanelComponent(self.page)
                panel.extract_panel_content(text, folder_path, group_name + ".json", mode, base_url)

    @staticmethod
    def run_playwright(task_function, *args):
        """Handles Playwright execution, browser setup, and teardown."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                task_function(page, *args)
            except (Error, TimeoutError) as e:
                print(f"Error while executing {task_function.__name__}: {e}")
            finally:
                browser.close()

    @staticmethod
    def save_json(data, output_file):
        """Save data to a JSON file."""
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    @staticmethod
    def clear_folder(folder_path):
        """Deletes all files and subdirectories in the specified folder."""
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)  # Delete file or symlink
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  # Delete folder and its contents
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")
