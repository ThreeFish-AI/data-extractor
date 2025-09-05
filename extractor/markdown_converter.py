"""Markdown conversion utilities for HTML content."""

import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse

from markdownify import markdownify as md
from bs4 import BeautifulSoup, Comment

logger = logging.getLogger(__name__)


class MarkdownConverter:
    """Convert HTML content to Markdown format."""
    
    def __init__(self):
        """Initialize the Markdown converter."""
        self.default_options = {
            'heading_style': 'ATX',  # Use # style headings
            'bullets': '-',  # Use - for bullet points
            'emphasis_mark': '*',  # Use * for emphasis
            'strong_mark': '**',  # Use ** for strong
            'link_style': 'INLINE',  # Use inline links [text](url)
            'autolinks': True,  # Convert plain URLs to links
            'wrap': False,  # Disable wrapping
        }

    def preprocess_html(self, html_content: str, base_url: Optional[str] = None) -> str:
        """
        Preprocess HTML content before Markdown conversion.
        
        Args:
            html_content: Raw HTML content
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Preprocessed HTML content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove comments
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
            
            # Remove unwanted elements
            unwanted_tags = ['script', 'style', 'nav', 'header', 'footer', 
                           'aside', 'advertisement', 'ads']
            for tag in unwanted_tags:
                for element in soup.find_all(tag):
                    element.decompose()
            
            # Remove elements with specific classes/ids commonly used for ads/navigation
            unwanted_patterns = [
                re.compile(r'.*(ad|advertisement|sidebar|nav|menu|footer|header).*', re.I)
            ]
            
            for pattern in unwanted_patterns:
                for element in soup.find_all(class_=pattern):
                    element.decompose()
                for element in soup.find_all(id=pattern):
                    element.decompose()
            
            # Convert relative URLs to absolute if base_url is provided
            if base_url:
                # Convert relative links
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if isinstance(href, str) and not href.startswith(('http://', 'https://')):
                        link['href'] = urljoin(base_url, href)
                
                # Convert relative image sources
                for img in soup.find_all('img', src=True):
                    src = img.get('src', '')
                    if isinstance(src, str) and not src.startswith(('http://', 'https://')):
                        img['src'] = urljoin(base_url, src)
            
            # Clean up empty paragraphs and divs
            for tag in soup.find_all(['p', 'div']):
                if not tag.get_text(strip=True) and not tag.find(['img', 'video', 'audio']):
                    tag.decompose()
            
            return str(soup)
            
        except Exception as e:
            logger.warning(f"Error preprocessing HTML: {str(e)}")
            return html_content

    def html_to_markdown(self, html_content: str, base_url: Optional[str] = None, 
                        custom_options: Optional[Dict[str, Any]] = None) -> str:
        """
        Convert HTML content to Markdown.
        
        Args:
            html_content: HTML content to convert
            base_url: Base URL for resolving relative URLs
            custom_options: Custom options for markdownify
            
        Returns:
            Markdown formatted content
        """
        try:
            # Use custom options if provided, otherwise use defaults
            options = self.default_options.copy()
            if custom_options:
                options.update(custom_options)
            
            # Preprocess HTML
            processed_html = self.preprocess_html(html_content, base_url)
            
            # Convert to Markdown
            markdown_content = md(processed_html, **options)
            
            # Post-process Markdown
            markdown_content = self.postprocess_markdown(markdown_content)
            
            return markdown_content
            
        except Exception as e:
            logger.error(f"Error converting HTML to Markdown: {str(e)}")
            return f"Error converting content: {str(e)}"

    def postprocess_markdown(self, markdown_content: str) -> str:
        """
        Post-process Markdown content for better formatting.
        
        Args:
            markdown_content: Raw Markdown content
            
        Returns:
            Cleaned up Markdown content
        """
        try:
            # Remove excessive blank lines (more than 2 consecutive)
            markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
            
            # Clean up list formatting
            markdown_content = re.sub(r'\n-\s*\n', '\n', markdown_content)
            
            # Clean up excessive spaces
            lines = []
            for line in markdown_content.split('\n'):
                # Remove trailing spaces but preserve intentional line breaks
                cleaned_line = line.rstrip()
                lines.append(cleaned_line)
            
            markdown_content = '\n'.join(lines)
            
            # Remove leading/trailing whitespace
            markdown_content = markdown_content.strip()
            
            return markdown_content
            
        except Exception as e:
            logger.warning(f"Error post-processing Markdown: {str(e)}")
            return markdown_content

    def extract_content_area(self, html_content: str) -> str:
        """
        Extract the main content area from HTML, removing navigation, ads, etc.
        
        Args:
            html_content: HTML content
            
        Returns:
            HTML content with main content area only
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try to find main content area using common selectors
            content_selectors = [
                'main',
                '[role="main"]',
                'article',
                '.content',
                '.post',
                '.entry',
                '.article',
                '#content',
                '#main',
                '.main-content',
                '.post-content',
                '.entry-content',
                '.article-content'
            ]
            
            main_content = None
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    # Take the first match that has substantial content
                    for element in elements:
                        text_length = len(element.get_text(strip=True))
                        if text_length > 200:  # Minimum content length
                            main_content = element
                            break
                    if main_content:
                        break
            
            # If no main content area found, use the body
            if not main_content:
                main_content = soup.find('body') or soup
            
            return str(main_content)
            
        except Exception as e:
            logger.warning(f"Error extracting content area: {str(e)}")
            return html_content

    def convert_webpage_to_markdown(self, scrape_result: Dict[str, Any], 
                                  extract_main_content: bool = True,
                                  include_metadata: bool = True,
                                  custom_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert a scraped webpage result to Markdown format.
        
        Args:
            scrape_result: Result from web scraping
            extract_main_content: Whether to extract main content area
            include_metadata: Whether to include page metadata
            custom_options: Custom options for markdownify
            
        Returns:
            Dictionary with Markdown content and metadata
        """
        try:
            if "error" in scrape_result:
                return {
                    "success": False,
                    "error": scrape_result["error"],
                    "url": scrape_result.get("url")
                }
            
            url = scrape_result.get("url", "")
            title = scrape_result.get("title", "")
            content_data = scrape_result.get("content", {})
            
            # Get HTML content - try different sources
            html_content = None
            if "html" in content_data:
                html_content = content_data["html"]
            elif "text" in content_data and content_data["text"]:
                # If we only have text, try to reconstruct basic HTML structure
                text_content = content_data["text"]
                links = content_data.get("links", [])
                images = content_data.get("images", [])
                
                # Build basic HTML structure
                html_parts = ["<html><head>"]
                if title:
                    html_parts.append(f"<title>{title}</title>")
                html_parts.append("</head><body>")
                
                # Add main text content
                html_parts.append(f"<div class='main-content'>{text_content}</div>")
                
                # Add links if available
                if links:
                    html_parts.append("<div class='links'>")
                    for link in links[:50]:  # Limit to first 50 links
                        link_url = link.get("url", "")
                        link_text = link.get("text", link_url)
                        html_parts.append(f"<a href='{link_url}'>{link_text}</a><br>")
                    html_parts.append("</div>")
                
                # Add images if available
                if images:
                    html_parts.append("<div class='images'>")
                    for img in images[:20]:  # Limit to first 20 images
                        img_src = img.get("src", "")
                        img_alt = img.get("alt", "")
                        html_parts.append(f"<img src='{img_src}' alt='{img_alt}'>")
                    html_parts.append("</div>")
                
                html_parts.append("</body></html>")
                html_content = "\n".join(html_parts)
            else:
                return {
                    "success": False,
                    "error": "No content found in scrape result",
                    "url": url
                }
            
            # Extract main content area if requested
            if extract_main_content:
                html_content = self.extract_content_area(html_content)
            
            # Convert to Markdown
            markdown_content = self.html_to_markdown(html_content, url, custom_options)
            
            # Prepare result
            result = {
                "success": True,
                "url": url,
                "markdown": markdown_content,
                "conversion_options": {
                    "extract_main_content": extract_main_content,
                    "include_metadata": include_metadata,
                    "custom_options": custom_options or {}
                }
            }
            
            # Include metadata if requested
            if include_metadata:
                metadata = {
                    "title": title,
                    "meta_description": scrape_result.get("meta_description"),
                    "word_count": len(markdown_content.split()),
                    "character_count": len(markdown_content),
                    "domain": urlparse(url).netloc if url else None,
                }
                
                # Add links and images count if available
                if "links" in content_data:
                    metadata["links_count"] = len(content_data["links"])
                if "images" in content_data:
                    metadata["images_count"] = len(content_data["images"])
                
                result["metadata"] = metadata
            
            return result
            
        except Exception as e:
            logger.error(f"Error converting webpage to Markdown: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": scrape_result.get("url", "")
            }

    def batch_convert_to_markdown(self, scrape_results: List[Dict[str, Any]], 
                                extract_main_content: bool = True,
                                include_metadata: bool = True,
                                custom_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert multiple scraped webpage results to Markdown format.
        
        Args:
            scrape_results: List of scraping results
            extract_main_content: Whether to extract main content area
            include_metadata: Whether to include page metadata
            custom_options: Custom options for markdownify
            
        Returns:
            Dictionary with converted results and summary
        """
        try:
            converted_results = []
            successful_conversions = 0
            failed_conversions = 0
            
            for scrape_result in scrape_results:
                conversion_result = self.convert_webpage_to_markdown(
                    scrape_result, extract_main_content, include_metadata, custom_options
                )
                
                if conversion_result.get("success"):
                    successful_conversions += 1
                else:
                    failed_conversions += 1
                
                converted_results.append(conversion_result)
            
            return {
                "success": True,
                "results": converted_results,
                "summary": {
                    "total": len(scrape_results),
                    "successful": successful_conversions,
                    "failed": failed_conversions,
                    "success_rate": successful_conversions / max(1, len(scrape_results))
                },
                "conversion_options": {
                    "extract_main_content": extract_main_content,
                    "include_metadata": include_metadata,
                    "custom_options": custom_options or {}
                }
            }
            
        except Exception as e:
            logger.error(f"Error in batch Markdown conversion: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }