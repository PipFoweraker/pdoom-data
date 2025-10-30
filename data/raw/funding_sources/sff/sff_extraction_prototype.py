#!/usr/bin/env python3
"""
SFF Grant Data Extraction Script (Prototype)

This is a prototype script for extracting grant data from the Survival and
Flourishing Fund website. The script needs to be updated with actual HTML
selectors once the website structure is verified.

Usage:
    python sff_extraction_prototype.py --output dumps/YYYY-MM-DD_HHMMSS/

Requirements:
    pip install requests beautifulsoup4 lxml
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required libraries not installed.")
    print("Please run: pip install requests beautifulsoup4 lxml")
    sys.exit(1)


# Configuration
BASE_URL = "https://survivalandflourishing.fund"
GRANTS_PAGE = "/grants"  # Update with actual grants page URL
REQUEST_DELAY = 2  # Seconds between requests (respectful crawling)
USER_AGENT = "pdoom-data-extractor/1.0 (Educational Research; +https://github.com/PipFoweraker/pdoom-data)"


def fetch_page(url: str) -> Optional[BeautifulSoup]:
    """
    Fetch and parse a webpage
    
    Args:
        url: Full URL to fetch
    
    Returns:
        BeautifulSoup object or None if fetch failed
    """
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'lxml')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None


def extract_grants_from_page(soup: BeautifulSoup, page_url: str) -> List[Dict]:
    """
    Extract grant data from a grants listing page
    
    Args:
        soup: BeautifulSoup object of the page
        page_url: URL of the page being parsed
    
    Returns:
        List of grant dictionaries
    
    Note:
        CSS selectors and extraction logic need to be updated based on
        actual website structure. Current implementation is a template.
    """
    grants = []
    
    # TODO: Update these selectors based on actual HTML structure
    # Example selectors (to be replaced):
    grant_elements = soup.find_all('div', class_='grant-item')
    
    for idx, element in enumerate(grant_elements):
        try:
            # TODO: Update extraction logic for each field
            # These are placeholder examples:
            
            recipient_elem = element.find('h3', class_='recipient-name')
            recipient_name = recipient_elem.text.strip() if recipient_elem else None
            
            amount_elem = element.find('span', class_='amount')
            amount_text = amount_elem.text.strip() if amount_elem else None
            amount = parse_amount(amount_text) if amount_text else None
            
            date_elem = element.find('time', class_='grant-date')
            date_text = date_elem.get('datetime') or date_elem.text.strip() if date_elem else None
            grant_date = parse_date(date_text) if date_text else None
            
            desc_elem = element.find('p', class_='description')
            description = desc_elem.text.strip() if desc_elem else None
            
            focus_elem = element.find('span', class_='focus-area')
            focus_area = focus_elem.text.strip() if focus_elem else None
            
            link_elem = element.find('a', href=True)
            source_url = link_elem.get('href') if link_elem else page_url
            if source_url and not source_url.startswith('http'):
                source_url = f"{BASE_URL}{source_url}"
            
            # Generate grant ID
            grant_id = f"SFF-{grant_date[:4] if grant_date else 'UNKN'}-{idx+1:03d}"
            
            grant = {
                'grant_id': grant_id,
                'source': 'sff',
                'recipient_name': recipient_name,
                'recipient_type': infer_recipient_type(recipient_name),
                'amount': amount,
                'currency': 'USD',
                'grant_date': grant_date,
                'grant_type': infer_grant_type(description, focus_area),
                'focus_area': focus_area,
                'description': description,
                'source_url': source_url,
                'extracted_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            
            grants.append(grant)
            
        except Exception as e:
            print(f"Error parsing grant element {idx}: {e}", file=sys.stderr)
            continue
    
    return grants


def parse_amount(amount_text: str) -> Optional[int]:
    """
    Parse amount from text (e.g., '$500,000' or '500K')
    
    Args:
        amount_text: Text containing amount
    
    Returns:
        Amount as integer or None
    """
    if not amount_text:
        return None
    
    # Remove currency symbols and whitespace
    text = amount_text.replace('$', '').replace(',', '').strip()
    
    # Handle K/M suffixes
    multiplier = 1
    if text.endswith('K') or text.endswith('k'):
        multiplier = 1000
        text = text[:-1]
    elif text.endswith('M') or text.endswith('m'):
        multiplier = 1000000
        text = text[:-1]
    
    try:
        return int(float(text) * multiplier)
    except ValueError:
        return None


def parse_date(date_text: str) -> Optional[str]:
    """
    Parse date to ISO 8601 format (YYYY-MM-DD)
    
    Args:
        date_text: Date text in various formats
    
    Returns:
        ISO 8601 date string or None
    """
    if not date_text:
        return None
    
    # Try various date formats
    formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%B %d, %Y',
        '%b %d, %Y',
        '%d %B %Y',
        '%d %b %Y',
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_text.strip(), fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None


def infer_recipient_type(recipient_name: Optional[str]) -> str:
    """
    Infer if recipient is organization or individual
    
    Args:
        recipient_name: Name of recipient
    
    Returns:
        'organization' or 'individual'
    """
    if not recipient_name:
        return 'unknown'
    
    # Simple heuristic: check for common org indicators
    org_indicators = ['Inc', 'LLC', 'Ltd', 'Foundation', 'Institute', 
                      'Center', 'Lab', 'University', 'College', 'Fund']
    
    for indicator in org_indicators:
        if indicator in recipient_name:
            return 'organization'
    
    # Check if name has typical person name structure (first last)
    parts = recipient_name.split()
    if len(parts) >= 2 and not any(char.isdigit() for char in recipient_name):
        return 'individual'
    
    return 'organization'  # Default to organization


def infer_grant_type(description: Optional[str], focus_area: Optional[str]) -> str:
    """
    Infer grant type from description and focus area
    
    Args:
        description: Grant description
        focus_area: Grant focus area
    
    Returns:
        Grant type string
    """
    text = f"{description or ''} {focus_area or ''}".lower()
    
    if 'fellowship' in text or 'fellow' in text:
        return 'Individual Fellowship'
    elif 'research' in text:
        return 'Research Grant'
    elif 'general' in text or 'operational' in text or 'support' in text:
        return 'General Support'
    elif 'project' in text:
        return 'Project Grant'
    
    return 'General Grant'


def get_all_pages() -> List[str]:
    """
    Get list of all grant page URLs (handle pagination)
    
    Returns:
        List of page URLs to scrape
    
    Note:
        This needs to be updated based on actual pagination structure
    """
    # TODO: Implement pagination discovery
    # For now, return just the main grants page
    return [f"{BASE_URL}{GRANTS_PAGE}"]


def scrape_all_grants() -> List[Dict]:
    """
    Scrape all grants from all pages
    
    Returns:
        List of all grant dictionaries
    """
    all_grants = []
    pages = get_all_pages()
    
    print(f"Found {len(pages)} page(s) to scrape")
    
    for page_num, page_url in enumerate(pages, 1):
        print(f"Scraping page {page_num}/{len(pages)}: {page_url}")
        
        soup = fetch_page(page_url)
        if not soup:
            print(f"Failed to fetch page: {page_url}", file=sys.stderr)
            continue
        
        grants = extract_grants_from_page(soup, page_url)
        print(f"  Extracted {len(grants)} grants")
        all_grants.extend(grants)
        
        # Respectful delay between pages
        if page_num < len(pages):
            time.sleep(REQUEST_DELAY)
    
    return all_grants


def save_grants(grants: List[Dict], output_dir: Path):
    """
    Save grants to JSON file and update metadata
    
    Args:
        grants: List of grant dictionaries
        output_dir: Directory to save files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save data
    data_file = output_dir / 'data.json'
    with open(data_file, 'w', encoding='ascii') as f:
        json.dump(grants, f, indent=2, ensure_ascii=True)
    
    print(f"Saved {len(grants)} grants to {data_file}")
    
    # Update metadata
    metadata_file = output_dir / '_metadata.json'
    metadata = {
        'extraction_date': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'source_name': 'sff',
        'source_url': BASE_URL,
        'extraction_method': 'web_scrape',
        'extractor_version': '1.0.0',
        'data_format': 'json',
        'record_count': len(grants),
        'extraction_notes': 'Automated extraction from SFF website',
        'fields_extracted': list(grants[0].keys()) if grants else [],
        'extraction_status': 'complete'
    }
    
    with open(metadata_file, 'w', encoding='ascii') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=True)
    
    print(f"Updated metadata: {metadata_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Extract grant data from Survival and Flourishing Fund'
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output directory for extracted data'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test extraction without saving data'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SFF Grant Data Extraction")
    print("=" * 60)
    print()
    print("WARNING: This is a prototype script.")
    print("HTML selectors need to be updated based on actual website structure.")
    print()
    
    # Scrape grants
    try:
        grants = scrape_all_grants()
        
        print()
        print(f"Total grants extracted: {len(grants)}")
        
        if grants and not args.dry_run:
            save_grants(grants, args.output)
            print()
            print("Extraction complete!")
        elif not grants:
            print("No grants found. Check HTML selectors and website structure.")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\nExtraction interrupted by user")
        return 1
    except Exception as e:
        print(f"Error during extraction: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
