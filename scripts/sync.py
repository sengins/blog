#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync Script - Deploy blog to GitHub Pages and Cloudflare Pages

Usage:
    python scripts/sync.py                  # Sync to all platforms
    python scripts/sync.py --git-only       # GitHub Pages only
    python scripts/sync.py --cf-only        # Cloudflare Pages only
    python scripts/sync.py --dry-run        # Preview changes without syncing
    python scripts/sync.py --help           # Show help

Prerequisites:
    1. GitHub: blog/ directory must be a Git repo with remote configured
    2. Cloudflare: Set environment variables:
       - CLOUDFLARE_API_TOKEN
       - CLOUDFLARE_ACCOUNT_ID
       - CLOUDFLARE_PROJECT_NAME
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_git_repo(blog_dir: str) -> bool:
    """Check if blog directory is a Git repository."""
    git_dir = os.path.join(blog_dir, ".git")
    return os.path.isdir(git_dir)


def get_git_status(blog_dir: str) -> list:
    """Get list of changed files in the Git repo."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=blog_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        changes = [line.strip() for line in result.stdout.split("\n") if line.strip()]
        return changes
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] Git status failed: {e}")
        return []


def git_sync(blog_dir: str, dry_run: bool = False) -> bool:
    """
    Commit and push changes to GitHub.

    Args:
        blog_dir: Blog directory (Git repo root)
        dry_run: If True, only show what would be done

    Returns:
        True if successful
    """
    print(f"\n  {'=' * 40}")
    print(f"  [GitHub Pages Sync]")
    print(f"  {'=' * 40}")

    if not check_git_repo(blog_dir):
        print(f"  [ERROR] Not a Git repository: {blog_dir}")
        print(f"  [HINT] Run: cd {blog_dir} && git init && git remote add origin <your-repo-url>")
        return False

    # Check for changes
    changes = get_git_status(blog_dir)
    if not changes:
        print(f"  [INFO] No changes to sync.")
        return True

    print(f"  Changes detected: {len(changes)} file(s)")
    for change in changes[:10]:
        print(f"    {change}")
    if len(changes) > 10:
        print(f"    ... and {len(changes) - 10} more")

    if dry_run:
        print(f"\n  [DRY RUN] No changes made")
        print(f"  Would commit and push {len(changes)} file(s)")
        return True

    try:
        # Git add
        print(f"  -> git add .")
        subprocess.run(["git", "add", "."], cwd=blog_dir, check=True, capture_output=True)

        # Git commit
        commit_msg = f"Update blog: {len(changes)} file(s) changed"
        print(f"  -> git commit -m \"{commit_msg}\"")
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=blog_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"  [OK] Commit successful")
        elif "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
            print(f"  [INFO] Nothing to commit")
            return True
        else:
            print(f"  [WARN] Commit may have issues: {result.stderr}")

        # Git push
        print(f"  -> git push")
        result = subprocess.run(
            ["git", "push"],
            cwd=blog_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"  [OK] Pushed to GitHub successfully!")
            return True
        else:
            print(f"  [ERROR] Push failed: {result.stderr}")
            print(f"  [HINT] Make sure you've configured the remote repository:")
            print(f"     git remote add origin https://github.com/yourname/your-repo.git")
            return False

    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] Git operation failed: {e}")
        return False
    except FileNotFoundError:
        print(f"  [ERROR] Git not found. Please install Git: https://git-scm.com/")
        return False


def cloudflare_sync(blog_dir: str, output_dir: str = None, dry_run: bool = False) -> bool:
    """
    Deploy to Cloudflare Pages using API.

    Args:
        blog_dir: Blog directory
        output_dir: Output directory (_site)
        dry_run: If True, only show what would be done

    Returns:
        True if successful
    """
    print(f"\n  {'=' * 40}")
    print(f"  [Cloudflare Pages Sync]")
    print(f"  {'=' * 40}")

    # Check environment variables
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    project_name = os.environ.get("CLOUDFLARE_PROJECT_NAME")

    if not all([api_token, account_id, project_name]):
        print(f"  [ERROR] Missing Cloudflare configuration.")
        print(f"  [HINT] Set these environment variables:")
        print(f"     set CLOUDFLARE_API_TOKEN=your_token")
        print(f"     set CLOUDFLARE_ACCOUNT_ID=your_account_id")
        print(f"     set CLOUDFLARE_PROJECT_NAME=your_project_name")
        return False

    if output_dir is None:
        output_dir = os.path.join(blog_dir, "_site")

    if not os.path.isdir(output_dir):
        print(f"  [ERROR] Output directory not found: {output_dir}")
        print(f"  [HINT] Run 'python scripts/publish.py' first")
        return False

    if dry_run:
        print(f"  [DRY RUN] No changes made")
        print(f"  Would deploy {output_dir} to Cloudflare Pages project: {project_name}")
        return True

    try:
        import requests

        # Get the list of files to upload
        files = {}
        output_path = Path(output_dir)
        for file_path in output_path.rglob("*"):
            if file_path.is_file():
                relative = file_path.relative_to(output_path).as_posix()
                with open(file_path, "rb") as f:
                    files[relative] = f.read()

        print(f"  Found {len(files)} file(s) to deploy")

        # Create deployment via Cloudflare API
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/{project_name}/deployments"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

        # Prepare manifest of files
        manifest = {}
        for file_path, content in files.items():
            import hashlib
            manifest[file_path] = hashlib.sha256(content).hexdigest()

        print(f"  -> Creating deployment...")
        response = requests.post(
            url,
            headers=headers,
            json={"manifest": manifest},
        )

        if response.status_code != 200:
            print(f"  [ERROR] API Error: {response.status_code}")
            print(f"     {response.text}")
            return False

        result = response.json()
        if not result.get("success"):
            print(f"  [ERROR] Deployment creation failed: {result.get('errors')}")
            return False

        deployment = result["result"]
        deployment_id = deployment["id"]

        # Upload files that need uploading
        upload_urls = deployment.get("requirements", [])
        if upload_urls:
            print(f"  -> Uploading {len(upload_urls)} file(s)...")
            for req in upload_urls:
                file_path = req["path"]
                if file_path in files:
                    upload_url = req["url"]
                    resp = requests.put(upload_url, data=files[file_path])
                    if resp.status_code not in (200, 201):
                        print(f"  [WARN] Upload failed for {file_path}: {resp.status_code}")

        print(f"  [OK] Deployed to Cloudflare Pages successfully!")
        print(f"  Deployment ID: {deployment_id}")
        return True

    except ImportError:
        print(f"  [ERROR] 'requests' library not found.")
        print(f"  [HINT] Run: pip install requests")
        return False
    except Exception as e:
        print(f"  [ERROR] Cloudflare sync failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Sync blog to GitHub Pages and/or Cloudflare Pages"
    )
    parser.add_argument(
        "--blog-dir",
        default=None,
        help="Blog root directory (default: ./blog)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: blog/_site)",
    )
    parser.add_argument(
        "--git-only",
        action="store_true",
        help="Sync to GitHub Pages only",
    )
    parser.add_argument(
        "--cf-only",
        action="store_true",
        help="Sync to Cloudflare Pages only",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without syncing",
    )

    args = parser.parse_args()

    # Determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    blog_dir = args.blog_dir or os.path.join(project_root, "blog")

    print(f"\n  [Agent Blog Publisher] Syncing...")
    print(f"  Blog dir: {blog_dir}")

    success = True

    # Sync to GitHub
    if not args.cf_only:
        if not git_sync(blog_dir, args.dry_run):
            success = False

    # Sync to Cloudflare
    if not args.git_only:
        if not cloudflare_sync(blog_dir, args.output_dir, args.dry_run):
            success = False

    print(f"\n  {'=' * 40}")
    if success:
        print(f"  [Done] Sync completed successfully!")
    else:
        print(f"  [WARN] Sync completed with some issues.")
    print(f"  {'=' * 40}\n")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
