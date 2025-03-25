import json
import os
import re
from playwright.sync_api import Page


class PanelComponent:
    """PanelComponent class provides methods to extract links and content from a panel on a page."""

    def __init__(self, page: Page):
        self.page = page

    def extract_panel_links(self, text: str, title: str, output_json_file: str):
        """Extracts links from the panel and saves them to a JSON file."""
        page_links = self.page.locator(f"{text} .panel li a").all()
        extracted_links = [
            {
                "url": link.get_attribute("href"),
                "text": link.inner_text().strip()
            }
            for link in page_links if link.get_attribute("href")
        ]

        # Load existing data if the file exists
        if os.path.exists(output_json_file):
            with open(output_json_file, "r", encoding="utf-8") as file:
                all_links_data = json.load(file)
        else:
            all_links_data = {}

        # Append new data under the formatted title
        all_links_data[title] = extracted_links

        # Save updated data to JSON file
        with open(output_json_file, "w", encoding="utf-8") as output_file:
            json.dump(all_links_data, output_file, indent=4)

        print(f"Appended extracted links under '{title}' in {output_json_file}")
        return list(all_links_data.keys())

    def extract_panel_content(self, title: str, folder_path: str, output_json_file: str, mode: str, base_url: str = None):
        """
        Scrape content from the page and save it in a JSON file.

        :param title: Title of the page
        :param output_json_file: JSON file where data will be saved
        :param base_url: Base URL to construct full links
        :param mode: Type of sections to scrape ("principle", "techniques", or "aria_techniques")
        """
        section_mapping = {
            "principle": ["brief", "success-criterion", "intent", "techniques"],
            "techniques": ["technique", "description", "examples", "related"],
            "aria_techniques": ["description", "structural_roles_with_html_equivalents"]
        }

        all_sections = section_mapping.get(mode, [])
        page_data = {"principle" if mode == "principle" else "technique": title}

        content_links = self.get_page_content_links()
        available_sections = {link.split("#")[-1] for link in content_links}  # Extract section IDs

        for section in all_sections:
            if section not in available_sections:
                page_data[section] = None
                continue

            section_locator = self.page.locator(f"main #{section}")
            description = self._extract_description(section_locator, mode)

            if section in ["techniques", "related"]:
                links = self._extract_links(section_locator, base_url)
                page_data[section] = {"links": links} if section == "related" else {"description": description, "links": links}

            elif section == "technique":
                page_data[section] = {
                    "name": self._get_text("#main h1 span").replace("Technique ", ""),
                    "aria_title": self._get_text("#main h1").replace(self._get_text("#main h1 span"), "").strip(),
                    "description": description
                }

            elif mode == "aria_techniques" and section in ["description", "structural_roles_with_html_equivalents"]:
                page_data[section] = {
                    "name": self._get_text(".main-content h1"),
                    "aria_title": self._get_text(".main-page-content > div.section-content"),
                    "description": description
                }
            else:
                page_data[section] = {"description": description}

        self._save_to_json(folder_path, output_json_file, page_data)

    def get_all_parent_links(self, base_url: str):
        """Get all links of parent elements only."""
        parent_links = self.page.locator("#main").locator("section li:not(:has(li)) a").all()
        return [
            {
                "link": f"{base_url}{link.get_attribute('href')}",
                "text": link.get_attribute('href'),
                "title": re.sub(r"[()\s-]+", "_", re.sub(r"^\d+\.\d+\.\d+\s*", "", link.inner_text().strip().lower())).strip("_")
            }
            for link in parent_links
        ]
    
    def get_all_technique_links(self, url: str):
        """Extracts categorized techniques and their links."""
        techniques_list = self.get_page_content_links()  # Get techniques like #aria
        techniques_data = []
        for technique in techniques_list:
            if technique == "#changelog":
                continue
            technique_name = technique.lstrip("#")  # Remove '#' prefix
            locator = f"xpath=//main[@id='main']/h2[@id='{technique_name}']/following-sibling::*[1]/li/a"
            links = self.page.locator(locator).all()
            extracted_links  = [
                {
                    "url": f"{url}{link.get_attribute('href')}",
                    "text": link.inner_text().strip()
                }
                for link in links if link.get_attribute("href")
            ]
            if extracted_links:  # Only add if there are links found
                techniques_data.append({
                    "techniques": technique_name,
                    "links": extracted_links
                })       
        return techniques_data

    def _extract_description(self, section_locator, mode):
        """Extracts description text from a given section locator."""
        if mode == "aria_techniques":
            return self._extract_aria_techniques_description()
        return section_locator.inner_text().strip() if section_locator.count() > 0 else "No text found"

    def _extract_aria_techniques_description(self):
        """Extracts description text for 'aria_techniques' mode, ignoring 'see_also' sections."""
        sections = self.page.query_selector_all("main section")
        return "\n\n".join(s.inner_text().strip() for s in sections if s.get_attribute("aria-labelledby") != "see_also")

    def _extract_links(self, section_locator, base_url):
        """Extracts hyperlinks from a section."""
        links = []
        for link in section_locator.locator("a").all():
            href = link.get_attribute("href")
            if href:
                href = href.lstrip('.')  # Trim leading ".." if present
                clean_url = f"{base_url}{href}" if href.startswith("/") else href
                links.append({"url": clean_url, "text": link.inner_text().strip()})
        return links
    
    def get_page_content_links(self):
        """Retrieve all page content links from the sidebar."""
        content_links = self.page.locator(".sidebar ul li a").all()
        return [link.get_attribute("href") for link in content_links if link.get_attribute("href")]
    
    def get_aria_links(self, base_url: str):
        """Retrieve all categorized ARIA links from the sidebar."""
        root_section = self.page.locator(".sidebar")
        aria_section_toggles = root_section.locator("xpath=//li[.//a[text()='ARIA']]//following-sibling::li[@class='toggle']").all()
        aria_links = []
        for toggle in aria_section_toggles:
            category = toggle.locator("summary").inner_text().strip()
            if category == "ARIA guides":
                print(f"Skipping category: {category}")
                continue  # Skip this category
            print(f"Processing category: {category}")
            category = re.sub(r'\s+', '_', category.lower())
            links = []
            for link in toggle.locator("ol li a").all():
                href = link.get_attribute("href")
                if href and href.startswith("/"):
                    links.append({
                    "text": link.evaluate("node => node.textContent.trim()") or "No Text Found",
                    "url": f"{base_url}{href}"
                })
            aria_links.append({
            "aria_techniques": category,  # Keep original category format
            "links": links
            })
            print(f"Category '{category}' -> Found {len(links)} links")

        return aria_links

    def _get_text(self, selector):
        """Safely retrieves inner text from a locator."""
        locator = self.page.locator(selector)
        return locator.inner_text().strip() if locator.count() > 0 else ""

    def _save_to_json(self, folder_path, filename, data):
        """Saves the scraped data to a JSON file inside a specific folder."""
        os.makedirs(folder_path, exist_ok=True)  # Ensure folder exists
        file_path = os.path.join(folder_path, filename)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
                if not isinstance(existing_data, list):
                    existing_data = []
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []

        existing_data.append(data)

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, indent=4)

        print(f"Data saved to {file_path}")
