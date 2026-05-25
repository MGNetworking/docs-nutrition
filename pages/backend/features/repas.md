# Repas

**Ajouté le :** 2026-05-02
**Référence spec :** `docs/pages/backend/annexes/workflow_enregistrement-repas.mermaid`

---

## Objectif

Permettre à l'utilisateur d'enregistrer ce qu'il a mangé (avec calcul automatique des valeurs nutritionnelles) et de sauvegarder ses repas habituels pour les réutiliser rapidement.

## Qui l'utilise

Tous les utilisateurs.
Repas sauvegardés limités selon le tier : Free = 5 · Pro = 50 · Business = illimité.

## Quand

- Après chaque repas pour enregistrer les apports de la journée
- Peut être renseigné rétroactivement (date passée autorisée)
- Depuis un repas sauvegardé pour éviter de tout ressaisir

## Ce qu'elle fait

- Crée un repas avec ses aliments (MealItems) et leurs quantités
- Calcule automatiquement `NutritionInfo` pour chaque MealItem (snapshot depuis FoodItem × quantité)
- Permet de marquer un repas comme sauvegardé (`IsSaved = true`) pour le réutiliser
- Vérifie la limite de repas sauvegardés selon le tier avant sauvegarde
- Permet de modifier les propriétés d'un repas (nom, type, notes, date de consommation)
- Permet d'ajouter ou retirer des MealItems d'un repas
- Supprime un repas et ses MealItems en cascade

## Ce qu'elle ne fait pas

- Un repas n'est pas lié à une Diet — la Diet active est déduite par le service au moment du bilan
- Ne modifie pas les valeurs nutritionnelles après création (snapshot immuable)

## Endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| `POST` | `/meals` | Créer un repas (ponctuel ou sauvegardé) |
| `GET` | `/meals` | Lister ses repas (`?saved=true`, `?date=`) |
| `GET` | `/meals/{id}` | Détail d'un repas |
| `PATCH` | `/meals/{id}` | Modifier les propriétés d'un repas (`name`, `mealType`, `notes`, `consumedAt`) |
| `DELETE` | `/meals/{id}` | Supprimer un repas |
| `POST` | `/meals/{id}/items` | Ajouter un MealItem |
| `DELETE` | `/meals/{id}/items/{itemId}` | Retirer un MealItem |

> **Impact bilan :** modifier `name`, `mealType` ou `notes` n'a aucun effet sur le bilan nutritionnel (le bilan agrège les `NutritionInfo` des `MealItems`, pas les métadonnées). Modifier `consumedAt` déplace le repas vers un autre jour — le bilan est recalculé automatiquement à la prochaine requête `GET /diets/{id}/bilan` (pas d'entité persistée à invalider).

## Dépendances

- `Aliments` — chaque MealItem référence un FoodItem
- `Bilan nutritionnel` — les MealItems alimentent le calcul du bilan
- `Abonnements` — limite de repas sauvegardés selon tier
