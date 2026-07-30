# Workflow — Écrire un test de niveau 3

> Tests d'intégration externe — PostgreSQL, Redis et Keycloak réels.
> Jira : NTR-28 · Sous-tâches NTR-72 (repositories), NTR-73 (Redis et import OFF).
> Dernière mise à jour : 2026-07-29

---

## 1. Vue d'ensemble

| | |
|---|---|
| **Question** | Mon application communique-t-elle correctement avec ses dépendances réelles ? |
| **Projet** | `tests/NutritionApi.Integration.Tests` |
| **Outil** | `WebApplicationFactory<Program>` + `docker-compose.yml` |
| **Marqueur** | `[Trait("Level", "3")]` — c'est lui qui pilote les filtres CI |
| **Lancement** | `./scripts/test-integration.sh` |
| **Cas** | 21 — IT-EXT-01 à 17 et IT-JOB-01 à 04 |
| **Durée** | environ 2 minutes — les cas de coupure redémarrent des conteneurs |

Ce niveau existe pour une seule raison : au niveau 2, les doublures remplacent précisément les
composants qu'il faudrait éprouver. `TestAuthHandler` remplace la validation JWT, les mocks de
repositories remplacent EF Core. Tester ces sujets là-bas ne prouverait rien.

**Frontière avec le niveau 2** — le niveau 2 valide que la tuyauterie interne est correctement
câblée. Il ne dit rien de la capacité à dialoguer avec un composant externe réel.

**Frontière avec le niveau 4** — le niveau 3 s'exécute sur un environnement **monté pour le test**.
Le niveau 4 s'exécute sur un environnement **déjà déployé**, que le test ne contrôle pas.

---

## 2. Un seul environnement, du poste à la CI

C'est la contrainte structurante de ce niveau : **`scripts/test-integration.sh` et
`scripts/dev-up.sh` montent la même pile**, depuis le même `docker-compose.yml`, avec les mêmes
fonctions de `lib.sh`. La CI appelle le script tel quel, sans déclarer ses propres services.

Ce n'est pas une commodité. Le niveau 3 doit valider la configuration Docker, le réseau entre
composants et la chaîne JWT réelle — c'est ce qui a fait écarter Testcontainers le 2026-07-21. Une
CI qui monterait ses propres conteneurs éprouverait sa propre définition, pas celle du projet.

Deux différences seulement avec `dev-up.sh` :

| | `dev-up.sh` | `test-integration.sh` |
|---|---|---|
| Migrations | `dotnet ef database update` | appliquées par la fabrique, sur la base du test |
| Données | `seed-dev.sql` | chaque test sème les siennes |

---

## 3. L'isolation par exécution

`TestDatabase` crée une base **par exécution** sur le conteneur `nutrition-postgres` :
`nutrition_test_<horodatage>_<suffixe>`. Elle y applique les migrations EF Core, puis la supprime en
sortie — connexions coupées d'abord, PostgreSQL refusant de supprimer une base encore utilisée.

Conséquences :

- `nutrition_dev` et ses données de démonstration ne sont jamais touchées.
- Deux exécutions simultanées ne se marchent pas dessus.
- Le contexte est construit **comme en production** : convention snake_case et
  `DatabaseExceptionInterceptor` compris. Un contexte de test qui omettrait l'intercepteur ne
  prouverait rien de IT-EXT-13.

Côté Redis, l'isolation passe par l'**index de base** (9 par défaut, le développement utilise 0) —
`defaultDatabase` dans la chaîne de connexion. Pas de seconde instance à monter.

Quatre variables d'environnement permettent de viser une autre infrastructure sans toucher au code :
`NUTRITION_TEST_POSTGRES`, `NUTRITION_TEST_REDIS`, `NUTRITION_TEST_REDIS_DB`,
`NUTRITION_TEST_KEYCLOAK`.

---

## 4. `IntegrationFactory` — l'application sans doublure

Rien n'est remplacé aux frontières d'Application : ni repository, ni cache, ni service Keycloak. Les
`IHostedService` sont **conservés** — le serveur Hangfire et l'enregistrement des jobs récurrents
sont précisément ce que les cas IT-JOB-* éprouvent. C'est l'inverse exact du niveau 2, où
`RemoveAll<IHostedService>()` est indispensable.

