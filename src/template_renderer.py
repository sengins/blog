"""
Template Renderer - Jinja2 template loading and rendering
"""

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


class TemplateRenderer:
    """Handles loading and rendering Jinja2 templates."""

    def __init__(self, template_dir: str):
        """
        Initialize the template renderer.

        Args:
            template_dir: Path to the directory containing HTML templates
        """
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_article(self, article: dict, config: dict) -> str:
        """
        Render an article page.

        Args:
            article: Article data dict with keys:
                - title: str
                - date: str
                - slug: str
                - tags: list[str]
                - content: str (HTML content)
                - summary: str (optional)
                - prev: dict (optional) - previous article
                - next: dict (optional) - next article
            config: Blog configuration dict

        Returns:
            Rendered HTML string
        """
        template = self.env.get_template("article.html")
        return template.render(
            article=article,
            config=config,
            current_year=datetime.now().year,
        )

    def render_index(self, articles: list, config: dict) -> str:
        """
        Render the blog index page.

        Args:
            articles: List of article data dicts (sorted by date desc)
            config: Blog configuration dict

        Returns:
            Rendered HTML string
        """
        template = self.env.get_template("index.html")
        return template.render(
            articles=articles,
            config=config,
            current_year=datetime.now().year,
        )
