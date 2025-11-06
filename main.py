from bs4 import BeautifulSoup, NavigableString
import requests
import yaml


class WebMDCrawler:
    """Crawls WebMD website and extract content"""
    def __init__(self, base_url='https://www.webmd.com/', headers=None):
        self.base_url = base_url
        self.headers = headers or {"User-Agent": "Mozilla/5.0"}
    
    def fetch(self, path):
        """Fetch HTML content from WebMD page"""
        url = self.base_url + path
        response = requests.get(url=url, headers=self.headers, timeout=20)
        response.raise_for_status()
        return response.text
    
    def parse(self, html):
        """Parse HTML using BeautifulSoup and lxml parser"""
        soup = BeautifulSoup(html, "lxml")
        return soup

    
    def extract_content(self, soup):
        """Extract content from WebMD disease page"""

        HEAD_LEVEL = {"h2": 2, "h3": 3, "h4": 4}
        BLOCK_TAGS = {"p", "ul", "ol"}

        # Extract title - WebMD uses h1 or specific title classes
        title = None
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(" ", strip=True)
        else:
            # Try alternative title locations
            title_el = soup.find(['h1', 'div'], class_=['title', 'page-title', 'article-title'])
            if title_el:
                title = title_el.get_text(" ", strip=True)
        
        # Find main content area - WebMD typically uses article or main content div
        content = (soup.find('article') or 
                   soup.find('div', class_=['article-body', 'article-content', 'main-content']) or
                   soup.find('main'))
        
        if not content:
            return {"title": title, "sections": []}

        # Initialize structure
        root = {"title": title, "sections": []}
        stack = [(1, root)]  # (level_number, node_dict)

        for el in content.descendants:
            # Skip text nodes and non-tag elements
            if isinstance(el, NavigableString) or not getattr(el, "name", None):
                continue

            name = el.name.lower()

            # Handle headings - create new section
            if name in HEAD_LEVEL:
                level = HEAD_LEVEL[name]

                # Pop stack until we find the right parent level
                while len(stack) > 1 and stack[-1][0] >= level:
                    stack.pop()
                
                # Create new section node
                node = {
                    "heading": el.get_text(" ", strip=True),
                    "level": level,
                    "content": [],
                    "subsections": []
                }

                # Add to parent's section or subsections
                parent = stack[-1][1]
                if "sections" in parent:
                    parent["sections"].append(node)
                else:
                    parent["subsections"].append(node)

                # Push this section onto stack
                stack.append((level, node))

            # Handle content blocks (paragraphs, lists)
            elif name in BLOCK_TAGS:
                # Only process if this is a direct child (not nested in another block)
                if el.parent and el.parent.name.lower() not in BLOCK_TAGS:
                    if stack:
                        current_node = stack[-1][1]
                        if "content" in current_node:
                            # Handle lists - preserve structure
                            if name in ("ul", "ol"):
                                items = [li.get_text(" ", strip=True)
                                        for li in el.find_all("li", recursive=False)]
                                if items:
                                    current_node["content"].append({
                                        "type": "list",
                                        "ordered": name == "ol",
                                        "items": items
                                    })
                            # Handle paragraphs - extract text
                            elif name == "p":
                                text = el.get_text(" ", strip=True)
                                if text:
                                    current_node["content"].append({
                                        "type": "paragraph",
                                        "text": text
                                    })
        return root

    def crawl(self, path):
        html = self.fetch(path)
        soup = BeautifulSoup(html, "lxml")
        return self.extract_content(soup)

    def to_markdown(self, data):
        """Convert structured data to markdown format for RAG"""
        lines = []

        # Add title
        if data.get("title"):
            lines.append(f"# {data['title']}\n")

        # Process sections recursively
        def process_section(section, level=2):
            """Recursively process sections and subsections"""
            # Add heading
            if section.get("heading"):
                heading_prefix = "#" * level
                lines.append(f"{heading_prefix} {section['heading']}\n")

            # Add content (paragraphs and lists)
            if section.get("content"):
                for item in section["content"]:
                    if item["type"] == "paragraph":
                        lines.append(f"{item['text']}\n")
                    elif item["type"] == "list":
                        # Handle ordered or unordered lists
                        for idx, list_item in enumerate(item["items"], 1):
                            if item["ordered"]:
                                lines.append(f"{idx}. {list_item}")
                            else:
                                lines.append(f"- {list_item}")
                        lines.append("")  # Add blank line after list

            # Process subsections recursively
            if section.get("subsections"):
                for subsection in section["subsections"]:
                    process_section(subsection, level + 1)

        # Process all top-level sections
        if data.get("sections"):
            for section in data["sections"]:
                process_section(section)

        return "\n".join(lines)

    def export_to_markdown(self, data, output_path):
        """Export crawled data to markdown file for RAG"""
        markdown_content = self.to_markdown(data)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Markdown exported to {output_path}")

    def export_to_yaml(self, data, output_path):
        """Export crawled data to YAML file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"Data exported to {output_path}")

if __name__ == "__main__":
    # Example usage for testing a single page
    crawler = WebMDCrawler()
    
    # Test with a WebMD disease page
    # Example: https://www.webmd.com/diabetes/type-2-diabetes
    data = crawler.crawl("diabetes/type-2-diabetes")
    print(data)

    # Export to YAML
    crawler.export_to_yaml(data, "type-2-diabetes.yaml")

    # Export to Markdown for RAG
    crawler.export_to_markdown(data, "type-2-diabetes.md")