**Une seule exception** — `IOffDumpReader`, qui télécharge le dump Open Food Facts. Ce n'est ni
PostgreSQL, ni Redis, ni Keycloak : c'est un tiers de plusieurs gigaoctets. Il est remplacé par une
source de lignes que le test remplit (`factory.DumpLines`). Restent réels le mapping, la persistance
par lots et l'invalidation du cache.

La base est créée dans le **constructeur**, pas dans `IAsyncLifetime` : `ConfigureWebHost` lit la
chaîne de connexion au premier client créé, elle doit donc déjà exister. Et la méthode de libération
de xUnit entre en conflit avec celle de `WebApplicationFactory`.

---

## 5. Les jetons — `KeycloakTokens`

Le client `nutrition-api` du realm est public et autorise le *direct access grant* : un mot de passe
suffit, aucun secret n'est nécessaire. Son mapper d'audience ajoute `nutrition-api` au jeton, ce que
l'API exige.

```csharp
using var client = await factory.CreateTokenClientAsync(KeycloakTokens.AdminUser);
```

Comptes du realm — mot de passe `test` :

| Compte | Rôles | Sujet |
|---|---|---|
| `test-user` | `user` | `11111111-0000-0000-0000-000000000001` |
| `test-pro` | `user` | `11111111-0000-0000-0000-000000000002` |
| `test-admin` | `user`, `admin` | `11111111-0000-0000-0000-000000000003` |

---

## 6. Les pièges à connaître

**La ligne `User` en base.** `UserResolutionMiddleware` renvoie 401 quand le compte du jeton est
absent de la base. Un test authentifié qui ne sème pas sa ligne `User` échoue sur un 401 qui ne dit
rien de ce qu'il vérifiait. Même piège qu'au niveau 2, cause différente : ici le jeton est valide.

**La collection partagée.** `ICollectionFixture` : une base, un démarrage d'hôte pour toute la
suite. Les classes s'exécutent séquentiellement et partagent l'état de la base. Chaque test sème ce
dont il a besoin et n'attend rien de ce qu'un autre a laissé — d'où les identifiants uniques par
test (`$"it-ext-01-{Guid.NewGuid()}"`).

**La parallélisation est désactivée** pour tout l'assembly, via
`[assembly: CollectionBehavior(DisableTestParallelization = true)]`. IT-EXT-14 arrête le conteneur
PostgreSQL : une autre collection tournant en parallèle se verrait couper la base sous les pieds.

**Les tests qui touchent à l'infrastructure se remettent en état.** IT-EXT-14, 15, 16 et 17 arrêtent
un conteneur ; tous le redémarrent et attendent qu'il repasse `healthy` avant de rendre la main —
`DatabaseExceptionTest` purge en plus les pools Npgsql. IT-JOB-01 supprime les définitions de jobs
récurrents, puis les réinscrit. Sans ces remises en état, l'ordre d'exécution deviendrait
significatif, ce que xUnit ne garantit pas.

---

## 6 bis. Couper une dépendance depuis un test

Quatre cas éprouvent le comportement en dépendance coupée. Le pilotage est centralisé dans
`Fixtures/DockerContainer.cs` :

```csharp
DockerContainer.Stop(DockerContainer.Redis);
// … observer la réaction de l'application …
DockerContainer.Start(DockerContainer.Redis);
await DockerContainer.WaitHealthyAsync(DockerContainer.Redis, TimeSpan.FromSeconds(60));
```

`WaitHealthyAsync` reprend la logique de `wait_healthy` de `scripts/lib.sh`. Les noms de conteneurs
sont surchargeables par variable d'environnement — `NUTRITION_TEST_PG_CONTAINER`,
`NUTRITION_TEST_REDIS_CONTAINER`, `NUTRITION_TEST_KC_CONTAINER`.

> Ce helper appartient au **projet de tests**. Aucune ligne du code de production ne connaît Docker :
> l'application ne sait pas comment elle est déployée, et n'a pas à le savoir. En production, ce qui
> arrête et relance un conteneur est l'orchestrateur.

**Le coût est réel.** Un redémarrage de Keycloak prend une quarantaine de secondes — import du realm
compris. C'est ce qui fait passer la suite de 20 secondes à 2 minutes. À peser avant d'ajouter un
cinquième cas de coupure.

**Trois comportements attendus différents, à ne pas confondre :**

