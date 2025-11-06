# WebMD Disease Crawler

A polite, resumable web crawler for extracting disease and condition information from WebMD for use in medical knowledge retrieval systems and RAG (Retrieval-Augmented Generation) applications.

## Features

- **Polite Crawling**: Configurable delays between requests (default 2s) to respect server resources
- **Resumable**: Can resume from any point if interrupted
- **Progress Tracking**: JSON reports with success/failure statistics
- **Multiple Formats**: Exports to both Markdown (RAG-ready) and YAML
- **Robust**: Automatic retry logic for failed requests
- **Comprehensive**: Discovers diseases from WebMD's A-Z index

## Installation

### Prerequisites

- Python 3.7+
- pip package manager

**Note**: The repository includes `webmd_links.json` with 1149 pre-extracted links (1059 conditions + 90 drugs), so you can start crawling immediately without running the extraction script.

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install beautifulsoup4 lxml pyyaml requests
```

## Project Structure

```
WebMD_WebCrawler/
├── main.py              # Core WebMDCrawler class
├── crawler_engine.py    # Polite crawling engine with batch processing
├── run_crawler.py       # CLI interface
├── webmd_links.json     # Pre-extracted links (1059 conditions + 90 drugs)
├── requirements.txt     # Python dependencies
├── .gitignore          # Excludes crawled data and cache
└── README.md           # This file
```

## Usage

### Quick Start - Test Mode

Test the crawler with just 5 diseases:

```bash
python run_crawler.py --mode test
```

### Crawling Modes

#### 1. Test Mode (5 diseases)
```bash
python run_crawler.py --mode test
```

#### 2. Sample Mode (50 diseases)
```bash
python run_crawler.py --mode sample
```

#### 3. All Diseases Mode
```bash
python run_crawler.py --mode all
```

⚠️ **Warning**: This will crawl all diseases from A-Z and may take several hours.

#### 4. Resume Mode
If crawling is interrupted, resume from a specific index:

```bash
python run_crawler.py --mode resume --start 100
```

### Advanced Options

#### Include Drug Pages
By default, only conditions/diseases are crawled. To include drugs:

```bash
python run_crawler.py --mode test --include-drugs
```

#### Custom Links File
If your `webmd_links.json` is in a different location:

```bash
python run_crawler.py --mode test --links-file /path/to/webmd_links.json
```

#### Custom Delay Between Requests
```bash
# 3 second delay (more polite)
python run_crawler.py --mode sample --delay 3.0

# 1 second delay (faster, less polite)
python run_crawler.py --mode sample --delay 1.0
```

#### Custom Output Directory
```bash
python run_crawler.py --mode test --output my_webmd_data
```

#### Custom Limit
```bash
# Crawl exactly 100 diseases
python run_crawler.py --mode resume --limit 100
```

### Complete Example
```bash
# Crawl all conditions and drugs with custom settings
python run_crawler.py \
  --mode all \
  --delay 2.5 \
  --output webmd_medical_knowledge \
  --include-drugs \
  --start 0
```

## Link Extraction

The crawler uses pre-extracted links from HTML files instead of live web scraping. This approach is:
- **Faster**: No need to discover links from A-Z index pages
- **More reliable**: Avoids 404 errors and site structure changes
- **Reproducible**: Same set of links every time

### Generating webmd_links.json

The `extract_links.py` script (located in `../` directory) parses pre-scraped HTML files:

```bash
cd /path/to/project/other
python3 extract_links.py
```

**Input files** (from `links/` folder):
- `conditions/a.html` through `conditions/z.html` - Condition pages organized by letter
- `drugs/drugs.html` - Common drug pages

**Output**: `webmd_links.json`
```json
{
  "conditions": [
    {"name": "Type 2 Diabetes", "url": "https://www.webmd.com/diabetes/type-2-diabetes"},
    ...
  ],
  "drugs": [
    {"name": "Metformin", "url": "https://www.webmd.com/drugs/2/drug-11285/metformin-oral/details"},
    ...
  ],
  "metadata": {
    "total_conditions": 1059,
    "total_drugs": 90,
    "total": 1149
  }
}
```

## Output Structure

After running, you'll get:

```
webmd_data/
├── markdown/
│   ├── type-2-diabetes.md
│   ├── hypertension.md
│   └── ...
├── yaml/
│   ├── type-2-diabetes.yaml
│   ├── hypertension.yaml
│   └── ...
└── crawl_report.json
```

### Markdown Format (RAG-Ready)

Example output in `markdown/`:

```markdown
# Type 2 Diabetes

## What Is Type 2 Diabetes?

Type 2 diabetes is a chronic condition that affects...

## Symptoms

