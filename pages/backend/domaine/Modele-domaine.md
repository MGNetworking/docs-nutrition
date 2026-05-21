# Modèle domaine — API de Gestion de Régime Alimentaire

> Concepts métier et leurs interactions.
> Source : cas d'usage (UC01-UC10) + règles métier.

---

## Agrégats racines

Un agrégat racine est un concept métier autonome qui protège ses propres règles.

### `User`

Point d'entrée du système. Tout appartient à un User.

**Attributs :**

| Attribut            | Type                | Notes                                      |
| ------------------- | ------------------- | ------------------------------------------ |
| Id                  | Guid                | Identifiant interne                        |
| KeycloakId          | string              | Identifiant Keycloak (OAuth2/OIDC)         |
| BirthDate           | DateOnly            | L'âge est calculé à la demande             |
| Gender              | enum Gender         |                                            |
| Height              | float               | En centimètres — fixe sur User             |
| ActivityLevel       | enum ActivityLevel  |                                            |
| Allergies           | List\<Allergen\>    | Enum calqué sur les 14 allergènes EU (Open Food Facts) — liste vide = confirmé aucune allergie |
| DietaryPreferences  | List\<string\>      | Libre (non filtrant) — liste vide = confirmé aucune préférence                     |
| CreatedAt           | DateTime            |                                            |
| DeletedAt           | DateTime?           | Null = compte actif / Renseigné = suppression demandée (grace period 30 jours) |
| SubscriptionTier    | enum SubscriptionTier | Free par défaut à la création — source de vérité en base (pas dans le JWT) |

**Responsabilités :**

- Détenir le profil physiologique (âge, sexe, taille, activité)
- Posséder ses Diet, ses Meal et son historique de poids (WeightEntry)

**Invariants :**

- Un User ne peut avoir qu'une seule Diet active à la fois
- Une Diet est optionnelle — un User peut enregistrer des Meal sans Diet active

**Responsabilité UX :**
- Les champs `Allergies` et `DietaryPreferences` sont **obligatoires** dans le formulaire de création de profil
- L'interface doit forcer un choix explicite : sélectionner des valeurs OU cocher *"Aucune contre-indication"*
- Une liste vide est donc non ambiguë côté domaine — elle signifie toujours *"confirmé : aucune"*

> **Pourquoi un enum `Allergen` et pas une `List<string>` libre ?** Les données alimentaires viennent d'Open Food Facts, qui normalise les allergènes sur les 14 allergènes officiels de l'Union Européenne (ex: `en:gluten`, `en:milk`). Utiliser un enum calqué sur ce référentiel permet une comparaison fiable et déterministe entre les allergènes de l'utilisateur et ceux d'un aliment. Avec des strings libres, un utilisateur pourrait écrire `"gluten"`, `"Gluten"`, `"blé"` ou `"wheat"` — la comparaison deviendrait impossible à fiabiliser.
>
> **Comportement de l'app :** l'application **signale** les allergènes présents dans un aliment — elle ne bloque pas le choix de l'utilisateur.

---

### `DietPlan`

Plan alimentaire réutilisable défini par l'utilisateur. Sert de base pour créer une `Diet`.

**Attributs :**

| Attribut          | Type                   | Notes                                       |
| ----------------- | ---------------------- | ------------------------------------------- |
| Id                | Guid                   |                                             |
| UserId            | Guid?                  | Clé étrangère vers User — null si `IsTemplate = true` |
| IsTemplate        | bool                   | `true` = template partagé (lecture seule, accessible à tous les utilisateurs Pro/Business) / `false` = plan personnel |
| Name              | string                 | Nom du plan défini par l'utilisateur (ex: "Mon keto habituel") — sert à différencier ses plans dans la liste |
| DietType          | enum DietType          |                                             |
| Goal              | enum Goal              |                                             |
| TargetWeight      | float                  | Poids cible en kg                           |
| MacroDistribution | MacroDistribution (VO) | Répartition cible des macros en %           |

**Responsabilités :**

