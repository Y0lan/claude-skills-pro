# Claude Skills Pro

Skills partagees pour Claude Code

## Skills disponibles

| Skill | Description | Usage |
|-------|-------------|-------|
| **sinapse-adr-writing** | Ecriture d'ADR (Architecture Decision Records) pour SINAPSE | Template MADR v4 adapte, Obsidian, Confluence |
| **madr-compliance** | Conformite MADR v4 upstream | Audit et review d'ADR contre la spec officielle |

## Installation

### Methode 1 : Copier dans le projet

```bash
# Depuis la racine de votre projet
mkdir -p .claude/skills
cp -r sinapse-adr-writing .claude/skills/
cp -r madr-compliance .claude/skills/
```

Les skills projet-level sont automatiquement charges pour toute personne utilisant Claude Code dans le repo.

### Methode 2 : Copier en global (user-level)

```bash
cp -r sinapse-adr-writing ~/.claude/skills/
cp -r madr-compliance ~/.claude/skills/
```

Les skills user-level sont disponibles dans tous vos projets.

## Structure

```
claude-skills-pro/
├── sinapse-adr-writing/
│   └── SKILL.md          # Template ADR SINAPSE (MADR v4 adapte FR)
├── madr-compliance/
│   └── SKILL.md          # Spec MADR v4 upstream + mapping SINAPSE
└── README.md
```

## Template ADR SINAPSE

Chaque ADR suit le template MADR v4 adapte pour SINAPSE :

- **Langue** : Francais
- **Format** : Obsidian Markdown (wikilinks, callouts)
- **Publication** : Confluence via script automatise
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
