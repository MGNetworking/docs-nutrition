# Recensement des tests

**Type :** Interne
**Référence spec :** [Niveaux de tests — définitions et périmètres](niveaux-de-tests.md)](niveaux-de-tests.md)

> **Portée de ce document : le périmètre — l'inventaire des cas qui doivent exister.**
> Il ne définit pas les niveaux (voir [Niveaux de tests — définitions et périmètres](niveaux-de-tests.md)](niveaux-de-tests.md)) et **ne porte
> aucun état d'avancement**.

> **Où lire l'avancement**
> — **Jira** fait foi : NTR-105 à NTR-111 (niveau 2), NTR-28 et ses sous-tâches (niveau 3).
> — Dans le code, les tests déjà cadrés existent en stubs `[Fact(Skip = "IT-XX-00 : …")]` :
>   compilés, ils ne peuvent pas dériver de la réalité.
>
> Une case à cocher ici créerait une troisième source de vérité, condamnée à devenir fausse.

---

## Niveau 1 — Tests unitaires

Écrits au fil des tickets feature. Cible : ~400 tests.

| Périmètre | Fichiers de tests |
|---|---|
| Controllers (service mocké, HttpContext manuel) | `*ControllerTest.cs` |
| Middlewares (pipeline mocké) | `UserResolutionMiddlewareTest.cs`, `ExceptionMiddlewareTest.cs` |
| Domain / Value Objects / Entités | `NutritionApi.Domain.Tests` |
| Services applicatifs | `NutritionApi.Application.Tests` |
| Traduction Open Food Facts (code pur) | `Jobs/OffImport/OffProductMapperTest.cs` |
| Cache Redis (multiplexeur mocké — clé, durée de vie, repli en panne) | `Caching/RedisFoodCacheServiceTest.cs` |

---

## Niveau 2 — Tests d'intégration interne

Jira : NTR-29 (chapeau) → NTR-134 (socle) et sous-tâches NTR-105 à NTR-111. Les sections
RgpdController et NutritionController n'ont pas de sous-tâche dédiée : elles restent rattachées au
chapeau NTR-29.

> **État au 2026-07-29 — 100 tests livrés.** Les identifiants au-delà de la nomenclature initiale
> (IT-ADM-10+, IT-USR-17+, IT-DP-11+, IT-DT-13+, IT-ML-17+) ont été ajoutés **pendant**
> l'implémentation : ils couvrent des comportements que le recensement initial ne prévoyait pas —
> ownership, limites de palier, invariants de domaine. Ils sont consignés ici pour que le
> recensement reste le reflet de ce qui existe.
>
> Le socle est décrit dans [Écrire un test de niveau 2](tests-niveau-2.md).
>
> **Trois défauts de production ont été découverts par ces tests**, aucun n'étant détectable en test
> unitaire : toute saisie invalide renvoyait 500 (NTR-135), aucun utilisateur ne pouvait s'inscrire
> (NTR-142), et vider un repas renvoyait 500. Les trois sont corrigés.

### Middlewares transverses (NTR-105)

#### UserResolutionMiddleware

| ID | Scénario | Résultat attendu |
|----|----------|------------------|
| IT-MW-01 | Token JWT valide + user présent en DB | `UserId` injecté dans `Items` → controller reçoit le bon Guid |
| IT-MW-02 | Token JWT valide + user absent en DB (sub inconnu) | 401 — middleware coupe la chaîne |
| IT-MW-03 | Requête sans token sur endpoint `[Authorize]` | 401 — bloqué par JWT middleware avant `UserResolutionMiddleware` |

#### ExceptionMiddleware

| ID | Scénario | Résultat attendu |
|----|----------|------------------|
| IT-EX-01 | Service lève `NotFoundException` | 404 ProblemDetails avec `detail` du message |
| IT-EX-02 | Service lève `ConflictException` | 409 ProblemDetails |
| IT-EX-03 | Service lève `ForbiddenException` | 403 ProblemDetails |
| IT-EX-04 | Service lève `UnprocessableException` | 422 ProblemDetails |
| IT-EX-05 | Exception non gérée | 500 ProblemDetails — message générique |

#### Auth JWT

