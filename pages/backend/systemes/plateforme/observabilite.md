# Observabilité — logs, métriques et traces

**Ajouté le :** 2026-07-29
**Type :** Interne
**Epic :** NTR-136

> Document de référence de l'epic Observabilité. Il porte l'état des lieux, le périmètre des cinq
> volets et les décisions — les tickets NTR-137 à NTR-141 y renvoient plutôt que de le dupliquer.
>
> ➜ Pour le traitement des erreurs et les niveaux de journalisation associés, voir NTR-135 et
> [Exception Filter](exception-filter.md). Cet epic décide **comment** la donnée circule, pas **quoi**
> journaliser.

---

## 1. Objectif

**Pouvoir diagnostiquer un incident de production sans se connecter au serveur.**

C'est la phrase qui décide si un ticket appartient à cet epic ou non.

## 2. État des lieux — un embryon non pensé comme tel

Plusieurs briques produisent déjà de la donnée d'observabilité, sans qu'elle soit exploitée.

| Élément | Ce qu'il produit | Ce qui manque |
|---|---|---|
| `RequestLoggingMiddleware` (NTR-121) | méthode, route, statut, **durée** par requête | c'est une métrique, traitée comme du texte |
| `ExceptionMiddleware` | journalisation des erreurs | aucune corrélation entre l'erreur vue par l'utilisateur et la trace serveur |
| `traceId` (NTR-135) | identifiant par requête dans les `ProblemDetails` | rien pour l'exploiter |
| `JobMonitoringService` | dernière exécution, prochaine, état des jobs | lisible seulement via `GET /admin/system/health` |
| Sortie des journaux | console | **en K3s, tout disparaît au redémarrage d'un pod** |
| Requêtes SQL | rien | une requête lente est indétectable |
| Métriques | rien | — |
| Traces | rien | — |

> **Le point le plus dur est la dernière ligne du haut.** Sans collecteur, un incident passé est
> irrécupérable : le pod redémarre, les journaux sont perdus. Toute la valeur de l'epic tient à
> cette bascule.

## 3. Les cinq volets

### Volet 1 — Journaux structurés et collecte (NTR-137)

Passer d'une sortie console non structurée à des journaux exploitables et conservés.

| Sujet | Détail |
|---|---|
| Format | Texte lisible en développement, **JSON en production** — un journal non structuré n'est pas requêtable |
| Enrichissement | `traceId`, identifiant utilisateur, environnement, version applicative, sur **chaque** entrée |
| Niveaux par catégorie | EF Core en `Information` journalise chaque requête SQL : verbeux et coûteux. À régler par catégorie, pas globalement. |
| Acheminement | Dépend du backend retenu — voir §5 |
| Données personnelles | **Ne jamais journaliser** le corps des requêtes ni les jetons. Le RGPD s'applique aussi aux journaux. |

### Volet 2 — Métriques applicatives (NTR-138)

| Indicateur | Source | Pourquoi |
|---|---|---|
| Durée et taux d'erreur par endpoint | `RequestLoggingMiddleware` mesure déjà la durée | détecter une dégradation avant les utilisateurs |
| Taux de succès du cache Redis | `RedisFoodCacheService` | un cache qui ne sert plus est un cache inutile — et coûteux |
| Durée et issue des jobs Hangfire | tables `hangfire` | un job qui échoue chaque nuit doit se voir |
| Saturation du pool PostgreSQL | Npgsql | cause classique de latence en production |

### Volet 3 — Traces distribuées (NTR-139)

Une requête traverse aujourd'hui **API → PostgreSQL → Redis → Keycloak** sans qu'on puisse dire où
le temps est passé.

```
GET /api/v1/food-items?search=poulet        durée totale : 850 ms
   ├── UserResolutionMiddleware → PostgreSQL      ? ms
   ├── FoodCacheService → Redis                   ? ms
   └── FoodItemRepository → PostgreSQL            ? ms
```

Sans trace, la seule information disponible est « 850 ms ». Avec, on sait lequel des trois est en
cause.