| Dépendance coupée | Réponse attendue | Pourquoi |
|---|---|---|
| PostgreSQL | **503** + `Retry-After` | l'application ne sait pas répondre sans sa base |
| Redis | **200**, données servies depuis la base | le cache est un accélérateur, pas une dépendance fonctionnelle |
| Keycloak, clés en cache | **200** | la validation est locale, aucun appel n'est nécessaire |
| Keycloak, au démarrage | **l'hôte ne démarre pas** | sans clés, l'instance rejetterait tous les jetons |

---

## 7. Les écarts assumés au recensement

**IT-EXT-13 ne porte pas sur `weight_entries`.** Le recensement décrit deux `WeightEntry` à la même
date. À l'écriture du test, `weight_entries` ne portait **aucune contrainte d'unicité** sur
`(user_id, measured_at)` : le doublon aurait été accepté, aucun code `23505` levé, le test n'aurait
rien prouvé. Il s'appuie donc sur `saved_food_items (user_id, food_item_id)`, qui exprime le même
invariant. L'assertion porte sur la `DbUpdateException` et son exception interne plutôt que sur le
409 : le service applicatif vérifie l'existence avant d'insérer, aucun appel HTTP ne peut atteindre
la contrainte.

> La contrainte manquante a depuis été ajoutée — migration
> `20260730102708_UniqueWeightEntryPerUserAndDate`. Le cas d'origine du recensement est donc
> redevenu possible ; réaligner IT-EXT-13 sur `weight_entries` reste à faire.

> IT-EXT-08 était marqué `Skip` faute de service account dans le realm. Le client confidentiel
> `nutrition-api-service` a été ajouté le 2026-07-30 — voir le défaut correspondant en section 7 bis.
> Le test s'exécute désormais.

---

## 7 bis. Les quatre défauts que ce niveau a trouvés

Tous corrigés. Et c'est l'illustration de ce que ce niveau apporte : `AddInterceptors` est une
configuration, une requête SQL brute est un contrat avec un schéma externe, un flux
`client_credentials` suppose un client qui existe — rien de tout cela ne se vérifie sans les vrais
composants.

**L'exception traduite n'atteignait jamais le middleware.** L'intercepteur était bien invoqué par EF
Core — le branchement fonctionnait. Mais EF Core **encapsule** les échecs de commande : l'exception
traduite remontait dans l'`InnerException` d'une `DbUpdateException`, jamais nue. Or
`ExceptionMiddleware` interceptait `ConflictException` et `ServiceUnavailableException` par leur type
direct. Elles tombaient donc dans le `catch` final : **500 au lieu de 409**.

Le middleware déballe désormais la chaîne des exceptions internes avant de faire correspondre les
types. Le déballage est volontairement générique — reconnaître `DbUpdateException` par son type
obligerait la couche API à référencer EF Core, ce que le reste du middleware évite précisément.

**Une base arrêtée n'était pas traduite du tout.** `DatabaseExceptionInterceptor` est un
`DbCommandInterceptor` : il n'est appelé que sur l'échec d'une commande, donc quand le serveur
répond. Conteneur arrêté, l'échec survient à l'**ouverture de la connexion** et la commande n'est
jamais atteinte — **500 au lieu de 503**.

D'où `DatabaseConnectionExceptionInterceptor`, un `DbConnectionInterceptor` qui délègue au `Translate`
du premier : une seule table de correspondance, deux points d'accroche. Les deux sont enregistrés
dans `AddInfrastructure`.

Ce second défaut n'aurait pu être trouvé qu'ici : il faut réellement couper la base.

**Le statut des jobs était faux après un déclenchement manuel.** `JobMonitoringService` déduisait le
statut du seul champ `LastJobState` de `hangfire.hash`, en considérant son absence comme « jamais
exécuté ». Or Hangfire ne l'écrit **pas** sur un déclenchement manuel : il n'inscrit que
`LastExecution` et `LastJobId`. Un job qui venait de réussir s'affichait donc `Scheduled` avec un
`lastRun` renseigné.

Le service joint désormais `hangfire.job` sur `LastJobId` pour lire l'état réel du run, avec repli sur
`LastJobState` quand la ligne a été purgée de l'historique.

Défaut invisible en test unitaire : la requête est du SQL brut sur le schéma de Hangfire, une doublure
n'aurait fait que rejouer l'hypothèse fausse.

