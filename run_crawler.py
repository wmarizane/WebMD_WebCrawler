#!/usr/bin/env python3
"""
Example script to run the WebMD polite crawler engine

Usage:
    python run_crawler.py --mode test      # Test with 5 diseases
    python run_crawler.py --mode sample    # Crawl 50 diseases
    python run_crawler.py --mode all       # Crawl all diseases
    python run_crawler.py --mode resume --start 100  # Resume from index 100
"""

import argparse
from crawler_engine import PoliteCrawlerEngine


def main():
    parser = argparse.ArgumentParser(description='WebMD Disease Crawler')
    parser.add_argument('--mode', choices=['test', 'sample', 'all', 'resume'],
                        default='test', help='Crawling mode')
    parser.add_argument('--start', type=int, default=0,
                        help='Starting index (for resume mode)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Maximum number of diseases to crawl')
    parser.add_argument('--delay', type=float, default=2.0,
                        help='Delay between requests in seconds')
    parser.add_argument('--output', default='webmd_data',
                        help='Output directory')
    parser.add_argument('--include-drugs', action='store_true',
                        help='Include drug pages in addition to conditions')
    parser.add_argument('--links-file', default=None,
                        help='Path to webmd_links.json (default: ../webmd_links.json)')

    args = parser.parse_args()

    # Initialize crawler engine
    engine = PoliteCrawlerEngine(
        delay=args.delay,
        output_dir=args.output
    )

    print("="*60)
    print("WEBMD POLITE CRAWLER ENGINE")
    print("="*60)
    print(f"Mode: {args.mode}")
    print(f"Delay: {args.delay}s between requests")
    print(f"Output: {args.output}/")
    print(f"Include drugs: {args.include_drugs}")
    print("="*60)
    print()

    # Execute based on mode
    if args.mode == 'test':
        print("Running in TEST mode - crawling first 5 items")
        engine.crawl_all_diseases(limit=5, links_json_path=args.links_file, 
                                  include_drugs=args.include_drugs)

    elif args.mode == 'sample':
        print("Running in SAMPLE mode - crawling first 50 items")
        engine.crawl_all_diseases(limit=50, links_json_path=args.links_file,
                                  include_drugs=args.include_drugs)

    elif args.mode == 'all':
        print("Running in ALL mode - crawling all items")
        print("This may take several hours. Press Ctrl+C to stop.")
        engine.crawl_all_diseases(links_json_path=args.links_file,
                                  include_drugs=args.include_drugs)

    elif args.mode == 'resume':
        print(f"Running in RESUME mode - starting from index {args.start}")
        engine.crawl_all_diseases(start_from=args.start, limit=args.limit,
                                  links_json_path=args.links_file,
                                  include_drugs=args.include_drugs)

    print("\nCrawling complete!")


if __name__ == "__main__":
    main()
