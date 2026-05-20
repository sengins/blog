#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publish Script - Convert Markdown articles to HTML

Usage:
    python scripts/publish.py              # Publish all articles
    python scripts/publish.py --help       # Show help

This script:
    1. Reads all Markdown files from blog/articles/
    2. Renders them to HTML using Jinja2 templates
    3. Copies CSS and assets to the output directory
    4. Generates index.html with article list
    5. Outputs everything to blog/_site/
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

# Add parent directory to path so we can import src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.blog_manager import BlogManager
from src.html_generator import HtmlGenerator
from src.template_renderer import TemplateRenderer


def publish(blog_dir: str, template_dir: str, output_dir: str = None):
    """
    Publish all articles: Markdown -> HTML.

    Args:
        blog_dir: Path to blog root directory
        template_dir: Path to HTML templates directory
        output_dir: Path to output directory (default: blog/_site)
    """
    # Initialize components
    blog = BlogManager(blog_dir)
    html_gen = HtmlGenerator()
    renderer = TemplateRenderer(template_dir)

    # Load config
    config = blog.load_config()

    # Determine output directory
    if output_dir is None:
        output_dir = os.path.join(blog_dir, "_site")
    output_path = Path(output_dir)

    # Create output directories
    output_articles_dir = output_path / "articles"
    output_css_dir = output_path / "css"
    output_assets_dir = output_path / "assets"
    output_images_dir = output_assets_dir / "images"

    output_articles_dir.mkdir(parents=True, exist_ok=True)
    output_css_dir.mkdir(parents=True, exist_ok=True)
    output_images_dir.mkdir(parents=True, exist_ok=True)

    # Copy CSS
    css_source = Path(template_dir) / "style.css"
    if css_source.exists():
        shutil.copy2(css_source, output_css_dir / "style.css")
        print("  [OK] Copied style.css")

    # Copy images
    source_images_dir = Path(blog_dir) / "assets" / "images"
    if source_images_dir.exists():
        for img_file in source_images_dir.rglob("*"):
            if img_file.is_file() and img_file.suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"):
                relative = img_file.relative_to(source_images_dir)
                dest = output_images_dir / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(img_file, dest)
        print("  [OK] Copied images")

    # Read all articles
    articles = blog.list_articles()
    print(f"\n  Found {len(articles)} article(s)")

    if not articles:
        # Generate empty index
        index_html = renderer.render_index([], config)
        with open(output_path / "index.html", "w", encoding="utf-8") as f:
            f.write(index_html)
        print("  [OK] Generated index.html (empty)")
        print(f"\n  Output: {output_path}")
        return

    # Build article data for rendering
    rendered_articles = []
    for i, article in enumerate(articles):
        # Convert Markdown content to HTML
        html_content = html_gen.to_html(article["content"])

        # Get summary if not in front matter
        summary = article.get("summary", "")
        if not summary:
            summary = html_gen.extract_summary(article["raw_content"])

        # Build article data
        article_data = {
            "title": article["title"],
            "date": article["date"],
            "slug": article["slug"],
            "tags": article.get("tags", []),
            "content": html_content,
            "summary": summary,
            "prev": None,
            "next": None,
        }

        # Set prev/next navigation
        if i > 0:
            prev = articles[i - 1]
            article_data["prev"] = {
                "title": prev["title"],
                "slug": prev["slug"],
            }
        if i < len(articles) - 1:
            next_article = articles[i + 1]
            article_data["next"] = {
                "title": next_article["title"],
                "slug": next_article["slug"],
            }

        rendered_articles.append(article_data)

    # Render and save each article
    for article_data in rendered_articles:
        html = renderer.render_article(article_data, config)
        output_file = output_articles_dir / f"{article_data['slug']}.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  [OK] {article_data['title']}")

    # Render and save index page
    index_articles = []
    for article_data in rendered_articles:
        index_articles.append({
            "title": article_data["title"],
            "date": article_data["date"],
            "slug": article_data["slug"],
            "tags": article_data["tags"],
            "summary": article_data["summary"],
        })

    index_html = renderer.render_index(index_articles, config)
    with open(output_path / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print("  [OK] index.html")

    print(f"\n  [Done] Published {len(rendered_articles)} article(s) to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Publish Markdown articles to HTML blog"
    )
    parser.add_argument(
        "--blog-dir",
        default=None,
        help="Blog root directory (default: ./blog)",
    )
    parser.add_argument(
        "--template-dir",
        default=None,
        help="Templates directory (default: ./templates)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: blog/_site)",
    )

    args = parser.parse_args()

    # Determine project root (directory containing this script's parent)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    blog_dir = args.blog_dir or os.path.join(project_root, "blog")
    template_dir = args.template_dir or os.path.join(project_root, "templates")

    print(f"\n  [Agent Blog Publisher] Publishing...")
    print(f"  {'=' * 40}")
    print(f"  Blog dir:      {blog_dir}")
    print(f"  Template dir:  {template_dir}")

    publish(blog_dir, template_dir, args.output_dir)
    print()


if __name__ == "__main__":
    main()
