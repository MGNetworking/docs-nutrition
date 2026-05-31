# Infrastructure Docs — Publication automatique (MkDocs + GitHub Pages)

> Ce document couvre la mise en place de la publication automatique du repo docs.
> Approche : **Docs-as-code** — les modifications markdown déclenchent un build MkDocs et un déploiement GitHub Pages.

---

## Vue d'ensemble

```
Modification markdown
        ↓
    git push (main)
        ↓
GitHub Actions — build MkDocs
        ↓
    GitHub Pages
        ↓
  Site docs public
```

---

## Prérequis

- Repo docs séparé du repo code (ex. `nutrition-docs`)
- GitHub Pages activé sur le repo docs
- Python 3.x disponible (MkDocs est un outil Python)

---

## Section 1 — Configuration MkDocs

### Fichiers à créer à la racine du repo docs

```text
nutrition-docs/
├── mkdocs.yml           ← configuration MkDocs
├── requirements.txt     ← dépendances Python
└── docs/                ← contenu markdown (existant)
    ├── index.md         ← page d'accueil (à créer)
    └── backend/
        ├── ...
```

---

### `requirements.txt`

```txt
mkdocs==1.6.1
mkdocs-material==9.5.49
mkdocs-mermaid2-plugin==1.2.1
```

> `mkdocs-mermaid2-plugin` — nécessaire pour rendre les fichiers `.mermaid` des workflows.

---

### `mkdocs.yml`

```yaml
site_name: Nutrition API — Documentation
site_description: Documentation technique du projet Nutrition API
site_author: Maxime Ghalem
docs_dir: docs

theme:
  name: material
  language: fr
  palette:
    - scheme: default
      primary: teal
      accent: teal
      toggle:
        icon: material/brightness-7
        name: Mode sombre
    - scheme: slate
      primary: teal
      accent: teal
      toggle:
        icon: material/brightness-4
        name: Mode clair
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - search.highlight
    - content.code.copy

plugins:
  - search:
      lang: fr
  - mermaid2

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true
  - tables
  - toc:
      permalink: true

nav:
  - Accueil: index.md
  - Backend:
    - Introduction: backend/1.nutrition-introduction.md
    - Cas d'usage: backend/2.nutrition-cas-usage.md
    - Specs fonctionnelles: backend/3.nutrition-specifications-fonctionnelles.md
    - Specs techniques: backend/4.nutrition-specifications-techniques.md
    - Contraintes: backend/5.nutrition-contraintes.md
    - Domaine:
      - Modèle domaine: backend/design/design-domain.md
      - Diagramme de classes: backend/annexes/Diagramme-classes.md
      - Règles métier: backend/design/Regles-metier.md
    - Livrables:
      - Specs frontend: backend/livrable/specs-frontend.md
      - Checklist implémentation: backend/livrable/checklist-implementation.md
    - Infrastructure:
      - Setup local & production: backend/annexes/infrastructure-setup.md
      - Keycloak Admin: backend/annexes/infrastructure-keycloak-admin.md
      - Import Open Food Facts: backend/annexes/infrastructure-import-off.md
      - Hangfire: backend/annexes/infrastructure-hangfire.md
      - Publication docs: backend/annexes/infrastructure-docs.md
```

---

### `docs/index.md` (page d'accueil)

```markdown
# Nutrition API — Documentation

API SaaS de gestion nutritionnelle — backend ASP.NET Core 10, architecture DDD 4 couches, déploiement Kubernetes.

## Navigation

| Section | Contenu |
|---|---|
| **Backend** | Specs fonctionnelles, modèle domaine, infrastructure |
| **Domaine** | Agrégats, Value Objects, règles métier |
| **Infrastructure** | Setup local, CI/CD, déploiement K3s |

## Liens

- [Repo API](https://github.com/<user>/nutrition-api)
- [Jira — Board NUT](https://votre-instance.atlassian.net/jira/software/projects/NUT/boards)
```

---

## Section 2 — GitHub Actions (déploiement automatique)

### Fichier à créer dans le repo docs

```text
nutrition-docs/
└── .github/
    └── workflows/
        └── docs.yml
```

### `.github/workflows/docs.yml`

```yaml
name: Docs

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Installer les dépendances
        run: pip install -r requirements.txt

      - name: Build (PR uniquement — vérification sans déploiement)
        if: github.event_name == 'pull_request'
        run: mkdocs build --strict

      - name: Build & Deploy (push main uniquement)
        if: github.event_name == 'push'
        run: mkdocs gh-deploy --force
```

> **Comportement :**
> - Sur **PR** : build uniquement (`--strict` bloque si des liens sont cassés) — pas de déploiement
> - Sur **push `main`** : build + déploiement GitHub Pages automatique

---

## Section 3 — Activation GitHub Pages

### Configuration initiale (une seule fois)

Dans le repo docs sur GitHub :

```
Settings → Pages
  → Source : Deploy from a branch
  → Branch : gh-pages / root
  → Save
```

> La branche `gh-pages` est créée automatiquement par `mkdocs gh-deploy` au premier run.

### URL du site publié

```
https://<username>.github.io/<repo-docs>/
```

---

## Section 4 — Test local

```bash
# Installer les dépendances
pip install -r requirements.txt

# Serveur local avec rechargement automatique
mkdocs serve

# Ouvrir http://127.0.0.1:8000
```

---

## Ordre de mise en place

| Étape | Action |
|---|---|
| 1 | Créer `requirements.txt` et `mkdocs.yml` à la racine du repo docs |
| 2 | Créer `docs/index.md` |
| 3 | Tester localement avec `mkdocs serve` |
| 4 | Créer `.github/workflows/docs.yml` |
| 5 | Activer GitHub Pages dans les settings du repo |
| 6 | Push sur `main` → premier déploiement automatique |

---

*Références : `infrastructure-setup.md` (CI/CD API) · `playbook/devops-playbook/README.md`*
