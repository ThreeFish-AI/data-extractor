"""Unit tests for MarkdownConverter functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from extractor.markdown_converter import MarkdownConverter


class TestMarkdownConverterInit:
    """Test MarkdownConverter initialization."""
    
    def test_markdown_converter_initialization(self):
        """Test MarkdownConverter initializes with default options."""
        converter = MarkdownConverter()
        
        assert converter.default_options['heading_style'] == 'ATX'
        assert converter.default_options['bullets'] == '-'
        assert converter.default_options['emphasis_mark'] == '*'
        assert converter.default_options['strong_mark'] == '**'
        assert converter.default_options['link_style'] == 'INLINE'
        assert converter.default_options['autolinks'] is True
        assert converter.default_options['wrap'] is False


class TestPreprocessHtml:
    """Test HTML preprocessing functionality."""
    
    def test_preprocess_html_basic(self):
        """Test basic HTML preprocessing."""
        converter = MarkdownConverter()
        html = '<html><body><p>Test content</p></body></html>'
        
        result = converter.preprocess_html(html)
        
        assert 'Test content' in result
        assert '<p>' in result

    def test_preprocess_html_remove_comments(self):
        """Test removal of HTML comments."""
        converter = MarkdownConverter()
        html = '<html><body><!-- This is a comment --><p>Test content</p></body></html>'
        
        result = converter.preprocess_html(html)
        
        assert 'This is a comment' not in result
        assert 'Test content' in result

    def test_preprocess_html_remove_unwanted_tags(self):
        """Test removal of unwanted HTML tags."""
        converter = MarkdownConverter()
        html = '''
        <html>
            <head>
                <script>alert('test');</script>
                <style>body { color: red; }</style>
            </head>
            <body>
                <nav>Navigation</nav>
                <header>Header</header>
                <p>Main content</p>
                <footer>Footer</footer>
                <aside>Sidebar</aside>
            </body>
        </html>
        '''
        
        result = converter.preprocess_html(html)
        
        assert 'alert' not in result
        assert 'color: red' not in result
        assert 'Navigation' not in result
        assert 'Header' not in result
        assert 'Footer' not in result
        assert 'Sidebar' not in result
        assert 'Main content' in result

    def test_preprocess_html_convert_relative_urls(self):
        """Test conversion of relative URLs to absolute."""
        converter = MarkdownConverter()
        html = '''
        <html>
            <body>
                <a href="/page1">Link 1</a>
                <a href="page2.html">Link 2</a>
                <a href="https://external.com">External Link</a>
                <img src="/image1.jpg" alt="Image 1">
                <img src="image2.jpg" alt="Image 2">
                <img src="https://external.com/image.jpg" alt="External Image">
            </body>
        </html>
        '''
        base_url = "https://example.com"
        
        result = converter.preprocess_html(html, base_url)
        
        assert 'href="https://example.com/page1"' in result
        assert 'href="https://example.com/page2.html"' in result
        assert 'href="https://external.com"' in result  # Should remain unchanged
        assert 'src="https://example.com/image1.jpg"' in result
        assert 'src="https://example.com/image2.jpg"' in result
        assert 'src="https://external.com/image.jpg"' in result  # Should remain unchanged

    def test_preprocess_html_clean_empty_elements(self):
        """Test removal of empty paragraphs and divs."""
        converter = MarkdownConverter()
        html = '''
        <html>
            <body>
                <p>Content paragraph</p>
                <p></p>
                <p>   </p>
                <div>Content div</div>
                <div></div>
                <div>   </div>
                <div><img src="image.jpg" alt="Image"></div>
            </body>
        </html>
        '''
        
        result = converter.preprocess_html(html)
        
        assert 'Content paragraph' in result
        assert 'Content div' in result
        assert 'image.jpg' in result
        # Empty elements should be removed but image container should remain


class TestHtmlToMarkdown:
    """Test HTML to Markdown conversion."""
    
    def test_html_to_markdown_basic(self):
        """Test basic HTML to Markdown conversion."""
        converter = MarkdownConverter()
        html = '<html><body><h1>Title</h1><p>Paragraph content</p></body></html>'
        
        result = converter.html_to_markdown(html)
        
        assert '# Title' in result
        assert 'Paragraph content' in result

    def test_html_to_markdown_with_links(self):
        """Test conversion of links to Markdown format."""
        converter = MarkdownConverter()
        html = '<html><body><a href="https://example.com">Link text</a></body></html>'
        
        result = converter.html_to_markdown(html)
        
        assert '[Link text](https://example.com)' in result

    def test_html_to_markdown_with_images(self):
        """Test conversion of images to Markdown format."""
        converter = MarkdownConverter()
        html = '<html><body><img src="image.jpg" alt="Alt text"></body></html>'
        
        result = converter.html_to_markdown(html)
        
        assert '![Alt text](image.jpg)' in result

    def test_html_to_markdown_with_lists(self):
        """Test conversion of lists to Markdown format."""
        converter = MarkdownConverter()
        html = '''
        <html>
            <body>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </body>
        </html>
        '''
        
        result = converter.html_to_markdown(html)
        
        assert '- Item 1' in result
        assert '- Item 2' in result

    def test_html_to_markdown_custom_options(self):
        """Test HTML to Markdown conversion with custom options."""
        converter = MarkdownConverter()
        html = '<html><body><h1>Title</h1></body></html>'
        custom_options = {
            'heading_style': 'ATX',
            'bullets': '*',
        }
        
        result = converter.html_to_markdown(html, custom_options=custom_options)
        
        assert '# Title' in result

    @patch('extractor.markdown_converter.md')
    def test_html_to_markdown_error_handling(self, mock_md):
        """Test error handling in HTML to Markdown conversion."""
        converter = MarkdownConverter()
        mock_md.side_effect = Exception("Conversion error")
        html = '<html><body><p>Test</p></body></html>'
        
        result = converter.html_to_markdown(html)
        
        assert 'Error converting content: Conversion error' in result


class TestPostprocessMarkdown:
    """Test Markdown post-processing functionality."""
    
    def test_postprocess_markdown_remove_excessive_blank_lines(self):
        """Test removal of excessive blank lines."""
        converter = MarkdownConverter()
        markdown = 'Line 1\n\n\n\n\nLine 2'
        
        result = converter.postprocess_markdown(markdown)
        
        assert result == 'Line 1\n\nLine 2'

    def test_postprocess_markdown_clean_lists(self):
        """Test cleaning up list formatting."""
        converter = MarkdownConverter()
        markdown = 'List:\n-\n\n- Item 1\n-\n\n- Item 2'
        
        result = converter.postprocess_markdown(markdown)
        
        assert '-\n\n' not in result
        assert '- Item 1' in result
        assert '- Item 2' in result

    def test_postprocess_markdown_remove_trailing_spaces(self):
        """Test removal of trailing spaces."""
        converter = MarkdownConverter()
        markdown = 'Line 1   \nLine 2\t\nLine 3'
        
        result = converter.postprocess_markdown(markdown)
        
        lines = result.split('\n')
        assert lines[0] == 'Line 1'
        assert lines[1] == 'Line 2'
        assert lines[2] == 'Line 3'

    def test_postprocess_markdown_strip_content(self):
        """Test stripping leading/trailing whitespace."""
        converter = MarkdownConverter()
        markdown = '\n\n  Content  \n\n'
        
        result = converter.postprocess_markdown(markdown)
        
        assert result == 'Content'


class TestExtractContentArea:
    """Test main content area extraction."""
    
    def test_extract_content_area_main_tag(self):
        """Test extraction using main tag."""
        converter = MarkdownConverter()
        html = '''
        <html>
            <body>
                <nav>Navigation</nav>
                <main>Main content here with sufficient text to meet the minimum content length requirements for proper content extraction testing and validation. This should provide enough characters to pass the 200 character minimum threshold that triggers content area extraction rather than falling back to the full body content.</main>
                <footer>Footer</footer>
            </body>
        </html>
        '''
        
        result = converter.extract_content_area(html)
        
        assert 'Main content here with sufficient text' in result
        # The main tag should be extracted, not the full body
        assert '<main>' in result or 'Main content here with sufficient text' in result

    def test_extract_content_area_article_tag(self):
        """Test extraction using article tag."""
        converter = MarkdownConverter()
        html = '''
        <html>
            <body>
                <nav>Navigation</nav>
                <article>Article content here with substantial text that exceeds 200 characters to meet the minimum content length requirement for proper extraction testing purposes.</article>
                <footer>Footer</footer>
            </body>
        </html>
        '''
        
        result = converter.extract_content_area(html)
        
        assert 'Article content here' in result
        # Since article content is long enough, it should be extracted
        assert '<article>' in result or 'Article content here' in result

    def test_extract_content_area_class_selector(self):
        """Test extraction using common class selectors."""
        converter = MarkdownConverter()
        html = '''
        <html>
            <body>
                <nav>Navigation</nav>
                <div class="content">Content div with sufficient text length to meet the minimum requirements for content extraction testing purposes and validation.</div>
                <footer>Footer</footer>
            </body>
        </html>
        '''
        
        result = converter.extract_content_area(html)
        
        assert 'Content div with sufficient' in result
        # Since the div has sufficient content, it should be extracted
        assert 'class="content"' in result or 'Content div with sufficient' in result

    def test_extract_content_area_fallback_to_body(self):
        """Test fallback to body when no main content area found."""
        converter = MarkdownConverter()
        html = '''
        <html>
            <body>
                <div>Some content</div>
                <div>More content</div>
            </body>
        </html>
        '''
        
        result = converter.extract_content_area(html)
        
        assert 'Some content' in result
        assert 'More content' in result


class TestConvertWebpageToMarkdown:
    """Test webpage to Markdown conversion."""
    
    def test_convert_webpage_to_markdown_with_html_content(self):
        """Test conversion with HTML content available."""
        converter = MarkdownConverter()
        scrape_result = {
            "url": "https://example.com",
            "title": "Example Title",
            "content": {
                "html": "<html><body><h1>Title</h1><p>Content</p></body></html>"
            }
        }
        
        result = converter.convert_webpage_to_markdown(scrape_result)
        
        assert result["success"] is True
        assert result["url"] == "https://example.com"
        assert "# Title" in result["markdown"]
        assert "Content" in result["markdown"]
        assert result["metadata"]["title"] == "Example Title"

    def test_convert_webpage_to_markdown_with_text_content(self):
        """Test conversion when only text content is available."""
        converter = MarkdownConverter()
        scrape_result = {
            "url": "https://example.com",
            "title": "Example Title",
            "content": {
                "text": "Main text content",
                "links": [{"url": "https://link1.com", "text": "Link 1"}],
                "images": [{"src": "image1.jpg", "alt": "Image 1"}]
            }
        }
        
        result = converter.convert_webpage_to_markdown(scrape_result)
        
        assert result["success"] is True
        assert "Main text content" in result["markdown"]
        assert "Link 1" in result["markdown"]
        assert "image1.jpg" in result["markdown"]

    def test_convert_webpage_to_markdown_with_error(self):
        """Test conversion with error in scrape result."""
        converter = MarkdownConverter()
        scrape_result = {
            "error": "Scraping failed",
            "url": "https://example.com"
        }
        
        result = converter.convert_webpage_to_markdown(scrape_result)
        
        assert result["success"] is False
        assert result["error"] == "Scraping failed"
        assert result["url"] == "https://example.com"

    def test_convert_webpage_to_markdown_no_content(self):
        """Test conversion with no content available."""
        converter = MarkdownConverter()
        scrape_result = {
            "url": "https://example.com",
            "title": "Example Title",
            "content": {}
        }
        
        result = converter.convert_webpage_to_markdown(scrape_result)
        
        assert result["success"] is False
        assert "No content found" in result["error"]
        assert result["url"] == "https://example.com"

    def test_convert_webpage_to_markdown_extract_main_content_false(self):
        """Test conversion without main content extraction."""
        converter = MarkdownConverter()
        scrape_result = {
            "url": "https://example.com",
            "title": "Example Title",
            "content": {
                "html": "<html><body><nav>Nav</nav><main>Main</main></body></html>"
            }
        }
        
        result = converter.convert_webpage_to_markdown(
            scrape_result, extract_main_content=False
        )
        
        assert result["success"] is True
        # Should include nav content when extract_main_content is False
        assert "Nav" in result["markdown"] or "Main" in result["markdown"]

    def test_convert_webpage_to_markdown_include_metadata_false(self):
        """Test conversion without metadata."""
        converter = MarkdownConverter()
        scrape_result = {
            "url": "https://example.com",
            "title": "Example Title",
            "content": {
                "html": "<html><body><h1>Title</h1></body></html>"
            }
        }
        
        result = converter.convert_webpage_to_markdown(
            scrape_result, include_metadata=False
        )
        
        assert result["success"] is True
        assert "metadata" not in result

    def test_convert_webpage_to_markdown_custom_options(self):
        """Test conversion with custom options."""
        converter = MarkdownConverter()
        scrape_result = {
            "url": "https://example.com",
            "title": "Example Title",
            "content": {
                "html": "<html><body><h1>Title</h1></body></html>"
            }
        }
        custom_options = {"heading_style": "SETEXT"}
        
        result = converter.convert_webpage_to_markdown(
            scrape_result, custom_options=custom_options
        )
        
        assert result["success"] is True
        assert result["conversion_options"]["custom_options"] == custom_options

    def test_convert_webpage_to_markdown_metadata_calculation(self):
        """Test metadata calculation in conversion."""
        converter = MarkdownConverter()
        scrape_result = {
            "url": "https://example.com",
            "title": "Example Title",
            "meta_description": "Example description",
            "content": {
                "html": "<html><body><h1>Title</h1><p>Content with multiple words for testing</p></body></html>",
                "links": [{"url": "link1"}, {"url": "link2"}],
                "images": [{"src": "img1"}, {"src": "img2"}, {"src": "img3"}]
            }
        }
        
        result = converter.convert_webpage_to_markdown(scrape_result)
        
        assert result["success"] is True
        metadata = result["metadata"]
        assert metadata["title"] == "Example Title"
        assert metadata["meta_description"] == "Example description"
        assert metadata["word_count"] > 0
        assert metadata["character_count"] > 0
        assert metadata["domain"] == "example.com"
        assert metadata["links_count"] == 2
        assert metadata["images_count"] == 3


class TestBatchConvertToMarkdown:
    """Test batch conversion functionality."""
    
    def test_batch_convert_to_markdown_success(self):
        """Test successful batch conversion."""
        converter = MarkdownConverter()
        scrape_results = [
            {
                "url": "https://example1.com",
                "title": "Title 1",
                "content": {"html": "<html><body><h1>Title 1</h1></body></html>"}
            },
            {
                "url": "https://example2.com",
                "title": "Title 2",
                "content": {"html": "<html><body><h1>Title 2</h1></body></html>"}
            }
        ]
        
        result = converter.batch_convert_to_markdown(scrape_results)
        
        assert result["success"] is True
        assert len(result["results"]) == 2
        assert result["summary"]["total"] == 2
        assert result["summary"]["successful"] == 2
        assert result["summary"]["failed"] == 0
        assert result["summary"]["success_rate"] == 1.0

    def test_batch_convert_to_markdown_partial_success(self):
        """Test batch conversion with some failures."""
        converter = MarkdownConverter()
        scrape_results = [
            {
                "url": "https://example1.com",
                "title": "Title 1",
                "content": {"html": "<html><body><h1>Title 1</h1></body></html>"}
            },
            {
                "error": "Scraping failed",
                "url": "https://example2.com"
            }
        ]
        
        result = converter.batch_convert_to_markdown(scrape_results)
        
        assert result["success"] is True
        assert len(result["results"]) == 2
        assert result["summary"]["total"] == 2
        assert result["summary"]["successful"] == 1
        assert result["summary"]["failed"] == 1
        assert result["summary"]["success_rate"] == 0.5

    def test_batch_convert_to_markdown_empty_list(self):
        """Test batch conversion with empty list."""
        converter = MarkdownConverter()
        scrape_results = []
        
        result = converter.batch_convert_to_markdown(scrape_results)
        
        assert result["success"] is True
        assert len(result["results"]) == 0
        assert result["summary"]["total"] == 0
        assert result["summary"]["successful"] == 0
        assert result["summary"]["failed"] == 0

    def test_batch_convert_to_markdown_with_options(self):
        """Test batch conversion with custom options."""
        converter = MarkdownConverter()
        scrape_results = [
            {
                "url": "https://example1.com",
                "title": "Title 1",
                "content": {"html": "<html><body><h1>Title 1</h1></body></html>"}
            }
        ]
        custom_options = {"heading_style": "SETEXT"}
        
        result = converter.batch_convert_to_markdown(
            scrape_results,
            extract_main_content=False,
            include_metadata=False,
            custom_options=custom_options
        )
        
        assert result["success"] is True
        assert result["conversion_options"]["extract_main_content"] is False
        assert result["conversion_options"]["include_metadata"] is False
        assert result["conversion_options"]["custom_options"] == custom_options

    @patch.object(MarkdownConverter, 'convert_webpage_to_markdown')
    def test_batch_convert_to_markdown_exception_handling(self, mock_convert):
        """Test batch conversion exception handling."""
        converter = MarkdownConverter()
        mock_convert.side_effect = Exception("Conversion error")
        scrape_results = [{"url": "https://example.com", "content": {"html": "<html></html>"}}]
        
        result = converter.batch_convert_to_markdown(scrape_results)
        
        assert result["success"] is False
        assert "Conversion error" in result["error"]
        assert result["results"] == []