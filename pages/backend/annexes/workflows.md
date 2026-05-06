# Workflows — Flux métier

> Tous les flux séquentiels du système Nutrition API.
> Source : fichiers `.mermaid` dans `annexes/`.

---

## 1. Authentification

```mermaid
sequenceDiagram
    participant Front as Client Frontend
    participant KC as Keycloak
    participant API as API ASP.NET Core

    Front->>KC: Requête d'authentification (auth code flow) avec client_id, redirect_uri, scope=openid
    KC-->>Front: Affiche formulaire login / inscription

    Front->>KC: Envoie credentials (login ou inscription)
    KC-->>Front: Redirige avec code d'autorisation (redirect_uri?code=xxx)

    Front->>KC: POST /token avec code + client_id + redirect_uri + PKCE
    KC-->>Front: access_token + refresh_token + id_token

    Note right of Front: Gestion session KC via token

    Front->>API: Requête API avec access_token (Authorization: Bearer ...)
    API->>KC: Vérifie validité token via introspection ou JWT validation
    alt token valide
        API->>API: Enregistre l'utilisateur dans la base métier si nouveau
        API-->>Front: Réponse OK (données métier)
    else token invalide
        API-->>Front: Erreur 401 Unauthorized
    end
```

---

## 2. Création du profil utilisateur

```mermaid
sequenceDiagram
    participant Device as Device (Client)
    participant KC as Keycloak
    participant API as API ASP.NET Core
    participant DB as PostgreSQL

    Note over Device: Précondition — access_token valide obtenu via Keycloak

    Note over Device: Formulaire obligatoire :<br/>BirthDate, Gender, Height, Weight,<br/>ActivityLevel, Allergies*, DietaryPreferences*<br/>(*choix explicite ou "Aucune contre-indication")

    Device->>API: POST /users/profile<br/>Authorization: Bearer access_token<br/>{ BirthDate, Gender, Height, Weight, ActivityLevel, Allergies, DietaryPreferences }

    API->>KC: Valide access_token (JWT validation)
    alt Token invalide ou expiré
        KC-->>API: Token rejeté
        API-->>Device: 401 Unauthorized
    else Token valide
        KC-->>API: Token valide — KeycloakId extrait

        API->>DB: SELECT User WHERE KeycloakId = ?
        alt Profil déjà existant
            DB-->>API: User trouvé
            API-->>Device: 409 Conflict — profil déjà créé
        else Profil inexistant
            DB-->>API: Aucun résultat

            alt Données invalides (champ manquant, valeur hors plage)
                API-->>Device: 400 Bad Request — détail des erreurs de validation
            else Données valides
                API->>DB: INSERT User { KeycloakId, BirthDate, Gender, Height,<br/>ActivityLevel, Allergies, DietaryPreferences, CreatedAt }
                API->>DB: INSERT WeightEntry { UserId, Weight, MeasuredAt = aujourd'hui }
                DB-->>API: Succès
                API-->>Device: 201 Created — { UserId, profil complet }
                Note over Device: Profil créé — redirection vers le dashboard utilisateur
            end
        end
    end
```

---

## 3. Mise à jour du profil

```mermaid
sequenceDiagram
    participant Device as Device (Client)
    participant KC as Keycloak
    participant API as API ASP.NET Core
    participant DB as PostgreSQL

    Note over Device: Précondition — access_token valide + profil utilisateur existant

    Note over Device: L'utilisateur modifie un ou plusieurs champs de son profil :<br/>BirthDate?, Gender?, Height?, ActivityLevel?,<br/>Allergies?, DietaryPreferences?

    Device->>API: PUT /users/me/profile<br/>Authorization: Bearer access_token<br/>{ BirthDate?, Gender?, Height?, ActivityLevel?,<br/>  Allergies?, DietaryPreferences? }

    API->>KC: Valide access_token (JWT validation)
    alt Token invalide ou expiré
        KC-->>API: Token rejeté
        API-->>Device: 401 Unauthorized
    else Token valide
        KC-->>API: Token valide — KeycloakId extrait

        API->>DB: SELECT User WHERE KeycloakId = ?
        alt Profil introuvable
            DB-->>API: Aucun résultat
            API-->>Device: 404 Not Found
        else Profil trouvé
            DB-->>API: User { UserId, ... }

            alt Données invalides (valeur hors plage, enum inconnu)
                API-->>Device: 400 Bad Request — détail des erreurs
            else Données valides
                API->>DB: UPDATE User SET<br/>BirthDate = ?, Gender = ?, Height = ?,<br/>ActivityLevel = ?, Allergies = ?,<br/>DietaryPreferences = ?<br/>WHERE Id = UserId
                DB-->>API: Succès
                API-->>Device: 200 OK — profil mis à jour
                Note over Device: Seuls les champs fournis sont mis à jour
            end
        end
    end
```

