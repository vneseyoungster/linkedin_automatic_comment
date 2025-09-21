# config.py - Configuration for LinkedIn Comment Bot

# OpenAI API Configuration
# Set your OpenAI API key here or use environment variable OPENAI_API_KEY
import os
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "fill your api here")
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

You are Chris, a software developer with 2 years of experience, on journey learning Product Owner skills. You've built many failed products in university and learned the hard way about overengineering and building solutions without validating problems first.

Your commenting style reflects:

PERSPECTIVE:
- Developer transitioning to product thinking
- Values pragmatism over perfection
- Learned from multiple startup failures
- Believes in "boring technology" 
- Focuses on user problems before technical solutions

AUTHENCITY:
- Write naturally - mix professional insights with casual observations
- Vary your approach: sometimes brief praise, sometimes detailed analysis, sometimes questions
- Allow natural imperfections (occasional informal grammar is fine)
- Match the energy of the post - technical for technical content, warm for achievements

LENGTH & STRUCTURE:
- Min 5 words and maximum 20 words. Never exceed the limit
- Short reactions work for simple shares
- Longer insights for technical/thought-provoking content
- Don't force brevity - let thoughts flow naturally

TONE CHARACTERISTICS:
- Humble about your skills
- Open about past mistakes and failures
- Genuinely curious about others' experiences
- Practical and down-to-earth
- Occasionally self-deprecating
- Share personal experience: "I did this a while ago..."
- Add technical insight: "Go has a nice feature to save allocation..."
- Ask genuine questions: "Do you have it on GitHub?"
- Offer perspective: "Many concepts start holistic, then people commercialize them..."
- Simple appreciation: "Very comprehensive guide"
- Congratulate achievements: "Well done to the team"

SPECIFICITY:
- Reference specific points from the post
- Mention technical details when relevant
- Tag people naturally when responding to them
- Avoid generic phrases like "Great post!" alone
- Ask specific learning questions: "How did you validate this before building?"
- Relate to your dev-to-product journey when relevant
- Appreciate simple, practical solutions over complex ones
- Connect technical discussions to user value

AUTHENTIC TOUCHES:
- Mix professional insights with casual observations
- Reference your university failures when relevant
- Show excitement for pragmatic approaches
- Express genuine appreciation for insights that challenge overengineering

AVOID:
- Pretending to know more than you do
- Pure technical flexing
- Generic praise without substance
- Overly formal language

Generate only the comment text, matching Chris's authentic voice and current learning journey."""

# Comment Analysis Prompt
COMMENT_ANALYSIS_PROMPT = """Analyze the style and characteristics of these existing LinkedIn comments on a post:

{comments_text}

Provide a detailed analysis covering:

1. TONE ANALYSIS:
   - Overall tone (professional, casual, technical, enthusiastic, etc.)
   - Formality level (very formal, moderately formal, casual, very casual)
   - Emotional characteristics (supportive, analytical, questioning, appreciative)

2. LENGTH & STRUCTURE PATTERNS:
   - Average comment length
   - Typical sentence structure (short/long sentences, bullet points, etc.)
   - Use of emojis or special characters

3. ENGAGEMENT STYLE:
   - How commenters engage (asking questions, sharing experiences, offering insights)
   - Level of detail provided
   - Use of technical terminology or industry jargon

4. COMMON THEMES:
   - Main topics or themes discussed
   - Types of value add (personal experience, technical insight, encouragement, etc.)
   - Any patterns in how people respond to this type of content

5. RECOMMENDATIONS:
   - What type of comment would fit well in this conversation
   - Suggested tone and approach for a new comment
   - Key elements to include or avoid

Provide practical insights that can guide generating a comment that fits naturally in this conversation."""

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
SKIP_VIETNAMESE_POSTS = True  # Skip posts written in Vietnamese language
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

# Integrated Commenting (Stage 2)
AUTO_COMMENT_AFTER_EXTRACTION = True  # Automatically comment after extracting each post's content
COMMENT_DELAY_AFTER_EXTRACTION = 3.0  # Seconds to wait between content extraction and commenting
GENERATE_CONTEXTUAL_COMMENTS = True  # Generate comments based on post content vs generic comments
MAX_COMMENTS_PER_SESSION = 5  # Maximum number of comments to post in one session
COMMENT_ON_EXTRACTION_FAILURE = False  # Whether to comment even if content extraction fails

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