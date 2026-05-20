"""
Blog Manager - Article CRUD and metadata management
"""

import os
import re
import json
import shutil
from datetime import datetime
from typing import Optional
from pathlib import Path


class BlogManager:
    """Manages blog articles: reading, writing, listing, and metadata."""

    def __init__(self, blog_dir: str):
        """
        Initialize the blog manager.

        Args:
            blog_dir: Path to the blog root directory (containing articles/, assets/, config.json)
        """
        self.blog_dir = Path(blog_dir)
        self.articles_dir = self.blog_dir / "articles"
        self.assets_dir = self.blog_dir / "assets"
        self.images_dir = self.assets_dir / "images"
        self.config_path = self.blog_dir / "config.json"

        # Ensure directories exist
        self.articles_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> dict:
        """Load blog configuration from config.json."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "title": "My Blog",
            "description": "A personal blog",
            "author": "Unknown",
            "language": "zh-CN",
            "site_url": "",
            "articles_per_page": 10,
            "date_format": "%Y-%m-%d",
            "social": {"github": "", "twitter": "", "email": ""},
            "theme": {"primary_color": "#2c3e50", "accent_color": "#3498db", "dark_mode": True},
        }

    def save_config(self, config: dict):
        """Save blog configuration to config.json."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    def parse_front_matter(self, content: str) -> tuple:
        """
        Parse YAML-like front matter from Markdown content.

        Args:
            content: Raw Markdown content with optional front matter

        Returns:
            Tuple of (metadata_dict, body_content)
        """
        metadata = {}
        body = content

        front_matter_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if front_matter_match:
            front_text = front_matter_match.group(1)
            body = content[front_matter_match.end():]

            for line in front_text.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    # Parse lists like [tag1, tag2]
                    if value.startswith("[") and value.endswith("]"):
                        value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",")]
                    # Parse quoted strings
                    elif value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    metadata[key] = value

        return metadata, body

    def build_front_matter(self, metadata: dict) -> str:
        """
        Build YAML-like front matter string from metadata dict.

        Args:
            metadata: Dict with keys like title, date, tags, slug

        Returns:
            Front matter string
        """
        lines = ["---"]
        for key, value in metadata.items():
            if isinstance(value, list):
                formatted = "[" + ", ".join(f'"{v}"' for v in value) + "]"
                lines.append(f"{key}: {formatted}")
            elif isinstance(value, str) and (" " in value or ":" in value):
                lines.append(f'{key}: "{value}"')
            else:
                lines.append(f"{key}: {value}")
        lines.append("---")
        return "\n".join(lines)

    def save_article(
        self,
        title: str,
        content: str,
        tags: list = None,
        date: str = None,
        slug: str = None,
    ) -> dict:
        """
        Save an article as a Markdown file.

        Args:
            title: Article title
            content: Markdown body content
            tags: List of tags
            date: Date string (YYYY-MM-DD), defaults to today
            slug: URL slug, auto-generated from title if not provided

        Returns:
            Article metadata dict
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        if tags is None:
            tags = []
        if slug is None:
            slug = self._generate_slug(title)

        metadata = {
            "title": title,
            "date": date,
            "tags": tags,
            "slug": slug,
        }

        # Build full content with front matter
        front_matter = self.build_front_matter(metadata)
        full_content = f"{front_matter}\n\n{content}"

        # Save file
        filename = f"{date}-{slug}.md"
        filepath = self.articles_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_content)

        metadata["filename"] = filename
        metadata["filepath"] = str(filepath)
        return metadata

    def read_article(self, filename: str) -> Optional[dict]:
        """
        Read and parse an article file.

        Args:
            filename: Article filename (e.g., "2025-06-01-my-article.md")

        Returns:
            Article dict with metadata and content, or None if not found
        """
        filepath = self.articles_dir / filename
        if not filepath.exists():
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            raw_content = f.read()

        metadata, body = self.parse_front_matter(raw_content)

        return {
            "title": metadata.get("title", "Untitled"),
            "date": metadata.get("date", ""),
            "tags": metadata.get("tags", []),
            "slug": metadata.get("slug", filename.replace(".md", "")),
            "filename": filename,
            "content": body,
            "raw_content": raw_content,
        }

    def list_articles(self) -> list:
        """
        List all articles sorted by date (newest first).

        Returns:
            List of article metadata dicts
        """
        articles = []
        if not self.articles_dir.exists():
            return articles

        for f in sorted(self.articles_dir.iterdir(), reverse=True):
            if f.suffix == ".md":
                article = self.read_article(f.name)
                if article:
                    articles.append(article)

        # Sort by date descending
        articles.sort(key=lambda a: a.get("date", ""), reverse=True)
        return articles

    def delete_article(self, filename: str) -> bool:
        """
        Delete an article file.

        Args:
            filename: Article filename

        Returns:
            True if deleted, False if not found
        """
        filepath = self.articles_dir / filename
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def _generate_slug(self, title: str) -> str:
        """
        Generate a URL-friendly slug from a title.

        Args:
            title: Article title (can be Chinese/English)

        Returns:
            Slug string
        """
        # Convert to lowercase
        slug = title.lower()

        # Replace Chinese/CJK characters with pinyin-like transliteration
        # For now, just remove non-alphanumeric chars and replace spaces with hyphens
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        slug = slug.strip("-")

        # If slug is empty (all Chinese), use a hash
        if not slug:
            import hashlib
            slug = hashlib.md5(title.encode()).hexdigest()[:8]

        return slug