| ID | Scénario | Résultat attendu |
|----|----------|------------------|
| IT-AUTH-01 | Token absent sur n'importe quel endpoint `[Authorize]` | 401 |
| IT-AUTH-02 | Token expiré | 401 — **couvert au niveau 3 par IT-EXT-18** : `TestAuthHandler` remplace ici le composant qui vérifie l'expiration, le cas n'y est pas testable |
| IT-AUTH-03 | Token valide, rôle insuffisant (`[Authorize(Roles = "admin")]`) | 403 |
| IT-AUTH-04 | Token valide avec rôle `admin` → endpoint admin | 200/201/204 selon l'endpoint |

#### Pipeline global

| ID | Scénario | Résultat attendu |
|----|----------|------------------|
| IT-PIPE-01 | Body JSON invalide (model binding failure) | 400 ProblemDetails standard ASP.NET |
| IT-PIPE-02 | Route inexistante | 404 |
| IT-PIPE-03 | Paramètre `{id:guid}` avec GUID malformé | **404** — corrigé après implémentation : la contrainte `:guid` participe à la **sélection** de l'endpoint, une valeur non conforme empêche la route de correspondre. Il n'y a donc aucune action à exécuter, et rien qui puisse produire un 400. |

---

### AdminController — `GET|POST|PUT|DELETE /api/v1/admin` (NTR-106)
> Restriction : `[Authorize(Roles = "admin")]`

| ID | Endpoint | Scénario | Résultat attendu |
|----|----------|----------|------------------|
| IT-ADM-01 | `GET /admin/dashboard` | User sans rôle admin | 403 |
| IT-ADM-02 | `GET /admin/dashboard` | User avec rôle admin | 200 `AdminDashboardResponse` |
| IT-ADM-03 | `GET /admin/system/health` | User admin | 200 `SystemHealthResponse` |
| IT-ADM-04 | `POST /admin/diet-plans/templates` | Body valide | 201 `DietPlanResponse` |
| IT-ADM-05 | `POST /admin/diet-plans/templates` | Body invalide | 422 |
| IT-ADM-06 | `PUT /admin/diet-plans/templates/{id}` | Template existant | 200 |
| IT-ADM-07 | `PUT /admin/diet-plans/templates/{id}` | Template inexistant | 404 |
| IT-ADM-08 | `DELETE /admin/diet-plans/templates/{id}` | Template existant | 204 |
| IT-ADM-09 | `DELETE /admin/diet-plans/templates/{id}` | Template inexistant | 404 |
| IT-ADM-10 | `PUT /admin/diet-plans/templates/{id}` | L'identifiant désigne un plan **personnel** | 404 — la route admin ne doit pas révéler l'existence d'un plan qui n'est pas un template |
| IT-ADM-11 | `POST /admin/diet-plans/templates` | Macros dont la somme n'atteint pas 100 % | 422 — invariant de `MacroDistribution` |
| IT-ADM-12 | `GET /admin/system/health` | User sans rôle admin | 403 |

---

### UsersController — `* /api/v1/users/me` (NTR-107)
> Restriction : `[Authorize]` — lit `sub` claim (pas de `UserResolutionMiddleware` sur ces endpoints)

