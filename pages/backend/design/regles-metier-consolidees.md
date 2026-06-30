# Règles métier consolidées

> Document de référence unique — toutes les règles métier extraites de `design-domain.md`, `design-application.md`, `design-api.md` et `Regles-metier.md`.
> Organisé par entité. Évite de naviguer entre plusieurs fichiers pour retrouver une règle.

---

## `User`

| Règle | Détail | Couche |
|---|---|---|
| Un seul acteur dans le système | Pas de rôle "nutritionniste" ou "coach" — un seul type d'utilisateur | Domain |
| Une seule Diet active à la fois | Le système bloque (409) si une Diet est déjà active au lancement | Application |
| Un User peut enregistrer des Meal sans Diet active | La Diet est optionnelle | Domain |
| Suppression = soft delete | `MarkAsDeleted()` pose `DeletedAt = UtcNow` — pas de DELETE SQL | Domain |
| Grace period 30 jours | Après `MarkAsDeleted()`, compte actif 30 jours avant purge | Application |
| `SubscriptionTier` lu en base, jamais depuis le JWT | La source de vérité est la base de données | Application |
| `Allergies` et `DietaryPreferences` obligatoires à la création | L'UI doit forcer un choix explicite ou cocher "Aucune contre-indication" | API |
| Liste vide = "confirmé : aucune" | Non ambigu — pas de null possible | Domain |
| `Allergen` est un enum calqué sur les 14 allergènes EU | Permet comparaison fiable avec les données Open Food Facts | Domain |
| L'app signale les allergènes — ne bloque pas l'utilisateur | Avertissement, pas d'interdiction | Domain |
| `Height` est fixe sur User | Ne change pas après la création du profil | Domain |
| `BirthDate` est fourni par l'utilisateur | Donnée réelle connue de l'utilisateur | Domain |
| `CreatedAt` est généré par le système | Timestamp technique — `DateTime.UtcNow` dans le constructeur | Domain |

---

## `DietPlan`

| Règle | Détail | Couche |
|---|---|---|
| `UserId = null` si `IsTemplate = true` | Un template n'appartient à aucun utilisateur | Domain |
| `UserId` obligatoire si `IsTemplate = false` | Un plan personnel appartient toujours à un User | Domain |
| Un template ne peut pas être attaché à un User | Invariant constructeur | Domain |
| Un plan personnel est toujours modifiable | Aucun lien avec les Diet déjà créées depuis lui | Domain |
| Modifier un DietPlan n'affecte jamais les Diet existantes | La Diet est un snapshot indépendant | Domain |
| Un DietPlan n'a pas de `CalorieTarget` | Ce calcul dépend du poids réel au moment du lancement | Domain |
| Un template est non modifiable par les utilisateurs | Lecture seule — Pro/Business uniquement | Application |
| Seul le rôle `admin` peut créer ou modifier un template | Vérifié via Keycloak | Application |
| `IsTemplate` est forcé côté service selon le contexte | `CreateAsync` → `false`, `AdminService.CreateTemplateAsync` → `true` | Application |
| Limites par tier : Free max 2, Pro max 20, Business illimité | Vérifié par `SubscriptionGuard` avant création | Application |
| Accès aux templates : Free ❌, Pro ✅, Business ✅ | 403 si tier insuffisant | Application |
| Pas de `DietPlanId` sur `Diet` | Après lancement, la Diet est indépendante — une référence serait trompeuse | Domain |

---

## `Diet`

