# Bilan nutritionnel

**Ajouté le :** 2026-05-02
**Type :** Utilisateur
**Référence spec :** `reference/diagrammes/workflow_bilan-nutritionnel.mermaid` · [3.nutrition-specifications-fonctionnelles](../../3.nutrition-specifications-fonctionnelles.md)

---

## Objectif

Fournir à l'utilisateur une analyse de ses apports nutritionnels réels sur la période d'un régime, comparés à ses objectifs (CalorieTarget + MacroDistribution).

## Qui l'utilise

Tous les utilisateurs — période accessible limitée selon le tier :
- Free → 7 derniers jours
- Pro → 1 an
- Business → illimité (période complète du régime)

## Quand

À tout moment pendant ou après un régime — l'utilisateur consulte son bilan pour suivre sa progression.

## Ce qu'elle fait

- Agrège tous les MealItems de la période (calories, protéines, glucides, lipides par jour)
- Compare les apports réels aux objectifs de la Diet (CalorieTarget, MacroDistribution)
- Inclut l'historique des pesées sur la période
- Calcule un résumé global (moyennes journalières)
- Clampe la période selon le tier de l'utilisateur

## Ce qu'elle ne fait pas

- Ne persiste pas le bilan — calculé à la demande à chaque appel (pas d'entité `SavedBilan`)
- Ne calcule pas de recommandations — affichage des données brutes uniquement

## Endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/nutrition/{id}/bilan` | Bilan nutritionnel d'un régime |

> Route portée par `NutritionController`, **et non par `DietsController`** — corrigé le
> 2026-07-23 d'après [Design technique — Couche API](../../design/design-api.md) et le code.

## Réponse

```json
{
  "diet": { "name", "calorieTarget", "macroDistribution", "startDate", "endDate" },
  "dailyData": [{ "date", "totalCalories", "totalProteins", "totalCarbs", "totalFats", "caloriesPercent" }],
  "weightEntries": [{ "measuredAt", "weight" }],
  "summary": { "avgDailyCalories", "avgCaloriesPercent", "avgProteins", "avgCarbs", "avgFats" }
}
```

## Dépendances

- `Diet` — source du CalorieTarget et MacroDistribution
- `Repas` — MealItems agrégés sur la période
- `Suivi du poids` — WeightEntries sur la période
- `Abonnements` — limite la période accessible
