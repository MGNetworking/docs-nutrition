# Tests — Recensement par niveau

Fichier vivant aligné sur la stratégie définie dans [`design-tests.md`](../design/design-tests.md).  
Chaque niveau répond à une question différente — ne pas dupliquer un test d'un niveau à l'autre.

> **Convention de statut**  
> `[ ]` À écrire — `[x]` Implémenté — `[-]` Hors scope (décision explicite)

---

## Niveau 1 — Tests Unitaires

> *Mon code fonctionne-t-il correctement de manière isolée ?*

Outil : xUnit + Moq — aucune dépendance externe, pas de Docker.

Les tests unitaires sont écrits au fil des tickets feature (par controller, service, middleware).  
Répartition cible : **~400 tests**.

| Périmètre | Fichiers de tests |
|-----------|-------------------|
| Controllers (service mocké, HttpContext manuel) | `*ControllerTest.cs` |
| Middlewares (pipeline mocké) | `UserResolutionMiddlewareTest.cs`, `ExceptionMiddlewareTest.cs` |
| Domain / Value Objects / Entités | à créer lors des tickets NTR-Domain |
| Services applicatifs | à créer lors des tickets NTR-Application |

---

## Niveau 2 — Tests d'Intégration Interne

> *La pipeline ASP.NET Core fonctionne-t-elle correctement ?*

Outil : `WebApplicationFactory<Program>` + helper JWT + `SeedAsync()`.  
Pas de Keycloak réel, pas de PostgreSQL réel — dépendances remplacées par mocks/fakes/InMemory.  
Répartition cible : **10 à 20 tests** (scénarios représentatifs, pas exhaustifs).

Tickets Jira : NTR-29 (chapeau) → sous-tâches NTR-105 à NTR-111.

### Middlewares transverses (NTR-105)

#### UserResolutionMiddleware

| ID | Scénario | Résultat attendu | Statut |
|----|----------|------------------|--------|
| IT-MW-01 | Token JWT valide + user présent en DB | `UserId` injecté dans `Items` → controller reçoit le bon Guid | `[ ]` |
| IT-MW-02 | Token JWT valide + user absent en DB (sub inconnu) | 401 — middleware coupe la chaîne | `[ ]` |
| IT-MW-03 | Requête sans token sur endpoint `[Authorize]` | 401 — bloqué par JWT middleware avant `UserResolutionMiddleware` | `[ ]` |

#### ExceptionMiddleware

| ID | Scénario | Résultat attendu | Statut |
|----|----------|------------------|--------|
| IT-EX-01 | Service lève `NotFoundException` | 404 ProblemDetails avec `detail` du message | `[ ]` |
| IT-EX-02 | Service lève `ConflictException` | 409 ProblemDetails | `[ ]` |
| IT-EX-03 | Service lève `ForbiddenException` | 403 ProblemDetails | `[ ]` |
| IT-EX-04 | Service lève `UnprocessableException` | 422 ProblemDetails | `[ ]` |
| IT-EX-05 | Exception non gérée | 500 ProblemDetails — message générique | `[ ]` |

#### Auth JWT

| ID | Scénario | Résultat attendu | Statut |
|----|----------|------------------|--------|
| IT-AUTH-01 | Token absent sur n'importe quel endpoint `[Authorize]` | 401 | `[ ]` |
| IT-AUTH-02 | Token expiré | 401 | `[ ]` |
| IT-AUTH-03 | Token valide, rôle insuffisant (`[Authorize(Roles = "admin")]`) | 403 | `[ ]` |
| IT-AUTH-04 | Token valide avec rôle `admin` → endpoint admin | 200/201/204 selon l'endpoint | `[ ]` |

#### Pipeline global

| ID | Scénario | Résultat attendu | Statut |
|----|----------|------------------|--------|
| IT-PIPE-01 | Body JSON invalide (model binding failure) | 400 ProblemDetails standard ASP.NET | `[ ]` |
| IT-PIPE-02 | Route inexistante | 404 | `[ ]` |
| IT-PIPE-03 | Paramètre `{id:guid}` avec GUID malformé | 400 | `[ ]` |

---

### AdminController — `GET|POST|PUT|DELETE /api/v1/admin` (NTR-106)
> Restriction : `[Authorize(Roles = "admin")]`

