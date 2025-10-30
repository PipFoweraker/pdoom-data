SFF Website Screenshots
========================

Investigation Date: 2025-10-30

Note: Due to network access restrictions during the investigation, screenshots
could not be captured. This file serves as a placeholder and documents what
screenshots should be captured when website access is available.

=== REQUIRED SCREENSHOTS ===

1. homepage_overview.png
   - Main landing page of survivalandflourishing.fund
   - Shows navigation structure
   - Captures overall site design

2. grants_database_page.png
   - Main grants or portfolio listing page
   - Shows how grants are displayed (table, cards, list)
   - Captures pagination controls if present

3. individual_grant_page.png
   - Example of a single grant detail page
   - Shows all available fields for a grant
   - Captures URL structure

4. grants_search_filters.png
   - Any search or filter functionality
   - Shows available filtering options
   - Captures sort options

5. developer_tools_network.png
   - Browser DevTools Network tab
   - Shows AJAX calls or API endpoints if any
   - Captures data loading mechanism

6. page_source_sample.png
   - View of HTML source structure
   - Shows grant data in HTML
   - Captures CSS classes and structure

=== SCREENSHOT CAPTURE INSTRUCTIONS ===

When capturing screenshots:

1. Use high resolution (1920x1080 or higher)
2. Capture full page when possible
3. Include browser address bar to show URL
4. Save as PNG format
5. Name files descriptively
6. Include date in filename if site changes frequently

Example naming: sff_grants_page_2025-10-30.png

=== ALTERNATIVE DOCUMENTATION ===

If screenshots cannot be captured, document instead:

1. URL structure and navigation
2. HTML structure (save sample HTML files)
3. CSS selectors for key elements
4. JavaScript behavior descriptions
5. Data location and format notes

Save HTML samples to: manual/html_samples/

=== CAPTURING PROCESS ===

Tools to use:
- Browser built-in screenshot (F12 DevTools)
- Browser extensions (Full Page Screen Capture)
- Command line tools (wkhtmltoimage, puppeteer)
- Python libraries (selenium, playwright)

Example with playwright:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://survivalandflourishing.fund/')
    page.screenshot(path='screenshots/homepage.png', full_page=True)
    browser.close()
```

=== STATUS ===

Screenshots captured: 0 / 6
HTML samples saved: 0
Network traces saved: 0

Reason: Network access blocked during investigation

=== NEXT STEPS ===

1. Gain access to survivalandflourishing.fund
2. Capture all required screenshots
3. Save HTML samples of key pages
4. Document actual website structure
5. Update investigation report with real observations

---
End of Screenshot Documentation
