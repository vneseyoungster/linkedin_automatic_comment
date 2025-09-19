import time
import json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from chrome_initialize import LinkedInCommentBot

class LinkedInSponsorScanner(LinkedInCommentBot):
    def __init__(self):
        super().__init__()
        self.sponsored_ember_ids = []

    def is_promoted_post(self, post_element):
        """
        Simple sponsor/advertising post detection
        """
        try:
            promoted_text = post_element.text.lower()
            return 'promoted' in promoted_text or 'sponsored' in promoted_text
        except:
            return False

    def scan_sponsored_posts(self):
        """
        Scan for sponsored post ember IDs only
        """
        print("Scanning for sponsored posts...")

        # Wait for page to settle
        time.sleep(3)

        # Scroll to bottom of page to load all content
        print("Scrolling to bottom of page to load all content...")
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Find all elements with ember IDs
        ember_elements = self.driver.find_elements(By.CSS_SELECTOR, "[id^='ember']")
        print(f"Found {len(ember_elements)} Ember elements")

        # Check each ember element for sponsored content
        for ember_elem in ember_elements:
            try:
                ember_id = ember_elem.get_attribute('id')

                # Check if this ember element is a sponsored post
                if self.is_promoted_post(ember_elem):
                    self.sponsored_ember_ids.append(ember_id)
                    print(f"📢 Found sponsored post: {ember_id}")

            except Exception as e:
                continue

        print(f"Sponsor scan completed! Found {len(self.sponsored_ember_ids)} sponsored posts")
        return self.sponsored_ember_ids

    def save_results_to_json(self, filename="sponsored_ember_ids.json"):
        """
        Save the sponsored ember IDs to a JSON file
        """
        try:
            data = {
                "scan_timestamp": datetime.now().isoformat(),
                "sponsored_ember_ids": self.sponsored_ember_ids,
                "total_sponsored_found": len(self.sponsored_ember_ids)
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Results saved to {filename}")
        except Exception as e:
            print(f"Error saving results: {e}")

    def print_results(self):
        """
        Print sponsored ember IDs
        """
        print("\n" + "="*50)
        print("📢 SPONSORED POST EMBER IDs")
        print("="*50)
        print(f"Total sponsored posts found: {len(self.sponsored_ember_ids)}")

        if self.sponsored_ember_ids:
            print("\nSponsored Ember IDs:")
            for i, ember_id in enumerate(self.sponsored_ember_ids, 1):
                print(f"{i}. {ember_id}")
        else:
            print("No sponsored posts found")

        print("="*50)

def main():
    scanner = LinkedInSponsorScanner()

    try:
        scanner.initialize_driver()
        sponsored_ids = scanner.scan_sponsored_posts()
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