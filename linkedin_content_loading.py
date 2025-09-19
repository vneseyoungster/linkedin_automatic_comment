import time
import json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from chrome_initialize import LinkedInCommentBot

class LinkedInAuthorScanner(LinkedInCommentBot):
    def __init__(self):
        super().__init__()
        self.scanned_data = {
            "scan_timestamp": datetime.now().isoformat(),
            "authors_found": [],
            "ember_elements_found": 0,
            "scan_summary": {}
        }

    def scan_ember_elements(self):
        """
        Scan for Ember elements that contain author information
        """
        print("Scanning for Ember elements with authors...")

        # Find all elements with ember IDs
        ember_elements = self.driver.find_elements(By.CSS_SELECTOR, "[id^='ember']")
        self.scanned_data["ember_elements_found"] = len(ember_elements)

        print(f"Found {len(ember_elements)} Ember elements")

        # Find post containers that have author elements
        author_containers = []

        for ember_elem in ember_elements:
            try:
                ember_id = ember_elem.get_attribute('id')

                # Check if this ember element contains author name structure
                if ember_elem.find_elements(By.CSS_SELECTOR, ".update-components-actor__title"):
                    author_containers.append({
                        "ember_id": ember_id,
                        "element": ember_elem,
                        "type": "author-container"
                    })
            except Exception as e:
                continue

        print(f"Found {len(author_containers)} containers with authors")
        return author_containers

    def extract_author_name(self, author_container):
        """
        Extract only the author name from a container using specific selector pattern
        """
        ember_id = author_container["ember_id"]
        element = author_container["element"]

        author_data = {
            "ember_id": ember_id,
            "author_name": None,
            "selector_used": None
        }

        try:
            # Primary selector from HTML tag pattern
            primary_selector = ".update-components-actor__title span.hoverable-link-text span span:first-child"

            # Fallback selectors
            author_selectors = [
                primary_selector,
                ".update-components-actor__title .hoverable-link-text",
                ".update-components-actor__title span[aria-hidden='true']",
                ".update-components-actor__name span",
                ".feed-shared-actor__name span"
            ]

            for selector in author_selectors:
                try:
                    author_elem = element.find_element(By.CSS_SELECTOR, selector)
                    author_text = author_elem.text.strip()
                    if author_text and len(author_text) > 2:
                        author_data["author_name"] = author_text
                        author_data["selector_used"] = selector
                        break
                except NoSuchElementException:
                    continue

        except Exception as e:
            author_data["extraction_error"] = str(e)

        return author_data

    def scan_all_authors(self):
        """
        Main scanning function that extracts only author names
        """
        print("Starting author scan...")

        # Wait for page to settle
        time.sleep(3)

        # Scroll to bottom of page to load all content
        print("Scrolling to bottom of page to load all content...")
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Scan for ember elements and author containers
        author_containers = self.scan_ember_elements()

        # Extract author names from each container
        for i, container in enumerate(author_containers):
            print(f"Extracting author from container {i+1}/{len(author_containers)}...")

            try:
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", container["element"])
                time.sleep(0.5)

                author_data = self.extract_author_name(container)
                if author_data["author_name"]:
                    self.scanned_data["authors_found"].append(author_data)

            except Exception as e:
                print(f"Error extracting from container {container['ember_id']}: {e}")
                continue

        # Generate summary
        self.scanned_data["scan_summary"] = {
            "total_ember_elements": self.scanned_data["ember_elements_found"],
            "total_containers_processed": len(author_containers),
            "unique_authors_found": len(set([a["author_name"] for a in self.scanned_data["authors_found"] if a["author_name"]])),
            "total_authors_found": len(self.scanned_data["authors_found"])
        }

        print("Author scan completed!")
        return self.scanned_data

    def save_results_to_json(self, filename="linkedin_authors.json"):
        """
        Save the scanned author data to a JSON file
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.scanned_data, f, indent=2, ensure_ascii=False)
            print(f"Results saved to {filename}")
        except Exception as e:
            print(f"Error saving results: {e}")

    def print_results(self):
        """
        Print a summary of the author scan results
        """
        print("\n" + "="*60)
        print("👥 LINKEDIN AUTHORS SCAN RESULTS")
        print("="*60)

        summary = self.scanned_data["scan_summary"]
        print(f"Total Ember elements found: {summary['total_ember_elements']}")
        print(f"Containers processed: {summary['total_containers_processed']}")
        print(f"Total authors found: {summary['total_authors_found']}")
        print(f"Unique authors found: {summary['unique_authors_found']}")

        print("\n👤 Authors found:")
        unique_authors = set()
        for i, author in enumerate(self.scanned_data["authors_found"][:10]):  # Show first 10 authors
            if author['author_name'] not in unique_authors:
                unique_authors.add(author['author_name'])
                print(f"{len(unique_authors)}. {author['author_name']} (Ember ID: {author['ember_id']})")

        if len(self.scanned_data["authors_found"]) > 10:
            print(f"... and {len(self.scanned_data['authors_found']) - 10} more")

        print("="*60)

def main():
    scanner = LinkedInAuthorScanner()

    try:
        scanner.initialize_driver()
        scan_results = scanner.scan_all_authors()
        scanner.save_results_to_json()
        scanner.print_results()

    except KeyboardInterrupt:
        print("\n⚠️  Script interrupted by user.")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

    finally:
        scanner.cleanup()

if __name__ == "__main__":
    main()