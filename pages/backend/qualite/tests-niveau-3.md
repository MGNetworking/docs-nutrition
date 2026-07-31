# Workflow — Écrire un test de niveau 3

> Tests d'intégration externe — PostgreSQL, Redis et Keycloak réels.
> Jira : NTR-28 · Sous-tâches NTR-72 (repositories), NTR-73 (Redis et import OFF).
> Dernière mise à jour : 2026-07-31

---

## 1. Vue d'ensemble

| | |
|---|---|
| **Question** | Mon application communique-t-elle correctement avec ses dépendances réelles ? |
| **Projet** | `tests/NutritionApi.ExternalIntegration.Tests` |
| **Outil** | `WebApplicationFactory<Program>` + `docker-compose.yml` |
| **Marqueur** | `[Trait("Level", "3")]` — c'est lui qui pilote les filtres CI |
| **Lancement** | `./scripts/test-integration.sh` |
| **Cas** | 25 — chaîne d'authentification, repositories, cache, jobs, dépendances coupées, garde-fous de démarrage |
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
  prouverait rien du test de violation d unicité.

Côté Redis, l'isolation passe par l'**index de base** (9 par défaut, le développement utilise 0) —
`defaultDatabase` dans la chaîne de connexion. Pas de seconde instance à monter.

Huit variables d'environnement permettent de viser une autre infrastructure sans toucher au code :
`NUTRITION_TEST_POSTGRES`, `NUTRITION_TEST_REDIS`, `NUTRITION_TEST_REDIS_DB`,
`NUTRITION_TEST_KEYCLOAK`, `NUTRITION_TEST_KEYCLOAK_URL`, et les trois noms de conteneurs
`NUTRITION_TEST_PG_CONTAINER`, `NUTRITION_TEST_REDIS_CONTAINER`, `NUTRITION_TEST_KC_CONTAINER`.

---

## 4. `IntegrationFactory` — l'application sans doublure

Rien n'est remplacé aux frontières d'Application : ni repository, ni cache, ni service Keycloak. Les
`IHostedService` sont **conservés** — le serveur Hangfire et l'enregistrement des jobs récurrents
sont précisément ce que les cas de supervision éprouvent. C'est l'inverse exact du niveau 2, où
`RemoveAll<IHostedService>()` est indispensable.

**Une seule exception** — `IOffDumpReader`, qui télécharge le dump Open Food Facts. Ce n'est ni
PostgreSQL, ni Redis, ni Keycloak : c'est un tiers de plusieurs gigaoctets. Il est remplacé par une
source de lignes que le test remplit (`factory.DumpLines`). Restent réels le mapping, la persistance
par lots et l'invalidation du cache.

La base est créée dans le **constructeur**, pas dans `IAsyncLifetime` : `ConfigureWebHost` lit la
chaîne de connexion au premier client créé, elle doit donc déjà exister. Et la méthode de libération
de xUnit entre en conflit avec celle de `WebApplicationFactory`.

---

## 4 bis. Un environnement de configuration à part

Le niveau 3 tourne sous l'environnement **`ExternalIntegration`**, avec son
`appsettings.ExternalIntegration.json`.

**Il ne peut pas réutiliser `Testing`.** Le niveau 2 s'en sert déjà, et pointe volontairement vers une
autorité factice injoignable. Un `appsettings.Testing.json` serait chargé par les deux — et
**gagnerait** sur les `UseSetting` de la fabrique de niveau 2, la configuration applicative étant
empilée après celle de l'hôte. Les tests de niveau 2 se mettraient à viser le vrai Keycloak.

Le partage se fait donc par nature de valeur :

| Où | Quoi | Pourquoi |
|---|---|---|
| `appsettings.ExternalIntegration.json` | journalisation, `RequireHttpsMetadata`, délai de démarrage | propre aux tests, statique |
| `UseSetting` depuis `RealmExport` | realm, secret du service account, autorité | vient du realm, ne doit exister qu'à un seul endroit |
| `UseSetting` dynamique | chaîne de connexion, index Redis | change à chaque exécution |

