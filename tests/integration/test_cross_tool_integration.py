"""Cross-tool integration tests for combined functionality scenarios."""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import patch

from extractor.server import (
    app,
    web_scraper,
    _get_pdf_processor,
)


class TestCrossToolIntegration:
    """Integration tests for scenarios involving multiple tools working together."""

    @pytest.fixture
    def pdf_processor(self):
        """创建 PDF 处理器实例用于测试"""
        return _get_pdf_processor()

    @pytest_asyncio.fixture
    async def all_tools(self, pdf_processor):
        """Get all MCP tools from the app."""
        return await app.get_tools()

    @pytest.mark.asyncio
    async def test_webpage_to_pdf_to_markdown_workflow(self, all_tools, pdf_processor):
        """Test a complete workflow: scrape webpage, then process any PDFs found."""
        scrape_tool = all_tools["scrape_webpage"]
        convert_pdf_tool = all_tools["convert_pdf_to_markdown"]

        # Mock webpage scraping that finds PDF links
        webpage_result = {
            "url": "https://example.com/research-page",
            "title": "Research Papers",
            "status_code": 200,
            "content": {
                "html": """
                <html>
                    <body>
                        <h1>Research Papers</h1>
                        <p>Here are some important research papers:</p>
                        <ul>
                            <li><a href="/papers/paper1.pdf">Machine Learning Basics</a></li>
                            <li><a href="/papers/paper2.pdf">Deep Learning Advanced</a></li>
                            <li><a href="https://external.com/paper3.pdf">Neural Networks</a></li>
                        </ul>
                    </body>
                </html>
                """,
                "links": [
                    {
                        "url": "https://example.com/papers/paper1.pdf",
                        "text": "Machine Learning Basics",
                    },
                    {
                        "url": "https://example.com/papers/paper2.pdf",
                        "text": "Deep Learning Advanced",
                    },
                    {
                        "url": "https://external.com/paper3.pdf",
                        "text": "Neural Networks",
                    },
                ],
            },
        }

        pdf_processing_result = {
            "success": True,
            "text": "# Machine Learning Basics\n\nThis paper covers fundamental concepts...",
            "markdown": "# Machine Learning Basics\n\nThis paper covers fundamental concepts in machine learning.",
            "source": "https://example.com/papers/paper1.pdf",
            "method_used": "pymupdf",
            "pages_processed": 15,
            "word_count": 5000,
            "metadata": {
                "title": "Machine Learning Basics",
                "author": "Dr. Smith",
                "total_pages": 15,
            },
        }

        with (
            patch.object(web_scraper, "scrape_url") as mock_scrape,
            patch("extractor.server._get_pdf_processor", return_value=pdf_processor),
            patch.object(pdf_processor, "process_pdf") as mock_pdf,
        ):
            mock_scrape.return_value = webpage_result
            mock_pdf.return_value = pdf_processing_result

            # Step 1: Scrape the webpage
            webpage_response = await scrape_tool.fn(
                url="https://example.com/research-page",
                method="simple",
                extract_config=None,
                wait_for_element=None,
            )

            assert webpage_response.success is True

            # Extract PDF links from the scraped content
            pdf_links = [
                link["url"]
                for link in webpage_response.data["content"]["links"]
                if link["url"].endswith(".pdf")
            ]
            assert len(pdf_links) == 3

            # Step 2: Process the first PDF found
            first_pdf_url = pdf_links[0]
            pdf_response = await convert_pdf_tool.fn(
                pdf_source=first_pdf_url,
                method="auto",
                include_metadata=True,
                page_range=None,
                output_format="markdown",
            )

            assert pdf_response.success is True
            assert pdf_response.pdf_source == first_pdf_url
            assert "Machine Learning Basics" in pdf_response.content

            # Verify the workflow executed correctly
            mock_scrape.assert_called_once_with(
                url="https://example.com/research-page",
                method="simple",
                extract_config=None,
                wait_for_element=None,
            )
            mock_pdf.assert_called_once_with(
                pdf_source=first_pdf_url,
                method="auto",
                include_metadata=True,
                page_range=None,
                output_format="markdown",
            )

    @pytest.mark.asyncio
    async def test_batch_scraping_with_pdf_extraction_workflow(
        self, all_tools, pdf_processor
    ):
        """Test batch webpage scraping followed by batch PDF processing."""
        batch_scrape_tool = all_tools["scrape_multiple_webpages"]
        batch_pdf_tool = all_tools["batch_convert_pdfs_to_markdown"]

        # Mock batch scraping results with mixed content including PDFs
        batch_scrape_results = [
            {
                "url": "https://site1.com",
                "title": "Site 1 - PDF Repository",
                "content": {
                    "html": "<html><body><h1>PDF Collection</h1><a href='/doc1.pdf'>Document 1</a></body></html>",
                    "links": [
                        {"url": "https://site1.com/doc1.pdf", "text": "Document 1"}
                    ],
                },
            },
            {
                "url": "https://site2.com",
                "title": "Site 2 - Research Portal",
                "content": {
                    "html": "<html><body><h1>Research</h1><a href='/research.pdf'>Research Paper</a></body></html>",
                    "links": [
                        {
                            "url": "https://site2.com/research.pdf",
                            "text": "Research Paper",
                        }
                    ],
                },
            },
        ]

        batch_pdf_results = {
            "success": True,
            "results": [
                {
                    "success": True,
                    "text": "Document 1 content...",
                    "markdown": "# Document 1\n\nContent of document 1.",
                    "source": "https://site1.com/doc1.pdf",
                    "word_count": 1000,
                },
                {
                    "success": True,
                    "text": "Research paper content...",
                    "markdown": "# Research Paper\n\nContent of research paper.",
                    "source": "https://site2.com/research.pdf",
                    "word_count": 3000,
                },
            ],
            "summary": {
                "total_pdfs": 2,
                "successful_count": 2,
                "failed": 0,
                "total_word_count": 4000,
            },
        }

        with (
            patch.object(web_scraper, "scrape_multiple_urls") as mock_batch_scrape,
            patch("extractor.server._get_pdf_processor", return_value=pdf_processor),
            patch.object(pdf_processor, "batch_process_pdfs") as mock_batch_pdf,
        ):
            mock_batch_scrape.return_value = batch_scrape_results
            mock_batch_pdf.return_value = batch_pdf_results

            # Step 1: Batch scrape multiple websites
            scrape_urls = ["https://site1.com", "https://site2.com"]
            scrape_response = await batch_scrape_tool.fn(
                urls=scrape_urls,
                method="simple",
                extract_config=None,
            )

            assert scrape_response.success is True
            assert len(scrape_response.results) == 2

            # Extract all PDF links from scraped results
            all_pdf_links = []
            for result in scrape_response.results:
                if (
                    result.success
                    and result.data
                    and "content" in result.data
                    and "links" in result.data["content"]
                ):
                    pdf_links = [
                        link["url"]
                        for link in result.data["content"]["links"]
                        if link["url"].endswith(".pdf")
                    ]
                    all_pdf_links.extend(pdf_links)

            assert len(all_pdf_links) == 2

            # Step 2: Batch process all found PDFs
            pdf_response = await batch_pdf_tool.fn(
                pdf_sources=all_pdf_links,
                method="auto",
                include_metadata=True,
                page_range=None,
                output_format="markdown",
            )

            assert pdf_response.success is True
            assert pdf_response.total_pdfs == 2
            assert pdf_response.successful_count == 2
            assert pdf_response.total_word_count == 4000

    @pytest.mark.asyncio
    async def test_metrics_collection_across_multiple_tools(
        self, all_tools, pdf_processor
    ):
        """Test that metrics are collected properly across different tool usage."""
        scrape_tool = all_tools["scrape_webpage"]
        pdf_tool = all_tools["convert_pdf_to_markdown"]
        markdown_tool = all_tools["convert_webpage_to_markdown"]
        metrics_tool = all_tools["get_server_metrics"]

        # Mock responses for different tools
        scrape_result = {
            "url": "https://test.com",
            "title": "Test Page",
            "content": {"html": "<html><body><h1>Test</h1></body></html>"},
        }

        pdf_result = {
            "success": True,
            "text": "PDF content",
            "markdown": "# PDF Document\n\nContent",
            "source": "/test.pdf",
            "word_count": 100,
        }

        _ = {
            "success": True,
            "markdown": "# Webpage\n\nConverted content",
            "metadata": {"title": "Test Page", "word_count": 50},
        }

        with (
            patch.object(web_scraper, "scrape_url") as mock_scrape,
            patch("extractor.server._get_pdf_processor", return_value=pdf_processor),
            patch.object(pdf_processor, "process_pdf") as mock_pdf,
        ):
            mock_scrape.return_value = scrape_result
            mock_pdf.return_value = pdf_result

            # Use multiple tools to generate metrics
            await scrape_tool.fn(
                url="https://test.com",
                method="auto",
                extract_config=None,
                wait_for_element=None,
            )
            await pdf_tool.fn(
                pdf_source="/test.pdf",
                method="auto",
                include_metadata=True,
                page_range=None,
                output_format="markdown",
            )
            await markdown_tool.fn(
                url="https://test.com",
                method="auto",
                extract_main_content=True,
                include_metadata=True,
                custom_options=None,
                wait_for_element=None,
                formatting_options=None,
                embed_images=False,
                embed_options=None,
            )

            # Check metrics collection
            metrics_response = await metrics_tool.fn()

            assert metrics_response.success is True
            # Verify metrics contain information about different operations
            # MetricsResponse has individual attributes, not a metrics dict
            assert hasattr(metrics_response, "total_requests")
            assert hasattr(metrics_response, "successful_requests")
            assert hasattr(metrics_response, "cache_stats")
            assert hasattr(metrics_response, "method_usage")

    @pytest.mark.asyncio
    async def test_error_propagation_across_tools(self, all_tools, pdf_processor):
        """Test how errors propagate when using multiple tools together."""
        scrape_tool = all_tools["scrape_webpage"]
        pdf_tool = all_tools["convert_pdf_to_markdown"]

        # Mock a failed scraping operation
        with patch.object(web_scraper, "scrape_url") as mock_scrape:
            mock_scrape.side_effect = Exception("Network timeout")

            # First tool fails
            scrape_response = await scrape_tool.fn(
                url="https://unreachable.com",
                method="auto",
                extract_config=None,
                wait_for_element=None,
            )
            assert scrape_response.success is False

        # Mock a failed PDF processing
        with (
            patch("extractor.server._get_pdf_processor", return_value=pdf_processor),
            patch.object(pdf_processor, "process_pdf") as mock_pdf,
        ):
            mock_pdf.return_value = {
                "success": False,
                "error": "PDF parsing failed",
                "source": "/corrupted.pdf",
            }

            # Second tool fails with proper error handling
            pdf_response = await pdf_tool.fn(
                pdf_source="/corrupted.pdf",
                method="auto",
                include_metadata=True,
                page_range=None,
                output_format="markdown",
            )
            assert pdf_response.success is False
            assert "PDF parsing failed" in (
                pdf_response.error["message"]
                if isinstance(pdf_response.error, dict)
                else pdf_response.error
            )

    @pytest.mark.asyncio
    async def test_resource_cleanup_across_multiple_tools(
        self, all_tools, pdf_processor
    ):
        """Test proper resource cleanup when using multiple tools."""
        import gc

        # Track initial memory state
        gc.collect()
        initial_objects = len(gc.get_objects())

        scrape_tool = all_tools["scrape_webpage"]
        pdf_tool = all_tools["convert_pdf_to_markdown"]
        batch_pdf_tool = all_tools["batch_convert_pdfs_to_markdown"]

        # Mock successful_count operations
        scrape_result = {
            "url": "https://test.com",
            "title": "Test",
            "content": {"html": "<html><body>Content</body></html>"},
        }

        pdf_result = {
            "success": True,
            "text": "Content " * 1000,  # Large content to test memory
            "markdown": "# Document\n\n" + "Paragraph.\n" * 500,
            "source": "/test.pdf",
            "word_count": 1000,
        }

        batch_pdf_result = {
            "success": True,
            "results": [pdf_result for _ in range(5)],
            "summary": {"total_pdfs": 5, "successful_count": 5, "failed": 0},
        }

        with (
            patch.object(web_scraper, "scrape_url") as mock_scrape,
            patch("extractor.server._get_pdf_processor", return_value=pdf_processor),
            patch.object(pdf_processor, "process_pdf") as mock_pdf,
            patch.object(pdf_processor, "batch_process_pdfs") as mock_batch_pdf,
        ):
            mock_scrape.return_value = scrape_result
            mock_pdf.return_value = pdf_result
            mock_batch_pdf.return_value = batch_pdf_result

            # Perform multiple operations with large data
            for i in range(10):
                await scrape_tool.fn(
                    url=f"https://test{i}.com",
                    method="auto",
                    extract_config=None,
                    wait_for_element=None,
                )
                await pdf_tool.fn(
                    pdf_source=f"/test{i}.pdf",
                    method="auto",
                    include_metadata=True,
                    page_range=None,
                    output_format="markdown",
                )

            # Perform batch operation
            await batch_pdf_tool.fn(
                pdf_sources=[f"/batch{i}.pdf" for i in range(5)],
                method="auto",
                include_metadata=True,
                page_range=None,
                output_format="markdown",
            )

        # Force garbage collection and check memory usage
        gc.collect()
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects

        # Allow reasonable object growth but detect potential leaks
        assert object_growth < 3000, (
            f"Potential memory leak: {object_growth} new objects"
        )

    @pytest.mark.asyncio
    async def test_concurrent_multi_tool_operations(self, all_tools, pdf_processor):
        """Test concurrent execution of different tools."""
        scrape_tool = all_tools["scrape_webpage"]
        pdf_tool = all_tools["convert_pdf_to_markdown"]
        markdown_tool = all_tools["convert_webpage_to_markdown"]

        # Mock results for concurrent operations
        scrape_result = {
            "url": "https://concurrent-test.com",
            "title": "Concurrent Test",
            "content": {"html": "<html><body><h1>Test</h1></body></html>"},
        }

        pdf_result = {
            "success": True,
            "text": "Concurrent PDF content",
            "markdown": "# Concurrent PDF\n\nContent",
            "source": "/concurrent.pdf",
        }

        _ = {
            "success": True,
            "markdown": "# Concurrent Markdown\n\nContent",
            "metadata": {"title": "Concurrent Test"},
        }

        with (
            patch.object(web_scraper, "scrape_url") as mock_scrape,
            patch("extractor.server._get_pdf_processor", return_value=pdf_processor),
            patch.object(pdf_processor, "process_pdf") as mock_pdf,
        ):
            mock_scrape.return_value = scrape_result
            mock_pdf.return_value = pdf_result

            # Create concurrent tasks using different tools
            tasks = (
                [
                    scrape_tool.fn(
                        url=f"https://test{i}.com",
                        method="auto",
                        extract_config=None,
                        wait_for_element=None,
                    )
                    for i in range(3)
                ]
                + [
                    pdf_tool.fn(
                        pdf_source=f"/test{i}.pdf",
                        method="auto",
                        include_metadata=True,
                        page_range=None,
                        output_format="markdown",
                    )
                    for i in range(3)
                ]
                + [
                    markdown_tool.fn(
                        url=f"https://markdown{i}.com",
                        method="auto",
                        extract_main_content=True,
                        include_metadata=True,
                        custom_options=None,
                        wait_for_element=None,
                        formatting_options=None,
                        embed_images=False,
                        embed_options=None,
                    )
                    for i in range(3)
                ]
            )

            # Execute all concurrently
            results = await asyncio.gather(*tasks)

            # Verify all operations succeeded
            for result in results:
                assert result.success is True

            # Verify appropriate number of calls to each mock
            assert (
                mock_scrape.call_count == 6
            )  # 3 scrape + 3 markdown (which uses scraping)
            assert mock_pdf.call_count == 3  # 3 PDF operations


