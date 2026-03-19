---
name: sinapse-adr-writing
description: Use when writing, editing, updating, or publishing Architecture Decision Records (ADR) for the SINAPSE project. Covers MADR v4 template adapted for SINAPSE, Obsidian formatting rules, inter-ADR coherence, and Confluence publication workflow.
---

# Writing ADRs for SINAPSE

## Overview

ADRs follow **MADR v4** adapted for SINAPSE: French, Obsidian wikilinks, Confluence badge macros. Each ADR answers exactly one architectural question and is published to Confluence via the `publish_sinapse_adrs.py` script.

## Quick Reference

| Field | Value |
|-------|-------|
| Vault | Racine du repo (vault Obsidian SINAPSE-ADR) |
| Naming | `ADR-NNN — Titre du sujet.md` |
| Statuses | `Proposé` / `Validé` / `Supersédé` / `En révision` / `Rejeté` |
| Confluence ADR parent | ID `207028250` (= ADR-000) |
| Publish script | `scripts/publish_sinapse_adrs.py` (in claude-skills-pro repo) |
| Index | `ADR-000 — Index.md` |

### Rôles ADR

| Rôle | Personne(s) | Règle |
|------|-------------|-------|
| **Décisionnaire** | Pierre Rossato (unique) | Toujours Pierre, sauf exception explicite |
| **Consulté(s)** | Yolan Maldonado + autres selon contexte | Au minimum Yolan, ajouter les contributeurs pertinents |
| **Informé(s)** | Équipe SINAPSE | Peut inclure DSI CAFAT selon le sujet |

---

## Step 1: Create the ADR File

### File naming

```
ADR-NNN — Titre du sujet.md
```

- `NNN` = next sequential 3-digit number — check the last entry in `ADR-000 — Index.md`
- Title in French, first word capitalized
- File lives at vault root (not in subdirectory)

### Frontmatter

```yaml
---
adr: "NNN"
titre: "Titre du sujet"
date: YYYY-MM-DD
statut: Proposé
deciders: "Pierre Rossato"
consulted: "Yolan Maldonado, Prénom NOM"
informed: "Équipe SINAPSE"
phase: N
prerequisites: "[[ADR-NNN — Titre|ADR-NNN]]"
related: "[[ADR-NNN — Titre|ADR-NNN]]"
tags: [adr, phase-N, domain]
---
```

### Body structure

```markdown
# ADR-NNN — Titre du sujet

| Champ | Valeur |
| --- | --- |
| Statut | Proposé |
| Date | YYYY-MM-DD |
| Décisionnaire(s) | Pierre Rossato |
| Consulté(s) | Yolan Maldonado, Prénom NOM |
| Informé(s) | Équipe SINAPSE |
| Phase | N |
| Prérequis | [[ADR-NNN — Titre\|ADR-NNN]] |
| Lié à | [[ADR-NNN — Titre\|ADR-NNN]] |

## Sommaire

- [[#Contexte et problème]]
- [[#Critères de décision]]
- [[#Options envisagées]]
- [[#Décision]]
  - [[#Conséquences]] (Techniques, Organisationnelles, Métier, Économiques)
  - [[#Critères de vérification]]
- [[#Pours et contres des différentes options envisagées]]
  - [[#Option A : Description courte]]
  - [[#Option B : Description courte]]
  - ✅ [[#Option C : Description courte]]
- [[#Autres informations et références]]

## Contexte et problème

3-5 phrases: describe the current situation, why a decision is needed,
and what constraints apply.

## Critères de décision

- Critère d'évaluation 1
- Critère d'évaluation 2
- Critère d'évaluation 3

## Options envisagées

1. Option A : Description courte
2. Option B : Description courte
3. Option C : Description courte

## Décision

> [!success] Option retenue : Option C : Description courte
> Je choisis X car [justification liée aux Critères de décision].

### Conséquences

Categorize consequences by domain (use only the relevant categories):

#### Techniques
- ... (dettes techniques, maintenabilité, sécurité, évolutivité)

#### Organisationnelles
- ... (rôles, responsabilités, gouvernance)

#### Métier
- ... (impact processus, utilisateurs, conformité)

#### Économiques
- ... (TCO, lien fournisseur, coût d'exploitation)

### Critères de vérification

- [ ] Étape de validation 1
- [ ] Étape de validation 2

## Pours et contres des différentes options envisagées

### Option A : Description courte

- Bon, car ...
- Neutre, car ...
- Mauvais, car ...

### Option B : Description courte

- Bon, car ...
- Mauvais, car ...

### ✅ Option C : Description courte

- Bon, car ...
- Mauvais, car ...

## Autres informations et références

- Ticket Jira : [REC-NNN](https://sinapse-gie-nc.atlassian.net/browse/REC-NNN)
- [Source](https://...)
```

