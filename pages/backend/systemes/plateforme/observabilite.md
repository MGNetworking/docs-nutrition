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
| Requêtes SQL (NTR-140) | chaque commande, avec sa durée, dans la trace | le seuil de lenteur et sa journalisation dédiée |
| Métriques (NTR-140, NTR-138) | durées et taux d'erreur HTTP, cache, jobs et pool de connexions | rien — il manque une destination |
| Traces (NTR-140) | l'arbre complet d'une requête, API comprise | rien à instrumenter — il manque une destination |

> **Le point le plus dur est la dernière ligne du haut.** Sans collecteur, un incident passé est
> irrécupérable : le pod redémarre, les journaux sont perdus. Toute la valeur de l'epic tient à
> cette bascule.
>
> Les trois dernières lignes ont changé avec NTR-140 : la donnée existe désormais, mais elle n'est
> envoyée nulle part tant que le §5 n'est pas tranché.

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

| Indicateur | Instrument | Pourquoi |
|---|---|---|
| Durée et taux d'erreur par endpoint | `http.server.request.duration`, publié par ASP.NET Core | détecter une dégradation avant les utilisateurs |
| Saturation du pool PostgreSQL | publié par Npgsql | cause classique de latence en production |
| Taux de succès du cache Redis | `nutrition.cache.lookups` | un cache qui ne sert plus est un cache inutile — et coûteux |
| Durée et issue des jobs Hangfire | `nutrition.job.duration` | un job qui échoue chaque nuit doit se voir |

**Les deux premiers n'ont demandé aucun code** : les bibliothèques les publient, il suffisait de les
écouter. La durée par endpoint est d'ailleurs mesurée deux fois — `RequestLoggingMiddleware` la
journalise pour l'œil humain, ASP.NET Core la compte pour l'outil. Les deux subsistent : elles ne
répondent pas à la même question.

**Les deux derniers naissent d'une décision prise dans le code**, et n'existaient donc nulle part.
Ils vivent en couche Infrastructure, là où l'événement se produit : un taux de succès de cache n'est
pas une préoccupation d'API, et le faire transiter par une interface d'Application aurait ajouté une
abstraction pour un usage unique.

| Choix | Ce qu'il évite |
|---|---|
| Une seule série `nutrition.cache.lookups`, étiquetée `hit`, `miss` ou `failure` | trois compteurs à tenir accordés ; le taux se calcule à la lecture |
| **`failure` distingué de `miss`** | un cache injoignable se présenterait sinon comme un cache qui ne sert jamais — deux pannes qui n'appellent pas la même intervention |
| Un **filtre serveur Hangfire**, plutôt qu'une mesure écrite dans chaque job | l'import OFF, la purge RGPD et tout job futur sont couverts sans y toucher |
| La durée des jobs en **secondes** | un seuil faux d'un facteur mille, sans que rien ne le signale |

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

**Ce qui est en place.** `AddObservability`, appelé depuis `Program.cs` après `AddInfrastructure`,
enregistre le fournisseur, l'identité du service et les instrumentations. Rien n'est mesuré à la
main : ASP.NET Core, `HttpClient`, Npgsql et StackExchange.Redis émettaient déjà ces événements,
personne ne les écoutait.

| Réglage | Rôle |
|---|---|
| `OpenTelemetry:ServiceName` | Nom porté par chaque mesure — sans lui, un collecteur recevant plusieurs applications ne sait pas laquelle a émis |
| `OpenTelemetry:OtlpEndpoint` | Adresse du collecteur. **Vide** : les mesures sont produites puis abandonnées, sans erreur |
| `OpenTelemetry:ConsoleExporter` | Sortie console, activée en développement uniquement |

L'attribut `deployment.environment` vient de l'hôte, non d'une valeur écrite en dur : c'est lui qui
distinguera une mesure de production d'une mesure de recette une fois collectées côte à côte.

Deux choix méritent d'être connus. Les **sondes de santé sont exclues des traces** — le kubelet les
interroge en continu et noierait tout le reste sous leur volume. Les **journaux n'ont pas de sortie
console** : le logger d'ASP.NET Core écrit déjà là, les doubler rendrait la console illisible ; leur
format et leur enrichissement relèvent de NTR-137.

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
| ✅ | Le socle OpenTelemetry est enregistré et porte l'identité du service — quatre cas de niveau 2 (NTR-140) |
| ✅ | Le compteur du cache distingue succès, défaut et panne, et la durée des jobs est enregistrée en secondes avec son issue — neuf cas de niveau 1 (NTR-138) |
| ⚠️ | Le **filtre Hangfire** n'est éprouvé qu'indirectement : aucun test ne fait exécuter un vrai job pour vérifier qu'il mesure |
| ⚠️ | Les instrumentations HTTP, SQL et Redis sont branchées, mais **aucune trace ni métrique n'a été constatée de bout en bout** : rien ne les reçoit encore |
| ⚠️ | `RequestLoggingMiddleware` et `JobMonitoringService` produisent de la donnée exploitable — vérifié par tests, mais rien ne la collecte |
| ❌ | Journaux structurés, supervision de la base |
| ❌ | Conservation des journaux après redémarrage d'un pod |

## 8. Où creuser

- [Pipeline HTTP](pipeline-http.md) — `RequestLoggingMiddleware`, ce qu'il mesure déjà
- [Exception Filter](exception-filter.md) — traitement des erreurs, et le `traceId` de NTR-135
- [Hangfire](../../briques/hangfire.md) — l'historique des jobs et les tables du schéma `hangfire`
- [Environnement local et production](../../briques/environnement-local.md) — la cible K3s