| Règle | Détail | Couche |
|---|---|---|
| Une seule Diet active par User | 409 Conflict si une Diet active existe déjà | Application |
| `StartDate` imposée par le système | = date du lancement (aujourd'hui) — l'utilisateur ne peut pas choisir une date future | Domain |
| `CalorieTarget` calculé au lancement puis figé | BMR/TDEE + Goal + WeightEntry le plus récent — ne change jamais | Application |
| La Diet est un snapshot complet et indépendant | Aucun lien avec le DietPlan d'origine après lancement | Domain |
| Une Diet est non modifiable une fois lancée | Sert de référence fixe pour le suivi nutritionnel | Domain |
| `EndDate` fixée automatiquement par le système | Au moment de l'archivage ou de l'annulation | Domain |
| `Active → Archived` | Régime terminé normalement par l'utilisateur | Domain |
| `Active → Cancelled` | Régime abandonné en cours de route | Domain |
| Lancement impossible sans WeightEntry | CalorieTarget incalculable — 422 | Application |
| Somme des macros = 100% | ProteinPercentage + CarbPercentage + FatPercentage = 100% — 422 si ≠ | Domain |
| La Diet active à la date d'un Meal est déduite par le service | Via `Diet.StartDate` / `EndDate` — pas de lien direct Meal → Diet | Application |

---

## `Meal`

| Règle | Détail | Couche |
|---|---|---|
| Un Meal appartient toujours à un User | `UserId` obligatoire | Domain |
| Un Meal contient au moins un MealItem pour être valide | Invariant | Domain |
| Un Meal n'a pas de lien direct vers une Diet | La Diet active est déduite par le service | Domain |
| `ConsumedAt` est fourni par l'utilisateur | L'utilisateur peut logger un repas consommé plus tôt | Domain |
| `IsSaved = true` = repas réutilisable dans la liste personnelle | Limites par tier : Free max 5, Pro max 50, Business illimité | Application |

---

## `MealItem`

| Règle | Détail | Couche |
|---|---|---|
| Ne peut pas exister sans son Meal | Suppression du Meal → suppression des MealItem | Domain |
| `NutritionInfo` est un snapshot calculé à la création | Calculé depuis `FoodItem.XxxPer100g × (Quantity / 100)` — ne change jamais | Domain |
| Le snapshot protège l'historique | Si FoodItem est mis à jour, les anciens MealItem ne changent pas | Domain |

---

## `WeightEntry`

| Règle | Détail | Couche |
|---|---|---|
| Immuable après création | Une mesure de poids est un fait historique | Domain |
| `MeasuredAt` est fourni par l'utilisateur | L'utilisateur peut enregistrer une mesure prise antérieurement | Domain |
| Suppression du User → suppression de ses WeightEntry | Cascade | Domain |
| Fournit le poids de référence pour le calcul BMR/TDEE | WeightEntry le plus récent utilisé au lancement d'une Diet | Application |

---

## `SavedFoodItem`

| Règle | Détail | Couche |
|---|---|---|
| Immuable après création | Lien entre un User et un FoodItem | Domain |
| Un même FoodItem ne peut être sauvegardé qu'une seule fois par User | Doublon interdit | Domain |
| Suppression du User → suppression de ses SavedFoodItem | Cascade | Domain |
| Limites par tier : Free max 10, Pro max 100, Business illimité | Vérifié par `SubscriptionGuard` | Application |

---

## `FoodItem`

| Règle | Détail | Couche |
|---|---|---|
| Table partagée entre tous les utilisateurs | Pas de données personnelles | Domain |
| Alimentée par job Hangfire quotidien | Import dump Open Food Facts | Infrastructure |
| Recherche en 2 niveaux : Redis → PostgreSQL | Cache miss → base + alimentation Redis (TTL 24h) | Application |
| Aucun appel direct à l'API OFF au moment de la recherche | Toujours depuis la base locale | Infrastructure |
| `SavedAt` généré par le système | `DateTime.UtcNow` dans le constructeur | Domain |

---

## `MacroDistribution` (Value Object)

| Règle | Détail | Couche |
|---|---|---|
| ProteinPercentage + CarbPercentage + FatPercentage = 100% | Invariant — 422 si non respecté | Domain |
| Exprimé en pourcentages, pas en grammes | Les grammes dépendent du CalorieTarget qui appartient à la Diet | Domain |
| Immuable | Toute modification crée une nouvelle instance | Domain |

---

## `NutritionInfo` (Value Object)

| Règle | Détail | Couche |
|---|---|---|
| Snapshot calculé une fois à la création du MealItem | `FoodItem.XxxPer100g × (Quantity / 100)` | Domain |
| Immuable | Ne change jamais, même si FoodItem est mis à jour | Domain |
| `Calories` en `float` | Précision nécessaire pour le bilan | Domain |
| `Proteins`, `Carbs`, `Fats` en `int` | En grammes | Domain |

---

## Calculs métier (couche Application)

### BMR — Mifflin-St Jeor (prioritaire)

| Sexe | Formule |
|---|---|
| Homme | `(10 × P) + (6,25 × T) - (5 × A) + 5` |
| Femme | `(10 × P) + (6,25 × T) - (5 × A) - 161` |

### TDEE

`TDEE = BMR × NAP`

| Niveau | NAP |
|---|---|
| Sédentaire | 1,2 |
| Légèrement actif | 1,375 |
| Modérément actif | 1,55 |
| Très actif | 1,725 |
| Extrêmement actif | 1,9 |

### Ajustement selon l'objectif

| Objectif | Ajustement |
|---|---|
| Perte de poids | TDEE - 15 à 20% (max 500 kcal/jour) |
| Maintien | TDEE |
| Prise de masse | TDEE + 15 à 20% (max 500 kcal/jour) |

### Macros par défaut selon DietType

| DietType | Glucides | Lipides | Protéines |
|---|---|---|---|
| Équilibré | 50% | 30% | 20% |
| Protéiné | 40% | 30% | 30% |
| Cétogène | 5% | 70% | 25% |

### Calcul en grammes

| Macro | Formule |
|---|---|
| Protéines (g) | `CalorieTarget × %P ÷ 4` |
| Glucides (g) | `CalorieTarget × %G ÷ 4` |
| Lipides (g) | `CalorieTarget × %L ÷ 9` |

---

## `SubscriptionGuard`

Classe de la couche Application (`Application/Services/SubscriptionGuard.cs`) — centralise toutes les vérifications de limites par tier. Lève `ForbiddenException` si la limite est atteinte ou le tier insuffisant. Pas de dépendance repository — logique pure.

**Toujours appeler `SubscriptionGuard` depuis le service avant toute création de ressource limitée.**

| Méthode | Free | Pro | Business |
|---|---|---|---|
| `CheckDietPlanLimit` | 2 | 20 | Illimité |
| `CheckTemplateAccess` | ❌ | ✅ | ✅ |
| `CheckSavedMealLimit` | 5 | 50 | Illimité |
| `CheckSavedFoodItemLimit` | 10 | 100 | Illimité |
| `CheckBilanPeriod` | 7 jours | 1 an | Illimité |

---

## Authentification & Autorisation

| Règle | Détail | Couche |
|---|---|---|
| `sub` du JWT = `User.KeycloakId` | Clé de résolution de l'identité interne | API |
| Toutes les données personnelles filtrées par `userId` | Un utilisateur ne voit jamais les données d'un autre | Application |
| Vérifications de tier dans la couche Application | Jamais dans le Domain ni dans l'API | Application |
| Token absent ou invalide → 401 | | API |
| Rôle insuffisant → 403 | Ex : user tente d'accéder à une route admin | API |
| Tier insuffisant → 403 | Ex : Free tente d'accéder aux templates | Application |
| Limite tier dépassée → 403 | Ex : 3ème DietPlan en Free | Application |

---

## Responsabilité des champs date

| Champ | Entité | Responsable | Raison |
|---|---|---|---|
| `CreatedAt` | User | Système | Moment technique de création |
| `SavedAt` | SavedFoodItem | Système | Moment technique d'enregistrement |
| `StartDate` | Diet | Système | La Diet démarre au moment du lancement |
| `EndDate` | Diet | Système | La Diet se termine au moment de la clôture |
| `BirthDate` | User | Utilisateur | Donnée réelle connue de l'utilisateur |
| `ConsumedAt` | Meal | Utilisateur | L'utilisateur peut logger un repas consommé plus tôt |
| `MeasuredAt` | WeightEntry | Utilisateur | L'utilisateur peut enregistrer une mesure prise antérieurement |