---

## 4. Gestion des DietPlans et lancement

```mermaid
sequenceDiagram
    participant Device as Device (Client)
    participant KC as Keycloak
    participant API as API ASP.NET Core
    participant DB as PostgreSQL

    Note over Device: Précondition — access_token valide + profil utilisateur existant

    %% PARTIE 1 — Création d'un DietPlan personnel
    Note over Device: L'utilisateur remplit le formulaire de plan :<br/>Name, DietType, Goal, TargetWeight, MacroDistribution

    Device->>API: POST /diet-plans<br/>Authorization: Bearer access_token<br/>{ Name, DietType, Goal, TargetWeight, MacroDistribution }

    API->>KC: Valide access_token (JWT validation)
    alt Token invalide ou expiré
        KC-->>API: Token rejeté
        API-->>Device: 401 Unauthorized
    else Token valide
        KC-->>API: Token valide — KeycloakId extrait

        API->>DB: SELECT User WHERE KeycloakId = ?
        alt Profil introuvable
            DB-->>API: Aucun résultat
            API-->>Device: 404 Not Found — profil utilisateur non créé
        else Profil trouvé
            DB-->>API: User { UserId, SubscriptionTier }

            API->>DB: SELECT COUNT(*) FROM DietPlan WHERE UserId = ? AND IsTemplate = false
            DB-->>API: count
            alt Limite atteinte (Free ≥ 2 / Pro ≥ 20 / Business : aucune)
                API-->>Device: 403 Forbidden — limite de plans personnels atteinte
            else Limite non atteinte
                alt Données invalides (champ manquant, MacroDistribution ≠ 100%)
                    API-->>Device: 400 Bad Request — détail des erreurs de validation
                else Données valides
                    API->>DB: INSERT DietPlan { UserId, Name, DietType, Goal,<br/>TargetWeight, MacroDistribution, IsTemplate = false }
                    DB-->>API: Succès
                    API-->>Device: 201 Created — { DietPlanId, plan complet }
                end
            end
        end
    end

    %% PARTIE 2 — Lancement d'un DietPlan → Diet active
    Note over Device: L'utilisateur sélectionne un DietPlan et clique "Lancer"

    Device->>API: POST /diet-plans/{dietPlanId}/launch<br/>Authorization: Bearer access_token

    API->>KC: Valide access_token (JWT validation)
    alt Token invalide ou expiré
        KC-->>API: Token rejeté
        API-->>Device: 401 Unauthorized
    else Token valide
        KC-->>API: Token valide — KeycloakId extrait

        API->>DB: SELECT User WHERE KeycloakId = ?
        DB-->>API: User { UserId }

        API->>DB: SELECT DietPlan WHERE Id = dietPlanId AND UserId = ?
        alt DietPlan introuvable
            DB-->>API: Aucun résultat
            API-->>Device: 404 Not Found
        else DietPlan trouvé
            DB-->>API: DietPlan { Name, DietType, Goal, TargetWeight, MacroDistribution }

            API->>DB: SELECT Diet WHERE UserId = ? AND DietStatus = Active
            alt Diet active existante
                DB-->>API: Diet active trouvée
                API-->>Device: 409 Conflict — un régime est déjà actif
            else Aucune Diet active
                DB-->>API: Aucun résultat

                API->>DB: SELECT WeightEntry WHERE UserId = ?<br/>ORDER BY MeasuredAt DESC LIMIT 1
                alt Aucune entrée de poids
                    DB-->>API: Aucun résultat
                    API-->>Device: 422 Unprocessable Entity — aucune mesure de poids enregistrée
                else WeightEntry trouvé
                    DB-->>API: WeightEntry { Weight, MeasuredAt }

                    Note over API: Calcul BMR (Mifflin-St Jeor) :<br/>BMR = f(Weight, Height, BirthDate, Gender)<br/>TDEE = BMR × ActivityLevel<br/>CalorieTarget = TDEE ± ajustement selon Goal

                    API->>DB: INSERT Diet { UserId, Name, DietType, Goal,<br/>TargetWeight, MacroDistribution, CalorieTarget,<br/>StartDate = aujourd'hui, EndDate = null, DietStatus = Active }
                    DB-->>API: Succès
                    API-->>Device: 201 Created — { DietId, diet complète }
                    Note over Device: Régime actif — redirection vers le tableau de bord
                end
            end
        end
    end
```

