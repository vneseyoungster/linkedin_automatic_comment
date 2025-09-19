# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is a LinkedIn automation system built with **inheritance-based architecture** where specialized scanners extend a base browser automation class.

### Core Architecture Pattern

All classes inherit from `LinkedInCommentBot` (chrome_initialize.py):
- `LinkedInAuthorScanner` - Extracts author information
- `LinkedInSponsorScanner` - Detects sponsored posts
- `LinkedInComprehensiveScanner` - Combines all functionality
- Original `LinkedInCommentBot` (main.py) - Full comment automation

### Key Design Principles

1. **Shared Browser Session**: All classes use the same Chrome profile and anti-detection setup
2. **Ember.js Element Targeting**: LinkedIn uses dynamic Ember IDs that must be handled with multiple CSS selector strategies
3. **Progressive Enhancement**: Each scanner builds on the base functionality
4. **Defensive CSS Selection**: Multiple selector fallbacks for LinkedIn's dynamic DOM

### Critical Implementation Details

**Chrome Profile Handling**: The system uses existing Chrome profiles to maintain login sessions. Profile loading has two fallback strategies (direct profile use → temporary profile copy) to handle DevToolsActivePort errors.

**LinkedIn DOM Navigation**: Posts are identified through `[id^='ember']` selectors, and content extraction requires multiple CSS selector strategies due to LinkedIn's dynamic class names.

**Anti-Detection**: Includes user agent spoofing, automation flag removal, and CDP commands to avoid bot detection.

## Common Development Commands

### Setup and Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# The system automatically installs ChromeDriver via webdriver-manager
```

### Running the System

```bash
# Primary comprehensive scanner (recommended)
python test.py

# Individual component testing
python linkedin_content_loading.py      # Author extraction only
python linkedin_sponsor_scanner.py      # Sponsor detection only
python main.py                          # Full comment automation
```

### Configuration

Edit `config.py` for:
- OpenAI API key
- Comment generation parameters
- Rate limiting settings
- Post filtering criteria

## Key Selector Patterns for LinkedIn

When working with LinkedIn's DOM, use these proven selector strategies:

**Author Extraction**:
```css
.update-components-actor__title span.hoverable-link-text span span:first-child
.update-components-actor__title .hoverable-link-text
.update-components-actor__title span[aria-hidden='true']
```

**Comment Button Detection**:
```css
[id^='feed-shared-social-action-bar-comment-']
button[aria-label*='comment' i]
```

**Content Extraction**:
```css
.fie-impression-container div[class*='biSBAHR'] > div > div
.fie-impression-container .break-words
```

**Expand Post Buttons**:
```css
.fie-impression-container div[class*='biSBAHR'] > div > button
button[aria-label*='more' i]
```

## Testing and Development Workflow

1. **Start with test.py** - It provides comprehensive scanning without side effects
2. **Use JSON output** - All scanners export structured data for analysis
3. **Monitor console output** - Detailed logging shows which selectors work
4. **Test incremental changes** - LinkedIn's DOM changes frequently

### Output Files Generated
- `linkedin_comprehensive_scan.json` - Complete scan results (test.py)
- `linkedin_authors.json` - Author-only data (linkedin_content_loading.py)
- `sponsored_ember_ids.json` - Sponsor post IDs (linkedin_sponsor_scanner.py)

## Working with LinkedIn's Dynamic DOM

LinkedIn uses Ember.js with:
- Dynamic class names that change between sessions
- Ember IDs that are reliable but unpredictable
- Progressive content loading requiring scroll-to-load patterns
- Anti-automation measures requiring careful timing

**Critical timing considerations**:
- Wait 2-3 seconds after page load before DOM queries
- Scroll elements into view before interaction
- Use 1.5-2 second delays after clicking "more" buttons
- Allow content expansion time before text extraction

## Security and Rate Limiting

The system includes built-in protections:
- Human-like scrolling patterns with random delays
- Natural typing simulation (50-150ms between characters)
- Configurable wait times between actions (30-60 seconds default)
- Chrome profile isolation to maintain separate sessions

**Important**: Never commit the `config.py` file with real API keys. Use environment variables in production.