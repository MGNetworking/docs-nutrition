# Exception Filter (Middleware)

**Ajouté le :** 2026-05-25

---

## Objectif

Intercepter les exceptions métier lancées par les couches Domain et Application, et les mapper en réponses HTTP structurées avec un message lisible par l'utilisateur.

## Qui l'utilise

Toutes les requêtes — le filtre est global sur l'ensemble des endpoints.

## Ce qu'il fait

- Intercepte les exceptions métier et retourne une réponse HTTP avec un code et un message explicite
- Laisse remonter les exceptions non gérées (erreurs système → 500)

## Ce qu'il ne fait pas

- Ne gère pas les erreurs JWT (401) — responsabilité du middleware Keycloak
- Ne gère pas la validation des inputs (400) — responsabilité du model binding / FluentValidation ASP.NET

## Mappings exception → HTTP

| Exception | Code HTTP | Cas métier |
|---|---|---|
| `ConflictException` | 409 | Diet active déjà existante pour cet utilisateur |
| `ConflictException` | 409 | FoodItem déjà sauvegardé par cet utilisateur |
| `ConflictException` | 409 | Pesée déjà enregistrée à cette date pour cet utilisateur |
| `NotFoundException` | 404 | Ressource introuvable (Diet, Meal, FoodItem, WeightEntry, DietPlan) |
| `UnprocessableException` | 422 | Lancement d'un régime sans WeightEntry existant |
| `ForbiddenException` | 403 | Limite tier dépassée (repas sauvegardés, historique poids, période bilan) |
| `ForbiddenException` | 403 | Accès aux templates DietPlan bloqué pour tier Free |

## Dépendances

- Toutes les couches Domain et Application — source des exceptions métier