---

## 5. Terminer une Diet

```mermaid
sequenceDiagram
    participant Device as Device (Client)
    participant KC as Keycloak
    participant API as API ASP.NET Core
    participant DB as PostgreSQL

    Note over Device: Précondition — access_token valide + Diet active existante

    Note over Device: L'utilisateur clique sur "Terminer mon régime"

    Device->>API: POST /diets/{dietId}/archive<br/>Authorization: Bearer access_token

    API->>KC: Valide access_token (JWT validation)
    alt Token invalide ou expiré
        KC-->>API: Token rejeté
        API-->>Device: 401 Unauthorized
    else Token valide
        KC-->>API: Token valide — KeycloakId extrait

        API->>DB: SELECT User WHERE KeycloakId = ?
        DB-->>API: User { UserId }

        API->>DB: SELECT Diet WHERE Id = dietId AND UserId = ?
        alt Diet introuvable ou n'appartient pas à l'utilisateur
            DB-->>API: Aucun résultat
            API-->>Device: 404 Not Found
        else Diet trouvée
            DB-->>API: Diet { DietStatus, EndDate }

            alt Diet déjà archivée
                API-->>Device: 409 Conflict — ce régime est déjà terminé
            else Diet active
                Note over API: EndDate = aujourd'hui (imposée système)<br/>DietStatus = Archived

                API->>DB: UPDATE Diet SET<br/>DietStatus = Archived,<br/>EndDate = aujourd'hui<br/>WHERE Id = dietId
                DB-->>API: Succès

                API-->>Device: 200 OK — { DietId, DietStatus = Archived, EndDate }
                Note over Device: Régime terminé — l'utilisateur peut lancer un nouveau plan
            end
        end
    end
```

---

## 6. Enregistrement de repas

```mermaid
sequenceDiagram
    participant Device as Device (Client)
    participant KC as Keycloak
    participant API as API ASP.NET Core
    participant DB as PostgreSQL

    Note over Device: Précondition — access_token valide + profil utilisateur existant

    %% CAS 1 — Depuis un repas sauvegardé
    Note over Device: L'utilisateur consulte sa liste de repas sauvegardés

    Device->>API: GET /meals?saved=true<br/>Authorization: Bearer access_token
    API->>KC: Valide access_token
    KC-->>API: Token valide — KeycloakId extrait
    API->>DB: SELECT Meal WHERE UserId = ? AND IsSaved = true
    DB-->>API: Liste des repas sauvegardés (avec leurs MealItems)
    API-->>Device: 200 OK — liste des repas sauvegardés

    Note over Device: L'utilisateur sélectionne un repas sauvegardé,<br/>ajuste les quantités et valide

    Device->>API: POST /meals<br/>Authorization: Bearer access_token<br/>{ Name, MealType, ConsumedAt, IsSaved = false,<br/>  Items: [{ FoodItemId, Quantity }, ...] }

    API->>KC: Valide access_token
    KC-->>API: Token valide — KeycloakId extrait
    API->>DB: SELECT User WHERE KeycloakId = ?
    DB-->>API: User { UserId }

    alt Aucun MealItem fourni
        API-->>Device: 400 Bad Request — un repas doit contenir au moins un aliment
    else Au moins un MealItem
        alt Quantité invalide (≤ 0)
            API-->>Device: 400 Bad Request — la quantité doit être supérieure à 0
        else Quantités valides
            loop Pour chaque MealItem
                API->>DB: SELECT FoodItem WHERE Id = FoodItemId
                DB-->>API: FoodItem { CaloriesPer100g, ProteinsPer100g, CarbsPer100g, FatsPer100g }
                Note over API: Calcul NutritionInfo (snapshot) :<br/>Calories = CaloriesPer100g × (Quantity / 100)
            end
            API->>DB: INSERT Meal + MealItems × N
            DB-->>API: Succès
            API-->>Device: 201 Created — { MealId, repas complet avec valeurs nutritionnelles }
        end
    end

    %% CAS 2 — Nouveau repas from scratch
    Note over Device: L'utilisateur crée un nouveau repas<br/>et choisit de le sauvegarder ou non

    Device->>API: POST /meals<br/>Authorization: Bearer access_token<br/>{ Name, MealType, ConsumedAt, IsSaved, Notes?,<br/>  Items: [{ FoodItemId, Quantity }, ...] }

    API->>KC: Valide access_token
    KC-->>API: Token valide — KeycloakId extrait
    API->>DB: SELECT User WHERE KeycloakId = ?
    DB-->>API: User { UserId }

    alt IsSaved = true
        API->>DB: SELECT COUNT(*) FROM Meal WHERE UserId = ? AND IsSaved = true
        DB-->>API: count
        alt Limite atteinte (Free ≥ 5 / Pro ≥ 50 / Business : aucune)
            API-->>Device: 403 Forbidden — limite de repas sauvegardés atteinte
        else Limite non atteinte
            API->>DB: INSERT Meal { IsSaved = true } + MealItems × N
            DB-->>API: Succès
            API-->>Device: 201 Created — repas sauvegardé dans la liste personnelle
        end
    else IsSaved = false
        API->>DB: INSERT Meal { IsSaved = false } + MealItems × N
        DB-->>API: Succès
        API-->>Device: 201 Created — repas enregistré pour la journée
    end
```

