# Workflow — Écrire un test de niveau 1

> Tests unitaires — une unité de code, toutes ses dépendances simulées.
> Dernière mise à jour : 2026-07-31

---

## 1. Vue d'ensemble

| | |
|---|---|
| **Question** | Mon code fonctionne-t-il correctement de manière isolée ? |
| **Projets** | `Domain.Tests`, `Application.Tests`, `Infrastructure.Tests`, `Api.Tests/Level1/` |
| **Outils** | xUnit + Moq |
| **Marqueur** | `[Trait("Level", "1")]` |
| **Lancement** | `dotnet test --filter "Level=1"` |
| **Volume** | environ 600 tests |
| **Durée** | moins d'une seconde par projet |

Aucun conteneur, aucune base, aucun réseau. C'est ce qui permet de les lancer à chaque sauvegarde.

**Frontière avec le niveau 2** — le niveau 1 teste la *logique* d'une classe. Il ne dit rien du
trajet d'une requête HTTP à travers l'application.

---

## 2. Où va quel test

| Ce que tu testes | Projet |
|---|---|
| Entité, value object, invariant métier | `NutritionApi.Domain.Tests` |
| Service applicatif, stratégie de calcul, garde d'abonnement | `NutritionApi.Application.Tests` |
| Code **pur** d'Infrastructure — traduction de données, mapping | `NutritionApi.Infrastructure.Tests` |
| Controller isolé, middleware isolé, service de démarrage (`IHostedService`), sonde de santé | `NutritionApi.Api.Tests/Level1/` |

**Le piège d'`Infrastructure.Tests`** — ce projet ne contient que du code qui ne parle **ni à une
base, ni au réseau**. Le mapping Open Food Facts y a sa place ; un repository, non. Repositories,
cache, jobs et lecteurs de flux relèvent du niveau 3, contre les vrais composants.

**Le cas des sondes de santé** — elles interrogent PostgreSQL, Redis et le serveur d'identité, ce qui
les ferait volontiers ranger au niveau 3. C'est vrai de leur chemin nominal, éprouvé là-bas contre les
vrais composants. Mais leurs **branches d'échec** — gestionnaire OIDC absent, realm sans clé publiée,
délai dépassé, multiplexeur qui lève — ne se produisent pas en arrêtant un conteneur : il faudrait
casser chaque dépendance d'une façon différente à chaque fois. Une doublure les atteint en quelques
millisecondes, et de façon déterministe.

> Ce partage a une conséquence pratique : le délai de renoncement des sondes est un paramètre
> optionnel du constructeur, laissé vide en production. Sans lui, chaque exécution de la suite
> attendrait cinq secondes pour éprouver une seule branche.

---

## 3. Le nommage

Une seule convention pour tout le projet : **`Méthode_Résultat_Condition`**, en anglais.

```
CreateAsync_ShouldReturnDietPlanResponse_WhenRequestIsValid
CreateAsync_ShouldThrow_WhenUserIdIsEmpty
GetByIdAsync_ShouldReturnNull_WhenPlanDoesNotExist
```

Le nom désigne la **méthode** éprouvée. C'est ce qui distingue ce niveau des suivants, où le test
nomme un endpoint parce qu'il en traverse plusieurs.

**Le résultat attendu vient avant la condition.** Un rapport de test doit se lire sans ouvrir les
fichiers.

---

## 4. Le pattern

Trois blocs, séparés par une ligne vide. Pas de commentaire `// Arrange` : la structure suffit.

```csharp
[Fact]
public async Task CreateAsync_ShouldReturnResponse_WhenRequestIsValid()
{
    var repository = new Mock<IDietPlanRepository>();
    repository.Setup(r => r.AddAsync(It.IsAny<DietPlan>())).Returns(Task.CompletedTask);
    var service = new DietPlanService(repository.Object, unitOfWork.Object);

    var resultat = await service.CreateAsync(userId, requete);

    Assert.Equal("Perte de poids", resultat.Name);
    repository.Verify(r => r.AddAsync(It.IsAny<DietPlan>()), Times.Once);
}
```

---

## 5. Le cas particulier des controllers

Testés **sans pipeline ASP.NET** : ni middleware, ni authentification, ni routage. Le contexte HTTP
est reconstruit à la main pour contourner volontairement ce que le niveau 2 couvre.

```csharp
var context = new DefaultHttpContext();
context.Items["UserId"] = userId;
context.User = new ClaimsPrincipal(
    new ClaimsIdentity([new Claim("sub", "keycloak-user-123")], "TestAuth"));
```

Un controller de niveau 1 vérifie qu'il appelle le bon service et traduit sa réponse. Qu'il soit
correctement routé et protégé relève du niveau 2.

---

## 6. Ce qui n'a rien à faire ici

Keycloak, JWT réel, PostgreSQL, Redis, Docker, Kubernetes, réseau, configuration système.

**La règle de tri** : si le test échoue, qu'est-ce que ça t'apprend ? Si la réponse est « une
dépendance externe ne répond pas comme prévu », le test n'est pas au bon niveau.

**Le cas limite : valider une configuration.** `KeycloakAdminConfigurationValidator` interrompt le
démarrage quand un paramètre Keycloak est vide, et ses tests sont bien de niveau 1 — la classe reçoit
un `KeycloakAdminOptions` construit à la main, ne lit aucun fichier et ne joint personne. La règle de
tri tranche : son échec apprend « le contrôle laisse passer une clé vide », pas « Keycloak est
tombé ». Ce qui relèverait d'un autre niveau, c'est de vérifier qu'un environnement donné fournit
réellement ces valeurs.

---

## 7. La limite structurelle

Un test unitaire ne prouve que ce que la doublure lui laisse prouver.

Le cas le plus net de ce projet : `DatabaseExceptionInterceptor.Translate` était couvert par cinq
tests unitaires, tous verts. Ils vérifiaient la traduction d'une exception PostgreSQL en exception
applicative — et elle était juste. Mais rien ne prouvait qu'EF Core **invoque** cet intercepteur.
Il l'invoquait ; en revanche l'exception traduite n'atteignait jamais le client, et l'API répondait
500 au lieu de 409.

Aucun test unitaire ne pouvait le voir. `AddInterceptors` est une configuration, et une
configuration ne se vérifie que contre une vraie base — donc au niveau 3.

**Quand tu écris une doublure, tu écris aussi ton hypothèse sur le comportement du composant réel.**
Si l'hypothèse est fausse, le test la confirme au lieu de la contredire.

---

## 8. Voir aussi

| Sujet | Document |
|---|---|
| Ce que chaque niveau couvre | [Niveaux de tests](niveaux-de-tests.md) |
| Écrire un test de niveau 2 | [Pipeline HTTP, doublures aux frontières](tests-niveau-2.md) |
| Écrire un test de niveau 3 | [PostgreSQL, Redis et Keycloak réels](tests-niveau-3.md) |
| Outillage xUnit et Moq | `nutrition-api/tests/XUNIT-GUIDE.md` |