**Important:** `## Sommaire` must be present — the publish script converts it to a Confluence TOC macro automatically.

---

## Step 2: Update ADR-000 Index

Add a row to the appropriate phase table in `ADR-000 — Index.md`:

```markdown
| [[ADR-NNN — Titre\|ADR-NNN]] | Description courte | ADR-XXX | [REC-N](https://sinapse-gie-nc.atlassian.net/browse/REC-N) | Proposé |
```

Also add the ADR to the dependency table (Logique organisationnelle) if it conditions or is conditioned by other ADRs.

---

## Step 3: Quality Checklist

### Content
- [ ] 1 problème = 1 ADR (no mixed topics)
- [ ] Contexte ≤ 5 phrases
- [ ] Options ≤ 4
- [ ] Décision au présent positif: "Je choisis X" (not conditional, first person singular)
- [ ] Conséquences catégorisées par domaine: Techniques, Organisationnelles, Métier, Économiques (utiliser uniquement les catégories pertinentes)
- [ ] Documents satellites (ENF, RG) referenced and linked
- [ ] Ticket Jira référencé dans "Autres informations et références"

### Structure & Metadata
- [ ] All 8 metadata fields present and filled
- [ ] Status is one of the 5 allowed values
- [ ] Date in `YYYY-MM-DD` format
- [ ] Décisionnaire = Pierre Rossato (sauf exception explicite)

### Inter-ADR Coherence
- [ ] No contradiction with prerequisite ADRs
- [ ] No duplicate with an existing ADR
- [ ] All cross-references use wikilinks: `[[ADR-NNN — Titre|ADR-NNN]]`

### Options format
- [ ] Options numbered AND lettered: `1. Option A : Description`, `2. Option B : Description`, etc.
- [ ] Letters in alphabetical order (A, B, C, D...) — no gaps
- [ ] Options list is plain text (no bold, no ✅ in the list)
- [ ] Same `Option X : Description` label used consistently in: Options list, Pros/Cons H3 headers, and Decision reference
- [ ] Chosen option marked with ✅ in TWO places: Sommaire entry (`✅ [[#Option C : ...]]`) and Pros/Cons H3 heading (`### ✅ Option C : ...`)

### Style
- [ ] No em-dashes `—` in body text (use `:` or `,` instead)
- [ ] Acronyms defined at first occurrence

---

## Step 4: Publish to Confluence

**Always use the publish script.** Never use MCP or manual Confluence uploads (10-20 KB size limits cause failures).

### Setup (one-time)

