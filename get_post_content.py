import time
import json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from chrome_initialize import LinkedInCommentBot

class LinkedInContentExtractor(LinkedInCommentBot):
    def __init__(self):
        super().__init__()
        self.extraction_results = {
            "scan_timestamp": datetime.now().isoformat(),
            "total_posts": 0,
            "posts_with_content": 0,
            "posts_with_read_more": 0,
            "expansion_successful": 0,
            "posts": []
        }

    def find_read_more_button(self, post_element):
        """
        Find the 'Read More' button using multiple selector strategies
        Returns the button element if found, None otherwise
        """
        # Multiple selector strategies for Read More buttons
        read_more_selectors = [
            # Primary selector from HTML tag analysis
            "div.fie-impression-container div[class*='biSBAHR'] > div > button",
            # Alternative selectors for different LinkedIn layouts
            "button[aria-label*='more' i]",
            "button span[class*='see-more']",
            ".feed-shared-update-v2__description button",
            "button[data-control-name*='see_more']",
            # Generic fallback
            "button:contains('more')"
        ]

        for selector in read_more_selectors:
            try:
                # Special handling for :contains() selector (not supported in CSS)
                if ':contains(' in selector:
                    buttons = post_element.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        if 'more' in button.text.lower():
                            return button
                else:
                    button = post_element.find_element(By.CSS_SELECTOR, selector)
                    if button.is_displayed():
                        print(f"✅ Found Read More button with selector: {selector}")
                        return button
            except (NoSuchElementException, TimeoutException):
                continue

        return None

    def extract_post_content(self, post_element):
        """
        Extract content from a post, handling Read More expansion if needed
        """
        post_data = {
            "post_id": None,
            "has_read_more": False,
            "content_expanded": False,
            "content": None,
            "content_length": 0,
            "extraction_time": datetime.now().isoformat(),
            "selectors_used": [],
            "errors": []
        }

        try:
            # Get post ID from element attributes
            post_id = post_element.get_attribute("id")
            if not post_id:
                # Try to find parent with ID
                parent = post_element.find_element(By.XPATH, "./ancestor::*[@id][1]")
                post_id = parent.get_attribute("id") if parent else "unknown"

            post_data["post_id"] = post_id
            print(f"\n🔍 Processing post: {post_id}")

            # Step 1: Check for Read More button
            read_more_button = self.find_read_more_button(post_element)

            if read_more_button:
                post_data["has_read_more"] = True
                print("📖 Found Read More button - attempting to expand...")

                # Scroll the button into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", read_more_button)
                time.sleep(1)

                try:
                    # Try clicking the Read More button
                    ActionChains(self.driver).move_to_element(read_more_button).click().perform()
                    post_data["content_expanded"] = True
                    print("✅ Successfully clicked Read More button")

                    # Wait for content to expand
                    time.sleep(2)

                except ElementClickInterceptedException:
                    # If ActionChains fails, try JavaScript click
                    try:
                        self.driver.execute_script("arguments[0].click();", read_more_button)
                        post_data["content_expanded"] = True
                        print("✅ Successfully clicked Read More button (JS)")
                        time.sleep(2)
                    except Exception as e:
                        post_data["errors"].append(f"Failed to click Read More: {str(e)}")
                        print(f"❌ Failed to click Read More button: {e}")

                except Exception as e:
                    post_data["errors"].append(f"Read More click error: {str(e)}")
                    print(f"❌ Error clicking Read More: {e}")

            # Step 2: Extract content using multiple strategies
            content_selectors = [
                # Primary selector from HTML tag analysis
                ".fie-impression-container div[class*='biSBAHR'] > div > div",
                # Alternative content selectors
                ".fie-impression-container .break-words",
                ".feed-shared-update-v2__description",
                ".feed-shared-update-v2__description-wrapper",
                "[data-test-id='main-feed-activity-card'] .break-words",
                ".update-components-text"
            ]

            content_found = False
            for selector in content_selectors:
                try:
                    content_elements = post_element.find_elements(By.CSS_SELECTOR, selector)
                    for elem in content_elements:
                        content_text = elem.text.strip()
                        if content_text and len(content_text) > 20:  # Only consider substantial content
                            post_data["content"] = content_text
                            post_data["content_length"] = len(content_text)
                            post_data["selectors_used"].append(selector)
                            content_found = True
                            print(f"✅ Extracted content ({len(content_text)} chars) using: {selector}")
                            break

                    if content_found:
                        break

                except (NoSuchElementException, TimeoutException):
                    continue

            if not content_found:
                post_data["errors"].append("No content found with any selector")
                print("❌ No content could be extracted")

        except Exception as e:
            post_data["errors"].append(f"General extraction error: {str(e)}")
            print(f"❌ Error processing post: {e}")

        return post_data

    def scan_all_posts_for_content(self):
        """
        Main function to scan all posts and extract their content
        """
        print("🚀 Starting LinkedIn content extraction...")

        # Wait for page to settle
        time.sleep(3)

        # Find all LinkedIn posts using Ember element strategy
        ember_selectors = [
            "[id^='ember']",
            "[data-id^='urn:li:activity:']",
            ".feed-shared-update-v2"
        ]

        all_posts = []
        for selector in ember_selectors:
            try:
                posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if posts:
                    all_posts.extend(posts)
                    print(f"📍 Found {len(posts)} elements with selector: {selector}")
            except Exception as e:
                print(f"❌ Error with selector {selector}: {e}")

        # Remove duplicates by element ID
        unique_posts = []
        seen_ids = set()
        for post in all_posts:
            post_id = post.get_attribute("id")
            if post_id and post_id not in seen_ids:
                unique_posts.append(post)
                seen_ids.add(post_id)

        print(f"📊 Found {len(unique_posts)} unique posts to process")
        self.extraction_results["total_posts"] = len(unique_posts)

        # Process each post
        for i, post in enumerate(unique_posts, 1):
            print(f"\n--- Processing post {i}/{len(unique_posts)} ---")

            try:
                # Extract content from this post
                post_data = self.extract_post_content(post)
                self.extraction_results["posts"].append(post_data)

                # Update statistics
                if post_data["content"]:
                    self.extraction_results["posts_with_content"] += 1

                if post_data["has_read_more"]:
                    self.extraction_results["posts_with_read_more"] += 1

                if post_data["content_expanded"]:
                    self.extraction_results["expansion_successful"] += 1

                # Add delay between posts to avoid rate limiting
                time.sleep(1.5)

            except Exception as e:
                print(f"❌ Error processing post {i}: {e}")
                error_post = {
                    "post_id": f"error_post_{i}",
                    "error": str(e),
                    "extraction_time": datetime.now().isoformat()
                }
                self.extraction_results["posts"].append(error_post)

        print(f"\n✅ Content extraction completed!")
        self.print_extraction_summary()

    def print_extraction_summary(self):
        """
        Print a summary of the extraction results
        """
        print("\n" + "="*60)
        print("📊 LINKEDIN CONTENT EXTRACTION SUMMARY")
        print("="*60)

        print(f"🔍 Total posts found: {self.extraction_results['total_posts']}")
        print(f"📝 Posts with content extracted: {self.extraction_results['posts_with_content']}")
        print(f"📖 Posts with Read More buttons: {self.extraction_results['posts_with_read_more']}")
        print(f"✅ Successful expansions: {self.extraction_results['expansion_successful']}")

        if self.extraction_results['posts_with_content'] > 0:
            # Show content length statistics
            content_lengths = [p.get('content_length', 0) for p in self.extraction_results['posts'] if p.get('content')]
            if content_lengths:
                avg_length = sum(content_lengths) / len(content_lengths)
                print(f"📏 Average content length: {avg_length:.0f} characters")
                print(f"📏 Longest post: {max(content_lengths)} characters")
                print(f"📏 Shortest post: {min(content_lengths)} characters")

        print("\n📄 Sample extracted content:")
        print("-" * 40)
        for post in self.extraction_results['posts'][:3]:  # Show first 3 posts
            if post.get('content'):
                content_preview = post['content'][:100] + "..." if len(post['content']) > 100 else post['content']
                print(f"📝 {post['post_id']}: {content_preview}")

        print("="*60)

    def save_results_to_json(self, filename="linkedin_content_extraction.json"):
        """
        Save extraction results to JSON file
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.extraction_results, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")

def main():
    """
    Main function for standalone testing
    """
    extractor = LinkedInContentExtractor()

    try:
        print("🚀 LinkedIn Content Extractor - Standalone Test")
        print("=" * 50)

        # Initialize browser and navigate to LinkedIn
        extractor.initialize_driver()

        # Wait for user to navigate to desired LinkedIn page
        input("\n📍 Navigate to the LinkedIn page you want to extract content from, then press Enter...")

        # Start content extraction
        extractor.scan_all_posts_for_content()

        # Save results
        extractor.save_results_to_json()

        # Keep browser open for inspection
        input("\n✅ Extraction complete! Press Enter to close browser...")

    except KeyboardInterrupt:
        print("\n⚠️ Script interrupted by user.")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

    finally:
        extractor.cleanup()

if __name__ == "__main__":
    main()