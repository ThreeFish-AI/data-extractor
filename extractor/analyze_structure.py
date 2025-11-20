#!/usr/bin/env python3
"""Analyze the structure issues in current markdown output."""


def analyze_markdown_structure():
    """Analyze the current markdown structure to identify issues."""

    with open("langchain_blog_simple.md", "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    print("🔍 Analyzing current markdown structure:")
    print("=" * 60)

    # Identify problematic lines (very long lines that should be split)
    long_lines = []
    for i, line in enumerate(lines):
        if len(line) > 200 and line.strip():
            long_lines.append((i + 1, len(line), line[:100] + "..."))

    print(f"📏 Long lines (>200 chars): {len(long_lines)}")
    for line_num, length, preview in long_lines[:10]:
        print(f"  Line {line_num:3d} ({length:4d} chars): {preview}")

    # Look for sentences that should be separate paragraphs
    print("\n🔤 Checking for sentence boundaries:")
    sentence_issues = []

    for i, line in enumerate(lines):
        if line.strip():
            # Look for multiple sentences in one line
            sentence_endings = line.count(".") + line.count("!") + line.count("?")
            if sentence_endings > 1 and len(line) > 100:
                sentence_issues.append((i + 1, sentence_endings, line[:100] + "..."))

    print(f"📝 Lines with multiple sentences: {len(sentence_issues)}")
    for line_num, count, preview in sentence_issues[:10]:
        print(f"  Line {line_num:3d} ({count} sentences): {preview}")

    # Check for missing paragraph breaks around key patterns
    print("\n🎯 Checking for missing paragraph breaks:")

    patterns_to_check = [
        ("Headers/Titles", r"[A-Z][a-z]+ [A-Z][a-z]+[A-Z]"),
        ("Questions", r"\?[A-Z]"),
        ("Topic transitions", r"\. [A-Z][a-z]+ (is|are|can|will|should)"),
    ]

    import re

    for pattern_name, pattern in patterns_to_check:
        matches = []
        for i, line in enumerate(lines):
            if re.search(pattern, line):
                matches.append((i + 1, line[:80] + "..."))

        print(f"  {pattern_name}: {len(matches)} potential issues")
        for line_num, preview in matches[:5]:
            print(f"    Line {line_num:3d}: {preview}")

    print("\n📊 Summary:")
    print(f"  Total lines: {len(lines)}")
    print(f"  Empty lines: {len([l for l in lines if not l.strip()])}")
    print(f"  Content lines: {len([l for l in lines if l.strip()])}")
    print(f"  Long lines (>200): {len(long_lines)}")
    print(f"  Multi-sentence lines: {len(sentence_issues)}")


if __name__ == "__main__":
    analyze_markdown_structure()