```bash
# Install dependencies
cd <path-to>/claude-skills-pro/scripts
pip install -r requirements.txt

# Set your Confluence credentials (add to ~/.bashrc or ~/.zshrc)
export CONFLUENCE_URL="https://sinapse-gie-nc.atlassian.net/wiki"
export CONFLUENCE_USERNAME="your-email@example.com"
export CONFLUENCE_API_TOKEN="your-api-token"

# Set your Atlassian account ID (for last-editor safety check)
# Find yours: Profile → Account Settings → account ID in URL
export CONFLUENCE_ACCOUNT_ID="712020:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### Copy scripts to vault working directory

```bash
# Copy the publish scripts to the vault publish directory
cp <path-to>/claude-skills-pro/scripts/*.py <vault-root>/.worktrees/clean-publish/
```

### Existing page (update)

```bash
cd <vault-root>/.worktrees/clean-publish

# Always dry-run first
python3 publish_sinapse_adrs.py --dry-run

# Upload one file
python3 publish_sinapse_adrs.py --only ADR-NNN

# Force upload (skip last-editor check — use after merging someone else's edits)
python3 publish_sinapse_adrs.py --only ADR-NNN --force
```

### New page (create + upload)

```bash
cd <vault-root>/.worktrees/clean-publish

# Create the new page AND upload content in one step
python3 publish_sinapse_adrs.py --new "ADR-NNN — Titre du sujet"
```

The script will:
1. Create the page under the ADR parent (`207028250`)
2. Upload the converted content
3. Print the new page ID — add it to `MANIFEST` in the script and to `CC ID.md`

### Safety: last-editor check

The publish script compares `CONFLUENCE_ACCOUNT_ID` against the page's last editor before overwriting. If someone else edited the page on Confluence, the script skips it with a warning. This prevents accidental overwrites of manual edits.

- **CONFLUENCE_ACCOUNT_ID not set**: safety check is disabled (warning printed)
- **--force flag**: explicitly skips the safety check
- **Normal operation**: only overwrites pages you last edited

---

## Obsidian → Confluence Auto-Conversions

The publish script handles these transparently — write Obsidian syntax, it renders correctly in Confluence:

| Obsidian syntax | Confluence result |
|-----------------|-------------------|
| `[[ADR-NNN — Titre\|ADR-NNN]]` | `<ac:link>` with alias |
| `> [!note] Titre` | Blue panel macro |
| `> [!warning] Titre` / `> [!important]` | Yellow warning panel |
| `> [!success] Titre` | Green tip panel (used for "Option retenue") |
| `> [!tip] Titre` | Green tip panel |
| `- [ ]` / `- [x]` | ☐ / ☑ Unicode |
| `## Sommaire` + link list | TOC macro |
| `Proposé` in `<td>` | Yellow badge |
| `Validé` in `<td>` | Green badge |
| `Supersédé` in `<td>` | Grey badge |
| `En révision` in `<td>` | Blue badge |
| `Rejeté` in `<td>` | Red badge |

---

## Confluence Structure

```
Cadrage Technique (207028235)
└── ADR - Architecture Decision Record (207028250)  ← parent for all ADRs
    ├── ADR-001 : OS postes SINAPSE       (222789671)
    ├── ADR-002 : Outils IA               (224231425)
    ├── ADR-003 : Namespace racine        (223608838)
    ├── ADR-004 : Cloud providers NC      (223936523)
    ├── ADR-005 : Sécurité (RGPD/NIS2)   (222101586)
    ├── ADR-006 : Infrastructure          (223674370)
    ├── ADR-007 : IAM                     (223346695)
    ├── ADR-008 : Base de données         (229015555)
    ├── ADR-009 : Modélisation données    (229933057)
    └── ADR-010+ : see CC ID.md for page IDs
```

Full page ID mapping is maintained in `CC ID.md` at vault root.

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Em-dash `—` in body text | Use `:` or `,` or rephrase |
| Décision au conditionnel ("nous choisirions") | "Je choisis" — present tense, positive, first person singular |
| Wikilink without alias `[[Titre]]` | Use `[[Titre\|ADR-NNN]]` to show only the number |
| Upload via MCP or manual Confluence edit | Use `publish_sinapse_adrs.py` script |
| `## Sommaire` omitted | Keep it — auto-converted to TOC macro |
| Decision Maker = "l'équipe" | Must be named individuals (Pierre Rossato) |
| Mermaid/PlantUML diagrams | Convert to PNG/SVG manually before upload (not handled by script) |
| Missing ✅ on chosen option | Add ✅ in TWO places: Sommaire entry and Pros/Cons H3 (`### ✅ Option X`). NOT in Options list. |
| Conséquences as Positif/Négatif | Categorize by domain: Techniques, Organisationnelles, Métier, Économiques |
| Bold or ✅ in Options list | Options list is plain text: `1. Option A : Desc` — no bold, no ✅ |
| Décisionnaire = "l'équipe" or multiple people | Always Pierre Rossato as unique décisionnaire |