---

## 4 ter. Le realm est la source de vérité

`RealmExport` lit `keycloak/realm-export.json`, copié dans la sortie de compilation. **Aucun compte,
identifiant, mot de passe ou secret n'est ressaisi dans les fixtures.**

```csharp
public static string SubjectOf(string username);   // le sub que porteront ses jetons
public static string PasswordOf(string username);
public static string SecretOf(string clientId);
public static string RequireClient(string clientId);
```

Avant, ces valeurs existaient à trois endroits : l'export du realm, les fixtures, et `seed-dev.sql`.
Un renommage de compte laissait les tests interroger un identifiant obsolète, sans que rien ne le
signale avant l'échec. Désormais l'erreur est explicite — « le compte *x* n'existe pas dans
keycloak/realm-export.json ».

**Trois clients de test** y sont déclarés, en plus de `nutrition-api` et du service account :

| Client | Particularité | Ce qu'il permet d'éprouver |
|---|---|---|
| `nutrition-api-tests-shortlived` | `access.token.lifespan` à 1 seconde | le rejet d'un jeton expiré, sans attendre les 1800 s du realm |
| `nutrition-api-tests-no-audience` | aucun mapper d'audience | le rejet d'un jeton destiné à une autre API |

La tolérance d'horloge JWT — cinq minutes par défaut — est annulée dans la fabrique, **et là
seulement**. Sans cela, un jeton expiré depuis une seconde resterait accepté. La production conserve
le comportement par défaut.

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
test (`$"{prefixe}-{Guid.NewGuid()}"`).

**La parallélisation est désactivée** pour tout l'assembly, via
`[assembly: CollectionBehavior(DisableTestParallelization = true)]`. Un cas arrête le conteneur
PostgreSQL : une autre collection tournant en parallèle se verrait couper la base sous les pieds.

**Les tests qui touchent à l'infrastructure se remettent en état.** Les quatre cas de coupure arrêtent
un conteneur ; tous le redémarrent et attendent qu'il repasse `healthy` avant de rendre la main —
`DatabaseExceptionTest` purge en plus les pools Npgsql. Le cas de la liste vide supprime les définitions de jobs
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

**Un test échappe à la collection partagée.** Celui qui vérifie le statut d'un job terminé démarre
**sa propre application**, donc son propre serveur Hangfire et sa propre base.

C'est le seul de la suite qui dépende d'un traitement de fond : il déclenche un job et attend qu'un
serveur le prenne et le mène à son terme. Or après les coupures de conteneurs, le serveur Hangfire de
l'application partagée ne reprend plus les jobs — l'attente expirait au bout de 60 secondes, alors
que le test passait en 5 secondes lancé seul.

> La cause exacte de ce blocage n'est pas identifiée. L'isolation traite le symptôme. Si un serveur
> Hangfire ne se remet réellement pas d'une coupure de base, c'est un défaut du produit qui reste à
> instruire.

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

Un cinquième cas relève du même refus de démarrer sans être une coupure : un paramètre
d'administration Keycloak vide — voir la section 6 ter.

---

## 6 ter. Éprouver un garde-fou de démarrage

Deux cas vérifient que l'application **refuse de démarrer** — l'un quand le serveur d'identité est
injoignable (`KeycloakOutageTest`), l'autre quand un paramètre d'administration Keycloak est vide
(`KeycloakAdminConfigurationTest`, NTR-149). Le motif est le même :

```csharp
using var sansSecret = factory.WithWebHostBuilder(
    builder => builder.UseSetting("Keycloak:ServiceClientSecret", string.Empty));

var echec = Assert.ThrowsAny<Exception>(() => sansSecret.CreateClient());

Assert.Contains("Keycloak:ServiceClientSecret", ExceptionChain.DeroulerLesCauses(echec), StringComparison.Ordinal);
```

