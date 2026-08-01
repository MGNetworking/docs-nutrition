# Redis

**Ajouté le :** 2026-07-26

> **Portée de ce document : Redis en tant que brique d'infrastructure, et elle seule.**
> Redis est un service **partagé** : il ne « sert » aucune fonctionnalité en particulier. Il n'a
> aujourd'hui qu'un seul usage — le cache des recherches d'aliments — mais rien dans sa
> configuration ne lui est propre : un second usage viendrait s'y ajouter sans rien modifier ici.
>
> ➜ Pour comprendre **comment le cache des recherches fonctionne de bout en bout** (le parcours
> d'une recherche, l'invalidation après import, les décisions), lire d'abord
> [Workflow — Cache des recherches d'aliments](../systemes/aliments/workflow-cache-recherche.md). Ce document-ci ne sert qu'à approfondir la brique.
>
> ➜ Pour **démarrer l'environnement local** (ports, docker-compose, comptes), voir
> [Environnement local et production](environnement-local.md).

---

## Pourquoi Redis

Le besoin est de **mémoriser des résultats de recherche entre les requêtes**, avec expiration
automatique.

**`IMemoryCache` a été écarté.** Le cache serait vécu dans le process de l'API, avec trois
conséquences rédhibitoires :

| Limite de `IMemoryCache` | Conséquence |
|---|---|
| Un cache par instance | Deux pods K3s ⇒ deux caches distincts, taux de succès divisé |
| Perdu à chaque redémarrage | Chaque déploiement repart d'un cache froid |
| Pas d'accès depuis l'extérieur du process | Le job d'import ne pourrait pas invalider le cache d'un autre pod |

Redis règle les trois : un store **externe et partagé**, qui survit au redémarrage de l'API,
avec une expiration (`TTL`) native et une sélection de clés par motif.

**Le coût assumé** : un service de plus à déployer et à surveiller, et un appel réseau là où
`IMemoryCache` n'avait qu'un accès mémoire.

---

## Comment le client fonctionne — le modèle mental

Le projet parle à Redis via **StackExchange.Redis**, et plus précisément via
`IConnectionMultiplexer` plutôt que l'abstraction .NET `IDistributedCache`.

> Le *pourquoi* de ce choix — et l'option écartée en détail — est documenté au §4 du
> [Workflow — Cache des recherches d'aliments](../systemes/aliments/workflow-cache-recherche.md). Ce document n'en décrit que les conséquences pratiques.

### Le multiplexeur n'est pas une connexion

`IConnectionMultiplexer` ne représente pas *une* connexion mais **le client complet**, qui
multiplexe toutes les commandes de l'application sur un petit nombre de sockets. Il est coûteux à
créer, thread-safe, et prévu pour vivre aussi longtemps que l'application.

D'où les durées de vie enregistrées dans `Infrastructure/DependencyInjection.cs` :

| Composant | Durée de vie | Raison |
|---|---|---|
| `IConnectionMultiplexer` | **Singleton** | Coûteux à créer, thread-safe — une seule instance pour tout le process |
| `RedisFoodCacheService` | **Scoped** | Simple consommateur du multiplexeur, aligné sur les autres services de la couche |

> **Ne jamais créer un `ConnectionMultiplexer` à la volée** dans un service ou une méthode :
> c'est l'anti-pattern classique de StackExchange.Redis (épuisement des sockets).

### Deux portes d'entrée, à ne pas confondre

```csharp
_redis.GetDatabase()          // les commandes de données : GET, SET, DEL…
_redis.GetServer(endpoint)    // les commandes d'administration : KEYS/SCAN, INFO, FLUSHDB…
```

`GetDatabase()` sans argument cible la **base 0** — le projet n'en utilise pas d'autre.

`GetServer()` est nécessaire parce que le parcours de clés par motif est une commande *serveur*,
pas une commande *données*. C'est précisément la capacité qui a justifié le choix
d'`IConnectionMultiplexer`, et elle est utilisée par `InvalidateAllSearchesAsync`.

### Le démarrage est tolérant

```csharp
options.AbortOnConnectFail = false;
```

Sans ce réglage, une instance Redis injoignable **à l'instant du démarrage** empêcherait l'API
entière de démarrer — le multiplexeur étant un singleton résolu au démarrage du conteneur DI.
Avec, `Connect` retourne immédiatement et la connexion est retentée en arrière-plan.

**Ce réglage ne concerne que le démarrage.** Une panne survenant en cours d'exécution est traitée
séparément, par le repli de `GetAsync` / `SetAsync` sur la base — voir « Points de vigilance ».

---

## Configuration

La clé racine est `Redis`, et **elle n'est pas dans `ConnectionStrings`** — le code lit
`configuration["Redis:ConnectionString"]`.

| Clé | Rôle | Défaut si absente |
|---|---|---|
| `Redis:ConnectionString` | Adresse du serveur, au format StackExchange.Redis (`hôte:port`) | aucun — `null` fait échouer le démarrage |
| `Redis:SearchCacheTtlHours` | Durée de vie des entrées de cache, en heures | `24` (constante `DefaultTtlHours`) |

### Valeur par environnement

| Environnement | Fichier / source | Valeur |
|---|---|---|
| Base commune | `appsettings.json` | `""` + `SearchCacheTtlHours: 24` |
| Dev local (`dotnet run`) | `appsettings.Development.json` | `localhost:6336` |
| Dev conteneurisé (profil `full`) | `appsettings.Docker.json` | `redis:6379` |
| Production K3s | ConfigMap, variable d'environnement | `Redis__ConnectionString` |

Deux points qui surprennent à la première lecture :

- **Seul `appsettings.json` porte `SearchCacheTtlHours`.** Les fichiers d'environnement ne
  redéfinissent que la chaîne de connexion ; le TTL est hérité de la base commune.
- **Le port diffère selon d'où l'on appelle.** `6336` est le port publié côté hôte par
  docker-compose ; à l'intérieur du réseau Docker, c'est le port natif `6379` sur l'hôte `redis`.
  En K3s, le double soulignement `__` remplace le `:` de la clé de configuration.

### Le conteneur (dev et CI)

```yaml
redis:
  image: redis:7
  container_name: nutrition-redis
  ports:
    - "6336:6379"
  volumes:
    - redis-data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    timeout: 3s
    retries: 10
```

L'API du profil `full` déclare `depends_on: redis: condition: service_healthy` — elle ne démarre
donc qu'une fois le `PING` satisfait.

**La version `redis:7` est figée** et doit rester alignée avec les manifests K3s : c'est le seul
alignement exigé entre les environnements.

> Le volume `redis-data` conserve les sauvegardes sur disque écrites par la configuration par
> défaut de l'image. Ce n'est **pas** une garantie de durabilité, et le projet n'en dépend pas :
> un cache perdu se reconstitue tout seul à la recherche suivante.

---

## Le contenu du keyspace

Aujourd'hui, toutes les clés écrites par l'application partagent le même préfixe :

| Élément | Valeur |
|---|---|
| Motif de clé | `food:search:v1:<mot-clé normalisé>` |
| Normalisation | minuscules (`ToLowerInvariant`) + espaces de bord retirés (`Trim`) |
| Version de schéma | `v1` — constante `SchemaVersion`, à incrémenter si `FoodItemSearchResponse` change de forme |
| Type Redis | chaîne simple (`StringSet` / `StringGet`) |
| Valeur | JSON d'une `List<FoodItemSearchResponse>` |
| Expiration | absolue, posée **à l'écriture** — jamais prolongée par une lecture |

Le préfixe joue un double rôle : il isole l'usage « recherche d'aliments » des futurs usages de
Redis, **et** il sert de motif d'invalidation globale — `food:search:*`, **sans la version**, pour
que les entrées d'un schéma antérieur soient effacées elles aussi.

> **Le JSON stocké est en PascalCase** (`System.Text.Json` appelé sans options), alors que la
> réponse HTTP de l'API est en camelCase (défaut ASP.NET Core). Ce n'est pas une incohérence :
> les deux sérialisations sont indépendantes. Mais il ne faut pas s'en étonner en lisant une
> valeur avec `redis-cli`.

---

## Observer et déboguer

Toutes les commandes ci-dessous passent par le conteneur de développement.

**Ouvrir une session :**

```bash
docker exec -it nutrition-redis redis-cli
```

**Lister les recherches actuellement en cache :**

```bash
docker exec -it nutrition-redis redis-cli --scan --pattern "food:search:*"
```

**Vérifier le temps de vie restant d'une entrée** (en secondes ; `-2` = clé absente, `-1` = sans
expiration) :

```bash
docker exec -it nutrition-redis redis-cli TTL "food:search:v1:poulet"
```

**Lire la valeur mise en cache :**

```bash
docker exec -it nutrition-redis redis-cli GET "food:search:v1:poulet"
```

**Forcer un cache miss sur un mot-clé, pour rejouer le chemin PostgreSQL :**

```bash
docker exec -it nutrition-redis redis-cli DEL "food:search:v1:poulet"
```

**Repartir d'un cache entièrement vide :**

```bash
docker exec -it nutrition-redis redis-cli FLUSHDB
```

### Vérifier qu'un cache hit se produit vraiment

La seule preuve fiable est **l'absence de requête SQL** au second appel : le corps de la réponse
HTTP est identique dans les deux cas. La marche à suivre : vider la clé (`DEL`), activer la
journalisation SQL d'EF Core, appeler la recherche deux fois de suite, et constater que le
`SELECT` n'apparaît qu'au premier appel.

Le mot-clé doit être écrit **tel qu'il est normalisé** : `« Poulet »` et `« poulet »` partagent
l'entrée `food:search:poulet`.

---

## Points de vigilance

### ⚠️ Une panne prolongée coûte de la latence

`GetAsync` et `SetAsync` interceptent `RedisException` : une panne fait retomber la recherche sur
PostgreSQL au lieu de produire une erreur 500 (le détail est au §4 du
[Workflow — Cache des recherches d'aliments](../systemes/aliments/workflow-cache-recherche.md)). Mais **chaque requête tente d'abord de joindre Redis** et
attend l'expiration du délai avant de basculer.

Aucun disjoncteur n'est en place : c'est un choix, réversible si des pannes durables se
manifestent. Les délais se règlent dans la chaîne de connexion
(`connectTimeout`, `syncTimeout`) sans toucher au code.

**L'invalidation globale est protégée elle aussi.** Un échec de `InvalidateAllSearchesAsync` est
journalisé en avertissement et l'import se déclare réussi. Il faisait auparavant échouer le job, ce
qui déclenchait une relance complète — retéléchargement du dump et retraitement de plusieurs
millions de lignes — pour un nettoyage de cache raté, alors que les aliments étaient déjà en base.

Le prix assumé : les recherches mémorisées restent sur l'ancien catalogue jusqu'à l'expiration de
leurs entrées, ou jusqu'au prochain import qui réussira son nettoyage.

### ⚠️ La version de schéma doit être incrémentée à la main

Les entrées stockent du JSON de `FoodItemSearchResponse` et la clé porte une version (`v1`).
**Tout changement de forme du DTO impose de passer `SchemaVersion` à `v2`** — sans quoi les
entrées déjà en cache deviennent indésérialisables et `JsonSerializer.Deserialize` lève, pendant
toute leur durée de vie restante.

Rien ne détecte l'oubli. C'est assumé : la `JsonException` n'est **pas** interceptée, précisément
pour que le défaut se signale au lieu d'être masqué — à la différence d'une `RedisException`, qui
n'est qu'une panne d'infrastructure.

> En dépannage immédiat, un `FLUSHDB` fait disparaître le symptôme ; le bump de version reste le
> geste correct.

### ⚠️ `server.Keys()` parcourt tous les endpoints

`InvalidateAllSearchesAsync` itère sur `GetEndPoints()` et supprime les clés du motif sur chacun.
C'est correct sur l'instance unique actuelle. Deux réserves si la topologie évolue :

- avec des réplicas, les endpoints renverraient les mêmes clés plusieurs fois, et les suppressions
  doivent viser le maître ;
- `server.Keys()` s'appuie sur `SCAN` (Redis ≥ 2.8), donc sans blocage du serveur — mais le
  parcours reste proportionnel à la taille du keyspace.

---

## Voir aussi

| Sujet | Document |
|---|---|
| Le fonctionnement du cache de bout en bout | [Workflow — Cache des recherches d'aliments](../systemes/aliments/workflow-cache-recherche.md) |
| Le besoin et le périmètre du cache | [Cache des recherches d'aliments](../systemes/aliments/cache-recherche.md) |
| Le job qui invalide le cache après import | [Workflow — Mise à disposition des aliments](../systemes/aliments/workflow-import.md) |
| Ports, docker-compose, manifests K3s | [Environnement local et production](environnement-local.md) |
