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
        self.driver.get("https://www.linkedin.com/login")

        # Wait for manual login
        input("Please log in to LinkedIn manually, then press Enter to continue...")
        self.wait_for_feed()

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

    def cleanup(self):
        if self.driver:
            print("\nClosing browser...")
            self.driver.quit()

def main():
    bot = LinkedInCommentBot()

    try:
        bot.initialize_driver()
        # Wait for LinkedIn to load
        time.sleep(5)
        print("LinkedIn page loaded successfully!")

    except KeyboardInterrupt:
        print("\n⚠️  Script interrupted by user.")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

    finally:
        bot.cleanup()

if __name__ == "__main__":
    main()