**La purge RGPD ne pouvait fonctionner nulle part.** IT-EXT-08 a révélé que le flux
`client_credentials` de `KeycloakAdminService` n'avait aucun client à qui s'adresser : le realm ne
déclarait que `nutrition-api`, **public** — donc sans secret, donc incapable de s'authentifier ainsi.
Et `AdminBaseUrl`, `Realm` et `ServiceClientSecret` étaient vides dans les trois fichiers de
configuration.

L'échec était silencieux : `TryPurgeAsync` intercepte toute exception, journalise, et retourne
`false`. Le job échouait chaque nuit sans que rien ne le signale ailleurs que dans les journaux.

Le client confidentiel `nutrition-api-service` a été ajouté au realm, avec son service account et les
rôles `view-users` et `manage-users` de `realm-management` — le strict nécessaire, `realm-admin`
transformerait une fuite du secret en compromission complète du realm.

Ce défaut ne pouvait être trouvé qu'ici : il ne s'agissait pas d'un bug de code, mais d'une
configuration absente. Aucun test unitaire ne l'aurait vu.

---

## 8. Décisions et leurs raisons

| Décision | Pourquoi | Option écartée |
|---|---|---|
| Projet dédié plutôt que répartition par couche | Les cas débordent d'une couche : repositories et cache relèvent d'Infrastructure, la chaîne JWT exige `WebApplicationFactory`. Et `Api.Tests` porte déjà la collection de niveau 2 avec ses doublures — l'inverse de ce niveau. | Répartir dans `Infrastructure.Tests` et `Api.Tests` : deux niveaux mélangés dans les mêmes projets. |
| Base par exécution sur le conteneur de dev | Isolation réelle sans second fichier compose — un seul environnement à connaître. | `docker-compose.PostgreSql` séparé : deux définitions à maintenir alignées. |
| Index Redis dédié | Le préfixe des clés est une constante privée du service ; l'index de base isole sans toucher au code de production. | Seconde instance Redis : un conteneur de plus pour la même garantie. |
| `IOffDumpReader` remplacé | Le dump réel pèse plusieurs gigaoctets et vient d'un tiers, hors périmètre du niveau. | Télécharger réellement : suite inutilisable en CI. |
| Marqueur `Level` plutôt que filtre par projet | Un test de niveau 3 ajouté ailleurs par erreur reste exclu de la CI unitaire et exécuté par la CI d'intégration. | `dotnet test <projet>` : le filtre dépendrait de l'arborescence. |
| Couper de vrais conteneurs pour les cas de panne | C'est la seule façon d'éprouver le comportement réel : une doublure ne fait que rejouer l'exception qu'on lui demande de lever. | Simuler la panne par une doublure : on vérifierait sa propre hypothèse. |
| Attente bornée au démarrage plutôt qu'échec immédiat | En cluster, l'API et le serveur d'identité démarrent souvent ensemble ; quelques secondes de décalage ne justifient pas un cycle de redémarrage. | Échec immédiat : redémarrages en boucle bruyants pour un cas nominal. |

---

## 9. Ce qui n'est pas couvert

| Manque | Statut |
|---|---|
| Déploiement, ingress, secrets, réseau du cluster | Niveau 4 — NTR-112 |
| Rejet des jetons expirés, mauvais issuer, mauvaise audience | Décrit dans NTR-28, non recensé — pas d'identifiant attribué |
| Contrainte d'unicité sur `weight_entries` | Ajoutée le 2026-07-30 — IT-EXT-13 reste à réaligner |
| Suppression d'un compte **existant** dans Keycloak | IT-EXT-08 sème un identifiant absent du realm : l'appel répond 404, traité comme succès |
| Coupure Redis pendant un import OFF | Non couvert — `InvalidateAllSearchesAsync` n'intercepte pas, l'import doit échouer visiblement |
| Rafraîchissement des clés du realm pendant une coupure Keycloak | Non couvert — fenêtre étroite, le démarrage bloquant traite le cas principal |

---

## 10. État

**21 tests, tous verts, aucun ignoré.** Vérifié le 2026-07-30 : `Réussi! - échec : 0, réussite : 21,
ignorée(s) : 0, total : 21` en 2 min 02. Les niveaux 1 et 2 restent verts après les correctifs de
production — 699 tests.
