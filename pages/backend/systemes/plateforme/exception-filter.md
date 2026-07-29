# Exception Filter (Middleware)

**Ajouté le :** 2026-05-25 · **Refondu le :** 2026-07-29 (NTR-135)
**Type :** Interne

> Ce document décrit la traduction des exceptions en réponses HTTP.
> ➜ Pour la position du middleware dans la chaîne, voir [Pipeline HTTP](pipeline-http.md).
> ➜ Pour la collecte et l'exploitation des journaux qu'il émet, voir [Observabilité](observabilite.md).

---

## Objectif

Traduire toute exception non gérée en réponse HTTP normalisée, sans jamais laisser fuiter de détail
d'infrastructure vers le client.

## Ce qu'il fait

- Traduit les exceptions applicatives et les invariants du domaine en codes HTTP
- Produit un `ProblemDetails` conforme à la **RFC 9457**, porteur d'un `traceId`
- Gradue la journalisation selon que la faute est côté client ou côté serveur

## Ce qu'il ne fait pas

- Ne gère pas l'authentification (401) — c'est le pipeline d'auth
- Ne gère pas la validation de liaison de modèle (400) — c'est `[ApiController]` et les DataAnnotations
- **Ne connaît ni Npgsql ni StackExchange.Redis** — voir « La règle de couche » plus bas

---

## Grille de traduction

| Exception | Code | Origine typique |
|---|---|---|
| `NotFoundException` | **404** | Ressource inexistante — Diet, Meal, FoodItem, WeightEntry, DietPlan, MealItem |
| `ConflictException` | **409** | Diet déjà active · aliment déjà en favori · pesée déjà saisie à cette date · violation d'unicité en base |
| `ForbiddenException` | **403** | Ownership violée · limite de palier atteinte · templates interdits au palier Free |
| `UnprocessableException` | **422** | Lancement d'un régime sans pesée existante |
| **`ArgumentException`** et dérivées | **422** | Invariant du domaine violé — macros ≠ 100 %, date future, poids négatif, énumération à `Unknown` |
| **`ServiceUnavailableException`** | **503** | PostgreSQL ou Keycloak injoignable — avec en-tête `Retry-After` |
| **`OperationCanceledException`** | *aucune* | Le client s'est déconnecté — **seulement** si `RequestAborted` est déclenché |
| Toute autre exception | **500** | Défaut inattendu |

### Pourquoi `ArgumentException` donne 422 et non 500

Par convention du projet (`conventions.md`), les invariants du domaine s'expriment par
`ArgumentException` et `ArgumentOutOfRangeException`. Ces exceptions signalent donc **une donnée
invalide**, pas un défaut interne.

Avant NTR-135, elles tombaient dans le filet générique : une saisie erronée produisait un **500**,
et le contrat OpenAPI — qui annonce 422 — n'était pas tenu. Le défaut a été découvert par
`IT_DP_03`, premier test à faire traverser le pipeline complet à une donnée invalide.

Le message d'origine est **transmis au client** : il vient du domaine et décrit la règle violée
(« Macro percentages must sum to 100 »), ce qui est exactement ce dont l'appelant a besoin.

> **Limite assumée.** Une quinzaine de sites lèvent `ArgumentException` sans être atteignables par
> une saisie — `SubscriptionGuard`, `NutritionCalculator`, `KeycloakAdminService`. Ceux-là signalent
> un vrai défaut et se retrouvent désormais en 422 au lieu de 500. La contrepartie est acceptée :
> ils restent journalisés, et la convention du projet fait d'`ArgumentException` le signal d'une
> donnée invalide.

### Pourquoi `InvalidOperationException` n'est **pas** dans la grille

Le domaine l'utilise pour certains invariants — « un repas doit garder au moins un aliment »
(`Meal.RemoveMealItem`). Il serait tentant de la mapper en 422 comme `ArgumentException`.

**Ce serait une erreur.** `InvalidOperationException` est levée partout par le framework lui-même :
`.First()` sur une collection vide, `.Single()` avec plusieurs éléments, un `DbContext` déjà libéré.
Ces cas sont des **défauts de code**.

La différence tient au traitement, pas au message :

| | 500 | 422 |
|---|---|---|
| Journal | `Error`, avec la trace | `Warning`, sans trace |
| Lecture | « le code a un défaut » | « le client a mal saisi » |
| Suite | on investigue | on ignore |

Un `.First()` sur liste vide devenu 422 serait rangé parmi les erreurs de saisie : il
n'apparaîtrait dans aucune alerte, et survivrait indéfiniment.

**La traduction se fait donc dans le service**, là où le sens de l'exception est connu :

```csharp
// MealService.RemoveItemAsync
if (meal.MealItems.Count <= 1)
    throw new UnprocessableException("A meal must keep at least one item. Delete the meal instead.");
```

Même principe que le 404 sur `MealItem` introuvable : un cas identifié est traduit à l'endroit où on
sait ce qu'il signifie, plutôt qu'un type entier au niveau du middleware.

`ArgumentException` fait exception à cette règle parce que le projet lui a donné une **convention**
explicite (`conventions.md`) : elle signale un invariant de domaine violé, jamais autre chose.

### Pourquoi l'annulation client est conditionnelle

```csharp
catch (OperationCanceledException) when (context.RequestAborted.IsCancellationRequested)
```

Sans la clause `when`, **tout** délai dépassé interne serait silencieusement absorbé. La condition
distingue « le client est parti » — qui n'est pas un incident — de « une opération a expiré côté
serveur », qui en est un et reste en 500.