- Stocker un plan alimentaire réutilisable (le "moule") sans dates ni objectif calorique
- Servir de base pour lancer une `Diet` — l'utilisateur choisit un plan dans sa liste et clique "Lancer"
- Rester dans la liste de l'utilisateur après le lancement — il peut être relancé ou modifié indépendamment

**Invariants :**

- Un `DietPlan` personnel (`IsTemplate = false`) est **toujours modifiable** — il n'a aucun lien avec les `Diet` déjà créées depuis lui
- La modification d'un `DietPlan` n'affecte jamais les `Diet` existantes (snapshot indépendant)
- Un `DietPlan` n'a pas de `CalorieTarget` — ce calcul dépend du poids réel de l'utilisateur au moment du lancement
- Un `DietPlan` template (`IsTemplate = true`) est **non modifiable** par les utilisateurs — accessible en lecture seule (Pro/Business uniquement)
- Un template a `UserId = null` — il n'appartient à aucun utilisateur
- Seul le rôle `admin` (Keycloak) peut créer ou modifier un template

> **Pourquoi pas de `DietPlanId` sur `Diet` ?** Une fois la `Diet` lancée, c'est un snapshot complet et indépendant. Si le plan est modifié après coup, une référence `DietPlanId` pointerait vers un objet qui n'a plus rien à voir avec la `Diet` créée — elle serait trompeuse et sans valeur métier.

---

### `Diet` ← concept central

Plan alimentaire d'un User sur une période définie.

**Attributs :**

