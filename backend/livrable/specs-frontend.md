# Specs Frontend — API de Gestion de Régime Alimentaire

> **Phase 5b — Validation des contrats API depuis les besoins réels du frontend**
> Ce document est agnostique du support (web, mobile, desktop) — il ne décrit pas le layout visuel, uniquement les données affichées et les appels API nécessaires par écran.

---

## Périmètre MVP — Écrans identifiés

| #   | Écran              | Description                                                | UC couverts |
| --- | ------------------ | ---------------------------------------------------------- | ----------- |
| 1   | Profil utilisateur | Données physiologiques + besoins calculés (BMR/TDEE)       | UC02, UC03  |
| 2   | Dashboard          | Diet active + bilan du jour + alertes                      | UC03, UC08  |
| 3   | Gestion DietPlans  | Liste des plans, créer / modifier / supprimer              | UC04        |
| 4   | Diet active        | Détails + lancement depuis un DietPlan + action "Terminer" | UC05        |
| 5   | Saisie repas       | Créer un repas + rechercher aliments + ajouter MealItems   | UC06, UC07  |
| 6   | Bilan nutritionnel | Bilan journalier + hebdomadaire + par Diet complète        | UC08, UC09  |
| 7   | Suivi du poids     | Historique WeightEntries + ajout / modification            | UC11        |
| 8   | RGPD               | Demande suppression + confirmation + réactivation compte   | UC12        |

> **Note UC01 — Authentification :** Ce cas d'usage est entièrement géré par Keycloak (redirection OAuth2/OIDC). Il n'y a pas d'écran à spécifier côté application — le frontend redirige vers Keycloak et reçoit le token JWT en retour.

> **Note UC10 — Recommandations alimentaires :** Hors périmètre MVP. Vision future — aucun écran à spécifier pour cette version.

---

## Format d'un écran

```
## Écran N — [Nom]

**But :** [Ce que l'utilisateur fait sur cet écran]

**Données affichées**
- [Donnée 1]
- [Donnée 2]

**Appels API**
- [MÉTHODE] /endpoint  →  { champs retournés }

**Actions disponibles**
- [Action 1 — appel API correspondant]
```

---

## Écran 1 — Profil utilisateur

**But :** Consulter et modifier ses données physiologiques, visualiser ses besoins nutritionnels calculés

**Données affichées**

- Prénom, email
- Âge, sexe, taille, poids actuel (dernière WeightEntry)
- Niveau d'activité physique
- Allergies (liste des Allergen)
- BMR calculé (kcal/jour)
- TDEE calculé (kcal/jour)

**Appels API**

- `GET /users/me` → `{ id, firstName, email, age, gender, height, activityLevel, allergies, latestWeight, bmr, tdee }`
- `PUT /users/me` → `{ age, gender, height, activityLevel, allergies }` — mise à jour du profil

**Actions disponibles**

- Modifier les données physiologiques → `PUT /users/me`
- Gérer les allergies (ajout / suppression) → `PUT /users/me`
- Supprimer son compte → redirection vers Écran 8 (RGPD)

---

## Écran 2 — Dashboard

**But :** Vue d'ensemble rapide — Diet active, avancement du jour, alerte si déséquilibre

**Données affichées**

- Diet active : nom du plan, type de régime, CalorieTarget, date de début
- Bilan du jour : calories consommées vs CalorieTarget, macros consommées vs cibles (%)
- Alerte déséquilibre si écart > seuil
- Dernier poids enregistré + delta vs poids de départ de la Diet

**Appels API**

- `GET /diets/active` → `{ id, planName, dietType, calorieTarget, startDate, macroDistribution }`
- `GET /diets/{id}/bilan?period=day&date=today` → `{ consumed, calorieTarget, delta, macros, alert }`
- `GET /users/me/weight-entries?limit=1` → `{ value, measuredAt }`

**Actions disponibles**

- Accéder au bilan complet → Écran 6
- Ajouter un repas → Écran 5
- Ajouter une entrée de poids → Écran 7

---

## Écran 3 — Gestion DietPlans

**But :** Consulter, créer, modifier et supprimer ses plans de régime réutilisables

**Données affichées**

- Liste des DietPlans : nom, type de régime, répartition macros (%)
- Indicateur si un plan est actuellement utilisé comme base d'une Diet active

**Appels API**

- `GET /diet-plans` → `[{ id, name, dietType, macroDistribution }]`
- `POST /diet-plans` → créer un nouveau plan
- `PUT /diet-plans/{id}` → modifier un plan existant
- `DELETE /diet-plans/{id}` → supprimer un plan

**Actions disponibles**

- Créer un nouveau plan → `POST /diet-plans`
- Modifier un plan → `PUT /diet-plans/{id}`
- Supprimer un plan → `DELETE /diet-plans/{id}`
- Lancer un régime depuis un plan → Écran 4

---

## Écran 4 — Diet active