Trois points qui ne vont pas de soi :

- **`CreateClient()` est le déclencheur**, pas le constructeur de la fabrique. C'est lui qui construit
  l'hôte et exécute les services hébergés.
- **Le délégué de `WithWebHostBuilder` s'applique après `ConfigureWebHost`**, ce qui permet d'écraser
  une valeur que la fabrique a déjà posée. Un cas de garde-fou n'a donc pas toujours besoin d'arrêter
  un conteneur : vider une clé suffit quand c'est la configuration qu'on éprouve.
- **L'hôte enveloppe l'exception du service qui a levé.** Le message d'origine n'est pas celui de
  l'exception de premier niveau, d'où `Fixtures/ExceptionChain.DeroulerLesCauses`, qui concatène la
  chaîne des causes avant d'y chercher le texte attendu.

**Ces cas doivent être vérifiés à l'envers.** Un test de garde-fou reste vert si le garde-fou n'est
branché nulle part — c'est même précisément ce qu'il est censé détecter. La vérification consiste à
retirer l'enregistrement de `Program.cs` et à constater le rouge : pour NTR-149,
`Assert.ThrowsAny() Failure: No exception was thrown`, l'API démarrant alors avec un secret vide.

---

## 7. Les écarts assumés

**Le test de violation d unicité ne porte pas sur `weight_entries`.** Le cas visait deux `WeightEntry` à la même
date. À l'écriture du test, `weight_entries` ne portait **aucune contrainte d'unicité** sur
`(user_id, measured_at)` : le doublon aurait été accepté, aucun code `23505` levé, le test n'aurait
rien prouvé. Il s'appuie donc sur `saved_food_items (user_id, food_item_id)`, qui exprime le même
invariant. L'assertion porte sur la `DbUpdateException` et son exception interne plutôt que sur le
409 : le service applicatif vérifie l'existence avant d'insérer, aucun appel HTTP ne peut atteindre
la contrainte.

> La contrainte manquante a depuis été ajoutée — migration
> `20260730102708_UniqueWeightEntryPerUserAndDate`. Le cas d'origine est donc
> redevenu possible ; réaligner ce test sur `weight_entries` reste à faire.

**Le test de purge crée un vrai compte Keycloak.** Il a d'abord semé un identifiant inventé : l'appel
de suppression répondait alors 404, que `KeycloakAdminService` traite comme « le compte n'existe
plus » et ignore. Le test passait sans jamais éprouver la suppression, et construisait un état
impossible en production — `keycloak_id` est par définition le `sub` d'un compte existant.

Il crée désormais un compte jetable via l'API d'administration, vérifie qu'il existe, lance la purge,
puis vérifie sa disparition **de Keycloak et de la base**. Un `finally` le supprime si le test échoue
avant la purge.

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

**La purge RGPD ne pouvait fonctionner nulle part.** Le test de purge a révélé que le flux
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
| Rejet d'un jeton de **mauvais issuer** | Exigerait un second realm dans l'export, pour un chemin de validation identique à celui de l'audience — écarté (NTR-148) |
| Contrainte d'unicité sur `weight_entries` | Ajoutée le 2026-07-30 — le test de violation reste à réaligner |
| Coupure Redis pendant un import OFF | Non couvert — `InvalidateAllSearchesAsync` n'intercepte pas, l'import doit échouer visiblement |
| Rafraîchissement des clés du realm pendant une coupure Keycloak | Non couvert — fenêtre étroite, le démarrage bloquant traite le cas principal |

---

## 10. État

**25 tests, tous verts, aucun ignoré.** Vérifié le 2026-07-31 : `Réussi! - échec : 0, réussite : 25,
ignorée(s) : 0, total : 25` en 1 min 54. Les niveaux 1 et 2 restent verts — 708 tests (599 et 109).
