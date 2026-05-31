# docs-nutrition

Documentation technique du projet **Nutrition API** — API SaaS de gestion nutritionnelle (ASP.NET Core 10, DDD 4 couches, Kubernetes).

Site publié : [https://mgnetworking.github.io/docs-nutrition/](https://mgnetworking.github.io/docs-nutrition/)

---

## Architecture du repo

```
docs-nutrition/                         ← racine du repo (ce dépôt)
├── README.md                           ← ce fichier
├── mkdocs.yml                          ← configuration MkDocs (nav, thème, plugins)
├── requirements.txt                    ← dépendances Python du site
├── jira-registry.json                  ← registre des imports Jira (ne pas modifier manuellement)
├── .gitignore
├── .github/
│   └── workflows/
│       └── docs.yml                    ← pipeline CI/CD (build sur PR, deploy sur push master)
└── pages/                              ← contenu publié (docs_dir MkDocs)
    ├── index.md                        ← page d'accueil du site
    └── backend/
        ├── 1.nutrition-introduction.md
        ├── 2.nutrition-cas-usage.md
        ├── 3.nutrition-specifications-fonctionnelles.md
        ├── 4.nutrition-specifications-techniques.md
        ├── 5.nutrition-contraintes.md
        ├── 6.nutrition-abonnements.md
        ├── 7.nutrition-admin.md
        ├── design/                     ← documents de design technique par couche
        │   ├── design-domain.md        ← modèle domaine, agrégats, invariants
        │   ├── design-application.md   ← services, DTOs, interfaces, DI
        │   ├── design-infrastructure.md ← EF Core, PostgreSQL, Redis, Hangfire
        │   ├── design-api.md           ← controllers, routing, middleware, auth
        │   └── Regles-metier.md        ← formules BMR/TDEE + invariants domaine
        ├── features/                   ← une page par fonctionnalité
        ├── annexes/
        │   ├── Diagramme-classes.md    ← diagramme Mermaid classDiagram
        │   ├── infrastructure-*.md     ← guides setup (Keycloak, Hangfire, OFF, MkDocs, CI)
        │   ├── workflows.md            ← 10 flux séquentiels Mermaid
        │   └── workflow_*.mermaid      ← sources brutes des diagrammes (non publiées)
        └── livrable/                   ← documents de travail internes (non publiés dans la nav)
            ├── checklist-implementation.md
            ├── jira-backlog-decomposition.md
            ├── jira_backlog.py
            └── specs-frontend.md
```

> **Règle :** `livrable/` et les fichiers `.mermaid` standalone ne figurent jamais dans la `nav:` de `mkdocs.yml` — ce sont des documents de travail, pas de la documentation publiée.

---

## Prérequis

- Python 3.x installé
- WSL2 (si Windows) — voir note ci-dessous

---

## Mise en place de l'environnement local (une seule fois)

> **Note WSL2 :** Ne jamais créer le venv dans `/mnt/d/` (filesystem NTFS Windows) — les packages s'installent partiellement et les modules sont introuvables à l'exécution. Créer le venv sur le filesystem Linux.

```bash
# Créer le venv sur le filesystem Linux
python3 -m venv ~/venvs/mkdocs-nutrition

# Activer le venv
source ~/venvs/mkdocs-nutrition/bin/activate

# Installer les dépendances depuis le repo (chemin Windows via WSL)
pip install -r requirements.txt
```

---

## Lancer le serveur local

```bash
# Activer le venv (si pas déjà actif)
source ~/venvs/mkdocs-nutrition/bin/activate

# Se placer dans le repo docs
cd /mnt/d/Projet/SaaS/nutrition-manager/docs

# Lancer le serveur avec rechargement automatique
mkdocs serve

# Ouvrir http://127.0.0.1:8000
```

Vérifier avant de commiter : navigation, rendu Mermaid, liens, recherche.

```bash
# Désactiver le venv quand terminé
deactivate
```

---

## Ajouter ou modifier du contenu

1. Éditer ou créer un fichier `.md` dans `pages/`
2. Si nouveau fichier → l'ajouter dans `mkdocs.yml` sous `nav:` (sauf livrables)
3. Tester en local avec `mkdocs serve`
4. Commiter et pousser sur `master`

```bash
git add pages/backend/<fichier>.md mkdocs.yml
git commit -m "docs(<scope>): <description>"
git push origin master
```

Le déploiement se fait automatiquement via GitHub Actions (~2 min).

---

## Pipeline CI/CD

Le fichier `.github/workflows/docs.yml` gère deux cas :

| Événement                    | Action                                                  |
| ---------------------------- | ------------------------------------------------------- |
| `push` sur `master`          | `mkdocs gh-deploy --force` → déploiement GitHub Pages   |
| `pull_request` vers `master` | `mkdocs build --strict` → vérification sans déploiement |

Le flag `--strict` bloque le build si un lien est cassé — corriger en local avant de merger.

---

## Dépendances

| Package                  | Version | Rôle                                       |
| ------------------------ | ------- | ------------------------------------------ |
| `mkdocs`                 | 1.6.1   | Moteur de génération du site               |
| `mkdocs-material`        | 9.5.49  | Thème Material Design                      |
| `mkdocs-mermaid2-plugin` | 1.2.1   | Rendu des diagrammes Mermaid               |
| `pymdown-extensions`     | 10.14.3 | Extensions markdown (superfences, tabbed…) |

Mettre à jour `requirements.txt` en cas de montée de version, puis relancer `pip install -r requirements.txt`.

---

## Fichiers de configuration

### `mkdocs.yml`

- `docs_dir: pages` — le contenu publié est dans `pages/` (contrainte MkDocs : `docs_dir` ne peut pas être le parent du fichier de config)
- `site_dir: site` — dossier de build local, exclu du git (`.gitignore`)
- Plugin `mermaid2` + `custom_fences` sur `pymdownx.superfences` — les blocs ` ```mermaid ``` ` sont rendus comme schémas interactifs

### `jira-registry.json`

Registre des imports Jira géré par `playbook/tools/import_jira.py` dans le repo parent. Ne pas modifier manuellement.

---

## Liens utiles

| Ressource           | URL                                            |
| ------------------- | ---------------------------------------------- |
| Site publié         | https://mgnetworking.github.io/docs-nutrition/ |
| Repo docs (ce repo) | https://github.com/MGNetworking/docs-nutrition |
| Repo code API       | _(à créer — nutrition-api)_                    |
