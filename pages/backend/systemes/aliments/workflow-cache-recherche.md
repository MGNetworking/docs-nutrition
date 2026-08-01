# Workflow — Cache des recherches d'aliments

**Ajouté le :** 2026-07-23
**Feature associée :** [Cache des recherches d'aliments](cache-recherche.md)
**Ticket :** NTR-54

> **Ce document explique comment le cache fonctionne, de bout en bout** — le chemin d'une
> recherche, les décisions techniques et leurs raisons, et l'état de confiance réel.

---

## 1. Vue d'ensemble

La recherche d'aliments suit une stratégie **cache-first** : Redis est toujours interrogé en
premier, PostgreSQL n'est sollicité qu'en cas d'absence.

```
        Utilisateur : « poulet »
                 │
                 ▼
        FoodItemService.SearchAsync
                 │
                 ▼
        ┌── Redis : food:search:poulet ──┐
        │                                 │
   TROUVÉ                            ABSENT
        │                                 │
        ▼                                 ▼
   retour immédiat            PostgreSQL (SearchByKeywordAsync)
   0 requête SQL                          │
                                          ▼
                              écrit dans Redis (24 h)
                                          │
                                          ▼
                                      retour
```

**Le catalogue est partagé par tous les utilisateurs** — un aliment ne dépend d'aucun compte.
C'est ce qui rend le cache mutualisable : la recherche « poulet » d'un utilisateur profite à
tous les suivants.

---

## 2. Qui fait quoi — les classes

```
Application/
├── Interfaces/ExternalServices/IFoodCacheService.cs   ← le contrat
└── Services/FoodItemService.cs                        ← l'orchestrateur (décide cache ou base)

Infrastructure/
└── Caching/RedisFoodCacheService.cs                   ← l'implémentation Redis
```

| Classe | Responsabilité |
|---|---|
| `IFoodCacheService` | Contrat côté Application : `GetAsync`, `SetAsync`, `InvalidateAsync`, `InvalidateAllSearchesAsync`. Ne connaît pas Redis. |
| `RedisFoodCacheService` | Traduit ce contrat en commandes Redis : construction de la clé, sérialisation JSON, durée de vie. |
| `FoodItemService` | Orchestre : interroge le cache, décide de basculer sur la base, réalimente le cache. **C'est lui qui porte la stratégie**, pas le cache. |

> La couche Application ignore totalement que le cache est Redis — elle ne voit que
> `IFoodCacheService`. C'est ce qui permettrait d'en changer sans toucher au service.

---

## 3. Le parcours d'une recherche

### Le code qui décide (`FoodItemService.SearchAsync`)

```csharp
var cachedItems = await _foodCache.GetAsync(keyword);
if (cachedItems is not null)
    return cachedItems.Take(limit).ToList();          // cache trouvé → 0 requête SQL

var foodItems = await _foodItemRepository.SearchByKeywordAsync(keyword, 20);
var foodItemsResponses = foodItems.Select(FoodItemSearchResponse.From).ToList();

await _foodCache.SetAsync(keyword, foodItemsResponses); // on réalimente le cache
return foodItemsResponses.Take(limit).ToList();
```

### Détail des étapes

| Étape | Ce qui se passe |
|---|---|
| **1. Clé** | `food:search:v1:` + mot-clé **normalisé** (minuscules, espaces de bord retirés). « Poulet » et « poulet  » partagent donc la même entrée. Le `v1` est la version de la forme sérialisée — voir §4. |
| **2. Lecture** | `StringGetAsync` — une valeur JSON, ou rien. |
| **3a. Trouvé** | Désérialisation, troncature à `limit`, retour. **Aucune requête SQL.** |
| **3b. Absent** | `SearchByKeywordAsync` (recherche insensible à la casse, triée par nom) → conversion en DTO. |
| **4. Écriture** | `StringSetAsync` avec la durée de vie configurée (24 h par défaut). |
| **5. Retour** | Troncature à `limit`. |

### Un point de conception à connaître

La base est toujours interrogée avec **une limite fixe de 20**, et c'est ce jeu de 20 qui est mis
en cache — la troncature à `limit` n'intervient **qu'après**.

Conséquence voulue : **une seule entrée de cache par mot-clé**, quelle que soit la limite demandée
par l'appelant. Sans cela, `poulet/limit=5` et `poulet/limit=10` créeraient deux entrées distinctes
pour la même recherche.

Conséquence à connaître : une demande avec `limit` supérieur à 20 ne renverra jamais plus de
20 résultats.

---

## 4. Décisions et leurs raisons

### `IConnectionMultiplexer` plutôt que `IDistributedCache`

`IDistributedCache` est l'abstraction .NET standard : plus simple, plus courte, et portable vers
un autre type de cache. **Elle aurait été le meilleur choix pour le besoin actuel.**

Ce qui a tranché, c'est la capacité à **supprimer les clés par motif** (`food:search:*`) après un
import qui rend tout le cache potentiellement périmé. Cette capacité est **effectivement utilisée**
depuis NTR-55 (`InvalidateAllSearchesAsync`, appelée en fin d'import) :

```csharp
// Possible uniquement avec IConnectionMultiplexer
foreach (var key in server.Keys(pattern: "food:search:*"))
    await db.KeyDeleteAsync(key);
```

> Le motif s'arrête volontairement à `food:search:` sans la version : une entrée écrite par une
> version de schéma antérieure doit être supprimée elle aussi.

`IDistributedCache` n'expose que `RemoveAsync(string key)` : il faudrait **nommer** chaque clé. Or
les clés naissent des saisies des utilisateurs et ne sont recensées nulle part — il faudrait tenir
soi-même un index, c'est-à-dire réimplémenter ce que Redis sait déjà faire.

**Le coût assumé** : on perd la portabilité vers un autre cache. Acceptable car Redis est une
décision actée (docker-compose, tests de niveau 3, manifests K3s).

### `AbortOnConnectFail = false`

Par défaut, si Redis ne répond pas **à l'instant du démarrage**, `Connect` lève une exception. Comme
le multiplexeur est un singleton validé au démarrage du conteneur DI, **l'API entière refuserait de
démarrer** — y compris la trentaine de routes qui n'utilisent jamais le cache.

Avec `AbortOnConnectFail = false`, la connexion est retentée en arrière-plan : l'API démarre, et le
cache devient opérationnel dès que Redis répond.

> Le scénario concret : `docker compose up` démarre les trois services en parallèle, et Redis met
> une à deux secondes à accepter les connexions. Sans ce réglage, l'API mourrait dans cette fenêtre.

### Durée de vie de 24 heures

Alignée sur la fréquence du job d'import quotidien : les entrées expirent d'elles-mêmes, ce qui
évite toute purge périodique. Configurable via `Redis:SearchCacheTtlHours`.

### Le repli sur la base plutôt que l'erreur 500

`AbortOnConnectFail = false` ne protège que le **démarrage**. Une panne survenant *pendant*
l'exécution levait une exception qui traversait le service et le controller jusqu'à
`ExceptionMiddleware`, et devenait une **erreur 500** — alors que PostgreSQL, qui détient les
vraies données, fonctionnait parfaitement. Inversion de priorité : un cache est une optimisation,
sa disparition doit coûter de la performance, pas de la disponibilité.

`GetAsync` et `SetAsync` interceptent donc `RedisException` :

| Méthode | Comportement en panne |
|---|---|
| `GetAsync` | Retourne `null` — la valeur qui signifie déjà « pas de cache », donc **aucune modification de `FoodItemService`** |
| `SetAsync` | Ignore l'échec : le résultat a déjà été retourné à l'utilisateur |
| `InvalidateAllSearchesAsync` | Ignore l'échec : l'import qui vient de l'appeler ne doit pas échouer pour autant — voir ci-dessous |
| `InvalidateAsync` | **Non protégée** — invalidation d'un seul mot-clé, sans appelant aujourd'hui |

Deux points volontaires :

- **`RedisException`, jamais `Exception`.** Une panne d'infrastructure se contourne ; une erreur
  de désérialisation révèle un vrai défaut et doit remonter.
- **Journalisation en avertissement.** Une dégradation silencieuse ne se manifesterait que par une
  lenteur inexpliquée.

**L'invalidation a longtemps été bloquante — elle ne l'est plus.** L'exception remontait à Hangfire,
qui marquait le job en échec et le relançait. Chaque relance **retéléchargeait le dump et retraitait
plusieurs millions de lignes**, alors que les aliments étaient déjà en base et que seul le nettoyage
du cache manquait. Disproportionné par rapport au geste qui avait échoué.

L'échec est donc désormais journalisé en avertissement, et l'import se déclare réussi.

**Ce que ça coûte, assumé.** Les recherches mémorisées portent sur l'ancien catalogue jusqu'à
l'expiration de leurs entrées — 24 h par défaut — ou jusqu'au prochain import qui réussira son
nettoyage. Une panne de Redis relève de l'exploitation du système, pas de l'import : l'application
la traverse déjà sans dégrader le service, et le client Redis se reconnecte seul dès que l'instance
revient.

> **Ce qui manque encore.** Rien ne signale qu'une panne de cache a eu lieu, sinon un avertissement
> dans les journaux. La route de santé de l'administration n'expose l'état ni de Redis, ni de
> PostgreSQL, ni du serveur d'identité. Sujet à instruire du côté de l'observabilité.

**Ce qui n'a pas été retenu** : un disjoncteur (*circuit breaker*, type Polly). Sans lui, chaque
requête attend l'expiration du délai Redis avant de basculer sur la base. Cela ne vaut le coût
d'une dépendance supplémentaire que si des pannes durables se manifestent.

### Une version dans la clé, plutôt qu'une purge au déploiement

Les entrées stockent du JSON de `FoodItemSearchResponse`. Sans marqueur de version, un changement
de forme du DTO rendait les entrées déjà en cache indésérialisables — donc en erreur — **jusqu'au
terme de leur durée de vie**, soit 24 h.

La clé porte désormais `v1`. Changer la forme du DTO s'accompagne d'un passage à `v2` : les
anciennes entrées deviennent simplement inatteignables et expirent seules.

**L'option écartée** était un `FLUSHDB` au déploiement : gratuit en code, mais dépendant d'un geste
humain à ne pas oublier. L'option retenue déplace l'oubli possible vers un endroit visible — la
constante `SchemaVersion`, juste à côté du DTO concerné.

> Ce choix ne détecte pas l'oubli du bump : une `JsonException` reste alors possible, et c'est
> assumé — elle signale précisément le défaut plutôt que de le masquer.

---

## 5. Ce que le cache ne couvre pas encore

### ✅ La résilience en cours d'exécution — implémentée

Traitée par le repli décrit au §4. Il subsiste un coût de latence pendant une panne, faute de
disjoncteur : chaque requête attend l'expiration du délai Redis avant de basculer sur la base.

### ✅ Invalidation après l'import — implémentée (NTR-55)

Sans elle, une entrée créée juste avant l'import de 03h00 aurait continué d'être servie **près de
24 heures avec des données antérieures à l'import** — masquant notamment les nouveaux produits
ajoutés chaque jour par Open Food Facts.

`OffImportJob` appelle donc `InvalidateAllSearchesAsync()` en fin d'exécution, **uniquement si au
moins un produit a été importé** (un catalogue inchangé ne justifie pas de vider le cache).

Le cache n'est pas rempli par l'import : il est **vidé**, puis se reconstitue naturellement à la
première recherche suivante, sur des données à jour.

---

## 6. État de confiance

| Élément | Niveau de vérification |
|---|---|
| Comportement cache-first | ⚠️ vérifié manuellement — cache vide → 1 requête SQL, cache trouvé → 0 requête |
| `FoodItemService.SearchAsync` | ✅ tests unitaires de la couche Application (mocks) |
| `RedisFoodCacheService` — clé versionnée, normalisation, durée de vie | ✅ 12 tests unitaires Infrastructure (mocks Moq) |
| Repli quand Redis est indisponible | ✅ tests unitaires — `GetAsync` retourne `null`, `SetAsync` n'échoue pas, avertissement journalisé dans les deux cas |
| Invalidation après import | ✅ testée unitairement (motif toutes versions, suppression de chaque clé) |
| Échec de l'invalidation qui ne doit pas faire échouer l'import | ✅ test unitaire — avertissement journalisé, aucune exception ; et cas de niveau 3 avec Redis réellement arrêté |
| Comportement contre un **Redis réel** (`SCAN`, sérialisation de bout en bout) | ⚠️ jamais exécuté — couverture prévue par **NTR-73** (niveau 3) |
| Topologie multi-endpoints ou avec réplicas | ❌ non vérifié — voir [Redis](../../briques/redis.md) |

---

## 7. Configuration

```json
"Redis": {
  "ConnectionString": "localhost:6336",
  "SearchCacheTtlHours": 24
}
```

| Clé | Rôle |
|---|---|
| `ConnectionString` | Adresse du serveur Redis — jamais en dur dans le code |
| `SearchCacheTtlHours` | Durée de vie des entrées (défaut 24 h si absente) |

---

## 8. Où creuser

| Sujet | Document |
|---|---|
| Le besoin et le périmètre | [Cache des recherches d'aliments](cache-recherche.md) |
| La recherche vue par l'utilisateur | [Aliments](index.md) |
| Le job qui met à jour le catalogue mis en cache | [Workflow — Mise à disposition des aliments](workflow-import.md) |
| Redis comme brique : client, configuration, débogage `redis-cli` | [Redis](../../briques/redis.md) |
| L'environnement de développement (docker-compose, ports) | [Environnement local et production](../../briques/environnement-local.md) |
