# Règles métier — Domaine Nutrition

> Ces règles définissent les invariants, contraintes et formules de calcul du domaine métier.
> Elles serviront de base pour l'étape 4 — Modèle domaine.

---

## Légende des abréviations

| Abréviation  | Signification                                            |
| ------------ | -------------------------------------------------------- |
| BMR / MB     | Métabolisme de base (calories/jour)                      |
| TDEE / BET   | Dépense énergétique quotidienne totale (calories/jour)   |
| NAP          | Niveau d'Activité Physique (coefficient multiplicateur)  |
| P            | Poids (kg)                                               |
| T            | Taille (cm)                                              |
| A            | Âge (années)                                             |
| MM           | Masse Maigre (kg)                                        |
| IMC          | Indice de Masse Corporelle (kg/m²)                       |
| MG           | Masse Grasse (%)                                         |
| %P / %L / %G | Pourcentage de calories : Protéines / Lipides / Glucides |
| MET          | Équivalent Métabolique de la Tâche (kcal/kg/h)           |

---

## 1. Calcul du métabolisme de base (BMR)

### Mifflin-St Jeor (1990) — formule prioritaire

| Sexe  | Formule                                     |
| ----- | ------------------------------------------- |
| Homme | BMR = (10 × P) + (6,25 × T) - (5 × A) + 5   |
| Femme | BMR = (10 × P) + (6,25 × T) - (5 × A) - 161 |

### Harris-Benedict révisée (1984) — formule alternative

| Sexe  | Formule                                                 |
| ----- | ------------------------------------------------------- |
| Homme | BMR = 88,362 + (13,397 × P) + (4,799 × T) - (5,677 × A) |
| Femme | BMR = 447,593 + (9,247 × P) + (3,098 × T) - (4,330 × A) |

### Autres formules disponibles

| Formule                        | Formule                                              | Cas d'usage                         |
| ------------------------------ | ---------------------------------------------------- | ----------------------------------- |
| Katch-McArdle                  | BMR = 370 + (21,6 × MM)                              | Tient compte de la masse musculaire |
| Harris-Benedict (1919) — Homme | BMR = 66,5 + (13,75 × P) + (5,003 × T) - (6,775 × A) | Version historique                  |
| Harris-Benedict (1919) — Femme | BMR = 655,1 + (9,563 × P) + (1,85 × T) - (4,676 × A) | Version historique                  |

---

## 2. Calcul des besoins caloriques totaux (TDEE)

**TDEE = BMR × NAP**

| Niveau d'activité | NAP   | Description                                        |
| ----------------- | ----- | -------------------------------------------------- |
| Sédentaire        | 1,2   | Peu ou pas d'exercice — travail de bureau          |
| Légèrement actif  | 1,375 | Exercice léger 1-3 jours/semaine                   |
| Modérément actif  | 1,55  | Exercice modéré 3-5 jours/semaine                  |
| Très actif        | 1,725 | Exercice intense 6-7 jours/semaine                 |
| Extrêmement actif | 1,9   | Travail physique intense — athlètes professionnels |

---

## 3. Ajustement calorique selon l'objectif

| Objectif       | Ajustement                              |
| -------------- | --------------------------------------- |
| Perte de poids | TDEE - 15 à 20% (maximum 500 kcal/jour) |
| Maintien       | TDEE                                    |
| Prise de masse | TDEE + 15 à 20% (maximum 500 kcal/jour) |

---

## 4. Répartition des macronutriments

### Par type de régime

| Type de régime | Glucides | Lipides | Protéines |
| -------------- | -------- | ------- | --------- |
| Équilibré      | 50%      | 30%     | 20%       |
| Protéiné       | 40%      | 30%     | 30%       |
| Cétogène       | 5%       | 70%     | 25%       |

### Calcul en grammes

| Macro         | Formule       |
| ------------- | ------------- |
| Protéines (g) | TDEE × %P ÷ 4 |
| Glucides (g)  | TDEE × %G ÷ 4 |
| Lipides (g)   | TDEE × %L ÷ 9 |

### Valeurs caloriques

| Macronutriment | Calories/gramme |
| -------------- | --------------- |
| Protéines      | 4 kcal/g        |
| Glucides       | 4 kcal/g        |
| Lipides        | 9 kcal/g        |

---

## 5. Calculs complémentaires

| Calcul                    | Formule                    |
| ------------------------- | -------------------------- |
| IMC                       | P ÷ T² (T en mètres)       |
| Masse maigre              | P - (P × %MG ÷ 100)        |
| Besoins en eau            | P × 0,033 (litres)         |
| Dépense activité physique | Durée (min) × MET × P ÷ 60 |

---

## 6. Invariants domaine

- **Une seule Diet active par User** — le système bloque (409 Conflict) si une Diet est déjà active au lancement d'un plan ; l'utilisateur doit terminer la Diet en cours avant d'en lancer une autre
- **MacroDistribution totale = 100%** — protéines + glucides + lipides = 100%
- **MealItem ne peut pas exister sans Meal** — suppression du Meal entraîne la suppression des MealItem

---

## 7. Conventions de modélisation

### Responsabilité des champs date/heure

Tout champ date ou heure doit préciser explicitement qui en est responsable.
Il existe deux cas distincts :

| Responsable | Mécanisme | Critère de décision |
|---|---|---|
| **Le système** | `DateTime.UtcNow` automatique dans le constructeur | La valeur est un timestamp technique — l'utilisateur ne la connaît pas et ne la choisit pas |
| **L'utilisateur** | Passé en paramètre du constructeur | La valeur est une donnée réelle connue de l'utilisateur, potentiellement antérieure à l'enregistrement |

**Exemples dans le projet :**

| Champ | Entité | Responsable | Raison |
|---|---|---|---|
| `CreatedAt` | User | Système | Moment technique de création du compte |
| `SavedAt` | SavedFoodItem | Système | Moment technique d'enregistrement du favori |
| `StartDate` | Diet | Système | La Diet démarre au moment du lancement |
| `EndDate` | Diet | Système | La Diet se termine au moment de la clôture |
| `BirthDate` | User | Utilisateur | Donnée réelle connue de l'utilisateur |
| `ConsumedAt` | Meal | Utilisateur | L'utilisateur peut logger un repas consommé plus tôt |
| `MeasuredAt` | WeightEntry | Utilisateur | L'utilisateur peut enregistrer une mesure prise antérieurement |

**Règle à appliquer avant tout nouveau champ date :**

> *"Est-ce que l'utilisateur connaît cette valeur, ou est-ce le système qui la génère ?"*
> - L'utilisateur la connaît → paramètre du constructeur
> - Le système la génère → `DateTime.UtcNow` dans le constructeur
