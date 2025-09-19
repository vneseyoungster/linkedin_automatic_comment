# config.py - Configuration for LinkedIn Comment Bot

# OpenAI API Configuration

# Commenting Configuration
COMMENTS_PER_RUN = 1  # Number of comments to post per session
MIN_WAIT_TIME = 30  # Minimum seconds to wait between comments
MAX_WAIT_TIME = 60  # Maximum seconds to wait between comments

# Post Filtering
MAX_POST_AGE_DAYS = 3  # Skip posts older than this many days

# Comment Generation Prompt
COMMENT_PROMPT = """Generate a professional LinkedIn comment for this post. 

Post by {author_name}: 
{post_content}

Guidelines:
- Be engaging and add value to the conversation
- Keep it under 100 words
- Be authentic and conversational, not overly formal
- If it's an achievement, congratulate them
- If it's a question, provide helpful insights
- If it's an article/share, add a thoughtful perspective
- Don't use too many emojis (max 1-2 if appropriate)
- Don't be generic - reference specific points from the post

Generate only the comment text, nothing else."""

# ========== CONTENT EXTRACTION CONFIGURATION ==========

# Post Limits
MAX_POSTS_TO_PROCESS = 10  # Maximum number of posts to extract content from (0 = no limit)
MAX_POSTS_TO_SCAN = 0  # Maximum posts to scan in Stage 1 (0 = scan all available)

# Content Extraction Behavior
AUTO_EXPAND_READ_MORE = True  # Automatically click "Read More" buttons
SKIP_SHORT_POSTS = True  # Skip posts with content shorter than MIN_CONTENT_LENGTH
MIN_CONTENT_LENGTH = 50  # Minimum content length in characters to consider
MAX_CONTENT_LENGTH = 5000  # Maximum content length to extract (longer posts will be truncated)

# Timing Configuration
DELAY_BETWEEN_POSTS = 1.5  # Seconds to wait between processing posts
DELAY_AFTER_READ_MORE = 2.0  # Seconds to wait after clicking Read More button
SCROLL_DELAY = 1.0  # Seconds to wait after scrolling to element

# Filtering Options
EXTRACT_FROM_SPONSORED = False  # Whether to extract content from sponsored posts
SKIP_VIDEO_POSTS = True  # Skip posts that are primarily video content
SKIP_IMAGE_ONLY_POSTS = True  # Skip posts that are primarily images without text

# Author Filtering
EXTRACT_FROM_SPECIFIC_AUTHORS = []  # List of author names to extract from (empty = all authors)
SKIP_AUTHORS = []  # List of author names to skip (empty = don't skip any)

# Example:
# EXTRACT_FROM_SPECIFIC_AUTHORS = ["John Doe", "Jane Smith"]  # Only extract from these authors
# SKIP_AUTHORS = ["Spam Account", "Bot User"]  # Skip these authors

# Content Type Filtering
EXTRACT_CONTENT_TYPES = [
    "text",      # Regular text posts
    "article",   # Shared articles with commentary
    "poll",      # Poll posts
    "document"   # Document shares with text
]

# Skip these content types:
SKIP_CONTENT_TYPES = [
    "video_only",    # Video-only posts without substantial text
    "image_only",    # Image-only posts without text
    "job_posting",   # Job postings
    "event"          # Event posts
]

# Output Configuration
SAVE_CONTENT_INCREMENTALLY = True  # Save results after each post (useful for large batches)
INCLUDE_POST_METADATA = True  # Include post timestamps, engagement metrics if available
EXPORT_TO_CSV = False  # Also export results to CSV format
EXPORT_TO_TXT = False  # Also export content to separate text files

# File Naming
CONTENT_EXTRACTION_FILENAME = "linkedin_content_extraction.json"
CSV_EXPORT_FILENAME = "linkedin_content_export.csv"
TXT_EXPORT_DIRECTORY = "extracted_content_txt"  # Directory for individual text files

# Error Handling
MAX_RETRIES_PER_POST = 2  # Number of times to retry extracting content from a failed post
CONTINUE_ON_ERROR = True  # Continue processing other posts if one fails
LOG_ERRORS_TO_FILE = True  # Save detailed error logs to file
ERROR_LOG_FILENAME = "content_extraction_errors.log"

# Advanced Options
USE_SELENIUM_WAIT = True  # Use explicit waits for better reliability
WAIT_TIMEOUT = 10  # Maximum seconds to wait for elements to load
HEADLESS_MODE = False  # Run browser in headless mode (not recommended for LinkedIn)
SAVE_SCREENSHOTS_ON_ERROR = False  # Save screenshot when content extraction fails