| ID | Endpoint | Scénario | Résultat attendu | Statut |
|----|----------|----------|------------------|--------|
| IT-ADM-01 | `GET /admin/dashboard` | User sans rôle admin | 403 | `[ ]` |
| IT-ADM-02 | `GET /admin/dashboard` | User avec rôle admin | 200 `AdminDashboardResponse` | `[ ]` |
| IT-ADM-03 | `GET /admin/system/health` | User admin | 200 `SystemHealthResponse` | `[ ]` |
| IT-ADM-04 | `POST /admin/diet-plans/templates` | Body valide | 201 `DietPlanResponse` | `[ ]` |
| IT-ADM-05 | `POST /admin/diet-plans/templates` | Body invalide | 422 | `[ ]` |
| IT-ADM-06 | `PUT /admin/diet-plans/templates/{id}` | Template existant | 200 | `[ ]` |
| IT-ADM-07 | `PUT /admin/diet-plans/templates/{id}` | Template inexistant | 404 | `[ ]` |
| IT-ADM-08 | `DELETE /admin/diet-plans/templates/{id}` | Template existant | 204 | `[ ]` |
| IT-ADM-09 | `DELETE /admin/diet-plans/templates/{id}` | Template inexistant | 404 | `[ ]` |

---

### UsersController — `* /api/v1/users/me` (NTR-107)
> Restriction : `[Authorize]` — lit `sub` claim (pas de `UserResolutionMiddleware` sur ces endpoints)

| ID | Endpoint | Scénario | Résultat attendu | Statut |
|----|----------|----------|------------------|--------|
| IT-USR-01 | `POST /users/me` | Nouveau user (sub inconnu) | 201 `UserProfileResponse` | `[ ]` |
| IT-USR-02 | `POST /users/me` | User déjà existant (sub connu) | 409 | `[ ]` |
| IT-USR-03 | `GET /users/me` | User existant | 200 `UserProfileResponse` | `[ ]` |
| IT-USR-04 | `GET /users/me` | sub valide mais absent en DB | 404 | `[ ]` |
| IT-USR-05 | `PUT /users/me` | User existant, body valide | 200 | `[ ]` |
| IT-USR-06 | `PUT /users/me` | User inexistant | 404 | `[ ]` |
| IT-USR-07 | `DELETE /users/me` | User existant | 204 | `[ ]` |
| IT-USR-08 | `DELETE /users/me` | User inexistant | 404 | `[ ]` |
| IT-USR-09 | `POST /users/me/reactivate` | User inactif | 200 | `[ ]` |
| IT-USR-10 | `POST /users/me/reactivate` | User déjà actif | 409 | `[ ]` |
| IT-USR-11 | `POST /users/me/reactivate` | User inexistant | 404 | `[ ]` |
| IT-USR-12 | `GET /users/me/export` | User existant | 200 avec données RGPD | `[ ]` |
| IT-USR-13 | `POST /users/me/weight-entries` | Entrée valide | 201 `WeightEntryResponse` | `[ ]` |
| IT-USR-14 | `POST /users/me/weight-entries` | Date déjà enregistrée | 409 | `[ ]` |
| IT-USR-15 | `GET /users/me/weight-entries` | User avec historique | 200 liste | `[ ]` |
| IT-USR-16 | `PUT /users/me/weight-entries/{id}` | Entrée existante | 200 | `[ ]` |
| IT-USR-17 | `PUT /users/me/weight-entries/{id}` | Entrée inexistante | 404 | `[ ]` |
| IT-USR-18 | `GET /users/me/saved-food-items` | User avec favoris | 200 liste | `[ ]` |
| IT-USR-19 | `POST /users/me/saved-food-items` | Aliment non déjà sauvegardé | 201 | `[ ]` |
| IT-USR-20 | `POST /users/me/saved-food-items` | Aliment déjà sauvegardé | 409 | `[ ]` |
| IT-USR-21 | `DELETE /users/me/saved-food-items/{id}` | Favori existant | 204 | `[ ]` |
| IT-USR-22 | `DELETE /users/me/saved-food-items/{id}` | Favori inexistant | 404 | `[ ]` |

---

### DietPlansController — `* /api/v1/diet-plans` (NTR-108)
> Restriction : `[Authorize]` — utilise `UserResolutionMiddleware` (Items["UserId"])