Le `traceId` livré par NTR-135 dans les `ProblemDetails` devient ici le **point de jonction** : un
utilisateur signale une erreur, l'identifiant mène directement à la trace complète.

### Volet 4 — Socle OpenTelemetry (NTR-140)

**Pourquoi OpenTelemetry plutôt qu'une bibliothèque par signal :**

- un standard unique pour les trois signaux, au lieu de trois outils à accorder ;
- instrumentation **automatique** d'ASP.NET Core, `HttpClient`, Npgsql et StackExchange.Redis — l'essentiel des traces sans écrire de code ;
- **indépendance du backend** : changer de destination ne touche que l'exportateur, jamais l'instrumentation.

Ce dernier point est décisif tant que la décision du §5 reste ouverte : le volet 4 peut être livré
**avant** que le backend soit choisi.

### Volet 5 — Observabilité de la base de données (NTR-141)

| Sujet | Détail |
|---|---|
| Requêtes lentes | seuil à définir, journalisation dédiée |
| Connexions | actives, en attente, rejetées |
| Croissance des tables `hangfire` | `job`, `state` et `counter` **grossissent sans purge configurée** — à surveiller avant que ce soit un incident |

## 4. Frontière avec NTR-135

Les deux sujets se touchent sur les niveaux de journalisation. La règle :

| | |
|---|---|
| **NTR-135** | **quoi** journaliser et à quel niveau — une règle de traitement des erreurs |
| **Cet epic** | **comment** la donnée est structurée, collectée, corrélée et exploitée |

NTR-135 est autonome : il ne dépend pas de cet epic et ne doit pas l'attendre.

## 5. Décision ouverte — le backend de collecte

**Non tranchée.** Elle conditionne le volet 1 ; les volets 2, 3 et 4 peuvent avancer sans elle.

| Option | Pour | Contre |
|---|---|---|
| **Grafana + Loki + Prometheus + Tempo** | tout-en-un, auto-hébergé, standard du marché, cohérent avec un VPS + K3s | quatre services de plus à exploiter et sauvegarder |
| **Seq** | très simple, excellent pour les journaux .NET, recherche confortable | orienté journaux — métriques et traces restent à traiter ailleurs ; licence au-delà d'un usage individuel |
| **SaaS** (Grafana Cloud, Axiom…) | rien à exploiter, palier gratuit souvent suffisant à ce stade | données applicatives hors de l'infrastructure — à évaluer au regard du RGPD |

**Critères pour trancher :** volume de journaux attendu, temps d'exploitation acceptable sur le VPS,
et sensibilité des données qui transiteraient par un tiers.

> Une fois la décision prise, l'inscrire dans le tableau des décisions d'architecture de
> `CLAUDE.md`, au même titre que docker-compose ou K3s.

## 6. Ce qui n'est pas couvert

| Sujet | Statut |
|---|---|
| Alerting (seuils, notifications) | Hors périmètre — vient après la collecte |
| Tableaux de bord | Hors périmètre — dépend du backend |
| Observabilité du front | Autre projet |
| Profilage continu | Non envisagé |

## 7. État de confiance

| Marque | Élément |
|---|---|
| ⚠️ | `RequestLoggingMiddleware` et `JobMonitoringService` produisent de la donnée exploitable — vérifié par tests, mais rien ne la collecte |
| ❌ | Journaux structurés, métriques, traces, instrumentation OpenTelemetry, supervision de la base |
| ❌ | Conservation des journaux après redémarrage d'un pod |

## 8. Où creuser

- [Pipeline HTTP](pipeline-http.md) — `RequestLoggingMiddleware`, ce qu'il mesure déjà
- [Exception Filter](exception-filter.md) — traitement des erreurs, et le `traceId` de NTR-135
- [Hangfire](../../briques/hangfire.md) — l'historique des jobs et les tables du schéma `hangfire`
- [Environnement local et production](../../briques/environnement-local.md) — la cible K3s
