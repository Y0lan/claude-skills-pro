# Claude Skills Pro

Skills et scripts partages pour Claude Code, utilises par l'equipe SINAPSE (GIE SINAPSE, Noumea, Nouvelle-Caledonie).

## Skills disponibles

| Skill | Description | Usage |
|-------|-------------|-------|
| **sinapse-adr-writing** | Ecriture d'ADR (Architecture Decision Records) pour SINAPSE | Template MADR v4 adapte, Obsidian, Confluence |
| **madr-compliance** | Conformite MADR v4 upstream | Audit et review d'ADR contre la spec officielle |

## Scripts

| Script | Description |
|--------|-------------|
| **publish_sinapse_adrs.py** | Publication batch des ADR/ENF/RG vers Confluence |
| **upload_confluence_v2.py** | Convertisseur Markdown → Confluence storage format |
| **confluence_auth.py** | Decouverte automatique des credentials Confluence |

## Installation

### 1. Installer les skills

#### Methode projet (recommande pour l'equipe)

```bash
# Depuis la racine du vault SINAPSE-ADR
mkdir -p .claude/skills
cp -r sinapse-adr-writing .claude/skills/
cp -r madr-compliance .claude/skills/
```

Les skills projet-level sont automatiquement charges pour toute personne utilisant Claude Code dans le repo.

#### Methode globale (user-level)

```bash
cp -r sinapse-adr-writing ~/.claude/skills/
cp -r madr-compliance ~/.claude/skills/
```

### 2. Installer les scripts de publication

```bash
# Installer les dependances Python
cd scripts
pip install -r requirements.txt

# Copier les scripts dans le repertoire de publication du vault
cp *.py <vault-root>/.worktrees/clean-publish/
```

### 3. Configurer les credentials

```bash
# Ajouter a ~/.bashrc ou ~/.zshrc

# Confluence credentials
export CONFLUENCE_URL="https://sinapse-gie-nc.atlassian.net/wiki"
export CONFLUENCE_USERNAME="votre-email@example.com"
export CONFLUENCE_API_TOKEN="votre-api-token"

# Safety check: votre Atlassian account ID
# Trouver le votre : Profil → Account Settings → ID dans l'URL
export CONFLUENCE_ACCOUNT_ID="712020:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

## Usage du script de publication

```bash
cd <vault-root>/.worktrees/clean-publish

# Previsualiser (dry-run)
python3 publish_sinapse_adrs.py --dry-run

# Publier toutes les ADR
python3 publish_sinapse_adrs.py

# Publier une seule ADR
python3 publish_sinapse_adrs.py --only ADR-004

# Creer et publier une nouvelle page
python3 publish_sinapse_adrs.py --new "ADR-024 — Nouveau sujet"

# Forcer la publication (ignore le check last-editor)
python3 publish_sinapse_adrs.py --only ADR-004 --force
```

### Safety: last-editor check

Le script verifie que le dernier editeur de la page Confluence est bien vous avant d'ecraser. Si quelqu'un d'autre a edite la page manuellement, le script refuse de publier (pour eviter d'ecraser ses modifications).

- **CONFLUENCE_ACCOUNT_ID non defini** : check desactive (warning affiche)
- **--force** : ignore le check explicitement
- **Fonctionnement normal** : ne publie que les pages dont vous etes le dernier editeur

## Structure

```
claude-skills-pro/
├── sinapse-adr-writing/
│   └── SKILL.md          # Template ADR SINAPSE (MADR v4 adapte FR)
├── madr-compliance/
│   └── SKILL.md          # Spec MADR v4 upstream + mapping SINAPSE
├── scripts/
│   ├── publish_sinapse_adrs.py   # Publication batch vers Confluence
│   ├── upload_confluence_v2.py   # Markdown → Confluence storage
│   ├── confluence_auth.py        # Credential discovery
│   └── requirements.txt         # Dependances Python
└── README.md
```

## Template ADR SINAPSE

Chaque ADR suit le template MADR v4 adapte pour SINAPSE :

- **Langue** : Francais
- **Format** : Obsidian Markdown (wikilinks, callouts)
- **Publication** : Confluence via `publish_sinapse_adrs.py` (jamais MCP)
- **Consequences** : categorisees par domaine (Techniques, Organisationnelles, Metier, Economiques)
- **Pros/Cons** : format `Bon, car` / `Mauvais, car` / `Neutre, car`

### Sections obligatoires

1. Contexte et probleme (3-5 phrases)
2. Criteres de decision
3. Options envisagees (numerotees A, B, C...)
4. Decision (`Je choisis X car...`)
5. Consequences (categorisees par domaine)
6. Criteres de verification
7. Pours et contres des differentes options
8. Autres informations et references
