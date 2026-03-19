#!/usr/bin/env python3
"""
Upload Markdown to Confluence (v2 - Improved)

Converts Markdown to Confluence storage format and uploads via REST API.
Used as a library by publish_sinapse_adrs.py and can also run standalone.

Key functions:
  - parse_markdown_file()        : Extract frontmatter, content, title from .md
  - convert_markdown_to_storage(): Markdown → Confluence storage HTML
  - upload_to_confluence()       : Upload/create page via REST API

Requirements:
    pip install atlassian-python-api md2cf python-dotenv PyYAML mistune

IMPORTANT: DO NOT USE MCP FOR CONFLUENCE PAGE UPLOADS — size limits apply!
"""

import sys
import argparse
import re
import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import yaml

# Check dependencies
try:
    import mistune
    from md2cf.confluence_renderer import ConfluenceRenderer
    from confluence_auth import get_confluence_client
except ImportError as e:
    print(f"ERROR: Missing dependency: {e}", file=sys.stderr)
    print("Install with: pip install atlassian-python-api md2cf python-dotenv PyYAML mistune", file=sys.stderr)
    sys.exit(1)


def parse_markdown_file(file_path: Path) -> Tuple[Dict, str, Optional[str]]:
    """
    Parse markdown file and extract frontmatter, content, and title.

    Args:
        file_path: Path to markdown file

    Returns:
        Tuple of (frontmatter_dict, markdown_content, extracted_title)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for YAML frontmatter
    frontmatter = {}
    markdown_content = content
    title = None

    # Parse frontmatter (between --- markers)
    if content.startswith('---\n'):
        parts = content.split('---\n', 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                markdown_content = parts[2].strip()
            except yaml.YAMLError as e:
                print(f"WARNING: Failed to parse YAML frontmatter: {e}", file=sys.stderr)

    # Extract title from frontmatter
    if 'title' in frontmatter:
        title = frontmatter['title']

    # Fallback: extract title from first H1 heading
    if not title:
        match = re.search(r'^#\s+(.+)$', markdown_content, re.MULTILINE)
        if match:
            title = match.group(1).strip()

    # Last fallback: use filename
    if not title:
        title = file_path.stem.replace('_', ' ')

    return frontmatter, markdown_content, title


def convert_markdown_to_storage(markdown_content: str) -> Tuple[str, List[str]]:
    """
    Convert markdown to Confluence storage format using md2cf.

    Uses base ConfluenceRenderer (NOT MermaidConfluenceRenderer)
    to avoid breaking regular markdown image handling.

    For Mermaid/PlantUML diagrams: Convert them to PNG/SVG files BEFORE calling
    this function, then use markdown image syntax: ![alt](path/to/image.png)

    Args:
        markdown_content: Markdown text with image paths

    Returns:
        Tuple of (storage_html, attachments_list)
    """
    # Use base ConfluenceRenderer
    renderer = ConfluenceRenderer()

    # Parse markdown
    parser = mistune.Markdown(renderer=renderer)
    storage_html = parser(markdown_content)

    # Get attachments (image paths found in markdown)
    attachments = getattr(renderer, 'attachments', [])

    return storage_html, attachments


def upload_to_confluence(
    confluence,
    page_id: str,
    title: str,
    storage_html: str,
    attachments: List[str],
    space_key: Optional[str] = None,
    parent_id: Optional[str] = None,
    skip_existing_attachments: bool = True
) -> Dict:
    """
    Upload page content and attachments to Confluence via REST API.

    Args:
        confluence: Confluence client instance
        page_id: Page ID (for updates) or None (for creates)
        title: Page title
        storage_html: Content in Confluence storage format
        attachments: List of file paths to upload as attachments
        space_key: Space key (required for creates)
        parent_id: Optional parent page ID
        skip_existing_attachments: If True, skip uploading attachments that already exist

    Returns:
        Dict with 'id', 'title', 'version', 'url' keys
    """
    if page_id:
        # UPDATE MODE
        try:
            page_info = confluence.get_page_by_id(page_id, expand='version')
            current_version = page_info['version']['number']
        except Exception as e:
            raise ValueError(f"Failed to fetch current version for page {page_id}: {e}")

        new_version = current_version + 1

        print(f"📄 Updating page {page_id}")
        print(f"   Current version: {current_version}")
        print(f"   New version: {new_version}")
        print(f"   Storage content length: {len(storage_html)} characters")
        print(f"   Attachments to upload: {len(attachments)}")

        try:
            result = confluence.update_page(
                page_id=page_id,
                title=title,
                body=storage_html,
                parent_id=parent_id,
                type='page',
                representation='storage',
                minor_edit=False,
                version_comment=f"Updated with images (v{current_version} → v{new_version})"
            )

            print(f"✅ Page updated successfully")
            print(f"   Version: {result.get('version', {}).get('number', 'unknown')}")

        except Exception as e:
            print(f"❌ ERROR updating page: {e}")
            raise

        # Upload attachments
        if attachments:
            print(f"\n📎 Uploading {len(attachments)} attachments...")
            _upload_attachments(confluence, page_id, attachments, skip_existing_attachments)

        return {
            'id': result['id'],
            'title': result['title'],
            'version': result.get('version', {}).get('number', 'unknown'),
            'url': confluence.url + result['_links']['webui']
        }

    else:
        # CREATE MODE
        if not space_key:
            raise ValueError("space_key is required to create new page")

        print(f"📄 Creating new page in space {space_key}")
        print(f"   Storage content length: {len(storage_html)} characters")
        print(f"   Attachments to upload: {len(attachments)}")

        try:
            result = confluence.create_page(
                space=space_key,
                title=title,
                body=storage_html,
                parent_id=parent_id,
                type='page',
                representation='storage'
            )

            new_page_id = result['id']
            print(f"✅ Page created successfully")
            print(f"   Page ID: {new_page_id}")
            print(f"   Version: {result.get('version', {}).get('number', 'unknown')}")

        except Exception as e:
            print(f"❌ ERROR creating page: {e}")
            raise

        # Upload attachments
        if attachments:
            print(f"\n📎 Uploading {len(attachments)} attachments...")
            _upload_attachments(confluence, new_page_id, attachments, skip_existing_attachments)

        return {
            'id': result['id'],
            'title': result['title'],
            'version': result.get('version', {}).get('number', 'unknown'),
            'url': confluence.url + result['_links']['webui']
        }


def _upload_attachments(
    confluence,
    page_id: str,
    attachments: List[str],
    skip_existing: bool = True
) -> None:
    """Upload attachment files to a Confluence page."""
    for i, attachment_path in enumerate(attachments, 1):
        filename = os.path.basename(attachment_path)
        print(f"   {i}. {filename}...", end=' ')

        if not os.path.exists(attachment_path):
            print(f"❌ File not found: {attachment_path}")
            continue

        try:
            if skip_existing:
                existing_attachments = confluence.get_attachments_from_content(page_id)
                already_exists = any(
                    att['title'] == filename
                    for att in existing_attachments.get('results', [])
                )

                if already_exists:
                    print("(already exists, skipping)")
                    continue

            ext = os.path.splitext(filename)[1].lower()
            content_type_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml',
                '.pdf': 'application/pdf'
            }
            content_type = content_type_map.get(ext, 'application/octet-stream')

            confluence.attach_file(
                filename=attachment_path,
                name=filename,
                content_type=content_type,
                page_id=page_id,
                comment=f"Uploaded via publish_sinapse_adrs.py"
            )
            print("✅")

        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Upload Markdown to Confluence (v2)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.md --id 780369923
  %(prog)s document.md --space SINAPSE --parent-id 123456
  %(prog)s document.md --id 780369923 --dry-run
        """
    )

    parser.add_argument('file', type=str, help='Markdown file to upload')
    parser.add_argument('--id', type=str, help='Page ID (for updates)')
    parser.add_argument('--space', type=str, help='Space key (required for new pages)')
    parser.add_argument('--title', type=str, help='Page title (overrides frontmatter/H1)')
    parser.add_argument('--parent-id', type=str, help='Parent page ID')
    parser.add_argument('--dry-run', action='store_true', help='Preview without uploading')
    parser.add_argument('--env-file', type=str, help='Path to .env file with credentials')
    parser.add_argument('--force-reupload', action='store_true',
                        help='Re-upload all attachments even if they already exist')

    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"ERROR: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        frontmatter, markdown_content, extracted_title = parse_markdown_file(file_path)
    except Exception as e:
        print(f"ERROR: Failed to parse markdown file: {e}", file=sys.stderr)
        sys.exit(1)

    title = args.title or extracted_title
    page_id = args.id or frontmatter.get('confluence', {}).get('id')
    space_key = args.space or frontmatter.get('confluence', {}).get('space')
    parent_id = args.parent_id or frontmatter.get('parent', {}).get('id')

    if not page_id and not space_key:
        print("ERROR: Either --id (for update) or --space (for create) must be provided", file=sys.stderr)
        sys.exit(1)

    try:
        print(f"\n📖 Reading markdown file: {args.file}")
        storage_content, attachments = convert_markdown_to_storage(markdown_content)
        print(f"   Storage HTML: {len(storage_content)} chars, {len(attachments)} images")
    except Exception as e:
        print(f"ERROR: Conversion failed: {e}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print("=" * 70)
        print("DRY-RUN MODE — No changes will be made")
        print(f"Title: {title} | Mode: {'UPDATE' if page_id else 'CREATE'}")
        print(f"Content preview: {storage_content[:300]}...")
        print("=" * 70)
        return

    try:
        confluence = get_confluence_client(env_file=args.env_file)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\n📤 Uploading to Confluence...")
    result = upload_to_confluence(
        confluence=confluence,
        page_id=page_id,
        title=title,
        storage_html=storage_content,
        attachments=attachments,
        space_key=space_key,
        parent_id=parent_id,
        skip_existing_attachments=not args.force_reupload
    )
    print(f"\n✅ Done: {result['url']}")


if __name__ == '__main__':
    main()
