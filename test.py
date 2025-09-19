import time
import json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from chrome_initialize import LinkedInCommentBot
import config

class LinkedInComprehensiveScanner(LinkedInCommentBot):
    def __init__(self):
        super().__init__()
        self.scan_results = {
            "scan_timestamp": datetime.now().isoformat(),
            "posts_data": [],
            "normal_posts": [],
            "sponsored_posts": [],
            "ember_elements_found": 0,
            "scan_summary": {}
        }

        # Content extraction results (Stage 2)
        self.content_results = {
            "extraction_timestamp": None,
            "total_posts_processed": 0,
            "posts_with_content": 0,
            "posts_with_read_more": 0,
            "expansion_successful": 0,
            "content_data": []
        }

    def is_promoted_post(self, post_element):
        """
        Simple sponsor/advertising post detection
        """
        try:
            promoted_text = post_element.text.lower()
            return 'promoted' in promoted_text or 'sponsored' in promoted_text
        except:
            return False

    def extract_author_name(self, element):
        """
        Extract author name from a post element using specific selector patterns
        """
        author_data = {
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

    def scroll_to_bottom(self):
        """
        Scroll down three times to load more content via LinkedIn's infinite scrolling
        """
        print("📜 Scrolling down to load more content...")

        for i in range(3):
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for new content to load
            time.sleep(2)
            print(f"   Scroll {i+1}/3 completed")

        print("✅ Finished scrolling - content loaded")

    def scan_all_posts(self):
        """
        Main scanning function that extracts posts, authors, and sponsor status
        """
        print("🔍 Starting comprehensive LinkedIn post scan...")

        # Wait for page to settle
        time.sleep(3)

        # Scroll to bottom to load all content
        self.scroll_to_bottom()

        # Find all elements with ember IDs
        ember_elements = self.driver.find_elements(By.CSS_SELECTOR, "[id^='ember']")
        self.scan_results["ember_elements_found"] = len(ember_elements)
        print(f"📊 Found {len(ember_elements)} Ember elements")

        # Find post containers that have author elements
        post_containers = []

        for ember_elem in ember_elements:
            try:
                ember_id = ember_elem.get_attribute('id')

                # Check if this ember element contains author name structure
                if ember_elem.find_elements(By.CSS_SELECTOR, ".update-components-actor__title"):
                    post_containers.append({
                        "ember_id": ember_id,
                        "element": ember_elem,
                        "type": "post-container"
                    })
            except Exception as e:
                continue

        print(f"📝 Found {len(post_containers)} post containers with authors")

        # Process each post container
        for i, container in enumerate(post_containers):
            print(f"⚙️ Processing post {i+1}/{len(post_containers)}...")

            try:
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", container["element"])
                time.sleep(0.5)

                # Extract author information
                author_data = self.extract_author_name(container["element"])

                # Check if it's a sponsored post
                is_sponsored = self.is_promoted_post(container["element"])

                # Create post data
                post_data = {
                    "ember_id": container["ember_id"],
                    "author_name": author_data["author_name"],
                    "is_sponsored": is_sponsored,
                    "selector_used": author_data.get("selector_used"),
                    "post_type": "sponsored" if is_sponsored else "normal"
                }

                # Add to appropriate lists
                self.scan_results["posts_data"].append(post_data)

                if is_sponsored:
                    self.scan_results["sponsored_posts"].append(post_data)
                    print(f"📢 Sponsored post found: {author_data['author_name']} (ID: {container['ember_id']})")
                else:
                    self.scan_results["normal_posts"].append(post_data)
                    print(f"👤 Normal post found: {author_data['author_name']} (ID: {container['ember_id']})")

            except Exception as e:
                print(f"❌ Error processing container {container['ember_id']}: {e}")
                continue

        # Generate summary
        self.scan_results["scan_summary"] = {
            "total_ember_elements": self.scan_results["ember_elements_found"],
            "total_posts_processed": len(post_containers),
            "total_posts_with_authors": len(self.scan_results["posts_data"]),
            "normal_posts_count": len(self.scan_results["normal_posts"]),
            "sponsored_posts_count": len(self.scan_results["sponsored_posts"]),
            "unique_authors_count": len(set([p["author_name"] for p in self.scan_results["posts_data"] if p["author_name"]]))
        }

        print("✅ Comprehensive scan completed!")
        return self.scan_results

    def save_results_to_json(self, filename="linkedin_comprehensive_scan.json"):
        """
        Save the comprehensive scan results to a JSON file
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.scan_results, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")

    def print_comprehensive_results(self):
        """
        Print a detailed summary of the comprehensive scan results
        """
        print("\n" + "="*80)
        print("🔍 LINKEDIN COMPREHENSIVE SCAN RESULTS")
        print("="*80)

        summary = self.scan_results["scan_summary"]
        print(f"📊 Total Ember elements found: {summary['total_ember_elements']}")
        print(f"📝 Total posts processed: {summary['total_posts_processed']}")
        print(f"👥 Posts with authors found: {summary['total_posts_with_authors']}")
        print(f"📄 Normal posts: {summary['normal_posts_count']}")
        print(f"📢 Sponsored posts: {summary['sponsored_posts_count']}")
        print(f"👤 Unique authors: {summary['unique_authors_count']}")

        # Show normal posts
        print(f"\n📄 NORMAL POSTS ({len(self.scan_results['normal_posts'])} found):")
        print("-" * 60)
        for i, post in enumerate(self.scan_results["normal_posts"][:10], 1):  # Show first 10
            print(f"{i}. {post['author_name']} (Ember ID: {post['ember_id']})")

        if len(self.scan_results["normal_posts"]) > 10:
            print(f"... and {len(self.scan_results['normal_posts']) - 10} more normal posts")

        # Show sponsored posts
        print(f"\n📢 SPONSORED POSTS ({len(self.scan_results['sponsored_posts'])} found):")
        print("-" * 60)
        if self.scan_results["sponsored_posts"]:
            for i, post in enumerate(self.scan_results["sponsored_posts"], 1):
                print(f"{i}. {post['author_name']} (Ember ID: {post['ember_id']})")
        else:
            print("No sponsored posts found")

        # Show all unique authors
        print(f"\n👥 UNIQUE AUTHORS ({summary['unique_authors_count']} found):")
        print("-" * 60)
        unique_authors = set()
        for post in self.scan_results["posts_data"]:
            if post["author_name"] and post["author_name"] not in unique_authors:
                unique_authors.add(post["author_name"])
                post_type = "📢 Sponsored" if post["is_sponsored"] else "📄 Normal"
                print(f"• {post['author_name']} - {post_type}")

        print("="*80)

    def find_read_more_button(self, post_element):
        """
        Find the 'Read More' button using multiple selector strategies
        Returns the button element if found, None otherwise
        """
        read_more_selectors = [
            # Primary selector from HTML tag analysis
            "div.fie-impression-container div[class*='biSBAHR'] > div > button",
            # Alternative selectors for different LinkedIn layouts
            "button[aria-label*='more' i]",
            "button span[class*='see-more']",
            ".feed-shared-update-v2__description button",
            "button[data-control-name*='see_more']"
        ]

        for selector in read_more_selectors:
            try:
                button = post_element.find_element(By.CSS_SELECTOR, selector)
                if button.is_displayed():
                    return button
            except (NoSuchElementException, TimeoutException):
                continue

        # Fallback: look for buttons containing "more" text
        try:
            buttons = post_element.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if 'more' in button.text.lower():
                    return button
        except Exception:
            pass

        return None

    def extract_post_content(self, post_element, ember_id):
        """
        Extract content from a specific post, handling Read More expansion if needed
        """
        content_data = {
            "ember_id": ember_id,
            "has_read_more": False,
            "content_expanded": False,
            "content": None,
            "content_length": 0,
            "extraction_time": datetime.now().isoformat(),
            "selectors_used": [],
            "errors": []
        }

        try:
            print(f"🔍 Extracting content from post: {ember_id}")

            # Step 1: Check for Read More button
            read_more_button = self.find_read_more_button(post_element)

            if read_more_button:
                content_data["has_read_more"] = True
                print("📖 Found Read More button - attempting to expand...")

                # Scroll the button into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", read_more_button)
                time.sleep(config.SCROLL_DELAY)

                try:
                    # Try clicking the Read More button
                    ActionChains(self.driver).move_to_element(read_more_button).click().perform()
                    content_data["content_expanded"] = True
                    print("✅ Successfully clicked Read More button")
                    time.sleep(config.DELAY_AFTER_READ_MORE)

                except ElementClickInterceptedException:
                    # If ActionChains fails, try JavaScript click
                    try:
                        self.driver.execute_script("arguments[0].click();", read_more_button)
                        content_data["content_expanded"] = True
                        print("✅ Successfully clicked Read More button (JS)")
                        time.sleep(config.DELAY_AFTER_READ_MORE)
                    except Exception as e:
                        content_data["errors"].append(f"Failed to click Read More: {str(e)}")
                        print(f"❌ Failed to click Read More button: {e}")

                except Exception as e:
                    content_data["errors"].append(f"Read More click error: {str(e)}")
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
                            content_data["content"] = content_text
                            content_data["content_length"] = len(content_text)
                            content_data["selectors_used"].append(selector)
                            content_found = True
                            print(f"✅ Extracted content ({len(content_text)} chars) using: {selector}")
                            break

                    if content_found:
                        break

                except (NoSuchElementException, TimeoutException):
                    continue

            if not content_found:
                content_data["errors"].append("No content found with any selector")
                print("❌ No content could be extracted")

        except Exception as e:
            content_data["errors"].append(f"General extraction error: {str(e)}")
            print(f"❌ Error processing post: {e}")

        return content_data

    def load_valid_posts(self, filename="linkedin_comprehensive_scan.json"):
        """
        Load valid (non-sponsored) posts from Stage 1 results
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                stage1_data = json.load(f)

            valid_posts = stage1_data.get("normal_posts", [])
            print(f"📚 Loaded {len(valid_posts)} valid posts from {filename}")
            return valid_posts

        except Exception as e:
            print(f"❌ Error loading valid posts: {e}")
            return []

    def apply_content_filters(self, posts):
        """
        Apply configuration-based filters to posts
        """
        filtered_posts = []

        for post in posts:
            author_name = post.get("author_name", "")

            # Apply author filtering
            if config.EXTRACT_FROM_SPECIFIC_AUTHORS:
                if author_name not in config.EXTRACT_FROM_SPECIFIC_AUTHORS:
                    print(f"⏭️  Skipping {author_name} - not in specific authors list")
                    continue

            if config.SKIP_AUTHORS:
                if author_name in config.SKIP_AUTHORS:
                    print(f"⏭️  Skipping {author_name} - in skip authors list")
                    continue

            # Apply sponsored filter
            if not config.EXTRACT_FROM_SPONSORED and post.get("is_sponsored", False):
                print(f"⏭️  Skipping sponsored post by {author_name}")
                continue

            filtered_posts.append(post)

        return filtered_posts

    def extract_content_from_valid_posts(self, valid_posts=None):
        """
        Stage 2: Extract content from valid posts identified in Stage 1
        """
        print("\n🚀 Starting Stage 2: Content Extraction...")
        print("="*60)

        # Validate configuration
        config_warnings = config.validate_config()
        if config_warnings:
            print("⚠️  Configuration warnings:")
            for warning in config_warnings:
                print(f"   • {warning}")
            print()

        self.content_results["extraction_timestamp"] = datetime.now().isoformat()

        # If no valid posts provided, load from Stage 1 results
        if valid_posts is None:
            valid_posts = self.load_valid_posts()

        if not valid_posts:
            print("❌ No valid posts found to process")
            return

        # Apply configuration filters
        filtered_posts = self.apply_content_filters(valid_posts)

        # Apply post limit from config
        if config.MAX_POSTS_TO_PROCESS > 0:
            filtered_posts = filtered_posts[:config.MAX_POSTS_TO_PROCESS]
            print(f"📊 Limited to {config.MAX_POSTS_TO_PROCESS} posts as per configuration")

        if not filtered_posts:
            print("❌ No posts remaining after applying filters")
            return

        self.content_results["total_posts_processed"] = len(filtered_posts)
        print(f"📊 Processing {len(filtered_posts)} filtered posts for content extraction...")
        print(f"⚙️  Configuration: {config.DELAY_BETWEEN_POSTS}s delay, auto-expand: {config.AUTO_EXPAND_READ_MORE}")

        # Process each valid post
        processed_count = 0
        for i, post_data in enumerate(filtered_posts, 1):
            ember_id = post_data.get("ember_id")
            author_name = post_data.get("author_name", "Unknown")

            print(f"\n--- Processing post {i}/{len(filtered_posts)} ---")
            print(f"👤 Author: {author_name}")
            print(f"🔖 Ember ID: {ember_id}")

            retry_count = 0
            success = False

            while retry_count <= config.MAX_RETRIES_PER_POST and not success:
                try:
                    # Find the post element by ember ID
                    post_element = self.driver.find_element(By.ID, ember_id)

                    # Scroll into view with configured delay
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_element)
                    time.sleep(config.SCROLL_DELAY)

                    # Extract content
                    content_data = self.extract_post_content(post_element, ember_id)

                    # Add author information to content data
                    content_data["author_name"] = author_name

                    # Apply content length filters
                    if content_data.get("content"):
                        content_length = len(content_data["content"])

                        if config.SKIP_SHORT_POSTS and content_length < config.MIN_CONTENT_LENGTH:
                            print(f"⏭️  Skipping short post ({content_length} chars < {config.MIN_CONTENT_LENGTH})")
                            success = True
                            continue

                        # Truncate if too long
                        if content_length > config.MAX_CONTENT_LENGTH:
                            content_data["content"] = content_data["content"][:config.MAX_CONTENT_LENGTH] + "..."
                            content_data["content_truncated"] = True
                            content_data["original_length"] = content_length
                            print(f"✂️  Truncated content from {content_length} to {config.MAX_CONTENT_LENGTH} chars")

                    # Store results
                    self.content_results["content_data"].append(content_data)

                    # Update statistics
                    if content_data["content"]:
                        self.content_results["posts_with_content"] += 1

                    if content_data["has_read_more"]:
                        self.content_results["posts_with_read_more"] += 1

                    if content_data["content_expanded"]:
                        self.content_results["expansion_successful"] += 1

                    processed_count += 1
                    success = True

                    # Save incrementally if configured
                    if config.SAVE_CONTENT_INCREMENTALLY and processed_count % 5 == 0:
                        self.save_content_results(f"linkedin_content_extraction_partial_{processed_count}.json")

                    # Add configured delay between posts
                    time.sleep(config.DELAY_BETWEEN_POSTS)

                except NoSuchElementException:
                    if retry_count == 0:
                        print(f"❌ Could not find post element with ID: {ember_id}")

                    if retry_count < config.MAX_RETRIES_PER_POST:
                        retry_count += 1
                        print(f"🔄 Retrying ({retry_count}/{config.MAX_RETRIES_PER_POST})...")
                        time.sleep(2)
                    else:
                        error_data = {
                            "ember_id": ember_id,
                            "author_name": author_name,
                            "error": "Element not found after retries",
                            "extraction_time": datetime.now().isoformat()
                        }
                        self.content_results["content_data"].append(error_data)
                        success = True  # Exit retry loop

                        if not config.CONTINUE_ON_ERROR:
                            print("❌ Stopping extraction due to error (CONTINUE_ON_ERROR = False)")
                            break

                except Exception as e:
                    if retry_count == 0:
                        print(f"❌ Error processing post {ember_id}: {e}")

                    if retry_count < config.MAX_RETRIES_PER_POST:
                        retry_count += 1
                        print(f"🔄 Retrying ({retry_count}/{config.MAX_RETRIES_PER_POST})...")
                        time.sleep(2)
                    else:
                        error_data = {
                            "ember_id": ember_id,
                            "author_name": author_name,
                            "error": str(e),
                            "extraction_time": datetime.now().isoformat()
                        }
                        self.content_results["content_data"].append(error_data)
                        success = True  # Exit retry loop

                        if not config.CONTINUE_ON_ERROR:
                            print("❌ Stopping extraction due to error (CONTINUE_ON_ERROR = False)")
                            break

            if not config.CONTINUE_ON_ERROR and not success:
                break

        print(f"\n✅ Content extraction completed!")
        self.print_content_extraction_summary()

    def print_content_extraction_summary(self):
        """
        Print a summary of the content extraction results
        """
        print("\n" + "="*80)
        print("📊 STAGE 2: CONTENT EXTRACTION SUMMARY")
        print("="*80)

        print(f"🔍 Total posts processed: {self.content_results['total_posts_processed']}")
        print(f"📝 Posts with content extracted: {self.content_results['posts_with_content']}")
        print(f"📖 Posts with Read More buttons: {self.content_results['posts_with_read_more']}")
        print(f"✅ Successful expansions: {self.content_results['expansion_successful']}")

        if self.content_results['posts_with_content'] > 0:
            # Show content length statistics
            content_lengths = [p.get('content_length', 0) for p in self.content_results['content_data'] if p.get('content')]
            if content_lengths:
                avg_length = sum(content_lengths) / len(content_lengths)
                print(f"📏 Average content length: {avg_length:.0f} characters")
                print(f"📏 Longest post: {max(content_lengths)} characters")
                print(f"📏 Shortest post: {min(content_lengths)} characters")

        print("\n📄 Sample extracted content:")
        print("-" * 60)
        for post in self.content_results['content_data'][:3]:  # Show first 3 posts
            if post.get('content'):
                content_preview = post['content'][:150] + "..." if len(post['content']) > 150 else post['content']
                print(f"📝 {post.get('author_name', 'Unknown')} ({post['ember_id']}):")
                print(f"   {content_preview}")
                print()

        print("="*80)

    def save_content_results(self, filename=None):
        """
        Save content extraction results to JSON file
        """
        if filename is None:
            filename = config.CONTENT_EXTRACTION_FILENAME

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.content_results, f, indent=2, ensure_ascii=False)
            print(f"💾 Content extraction results saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving content results: {e}")

