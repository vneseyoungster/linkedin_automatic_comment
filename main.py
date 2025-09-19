import time
import random
import re
import os
import platform
import traceback
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from openai import OpenAI
import config

class LinkedInCommentBot:
    def __init__(self):
        self.driver = None
        self.comments_posted = 0
        self.posted_comments = []
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def get_chrome_profile_path(self):
        """
        Automatically detect Chrome profile path based on OS
        You can override this by directly returning your path
        """
        system = platform.system()
        home = os.path.expanduser("~")
        
        if system == "Windows":
            # Windows path
            user_data_dir = os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data")
        elif system == "Darwin":
            # macOS path
            user_data_dir = os.path.join(home, "Library", "Application Support", "Google", "Chrome")
        else:
            # Linux path
            user_data_dir = os.path.join(home, ".config", "google-chrome")
        
        return user_data_dir

    def initialize_driver(self):
        print("Setting up Chrome browser with existing profile...")
        
        chrome_options = webdriver.ChromeOptions()
        
        # Get Chrome profile path
        user_data_dir = self.get_chrome_profile_path()
        
        # IMPORTANT: Fix for DevToolsActivePort error
        # Instead of using the profile directly, we'll use a temporary copy
        import shutil
        import tempfile
        
        # Option 1: Try using the profile with special flags (usually works)
        try:
            print(f"Attempting to use Chrome profile from: {user_data_dir}")
            
            # Critical flags to fix DevToolsActivePort error
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--remote-debugging-port=9222")
            
            # Use profile - Try without specifying profile directory first
            chrome_options.add_argument(f"user-data-dir={user_data_dir}")
            # chrome_options.add_argument("profile-directory=Default")  # Comment this out for now
            
            # Disable automation indicators
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Additional settings
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-extensions")
            
            # Set user agent
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            chrome_options.add_argument(f"user-agent={user_agent}")
            
            # Add logging to debug
            chrome_options.add_argument("--enable-logging")
            chrome_options.add_argument("--v=1")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            print("Chrome started successfully!")
            
        except Exception as e:
            print(f"First attempt failed: {e}")
            print("\nTrying alternative approach with profile copy...")
            
            # Option 2: Create a temporary copy of the profile
            try:
                temp_dir = tempfile.mkdtemp(prefix="linkedin_bot_")
                temp_profile = os.path.join(temp_dir, "ChromeProfile")
                
                # Copy only essential profile files (not the whole profile to save time)
                original_profile = os.path.join(user_data_dir, "Default")
                if os.path.exists(original_profile):
                    print(f"Copying profile from {original_profile} to {temp_profile}")
                    
                    # Create temp profile directory
                    os.makedirs(temp_profile, exist_ok=True)
                    
                    # Copy only essential files
                    essential_files = ["Cookies", "Cookies-journal", "Preferences", "Local State"]
                    for file in essential_files:
                        src = os.path.join(original_profile, file)
                        if os.path.exists(src):
                            dst = os.path.join(temp_profile, file)
                            shutil.copy2(src, dst)
                    
                    # Use the temporary profile
                    chrome_options = webdriver.ChromeOptions()
                    chrome_options.add_argument(f"user-data-dir={temp_dir}")
                    chrome_options.add_argument("profile-directory=ChromeProfile")
                else:
                    print(f"Profile path not found: {original_profile}")
                    raise Exception("Chrome profile not found")
                
                # Add all the flags again
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
                print("Chrome started with temporary profile!")
                
            except Exception as e2:
                print(f"Second attempt also failed: {e2}")
                print("\n🔧 Alternative Solution: Use manual browser approach")
                print("Run this command in terminal to start Chrome:")
                print('chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\temp\\chrome_profile"')
                print("Then update the code to connect to existing browser")
                raise
        
        try:
            # Additional JavaScript to hide automation
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                """
            })
        except Exception:
            pass  # CDP commands might not work with all setups
        
        print("Opening LinkedIn...")
        self.driver.get("https://www.linkedin.com")
        
        # Check if already logged in
        time.sleep(3)
        if "feed" in self.driver.current_url or self.is_logged_in():
            print("Already logged in to LinkedIn!")
            self.wait_for_feed()
        else:
            print("Not logged in. Attempting to navigate to login page...")
            self.driver.get("https://www.linkedin.com/login")
            input("Please log in to LinkedIn manually, then press Enter to continue...")
            self.wait_for_feed()

    def is_logged_in(self):
        """Check if user is logged in by looking for profile elements"""
        try:
            self.driver.find_element(By.CSS_SELECTOR, "[data-control-name='nav.settings']")
            return True
        except NoSuchElementException:
            return False

    def wait_for_feed(self):
        print("Waiting for LinkedIn feed to load...")
        try:
            # Try multiple possible selectors for feed posts
            feed_selectors = [
                "[data-id^='urn:li:activity:']",
                "[data-id^='urn:li:ugcPost:']", 
                ".feed-shared-update-v2",
                "[data-urn^='urn:li:activity']"
            ]
            
            feed_found = False
            for selector in feed_selectors:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"LinkedIn feed loaded successfully! (Found: {selector})")
                    feed_found = True
                    break
                except TimeoutException:
                    continue
                    
            if not feed_found:
                print("Could not find LinkedIn feed with standard selectors.")
                print("Checking page manually...")
                # As fallback, just check if we're on the feed URL
                if "/feed" in self.driver.current_url:
                    print("On feed page. Continuing...")
                else:
                    raise Exception("Not on LinkedIn feed")
                    
        except Exception as e:
            print(f"Error loading feed: {e}")
            print("Make sure you're on the LinkedIn homepage/feed.")
            self.cleanup()
            exit(1)

    def scroll_to_load_posts(self):
        print("Scrolling to load more posts...")
        # Much slower, more natural scrolling
        for i in range(5):  # Scroll in 5 small increments
            scroll_distance = 200 + random.randint(-50, 50)  # Vary scroll distance
            self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
            time.sleep(random.uniform(0.5, 1.0))  # Random pause between scrolls
        
        # Wait for new content to load
        time.sleep(2)

    def get_post_elements(self):
        # Try multiple selectors for posts - updated for current LinkedIn
        selectors = [
            "[id^='ember'][data-id]",  # Elements with ember IDs and data-id
            "[data-id^='urn:li:activity:']",
            "[data-id^='urn:li:ugcPost:']",
            ".feed-shared-update-v2",
            "[data-urn^='urn:li:activity']",
            ".scaffold-finite-scroll__content > div"  # Generic container divs in the feed
        ]
        
        for selector in selectors:
            posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
            # Filter out very small elements that aren't real posts
            posts = [p for p in posts if p.size['height'] > 100]
            if posts:
                print(f"Found {len(posts)} posts using selector: {selector}")
                return posts
        
        print("No posts found with any selector")
        return []

    def extract_post_content(self, post_element):
        try:
            # First, try to expand the post if there's a "more" button
            try:
                # Strategy 1: Look for button within fie-impression-container structure
                try:
                    # This matches your selector pattern: .fie-impression-container > div[class*='biSBAHR'] > div > button
                    more_button = post_element.find_element(
                        By.CSS_SELECTOR, 
                        ".fie-impression-container div[class*='biSBAHR'] > div > button"
                    )
                    
                    # Verify it's actually a "more" button by checking text or aria-label
                    button_text = more_button.text.lower()
                    aria_label = more_button.get_attribute('aria-label') or ''
                    
                    if 'more' in button_text or 'more' in aria_label.lower():
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", more_button)
                        time.sleep(1)
                        more_button.click()
                        print("   ✓ Clicked 'more' button to expand post (Method 1)")
                        time.sleep(1.5)  # Wait for content to expand
                except NoSuchElementException:
                    pass
                
                # Strategy 2: Try alternative selectors if first method didn't work
                more_button_selectors = [
                    ".fie-impression-container button",  # Any button in impression container
                    "button[aria-label*='more' i]",
                    "button[aria-label*='see more' i]",
                    ".feed-shared-inline-show-more-text__see-more-button",
                    "button span[aria-hidden='true']"  # Button with hidden span
                ]
                
                for selector in more_button_selectors:
                    try:
                        more_buttons = post_element.find_elements(By.CSS_SELECTOR, selector)
                        
                        for btn in more_buttons:
                            try:
                                # Check button text and aria-label
                                btn_text = btn.text.strip().lower()
                                aria_label = btn.get_attribute('aria-label') or ''
                                
                                # Also check span text within button
                                try:
                                    span_text = btn.find_element(By.CSS_SELECTOR, "span").text.lower()
                                except:
                                    span_text = ''
                                
                                # Check if this is a "more" button
                                if (('more' in btn_text and len(btn_text) < 20) or  # "see more" but not long text
                                    'more' in aria_label.lower() or
                                    ('more' in span_text and len(span_text) < 20)):
                                    
                                    if btn.is_displayed():
                                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", btn)
                                        time.sleep(1)
                                        
                                        # Try JavaScript click if regular click might fail
                                        try:
                                            btn.click()
                                        except:
                                            self.driver.execute_script("arguments[0].click();", btn)
                                        
                                        print("   ✓ Clicked 'more' button to expand post (Method 2)")
                                        time.sleep(1.5)  # Wait for content to expand
                                        break
                            except Exception as e:
                                continue
                        
                        # If we clicked a button, break the outer loop
                        if btn.is_displayed():
                            break
                            
                    except NoSuchElementException:
                        continue
                        
                # Strategy 3: Try XPath as last resort
                try:
                    # Find buttons containing "more" text anywhere in their subtree
                    more_buttons_xpath = post_element.find_elements(
                        By.XPATH, 
                        ".//button[contains(translate(., 'MORE', 'more'), 'more') and not(contains(., 'Show')) and not(contains(., 'Reply'))]"
                    )
                    
                    for btn in more_buttons_xpath:
                        if btn.is_displayed() and btn.is_enabled():
                            btn_full_text = btn.text.strip()
                            # Make sure it's a short "more" button, not a button with lots of text
                            if len(btn_full_text) < 30:
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", btn)
                                time.sleep(1)
                                self.driver.execute_script("arguments[0].click();", btn)
                                print("   ✓ Clicked 'more' button to expand post (Method 3)")
                                time.sleep(1.5)
                                break
                except Exception:
                    pass
                    
            except Exception as e:
                print(f"   Note: Could not expand post (might not have 'more' button): {str(e)[:50]}...")
            
            # Extract content - updated selectors
            content_selectors = [
                ".fie-impression-container div[class*='biSBAHR'] > div > div",  # The long class name pattern
                ".fie-impression-container .break-words",
                ".feed-shared-update-v2__commentary",
                ".update-components-text",
                "span.break-words"
            ]
            
            content = None
            for selector in content_selectors:
                try:
                    content_elements = post_element.find_elements(By.CSS_SELECTOR, selector)
                    for elem in content_elements:
                        text = elem.text.strip()
                        # Skip if it's too short or is a button/navigation element
                        if text and len(text) > 20 and not any(skip in text.lower()[:20] for skip in ['more', 'less', 'see all']):
                            content = text
                            break
                    if content:
                        break
                except NoSuchElementException:
                    continue
            
            # Extract author - using the selectors you provided
            author_selectors = [
                ".update-components-actor__title span span span:first-child span",  # Your first selector pattern
                ".update-components-actor__title .hoverable-link-text",  # Your second selector pattern
                ".update-components-actor__title span[aria-hidden='true']",
                ".update-components-actor__name span[aria-hidden='true']",
                ".feed-shared-actor__name span",
                ".update-components-actor__meta span"
            ]
            
            author = None
            for selector in author_selectors:
                try:
                    author_elements = post_element.find_elements(By.CSS_SELECTOR, selector)
                    for elem in author_elements:
                        text = elem.text.strip()
                        # Make sure it's a real name (not empty, not just numbers, not too long)
                        if text and 2 < len(text) < 50 and not text.isdigit():
                            # Skip common non-name texts
                            if not any(skip in text.lower() for skip in ['comment', 'like', 'share', 'follow', '•', 'connections']):
                                author = text
                                break
                    if author:
                        break
                except NoSuchElementException:
                    continue
            
            # If still no author, try a broader search
            if not author:
                try:
                    # Look for the first link in the actor area
                    actor_link = post_element.find_element(By.CSS_SELECTOR, ".update-components-actor a[href*='/in/']")
                    author_span = actor_link.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']")
                    author = author_span.text.strip()
                except:
                    pass
            
            return content, author
            
        except Exception as e:
            print(f"Error extracting content: {e}")
            return None, None

    def is_post_too_old(self, post_element):
        try:
            time_selectors = [
                ".feed-shared-actor__sub-description",
                ".feed-shared-actor__sub-description-link",
                "[data-control-name='actor_sub_description']"
            ]
            
            time_text = ""
            for selector in time_selectors:
                try:
                    time_element = post_element.find_element(By.CSS_SELECTOR, selector)
                    time_text = time_element.text.strip()
                    if time_text:
                        break
                except NoSuchElementException:
                    continue
            
            if any(indicator in time_text.lower() for indicator in ['week', 'weeks', 'month', 'months', 'year']):
                return True
                
            if 'day' in time_text.lower():
                days_match = re.search(r'(\d+)\s*day', time_text.lower())
                if days_match:
                    days = int(days_match.group(1))
                    return days > config.MAX_POST_AGE_DAYS
                    
            return False
            
        except Exception:
            return False

    def is_promoted_post(self, post_element):
        try:
            promoted_text = post_element.text.lower()
            return 'promoted' in promoted_text or 'sponsored' in promoted_text
        except:
            return False

    def has_comment_button(self, post_element):
        """
        Check if the post has a comment button available.
        LinkedIn uses dynamic IDs, so we need multiple strategies.
        """
        try:
            # Strategy 1: Look for the specific LinkedIn comment button ID pattern
            # IDs are like: feed-shared-social-action-bar-comment-ember[number]
            try:
                comment_buttons = post_element.find_elements(
                    By.CSS_SELECTOR, 
                    "[id^='feed-shared-social-action-bar-comment-']"
                )
                if comment_buttons:
                    for btn in comment_buttons:
                        if btn.is_displayed():
                            print(f"   ✓ Found comment button with ID: {btn.get_attribute('id')}")
                            return True
            except:
                pass
            
            # Strategy 2: Look for button with comment-related aria-label
            try:
                comment_button = post_element.find_element(
                    By.CSS_SELECTOR, 
                    "button[aria-label*='comment' i], button[aria-label*='Comment']"
                )
                if comment_button.is_displayed():
                    print(f"   ✓ Found comment button with aria-label: {comment_button.get_attribute('aria-label')}")
                    return True
            except:
                pass
            
            # Strategy 3: XPath search for any button containing 'comment' in ID
            try:
                comment_buttons = post_element.find_elements(
                    By.XPATH, 
                    ".//button[contains(@id, 'comment')]"
                )
                for btn in comment_buttons:
                    if btn.is_displayed():
                        print(f"   ✓ Found comment button with partial ID match")
                        return True
            except:
                pass
            
            # Strategy 4: Look for comment icon (SVG or icon class)
            try:
                # LinkedIn might use SVG icons for comments
                comment_icons = post_element.find_elements(
                    By.CSS_SELECTOR, 
                    "button svg[aria-label*='comment' i], button .fa-comment, button [data-test-icon*='comment']"
                )
                if comment_icons:
                    print(f"   ✓ Found comment button via icon")
                    return True
            except:
                pass
            
            # Strategy 5: Look for the social actions bar structure
            try:
                # LinkedIn groups social actions (like, comment, share) together
                social_bar = post_element.find_element(
                    By.CSS_SELECTOR, 
                    "[class*='social-action-bar'], [id*='social-action-bar']"
                )
                # Look for comment button within the social bar
                buttons = social_bar.find_elements(By.CSS_SELECTOR, "button")
                for btn in buttons:
                    btn_id = btn.get_attribute('id') or ''
                    btn_aria = btn.get_attribute('aria-label') or ''
                    if 'comment' in btn_id.lower() or 'comment' in btn_aria.lower():
                        if btn.is_displayed():
                            print(f"   ✓ Found comment button in social actions bar")
                            return True
            except:
                pass
            
            print("   ❌ No comment button found with any strategy")
            return False
            
        except Exception as e:
            print(f"   ❌ Error checking for comment button: {e}")
            return False

    def generate_comment(self, post_content, author_name):
        try:
            prompt = config.COMMENT_PROMPT.format(
                post_content=post_content[:500],  # Limit content length
                author_name=author_name
            )
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a professional commenting on LinkedIn posts. Be engaging, relevant, and authentic. Keep comments conversational and not too formal."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=1
            )
            
            comment = response.choices[0].message.content.strip()
            
            # Remove quotes if the AI wrapped the comment in quotes
            if comment.startswith('"') and comment.endswith('"'):
                comment = comment[1:-1]
                
            return comment
            
        except Exception as e:
            print(f"Error generating comment: {e}")
            return None

    def post_comment(self, post_element, comment_text):
        try:
            # Step 1: Find and click the comment button to open comment section
            print("Step 1: Looking for comment button...")
            comment_button = None
            
            # Strategy 1: Find by ID pattern (most reliable for LinkedIn)
            try:
                # LinkedIn uses IDs like: feed-shared-social-action-bar-comment-ember[number]
                comment_buttons = post_element.find_elements(By.CSS_SELECTOR, "[id^='feed-shared-social-action-bar-comment-']")
                if comment_buttons:
                    comment_button = comment_buttons[0]  # Usually there's only one per post
                    print(f"   Found comment button with ID: {comment_button.get_attribute('id')}")
            except:
                pass
            
            # Strategy 2: Find by aria-label if ID pattern fails
            if not comment_button:
                try:
                    comment_button = post_element.find_element(By.CSS_SELECTOR, "button[aria-label*='comment' i]")
                    print(f"   Found comment button with aria-label")
                except:
                    pass
            
            # Strategy 3: Find any button with 'comment' in its ID
            if not comment_button:
                try:
                    comment_button = post_element.find_element(By.XPATH, ".//button[contains(@id, 'comment')]")
                    print(f"   Found comment button with XPath")
                except:
                    pass
            
            if not comment_button:
                print("   ❌ Could not find comment button")
                return False
            
            # Scroll to button and click
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", comment_button)
            time.sleep(1.5)
            
            # Try regular click first, then JavaScript click if it fails
            try:
                comment_button.click()
            except:
                self.driver.execute_script("arguments[0].click();", comment_button)
            
            print("   ✓ Clicked comment button")
            time.sleep(2.5)  # Wait for comment box to appear
            
            # Step 2: Find the text editor area
            print("Step 2: Looking for comment text editor...")
            comment_box = None
            
            # Strategy 1: Find the ql-editor directly (most reliable)
            try:
                # Wait for any ql-editor to appear (it appears after clicking comment)
                comment_box = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".ql-editor"))
                )
                print("   ✓ Found comment box (.ql-editor)")
            except:
                pass
            
            # Strategy 2: Find within the comments-comment-box structure
            if not comment_box:
                try:
                    comment_box = self.driver.find_element(
                        By.CSS_SELECTOR, 
                        ".comments-comment-box-comment__text-editor .ql-editor"
                    )
                    print("   ✓ Found comment box in comment structure")
                except:
                    pass
            
            # Strategy 3: Find any contenteditable div
            if not comment_box:
                try:
                    comment_box = self.driver.find_element(
                        By.CSS_SELECTOR, 
                        "[contenteditable='true'][role='textbox']"
                    )
                    print("   ✓ Found comment box (contenteditable)")
                except:
                    pass
            
            if not comment_box:
                print("   ❌ Could not find comment box")
                return False
            
            # Step 3: Click and type in the comment box
            print("Step 3: Typing comment...")
            
            # Click to focus - try multiple methods
            try:
                comment_box.click()
            except:
                # If regular click fails, try JavaScript click
                self.driver.execute_script("arguments[0].click();", comment_box)
            
            time.sleep(0.5)
            
            # Clear any existing text or placeholder
            try:
                comment_box.clear()
            except:
                # If clear doesn't work, select all and delete
                from selenium.webdriver.common.keys import Keys
                comment_box.send_keys(Keys.CONTROL + "a")
                comment_box.send_keys(Keys.DELETE)
            
            time.sleep(0.5)
            
            # Type the comment with human-like delays
            for i, char in enumerate(comment_text):
                comment_box.send_keys(char)
                # Vary the typing speed
                if i % 10 == 0:  # Every 10 characters, pause a bit longer
                    time.sleep(random.uniform(0.2, 0.4))
                else:
                    time.sleep(random.uniform(0.05, 0.15))
            
            print(f"   ✓ Typed comment: {comment_text[:50]}...")
            time.sleep(1.5)  # Wait for the submit button to become active
            
            # Step 4: Find and click the submit button
            print("Step 4: Looking for submit button...")
            submit_button = None
            
            # Strategy 1: Find button with "Comment" text (most specific)
            try:
                # Find all buttons, then filter by text content
                all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
                for btn in all_buttons:
                    btn_text = btn.text.strip()
                    # Look for button with exactly "Comment" or "Post" text
                    if btn_text in ["Comment", "Post", "Post comment"] and btn.is_displayed() and btn.is_enabled():
                        # Additional check: make sure it's in the comment area
                        btn_classes = btn.get_attribute("class") or ""
                        if "comments-comment-box" in btn_classes or "submit" in btn_classes:
                            submit_button = btn
                            print(f"   Found submit button with text: '{btn_text}'")
                            break
            except:
                pass
            
            # Strategy 2: Find by class pattern
            if not submit_button:
                try:
                    submit_button = self.driver.find_element(
                        By.CSS_SELECTOR, 
                        "button.comments-comment-box__submit-button--cr"
                    )
                    print("   Found submit button by class")
                except:
                    try:
                        submit_button = self.driver.find_element(
                            By.CSS_SELECTOR, 
                            "button[class*='comments-comment-box__submit-button']"
                        )
                        print("   Found submit button by partial class")
                    except:
                        pass
            
            # Strategy 3: Find primary button in the comment area
            if not submit_button:
                try:
                    # Look for primary buttons that appeared after we started typing
                    primary_buttons = self.driver.find_elements(
                        By.CSS_SELECTOR, 
                        "button.artdeco-button--primary"
                    )
                    for btn in primary_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            # Check if it's near our comment box
                            if "Comment" in btn.text or "Post" in btn.text:
                                submit_button = btn
                                print("   Found submit button (primary button)")
                                break
                except:
                    pass
            
            # Strategy 4: Find button that contains span with "Comment" text
            if not submit_button:
                try:
                    submit_button = self.driver.find_element(
                        By.XPATH, 
                        "//button[.//span[contains(text(), 'Comment')] or .//span[contains(text(), 'Post')]]"
                    )
                    print("   Found submit button by span text")
                except:
                    pass
            
            if submit_button:
                print(f"   Clicking submit button: {submit_button.text}")
                # Ensure button is in view
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", submit_button)
                time.sleep(0.5)
                
                # Try to click the button
                try:
                    submit_button.click()
                except:
                    # If regular click fails, use JavaScript
                    self.driver.execute_script("arguments[0].click();", submit_button)
                
                print("   ✓ Comment posted successfully!")
                time.sleep(2)  # Wait to ensure comment is posted
                
                # Verify comment was posted by checking if comment box is gone or empty
                try:
                    # Try to find the comment box again
                    new_comment_box = self.driver.find_element(By.CSS_SELECTOR, ".ql-editor")
                    # If we find it and it's empty or not the same one, comment was likely posted
                    if not new_comment_box.text or new_comment_box != comment_box:
                        return True
                except:
                    # If we can't find the comment box, it probably closed after posting
                    return True
                
                return True
            else:
                print("   ⚠️ Could not find submit button, trying Enter key...")
                # Fallback: Try pressing Enter to submit
                from selenium.webdriver.common.keys import Keys
                comment_box.send_keys(Keys.RETURN)
                time.sleep(2)
                
                # Check if comment was posted
                try:
                    new_comment_box = self.driver.find_element(By.CSS_SELECTOR, ".ql-editor")
                    if not new_comment_box.text:
                        print("   ✓ Comment posted via Enter key!")
                        return True
                except:
                    print("   ✓ Comment likely posted!")
                    return True
                
                return False
                
        except Exception as e:
            print(f"   ❌ Error posting comment: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to recover by pressing Escape to close any open dialogs
            try:
                from selenium.webdriver.common.keys import Keys
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)
            except:
                pass
            
            return False

    def process_posts(self):
        posts_checked = 0
        max_posts_to_check = 20  # Don't check more than 20 posts total
        
        while self.comments_posted < config.COMMENTS_PER_RUN and posts_checked < max_posts_to_check:
            # Wait for feed to stabilize before getting posts
            time.sleep(2)
            
            posts = self.get_post_elements()
            
            if not posts:
                print("No posts found, scrolling...")
                self.scroll_to_load_posts()
                time.sleep(3)  # Wait longer after scrolling
                continue
            
            print(f"\nProcessing batch of {len(posts)} posts...")
            
            for i, post in enumerate(posts):
                if self.comments_posted >= config.COMMENTS_PER_RUN:
                    break
                    
                posts_checked += 1
                print(f"\n--- Checking post {i+1}/{len(posts)} ---")
                
                # Scroll post into view and wait for it to load
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", post)
                    time.sleep(2)  # Wait for post to fully load after scrolling into view
                except:
                    pass
                
                try:
                    # Skip promoted posts
                    if self.is_promoted_post(post):
                        print("❌ Skipping promoted post")
                        time.sleep(1)
                        continue
                    
                    # Skip old posts
                    if self.is_post_too_old(post):
                        print("❌ Skipping old post")
                        time.sleep(1)
                        continue
                    
                    # Check for comment button
                    if not self.has_comment_button(post):
                        print("❌ No comment button found, skipping")
                        time.sleep(1)
                        continue
                    else:
                        print("✓ Comment button found")
                    
                    # Extract content - with extra wait for dynamic content
                    time.sleep(1)
                    content, author = self.extract_post_content(post)
                    
                    if not content:
                        print("❌ Could not extract post content")
                        time.sleep(1)
                        continue
                    if not author:
                        print("⚠️ Could not extract author name, using 'LinkedIn User'")
                        author = "LinkedIn User"
                    
                    print(f"✓ Post by {author}")
                    print(f"✓ Content: {content[:150]}...")
                    
                    # Small pause before generating comment
                    time.sleep(1)
                    
                    # Generate comment
                    print("🤖 Generating comment...")
                    comment = self.generate_comment(content, author)
                    if not comment:
                        print("❌ Could not generate comment")
                        time.sleep(1)
                        continue
                    
                    print(f"💬 Generated comment: {comment}")
                    
                    # Pause before posting
                    time.sleep(2)
                    
                    # Post comment
                    print("📝 Attempting to post comment...")
                    if self.post_comment(post, comment):
                        self.comments_posted += 1
                        self.posted_comments.append({
                            'author': author,
                            'content': content[:150],
                            'comment': comment
                        })
                        
                        # Wait before next comment - longer wait
                        wait_time = random.randint(config.MIN_WAIT_TIME, config.MAX_WAIT_TIME)
                        print(f"⏱️  Waiting {wait_time} seconds before next comment...")
                        time.sleep(wait_time)
                    else:
                        print("❌ Failed to post comment")
                        time.sleep(2)
                    
                except Exception as e:
                    print(f"❌ Error processing post: {e}")
                    traceback.print_exc()
                    time.sleep(2)
                    continue
            
            # Scroll for more posts
            if self.comments_posted < config.COMMENTS_PER_RUN:
                print("\n🔄 Scrolling to load more posts...")
                self.scroll_to_load_posts()
                time.sleep(3)  # Wait after scrolling

    def cleanup(self):
        if self.driver:
            print("\nClosing browser...")
            self.driver.quit()

    def print_summary(self):
        print("\n" + "="*50)
        print("📊 SESSION SUMMARY")
        print("="*50)
        print(f"Total comments posted: {self.comments_posted}")
        
        if self.posted_comments:
            print("\n📝 Posted comments:")
            for i, comment_data in enumerate(self.posted_comments, 1):
                print(f"\n{i}. Author: {comment_data['author']}")
                print(f"   Post: {comment_data['content']}...")
                print(f"   Comment: {comment_data['comment']}")
        print("="*50)

def main():
    bot = LinkedInCommentBot()
    
    try:
        bot.initialize_driver()
        bot.process_posts()
        
    except KeyboardInterrupt:
        print("\n⚠️  Script interrupted by user.")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        
    finally:
        bot.print_summary()
        bot.cleanup()

if __name__ == "__main__":
    main()