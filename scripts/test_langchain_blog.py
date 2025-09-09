#!/usr/bin/env python3
"""Standalone script to test LangChain blog conversion manually."""

import asyncio
import tempfile
from extractor.scraper import WebScraper
from extractor.markdown_converter import MarkdownConverter


async def main():
    """Manual test of LangChain blog conversion with detailed output."""
    url = "https://blog.langchain.com/context-engineering-for-agents/"

    scraper = WebScraper()
    converter = MarkdownConverter()

    print(f"🔍 Testing URL: {url}")
    print("=" * 80)

    # Test with different scraping methods
    methods = ["simple", "selenium"]  # Skip scrapy as it often fails for this URL

    for method in methods:
        print(f"\n🔍 Testing with method: {method}")
        print("-" * 50)

        try:
            scrape_result = await scraper.scrape_url(url=url, method=method)

            if "error" in scrape_result:
                print(f"❌ Scraping failed: {scrape_result['error']}")
                continue

            # Show what we got from scraping
            content = scrape_result.get("content", {})
            html_content = content.get("html", "")
            text_content = content.get("text", "")

            print(f"📄 Content keys: {list(content.keys())}")
            print(f"📏 HTML length: {len(html_content) if html_content else 0}")
            print(f"📏 Text length: {len(text_content) if text_content else 0}")

            # Convert to Markdown
            result = converter.convert_webpage_to_markdown(
                scrape_result=scrape_result,
                extract_main_content=True,
                include_metadata=True,
            )

            if result.get("success"):
                markdown = result["markdown"]
                lines = markdown.split("\n")
                empty_lines = [i for i, line in enumerate(lines) if line.strip() == ""]
                long_lines = [line for line in lines if len(line) > 200]
                multi_sentence_lines = [
                    line
                    for line in lines
                    if line.count(".") + line.count("!") + line.count("?") > 1
                    and len(line) > 50
                ]

                print(f"✅ Conversion successful!")
                print(f"   📊 Total lines: {len(lines)}")
                print(
                    f"   📊 Empty lines: {len(empty_lines)} ({len(empty_lines) / len(lines) * 100:.1f}%)"
                )
                print(f"   📊 Content lines: {len(lines) - len(empty_lines)}")
                print(f"   📊 Total characters: {len(markdown):,}")
                print(f"   📊 Long lines (>200 chars): {len(long_lines)}")
                print(f"   📊 Multi-sentence lines: {len(multi_sentence_lines)}")

                # Show first few lines to check structure
                print(f"\n📋 First 10 lines preview:")
                for i, line in enumerate(lines[:10]):
                    if line.strip():
                        print(f"  {i:2d}: {line[:80]}{'...' if len(line) > 80 else ''}")
                    else:
                        print(f"  {i:2d}: [empty line]")

                # Save to temp file for inspection
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=f"_langchain_blog_{method}.md",
                    delete=False,
                    encoding="utf-8",
                ) as f:
                    f.write(markdown)
                    filename = f.name
                print(f"💾 Saved to: {filename}")

                # Check formatting quality
                if len(empty_lines) > 10 and len(lines) > 50:
                    print("✅ Good paragraph structure detected!")
                    if len(long_lines) < 10 and len(multi_sentence_lines) < 20:
                        print("🎉 Excellent formatting quality!")
                    else:
                        print("⚠️  Still has some long/multi-sentence lines")
                else:
                    print("❌ Poor paragraph structure")

                # Show sample from middle
                if len(lines) > 50:
                    print(f"\n📋 Sample from middle (lines 25-30):")
                    for i in range(25, min(30, len(lines))):
                        line = lines[i]
                        if line.strip():
                            print(
                                f"  {i:2d}: {line[:80]}{'...' if len(line) > 80 else ''}"
                            )
                        else:
                            print(f"  {i:2d}: [empty line]")

            else:
                print(f"❌ Conversion failed: {result.get('error')}")

        except Exception as e:
            print(f"❌ Error with {method}: {str(e)}")

    print(f"\n🏁 Testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
