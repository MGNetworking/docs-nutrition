# Mise à disposition des aliments

**Ajouté le :** 2026-07-23
**Type :** Interne
**Référence spec :** `docs/pages/backend/annexes/workflow-import-aliments.md` (fonctionnement de bout en bout)

> Fonctionnalité de fonctionnement applicatif : elle alimente le catalogue interrogé par la recherche d'aliments (`features/utilisateur/aliments.md`) et expose son état de santé au back-office admin (`features/interne/admin-dashboard.md`).

---

## Objectif

Rendre les produits d'Open Food Facts disponibles à l'application sans jamais appeler l'API externe pendant une recherche utilisateur. Sans cette fonctionnalité, la table `FoodItem` reste vide et toute recherche renvoie une liste vide.

## Qui l'utilise

Aucun acteur humain pour le remplissage — job de fond déclenché par le planificateur. La supervision est consultée par l'administrateur via le back-office.

## Quand

- Import : quotidien, chaque nuit (le dump Open Food Facts est publié chaque jour)
- Supervision : à la demande, quand l'administrateur ouvre la santé système

## Ce qu'elle fait

- Télécharge le dump officiel Open Food Facts (traitement par batch)
- Insère les nouveaux produits, met à jour les produits existants (`FoodItem.UpdateFromImport`)
- Ignore les produits invalides sans interrompre le traitement du reste
- Vide le cache des recherches en fin d'import, dès qu'au moins un produit a été importé
- Expose l'état des jobs planifiés (dernier run, prochain run, statut) au back-office admin

## Ce qu'elle ne fait pas

- N'appelle jamais l'API Open Food Facts au moment d'une recherche utilisateur
- Ne rend pas disponibles les produits ajoutés à OFF dans les dernières 24 h (cas marginal accepté)
- Ne déclenche aucune notification — l'échec se lit dans la supervision

## Les deux volets

| Volet | Rôle | Effet visible |
|---|---|---|
| **Remplissage** | Job d'import du dump OFF vers `FoodItem` | Le catalogue de recherche se remplit chaque nuit |
| **Supervision** | Lecture de l'état des jobs planifiés | `GET /admin/system/health` renvoie le statut de l'import |

## Endpoint (point de contact visible)

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/system/health` | Santé des jobs planifiés (dont le dernier import OFF) — voir `features/interne/admin-dashboard.md` |

## Comprendre le fonctionnement

➜ **`annexes/workflow-import-aliments.md`** — le document à lire en premier : schéma d'ensemble,
rôle de chaque classe, parcours d'un produit, parcours de la supervision, décisions et raisons.

Les deux annexes ci-dessous n'éclairent chacune **qu'une brique isolée** ; elles ne décrivent pas
le fonctionnement d'ensemble :

| Brique | Document | Ce qu'il couvre |
|---|---|---|
| Le moteur de jobs | `annexes/infrastructure-hangfire.md` | Planification, stockage, dashboard — **partagé** avec la purge RGPD |
| La source de données | `annexes/infrastructure-import-off.md` | Pourquoi un dump, quels champs sont repris, à quelle fréquence |

## Dépendances

- PostgreSQL — table `FoodItem` alimentée par l'import, et stockage de l'état des jobs
- `features/utilisateur/aliments.md` — la fonctionnalité utilisateur consommatrice du catalogue
- `features/interne/admin-dashboard.md` — expose la supervision de l'import