| Attribut          | Type                    | Notes                                            |
| ----------------- | ----------------------- | ------------------------------------------------ |
| Id                | Guid                    |                                                  |
| UserId            | Guid                    | Clé étrangère vers User                          |
| Name              | string                  | Copié depuis `DietPlan.Name` au lancement        |
| DietType          | enum DietType           | Copié depuis `DietPlan`                          |
| Goal              | enum Goal               | Copié depuis `DietPlan` — objectif porté par la Diet, pas par le User |
| TargetWeight      | float                   | Copié depuis `DietPlan` — poids cible en kg      |
| CalorieTarget     | int                     | Calculé au lancement (BMR/TDEE + Goal + WeightEntry le plus récent) — snapshot, ne change jamais |
| MacroDistribution | MacroDistribution (VO)  | Copié depuis `DietPlan` — répartition cible des macros en % |
| DietStatus        | enum DietStatus         | Active / Inactive / Archived                     |
| StartDate         | DateOnly                | Imposée par le système = date du lancement (aujourd'hui) |
| EndDate           | DateOnly?               | Nullable — null si régime non terminé, modifiable après lancement |

**Responsabilités :**

- Définir le type de régime (équilibré, keto, méditerranéen...)
- Porter l'objectif de l'utilisateur (`Goal`) pour cette période
- Porter le `CalorieTarget` calculé au moment de la création (snapshot physiologique) — la Diet est un plan fixe, pas un plan adaptatif
- Porter la répartition des macros (`MacroDistribution`)
- Gérer son statut (Active / Inactive / Archived)
- Délimiter sa période via `StartDate` et `EndDate`

**Invariants :**

- **Une seule Diet Active par User** — le système bloque (409) si une Diet est déjà active au lancement d'un nouveau plan ; l'utilisateur doit terminer la Diet en cours avant d'en lancer une autre
- La somme des macros (protéines + glucides + lipides) doit toujours être égale à 100%
- `StartDate` est imposée par le système (= date du lancement) — l'utilisateur ne peut pas choisir une date future
- `CalorieTarget` est calculé par le service au lancement (BMR/TDEE + Goal + WeightEntry le plus récent) puis stocké en snapshot — ne change jamais, même si le poids évolue
- Une `Diet` est **non modifiable** une fois lancée (sauf `EndDate`) — elle sert de référence fixe pour le suivi nutritionnel sur la période
- Une `Diet` est un snapshot complet et indépendant — aucun lien avec le `DietPlan` d'origine après son lancement

---

### `Meal`

Repas enregistré par l'utilisateur à un instant donné.

**Attributs :**

| Attribut    | Type              | Notes                           |
| ----------- | ----------------- | ------------------------------- |
| Id          | Guid              |                                 |
| UserId      | Guid              | Clé étrangère vers User         |
| Name        | string            | Nom du repas                    |
| MealType    | enum MealType     | Breakfast, Lunch, Dinner, Snack |
| ConsumedAt  | DateTime          | Date et heure du repas          |
| Notes       | string?           | Notes libres, optionnelles      |
| Items       | List\<MealItem\>  | Relation de navigation          |
| IsSaved     | bool              | `true` = repas sauvegardé dans la liste personnalisée de l'utilisateur (réutilisable) / `false` = repas ponctuel (enregistrement unique) |

> **Pourquoi `IsSaved` ?** L'utilisateur peut vouloir retrouver rapidement ses repas habituels sans les recréer. La structure d'un repas ponctuel et d'un repas sauvegardé est identique — seule la persistance dans la liste personnalisée diffère. Un flag suffit, deux entités distinctes seraient une sur-ingénierie.

**Responsabilités :**

- Enregistrer ce que l'utilisateur a mangé (liste de MealItem)
- Porter le type de repas (petit-déjeuner, déjeuner, dîner, collation)
- Permettre le calcul des apports nutritionnels du repas

**Invariants :**

- Un Meal appartient toujours à un User
- Un Meal contient au moins un MealItem pour être valide
- Un Meal n'a pas de lien direct vers une Diet — la Diet active à la date du repas est déduite par le service via `Diet.StartDate` / `EndDate`

---

## Entités enfants

### `MealItem`

Un aliment dans un repas. Ne peut pas exister sans son Meal.

**Attributs :**

| Attribut   | Type               | Notes                                              |
| ---------- | ------------------ | -------------------------------------------------- |
| Id         | Guid               |                                                    |
| MealId     | Guid               | Clé étrangère vers Meal                            |
| FoodItemId | Guid               | Référence vers FoodItem                            |
| Quantity   | float              | Quantité consommée en grammes                      |
| Nutrition  | NutritionInfo (VO) | Snapshot calculé à la création depuis FoodItem     |

**Responsabilités :**

- Référencer un aliment depuis la table locale `FoodItem`
- Porter la quantité consommée en grammes
- Permettre le calcul des apports nutritionnels pour cette quantité

**Invariants :**

- La suppression d'un Meal entraîne la suppression de ses MealItem

---

### `SavedFoodItem`

Aliment sauvegardé par l'utilisateur dans sa liste personnelle. Ne peut pas exister sans son User.

> **Pourquoi cette entité ?** `FoodItem` est une table de référence partagée entre tous les utilisateurs — on ne peut pas y stocker des préférences individuelles. `SavedFoodItem` est un lien personnel entre un utilisateur et un aliment qu'il souhaite retrouver rapidement lors de la création de ses repas.

**Attributs :**

| Attribut   | Type     | Notes                          |
| ---------- | -------- | ------------------------------ |
| Id         | Guid     |                                |
| UserId     | Guid     | Clé étrangère vers User        |
| FoodItemId | Guid     | Référence vers FoodItem        |
| SavedAt    | DateTime | Date de sauvegarde             |

**Responsabilités :**

- Mémoriser les aliments fréquemment utilisés par l'utilisateur
- Permettre un accès rapide à ses aliments habituels lors de la création d'un repas

**Invariants :**

- La suppression d'un User entraîne la suppression de ses SavedFoodItem
- Un même FoodItem ne peut être sauvegardé qu'une seule fois par User

---

### `WeightEntry`

Enregistrement du poids de l'utilisateur à un instant donné. Ne peut pas exister sans son User.

> **Pourquoi `WeightEntry` et pas un champ `Weight` fixe sur `User` ?** Un champ fixe écrase la valeur à chaque mise à jour — aucun historique possible. `WeightEntry` permet de suivre l'évolution du poids dans le temps, de fournir le poids de référence au moment de la création d'une Diet (WeightEntry le plus récent), et de comparer le poids réel contre `Diet.TargetWeight` pour le suivi du régime.

**Attributs :**

| Attribut   | Type     | Notes                   |
| ---------- | -------- | ----------------------- |
| Id         | Guid     |                         |
| UserId     | Guid     | Clé étrangère vers User |
| Weight     | float    | En kilogrammes          |
| MeasuredAt | DateOnly | Date de la mesure       |

**Responsabilités :**

- Stocker le poids mesuré et la date de mesure
- Permettre le suivi de la progression pondérale dans le temps
- Fournir le poids de référence pour le calcul BMR/TDEE au moment de la création d'une Diet

**Invariants :**

- La suppression d'un User entraîne la suppression de ses WeightEntry

---

### `FoodItem`

Table de référence locale des données alimentaires issues d'Open Food Facts. Partagée entre tous les utilisateurs.

> **`FoodItem` couvre deux catégories :**
> - **Ingrédients bruts** — farine, tomate, mozzarella, poulet...
> - **Produits finis** — Pizza Margherita Buitoni, Sandwich jambon-beurre, Lasagnes bolognaise...
>
> Pour le domaine, la distinction est transparente — un `MealItem` référence un `FoodItem` quel que soit son type. L'utilisateur peut donc composer un `Meal` avec des ingrédients détaillés ou simplement sélectionner un produit fini comme une pizza entière. Open Food Facts fournit les valeurs nutritionnelles pour 100g dans les deux cas.

> **Stratégie de recherche en 2 niveaux :**
> 1. **Cache Redis** — si le mot-clé a déjà été cherché récemment, réponse immédiate sans toucher la base
> 2. **PostgreSQL** (`FoodItem`) — si absent du cache, lecture en base + alimentation du cache
>
> Si l'aliment est introuvable en base → réponse vide. Aucun appel direct à l'API Open Food Facts au moment de la recherche.
>
> **Alimentation de la table `FoodItem` :** un job planifié (couche Infrastructure) importe le dump officiel Open Food Facts quotidiennement. La base est ainsi pré-remplie avec 3M+ produits indépendamment des actions utilisateur. Voir `docs/annexes/infrastructure-import-off.md`.

**Attributs :**

| Attribut        | Type              | Notes                                                      |
| --------------- | ----------------- | ---------------------------------------------------------- |
| Id              | Guid              | Identifiant interne                                        |
| OffId           | string            | Identifiant Open Food Facts (code-barres)                  |
| Name            | string            |                                                            |
| CaloriesPer100g | float             | kcal pour 100g                                             |
| ProteinsPer100g | float             | g pour 100g                                                |
| CarbsPer100g    | float             | g pour 100g                                                |
| FatsPer100g     | float             | g pour 100g                                                |
| AllergensTags   | List\<Allergen\>  | Tags normalisés OFF (ex: en:gluten)                        |
| CachedAt        | DateTime          | Date de récupération depuis Open Food Facts                |

**Responsabilités :**

- Stocker les informations nutritionnelles d'un aliment (calories, macros, allergènes)
- Servir de référence partagée entre tous les utilisateurs pour la recherche et la création de repas

---

## Value Objects

Valeurs immuables sans identité propre.

### `MacroDistribution`

Répartition cible des macronutriments en pourcentage. Appartient à une `Diet` ou un `DietPlan`.

> **Ce que c'est :** Un **objectif** — ce que l'utilisateur *devrait* manger sur son régime.
> Exemple : régime Keto → 5% glucides / 70% lipides / 25% protéines.
>
> **Ce que ce n'est pas :** Ce n'est pas ce que l'utilisateur a réellement mangé. Ce n'est pas exprimé en grammes. C'est uniquement une répartition proportionnelle qui définit les règles du régime.
>
> **Pourquoi des pourcentages et pas des grammes ?** Les grammes dépendent du `CalorieTarget` — qui lui appartient à la `Diet`. La répartition en % reste stable quel que soit l'objectif calorique. Cela permet de réutiliser `MacroDistribution` aussi bien sur `DietPlan` (sans CalorieTarget) que sur `Diet`.

| Attribut          | Type | Description                        |
| ----------------- | ---- | ---------------------------------- |
| ProteinPercentage | int  | % de calories venant des protéines |
| CarbPercentage    | int  | % de calories venant des glucides  |
| FatPercentage     | int  | % de calories venant des lipides   |

**Invariant :** ProteinPercentage + CarbPercentage + FatPercentage = 100%

---

### `NutritionInfo`

Valeurs nutritionnelles réelles d'un aliment pour une quantité donnée. Appartient à un `MealItem`.

> **Ce que c'est :** Une **réalité mesurée** — ce que l'utilisateur *a vraiment* mangé pour un aliment donné à une quantité donnée.
> Exemple : 150g de poulet → 247 kcal, 46g de protéines, 5g de lipides, 0g de glucides.
>
> **Ce que ce n'est pas :** Ce n'est pas un objectif. Ce n'est pas exprimé en pourcentages.
>
> **Pourquoi un snapshot ?** Les données de `FoodItem` peuvent être mises à jour (cache Open Food Facts). Stocker un snapshot à la création garantit que l'historique nutritionnel de l'utilisateur ne change jamais rétroactivement.
>
> **Différence clé avec `MacroDistribution` :**
>
> | | MacroDistribution | NutritionInfo |
> |---|---|---|
> | Nature | Objectif du régime | Valeurs réelles consommées |
> | Unité | % | grammes / kcal |
> | Appartient à | `Diet` / `DietPlan` | `MealItem` |
> | Modifiable | Non (VO immuable) | Non (VO immuable — snapshot) |

| Attribut | Type  | Description              |
| -------- | ----- | ------------------------ |
| Calories | float | kcal                     |
| Proteins | float | grammes                  |
| Carbs    | float | grammes                  |
| Fats     | float | grammes                  |

**Calcul :** `FoodItem.XxxPer100g × (MealItem.Quantity / 100)`
**Snapshot** — calculé une fois à la création du MealItem, puis stocké définitivement.

---

### `NutritionNeeds`

Résultat du calcul nutritionnel personnalisé. N'est pas persisté — calculé à la demande.

| Attribut          | Type   | Description                       |
| ----------------- | ------ | --------------------------------- |
| Bmr               | float  | Métabolisme de base (kcal)        |
| Tdee              | float  | Dépense énergétique totale (kcal) |
| TargetCalories    | float  | Objectif calorique selon le Goal  |
| MacroDistribution | MacroDistribution (VO) | Répartition cible des macros en % |

---

## Relations entre les concepts

```
User
├── possède plusieurs DietPlan personnels (IsTemplate = false — toujours modifiables)
│   └── sert de base pour lancer une Diet (snapshot au lancement — lien coupé ensuite)
├── accède en lecture aux DietPlan templates (IsTemplate = true, UserId = null) — Pro/Business uniquement
├── possède plusieurs Diet (une seule Active à la fois, optionnelle)
│   ├── lancée depuis un DietPlan (snapshot indépendant)
│   ├── porte un Name, Goal, DietType, TargetWeight, MacroDistribution (copiés du DietPlan)
│   ├── porte un CalorieTarget (calculé au lancement)
│   └── StartDate = date du lancement (imposée système)
├── possède plusieurs Meal (indépendant de Diet)
│   └── contient plusieurs MealItem
│       └── référence un FoodItem
├── possède plusieurs WeightEntry (historique du poids)
└── possède plusieurs SavedFoodItem (liste personnelle d'aliments)
    └── référence un FoodItem

Service : déduit la Diet active à la date d'un Meal via Diet.StartDate / EndDate (uniquement pour le bilan nutritionnel)
```

---

## Authentification & Autorisation

### Flux d'authentification

Keycloak est le fournisseur d'identité (OAuth2/OIDC). L'API ne gère pas les mots de passe.

```
Client → Keycloak (login) → JWT Bearer token
Client → API (Bearer token) → Middleware valide le JWT → extrait sub → résout User.Id
```

- `sub` du JWT = `User.KeycloakId` — clé de résolution de l'identité interne
- Toutes les requêtes sur des données personnelles sont filtrées par `User.Id` résolu depuis le token

### Rôles Keycloak

| Rôle | Qui | Accès |
|---|---|---|
| `user` | Tous les utilisateurs authentifiés | Données personnelles + données partagées selon tier |
| `admin` | Compte interne (service account) | Gestion des templates, opérations RGPD, import OFF |

### Isolation des données

| Type de donnée | Règle d'accès |
|---|---|
| `Diet`, `Meal`, `DietPlan` personnel, `WeightEntry`, `SavedFoodItem` | Filtrées par `userId` du token — un utilisateur ne voit jamais les données d'un autre |
| `FoodItem` | Partagé — accessible à tous les utilisateurs authentifiés |
| `DietPlan` template (`IsTemplate = true`) | Partagé — accessible en lecture seule aux tiers Pro et Business |

### Autorisation par tier

Le tier (`User.SubscriptionTier`) est **toujours lu en base**, jamais depuis le JWT.

Les vérifications s'effectuent dans la **couche Application** (services), jamais dans le domaine ni dans l'API.

| Violation | Code HTTP |
|---|---|
| Token absent ou invalide | 401 Unauthorized |
| Rôle insuffisant (ex: user tente d'accéder à admin) | 403 Forbidden |
| Tier insuffisant (ex: Free tente d'accéder aux templates) | 403 Forbidden |
| Limite tier dépassée (ex: 3ème DietPlan en Free) | 403 Forbidden |

---

## Enums

| Enum            | Valeurs                                                                        |
| --------------- | ------------------------------------------------------------------------------ |
| `ActivityLevel` | Sedentary, LightlyActive, ModeratelyActive, VeryActive, ExtremelyActive        |
| `Goal`          | WeightLoss, Maintenance, WeightGain                                            |
| `DietType`      | Balanced, HighProtein, Keto, Mediterranean, LowCarb, Vegetarian, Vegan, Custom |
| `DietStatus`    | Active, Inactive, Archived                                                     |
| `MealType`      | Breakfast, Lunch, Dinner, Snack                                                |
| `Gender`        | Male, Female, Other                                                            |
| `Allergen`      | Gluten, Crustaceans, Eggs, Fish, Peanuts, Soybeans, Milk, Nuts, Celery, Mustard, SesameSeeds, SulphurDioxide, Lupin, Molluscs |
| `SubscriptionTier` | Free, Pro, Business |

---

## Décisions transverses — à traiter avant la mise en production

> Ces points ne modifient pas le modèle domaine actuel mais ont un impact sur l'implémentation et la conformité légale.

### Politique de rétention des données

**Décision non tranchée.** Les questions à trancher côté produit :
- Conservation tant que le compte est actif ?
- Suppression automatique après X mois d'inactivité ?
- Export des données proposé à l'utilisateur avant suppression ?

**Impact technique probable :** Soft delete sur `User` (`DeletedAt`) avec cascade sur toutes ses données liées.

### Conformité RGPD

Les données alimentaires (`Meal`, `MealItem`, `WeightEntry`) sont des **données de santé** au sens de l'Article 9 du RGPD. Elles sont donc soumises à des obligations renforcées :

| Obligation | Impact technique |
|---|---|
| Droit à l'effacement (Art. 17) | Endpoint de suppression de compte avec cascade complète |
| Portabilité des données (Art. 20) | Endpoint d'export des données utilisateur |
| Consentement explicite | Formulaire d'inscription avec consentement à la collecte de données de santé |
| Durée de conservation définie | Liée à la décision de politique de rétention ci-dessus |

> **Pourquoi c'est important ?** Ces obligations s'appliquent dès le premier utilisateur en production. Ne pas les traiter comme des fonctionnalités secondaires.

---

## Ce qui appartient au Service (pas au domaine)

Ces calculs nécessitent des données externes au domaine — ils vivent dans la couche Application.

| Calcul                                          | Pourquoi c'est un Service                                               |
| ----------------------------------------------- | ----------------------------------------------------------------------- |
| Calcul BMR / TDEE                               | Nécessite les formules et les facteurs NAP — règle externe au domaine   |
| Calcul CalorieTarget à la création d'une Diet   | Utilise le WeightEntry le plus récent + profil User + Goal de la Diet   |
| Déduction de la Diet active à la date d'un Meal | Compare la date du Meal aux Diet.StartDate / EndDate du User            |
| Proposition MacroDistribution selon DietType    | Nécessite une table de correspondance externe                           |
| Alertes de déséquilibre                         | Compare les apports agrégés aux objectifs — implique plusieurs agrégats |
