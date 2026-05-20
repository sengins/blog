"""
HTML Generator - Convert Markdown to HTML
"""

import re
import mistune
from typing import Optional


class BlogMarkdownRenderer(mistune.HTMLRenderer):
    """Custom Markdown renderer with blog-specific styling."""

    def __init__(self):
        super().__init__()

    def image(self, src: str, alt: str = "", title: Optional[str] = None) -> str:
        """Render images with optional caption from alt text."""
        html = f'<img src="{src}" alt="{alt}"'
        if title:
            html += f' title="{title}"'
        html += ' loading="lazy">'
        if alt:
            html += f"\n<em>{alt}</em>"
        return html

    def link(self, text: str, url: str, title: Optional[str] = None) -> str:
        """Render links with target=_blank for external links."""
        attrs = f'href="{url}"'
        if url.startswith(("http://", "https://")):
            attrs += ' target="_blank" rel="noopener"'
        if title:
            attrs += f' title="{title}"'
        return f'<a {attrs}>{text}</a>'


class HtmlGenerator:
    """Converts Markdown content to HTML."""

    def __init__(self):
        self.renderer = BlogMarkdownRenderer()
        self.markdown = mistune.create_markdown(
            renderer=self.renderer,
            plugins=[
                "strikethrough",
                "footnotes",
                "table",
                "url",
                "task_lists",
                "def_list",
            ],
        )

    def to_html(self, markdown_content: str) -> str:
        """
        Convert Markdown string to HTML string.

        Args:
            markdown_content: Raw Markdown text

        Returns:
            HTML string
        """
        html = self.markdown(markdown_content)
        # Post-process: wrap tables in responsive container
        html = re.sub(r'<table>', '<div class="table-wrapper"><table>', html)
        html = re.sub(r'</table>', '</table></div>', html)
        return html

    def extract_title(self, markdown_content: str) -> Optional[str]:
        """
        Extract the first H1 title from Markdown content.

        Args:
            markdown_content: Raw Markdown text

        Returns:
            Title string or None if not found
        """
        match = re.search(r"^#\s+(.+)$", markdown_content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None

    def extract_summary(self, markdown_content: str, max_length: int = 200) -> str:
        """
        Extract a summary from Markdown content (first paragraph).

        Args:
            markdown_content: Raw Markdown text
            max_length: Maximum summary length

        Returns:
            Summary string
        """
        # Remove front matter
        content = re.sub(r"^---\n.*?\n---\n", "", markdown_content, flags=re.DOTALL)

        # Remove headers
        content = re.sub(r"^#+\s+.*$", "", content, flags=re.MULTILINE)

        # Get first non-empty paragraph
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        for para in paragraphs:
            # Skip code blocks, lists, etc.
            if not para.startswith(("```", "-", "*", "|", ">")):
                # Strip markdown formatting
                plain = re.sub(r"[*_~`#\[\]]", "", para)
                plain = re.sub(r"!\[.*?\]\(.*?\)", "", plain)
                plain = re.sub(r"\[([^\]]+)\]\(.*?\)", r"\1", plain)
                plain = plain.strip()
                if plain and len(plain) > 20:
                    if len(plain) > max_length:
                        return plain[:max_length].rsplit(" ", 1)[0] + "..."
                    return plain
        return ""