| ID | Endpoint | Scénario | Résultat attendu | Statut |
|----|----------|----------|------------------|--------|
| IT-DP-01 | `GET /diet-plans` | User avec plans | 200 — vérifie que `UserResolutionMiddleware` a injecté le bon `UserId` | `[ ]` |
| IT-DP-02 | `POST /diet-plans` | Body valide | 201 `DietPlanResponse` | `[ ]` |
| IT-DP-03 | `POST /diet-plans` | Body invalide | 422 | `[ ]` |
| IT-DP-04 | `PUT /diet-plans/{id}` | Plan existant et appartient à l'user | 200 | `[ ]` |
| IT-DP-05 | `PUT /diet-plans/{id}` | Plan appartenant à un autre user | 403 | `[ ]` |
| IT-DP-06 | `PUT /diet-plans/{id}` | Plan inexistant | 404 | `[ ]` |
| IT-DP-07 | `DELETE /diet-plans/{id}` | Plan existant et ownership | 204 | `[ ]` |
| IT-DP-08 | `DELETE /diet-plans/{id}` | Plan inexistant | 404 | `[ ]` |
| IT-DP-09 | `POST /diet-plans/{id}/launch` | Plan valide, pas de Diet active | 201 `DietResponse` | `[ ]` |
| IT-DP-10 | `POST /diet-plans/{id}/launch` | Diet déjà active (409 métier) | 409 | `[ ]` |
| IT-DP-11 | `POST /diet-plans/{id}/launch` | Plan inexistant | 404 | `[ ]` |
| IT-DP-12 | `POST /diet-plans/{id}/launch` | Données du plan insuffisantes | 422 | `[ ]` |
| IT-DP-13 | `GET /diet-plans/templates` | User Free | 403 | `[ ]` |
| IT-DP-14 | `GET /diet-plans/templates` | User Pro/Business | 200 liste templates | `[ ]` |

---

### DietsController — `* /api/v1/diets` (NTR-109)
> Restriction : `[Authorize]` — utilise `UserResolutionMiddleware`

| ID | Endpoint | Scénario | Résultat attendu | Statut |
|----|----------|----------|------------------|--------|
| IT-DT-01 | `GET /diets/active` | Diet active existante | 200 `DietResponse` | `[ ]` |
| IT-DT-02 | `GET /diets/active` | Aucune diet active | 404 | `[ ]` |
| IT-DT-03 | `GET /diets` | Historique non vide | 200 liste | `[ ]` |
| IT-DT-04 | `GET /diets/{id}` | Diet existante et ownership | 200 | `[ ]` |
| IT-DT-05 | `GET /diets/{id}` | Diet inexistante | 404 | `[ ]` |
| IT-DT-06 | `POST /diets/{id}/archive` | Diet active → archivée | 200 avec nouveau statut | `[ ]` |
| IT-DT-07 | `POST /diets/{id}/archive` | Diet déjà archivée | 422 | `[ ]` |
| IT-DT-08 | `POST /diets/{id}/archive` | Diet inexistante | 404 | `[ ]` |
| IT-DT-09 | `GET /diets/{id}/bilan?period=day` | Bilan journalier | 200 `NutritionBilanResponse` | `[ ]` |
| IT-DT-10 | `GET /diets/{id}/bilan?period=week` | Bilan hebdomadaire | 200 | `[ ]` |
| IT-DT-11 | `GET /diets/{id}/bilan?period=custom&startDate=...&endDate=...` | Bilan sur plage personnalisée | 200 | `[ ]` |
| IT-DT-12 | `GET /diets/{id}/bilan` | Diet appartenant à un autre user | 403 | `[ ]` |
| IT-DT-13 | `GET /diets/{id}/bilan` | Diet inexistante | 404 | `[ ]` |

---

### FoodItemsController — `GET /api/v1/food-items` (NTR-110)
> Restriction : `[Authorize]` — orchestration Redis + PostgreSQL (voir `FoodItem Search — flux Redis+PG`)

| ID | Endpoint | Scénario | Résultat attendu | Statut |
|----|----------|----------|------------------|--------|
| IT-FD-01 | `GET /food-items?search=poulet` | Cache Redis hit | 200 — résultat servi depuis Redis | `[ ]` |
| IT-FD-02 | `GET /food-items?search=poulet` | Cache Redis miss → PostgreSQL | 200 — résultat depuis DB + stocké en Redis (TTL 24h) | `[ ]` |
| IT-FD-03 | `GET /food-items?search=poulet&limit=5` | Limit respectée | 200 — au plus 5 résultats | `[ ]` |
| IT-FD-04 | `GET /food-items` (sans `search`) | Paramètre obligatoire absent | 400 | `[ ]` |

---

### MealsController — `* /api/v1/meals` (NTR-111)
> Restriction : `[Authorize]` — utilise `UserResolutionMiddleware`

