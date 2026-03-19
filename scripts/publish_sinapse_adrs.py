#!/usr/bin/env python3
"""
Batch publish SINAPSE ADRs/ENFs/RGs to Confluence.

Handles:
  - Wikilink [[filename|alias]] → <ac:link> page macro
  - DONE suffix removal from file titles
  - Hierarchical upload (ADR-000 as index, ADR-001+ as children)
  - ENF and RG document organisation
  - Last-editor safety check (prevents overwriting others' edits)

Upload hierarchy:
  Cadrage Technique (207028235)
  ├── ENF - Exigences Non Fonctionnelles (206635029)
  │   ├── ENF-002 : Outillage développeur SINAPSE
  │   ├── ENF-003 : Workflow agentique Claude Code SINAPSE
  │   └── ENF-004 : Configuration Keycloak SINAPSE
  ├── ADR - Architecture Decision Record (207028250) ← updated by ADR-000
  │   ├── ADR-001 to ADR-023
  │   └── (new ADRs via --new flag)
  └── RG - Règles de Gestion
      └── RG-001 : Politique usage IA SINAPSE

Setup:
    1. pip install -r requirements.txt
    2. Set Confluence credentials (see confluence_auth.py for discovery chain)
    3. Set CONFLUENCE_ACCOUNT_ID to your Atlassian account ID (for safety check)

Usage:
    python3 publish_sinapse_adrs.py --dry-run              # Preview all
    python3 publish_sinapse_adrs.py                        # Publish all
    python3 publish_sinapse_adrs.py --only ADR-004         # One file only
    python3 publish_sinapse_adrs.py --new "ADR-024 — X"   # Create + upload new page
"""

import sys
import os
import re
import argparse
from pathlib import Path

# ─── Path setup ──────────────────────────────────────────────────────────────
VAULT_DIR = Path(__file__).parent
SCRIPTS_DIR = Path(__file__).resolve().parent

# Add scripts directory to path for co-located modules (confluence_auth, upload_confluence_v2)
sys.path.insert(0, str(SCRIPTS_DIR))

# Ensure pip-installed packages are importable
import site
for _sp in site.getsitepackages() + [site.getusersitepackages()]:
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

from upload_confluence_v2 import (
    parse_markdown_file,
    convert_markdown_to_storage,
    upload_to_confluence,
)
from confluence_auth import get_confluence_client

# ─── Confluence constants ─────────────────────────────────────────────────────
SPACE_KEY           = "SINAPSE"
ADR_SECTION_ID      = "207028250"   # "ADR - Architecture Decision Record" → becomes ADR-000
ENF_PARENT_ID       = "206635029"   # "ENF - Exigences Non Fonctionnelles"
CADRAGE_ID          = "207028235"   # "Cadrage Technique" → parent for RG section

# Safety: your Atlassian account ID (used by last-editor check)
# Set via environment variable: export CONFLUENCE_ACCOUNT_ID="712020:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
# Find yours at: https://sinapse-gie-nc.atlassian.net/wiki/people → click your profile → ID in URL
MY_ACCOUNT_ID = os.environ.get("CONFLUENCE_ACCOUNT_ID", "")

# ─── Upload manifest ──────────────────────────────────────────────────────────
# (file_stem, page_id_to_update | None, parent_id_for_create | None)
# page_id → UPDATE existing page; parent_id → CREATE new child page
MANIFEST = [
    # ADR-000 replaces the ADR section stub (already published — UPDATE)
    ("ADR-000 — Index",                                            "207028250",  None),
    # ADR-001 to 023: already published — UPDATE with their page IDs
    ("ADR-001 — Configuration poste de développement DONE",       "222789671",  None),
    ("ADR-002 — Outils IA pour le développement DONE",            "224231425",  None),
    ("ADR-003 — Namespace racine DONE",                           "223608838",  None),
    ("ADR-004 — Cloud providers adaptés à la Nouvelle-Calédonie", "223936523",  None),
    ("ADR-005 — Sécurité et Conformité (RGPD-NIS2)",              "222101586",  None),
    ("ADR-006 — Infrastructure et Déploiement",                   "223674370",  None),
    ("ADR-007 — IAM et Gestion des accès",                        "223346695",  None),
    ("ADR-008 — Base de données",                                 "229015555",  None),
    ("ADR-009 — Modélisation des données et Schéma canonique",    "229933057",  None),
    ("ADR-010 — MDM et Gouvernance des données",                  "230227972",  None),
    ("ADR-011 — Gestion documentaire (GED)",                      "233340929",  None),
    ("ADR-012 — Broker événementiel",                             "251527178",  None),
    ("ADR-013 — ETL et Intégration de données",                   "252542977",  None),
    ("ADR-014 — Stratégie de migration des données",              "252903425",  None),
    ("ADR-015 — Intégration des systèmes Legacy",                "253034497",  None),
    ("ADR-016 — API Management et Gateway",                      "253263873",  None),
    ("ADR-017 — Backend",                                        "255131664",  None),
    ("ADR-018 — Frontend",                                       "255918095",  None),
    ("ADR-019 — BPM et Workflow",                                  "256933889",  None),
    ("ADR-020 — Système de traces",                                 "260014086",  None),
    ("ADR-021 — CI-CD et DevOps",                                   "261357591",  None),
    ("ADR-022 — Monitoring et Observabilité",                        "262209538",  None),
    ("ADR-023 — Tests et Qualité",                                   "263094273",  None),
    # ENFs
    ("ENF-002 — Outillage développeur SINAPSE",                   "222134436",  None),
    ("ENF-003 — Workflow agentique Claude Code SINAPSE",          "223838211",  None),
    ("ENF-004 — Configuration Keycloak SINAPSE",                  "222789704",  None),
    ("ENF-007 — PKI et certificats SINAPSE",                     "268795909",  None),
    # Catalogue
    ("CATALOGUE — Solutions SaaS et Logiciels",                   "229900304",  None),
    # WIKI
    ("WIKI — Pratiques de sécurité",                              "232521729",  None),
]


