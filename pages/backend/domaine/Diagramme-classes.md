# Diagramme de classes — API Nutrition

> Généré depuis `Modele-domaine.md`.
> Source de vérité : `Modele-domaine.md` — modifier ce fichier en cas de changement.

---

```mermaid
classDiagram

    %% ─── Aggregate Roots ───────────────────────────────────────────

    class User {
        <<Aggregate Root>>
        +Guid Id
        +string KeycloakId
        +DateOnly BirthDate
        +Gender Gender
        +float Height
        +ActivityLevel ActivityLevel
        +List~Allergen~ Allergies
        +List~string~ DietaryPreferences
        +SubscriptionTier SubscriptionTier
        +DateTime CreatedAt
        +DateTime? DeletedAt
    }

    class DietPlan {
        <<Aggregate Root>>
        +Guid Id
        +Guid? UserId
        +bool IsTemplate
        +string Name
        +DietType DietType
        +Goal Goal
        +float TargetWeight
        +MacroDistribution MacroDistribution
    }

    class Diet {
        <<Aggregate Root>>
        +Guid Id
        +Guid UserId
        +string Name
        +DietType DietType
        +Goal Goal
        +float TargetWeight
        +int CalorieTarget
        +MacroDistribution MacroDistribution
        +DietStatus DietStatus
        +DateOnly StartDate
        +DateOnly? EndDate
    }

    class Meal {
        <<Aggregate Root>>
        +Guid Id
        +Guid UserId
        +string Name
        +MealType MealType
        +DateTime ConsumedAt
        +string? Notes
        +List~MealItem~ Items
        +bool IsSaved
    }

    class FoodItem {
        <<Aggregate Root>>
        +Guid Id
        +string OffId
        +string Name
        +float CaloriesPer100g
        +float ProteinsPer100g
        +float CarbsPer100g
        +float FatsPer100g
        +List~Allergen~ AllergensTags
        +DateTime CachedAt
    }

    %% ─── Entités enfants ────────────────────────────────────────────

    class WeightEntry {
        <<Entity>>
        +Guid Id
        +Guid UserId
        +float Weight
        +DateOnly MeasuredAt
    }

    class MealItem {
        <<Entity>>
        +Guid Id
        +Guid MealId
        +Guid FoodItemId
        +float Quantity
        +NutritionInfo Nutrition
    }

    class SavedFoodItem {
        <<Entity>>
        +Guid Id
        +Guid UserId
        +Guid FoodItemId
        +DateTime SavedAt
    }

    %% ─── Value Objects ──────────────────────────────────────────────

    class MacroDistribution {
        <<Value Object>>
        +int ProteinPercentage
        +int CarbPercentage
        +int FatPercentage
        ProteinPercentage + CarbPercentage + FatPercentage = 100
    }

    class NutritionInfo {
        <<Value Object>>
        +float Calories
        +int Proteins
        +int Carbs
        +int Fats
    }

    class NutritionNeeds {
        <<Value Object>>
        +float Bmr
        +float Tdee
        +float TargetCalories
        +MacroDistribution MacroDistribution
    }

    %% ─── Enums ──────────────────────────────────────────────────────

    class ActivityLevel {
        <<Enum>>
        Sedentary
        LightlyActive
        ModeratelyActive
        VeryActive
        ExtremelyActive
    }

    class Allergen {
        <<Enum>>
        Gluten
        Crustaceans
        Eggs
        Fish
        Peanuts
        Soybeans
        Milk
        Nuts
        Celery
        Mustard
        SesameSeeds
        SulphurDioxide
        Lupin
        Molluscs
    }

    class DietStatus {
        <<Enum>>
        Active
        Inactive
        Archived
    }

    class DietType {
        <<Enum>>
        Balanced
        HighProtein
        Keto
        Mediterranean
        LowCarb
        Vegetarian
        Vegan
        Custom
    }

    class Gender {
        <<Enum>>
        Male
        Female
        Other
    }

    class Goal {
        <<Enum>>
        WeightLoss
        Maintenance
        WeightGain
    }

    class MealType {
        <<Enum>>
        Breakfast
        Lunch
        Dinner
        Snack
    }

    class SubscriptionTier {
        <<Enum>>
        Free
        Pro
        Business
    }

    %% ─── Relations ──────────────────────────────────────────────────

    %% Composition — l'enfant n'existe pas sans le parent
    User "1" *-- "0..*" WeightEntry : possède
    Meal "1" *-- "0..*" MealItem : contient
    Diet "1" *-- "1" MacroDistribution : cible macros
    MealItem "1" *-- "1" NutritionInfo : snapshot nutritionnel
    NutritionNeeds "1" *-- "1" MacroDistribution : macros calculées

    %% Association — référence sans dépendance de vie
    User "1" --> "0..*" DietPlan : possède
    User "1" --> "0..*" Diet : possède
    User "1" --> "0..*" Meal : possède
    User "1" *-- "0..*" SavedFoodItem : liste personnelle
    MealItem "*" --> "1" FoodItem : référence
    SavedFoodItem "*" --> "1" FoodItem : référence

    %% Dépendances vers les enums
    User ..> Gender
    User ..> ActivityLevel
    User ..> Allergen
    User ..> SubscriptionTier
    DietPlan ..> DietType
    DietPlan ..> Goal
    Diet ..> DietType
    Diet ..> Goal
    Diet ..> DietStatus
    Meal ..> MealType
    FoodItem ..> Allergen
```

---

## Légende

| Notation | Signification |
|---|---|
| `◆──` (composition) | L'enfant n'existe pas sans le parent — suppression en cascade |
| `──>` (association) | Référence — les deux objets ont des cycles de vie indépendants |
| `..>` (dépendance) | Utilise un enum ou un type externe |
| `<<Aggregate Root>>` | Point d'entrée du système, accessible par son Id |
| `<<Entity>>` | Entité enfant, accessible uniquement via son parent |
| `<<Value Object>>` | Valeur immuable sans identité propre |
| `<<Enum>>` | Liste fixe de valeurs |
