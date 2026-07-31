# Niveaux de tests — définitions et périmètres

**Type :** Interne
**Référence spec :** [Stratégie de Tests du Projet](../design/design-tests.md)](../design/design-tests.md)

> **Portée de ce document : ce qu'est chaque niveau de test, et où s'arrête son périmètre.**
> Il ne recense aucun test précis — pour la liste des tests à écrire et leur avancement, voir
> [Recensement des tests](recensement-des-tests.md)](recensement-des-tests.md).

---

## Le principe fondateur

Le projet distingue **quatre niveaux de tests**. Chacun répond à **une question différente** et
couvre **un risque différent**.

> **Règle de non-duplication** — un test appartient au niveau qui couvre *son* risque propre. Si
> un test échoue et que la cause serait déjà révélée par un niveau inférieur, il est en double.

Le test pratique pour classer un test : **« si ce test échoue, qu'est-ce que ça m'apprend ? »**

| Niveau | Question à laquelle il répond | Risque couvert |
|---|---|---|
| **1 — Unitaires** | Mon code fonctionne-t-il de manière isolée ? | Ma logique est fausse |
| **2 — Intégration interne** | Ma pipeline ASP.NET fonctionne-t-elle ? | Ma tuyauterie HTTP est mal câblée |
| **3 — Intégration externe** | Mon application communique-t-elle avec ses dépendances réelles ? | Ma requête SQL, ma connexion Redis ou ma chaîne JWT ne fonctionnent pas |
| **4 — Smoke tests** | Mon système déployé fonctionne-t-il réellement ? | Mon déploiement, mes secrets ou mon réseau sont mal configurés |

**Exemple de lecture** — la recherche d'aliments traverse les quatre niveaux sans redondance :
le niveau 1 vérifie que le service interroge le cache *puis* la base ; le niveau 2 que la route
répond 200 avec le bon JSON ; le niveau 3 que la requête SQL et Redis fonctionnent réellement ;
le niveau 4 que l'endpoint répond en production avec un vrai jeton.

---

## Niveau 1 — Tests unitaires

> *Mon code fonctionne-t-il correctement de manière isolée ?*

**Ce qui est couvert** — une unité de code unique, avec **toutes ses dépendances simulées** :
classe métier du domaine, service applicatif, value object, validateur, extension, middleware
isolé, et controller (service simulé, contexte HTTP reconstruit à la main).

**Ce qui n'est jamais couvert ici** — Keycloak, JWT réel, PostgreSQL, Redis, Docker, Kubernetes,
réseau, configuration système. Aucune dépendance externe, aucun conteneur.

**Frontière avec le niveau 2** — le niveau 1 teste la *logique* d'une classe, jamais le trajet
d'une requête HTTP à travers l'application.

**Cas particulier des controllers** — testés sans pipeline ASP.NET : ni middleware, ni
authentification réelle. Le contexte HTTP est reconstruit manuellement (`DefaultHttpContext`,
claims posés à la main) afin de contourner volontairement les middlewares.

**Dans la couche Infrastructure** — ce niveau se limite au **code pur**, c'est-à-dire aux classes
qui ne parlent ni à une base, ni au réseau (par exemple la traduction des données Open Food
Facts). Repositories, cache, jobs et lecteurs de flux relèvent du **niveau 3**.

**Outil** : xUnit + Moq · **Cible** : ~400 tests · **Écrits au fil des tickets feature**

---

## Niveau 2 — Tests d'intégration interne

> *La pipeline ASP.NET Core fonctionne-t-elle correctement ?*

**Ce qui est couvert** — le trajet complet d'une requête *à l'intérieur* de l'application :
routing, authentification ASP.NET, middlewares personnalisés, controllers, sérialisation JSON,
gestion des erreurs (`ProblemDetails`).

**Ce qui n'est pas couvert ici** — pas de Keycloak réel, pas de PostgreSQL réel, pas de Docker.
Les dépendances externes sont remplacées par des simulations (mocks, fakes, providers InMemory).

**Frontière avec le niveau 3** — le niveau 2 valide que *ma* tuyauterie est correctement câblée ;
il ne dit rien de ma capacité à dialoguer avec un composant externe réel.

> ⚠️ Ce niveau ne concerne **pas** la couche Infrastructure : il teste la pipeline HTTP, il vit
> donc dans le projet de tests de la couche API.

**Outil** : `WebApplicationFactory<Program>` + helper JWT + `SeedAsync()`
**Cible** : 10 à 20 tests (scénarios représentatifs, pas exhaustifs) · **Jira** : NTR-29 → NTR-105 à NTR-111

---

## Niveau 3 — Tests d'intégration externe

> *Mon application communique-t-elle correctement avec ses dépendances réelles ?*

**Ce qui est couvert** — les interactions avec les vrais composants : requêtes SQL réellement
exécutées par EF Core, écritures et expirations réelles dans Redis, chaîne JWT complète émise par
un vrai Keycloak (issuer, audience, signature), exécution réelle des jobs planifiés.