# ─── Preprocessing functions ──────────────────────────────────────────────────

def convert_callouts(content: str) -> str:
    """
    Convert Obsidian callout blocks to Confluence panel macros (token/placeholder approach).

    Obsidian syntax:
        > [!type] Optional Title
        > Line 1
        > Line 2

    Maps to <ac:structured-macro ac:name="…"> with rich-text body.
    The body is converted recursively via convert_markdown_to_storage().
    """
    _TYPE_MAP = {
        "note":      "note",
        "warning":   "warning",
        "tip":       "tip",
        "important": "warning",
        "info":      "info",
        "success":   "tip",
    }

    # Match a full callout block: opening line + any number of "> content" lines
    pattern = re.compile(
        r"^> \[!(\w+)\][ \t]*(.*?)\n((?:>[ \t]?[^\n]*\n?)*)",
        re.MULTILINE,
    )

    def _replace(m: re.Match) -> str:
        callout_type = m.group(1).lower()
        title_text   = m.group(2).strip()
        title_text   = re.sub(r'\*\*(.*?)\*\*', r'\1', title_text)
        body_lines   = m.group(3)

        macro_name = _TYPE_MAP.get(callout_type, "note")

        # Strip leading "> " from each body line
        stripped_lines = []
        for line in body_lines.splitlines():
            stripped_lines.append(re.sub(r"^>[ \t]?", "", line))
        body_md = "\n".join(stripped_lines).strip()

        # Resolve wikilinks in the body before converting (uses the module-level TITLE_MAP)
        if body_md and TITLE_MAP:
            body_md = resolve_wikilinks(body_md, TITLE_MAP)
        body_html, _ = convert_markdown_to_storage(body_md) if body_md else ("", [])
        if body_md and TITLE_MAP:
            body_html = expand_placeholders(body_html)

        title_xml = (
            f'<ac:parameter ac:name="title">{title_text}</ac:parameter>'
            if title_text else ""
        )
        macro = (
            f'<ac:structured-macro ac:name="{macro_name}">'
            f'{title_xml}'
            f'<ac:rich-text-body>{body_html}</ac:rich-text-body>'
            f'</ac:structured-macro>'
        )
        token = f"CALL{len(PLACEHOLDER_MAP):04d}END"
        PLACEHOLDER_MAP[token] = macro
        return token + "\n"

    return pattern.sub(_replace, content)


def convert_sommaire(content: str) -> str:
    """
    Replace an Obsidian '## Sommaire' section (heading + bullet list of internal links)
    with a Confluence TOC macro token.
    """
    toc_macro = (
        '<ac:structured-macro ac:name="toc">'
        '<ac:parameter ac:name="maxLevel">3</ac:parameter>'
        '</ac:structured-macro>'
    )
    token = f"TOCM{len(PLACEHOLDER_MAP):04d}END"
    PLACEHOLDER_MAP[token] = toc_macro

    # Match "## Sommaire" heading + blank line + any number of bullet lines
    pattern = re.compile(
        r"^## Sommaire\n\n(?:[ \t]*- [^\n]*\n)*",
        re.MULTILINE,
    )
    result, count = pattern.subn(token + "\n\n", content)
    if count == 0:
        # No sommaire found — remove the unused token
        del PLACEHOLDER_MAP[token]
    return result


