"""
Image Processor - Handle image copying, compression, and thumbnails
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageOps
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


class ImageProcessor:
    """Processes images for blog articles."""

    def __init__(self, images_dir: str):
        """
        Initialize the image processor.

        Args:
            images_dir: Path to the blog's images directory (blog/assets/images/)
        """
        self.images_dir = Path(images_dir)
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def save_image(
        self,
        source_path: str,
        date: str = None,
        max_width: int = 1200,
        quality: int = 85,
    ) -> Optional[dict]:
        """
        Copy/save an image to the blog's images directory.

        Args:
            source_path: Path to the source image file
            date: Date string for organizing (YYYY-MM-DD), defaults to today
            max_width: Maximum width for resizing (None to skip)
            quality: JPEG/WebP compression quality (1-100)

        Returns:
            Dict with image info, or None if failed:
            {
                "filename": "image-1.jpg",
                "relative_path": "../assets/images/2025-06-01/image-1.jpg",
                "url_path": "assets/images/2025-06-01/image-1.jpg",
                "width": 800,
                "height": 600,
                "size_kb": 123.4
            }
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        source = Path(source_path)
        if not source.exists():
            return None

        # Create date-based subdirectory
        date_dir = self.images_dir / date
        date_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        ext = source.suffix.lower()
        if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
            ext = ".jpg"  # Convert unknown formats to jpg

        # Count existing files to generate unique name
        existing = list(date_dir.glob(f"*{ext}"))
        filename = f"image-{len(existing) + 1}{ext}"
        dest_path = date_dir / filename

        # Process image
        if HAS_PILLOW and ext in (".jpg", ".jpeg", ".png", ".webp"):
            try:
                img = Image.open(source)
                original_width, original_height = img.size

                # Resize if needed
                if max_width and original_width > max_width:
                    ratio = max_width / original_width
                    new_height = int(original_height * ratio)
                    img = img.resize((max_width, new_height), Image.LANCZOS)

                # Save with compression
                save_kwargs = {"quality": quality, "optimize": True}
                if ext in (".png",):
                    save_kwargs = {"optimize": True}
                img.save(dest_path, **save_kwargs)

                width, height = img.size
            except Exception as e:
                print(f"Warning: Image processing failed ({e}), copying raw file.")
                shutil.copy2(source, dest_path)
                width, height = 0, 0
        else:
            # No Pillow available, just copy
            shutil.copy2(source, dest_path)
            width, height = 0, 0

        size_kb = round(dest_path.stat().st_size / 1024, 1)

        return {
            "filename": filename,
            "relative_path": f"../assets/images/{date}/{filename}",
            "url_path": f"assets/images/{date}/{filename}",
            "width": width,
            "height": height,
            "size_kb": size_kb,
        }

    def save_image_from_url(self, url: str, date: str = None) -> Optional[dict]:
        """
        Download and save an image from a URL.

        Args:
            url: Image URL
            date: Date string for organizing

        Returns:
            Image info dict or None if failed
        """
        try:
            import requests
            from urllib.parse import urlparse

            # Download image
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # Determine extension from URL or content-type
            parsed = urlparse(url)
            ext = os.path.splitext(parsed.path)[1]
            if not ext or ext.lower() not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
                content_type = response.headers.get("content-type", "")
                ext_map = {
                    "image/jpeg": ".jpg",
                    "image/png": ".png",
                    "image/gif": ".gif",
                    "image/webp": ".webp",
                }
                ext = ext_map.get(content_type, ".jpg")

            # Save to temp file
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")

            date_dir = self.images_dir / date
            date_dir.mkdir(parents=True, exist_ok=True)

            existing = list(date_dir.glob(f"*{ext}"))
            filename = f"image-{len(existing) + 1}{ext}"
            temp_path = date_dir / filename

            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Process the downloaded image
            return self.save_image(str(temp_path), date)

        except Exception as e:
            print(f"Warning: Failed to download image from {url}: {e}")
            return None