class TestRealWorldIntegrationScenarios:
    """Integration tests simulating real-world usage scenarios."""

    @pytest.fixture
    def pdf_processor(self):
        """创建 PDF 处理器实例用于测试"""
        return _get_pdf_processor()

    @pytest_asyncio.fixture
    async def scenario_tools(self):
        """Get tools commonly used together in real scenarios."""
        tools = await app.get_tools()
        return {
            "scrape_webpage": tools["scrape_webpage"],
            "scrape_multiple_webpages": tools["scrape_multiple_webpages"],
            "convert_webpage_to_markdown": tools["convert_webpage_to_markdown"],
            "convert_pdf_to_markdown": tools["convert_pdf_to_markdown"],
            "batch_convert_pdfs_to_markdown": tools["batch_convert_pdfs_to_markdown"],
            "extract_links": tools["extract_links"],
            "get_server_metrics": tools["get_server_metrics"],
            "clear_cache": tools["clear_cache"],
        }

    @pytest.mark.asyncio
    async def test_research_paper_collection_scenario(
        self, scenario_tools, pdf_processor
    ):
        """Test a complete research paper collection workflow."""
        # Scenario: User wants to collect and convert all research papers from an academic site

        # Step 1: Extract all links from the main page
        extract_links_tool = scenario_tools["extract_links"]

        links_result = {
            "url": "https://academic-site.com/papers",
            "links": [
                {
                    "url": "https://academic-site.com/paper1.pdf",
                    "text": "Machine Learning",
                },
                {
                    "url": "https://academic-site.com/paper2.pdf",
                    "text": "Deep Learning",
                },
                {
                    "url": "https://academic-site.com/paper3.html",
                    "text": "Overview Page",
                },
                {
                    "url": "https://academic-site.com/paper4.pdf",
                    "text": "Neural Networks",
                },
            ],
        }

        with patch.object(web_scraper, "scrape_url") as mock_scrape:
            mock_scrape.return_value = {
                "url": "https://academic-site.com/papers",
                "content": {"links": links_result["links"]},
            }

            # Extract all links
            links_response = await extract_links_tool.fn(
                url="https://academic-site.com/papers",
                filter_domains=None,
                exclude_domains=None,
                internal_only=False,
            )

            assert links_response.success is True

        # Step 2: Filter PDF links and batch process them
        pdf_links = [
            "https://academic-site.com/paper1.pdf",
            "https://academic-site.com/paper2.pdf",
            "https://academic-site.com/paper4.pdf",
        ]

        batch_pdf_tool = scenario_tools["batch_convert_pdfs_to_markdown"]

        batch_result = {
            "success": True,
            "results": [
                {
                    "success": True,
                    "markdown": f"# Paper {i}\n\nResearch content {i}.",
                    "source": pdf_links[i - 1],
                    "word_count": 1000 * i,
                    "metadata": {"title": f"Research Paper {i}"},
                }
                for i in range(1, 4)
            ],
            "summary": {
                "total_pdfs": 3,
                "successful_count": 3,
                "failed": 0,
                "total_word_count": 6000,
            },
        }

        with (
            patch("extractor.server._get_pdf_processor", return_value=pdf_processor),
            patch.object(pdf_processor, "batch_process_pdfs") as mock_batch_pdf,
        ):
            mock_batch_pdf.return_value = batch_result

            batch_response = await batch_pdf_tool.fn(
                pdf_sources=pdf_links,
                method="auto",
                include_metadata=True,
                page_range=None,
                output_format="markdown",
            )

            assert batch_response.success is True
            assert batch_response.successful_count == 3
            assert batch_response.total_word_count == 6000

        # Step 3: Also convert the overview HTML page to markdown
        markdown_tool = scenario_tools["convert_webpage_to_markdown"]

        with patch.object(web_scraper, "scrape_url") as mock_scrape:
            mock_scrape.return_value = {
                "url": "https://academic-site.com/paper3.html",
                "title": "Research Overview",
                "content": {
                    "html": "<html><body><h1>Research Overview</h1><p>Summary of all papers.</p></body></html>"
                },
            }

            markdown_response = await markdown_tool.fn(
                url="https://academic-site.com/paper3.html",
                method="auto",
                extract_main_content=True,
                include_metadata=True,
                custom_options=None,
                wait_for_element=None,
                formatting_options=None,
                embed_images=False,
                embed_options=None,
            )

            assert markdown_response.success is True
            assert "Research Overview" in markdown_response.markdown_content

        # Step 4: Check final metrics
        metrics_tool = scenario_tools["get_server_metrics"]
        metrics_response = await metrics_tool.fn()
        assert metrics_response.success is True

    @pytest.mark.asyncio
    async def test_website_documentation_backup_scenario(
        self, scenario_tools, pdf_processor
    ):
        """Test creating a complete backup of website documentation."""
        # Scenario: User wants to backup all documentation pages as markdown

        # Step 1: Scrape the main documentation index
        scrape_tool = scenario_tools["scrape_webpage"]

        index_result = {
            "url": "https://docs.example.com",
            "title": "Documentation Index",
            "content": {
                "html": """
                <html>
                    <body>
                        <h1>Documentation</h1>
                        <nav>
                            <ul>
                                <li><a href="/getting-started">Getting Started</a></li>
                                <li><a href="/api-reference">API Reference</a></li>
                                <li><a href="/tutorials">Tutorials</a></li>
                                <li><a href="/faq.pdf">FAQ (PDF)</a></li>
                            </ul>
                        </nav>
                    </body>
                </html>
                """,
                "links": [
                    {
                        "url": "https://docs.example.com/getting-started",
                        "text": "Getting Started",
                    },
                    {
                        "url": "https://docs.example.com/api-reference",
                        "text": "API Reference",
                    },
                    {"url": "https://docs.example.com/tutorials", "text": "Tutorials"},
                    {"url": "https://docs.example.com/faq.pdf", "text": "FAQ (PDF)"},
                ],
            },
        }

        with patch.object(web_scraper, "scrape_url") as mock_scrape:
            mock_scrape.return_value = index_result

            index_response = await scrape_tool.fn(
                url="https://docs.example.com",
                method="auto",
                extract_config=None,
                wait_for_element=None,
            )
            assert index_response.success is True

        # Step 2: Batch convert all HTML pages to markdown
        html_pages = [
            "https://docs.example.com/getting-started",
            "https://docs.example.com/api-reference",
            "https://docs.example.com/tutorials",
        ]

        batch_markdown_tool = scenario_tools["convert_webpage_to_markdown"]

        # Process each HTML page (simulate batch by calling individually)
        html_results = []
        for i, url in enumerate(html_pages):
            with patch.object(web_scraper, "scrape_url") as mock_scrape:
                mock_scrape.return_value = {
                    "url": url,
                    "title": f"Documentation Page {i + 1}",
                    "content": {
                        "html": f"<html><body><h1>Page {i + 1}</h1><p>Content for page {i + 1}</p></body></html>"
                    },
                }

                result = await batch_markdown_tool.fn(
                    url=url,
                    method="auto",
                    extract_main_content=True,
                    include_metadata=True,
                    custom_options=None,
                    wait_for_element=None,
                    formatting_options=None,
                    embed_images=False,
                    embed_options=None,
                )
                assert result.success is True
                html_results.append(result)

        # Step 3: Convert the PDF to markdown
        pdf_tool = scenario_tools["convert_pdf_to_markdown"]

        with (
            patch("extractor.server._get_pdf_processor", return_value=pdf_processor),
            patch.object(pdf_processor, "process_pdf") as mock_pdf,
        ):
            mock_pdf.return_value = {
                "success": True,
                "markdown": "# FAQ\n\n## Q: How to get started?\nA: Follow the getting started guide.",
                "source": "https://docs.example.com/faq.pdf",
                "word_count": 50,
            }

            pdf_result = await pdf_tool.fn(
                pdf_source="https://docs.example.com/faq.pdf",
                method="auto",
                include_metadata=True,
                page_range=None,
                output_format="markdown",
            )
            assert pdf_result.success is True

        # Verify complete documentation backup
        assert len(html_results) == 3
        for result in html_results:
            assert "Page" in result.markdown_content
        assert "FAQ" in pdf_result.content

    @pytest.mark.asyncio
    async def test_competitive_analysis_scenario(self, scenario_tools, pdf_processor):
        """Test competitive analysis workflow across multiple competitor sites."""
        # Scenario: Analyze multiple competitor websites and their resources

        competitor_urls = [
            "https://competitor1.com",
            "https://competitor2.com",
            "https://competitor3.com",
        ]

        # Step 1: Batch scrape all competitor sites
        batch_scrape_tool = scenario_tools["scrape_multiple_webpages"]

        competitor_results = [
            {
                "url": url,
                "title": f"Competitor {i + 1}",
                "content": {
                    "html": f"""
                    <html>
                        <body>
                            <h1>Competitor {i + 1}</h1>
                            <p>Product features: Feature A, Feature B</p>
                            <a href="/whitepaper{i + 1}.pdf">Download Whitepaper</a>
                        </body>
                    </html>
                    """,
                    "links": [
                        {
                            "url": f"{url}/whitepaper{i + 1}.pdf",
                            "text": "Download Whitepaper",
                        }
                    ],
                },
            }
            for i, url in enumerate(competitor_urls)
        ]

        with patch.object(web_scraper, "scrape_multiple_urls") as mock_batch_scrape:
            mock_batch_scrape.return_value = competitor_results

            scrape_response = await batch_scrape_tool.fn(
                urls=competitor_urls,
                method="simple",
                extract_config=None,
            )

            assert scrape_response.success is True
            assert len(scrape_response.results) == 3

        # Step 2: Extract all whitepaper PDFs found
        pdf_urls = []
        for result in competitor_results:
            if "content" in result and "links" in result["content"]:
                pdf_links = [
                    link["url"]
                    for link in result["content"]["links"]
                    if link["url"].endswith(".pdf")
                ]
                pdf_urls.extend(pdf_links)

        assert len(pdf_urls) == 3

        # Step 3: Batch process all competitor whitepapers
        batch_pdf_tool = scenario_tools["batch_convert_pdfs_to_markdown"]

        whitepaper_results = {
            "success": True,
            "results": [
                {
                    "success": True,
                    "markdown": f"# Competitor {i + 1} Whitepaper\n\nProduct analysis and features.",
                    "source": pdf_urls[i],
                    "word_count": (i + 1) * 500,
                    "metadata": {"title": f"Competitor {i + 1} Whitepaper"},
                }
                for i in range(3)
            ],
            "summary": {
                "total_pdfs": 3,
                "successful_count": 3,
                "total_word_count": 3000,  # 500 + 1000 + 1500
            },
        }

        with (
            patch("extractor.server._get_pdf_processor", return_value=pdf_processor),
            patch.object(pdf_processor, "batch_process_pdfs") as mock_batch_pdf,
        ):
            mock_batch_pdf.return_value = whitepaper_results

            pdf_response = await batch_pdf_tool.fn(
                pdf_sources=pdf_urls,
                method="auto",
                include_metadata=True,
                page_range=None,
                output_format="markdown",
            )

            assert pdf_response.success is True
            assert pdf_response.total_word_count == 3000

        # Step 4: Generate final metrics for the analysis
        metrics_tool = scenario_tools["get_server_metrics"]
        clear_cache_tool = scenario_tools["clear_cache"]

        # Clear cache and get final metrics
        await clear_cache_tool.fn()
        metrics_response = await metrics_tool.fn()

        assert metrics_response.success is True
        # In a real scenario, metrics would show the analysis activity