- Increased thirst
- Frequent urination
- Increased hunger
...
```

### YAML Format (Structured)

Example output in `yaml/`:

```yaml
title: Type 2 Diabetes
sections:
  - heading: What Is Type 2 Diabetes?
    level: 2
    content:
      - type: paragraph
        text: Type 2 diabetes is a chronic condition...
    subsections: []
```

### Progress Report

`crawl_report.json` tracks your progress:

```json
{
  "timestamp": "2025-11-05 14:30:00",
  "start_from": 0,
  "progress": {
    "total": 50,
    "successful": 48,
    "failed": 2,
    "failed_list": [...]
  }
}
```

## Programmatic Usage

You can also use the crawler programmatically in your Python code:

### Single Page Crawl

```python
from main import WebMDCrawler

crawler = WebMDCrawler()

# Crawl a specific disease
data = crawler.crawl("diabetes/type-2-diabetes")

# Export to markdown
crawler.export_to_markdown(data, "type-2-diabetes.md")

# Export to YAML
crawler.export_to_yaml(data, "type-2-diabetes.yaml")
```

### Batch Crawling

```python
from crawler_engine import PoliteCrawlerEngine

engine = PoliteCrawlerEngine(
    delay=2.0,
    output_dir='my_data'
)

# Crawl first 10 diseases
engine.crawl_all_diseases(limit=10)
```

## Best Practices

### 1. Be Polite
- Use delays of 2-3 seconds between requests
- Don't run multiple crawlers simultaneously on the same site
- Respect robots.txt (this crawler uses a user agent)

### 2. Handle Interruptions
- Use Ctrl+C to gracefully stop crawling
- Note the index shown when stopped
- Resume with `--mode resume --start <index>`

### 3. Monitor Progress
- Check `crawl_report.json` for failures
- Review failed items and retry if needed
- Monitor console output for errors

### 4. Data Management
```bash
# Check how many files were crawled
ls webmd_data/markdown/*.md | wc -l

# View a sample
cat webmd_data/markdown/type-2-diabetes.md

# Search across all crawled data
grep -r "symptoms" webmd_data/markdown/
```

## Troubleshooting

### Issue: Import Errors
```
ImportError: No module named 'bs4'
```
**Solution**: Install dependencies
```bash
pip install beautifulsoup4 lxml pyyaml requests
```

### Issue: Connection Timeout
```
requests.exceptions.Timeout
```
**Solution**: Increase delay or check internet connection
```bash
python run_crawler.py --mode test --delay 3.0
```

### Issue: No Content Extracted
Some pages may have different HTML structures.

**Solution**: Check the page manually and adjust selectors in `main.py` if needed.

### Issue: Rate Limiting
If you get 429 errors (too many requests):

**Solution**: Increase delay significantly
```bash
python run_crawler.py --mode test --delay 5.0
```

## For BLUE-med Project

This crawler is part of the BLUE-med multi-agent medical error detection system. The crawled data serves as:

1. **Knowledge Source**: WebMD provides patient-oriented medical knowledge for Expert Agent B
2. **RAG Context**: Markdown files are indexed for retrieval-augmented generation
3. **Validation**: Used to cross-reference and validate medical claims

### Integration with RAG

```python
# Example: Load into vector database
from pathlib import Path

markdown_dir = Path("webmd_data/markdown")
for md_file in markdown_dir.glob("*.md"):
    content = md_file.read_text()
    # Index into your vector store (e.g., FAISS, Pinecone)
    vector_store.add_document(content, metadata={"source": "WebMD", "disease": md_file.stem})
```

## License & Ethics

⚠️ **Important Ethical Considerations**:

- This tool is for **educational and research purposes only**
- Respect WebMD's Terms of Service
- Be polite: use reasonable delays (≥2s)
- Do not republish or commercialize crawled content
- Attribute WebMD when using this data
- For production use, consider WebMD's official APIs or partnerships

## Contributing

This crawler was developed as part of the BLUE-med project (The University of Memphis, Fall 2025).

Team members:
- Nguyen Anh Khoa Tran (U00917031)
- Saukun Thika You (U00882629)
- Wesley K. Marizane (U00859208)

## Related Files

- **Mayo Clinic Crawler**: `../MayoClinic_WebCrawler/` - Similar crawler for Mayo Clinic
- **Project Proposal**: `../proposal.txt` - Full BLUE-med project description
- **Dataset Info**: `../models_datasets.txt` - Information about all data sources

## Support

For issues or questions:
1. Check `crawl_report.json` for failure details
2. Review console output for specific error messages
3. Verify dependencies are installed correctly
4. Ensure stable internet connection

---

**Last Updated**: November 5, 2025  
**Version**: 1.0.0  
**Python**: 3.7+