---

## 7. Bilan nutritionnel

```mermaid
sequenceDiagram
    participant Device as Device (Client)
    participant KC as Keycloak
    participant API as API ASP.NET Core
    participant DB as PostgreSQL

    Note over Device: Précondition — access_token valide + profil utilisateur existant

    Note over Device: L'utilisateur sélectionne une Diet et demande son bilan

    Device->>API: GET /diets/{dietId}/bilan<br/>Authorization: Bearer access_token

    API->>KC: Valide access_token (JWT validation)
    alt Token invalide ou expiré
        KC-->>API: Token rejeté
        API-->>Device: 401 Unauthorized
    else Token valide
        KC-->>API: Token valide — KeycloakId extrait

        API->>DB: SELECT User WHERE KeycloakId = ?
        DB-->>API: User { UserId, SubscriptionTier }

        API->>DB: SELECT Diet WHERE Id = dietId AND UserId = ?
        alt Diet introuvable
            DB-->>API: Aucun résultat
            API-->>Device: 404 Not Found
        else Diet trouvée
            DB-->>API: Diet { Name, CalorieTarget, MacroDistribution,<br/>TargetWeight, StartDate, EndDate, DietStatus }

            Note over API: Période effective clampée selon SubscriptionTier :<br/>Free → max 7 derniers jours<br/>Pro → max 1 an<br/>Business → période complète de la Diet

            API->>DB: SELECT Meal JOIN MealItem<br/>WHERE UserId = ? AND ConsumedAt BETWEEN StartDate AND EndDate
            DB-->>API: Liste des MealItems avec NutritionInfo par jour

            API->>DB: SELECT WeightEntry<br/>WHERE UserId = ? AND MeasuredAt BETWEEN StartDate AND EndDate
            DB-->>API: Liste des WeightEntry { MeasuredAt, Weight }

            Note over API: Agrégation par jour :<br/>totalCalories, totalProteins, totalCarbs, totalFats<br/>+ pourcentages vs CalorieTarget et MacroDistribution<br/>+ résumé global (moyennes)

            API-->>Device: 200 OK —<br/>{ diet, dailyData[], weightEntries[], summary }
        end
    end
```

---

## 8. Recherche d'aliment