def convert_checkboxes(content: str) -> str:
    """
    Convert Markdown checkboxes to Unicode symbols (no placeholder needed).
      - [ ]  →  ☐
      - [x]  →  ☑
      - [X]  →  ☑
    """
    content = re.sub(r"- \[x\]", "- ☑", content, flags=re.IGNORECASE)
    content = re.sub(r"- \[ \]", "- ☐", content)
    return content


def add_status_badges(storage_html: str) -> str:
    """
    Post-process the storage HTML to replace status text inside <td> cells
    with Confluence Status macro badges.
    """
    _STATUS_COLOURS = {
        "Proposé":     "Yellow",
        "Validé":      "Green",
        "Supersédé":   "Grey",
        "En révision": "Blue",
        "Rejeté":      "Red",
    }

    for status_text, colour in _STATUS_COLOURS.items():
        badge = (
            f'<ac:structured-macro ac:name="status">'
            f'<ac:parameter ac:name="colour">{colour}</ac:parameter>'
            f'<ac:parameter ac:name="title">{status_text}</ac:parameter>'
            f'</ac:structured-macro>'
        )
        # Only replace inside <td>…</td> to avoid false positives in body text
        storage_html = re.sub(
            rf"(<td[^>]*>)(.*?)({re.escape(status_text)})(.*?)(</td>)",
            lambda m: m.group(1) + m.group(2) + badge + m.group(4) + m.group(5),
            storage_html,
            flags=re.DOTALL,
        )
    return storage_html


# ─── Wikilink preprocessing ───────────────────────────────────────────────────