| ID | Endpoint | Scénario | Résultat attendu | Statut |
|----|----------|----------|------------------|--------|
| IT-ML-01 | `POST /meals` | User avec diet active, body valide | 201 `MealResponse` | `[ ]` |
| IT-ML-02 | `POST /meals` | User sans diet active | 403 | `[ ]` |
| IT-ML-03 | `POST /meals` | FoodItem référencé inexistant | 404 | `[ ]` |
| IT-ML-04 | `GET /meals` | Sans filtre | 200 liste | `[ ]` |
| IT-ML-05 | `GET /meals?saved=true` | Filtre repas sauvegardés | 200 — uniquement repas `saved` | `[ ]` |
| IT-ML-06 | `GET /meals?date=2024-01-15` | Filtre par date | 200 — uniquement repas du jour | `[ ]` |
| IT-ML-07 | `GET /meals/{id}` | Repas existant et ownership | 200 | `[ ]` |
| IT-ML-08 | `GET /meals/{id}` | Repas inexistant | 404 | `[ ]` |
| IT-ML-09 | `PATCH /meals/{id}` | Repas existant | 200 | `[ ]` |
| IT-ML-10 | `PATCH /meals/{id}` | Repas inexistant | 404 | `[ ]` |
| IT-ML-11 | `DELETE /meals/{id}` | Repas existant | 204 | `[ ]` |
| IT-ML-12 | `DELETE /meals/{id}` | Repas inexistant | 404 | `[ ]` |
| IT-ML-13 | `POST /meals/{id}/items` | FoodItem valide | 201 `MealResponse` mis à jour | `[ ]` |
| IT-ML-14 | `POST /meals/{id}/items` | Repas inexistant | 404 | `[ ]` |
| IT-ML-15 | `DELETE /meals/{id}/items/{itemId}` | Item existant | 204 | `[ ]` |
| IT-ML-16 | `DELETE /meals/{id}/items/{itemId}` | Item inexistant | 404 | `[ ]` |

---

## Niveau 3 — Tests d'Intégration Externe

> *Mon application communique-t-elle correctement avec ses dépendances réelles ?*

Outil : `WebApplicationFactory<Program>` + **Testcontainers** (PostgreSQL + Redis réels).  
Répartition cible : **5 à 10 tests**.

Ticket Jira : NTR-28.

### Repositories — PostgreSQL réel

| ID | Scénario | Ce que l'on vérifie | Statut |
|----|----------|---------------------|--------|
| IT-EXT-01 | `UserRepository.GetByKeycloakIdAsync` — user existant | Lecture EF Core → PostgreSQL correcte | `[ ]` |
| IT-EXT-02 | `DietPlanRepository.GetUserPlansAsync` — plans d'un user | Filtre par UserId en DB | `[ ]` |
| IT-EXT-03 | `DietRepository.GetActiveAsync` — diet active | Requête avec filtre statut | `[ ]` |
| IT-EXT-04 | Migration EF Core appliquée sur schéma vierge | Toutes les tables créées sans erreur | `[ ]` |

### Cache Redis réel

| ID | Scénario | Ce que l'on vérifie | Statut |
|----|----------|---------------------|--------|
| IT-EXT-05 | `FoodItemService.SearchAsync` — cache miss puis hit | Ecriture + lecture Redis (TTL 24h) | `[ ]` |
| IT-EXT-06 | Expiration TTL Redis | Après expiration, retour en PostgreSQL | `[ ]` |

### Jobs Hangfire

| ID | Scénario | Ce que l'on vérifie | Statut |
|----|----------|---------------------|--------|
| IT-EXT-07 | Import OFF déclenché manuellement | Job s'exécute, `FoodItem` insérés en DB | `[ ]` |
| IT-EXT-08 | Purge RGPD déclenchée manuellement | Données anonymisées en DB après exécution | `[ ]` |

---

## Niveau 4 — Smoke Tests Kubernetes

> *Le système déployé fonctionne-t-il réellement ?*

Exécutés après chaque déploiement sur un environnement réel (staging/prod).  
Répartition cible : **2 à 5 tests**.

Ticket Jira : NTR-112.

| ID | Scénario | Ce que l'on vérifie | Statut |
|----|----------|---------------------|--------|
| IT-SMOKE-01 | `GET /health` | Pod API démarré, connexions DB/Redis actives | `[ ]` |
| IT-SMOKE-02 | `GET /api/v1/users/me` avec JWT valide | Keycloak joignable, JWT validé, DB répondante | `[ ]` |
| IT-SMOKE-03 | `GET /api/v1/food-items?search=poulet` | Redis joignable, PostgreSQL joignable | `[ ]` |

---

## Infrastructure par niveau

| Niveau | Outil principal | Docker requis | Vitesse |
|--------|-----------------|---------------|---------|
| Niveau 1 — Unitaires | xUnit + Moq | Non | Très rapide |
| Niveau 2 — Intégration Interne | WebApplicationFactory | Non | Rapide |
| Niveau 3 — Intégration Externe | WebApplicationFactory + Testcontainers | Oui | Lent |
| Niveau 4 — Smoke Tests K8s | Client HTTP | Oui (cluster) | Variable |