```mermaid
sequenceDiagram
    participant Device as Device (Client)
    participant Cache as Cache (Redis)
    participant KC as Keycloak
    participant API as API ASP.NET Core
    participant DB as PostgreSQL

    Note over Device: Précondition — access_token valide + profil utilisateur existant
    Note over DB: FoodItem pré-remplie via import dump OFF quotidien

    %% PARTIE 1 — Recherche par mot-clé
    Device->>API: GET /food-items?search={motclé}<br/>Authorization: Bearer access_token

    API->>KC: Valide access_token (JWT validation)
    alt Token invalide ou expiré
        KC-->>API: Token rejeté
        API-->>Device: 401 Unauthorized
    else Token valide
        KC-->>API: Token valide

        API->>Cache: GET food-items:{motclé}
        alt Résultats trouvés en cache
            Cache-->>API: Liste FoodItem
            API-->>Device: 200 OK — liste des aliments (depuis cache)
        else Cache miss
            Cache-->>API: Aucun résultat

            API->>DB: SELECT FoodItem WHERE Name LIKE %motclé%
            alt Résultats trouvés en base
                DB-->>API: Liste FoodItem
                API->>Cache: SET food-items:{motclé} (TTL court)
                API-->>Device: 200 OK — liste des aliments (depuis base)
            else Introuvable en base
                DB-->>API: Aucun résultat
                API-->>Device: 200 OK — liste vide
            end
        end
    end

    %% PARTIE 2 — Sauvegarde dans la liste personnelle
    Note over Device: L'utilisateur sélectionne un aliment et clique "Sauvegarder"

    Device->>API: POST /users/me/saved-food-items<br/>Authorization: Bearer access_token<br/>{ FoodItemId }

    API->>KC: Valide access_token (JWT validation)
    alt Token invalide ou expiré
        KC-->>API: Token rejeté
        API-->>Device: 401 Unauthorized
    else Token valide
        KC-->>API: Token valide — KeycloakId extrait

        API->>DB: SELECT User WHERE KeycloakId = ?
        DB-->>API: User { UserId, SubscriptionTier }

        API->>DB: SELECT SavedFoodItem WHERE UserId = ? AND FoodItemId = ?
        alt Déjà sauvegardé
            DB-->>API: SavedFoodItem trouvé
            API-->>Device: 409 Conflict — aliment déjà dans la liste personnelle
        else Pas encore sauvegardé
            API->>DB: SELECT COUNT(*) FROM SavedFoodItem WHERE UserId = ?
            DB-->>API: count
            alt Limite atteinte (Free ≥ 10 / Pro ≥ 100 / Business : aucune)
                API-->>Device: 403 Forbidden — limite d'aliments sauvegardés atteinte
            else Limite non atteinte
                API->>DB: INSERT SavedFoodItem { UserId, FoodItemId, SavedAt }
                DB-->>API: Succès
                API-->>Device: 201 Created — aliment ajouté à la liste personnelle
            end
        end
    end
```

---

## 9. Gestion du poids

```mermaid
sequenceDiagram
    participant Device as Device (Client)
    participant KC as Keycloak
    participant API as API ASP.NET Core
    participant DB as PostgreSQL

    Note over Device: Précondition — access_token valide + profil utilisateur existant

    %% PARTIE 1 — Ajouter une entrée de poids
    Note over Device: L'utilisateur saisit son poids<br/>MeasuredAt = aujourd'hui par défaut (modifiable)

    Device->>API: POST /users/me/weight-entries<br/>Authorization: Bearer access_token<br/>{ Weight, MeasuredAt }

    API->>KC: Valide access_token
    KC-->>API: Token valide — KeycloakId extrait

    API->>DB: SELECT User WHERE KeycloakId = ?
    DB-->>API: User { UserId }

    alt Données invalides (Weight ≤ 0)
        API-->>Device: 400 Bad Request
    else Données valides
        API->>DB: SELECT WeightEntry WHERE UserId = ? AND MeasuredAt = ?
        alt Entrée existante pour cette date
            DB-->>API: WeightEntry trouvé
            API-->>Device: 409 Conflict — une pesée existe déjà pour cette date
        else Aucune entrée pour cette date
            DB-->>API: Aucun résultat
            API->>DB: INSERT WeightEntry { UserId, Weight, MeasuredAt }
            DB-->>API: Succès
            API-->>Device: 201 Created — { WeightEntryId, Weight, MeasuredAt }
        end
    end

    %% PARTIE 2 — Modifier une entrée de poids
    Note over Device: L'utilisateur modifie une pesée existante

    Device->>API: PUT /users/me/weight-entries/{id}<br/>Authorization: Bearer access_token<br/>{ Weight?, MeasuredAt? }

    API->>KC: Valide access_token
    KC-->>API: Token valide — KeycloakId extrait

    API->>DB: SELECT User WHERE KeycloakId = ?
    DB-->>API: User { UserId }

    API->>DB: SELECT WeightEntry WHERE Id = ? AND UserId = ?
    alt Introuvable ou n'appartient pas à l'utilisateur
        DB-->>API: Aucun résultat
        API-->>Device: 404 Not Found
    else Trouvé
        DB-->>API: WeightEntry existant

        alt Nouvelle MeasuredAt déjà prise par une autre entrée
            API->>DB: SELECT WeightEntry WHERE UserId = ? AND MeasuredAt = ? AND Id ≠ ?
            DB-->>API: Conflit trouvé
            API-->>Device: 409 Conflict — une pesée existe déjà pour cette date
        else Pas de conflit
            API->>DB: UPDATE WeightEntry SET Weight = ?, MeasuredAt = ? WHERE Id = ?
            DB-->>API: Succès
            API-->>Device: 200 OK — { WeightEntryId, Weight, MeasuredAt }
        end
    end
```