| ID | Endpoint | Scénario | Résultat attendu |
|----|----------|----------|------------------|
| IT-USR-01 | `POST /users/me` | Nouveau user (sub inconnu) | 201 `UserProfileResponse` |
| IT-USR-02 | `POST /users/me` | User déjà existant (sub connu) | 409 |
| IT-USR-03 | `GET /users/me` | User existant | 200 `UserProfileResponse` |
| IT-USR-04 | `GET /users/me` | sub valide mais absent en DB | 404 |
| IT-USR-05 | `PUT /users/me` | User existant, body valide | 200 |
| IT-USR-06 | `PUT /users/me` | User inexistant | 404 |
| IT-USR-07 | `POST /users/me/weight-entries` | Entrée valide | 201 `WeightEntryResponse` |
| IT-USR-08 | `POST /users/me/weight-entries` | Date déjà enregistrée | 409 |
| IT-USR-09 | `GET /users/me/weight-entries` | User avec historique | 200 liste |
| IT-USR-10 | `PUT /users/me/weight-entries/{id}` | Entrée existante | 200 |
| IT-USR-11 | `PUT /users/me/weight-entries/{id}` | Entrée inexistante | 404 |
| IT-USR-12 | `GET /users/me/saved-food-items` | User avec favoris | 200 liste |
| IT-USR-13 | `POST /users/me/saved-food-items` | Aliment non déjà sauvegardé | 201 |
| IT-USR-14 | `POST /users/me/saved-food-items` | Aliment déjà sauvegardé | 409 |
| IT-USR-15 | `DELETE /users/me/saved-food-items/{id}` | Favori existant | 204 |
| IT-USR-16 | `DELETE /users/me/saved-food-items/{id}` | Favori inexistant | 404 |
| IT-USR-17 | `PUT /users/me` | Date de naissance dans le futur | 422 — invariant de `User` |
| IT-USR-18 | `PUT /users/me` | Taille négative | 422 — invariant de `User` |
| IT-USR-19 | `PUT /users/me/weight-entries/{id}` | Pesée appartenant à un autre utilisateur | 404 — et non 403 : révéler son existence serait une fuite d'information |
| IT-USR-20 | `POST /users/me/saved-food-items` | Limite du palier atteinte (Free : 10) | 403 |
| IT-USR-21 | `DELETE /users/me/saved-food-items/{id}` | Favori appartenant à un autre utilisateur | 403 |
| IT-USR-22 | `POST /users/me/weight-entries` | **Sans date fournie**, une pesée existe déjà pour aujourd'hui | 409 — le contrôle doit porter sur la date effective. Son absence laissait créer des doublons silencieux (NTR-145) |
| IT-USR-22 | `GET /users/me` | Jeton valide, aucun profil en base | 401 — la dispense `[AllowWithoutProfile]` ne vaut que pour la création |

---

