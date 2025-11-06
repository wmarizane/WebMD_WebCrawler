from bs4 import BeautifulSoup
import requests
import time
import os
import json
from urllib.parse import urljoin
from main import WebMDCrawler


class PoliteCrawlerEngine:
    """Polite crawling engine for WebMD diseases and conditions"""

    def __init__(self, base_url='https://www.webmd.com/',
                 delay=2.0, max_retries=3, output_dir='crawled_data'):
        """
        Initialize the polite crawler engine

        Args:
            base_url: Base URL of the website
            delay: Delay between requests in seconds (default 2s)
            max_retries: Maximum number of retries for failed requests
            output_dir: Directory to save crawled data
        """
        self.base_url = base_url
        self.delay = delay
        self.max_retries = max_retries
        self.output_dir = output_dir
        self.headers = {"User-Agent": "Mozilla/5.0 (Educational crawler)"}
        self.crawler = WebMDCrawler(base_url=base_url, headers=self.headers)

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/markdown", exist_ok=True)
        os.makedirs(f"{output_dir}/yaml", exist_ok=True)

    def fetch_with_retry(self, url):
        """Fetch URL with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=20)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay * 2)  # Wait longer on retry
                else:
                    raise
        return None

    def get_all_disease_links(self, links_json_path=None, include_drugs=False):
        """
        Load disease/condition and drug links from pre-extracted JSON file
        
        Args:
            links_json_path: Path to webmd_links.json (default: ../webmd_links.json)
            include_drugs: If True, include drug links as well (default: False)
        
        Returns:
            List of tuples: [(disease_name, disease_url), ...]
        """
        print("Loading WebMD links from pre-extracted JSON file...")
        
        # Default to webmd_links.json in parent directory
        if links_json_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            links_json_path = os.path.join(os.path.dirname(script_dir), 'webmd_links.json')
        
        # Check if file exists
        if not os.path.exists(links_json_path):
            print(f"Error: Links file not found at {links_json_path}")
            print("Please run extract_links.py first to generate the links file.")
            return []
        
        # Load JSON
        try:
            with open(links_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error loading links file: {e}")
            return []
        
        all_items = []
        
        # Add conditions
        if 'conditions' in data:
            conditions = data['conditions']
            print(f"  Loaded {len(conditions)} condition links")
            for item in conditions:
                all_items.append((item['name'], item['url']))
        
        # Add drugs if requested
        if include_drugs and 'drugs' in data:
            drugs = data['drugs']
            print(f"  Loaded {len(drugs)} drug links")
            for item in drugs:
                all_items.append((item['name'], item['url']))
        
        print(f"\nTotal links loaded: {len(all_items)}")
        return all_items

    def extract_disease_slug(self, url):
        """Extract disease slug from URL for filename"""
        # Example: https://www.webmd.com/diabetes/type-2-diabetes
        # Returns: type-2-diabetes
        # Remove base URL and query params
        path = url.replace(self.base_url, '').split('?')[0]
        # Get the last meaningful part
        parts = [p for p in path.split('/') if p]
        if parts:
            slug = parts[-1]
            return slug
        return None

    def crawl_disease(self, disease_name, disease_url):
        """
        Crawl a single disease page

        Args:
            disease_name: Name of the disease
            disease_url: URL of the disease page

        Returns:
            dict: Extracted data or None if failed
        """
        try:
            print(f"Crawling: {disease_name}")

            # Extract the path from full URL
            path = disease_url.replace(self.base_url, '')

            # Crawl the page
            data = self.crawler.crawl(path)

            if data and data.get('sections'):
                return data
            else:
                print(f"  Warning: No content found for {disease_name}")
                return None

        except Exception as e:
            print(f"  Error crawling {disease_name}: {e}")
            return None

    def save_disease_data(self, disease_name, disease_url, data):
        """Save disease data to both markdown and YAML"""
        slug = self.extract_disease_slug(disease_url)
        if not slug:
            slug = disease_name.lower().replace(' ', '-').replace('/', '-')

        # Clean slug to be filesystem safe
        slug = ''.join(c if c.isalnum() or c in '-_' else '-' for c in slug)

        # Save as markdown
        md_path = f"{self.output_dir}/markdown/{slug}.md"
        self.crawler.export_to_markdown(data, md_path)

        # Save as YAML
        yaml_path = f"{self.output_dir}/yaml/{slug}.yaml"
        self.crawler.export_to_yaml(data, yaml_path)

        return slug

    def crawl_all_diseases(self, limit=None, start_from=0, links_json_path=None, include_drugs=False):
        """
        Crawl all diseases and conditions

        Args:
            limit: Maximum number of diseases to crawl (None = all)
            start_from: Index to start from (for resuming)
            links_json_path: Path to webmd_links.json file
            include_drugs: If True, include drug pages as well
        """
        # Get all disease links
        diseases = self.get_all_disease_links(links_json_path=links_json_path, 
                                              include_drugs=include_drugs)

        if limit:
            diseases = diseases[start_from:start_from + limit]
        else:
            diseases = diseases[start_from:]

        print(f"\nStarting crawl of {len(diseases)} diseases...")
        print(f"Delay between requests: {self.delay}s")
        print(f"Output directory: {self.output_dir}\n")

        # Track progress
        progress = {
            'total': len(diseases),
            'successful': 0,
            'failed': 0,
            'failed_list': []
        }

        for idx, (disease_name, disease_url) in enumerate(diseases, start=start_from + 1):
            print(f"[{idx}/{start_from + len(diseases)}] ", end="")

            try:
                # Crawl the disease page
                data = self.crawl_disease(disease_name, disease_url)

                if data:
                    # Save the data
                    slug = self.save_disease_data(disease_name, disease_url, data)
                    print(f"  ✓ Saved as {slug}")
                    progress['successful'] += 1
                else:
                    progress['failed'] += 1
                    progress['failed_list'].append((disease_name, disease_url))

                # Be polite - wait between requests
                time.sleep(self.delay)

            except KeyboardInterrupt:
                print("\n\nCrawling interrupted by user.")
                print(f"Progress: {progress['successful']} successful, {progress['failed']} failed")
                print(f"You can resume from index {idx}")
                break
            except Exception as e:
                print(f"  ✗ Unexpected error: {e}")
                progress['failed'] += 1
                progress['failed_list'].append((disease_name, disease_url))
                time.sleep(self.delay)

        # Save progress report
        self.save_progress_report(progress, start_from)

        # Print summary
        print("\n" + "="*60)
        print("CRAWL SUMMARY")
        print("="*60)
        print(f"Total processed: {progress['successful'] + progress['failed']}")
        print(f"Successful: {progress['successful']}")
        print(f"Failed: {progress['failed']}")

        if progress['failed_list']:
            print("\nFailed items:")
            for name, url in progress['failed_list'][:10]:  # Show first 10
                print(f"  - {name}: {url}")
            if len(progress['failed_list']) > 10:
                print(f"  ... and {len(progress['failed_list']) - 10} more")

    def save_progress_report(self, progress, start_from):
        """Save progress report as JSON"""
        report_path = f"{self.output_dir}/crawl_report.json"
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'start_from': start_from,
            'progress': progress
        }
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nProgress report saved to {report_path}")


if __name__ == "__main__":
    # Example usage
    engine = PoliteCrawlerEngine(
        delay=2.0,  # 2 second delay between requests
        output_dir='webmd_data'
    )

    # Test with first 5 diseases
    print("Testing crawler with first 5 diseases...")
    engine.crawl_all_diseases(limit=5)

    # To crawl all diseases:
    # engine.crawl_all_diseases()

    # To resume from a specific index:
    # engine.crawl_all_diseases(start_from=50)
