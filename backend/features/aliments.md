# Aliments

**Ajouté le :** 2026-05-02
**Référence spec :** `docs/backend/annexes/workflow_recherche-aliment.mermaid` · `docs/backend/annexes/infrastructure-import-off.md`

---

## Objectif

Permettre à l'utilisateur de rechercher des aliments parmi 3M+ produits issus d'Open Food Facts, et de constituer une liste personnelle d'aliments favoris pour accélérer la saisie de ses repas.

## Qui l'utilise

- Recherche : tous les utilisateurs
- Liste personnelle (SavedFoodItems) : tous — limitée selon tier (Free: 10 · Pro: 100 · Business: illimité)

## Quand

- Lors de la création d'un repas : l'utilisateur cherche un aliment à ajouter
- Pour constituer sa liste personnelle : l'utilisateur sauvegarde ses aliments habituels

## Ce qu'elle fait

- Recherche un aliment par mot-clé — cache Redis d'abord, puis PostgreSQL (2 niveaux)
- Retourne les valeurs nutritionnelles pour 100g + allergènes
- Affiche un avertissement si l'aliment contient un allergène déclaré par l'utilisateur
- Sauvegarde un aliment dans la liste personnelle (`SavedFoodItem`)
- Vérifie la limite de SavedFoodItems selon le tier avant ajout
- Interdit le doublon (même FoodItem sauvegardé deux fois — 409)
- Liste et supprime les SavedFoodItems personnels

## Ce qu'elle ne fait pas

- Aucun appel direct à l'API Open Food Facts à la demande — la base est pré-remplie par un job nocturne
- Si un aliment est introuvable → liste vide (disponible après le prochain import)
- N'affiche pas les allergènes dans une liste blanche/noire — signalement uniquement

## Endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/food-items?search={motclé}` | Rechercher un aliment |
| `GET` | `/users/me/saved-food-items` | Liste personnelle d'aliments |
| `POST` | `/users/me/saved-food-items` | Sauvegarder un aliment |
| `DELETE` | `/users/me/saved-food-items/{id}` | Retirer un aliment de la liste |

## Dépendances

- Redis (cache recherche)
- PostgreSQL `FoodItem` (base pré-remplie)
- Job import Open Food Facts (quotidien — voir `infrastructure-import-off.md`)
- `Abonnements` — limite SavedFoodItems selon tier