### RgpdController — `* /api/v1/rgpd` (NTR-29)
> Restriction : `[Authorize]`. Ces routes sont portées par `RgpdController`, **pas** par
> `UsersController` — voir [RGPD — Droits de l'utilisateur](../systemes/rgpd/index.md).

| ID | Endpoint | Scénario | Résultat attendu |
|----|----------|----------|------------------|
| IT-RGPD-01 | `DELETE /rgpd` | User existant | 204 |
| IT-RGPD-02 | `DELETE /rgpd` | User inexistant | 404 |
| IT-RGPD-03 | `POST /rgpd/reactivate` | User inactif | 200 |
| IT-RGPD-04 | `POST /rgpd/reactivate` | User déjà actif | 409 |
| IT-RGPD-05 | `POST /rgpd/reactivate` | User inexistant | 404 |
| IT-RGPD-06 | `GET /rgpd/export` | User existant | 200 avec données RGPD (ZIP) |

---

### DietPlansController — `* /api/v1/diet-plans` (NTR-108)
> Restriction : `[Authorize]` — utilise `UserResolutionMiddleware` (Items["UserId"])

| ID | Endpoint | Scénario | Résultat attendu |
|----|----------|----------|------------------|
| IT-DP-01 | `GET /diet-plans` | User avec plans | 200 — vérifie que `UserResolutionMiddleware` a injecté le bon `UserId` |
| IT-DP-02 | `POST /diet-plans` | Body valide | 201 `DietPlanResponse` |
| IT-DP-03 | `POST /diet-plans` | Body invalide | 422 |
| IT-DP-04 | `PUT /diet-plans/{id}` | Plan existant et appartient à l'user | 200 |
| IT-DP-05 | `PUT /diet-plans/{id}` | Plan appartenant à un autre user | 403 |
| IT-DP-06 | `PUT /diet-plans/{id}` | Plan inexistant | 404 |
| IT-DP-07 | `DELETE /diet-plans/{id}` | Plan existant et ownership | 204 |
| IT-DP-08 | `DELETE /diet-plans/{id}` | Plan inexistant | 404 |
| IT-DP-09 | `GET /diet-plans/templates` | User Free | 403 |
| IT-DP-10 | `GET /diet-plans/templates` | User Pro/Business | 200 liste templates |
| IT-DP-11 | `POST /diet-plans` | Limite du palier atteinte (Free : 2) | 403 |
| IT-DP-12 | `POST /diet-plans` | Palier Pro sous sa limite (20) alors que le quota Free serait dépassé | 201 |
| IT-DP-13 | `POST /diet-plans` | Champ `name` absent du corps JSON | 400 — validation de liaison de modèle, distincte du 422 des invariants |

> Le lancement d'un plan (`POST /diets/{id}/launch`) est porté par `DietsController` — voir la
> section suivante.

---

### DietsController — `* /api/v1/diets` (NTR-109)
> Restriction : `[Authorize]` — utilise `UserResolutionMiddleware`

| ID | Endpoint | Scénario | Résultat attendu |
|----|----------|----------|------------------|
| IT-DT-01 | `GET /diets/active` | Diet active existante | 200 `DietResponse` |
| IT-DT-02 | `GET /diets/active` | Aucune diet active | 404 |
| IT-DT-03 | `GET /diets` | Historique non vide | 200 liste |
| IT-DT-04 | `GET /diets/{id}` | Diet existante et ownership | 200 |
| IT-DT-05 | `GET /diets/{id}` | Diet inexistante | 404 |
| IT-DT-06 | `POST /diets/{id}/archive` | Diet active → archivée | 200 avec nouveau statut |
| IT-DT-07 | `POST /diets/{id}/archive` | Diet déjà archivée | 422 |
| IT-DT-08 | `POST /diets/{id}/archive` | Diet inexistante | 404 |
| IT-DT-09 | `POST /diets/{id}/launch` | Plan valide, pas de Diet active | 201 `DietResponse` |
| IT-DT-10 | `POST /diets/{id}/launch` | Diet déjà active (409 métier) | 409 |
| IT-DT-11 | `POST /diets/{id}/launch` | Plan inexistant | 404 |
| IT-DT-12 | `POST /diets/{id}/launch` | Données du plan insuffisantes | 422 |
| IT-DT-13 | `GET /diets/{id}` | Diète appartenant à un autre utilisateur | 403 |
| IT-DT-14 | `POST /diets/{id}/launch` | Lancement d'un **template** en palier Free | 403 |

---

### NutritionController — `GET /api/v1/nutrition/{id}/bilan` (NTR-29)
> Restriction : `[Authorize]` — le bilan est porté par `NutritionController`, **pas** par
> `DietsController`. Le `{id}` est celui de la Diet.

| ID | Endpoint | Scénario | Résultat attendu |
|----|----------|----------|------------------|
| IT-NUT-01 | `GET /nutrition/{id}/bilan?period=day` | Bilan journalier | 200 `NutritionBilanResponse` |
| IT-NUT-02 | `GET /nutrition/{id}/bilan?period=week` | Bilan hebdomadaire | 200 |
| IT-NUT-03 | `GET /nutrition/{id}/bilan?period=custom&startDate=...&endDate=...` | Bilan sur plage personnalisée | 200 |
| IT-NUT-04 | `GET /nutrition/{id}/bilan` | Diet appartenant à un autre user | 403 |
| IT-NUT-05 | `GET /nutrition/{id}/bilan` | Diet inexistante | 404 |

---

### FoodItemsController — `GET /api/v1/food-items` (NTR-110)
> Restriction : `[Authorize]` — orchestration Redis + PostgreSQL (voir [Workflow — Cache des recherches d'aliments](../systemes/aliments/workflow-cache-recherche.md))

| ID | Endpoint | Scénario | Résultat attendu |
|----|----------|----------|------------------|
| IT-FD-01 | `GET /food-items?search=poulet` | Cache Redis hit | 200 — résultat servi depuis Redis |
| IT-FD-02 | `GET /food-items?search=poulet` | Cache Redis miss → PostgreSQL | 200 — résultat depuis DB + stocké en Redis (TTL 24h) |
| IT-FD-03 | `GET /food-items?search=poulet&limit=5` | Limit respectée | 200 — au plus 5 résultats |
| IT-FD-04 | `GET /food-items` (sans `search`) | Paramètre obligatoire absent | 400 |

---

### MealsController — `* /api/v1/meals` (NTR-111)
> Restriction : `[Authorize]` — utilise `UserResolutionMiddleware`

| ID | Endpoint | Scénario | Résultat attendu |
|----|----------|----------|------------------|
| IT-ML-01 | `POST /meals` | User avec diet active, body valide | 201 `MealResponse` |
| IT-ML-02 | `POST /meals` | User sans diet active | 403 |
| IT-ML-03 | `POST /meals` | FoodItem référencé inexistant | 404 |
| IT-ML-04 | `GET /meals` | Sans filtre | 200 liste |
| IT-ML-05 | `GET /meals?saved=true` | Filtre repas sauvegardés | 200 — uniquement repas `saved` |
| IT-ML-06 | `GET /meals?date=2024-01-15` | Filtre par date | 200 — uniquement repas du jour |
| IT-ML-07 | `GET /meals/{id}` | Repas existant et ownership | 200 |
| IT-ML-08 | `GET /meals/{id}` | Repas inexistant | 404 |
| IT-ML-09 | `PATCH /meals/{id}` | Repas existant | 200 |
| IT-ML-10 | `PATCH /meals/{id}` | Repas inexistant | 404 |
| IT-ML-11 | `DELETE /meals/{id}` | Repas existant | 204 |
| IT-ML-12 | `DELETE /meals/{id}` | Repas inexistant | 404 |
| IT-ML-13 | `POST /meals/{id}/items` | FoodItem valide | 201 `MealResponse` mis à jour |
| IT-ML-14 | `POST /meals/{id}/items` | Repas inexistant | 404 |
| IT-ML-15 | `DELETE /meals/{id}/items/{itemId}` | Item existant | 204 |
| IT-ML-16 | `DELETE /meals/{id}/items/{itemId}` | Item inexistant | 404 |
| IT-ML-17 | `DELETE /meals/{id}/items/{itemId}` | **Dernier** item du repas | 422 — le domaine interdit de vider un repas ; il faut supprimer le repas lui-même |
| IT-ML-18 | `POST /meals` | Repas **ponctuel** alors que le quota de repas sauvegardés est dépassé | 201 — la limite ne s'applique qu'aux repas sauvegardés |
| IT-ML-19 | `POST /meals` | Quantité négative sur un item | 422 — invariant de `MealItem` |
| IT-ML-20 | `GET /meals/{id}` | Repas appartenant à un autre utilisateur | 403 |

---

## Niveau 3 — Tests d'intégration externe

Jira : NTR-28 → sous-tâches NTR-72 (repositories), NTR-73 (Redis et import OFF).
**23 cas** — IT-EXT-01 à 19 et IT-JOB-01 à 04.

> **État : 23 cas implémentés, 23 verts.** Projet `tests/NutritionApi.ExternalIntegration.Tests`, lancement
> par `./scripts/test-integration.sh`. Voir [Écrire un test de niveau 3](tests-niveau-3.md) pour le
> fonctionnement, les quatre défauts trouvés, et l'écart restant — IT-EXT-13 s'appuie sur
> `saved_food_items` alors que la contrainte d'unicité de `weight_entries` a depuis été ajoutée, le
> réalignement reste à faire.
>
> IT-EXT-15 à 17 ont été ajoutés après coup : ils éprouvent le comportement en **dépendance coupée**,
> qui n'était pas au recensement initial. Ils coupent réellement un conteneur, d'où une durée de
> suite passée d'environ 20 secondes à 2 minutes.

### Chaîne d'authentification — Keycloak réel

Transférés depuis NTR-74 le 2026-07-27 : au niveau 2, le `TestAuthHandler` remplace le schéma
d'authentification, donc court-circuite précisément le composant à éprouver. Ces cas ne peuvent
vivre qu'ici.

| ID | Scénario | Ce que l'on vérifie |
|----|----------|---------------------|
| IT-EXT-09 | Token émis par Keycloak → `GET /api/v1/users/me` | Chaîne complète : issuer, audience et signature validés par l'API |
| IT-EXT-10 | Token sans le rôle `admin` → `GET /api/v1/admin/dashboard` | 403 — mapping `realm_access.roles` → policy AdminOnly |
| IT-EXT-16 | **Keycloak arrêté**, clés déjà en cache, jeton valide | **200** — la validation étant locale, la coupure est invisible pour les utilisateurs déjà connectés |
| IT-EXT-17 | **Keycloak arrêté au démarrage** de l'application | L'hôte **refuse de démarrer** — sans clés, l'instance rejetterait tous les jetons |
| IT-EXT-18 | Jeton réellement émis puis **expiré** | 401 — reprend IT-AUTH-02, qui ne pouvait pas exister au niveau 2 : `TestAuthHandler` y remplace le composant qui vérifie l'expiration |
| IT-EXT-19 | Jeton dont l'`aud` ne contient pas `nutrition-api` | 401 — sans ce contrôle, un jeton obtenu pour une autre API serait accepté |

### Repositories — PostgreSQL réel

| ID | Scénario | Ce que l'on vérifie |
|----|----------|---------------------|
| IT-EXT-01 | `UserRepository.GetByKeycloakIdAsync` — user existant | Lecture EF Core → PostgreSQL correcte |
| IT-EXT-02 | `DietPlanRepository.GetByUserIdAsync` — plans d'un user | Filtre par UserId en DB |
| IT-EXT-03 | `DietRepository.GetActiveByUserIdAsync` — diet active | Requête avec filtre statut |
| IT-EXT-04 | Migration EF Core appliquée sur schéma vierge | Toutes les tables créées sans erreur |

### Traitement des erreurs de persistance — PostgreSQL réel

Transférés depuis NTR-135 : ce sont les deux seuls cas de ce ticket qu'un test de niveau 2 ne peut
pas couvrir, les doublures y remplaçant précisément le composant à éprouver.

| ID | Scénario | Ce que l'on vérifie |
|----|----------|---------------------|
| IT-EXT-13 | Deux `SavedFoodItem` identiques pour le même user — `weight_entries` ne porte pas de contrainte d'unicité, voir [niveau 3](tests-niveau-3.md#7-les-deux-écarts-assumés-au-recensement) | `ConflictException` et non erreur brute — `DatabaseExceptionInterceptor` reçoit la `PostgresException` `23505` enveloppée par EF Core dans une `DbUpdateException`, et discrimine sur l'exception interne |
| IT-EXT-14 | Conteneur PostgreSQL arrêté, puis appel d'un endpoint de lecture | **503** avec `Retry-After` et non 500 — chemin `NpgsqlException` → `ServiceUnavailableException` |

> `DatabaseExceptionInterceptor.Translate` est couvert par 5 tests unitaires. Ce qui reste à
> éprouver est le **branchement** : qu'EF Core invoque bien l'intercepteur au bon moment. Un
> `AddInterceptors` est une configuration, et une configuration ne se vérifie que contre une vraie base.

### Cache Redis réel

| ID | Scénario | Ce que l'on vérifie |
|----|----------|---------------------|
| IT-EXT-05 | `FoodItemService.SearchAsync` — cache miss puis hit | Écriture + lecture Redis (TTL 24h) |
| IT-EXT-06 | Expiration TTL Redis | Après expiration, retour en PostgreSQL |
| IT-EXT-11 | Import OFF ayant importé ≥ 1 produit → cache | Clés `food:search:*` supprimées ; la recherche suivante renvoie les données à jour |
| IT-EXT-12 | Import OFF n'ayant importé aucun produit | Cache **non** vidé — catalogue inchangé |
| IT-EXT-15 | **Redis arrêté** → recherche d'aliment | **200** avec les données de PostgreSQL — le repli est une promesse du système, un 503 y serait disproportionné |

### Jobs Hangfire

| ID | Scénario | Ce que l'on vérifie |
|----|----------|---------------------|
| IT-EXT-07 | Import OFF déclenché manuellement | Job s'exécute, `FoodItem` insérés en DB |
| IT-EXT-08 | Purge RGPD déclenchée manuellement | Données anonymisées en DB après exécution |
| IT-JOB-01 | Aucun job récurrent enregistré | `GetJobsStatusAsync` renvoie une liste vide |
| IT-JOB-02 | Job enregistré, jamais exécuté | `LastRun` null, `NextRun` renseigné, statut `Scheduled` |
| IT-JOB-03 | Job exécuté avec succès | `LastRun` renseigné, statut `Succeeded` |
| IT-JOB-04 | Nom du job retourné | Exactement `import-off` — garantit `LastImportAt` côté `AdminService` |

---

## Niveau 4 — Smoke tests (environnement déployé)

Jira : NTR-112 · Paliers : NTR-89 (palier 1), NTR-90 (palier 2), NTR-91 (palier 3).

| ID | Scénario | Ce que l'on vérifie |
|----|----------|---------------------|
| IT-SMOKE-01 | `GET /health` et `GET /health/ready` | Pod API démarré ; PostgreSQL et Redis connectés (503 sinon) — **dépend de NTR-88 : ces endpoints n'existent pas encore** |
| IT-SMOKE-02 | `GET /api/v1/users/me` avec le JWT du compte d'exploitation | Keycloak joignable, JWT validé (issuer, audience, signature), DB répondante |
| IT-SMOKE-03 | `GET /api/v1/food-items?search=poulet` | Redis joignable, PostgreSQL joignable |
