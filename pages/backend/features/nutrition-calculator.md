# Moteur de calcul nutritionnel (NutritionCalculator)

**Ajouté le :** 2026-06-12
**Référence spec :** `docs/pages/backend/design/Regles-metier.md` · `docs/pages/backend/design/regles-metier-consolidees.md`

---

## Objectif

Centraliser toute la logique de calcul nutritionnel dans un service statique de la couche Application. Éviter la duplication de formules métier à travers les services applicatifs.

## Qui l'utilise

- `DietPlansService.LaunchAsync` — calcul du `CalorieTarget` au lancement d'un régime
- `UserService.GetUserProfileAsync` — calcul des `NutritionNeeds` pour le profil utilisateur (à venir)
- Tout futur service ayant besoin d'un calcul nutritionnel

## Quand

- Au lancement d'un `DietPlan` → création d'une `Diet` avec `CalorieTarget` figé
- À la lecture du profil utilisateur → affichage des besoins caloriques journaliers

---

## Ce qu'il fait

### `NutritionNeeds Calculate(User user, float weightKg, Goal goal, MacroDistribution macros)`

Calcule les besoins caloriques complets d'un utilisateur à un instant T.

**Entrées :**
- `user` — profil (genre, taille, date de naissance, niveau d'activité)
- `weightKg` — poids actuel de l'utilisateur (issu du `WeightEntry` le plus récent)
- `goal` — objectif (`WeightLoss`, `Maintenance`, `WeightGain`)
- `macros` — répartition macros en pourcentages

**Calculs :**

#### 1. Âge
Calculé depuis `BirthDate`, corrigé si l'anniversaire n'est pas encore passé cette année.

#### 2. BMR — Mifflin-St Jeor (formule prioritaire)

| Sexe | Formule |
|---|---|
| Homme | `(10 × P) + (6.25 × T) - (5 × A) + 5` |
| Femme | `(10 × P) + (6.25 × T) - (5 × A) - 161` |

#### 2b. BMR — Harris-Benedict révisée (formule alternative)

| Sexe | Formule |
|---|---|
| Homme | `88.362 + (13.397 × P) + (4.799 × T) - (5.677 × A)` |
| Femme | `447.593 + (9.247 × P) + (3.098 × T) - (4.330 × A)` |

#### 3. TDEE : `BMR × NAP`

| ActivityLevel | NAP | Description |
|---|---|---|
| Sedentary | 1.2 | Peu ou pas d'exercice — travail de bureau |
| LightlyActive | 1.375 | Exercice léger 1-3 jours/semaine |
| ModeratelyActive | 1.55 | Exercice modéré 3-5 jours/semaine |
| VeryActive | 1.725 | Exercice intense 6-7 jours/semaine |
| ExtremelyActive | 1.9 | Travail physique intense — athlètes professionnels |

#### 4. CalorieTarget selon objectif

| Goal | Formule |
|---|---|
| WeightLoss | `TDEE - min(TDEE × 15%, 500 kcal)` |
| Maintenance | `TDEE` |
| WeightGain | `TDEE + min(TDEE × 15%, 500 kcal)` |

**Retourne :** `NutritionNeeds` — value object contenant `Bmr`, `Tdee`, `TargetCalories`, `MacroDistribution`

---

### `MacroGrams ToGrams(MacroDistribution macros, int calorieTarget)`

Convertit une répartition macros en pourcentages vers des grammes journaliers.

**Valeurs caloriques par macronutriment :**

| Macro | kcal/g |
|---|---|
| Protéines | 4 |
| Glucides | 4 |
| Lipides | 9 |

**Formules :**

| Macro | Formule |
|---|---|
| Protéines (g) | `CalorieTarget × %P ÷ 4` |
| Glucides (g) | `CalorieTarget × %C ÷ 4` |
| Lipides (g) | `CalorieTarget × %L ÷ 9` |

**Retourne :** `MacroGrams` — value object contenant `ProteinG`, `CarbG`, `FatG` (à créer)

---

### `MacroDistribution GetDefaultMacros(DietType dietType)`

Retourne la répartition macros par défaut selon le type de régime.

| DietType | Glucides | Lipides | Protéines |
|---|---|---|---|
| Balanced | 50% | 30% | 20% |
| HighProtein | 40% | 30% | 30% |
| Keto | 5% | 70% | 25% |

> Les autres types (Mediterranean, LowCarb, Vegetarian, Vegan, Custom) n'ont pas de valeurs par défaut définies dans les specs — à compléter.

---

### Calculs complémentaires (à venir)

| Méthode | Formule | Retourne |
|---|---|---|
| `CalculateImc(float weightKg, float heightCm)` | `P ÷ (T/100)²` | `float` |
| `CalculateWaterNeeds(float weightKg)` | `P × 0.033` | `float` (litres) |
| `CalculateActivityExpenditure(float weightKg, float metValue, int durationMin)` | `durée(min) × MET × P ÷ 60` | `float` (kcal) |

---

## Ce qu'il ne fait pas

- Ne persiste rien — calcul pur sans effet de bord
- Ne récupère pas le `WeightEntry` — c'est la responsabilité du service appelant
- Ne calcule pas le bilan nutritionnel journalier — c'est le rôle de `DietsService`

## Emplacement

`src/NutritionApi.Application/Services/NutritionCalculator.cs`

Service applicatif statique — pas d'état, pas de dépendances injectées. Les calculs BMR/TDEE sont des règles métier de la couche Application selon `regles-metier-consolidees.md`.

## Dépendances

- `User` — source des données profil
- `NutritionNeeds` — value object retourné par `Calculate`
- `MacroGrams` — value object retourné par `ToGrams` (à créer)
- `MacroDistribution` — répartition macros en entrée et en retour de `GetDefaultMacros`