def build_title_map(vault_dir: Path) -> dict[str, str]:
    """
    Scan all .md files in vault_dir, extract H1 title.
    Returns {file_stem: h1_title}.
    """
    title_map: dict[str, str] = {}
    for md_file in sorted(vault_dir.glob("*.md")):
        stem = md_file.stem
        with open(md_file, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("# "):
                    title_map[stem] = stripped[2:].strip()
                    break
    return title_map


def _normalize_fallback(target: str) -> str:
    """
    Convert a filename stem to a plausible Confluence page title
    when the file is not in the upload set.

    Rules:
      - Strip trailing ' DONE'
      - Replace ' — ' with ' : '
    """
    t = target.strip()
    if t.endswith(" DONE"):
        t = t[:-5]
    t = t.replace(" — ", " : ")
    return t


def resolve_wikilinks(content: str, title_map: dict[str, str]) -> str:
    """
    Convert Obsidian wikilinks to Confluence <ac:link> macros using a
    two-pass placeholder approach:

      Pass 1 (pre-mistune): replace [[...]] with opaque tokens so mistune
                            never sees the XML.
      Pass 2 (post-mistune): called via `expand_placeholders()` on the
                             resulting storage HTML.

    Returns the markdown with placeholders inserted.
    The sibling dict PLACEHOLDER_MAP is populated for the second pass.
    """
    def _replace(m: re.Match) -> str:
        inner = m.group(1).replace("\\|", "|")

        if "|" in inner:
            target, alias = inner.split("|", 1)
            target, alias = target.strip(), alias.strip()
        else:
            target, alias = inner.strip(), None

        # Internal anchor links: strip to readable text
        if target.startswith("#"):
            return alias if alias else target[1:]

        # Resolve Confluence page title
        conf_title = title_map.get(target, _normalize_fallback(target))

        if alias:
            macro = (
                f'<ac:link>'
                f'<ri:page ri:content-title="{conf_title}" />'
                f'<ac:plain-text-link-body>'
                f'<![CDATA[{alias}]]>'
                f'</ac:plain-text-link-body>'
                f'</ac:link>'
            )
        else:
            macro = f'<ac:link><ri:page ri:content-title="{conf_title}" /></ac:link>'

        token = f"WKLN{len(PLACEHOLDER_MAP):04d}END"
        PLACEHOLDER_MAP[token] = macro
        return token

    return re.sub(r"\[\[([^\]]+)\]\]", _replace, content)


# Module-level registries shared by all preprocessing functions
PLACEHOLDER_MAP: dict[str, str] = {}
TITLE_MAP: dict[str, str] = {}   # set once per file in upload_file()


def expand_placeholders(storage_html: str) -> str:
    """Replace opaque tokens in the storage HTML with <ac:link> macros."""
    for token, macro in PLACEHOLDER_MAP.items():
        storage_html = storage_html.replace(token, macro)
    return storage_html


# ─── Upload helpers ───────────────────────────────────────────────────────────

def check_last_editor(confluence, page_id: str) -> tuple[bool, str, str]:
    """
    Check if the last editor of a page is the expected user (MY_ACCOUNT_ID).
    Returns (is_safe, editor_name, edit_date).

    If MY_ACCOUNT_ID is not set, returns (True, ...) — safety check is skipped.
    """
    page = confluence.get_page_by_id(page_id, expand='version')
    editor = page['version']['by']
    editor_id = editor.get('accountId', '')
    editor_name = editor.get('displayName', 'Unknown')
    edit_date = page['version']['when'][:10]

    if not MY_ACCOUNT_ID:
        return (True, editor_name, edit_date)

    return (editor_id == MY_ACCOUNT_ID, editor_name, edit_date)


def upload_file(
    confluence,
    stem: str,
    page_id: str | None,
    parent_id: str | None,
    title_map: dict[str, str],
    dry_run: bool = False,
) -> dict | None:
    """Find file by stem, preprocess, convert, upload."""
    candidates = list(VAULT_DIR.glob(f"{stem}.md"))
    if not candidates:
        print(f"  ⚠️  File not found: {stem}.md — skipping")
        return None

    file_path = candidates[0]
    frontmatter, markdown_content, title = parse_markdown_file(file_path)
    title = _normalize_fallback(title)

    # Reset shared registries for this file
    PLACEHOLDER_MAP.clear()
    TITLE_MAP.clear()
    TITLE_MAP.update(title_map)

    # ── Strip H1 from body (title comes from API, avoids duplication) ────
    markdown_content = re.sub(r'^#\s+.+\n*', '', markdown_content, count=1, flags=re.MULTILINE)

    # ── Preprocessing (before mistune) ──────────────────────────────────────
    markdown_content = convert_callouts(markdown_content)              # → CALL tokens
    markdown_content = convert_sommaire(markdown_content)              # → TOCM token
    markdown_content = convert_checkboxes(markdown_content)           # → ☐ ☑ (no tokens)
    markdown_content = resolve_wikilinks(markdown_content, title_map)  # → WKLN tokens

    # Convert to Confluence storage format
    storage_html, attachments = convert_markdown_to_storage(markdown_content)

    # ── Post-processing (after mistune) ─────────────────────────────────────
    storage_html = expand_placeholders(storage_html)   # WKLN + CALL + TOCM → XML
    storage_html = add_status_badges(storage_html)     # Statut text → badge coloré

    mode_label = f"UPDATE {page_id}" if page_id else f"CREATE under {parent_id}"
    print(f"\n  {'─'*56}")
    print(f"  📄 {title}")
    print(f"     Mode: {mode_label}")
    print(f"     Size: {len(storage_html):,} chars")

    if dry_run:
        print(f"     [DRY-RUN] First 200 chars of storage:")
        print(f"     {storage_html[:200].replace(chr(10), ' ')}")
        return {"id": page_id or "NEW", "title": title, "url": "#dry-run"}

    # Safety check: abort if last editor is not us (skip if CONFLUENCE_ACCOUNT_ID not set)
    if page_id and confluence:
        is_safe, editor_name, edit_date = check_last_editor(confluence, page_id)
        if not is_safe:
            print(f"     ⛔ SKIPPED — last edited by {editor_name} on {edit_date}")
            print(f"        Set CONFLUENCE_ACCOUNT_ID or use --force to override")
            return None

    import time as _time
    for attempt in range(1, 4):
        try:
            result = upload_to_confluence(
                confluence=confluence,
                page_id=page_id,
                title=title,
                storage_html=storage_html,
                attachments=attachments,
                space_key=SPACE_KEY,
                parent_id=parent_id,
            )
            print(f"     ✅ {result['url']}")
            return result
        except Exception as e:
            if "ConflictException" in str(e) and attempt < 3:
                wait = attempt * 3
                print(f"     ⚠️  Confluence version conflict (attempt {attempt}/3), retrying in {wait}s...")
                _time.sleep(wait)
            else:
                raise


def create_rg_parent(confluence, dry_run: bool) -> str:
    """Create 'RG - Règles de Gestion' page as child of Cadrage Technique."""
    title = "RG - Règles de Gestion"
    body = (
        "<p>Cet espace contient les règles de gestion du SI SINAPSE.</p>"
        "<p>Les règles de gestion définissent les comportements, politiques et contraintes "
        "qui s'appliquent au système. Elles répondent à la question "
        "«&nbsp;quelles règles métier et opérationnelles le système doit-il respecter&nbsp;».</p>"
        "<p>Des écarts peuvent être décidés et doivent être tracés dans des ADR.</p>"
    )

    print(f"\n  {'─'*56}")
    print(f"  📁 Creating: {title}")
    print(f"     Parent: Cadrage Technique ({CADRAGE_ID})")

    if dry_run:
        print("     [DRY-RUN]")
        return "DRY-RUN-RG-ID"

    result = confluence.create_page(
        space=SPACE_KEY,
        title=title,
        body=body,
        parent_id=CADRAGE_ID,
        type="page",
        representation="storage",
    )
    rg_id = result["id"]
    print(f"     ✅ Created RG parent: ID {rg_id}")
    return rg_id


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish SINAPSE ADRs/ENFs/RGs to Confluence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 publish_sinapse_adrs.py --dry-run          # Preview all
  python3 publish_sinapse_adrs.py                    # Publish all
  python3 publish_sinapse_adrs.py --only ADR-004     # One file only
  python3 publish_sinapse_adrs.py --new "ADR-024 — Nouveau sujet"  # Create new page
  python3 publish_sinapse_adrs.py --skip-rg          # Skip RG parent creation
  python3 publish_sinapse_adrs.py --force --only ADR-004  # Skip last-editor check

Environment:
  CONFLUENCE_ACCOUNT_ID   Your Atlassian account ID (for last-editor safety check)
  CONFLUENCE_URL          Confluence base URL
  CONFLUENCE_USERNAME     Your Atlassian email
  CONFLUENCE_API_TOKEN    Your Atlassian API token
        """,
    )
    parser.add_argument("--dry-run",  action="store_true", help="Preview without uploading")
    parser.add_argument("--only",     type=str,            help="Publish only files starting with this prefix")
    parser.add_argument("--new",      type=str,            help="Create new page under ADR parent (provide file stem)")
    parser.add_argument("--skip-rg",  action="store_true", help="Skip RG parent page creation")
    parser.add_argument("--force",    action="store_true", help="Skip last-editor safety check")
    args = parser.parse_args()

    print("=" * 60)
    print("🚀  SINAPSE ADR Confluence Publisher")
    print(f"    Vault : {VAULT_DIR}")
    print(f"    Mode  : {'DRY-RUN ⚡' if args.dry_run else 'LIVE 🔴'}")
    if args.force:
        print(f"    Force : ON (last-editor check disabled)")
    print("=" * 60)

    # Warn if safety check is disabled
    if not MY_ACCOUNT_ID and not args.dry_run and not args.force:
        print("\n⚠️  CONFLUENCE_ACCOUNT_ID not set — last-editor safety check disabled")
        print("   Set it: export CONFLUENCE_ACCOUNT_ID='712020:your-atlassian-id'")
        print("   Find yours: Profile → Account Settings → account ID in URL")

    # Temporarily disable safety check if --force
    global MY_ACCOUNT_ID
    if args.force:
        MY_ACCOUNT_ID = ""

    # Build title map from every .md in the vault
    print("\n📚 Building title map...")
    title_map = build_title_map(VAULT_DIR)
    print(f"   {len(title_map)} files indexed")

    # Connect to Confluence
    if not args.dry_run:
        confluence = get_confluence_client()
        print("   ✅ Connected to Confluence")
    else:
        confluence = None

    # ── Handle --new: create a new page under ADR parent ─────────────────────
    if args.new:
        print(f"\n📤 Creating new page: {args.new}")
        result = upload_file(confluence, args.new, None, ADR_SECTION_ID, title_map, args.dry_run)
        if result and not args.dry_run:
            print(f"\n💡 New page ID: {result['id']}")
            print(f"   Add this to MANIFEST in publish_sinapse_adrs.py:")
            print(f'   ("{args.new}",{" " * max(1, 56 - len(args.new))}"{result["id"]}",  None),')
            print(f"   Also add to CC ID.md in the vault.")
        print(f"\n{'='*60}")
        print("✅  Done!")
        print("=" * 60)
        return

    # ── Upload manifest (ADRs + ENFs + CATALOGUE + WIKI) ─────────────────────
    print("\n📤 Uploading documents...")
    for stem, page_id, parent_id in MANIFEST:
        if args.only and not stem.upper().startswith(args.only.upper()):
            continue
        upload_file(confluence, stem, page_id, parent_id, title_map, args.dry_run)

    # ── RG-001 (UPDATE — page already exists) ────────────────────────────────
    rg_stem = "RG-001 — Politique usage IA SINAPSE"
    if not args.only or rg_stem.upper().startswith(args.only.upper()):
        upload_file(confluence, rg_stem, "222789726", None, title_map, args.dry_run)

    print(f"\n{'='*60}")
    print("✅  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