**But :** Lancer un régime depuis un DietPlan et consulter / terminer la Diet en cours

**Données affichées**

- DietPlan source : nom, type, répartition macros
- CalorieTarget calculé (snapshot au lancement)
- Date de début
- Statut (Active / Archived)
- Poids de référence au lancement (WeightEntry utilisée pour le calcul)

**Appels API**

- `GET /diets/active` → `{ id, planName, dietType, calorieTarget, startDate, status, referenceWeight }`
- `POST /diet-plans/{id}/launch` → lancement du plan → `201 { id, calorieTarget, startDate }`
- `POST /diets/{id}/archive` → terminer la Diet active (EndDate = aujourd'hui)

**Actions disponibles**

- Lancer un régime (depuis Écran 3) → `POST /diet-plans/{id}/launch`
- Terminer le régime actif → `POST /diets/{id}/archive`

---

## Écran 5 — Saisie repas

**But :** Créer un repas, rechercher des aliments et ajouter des MealItems avec les quantités

**Données affichées**

- Type de repas (petit-déjeuner / déjeuner / dîner / collation)
- Date et heure du repas (modifiable — repas rétroactifs autorisés)
- Liste des MealItems : nom aliment, quantité (g), calories, macros calculés
- Total nutritionnel du repas en cours
- Résultats de recherche aliment : nom, marque, valeurs nutritionnelles / 100g, allergènes

**Appels API**

- `POST /meals` → `{ mealType, consumedAt }` → `201 { id }`
- `GET /users/me/saved-food-items` → liste des favoris chargée une fois à l'ouverture de l'écran
- `GET /food-items?search={terme}` → `[{ id, name, brand, nutritionPer100g, allergens }]`
- `POST /meals/{id}/items` → `{ foodItemId, quantityInGrams }` → `201 { id, nutritionInfo }`
- `DELETE /meals/{id}/items/{itemId}` → supprimer un MealItem
- `POST /users/me/saved-food-items` → `{ foodItemId }` → sauvegarder un aliment dans les favoris

**Actions disponibles**

- Rechercher un aliment → `GET /food-items?search=`
- Ajouter un aliment au repas → `POST /meals/{id}/items`
- Supprimer un MealItem → `DELETE /meals/{id}/items/{itemId}`
- Sauvegarder un aliment en favori → `POST /users/me/saved-food-items`

---

## Écran 6 — Bilan nutritionnel

**But :** Consulter ses apports nutritionnels sur une période (jour / semaine / durée complète d'une Diet)

**Données affichées**

- Sélecteur de période : journalier / hebdomadaire / Diet complète
- Calories consommées vs CalorieTarget (valeur + %)
- Macros consommées vs cibles (grammes réels vs % objectif)
- Jours conformes sur la période (journalier uniquement)
- Tendances hebdomadaires : moyenne calories, moyenne macros

**Appels API**

- `GET /diets/{id}/bilan?period=day&date={date}` → `{ consumed, calorieTarget, delta, macros, alert }`
- `GET /diets/{id}/bilan?period=week&startDate={date}` → `{ averageCalories, averageMacros, compliantDays }`
- `GET /diets/{id}/bilan` → bilan sur toute la durée de la Diet

**Actions disponibles**

- Changer la période → paramètre `period` sur `GET /diets/{id}/bilan`
- Naviguer entre les jours / semaines → paramètre `date` / `startDate`

---

## Écran 7 — Suivi du poids

**But :** Consulter l'historique du poids et ajouter / modifier des entrées

**Données affichées**

- Historique des WeightEntries : poids (kg) + date
- Poids actuel (dernière entrée)
- Delta vs poids de départ de la Diet active
- Courbe d'évolution (données brutes — rendu graphique côté frontend)

**Appels API**

- `GET /users/me/weight-entries` → `[{ id, value, measuredAt }]`
- `POST /users/me/weight-entries` → `{ value, measuredAt }` → `201 { id }`
- `PUT /users/me/weight-entries/{id}` → `{ value, measuredAt }` → modifier une entrée existante

**Actions disponibles**

- Ajouter une entrée de poids → `POST /users/me/weight-entries`
- Modifier une entrée → `PUT /users/me/weight-entries/{id}`

---

## Écran 8 — RGPD

**But :** Exercer ses droits RGPD — demander la suppression du compte ou réactiver un compte en grace period

**Données affichées**

- Statut du compte (Actif / En cours de suppression + date d'expiration de la grace period)
- Lien de réactivation (valable 30 jours après la demande de suppression)

**Appels API**

- `DELETE /users/me` → demande de suppression (Keycloak désactivé + email envoyé avec lien signé 30j)
- `POST /users/me/reactivate` → `{ token }` → réactivation via token signé (Keycloak réactivé)

**Actions disponibles**

- Demander la suppression du compte → `DELETE /users/me` (confirmation requise côté frontend)
- Réactiver le compte (depuis le lien email) → `POST /users/me/reactivate` avec token en body