**Ce qui n'est pas couvert ici** — le déploiement, l'ingress, les secrets, le réseau du cluster.

**Frontière avec le niveau 4** — le niveau 3 s'exécute sur un environnement **monté pour le test**
(local ou CI) ; le niveau 4 s'exécute sur un environnement **déjà déployé**, que le test ne
contrôle pas.

**Pourquoi docker-compose et non Testcontainers** — les trois services (PostgreSQL, Redis,
Keycloak) sont ceux du `docker-compose.yml` de développement, réutilisés en CI. Ce choix permet de
valider ce que des conteneurs isolés ne peuvent pas : **la configuration Docker, le réseau entre
composants et la chaîne JWT réelle**. Décision d'architecture actée le 2026-07-21.

**Isolation par exécution** — une base `nutrition_test_<horodatage>` est créée sur le conteneur
PostgreSQL de développement, migrée, puis supprimée en sortie ; le cache utilise un **index Redis
dédié**. Aucun second fichier compose : un seul environnement à connaître, du poste à la CI.

**Outil** : `WebApplicationFactory<Program>` + docker-compose · **Cible** : 23 tests · **Jira** : NTR-28

> L'estimation d'origine était de 5 à 10 tests. Elle a été révisée après les transferts de NTR-74
> (validation JWT) et NTR-135 (branchement de l'intercepteur), et l'ajout des cas de statut Hangfire.

---

## Niveau 4 — Smoke tests (environnement déployé)

> *Le système déployé fonctionne-t-il réellement ?*

**Ce qui est couvert** — l'application **déjà déployée**, atteinte de l'extérieur :
`Client → Ingress → Service → Pod API → Keycloak → PostgreSQL`. On vérifie que le déploiement, la
configuration, les secrets et le réseau sont corrects — **pas la logique métier**, déjà couverte
par les niveaux inférieurs.

**Quand** — après chaque déploiement, sur un environnement réel (staging ou production).

**Identité utilisée** — les scénarios authentifiés s'appuient sur un **compte d'exploitation** :
un client Keycloak à service account, accompagné de **sa ligne `User` en base**. Sans ce profil,
`UserResolutionMiddleware` renvoie 401 — indiscernable d'un rejet de jeton, ce qui priverait le
smoke test de tout pouvoir de diagnostic. Le `client_secret` vit dans un Secret Kubernetes, jamais
dans git. Provisionnement : NTR-125.

**Outil** : client HTTP · **Cible** : 2 à 5 tests · **Jira** : NTR-112

> ⚠️ **Deux échelles de « niveaux » coexistent dans le projet.** Les sous-tâches NTR-89/90/91
> découpent ce niveau 4 en **trois paliers de smoke tests** (l'API répond → les dépendances sont
> joignables → scénario end-to-end). Le « palier 3 » d'un smoke test n'a donc aucun rapport avec
> le « niveau 3 » ci-dessus.

---

## Infrastructure requise par niveau

| Niveau | Outil principal | Docker requis | Vitesse |
|---|---|---|---|
| 1 — Unitaires | xUnit + Moq | Non | Très rapide |
| 2 — Intégration interne | `WebApplicationFactory` | Non | Rapide |
| 3 — Intégration externe | `WebApplicationFactory` + docker-compose | Oui | Lent |
| 4 — Smoke tests | Client HTTP | Oui (environnement déployé) | Variable |

---

## Où et quand ils s'exécutent

| Transition | Workflow CI | Ce qui tourne |
|---|---|---|
| `feature/*` → `dev` | `ci-unit.yml` | Build + niveaux 1 et 2 — `--filter "Level!=3"` |
| `feature/*` → `dev` | `ci-integration.yml` | Pile docker-compose + niveau 3 — `--filter "Level=3"` |
| `dev` → `main` | `ci-release.yml` | Build + tests + couverture + rapport PR |
| `dev` → `prod` | `ci-deploy.yml` | Build Release + déploiement VPS |

> **Comment les niveaux se distinguent.** Le niveau 3 porte `[Trait("Level", "3")]` ; les deux
> filtres sont donc disjoints, aucun test n'est joué deux fois ni oublié. Le niveau 2 se reconnaît à
> son namespace `NutritionApi.Api.Tests.Integration`, convention antérieure au marqueur.

> **État au 2026-07-30** — niveaux 1 et 2 : 700 tests. Niveau 3 : 23 tests, exécutés par
> `ci-integration.yml`, qui appelle `./scripts/test-integration.sh` sans déclarer de service propre.
> Niveau 4 : non commencé, dépend de NTR-88 pour les endpoints de santé.

---

## Voir aussi

| Sujet | Document |
|---|---|
| La liste des tests à écrire et leur avancement | [Recensement des tests](recensement-des-tests.md)](recensement-des-tests.md) |
| La stratégie de référence (source de vérité) | [Stratégie de Tests du Projet](../design/design-tests.md)](../design/design-tests.md) |
| Le workflow Git et les branches | `CONTRIBUTING.md` du dépôt `nutrition-api` |
