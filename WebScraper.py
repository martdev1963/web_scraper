#!/usr/bin/env python3
"""
---------------------------------------------------------------------------------------------------------------
Web Scraper App
A comprehensive web scraper for extracting data from websites
https://www.geeksforgeeks.org/linux-unix/linux-commands-cheat-sheet/
https://chatgpt.com/c/68569ce9-f6d4-8009-aaa3-d0449cff32dc
---------------------------------------------------------------------------------------------------------------
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import argparse
import sys
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any
import re
import os
from datetime import datetime

#from selenium import webdriver
#from selenium.webdriver.chrome.options import Options

# Then use:
#options = webdriver.ChromeOptions()  # Instead of just Options()

class WebScraper:
    """A flexible web scraper class for extracting data from websites"""
    
    def __init__(self, delay: float = 1.0, timeout: int = 10):
        """
        Initialize the web scraper
        
        Args:
            delay: Delay between requests in seconds (be respectful!)
            timeout: Request timeout in seconds
        """
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_page(self, url: str) -> BeautifulSoup:
        """
        Fetch and parse a web page
        
        Args:
            url: URL to scrape
            
        Returns:
            BeautifulSoup object of the parsed HTML
        """
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Add delay to be respectful
            time.sleep(self.delay)
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from a page"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            links.append(full_url)
        return links
    
    def extract_text(self, soup: BeautifulSoup, selector: str = None) -> List[str]:
        """Extract text content from elements"""
        if selector:
            elements = soup.select(selector)
        else:
            elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        return [elem.get_text(strip=True) for elem in elements if elem.get_text(strip=True)]
    
    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract image information"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            alt = img.get('alt', '')
            if src:
                full_url = urljoin(base_url, src)
                images.append({
                    'url': full_url,
                    'alt': alt,
                    'filename': os.path.basename(urlparse(full_url).path)
                })
        return images
    
    def extract_table_data(self, soup: BeautifulSoup) -> List[List[str]]:
        """Extract data from HTML tables"""
        tables_data = []
        
        for table in soup.find_all('table'):
            table_data = []
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data:  # Only add non-empty rows
                    table_data.append(row_data)
            
            if table_data:
                tables_data.append(table_data)
        
        return tables_data
    
    def scrape_page(self, url: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Scrape a single page with configurable extraction
        
        Args:
            url: URL to scrape
            config: Configuration dict specifying what to extract
            
        Returns:
            Dictionary containing extracted data
        """
        if config is None:
            config = {
                'extract_links': True,
                'extract_text': True,
                'extract_images': True,
                'extract_tables': True,
                'text_selector': None
            }
        
        soup = self.get_page(url)
        if not soup:
            return None
        
        data = {
            'url': url,
            'title': soup.title.string if soup.title else '',
            'timestamp': datetime.now().isoformat()
        }
        
        if config.get('extract_links'):
            data['links'] = self.extract_links(soup, url)
        
        if config.get('extract_text'):
            data['text'] = self.extract_text(soup, config.get('text_selector'))
        
        if config.get('extract_images'):
            data['images'] = self.extract_images(soup, url)
        
        if config.get('extract_tables'):
            data['tables'] = self.extract_table_data(soup)
        
        return data
    
    def scrape_multiple_pages(self, urls: List[str], config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Scrape multiple pages"""
        results = []
        
        for url in urls:
            result = self.scrape_page(url, config)
            if result:
                results.append(result)
        
        return results
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str):
        """Save scraped data to CSV file"""
        if not data:
            print("No data to save")
            return
        
        # Flatten the data for CSV
        flattened_data = []
        for item in data:
            flat_item = {
                'url': item['url'],
                'title': item['title'],
                'timestamp': item['timestamp'],
                'num_links': len(item.get('links', [])),
                'num_images': len(item.get('images', [])),
                'num_tables': len(item.get('tables', [])),
                'text_preview': ' '.join(item.get('text', []))[:200] + '...' if item.get('text') else ''
            }
            flattened_data.append(flat_item)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if flattened_data:
                fieldnames = flattened_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened_data)
        
        print(f"Data saved to {filename}")
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {filename}")


def main():
    """Main function for command line interface"""
    parser = argparse.ArgumentParser(description='Web Scraper App')
    parser.add_argument('urls', nargs='+', help='URLs to scrape')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests (seconds)')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout (seconds)')
    parser.add_argument('--output', '-o', default='scraped_data', help='Output filename (without extension)')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both', help='Output format')
    parser.add_argument('--text-selector', help='CSS selector for text extraction')
    parser.add_argument('--no-links', action='store_true', help='Skip link extraction')
    parser.add_argument('--no-images', action='store_true', help='Skip image extraction')
    parser.add_argument('--no-tables', action='store_true', help='Skip table extraction')
    parser.add_argument('--no-text', action='store_true', help='Skip text extraction')
    
    args = parser.parse_args()
    
    # Create scraper instance
    scraper = WebScraper(delay=args.delay, timeout=args.timeout)
    
    # Configure extraction
    config = {
        'extract_links': not args.no_links,
        'extract_text': not args.no_text,
        'extract_images': not args.no_images,
        'extract_tables': not args.no_tables,
        'text_selector': args.text_selector
    }
    
    # Scrape the URLs
    print(f"Starting to scrape {len(args.urls)} URLs...")
    results = scraper.scrape_multiple_pages(args.urls, config)
    
    if not results:
        print("No data was scraped successfully")
        return
    
    print(f"Successfully scraped {len(results)} pages")
    
    # Save results
    if args.format in ['json', 'both']:
        scraper.save_to_json(results, f"{args.output}.json")
    
    if args.format in ['csv', 'both']:
        scraper.save_to_csv(results, f"{args.output}.csv")
    
    # Print summary
    print(f"\nScraping Summary:")
    print(f"Pages scraped: {len(results)}")
    total_links = sum(len(r.get('links', [])) for r in results)
    total_images = sum(len(r.get('images', [])) for r in results)
    print(f"Total links found: {total_links}")
    print(f"Total images found: {total_images}")


if __name__ == "__main__":
    # Example usage when run directly
    if len(sys.argv) == 1:
        print("Web Scraper App")
        print("===============")
        print()
        print("Example usage:")
        print("python web_scraper.py https://example.com")
        print("python web_scraper.py https://example.com --output my_data --format json")
        print("python web_scraper.py https://site1.com https://site2.com --delay 2")
        print()
        print("For help: python web_scraper.py --help")
        print()
        
        # Interactive mode
        url = input("Enter a URL to scrape (or press Enter to exit): ").strip()
        if url:
            scraper = WebScraper()
            result = scraper.scrape_page(url)
            if result:
                scraper.save_to_json([result], "scraped_data.json")
                print(f"Scraped data saved to scraped_data.json")
            else:
                print("Failed to scrape the URL")
    else:
        main()