---

## 10. RGPD

```mermaid
sequenceDiagram
    participant Device as Device (Client)
    participant KC as Keycloak
    participant API as API ASP.NET Core
    participant DB as PostgreSQL
    participant KCAdmin as Keycloak Admin API
    participant Mail as Service Email

    Note over Device: Précondition — access_token valide + profil utilisateur existant

    %% PARTIE 1 — Export des données (RGPD Art. 20)
    Note over Device: L'utilisateur demande l'export de toutes ses données

    Device->>API: GET /users/me/export<br/>Authorization: Bearer access_token

    API->>KC: Valide access_token
    KC-->>API: Token valide — KeycloakId extrait

    API->>DB: SELECT User + WeightEntries + DietPlans + Diets<br/>+ Meals + MealItems + SavedFoodItems<br/>WHERE UserId = ?
    DB-->>API: Toutes les données utilisateur

    API-->>Device: 200 OK — fichier JSON contenant toutes les données

    %% PARTIE 2 — Suppression du compte (RGPD Art. 17)
    Note over Device: L'utilisateur demande la suppression de son compte

    Device->>API: DELETE /users/me<br/>Authorization: Bearer access_token

    API->>KC: Valide access_token
    KC-->>API: Token valide — KeycloakId extrait

    API->>DB: SELECT User WHERE KeycloakId = ?
    DB-->>API: User { UserId, KeycloakId }

    alt Compte déjà en attente de suppression
        API-->>Device: 409 Conflict — suppression déjà demandée
    else Compte actif
        API->>DB: UPDATE User SET DeletedAt = maintenant
        DB-->>API: Succès

        API->>KCAdmin: PATCH /admin/realms/{realm}/users/{KeycloakId}<br/>{ enabled: false }
        KCAdmin-->>API: Succès — compte Keycloak désactivé

        API->>Mail: Envoyer email de confirmation avec lien de réactivation (30 jours)
        Mail-->>API: Email envoyé

        API-->>Device: 200 OK — compte en cours de suppression
    end

    %% PARTIE 3 — Réactivation du compte (< 30 jours)
    Note over Device: L'utilisateur clique sur le lien de réactivation reçu par email

    Device->>API: POST /users/me/reactivate<br/>{ token: "lien signé reçu par email" }

    API->>API: Valide le token signé (non expiré + correspond à UserId)

    alt Token invalide ou expiré
        API-->>Device: 400 Bad Request — lien invalide ou expiré
    else Token valide
        API->>DB: SELECT User WHERE Id = ? AND DeletedAt IS NOT NULL
        alt DeletedAt > 30 jours (compte déjà purgé)
            DB-->>API: Aucun résultat
            API-->>Device: 404 Not Found — compte définitivement supprimé
        else Dans le délai de 30 jours
            DB-->>API: User trouvé
            API->>DB: UPDATE User SET DeletedAt = null
            DB-->>API: Succès
            API->>KCAdmin: PATCH /admin/realms/{realm}/users/{KeycloakId}<br/>{ enabled: true }
            KCAdmin-->>API: Succès — compte Keycloak réactivé
            API-->>Device: 200 OK — compte réactivé. Toutes vos données sont intactes.
        end
    end

    %% PARTIE 4 — Purge automatique après 30 jours (job Infrastructure)
    Note over API: Job planifié — exécuté quotidiennement

    API->>DB: SELECT User WHERE DeletedAt <= maintenant - 30 jours
    DB-->>API: Liste des utilisateurs à purger

    loop Pour chaque utilisateur à purger
        API->>DB: DELETE cascade :<br/>MealItems → Meals → WeightEntries<br/>SavedFoodItems → DietPlans → Diets → User
        DB-->>API: Succès
        API->>KCAdmin: DELETE /admin/realms/{realm}/users/{KeycloakId}
        KCAdmin-->>API: Compte Keycloak supprimé définitivement
    end

    Note over API: Purge terminée — données irrécupérables
```
