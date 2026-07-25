# Workflow — Cache des recherches d'aliments

**Ajouté le :** 2026-07-23
**Feature associée :** `features/interne/recherche-aliments-cache.md`
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
| `IFoodCacheService` | Contrat côté Application : `GetAsync`, `SetAsync`, `InvalidateAsync`. Ne connaît pas Redis. |
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
| **1. Clé** | `food:search:` + mot-clé **normalisé** (minuscules, espaces de bord retirés). « Poulet » et « poulet  » partagent donc la même entrée. |
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

---

## 5. Ce que le cache ne couvre pas encore

### ⚠️ La résilience en cours d'exécution — non traitée

`AbortOnConnectFail = false` protège **uniquement le démarrage**. Si Redis tombe pendant que
l'application tourne, chaque appel au cache lève une exception qui n'est interceptée nulle part :
elle traverse le service et le controller, atteint `ExceptionMiddleware`, et devient une **erreur 500**.

**C'est une inversion de priorité** : un cache est une optimisation ; sa disparition devrait coûter
de la performance, pas de la disponibilité — d'autant que PostgreSQL, qui détient les vraies
données, fonctionne parfaitement.

**Le correctif est déjà rédigé** : intercepter `RedisException` (et surtout pas `Exception`, qui
masquerait les vrais bugs de désérialisation), retourner `null` en lecture — valeur déjà interprétée
comme « pas de cache », donc **aucune modification de `FoodItemService` nécessaire** — ignorer
l'échec en écriture, et journaliser en avertissement pour que la dégradation ne soit pas silencieuse.

> **Statut : non implémenté, aucun ticket créé.**

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
| Comportement cache-first | ✅ vérifié manuellement — cache vide → 1 requête SQL, cache trouvé → 0 requête |
| `FoodItemService.SearchAsync` | ✅ couvert par les tests unitaires de la couche Application (mocks) |
| `RedisFoodCacheService` | ⚠️ pas de test automatisé — nécessite un Redis réel → **NTR-73** (niveau 3) |
| Invalidation après import | ⚠️ implémentée, **non testée** — couverture prévue par **NTR-73** |
| Résilience en cours d'exécution | ❌ non implémentée (voir §5) |

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
| Le besoin et le périmètre | `features/interne/recherche-aliments-cache.md` |
| La recherche vue par l'utilisateur | `features/utilisateur/aliments.md` |
| Le job qui met à jour le catalogue mis en cache | `annexes/workflow-import-aliments.md` |
| L'environnement Redis (docker-compose, ports) | `annexes/infrastructure-setup.md` |
