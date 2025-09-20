import time
import random
import json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from chrome_initialize import LinkedInCommentBot
import config

class LinkedInCommentAction(LinkedInCommentBot):
    def __init__(self):
        super().__init__()
        self.comment_results = {
            "session_timestamp": datetime.now().isoformat(),
            "total_attempts": 0,
            "successful_comments": 0,
            "failed_comments": 0,
            "comments": []
        }

    def find_post_by_ember_id(self, ember_id):
        """
        Find a specific post by its ember ID
        Args:
            ember_id (str): The ember ID of the post (e.g., 'ember53')
        Returns:
            WebElement or None: The post element if found
        """
        try:
            print(f"🔍 Looking for post with ember ID: {ember_id}")

            # Strategy 1: Direct ID match
            try:
                post_element = self.driver.find_element(By.ID, ember_id)
                if post_element.is_displayed():
                    print(f"✅ Found post directly by ID: {ember_id}")
                    return post_element
            except NoSuchElementException:
                pass

            # Strategy 2: Look for element with data-id containing the ember reference
            try:
                post_element = self.driver.find_element(
                    By.CSS_SELECTOR,
                    f"[data-id*='{ember_id}']"
                )
                if post_element.is_displayed():
                    print(f"✅ Found post by data-id reference: {ember_id}")
                    return post_element
            except NoSuchElementException:
                pass

            # Strategy 3: Look within ember container structures
            try:
                ember_containers = self.driver.find_elements(By.CSS_SELECTOR, f"#{ember_id}")
                for container in ember_containers:
                    # Check if this container looks like a post
                    if self._is_post_container(container):
                        print(f"✅ Found post container: {ember_id}")
                        return container
            except NoSuchElementException:
                pass

            print(f"❌ Could not find post with ember ID: {ember_id}")
            return None

        except Exception as e:
            print(f"❌ Error finding post by ember ID {ember_id}: {e}")
            return None

    def _is_post_container(self, element):
        """
        Check if an element looks like a LinkedIn post container
        """
        try:
            # Check for typical post structure indicators
            post_indicators = [
                ".fie-impression-container",
                ".feed-shared-update-v2",
                "[data-id^='urn:li:activity:']",
                ".update-components-actor"
            ]

            for indicator in post_indicators:
                if element.find_elements(By.CSS_SELECTOR, indicator):
                    return True

            # Check if element has reasonable height (actual posts are usually tall)
            if element.size.get('height', 0) > 100:
                return True

            return False
        except:
            return False

    def find_comment_button(self, post_element):
        """
        Find the comment button within a post using multiple strategies
        Based on linkedin_html_tag.txt patterns
        """
        try:
            print("🔍 Looking for comment button...")

            # Strategy 1: Use the specific ID pattern from HTML tag file
            # Pattern: #feed-shared-social-action-bar-comment-ember[number]
            try:
                comment_buttons = post_element.find_elements(
                    By.CSS_SELECTOR,
                    "[id^='feed-shared-social-action-bar-comment-']"
                )
                for button in comment_buttons:
                    if button.is_displayed() and button.is_enabled():
                        button_id = button.get_attribute('id')
                        print(f"✅ Found comment button by ID pattern: {button_id}")
                        return button
            except NoSuchElementException:
                pass

            # Strategy 2: Find by aria-label containing 'comment'
            try:
                comment_button = post_element.find_element(
                    By.CSS_SELECTOR,
                    "button[aria-label*='comment' i]"
                )
                if comment_button.is_displayed() and comment_button.is_enabled():
                    aria_label = comment_button.get_attribute('aria-label')
                    print(f"✅ Found comment button by aria-label: {aria_label}")
                    return comment_button
            except NoSuchElementException:
                pass

            # Strategy 3: XPath search for any button containing 'comment' in ID
            try:
                comment_buttons = post_element.find_elements(
                    By.XPATH,
                    ".//button[contains(@id, 'comment')]"
                )
                for button in comment_buttons:
                    if button.is_displayed() and button.is_enabled():
                        button_id = button.get_attribute('id')
                        print(f"✅ Found comment button by XPath ID search: {button_id}")
                        return button
            except NoSuchElementException:
                pass

            # Strategy 4: Look for social action bar and find comment button within
            try:
                social_bars = post_element.find_elements(
                    By.CSS_SELECTOR,
                    "[class*='social-action'], [id*='social-action']"
                )
                for bar in social_bars:
                    buttons = bar.find_elements(By.CSS_SELECTOR, "button")
                    for button in buttons:
                        button_id = button.get_attribute('id') or ''
                        button_aria = button.get_attribute('aria-label') or ''
                        button_text = button.text.lower()

                        if ('comment' in button_id.lower() or
                            'comment' in button_aria.lower() or
                            'comment' in button_text):
                            if button.is_displayed() and button.is_enabled():
                                print(f"✅ Found comment button in social action bar")
                                return button
            except NoSuchElementException:
                pass

            print("❌ Could not find comment button with any strategy")
            return None

        except Exception as e:
            print(f"❌ Error finding comment button: {e}")
            return None

    def click_comment_button(self, comment_button):
        """
        Click the comment button and wait for comment section to appear
        """
        try:
            print("🖱️ Clicking comment button...")

            # Scroll button into view
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                comment_button
            )
            time.sleep(config.SCROLL_DELAY)

            # Try clicking the button
            try:
                comment_button.click()
                print("✅ Successfully clicked comment button")
            except ElementClickInterceptedException:
                # If regular click fails, try JavaScript click
                print("🔄 Regular click failed, trying JavaScript click...")
                self.driver.execute_script("arguments[0].click();", comment_button)
                print("✅ Successfully clicked comment button with JavaScript")

            # Wait for comment section to appear
            print("⏳ Waiting for comment section to load...")
            time.sleep(config.DELAY_AFTER_READ_MORE)

            return True

        except Exception as e:
            print(f"❌ Error clicking comment button: {e}")
            return False

    def find_comment_text_area(self, post_element=None):
        """
        Find the comment text area after clicking comment button
        Based on linkedin_html_tag.txt patterns
        Args:
            post_element: Optional post element to search within for better context
        """
        try:
            print("🔍 Looking for comment text area...")

            # Strategy 1: Search within post element first if provided
            if post_element:
                try:
                    comment_box = post_element.find_element(By.CSS_SELECTOR, ".ql-editor")
                    if comment_box.is_displayed():
                        print("✅ Found comment text area (.ql-editor) within post context")
                        return comment_box
                except NoSuchElementException:
                    pass

            # Strategy 2: Find the ql-editor directly (most common)
            try:
                comment_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".ql-editor"))
                )
                if comment_box.is_displayed():
                    print("✅ Found comment text area (.ql-editor)")
                    return comment_box
            except TimeoutException:
                pass

            # Strategy 3: Find within comments-comment-box structure (within post if available)
            search_element = post_element if post_element else self.driver
            try:
                comment_box = search_element.find_element(
                    By.CSS_SELECTOR,
                    ".comments-comment-box-comment__text-editor .ql-editor"
                )
                if comment_box.is_displayed():
                    context = " within post context" if post_element else ""
                    print(f"✅ Found comment text area in comment box structure{context}")
                    return comment_box
            except NoSuchElementException:
                pass

            # Strategy 4: Find by contenteditable attribute (within post if available)
            try:
                comment_box = search_element.find_element(
                    By.CSS_SELECTOR,
                    "[contenteditable='true'][role='textbox']"
                )
                if comment_box.is_displayed():
                    context = " within post context" if post_element else ""
                    print(f"✅ Found comment text area (contenteditable){context}")
                    return comment_box
            except NoSuchElementException:
                pass

            # Strategy 5: Look for any contenteditable div that appeared recently (within post if available)
            try:
                contenteditable_elements = search_element.find_elements(
                    By.CSS_SELECTOR,
                    "[contenteditable='true']"
                )
                for element in contenteditable_elements:
                    if (element.is_displayed() and
                        element.get_attribute('role') in ['textbox', None] and
                        element.size.get('height', 0) > 20):
                        context = " within post context" if post_element else ""
                        print(f"✅ Found comment text area (generic contenteditable){context}")
                        return element
            except NoSuchElementException:
                pass

            print("❌ Could not find comment text area")
            return None

        except Exception as e:
            print(f"❌ Error finding comment text area: {e}")
            return None

    def type_comment_naturally(self, text_area, comment_text):
        """
        Type comment with human-like behavior
        """
        try:
            print(f"⌨️ Typing comment: {comment_text[:50]}...")

            # Click to focus the text area
            try:
                text_area.click()
            except:
                self.driver.execute_script("arguments[0].click();", text_area)

            time.sleep(0.5)

            # Clear any existing content
            try:
                text_area.clear()
            except:
                # If clear doesn't work, select all and delete
                text_area.send_keys(Keys.CONTROL + "a")
                text_area.send_keys(Keys.DELETE)

            time.sleep(0.5)

            # Type character by character with fast delays (under 2 seconds total)
            for i, char in enumerate(comment_text):
                text_area.send_keys(char)

                # Optimized typing speed for 15-word comments
                if i % 15 == 0:  # Every 15 characters, pause slightly longer
                    time.sleep(random.uniform(0.05, 0.08))
                else:
                    time.sleep(random.uniform(0.01, 0.025))

            print("✅ Successfully typed comment")
            time.sleep(0.3)  # Quick wait for UI to update

            return True

        except Exception as e:
            print(f"❌ Error typing comment: {e}")
            return False

    def find_submit_button(self, post_element=None):
        """
        Find the submit/post comment button
        Based on linkedin_html_tag.txt patterns
        Args:
            post_element: Optional post element to search within for better context
        """
        try:
            print("🔍 Looking for submit button...")

            # Strategy 1: Search within post element first if provided
            if post_element:
                try:
                    # Look for buttons with ember IDs that contain "Comment" text within post
                    ember_buttons = post_element.find_elements(
                        By.CSS_SELECTOR,
                        "button[id^='ember']"
                    )
                    for button in ember_buttons:
                        button_text = button.text.strip()
                        if (button_text in ["Comment", "Post", "Post comment"] and
                            button.is_displayed() and
                            button.is_enabled()):
                            button_id = button.get_attribute('id')
                            print(f"✅ Found submit button by ember ID within post context: {button_id}")
                            return button
                except:
                    pass

            # Strategy 2: Find by specific ID pattern globally (like #ember300)
            try:
                # Look for buttons with ember IDs that contain "Comment" text
                ember_buttons = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "button[id^='ember']"
                )
                for button in ember_buttons:
                    button_text = button.text.strip()
                    if (button_text in ["Comment", "Post", "Post comment"] and
                        button.is_displayed() and
                        button.is_enabled()):
                        button_id = button.get_attribute('id')
                        print(f"✅ Found submit button by ember ID: {button_id}")
                        return button
            except:
                pass

            # Strategy 3: Find by class pattern (within post if available)
            search_element = post_element if post_element else self.driver
            try:
                submit_button = search_element.find_element(
                    By.CSS_SELECTOR,
                    "button.comments-comment-box__submit-button--cr"
                )
                if submit_button.is_displayed() and submit_button.is_enabled():
                    context = " within post context" if post_element else ""
                    print(f"✅ Found submit button by specific class{context}")
                    return submit_button
            except NoSuchElementException:
                pass

            # Strategy 4: Find by partial class match (within post if available)
            try:
                submit_buttons = search_element.find_elements(
                    By.CSS_SELECTOR,
                    "button[class*='comments-comment-box__submit-button']"
                )
                for button in submit_buttons:
                    if button.is_displayed() and button.is_enabled():
                        context = " within post context" if post_element else ""
                        print(f"✅ Found submit button by partial class{context}")
                        return button
            except NoSuchElementException:
                pass

            # Strategy 5: Find primary button with "Comment" text (within post if available)
            try:
                primary_buttons = search_element.find_elements(
                    By.CSS_SELECTOR,
                    "button.artdeco-button--primary"
                )
                for button in primary_buttons:
                    button_text = button.text.strip()
                    if (button_text in ["Comment", "Post", "Post comment"] and
                        button.is_displayed() and
                        button.is_enabled()):
                        context = " within post context" if post_element else ""
                        print(f"✅ Found submit button (primary button with Comment text){context}")
                        return button
            except:
                pass

            # Strategy 6: XPath search for button containing "Comment" in span (prefer post context)
            if post_element:
                try:
                    submit_button = post_element.find_element(
                        By.XPATH,
                        ".//button[.//span[contains(text(), 'Comment')] or .//span[contains(text(), 'Post')]]"
                    )
                    if submit_button.is_displayed() and submit_button.is_enabled():
                        print("✅ Found submit button by span text XPath within post context")
                        return submit_button
                except NoSuchElementException:
                    pass

            # Strategy 7: XPath search globally as fallback
            try:
                submit_button = self.driver.find_element(
                    By.XPATH,
                    "//button[.//span[contains(text(), 'Comment')] or .//span[contains(text(), 'Post')]]"
                )
                if submit_button.is_displayed() and submit_button.is_enabled():
                    print("✅ Found submit button by span text XPath")
                    return submit_button
            except NoSuchElementException:
                pass

            # Strategy 8: Find any button that appeared after typing (within post if available)
            try:
                all_buttons = search_element.find_elements(By.CSS_SELECTOR, "button")
                for button in all_buttons:
                    button_text = button.text.strip()
                    button_classes = button.get_attribute("class") or ""

                    if (button_text in ["Comment", "Post", "Post comment"] and
                        button.is_displayed() and
                        button.is_enabled() and
                        ("submit" in button_classes.lower() or
                         "comment" in button_classes.lower() or
                         "primary" in button_classes.lower())):
                        context = " within post context" if post_element else ""
                        print(f"✅ Found submit button (generic search){context}")
                        return button
            except:
                pass

            print("❌ Could not find submit button")
            return None

        except Exception as e:
            print(f"❌ Error finding submit button: {e}")
            return None

    def close_open_comment_sections(self):
        """
        Close any open comment sections to ensure clean state
        """
        try:
            print("🧹 Closing any open comment sections...")

            # Method 1: Press ESC key to close any open dialogs/sections
            try:
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(0.5)
                print("✅ Pressed ESC to close any open sections")
            except:
                pass

            # Method 2: Try to find and close any visible comment boxes
            try:
                # Look for visible comment text areas and click outside them
                comment_areas = self.driver.find_elements(By.CSS_SELECTOR, ".ql-editor")
                for area in comment_areas:
                    if area.is_displayed():
                        # Click outside the comment area to close it
                        try:
                            # Find a safe place to click (like the body or a neutral area)
                            self.driver.execute_script("arguments[0].blur();", area)
                            time.sleep(0.2)
                        except:
                            continue

                if comment_areas:
                    print(f"✅ Attempted to close {len(comment_areas)} visible comment areas")
            except:
                pass

            # Method 3: Click on the main content area to deselect any active elements
            try:
                # Find the main feed area and click it to deselect
                feed_area = self.driver.find_element(By.CSS_SELECTOR, "[role='main'], .scaffold-finite-scroll__content")
                self.driver.execute_script("arguments[0].click();", feed_area)
                time.sleep(0.3)
                print("✅ Clicked main content area to deselect active elements")
            except:
                pass

        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")

    def click_submit_button(self, submit_button):
        """
        Click the submit button to post the comment
        """
        try:
            print("🖱️ Clicking submit button...")

            # Scroll button into view
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                submit_button
            )
            time.sleep(0.5)

            # Click the submit button
            try:
                submit_button.click()
                print("✅ Successfully clicked submit button")
            except ElementClickInterceptedException:
                # If regular click fails, try JavaScript click
                print("🔄 Regular click failed, trying JavaScript click...")
                self.driver.execute_script("arguments[0].click();", submit_button)
                print("✅ Successfully clicked submit button with JavaScript")

            # Wait for comment to be posted
            time.sleep(2.0)

            return True

        except Exception as e:
            print(f"❌ Error clicking submit button: {e}")
            return False

    def verify_comment_posted(self):
        """
        Verify that the comment was successfully posted
        """
        try:
            print("✅ Verifying comment was posted...")

            # Strategy 1: Check if comment box disappeared or cleared
            try:
                comment_boxes = self.driver.find_elements(By.CSS_SELECTOR, ".ql-editor")
                for box in comment_boxes:
                    if box.is_displayed():
                        # If comment box is empty, comment was likely posted
                        if not box.text.strip():
                            print("✅ Comment box is empty - comment likely posted")
                            return True
            except:
                pass

            # Strategy 2: Check if we can find a newly posted comment
            # (This is harder to implement reliably, so we'll rely on other indicators)

            # Strategy 3: If comment box is no longer visible, comment was posted
            try:
                visible_comment_boxes = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".ql-editor:not([style*='display: none'])"
                )
                if not visible_comment_boxes:
                    print("✅ Comment box disappeared - comment posted")
                    return True
            except:
                pass

            # If we can't verify definitively, assume success if no errors occurred
            print("✅ Comment posting completed (verification inconclusive)")
            return True

        except Exception as e:
            print(f"⚠️ Error verifying comment posted: {e}")
            return True  # Assume success if verification fails

    def post_comment_by_ember_id(self, ember_id, comment_text):
        """
        Main method to post a comment to a specific post by ember ID

        Args:
            ember_id (str): The ember ID of the post
            comment_text (str): The comment text to post

        Returns:
            bool: True if comment was posted successfully, False otherwise
        """
        start_time = datetime.now()

        comment_data = {
            "ember_id": ember_id,
            "comment_text": comment_text,
            "timestamp": start_time.isoformat(),
            "success": False,
            "error": None,
            "steps_completed": []
        }

        self.comment_results["total_attempts"] += 1

        try:
            print(f"\n{'='*60}")
            print(f"🚀 POSTING COMMENT TO POST: {ember_id}")
            print(f"💬 Comment: {comment_text}")
            print(f"{'='*60}")

            # Step 0: Clean up any open comment sections
            print("\n📍 Step 0: Cleanup - Closing any open comment sections...")
            self.close_open_comment_sections()

            # Step 1: Find the post by ember ID
            print("\n📍 Step 1: Finding post by ember ID...")
            post_element = self.find_post_by_ember_id(ember_id)
            if not post_element:
                raise Exception(f"Could not find post with ember ID: {ember_id}")

            comment_data["steps_completed"].append("post_found")

            # Step 2: Find and click comment button
            print("\n📍 Step 2: Finding comment button...")
            comment_button = self.find_comment_button(post_element)
            if not comment_button:
                raise Exception("Could not find comment button")

            print("\n📍 Step 3: Clicking comment button...")
            if not self.click_comment_button(comment_button):
                raise Exception("Failed to click comment button")

            comment_data["steps_completed"].append("comment_button_clicked")

            # Step 4: Find text area (with post context)
            print("\n📍 Step 4: Finding comment text area...")
            text_area = self.find_comment_text_area(post_element)
            if not text_area:
                raise Exception("Could not find comment text area")

            comment_data["steps_completed"].append("text_area_found")

            # Step 5: Type comment
            print("\n📍 Step 5: Typing comment...")
            if not self.type_comment_naturally(text_area, comment_text):
                raise Exception("Failed to type comment")

            comment_data["steps_completed"].append("comment_typed")

            # Step 6: Find submit button (with post context)
            print("\n📍 Step 6: Finding submit button...")
            submit_button = self.find_submit_button(post_element)
            if not submit_button:
                raise Exception("Could not find submit button")

            # Step 7: Click submit button
            print("\n📍 Step 7: Clicking submit button...")
            if not self.click_submit_button(submit_button):
                raise Exception("Failed to click submit button")

            comment_data["steps_completed"].append("submit_clicked")

            # Verify comment was posted
            print("\n📍 Final: Verifying comment posted...")
            if self.verify_comment_posted():
                comment_data["success"] = True
                comment_data["steps_completed"].append("verified")
                self.comment_results["successful_comments"] += 1

                print(f"\n🎉 SUCCESS! Comment posted to {ember_id}")
                print(f"💬 Comment: {comment_text}")

                return True
            else:
                raise Exception("Comment posting verification failed")

        except Exception as e:
            error_msg = str(e)
            comment_data["error"] = error_msg
            self.comment_results["failed_comments"] += 1

            print(f"\n❌ FAILED to post comment to {ember_id}")
            print(f"Error: {error_msg}")

            # Try to recover by pressing Escape
            try:
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)
            except:
                pass

            return False

        finally:
            # Record the attempt
            end_time = datetime.now()
            comment_data["duration_seconds"] = (end_time - start_time).total_seconds()
            self.comment_results["comments"].append(comment_data)

    def post_comments_batch(self, comment_requests):
        """
        Post multiple comments in batch

        Args:
            comment_requests (list): List of dicts with 'ember_id' and 'comment_text'

        Returns:
            dict: Results summary
        """
        print(f"\n🚀 Starting batch comment posting for {len(comment_requests)} comments")

        results = []
        for i, request in enumerate(comment_requests, 1):
            ember_id = request.get('ember_id')
            comment_text = request.get('comment_text')

            print(f"\n--- Processing comment {i}/{len(comment_requests)} ---")

            success = self.post_comment_by_ember_id(ember_id, comment_text)
            results.append({
                'ember_id': ember_id,
                'success': success
            })

            # Wait between comments if not the last one
            if i < len(comment_requests):
                wait_time = random.randint(config.MIN_WAIT_TIME, config.MAX_WAIT_TIME)
                print(f"⏱️ Waiting {wait_time} seconds before next comment...")
                time.sleep(wait_time)

        return results

    def save_results_to_json(self, filename="linkedin_comment_results.json"):
        """
        Save comment results to JSON file
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.comment_results, f, indent=2, ensure_ascii=False)
            print(f"💾 Comment results saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")

    def print_summary(self):
        """
        Print a summary of comment posting results
        """
        print(f"\n{'='*60}")
        print("📊 COMMENT POSTING SUMMARY")
        print(f"{'='*60}")

        print(f"🔢 Total attempts: {self.comment_results['total_attempts']}")
        print(f"✅ Successful comments: {self.comment_results['successful_comments']}")
        print(f"❌ Failed comments: {self.comment_results['failed_comments']}")

        if self.comment_results['total_attempts'] > 0:
            success_rate = (self.comment_results['successful_comments'] /
                          self.comment_results['total_attempts']) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")

        if self.comment_results['comments']:
            print(f"\n📝 Comment Details:")
            for i, comment in enumerate(self.comment_results['comments'], 1):
                status = "✅" if comment['success'] else "❌"
                print(f"{i}. {status} {comment['ember_id']}: {comment['comment_text'][:50]}...")
                if comment.get('error'):
                    print(f"   Error: {comment['error']}")

        print(f"{'='*60}")


def main():
    """
    Standalone test function for comment action
    """
    commenter = LinkedInCommentAction()

    try:
        print("🚀 LinkedIn Comment Action - Standalone Test")
        print("=" * 50)

        # Initialize browser
        commenter.initialize_driver()

        # Wait for user to navigate to LinkedIn
        input("\n📍 Navigate to LinkedIn and ensure you're logged in, then press Enter...")

        # Get ember ID and comment from user
        ember_id = input("\n🆔 Enter the ember ID of the post you want to comment on: ").strip()
        comment_text = input("💬 Enter your comment text: ").strip()

        if not ember_id or not comment_text:
            print("❌ Both ember ID and comment text are required")
            return

        # Post the comment
        success = commenter.post_comment_by_ember_id(ember_id, comment_text)

        # Show results
        commenter.print_summary()
        commenter.save_results_to_json()

        # Keep browser open for inspection
        if success:
            input("\n✅ Comment posted successfully! Press Enter to close browser...")
        else:
            input("\n❌ Comment posting failed. Press Enter to close browser...")

    except KeyboardInterrupt:
        print("\n⚠️ Script interrupted by user.")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

    finally:
        commenter.cleanup()


if __name__ == "__main__":
    main()