---

## Format de réponse — RFC 9457

```json
{
  "type": "https://tools.ietf.org/html/rfc9110#section-15.5.5",
  "title": "Ressource introuvable",
  "status": 404,
  "detail": "DietPlan not found.",
  "traceId": "0HN7GK2M4V9PL:00000003"
}
```

| Champ | Rôle |
|---|---|
| `type` | Identifiant **stable** du type de problème — c'est sur lui que s'appuie un client généré (NSwag, Kiota), pas sur le libellé |
| `title` | Libellé de la catégorie, invariant pour un même statut |
| `detail` | Message destiné à l'appelant. **Générique** pour les 500 et 503. |
| `traceId` | `HttpContext.TraceIdentifier` |

### Pourquoi le `traceId` est indispensable

Sans lui, un utilisateur signalant « j'ai eu une erreur » ne laisse **aucun moyen** de retrouver
l'entrée de journal correspondante. Le réflexe devient alors de rendre les messages plus bavards —
c'est-à-dire exactement ce qu'il faut éviter.

L'identifiant est opaque : il n'a aucune valeur pour un attaquant, et c'est lui qui **permet** de
garder les messages muets.

---

## Ce qui ne franchit jamais la frontière HTTP

| Cas | Ce que reçoit le client | Ce que reçoit le journal |
|---|---|---|
| Erreur inattendue (500) | « Une erreur interne est survenue. » | L'exception complète, avec sa trace |
| Dépendance injoignable (503) | « Le service est temporairement indisponible… » | Le **nom de la dépendance** et la cause technique |

Le nom de la dépendance est une information d'architecture : le divulguer renseignerait un attaquant
sur la composition du système.

---

## Graduation des journaux

| Catégorie | Niveau | Trace |
|---|---|---|
| 4xx — faute du client | `Warning` | non — il ne révèle aucun défaut |
| 503 — dépendance externe | `Error` | oui, avec la dépendance nommée |
| 500 — inattendu | `Error` | oui, complète |
| Annulation client | `Information` | non |

Avant NTR-135, tout ce qui n'était pas traduit partait en `LogError` : une saisie invalide et une
base morte déclenchaient la même alerte.

---

## La règle de couche

Le middleware appartient à la couche **API**. Lui faire attraper `NpgsqlException` ou
`RedisConnectionException` l'obligerait à référencer des packages confinés à Infrastructure.

C'est **Infrastructure qui traduit** :

```
DatabaseExceptionInterceptor    ──┐
KeycloakAdminService            ──┼── lèvent ServiceUnavailableException
                                  │   (ou ConflictException sur violation d'unicité)
                                  ▼
                     ExceptionMiddleware → 503 / 409
                     (ne connaît ni Npgsql ni Redis)
```

| Point de traduction | Ce qu'il attrape | Ce qu'il lève |
|---|---|---|
| `Persistence/Interceptors/DatabaseExceptionInterceptor` | `PostgresException` code `23505` | `ConflictException` |
| | `NpgsqlException`, `SocketException`, `TimeoutException` | `ServiceUnavailableException("PostgreSQL")` |
| `ExternalServices/Keycloak/KeycloakAdminService` | `HttpRequestException` **sans statut**, `TaskCanceledException` | `ServiceUnavailableException("Keycloak")` |

Deux discriminations méritent l'attention :

**`HttpRequestException` avec un statut n'est pas une indisponibilité** — elle vient d'une réponse
HTTP d'erreur de l'API Admin. La confondre masquerait un défaut de configuration en panne passagère.

**EF Core enveloppe les erreurs Npgsql** dans `DbUpdateException` lors d'un `SaveChanges`. La
discrimination porte donc sur l'exception **interne**, jamais sur le type externe.

### Le cas Redis — pas de 503

`RedisFoodCacheService` attrape ses propres `RedisException`, journalise en `Warning` et **se replie
sur PostgreSQL**. La recherche fonctionne sans cache, plus lentement.

Un 503 y serait disproportionné : le service rend le résultat attendu. Mais l'incident est
**journalisé** — sans quoi la panne deviendrait invisible et le surcoût de latence inexplicable.

---

## État de confiance

| Marque | Élément |
|---|---|
| ✅ | Les sept traductions — 16 tests unitaires dans `ExceptionMiddlewareTest` |
| ✅ | `traceId`, `title` et `type` présents dans toute réponse d'erreur |
| ✅ | Aucune fuite de message interne en 500, ni de nom de dépendance en 503 |
| ✅ | Discrimination des échecs PostgreSQL — 5 tests sur `DatabaseExceptionInterceptor.Translate` |
| ✅ | Keycloak injoignable et délai dépassé — 2 tests |
| ✅ | Bout en bout via le pipeline réel — `MiddlewaresIntegrationTest` |
| ⚠️ | Le branchement de l'intercepteur sur EF Core est configuré, **jamais éprouvé contre une vraie base** — niveau 3 (NTR-28) |
| ❌ | Comportement réel lors d'une coupure PostgreSQL ou Keycloak en cours d'exécution |

---

## Voir aussi

- [Pipeline HTTP](pipeline-http.md) — position du middleware et ordre de traversée
- [Observabilité](observabilite.md) — collecte des journaux qu'il émet
- [Keycloak Admin API](../../briques/keycloak-admin.md) — la traduction côté Keycloak