# Stage 2 Automation
AUTO_START_STAGE_2 = False  # Automatically start Stage 2 without user prompt
SKIP_STAGE_2_PROMPT = False  # Skip the Stage 2 confirmation prompt entirely

# Performance Settings
BATCH_SIZE = 5  # Process posts in batches (0 = process all at once)
MEMORY_CLEANUP_INTERVAL = 20  # Clear browser cache every N posts

# ========== VALIDATION RULES ==========
def validate_config():
    """Validate configuration settings and provide warnings for invalid values"""
    warnings = []

    if MAX_POSTS_TO_PROCESS < 0:
        warnings.append("MAX_POSTS_TO_PROCESS cannot be negative. Setting to 0 (no limit).")
        globals()['MAX_POSTS_TO_PROCESS'] = 0

    if MIN_CONTENT_LENGTH < 10:
        warnings.append("MIN_CONTENT_LENGTH is very low. Consider setting to at least 20 characters.")

    if DELAY_BETWEEN_POSTS < 0.5:
        warnings.append("DELAY_BETWEEN_POSTS is very low. This may trigger rate limiting.")

    if MAX_POSTS_TO_PROCESS > 100 and not SAVE_CONTENT_INCREMENTALLY:
        warnings.append("Processing many posts without incremental saving may cause data loss.")

    if EXTRACT_FROM_SPECIFIC_AUTHORS and SKIP_AUTHORS:
        common_authors = set(EXTRACT_FROM_SPECIFIC_AUTHORS) & set(SKIP_AUTHORS)
        if common_authors:
            warnings.append(f"Authors in both EXTRACT_FROM_SPECIFIC_AUTHORS and SKIP_AUTHORS: {common_authors}")

    return warnings

# ========== PRESETS ==========
def apply_preset(preset_name):
    """Apply predefined configuration presets"""
    global MAX_POSTS_TO_PROCESS, DELAY_BETWEEN_POSTS, AUTO_START_STAGE_2

    if preset_name == "quick_test":
        MAX_POSTS_TO_PROCESS = 5
        DELAY_BETWEEN_POSTS = 1.0
        AUTO_START_STAGE_2 = True
        print("Applied 'quick_test' preset: 5 posts, fast processing")

    elif preset_name == "small_batch":
        MAX_POSTS_TO_PROCESS = 10
        DELAY_BETWEEN_POSTS = 1.5
        AUTO_START_STAGE_2 = False
        print("Applied 'small_batch' preset: 10 posts, normal speed")

    elif preset_name == "large_batch":
        MAX_POSTS_TO_PROCESS = 50
        DELAY_BETWEEN_POSTS = 2.0
        SAVE_CONTENT_INCREMENTALLY = True
        print("Applied 'large_batch' preset: 50 posts, slower speed, incremental saving")

    elif preset_name == "conservative":
        MAX_POSTS_TO_PROCESS = 20
        DELAY_BETWEEN_POSTS = 3.0
        DELAY_AFTER_READ_MORE = 3.0
        CONTINUE_ON_ERROR = True
        print("Applied 'conservative' preset: 20 posts, slow and careful processing")

    else:
        print(f"Unknown preset: {preset_name}")
        print("Available presets: 'quick_test', 'small_batch', 'large_batch', 'conservative'")

# Optional: Specific Chrome Profile Settings
# Uncomment and customize if needed
# CHROME_USER_DATA_DIR = r"C:\Users\YourName\AppData\Local\Google\Chrome\User Data"
# CHROME_PROFILE = "Profile 1"  # or "Default"

# ========== USAGE EXAMPLES ==========
"""
USAGE EXAMPLES:

1. Extract content from 10 posts only:
   MAX_POSTS_TO_PROCESS = 10

2. Extract only from specific authors:
   EXTRACT_FROM_SPECIFIC_AUTHORS = ["John Doe", "Jane Smith"]

3. Skip sponsored posts:
   EXTRACT_FROM_SPONSORED = False

4. Conservative processing (slower but more reliable):
   apply_preset("conservative")

5. Quick test with 5 posts:
   apply_preset("quick_test")

6. Process all available posts:
   MAX_POSTS_TO_PROCESS = 0

7. Save to CSV as well:
   EXPORT_TO_CSV = True

8. Auto-start Stage 2 without prompt:
   AUTO_START_STAGE_2 = True
"""