def main():
    """
    Main test function that runs the two-stage workflow
    """
    print("🚀 Starting LinkedIn Comprehensive Scanner - Two-Stage Workflow")
    print("="*70)

    scanner = LinkedInComprehensiveScanner()

    try:
        # ========== STAGE 1: POST DISCOVERY & CLASSIFICATION ==========
        print("🔍 STAGE 1: Post Discovery & Classification")
        print("="*50)

        # Step 1: Initialize Chrome and open login
        print("Step 1: Initializing Chrome browser...")
        scanner.initialize_driver()

        # Step 2: Manual login (handled in initialize_driver)
        print("Step 2: Manual login completed ✅")

        # Step 3-6: Scroll, load authors, detect sponsors, return results
        print("Step 3-6: Scanning posts, authors, and sponsors...")
        scan_results = scanner.scan_all_posts()

        # Save Stage 1 results to JSON
        scanner.save_results_to_json()

        # Print comprehensive results
        scanner.print_comprehensive_results()

        # Show Stage 1 completion summary
        normal_posts_count = len(scanner.scan_results.get("normal_posts", []))
        sponsored_posts_count = len(scanner.scan_results.get("sponsored_posts", []))

        print(f"\n✅ STAGE 1 COMPLETED!")
        print(f"📊 Found {normal_posts_count} valid posts (non-sponsored)")
        print(f"📢 Found {sponsored_posts_count} sponsored posts")
        print(f"💾 Results saved to 'linkedin_comprehensive_scan.json'")

        # Initialize user_choice for scope
        user_choice = 'skip'

        # ========== STAGE 2: CONTENT EXTRACTION (OPTIONAL) ==========
        if normal_posts_count > 0:
            print("\n" + "="*70)
            print("🚀 STAGE 2: Content Extraction (Optional)")
            print("="*50)

            # Calculate estimated posts after filtering
            estimated_posts = min(normal_posts_count, config.MAX_POSTS_TO_PROCESS if config.MAX_POSTS_TO_PROCESS > 0 else normal_posts_count)

            print(f"📋 Ready to extract content from up to {estimated_posts} valid posts")
            print("⚠️  This process will click 'Read More' buttons and extract full post content")
            print("⏱️  Estimated time: ~{:.1f} minutes".format(estimated_posts * config.DELAY_BETWEEN_POSTS / 60))
            print(f"⚙️  Config: MAX_POSTS_TO_PROCESS = {config.MAX_POSTS_TO_PROCESS}")

            # Check for automation settings
            if config.AUTO_START_STAGE_2:
                print("🤖 AUTO_START_STAGE_2 is enabled - starting automatically...")
                user_choice = ""
            elif config.SKIP_STAGE_2_PROMPT:
                print("⏭️  SKIP_STAGE_2_PROMPT is enabled - skipping content extraction")
                user_choice = "skip"
            else:
                # User prompt for Stage 2
                user_choice = input("\n❓ Do you want to proceed with content retrieval? Press Enter to continue (or 'n' to skip): ").strip().lower()

            if user_choice in ['n', 'no', 'skip']:
                print("⏭️  Skipping content extraction. Only post discovery results saved.")
            else:
                print("\n🚀 Starting content extraction...")

                # Execute Stage 2: Content Extraction
                scanner.extract_content_from_valid_posts(scanner.scan_results["normal_posts"])

                # Save Stage 2 results
                scanner.save_content_results()

                print(f"\n✅ STAGE 2 COMPLETED!")
                print(f"💾 Content results saved to '{config.CONTENT_EXTRACTION_FILENAME}'")

        else:
            print(f"\n⚠️  No valid posts found for content extraction")
            print(f"📢 Only sponsored posts were detected - skipping Stage 2")

        # Final summary
        print("\n" + "="*70)
        print("🏁 TWO-STAGE WORKFLOW COMPLETED!")
        print("="*70)
        print("📁 Generated Files:")
        print("   • linkedin_comprehensive_scan.json - Post discovery results")
        if normal_posts_count > 0 and user_choice not in ['n', 'no', 'skip']:
            print(f"   • {config.CONTENT_EXTRACTION_FILENAME} - Content extraction results")

        print(f"\n📊 Final Summary:")
        print(f"   • Total posts processed: {len(scanner.scan_results.get('posts_data', []))}")
        print(f"   • Valid posts: {normal_posts_count}")
        print(f"   • Sponsored posts: {sponsored_posts_count}")
        if hasattr(scanner, 'content_results') and scanner.content_results.get('posts_with_content', 0) > 0:
            print(f"   • Posts with content extracted: {scanner.content_results['posts_with_content']}")

        input("\n✅ Workflow complete! Press Enter to close browser...")

    except KeyboardInterrupt:
        print("\n⚠️ Script interrupted by user.")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

    finally:
        scanner.cleanup()
        print("\n🏁 LinkedIn Scanner closed!")

if __name__ == "__main__":
    main()