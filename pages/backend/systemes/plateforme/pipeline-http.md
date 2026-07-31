# Workflow — Pipeline HTTP

**Ajouté le :** 2026-07-27 · **Feature associée :** Plateforme API · **Ticket :** NTR-121

> Ce document explique la traversée d'une requête de bout en bout : quel composant s'exécute, dans
> quel ordre, et pourquoi cet ordre. Les fiches voisines ne décrivent chacune qu'un maillon —
> [Exception Filter](exception-filter.md) pour la traduction des erreurs,
> [OpenAPI](openapi.md) pour la spec.

---

## 1. Vue d'ensemble

### Deux phases, pas une

Le routage **sélectionne** l'action au tout début, et ce n'est qu'à la toute fin qu'elle est
**exécutée**. Tous les middlewares s'exécutent entre les deux.

```
┌─ SÉLECTION ────────────────────────────────────────────────┐
│  UseRouting()                                              │
│    compare l'URL aux routes → trouve l'action              │
│    la dépose dans HttpContext, avec ses attributs          │
│    ⚠️ le controller n'est PAS instancié, l'action PAS appelée│
└────────────────────────────────────────────────────────────┘
                          ↓  les middlewares (ci-dessous)
┌─ EXÉCUTION ────────────────────────────────────────────────┐
│  UseEndpoints()                                            │
│    instancie le controller, injecte ses dépendances,       │
│    appelle enfin l'action                                  │
└────────────────────────────────────────────────────────────┘
```

**Ni `UseRouting` ni `UseEndpoints` n'apparaissent dans `Program.cs`.** Depuis .NET 6,
`WebApplication` les insère automatiquement — au début et à la fin du pipeline — dès qu'un `Map*`
est présent. `app.MapControllers()` suffit à les déclencher.

C'est cette séparation qui rend les attributs exploitables : `UseAuthorization` lit `[Authorize]` sur
l'action **déjà sélectionnée**, sans quoi il ne saurait pas quelle policy appliquer. Elle explique
aussi deux comportements observés :

- **Un GUID malformé donne 404, pas 400.** La contrainte `{id:guid}` participe à la sélection :
  aucune action ne correspond, il n'y a rien à exécuter.
- **`/hangfire` ne traverse pas les middlewares suivants.** C'est un endpoint sélectionné en phase 1,
  qui répond avant d'atteindre `UserResolutionMiddleware`.

Si un middleware interrompt entre les deux phases, **le controller n'est jamais instancié**.

### Le pipeline

```
                    ┌─────────────────────────────────────────────┐
   requête HTTP ───►│ RequestLoggingMiddleware                    │  chronomètre démarré
                    ├─────────────────────────────────────────────┤
                    │ UseSwagger / UseSwaggerUI   (hors prod)     │
                    ├─────────────────────────────────────────────┤
                    │ UseHttpsRedirection                         │
                    ├─────────────────────────────────────────────┤
                    │ UseCors("front")                            │
                    ├─────────────────────────────────────────────┤
                    │ ExceptionMiddleware                         │  filet d'erreurs
                    ├─────────────────────────────────────────────┤
                    │ UseAuthentication                           │  JWT → ClaimsPrincipal
                    ├─────────────────────────────────────────────┤
                    │ UseAuthorization                            │  policies, rôles
                    ├─────────────────────────────────────────────┤
                    │ MapHangfireDashboard("/hangfire")           │  ─┐ sortie possible
                    ├─────────────────────────────────────────────┤   │
                    │ UserResolutionMiddleware                    │   │ keycloakId → User.Id
                    ├─────────────────────────────────────────────┤   │
                    │ MapControllers                              │   │
                    └─────────────────────────────────────────────┘  ─┘
                            │
   réponse HTTP ◄───────────┘  chronomètre arrêté, une ligne de log émise
```

## 2. Qui fait quoi

```
NutritionApi.Api/
├── Program.cs                        — compose le pipeline, dans cet ordre
└── Middleware/
    ├── RequestLoggingMiddleware.cs   — trace la requête
    ├── ExceptionMiddleware.cs        — traduit les exceptions en réponses HTTP
    └── UserResolutionMiddleware.cs   — résout l'utilisateur interne
```

| Composant | Responsabilité unique |
|---|---|
| `RequestLoggingMiddleware` | Émettre **une** entrée de journal par requête : méthode, route, statut, durée |
| `UseHttpsRedirection` | Rediriger le trafic en clair vers HTTPS |
| `UseCors("front")` | Refuser les appels dont l'origine n'est pas déclarée |
| `ExceptionMiddleware` | Convertir toute exception non gérée en réponse HTTP normalisée (RFC 9457, avec `traceId`) — voir [Exception Filter](exception-filter.md) |
| `UseAuthentication` | Valider le JWT Keycloak et peupler `HttpContext.User` |
| `UseAuthorization` | Appliquer les policies (`AdminOnly`) et les rôles |
| `MapHangfireDashboard` | Servir `/hangfire`, protégé par `HangfireAdminAuthorizationFilter` |
| `UserResolutionMiddleware` | Traduire le `sub` du token en `User.Id` interne, déposé dans `HttpContext.Items` — **et refuser** la requête si aucun profil ne correspond, sauf sur les actions marquées `[AllowWithoutProfile]` |
| `MapControllers` | Router vers l'action et exécuter le traitement métier |

## 3. Le parcours d'une requête

1. **Le chronomètre démarre.** `RequestLoggingMiddleware` retient l'horodatage et passe la main.
2. **Redirection HTTPS** si la requête est arrivée en clair — la réponse est un 307, et elle sera
   tracée comme telle.
3. **CORS.** Si l'origine n'est pas dans `Cors:AllowedOrigins`, les en-têtes d'autorisation ne sont
   pas émis et le navigateur bloque la réponse côté client.
4. **Le filet d'erreurs se déploie.** À partir d'ici, toute exception remonte à
   `ExceptionMiddleware`, qui produit la réponse HTTP correspondante.
5. **Authentification.** Le JWT est validé contre la clé publique Keycloak ; `KeycloakClaimsTransformation`
   convertit `realm_access.roles` en `ClaimTypes.Role` standards.
6. **Autorisation.** Les policies s'appliquent. Un refus produit un 401 ou un 403.
7. **`/hangfire` sort du pipeline** si la route correspond : le dashboard répond directement.
8. **Résolution de l'utilisateur.** `UserResolutionMiddleware` échange le `sub` contre le `User.Id`
   interne. Un compte absent en base donne un 401, même avec un token valide — **sauf** si l'action
   porte `[AllowWithoutProfile]`.
9. **L'action s'exécute**, la réponse remonte.
10. **Le chronomètre s'arrête.** Le `finally` de `RequestLoggingMiddleware` lit le statut réellement
    écrit et émet la ligne de journal.

## 4. Décisions et leurs raisons

| Décision | Pourquoi | Option écartée |
|---|---|---|
| Le logging est **en tête**, avant `ExceptionMiddleware` | C'est la seule position d'où la durée couvre le traitement entier et d'où le statut lu est le statut final — y compris le 500 écrit par `ExceptionMiddleware`. | Le placer après : la durée exclurait le traitement d'erreur, et une requête en échec serait tracée avec le statut par défaut 200. |
| Le logging **relance** l'exception | La réponse d'erreur appartient à `ExceptionMiddleware`, et à lui seul. Deux composants qui écrivent la réponse, c'est une réponse corrompue. | Capturer et répondre depuis le logging : duplication de la logique d'erreur. |
| Niveau gradué sur le statut (Information / Warning ≥ 400 / Error ≥ 500) | Un 500 noyé au niveau Information est invisible en production. La graduation rend le journal filtrable sans parser le message. | Tout en Information : simple, mais inutilisable pour l'alerte. |
| CORS **fermé par défaut** — section vide = aucune origine | Un oubli de configuration doit bloquer, jamais ouvrir. Une politique permissive oubliée en production est une faille silencieuse. | `AllowAnyOrigin()` en développement : diverge de la production, et masque les erreurs de configuration jusqu'au déploiement. |
| `UseCors` **avant** `ExceptionMiddleware` | Une requête refusée par CORS n'a pas à traverser le reste du pipeline. | Après l'authentification : coût inutile et en-têtes CORS absents des réponses d'erreur. |
| Le dashboard Hangfire est monté **après** `UseAuthorization` | Son filtre lit `HttpContext.User`, qui n'est peuplé qu'après les middlewares d'authentification. | Avant : le filtre verrait un utilisateur vide et refuserait tout le monde. |
| …et **avant** `UserResolutionMiddleware` | Le dashboard n'a pas besoin de la correspondance `keycloakId` → `User` interne. | Après : un administrateur sans profil applicatif en base serait refusé. |
| La dispense de profil est un **attribut**, pas une liste de chemins | `[AllowWithoutProfile]` vit sur l'action qu'il concerne et la suit si sa route change. | Comparer `Request.Path` dans le middleware : plus court, mais renommer la route romprait la dispense **silencieusement** — et le blocage reviendrait à l'identique (NTR-142). |

### La dispense `[AllowWithoutProfile]`

`POST /users/me` crée le profil utilisateur. Sans dispense, `UserResolutionMiddleware` le refusait :
**il fallait déjà posséder un profil pour en créer un** — aucun utilisateur ne pouvait s'inscrire
(NTR-142).

```csharp
// UsersController.cs — l'étiquette
[HttpPost("me")]
[AllowWithoutProfile]
public async Task<IActionResult> CreateUser(...)

// UserResolutionMiddleware.cs — le lecteur
private static bool AllowsMissingProfile(HttpContext context)
    => context.GetEndpoint()?.Metadata.GetMetadata<AllowWithoutProfileAttribute>() is not null;
```

Un attribut n'exécute rien : il **stocke** une information dans l'assembly. Le middleware la **lit**
via `GetEndpoint()`, disponible parce que le routage a déjà eu lieu (phase 1). Les deux morceaux
sont indissociables — l'attribut seul est inerte, la lecture seule ne trouve rien.

`[Authorize]` fonctionne exactement ainsi : la seule différence est que son lecteur est fourni par
Microsoft.

> La dispense ne vaut **que** pour l'action marquée. Partout ailleurs, un jeton valide sans profil
> reste refusé — c'est vérifié par un test dédié.

## 4 bis. La validation des jetons est locale — et ce que ça implique

`UseAuthentication` ne contacte **pas** Keycloak à chaque requête. Au premier besoin, l'API récupère
les clés publiques de signature du realm et les met en cache ; ensuite, chaque signature est vérifiée
par un calcul local, sans aucun appel réseau.

Deux conséquences opposées, l'une rassurante, l'autre dangereuse.

**Une coupure de Keycloak est invisible pour les utilisateurs déjà connectés.** Les jetons en
circulation continuent d'être validés. Constaté par IT-EXT-16 : conteneur Keycloak arrêté, jeton
valide, réponse 200. Ce qui casse, c'est l'**émission** de nouveaux jetons — passé
`accessTokenLifespan`, plus personne ne peut entrer.

**Une instance démarrée sans Keycloak n'a aucune clé.** Elle accepte le trafic et refuse **tous** les
jetons, pendant que ses voisines, démarrées plus tôt, fonctionnent normalement. Deux réplicas
derrière le même service, deux comportements — le pire cas à diagnostiquer.

### Le garde-fou : `KeycloakAvailabilityService`

Un `IHostedService` force la récupération des clés au démarrage, avant que l'application n'accepte
la moindre requête. S'il n'y parvient pas dans le délai imparti, le démarrage est interrompu.

| Clé | Défaut | Rôle |
|---|---|---|
| `Keycloak:StartupTimeoutSeconds` | `60` | délai maximal ; réessai toutes les 3 s |

**L'attente est bornée plutôt qu'immédiate** : dans un cluster, l'API et Keycloak démarrent souvent
ensemble, et quelques secondes de décalage ne justifient pas un cycle de redémarrage. Passé le délai,
l'échec est franc — le processus s'arrête, et l'orchestrateur relance le pod (`CrashLoopBackOff`
sous Kubernetes). Aucun code d'orchestration n'est nécessaire : c'est le comportement natif.

Le service vérifie que des clés ont été **publiées**, pas seulement que le serveur a répondu : un
realm qui répond sans clé de signature est aussi inutilisable qu'un serveur absent.

> Implémenté en `IHostedService` à dessein — les tests de niveau 2 pointent vers une autorité factice
> et retirent déjà tous les services hébergés. Ils ne sont donc pas concernés.

Éprouvé par IT-EXT-17 : Keycloak arrêté au démarrage, l'hôte refuse de démarrer.

---

## 5. Ce qui n'est pas couvert

| Manque | Statut |
|---|---|
| `Cors:AllowedOrigins` est **vide** dans `appsettings.json` | À renseigner par environnement — en l'état, aucun appel cross-origin ne passe |
| Aucune limitation de débit (*rate limiting*) | Non prévu à ce stade |
| Le journal ne porte pas d'identifiant de corrélation | Le `TraceIdentifier` d'ASP.NET existe mais n'est pas repris dans la trace |
| Le corps des requêtes et réponses n'est jamais journalisé | Volontaire — données personnelles |

## 6. État de confiance

| Marque | Élément |
|---|---|
| ✅ | Contenu et niveau de la trace, comportement en cas d'exception — `RequestLoggingMiddleware` couvert par 15 cas de test |
| ✅ | Traduction des exceptions en statuts — 16 tests dans `ExceptionMiddlewareTest`, dont les invariants de domaine (422), les dépendances injoignables (503) et l'annulation client, ajoutés par NTR-135 |
| ✅ | Aucune fuite de message interne ni de nom de dépendance dans les réponses d'erreur |
| ✅ | Résolution de l'utilisateur — `UserResolutionMiddlewareTest` |
| ⚠️ | L'**ordre** du pipeline : établi par lecture de `Program.cs` et raisonnement, jamais constaté sur une requête réelle |
| ❌ | Le comportement CORS de bout en bout — demande un navigateur et une origine tierce |
| ✅ | Une coupure de Keycloak reste sans effet sur les jetons en cours — IT-EXT-16 |
| ✅ | L'application refuse de démarrer sans les clés du realm — IT-EXT-17 |
| ❌ | Le refus du dashboard Hangfire à un non-admin — **attendu du niveau 3, non couvert**. NTR-28 est fermé sans l'avoir traité : aucun test n'appelle `/hangfire`. Sans ticket porteur |

## 7. Configuration

```json
{
  "Cors": {
    "AllowedOrigins": []
  },
  "Keycloak": {
    "StartupTimeoutSeconds": 60
  }
}
```

| Clé | Rôle |
|---|---|
| `Cors:AllowedOrigins` | Tableau des origines acceptées, schéma et port compris (`https://app.exemple.fr`). Vide = tout refusé. |
| `Keycloak:StartupTimeoutSeconds` | Délai maximal d'attente des clés du realm au démarrage. Surchargeable par `Keycloak__StartupTimeoutSeconds` en variable d'environnement. |

La politique autorise tout en-tête, toute méthode, et les *credentials* — mais uniquement pour ces
origines. `AllowCredentials()` est d'ailleurs incompatible avec une origine générique : la liste
explicite n'est pas seulement plus sûre, elle est obligatoire ici.

## 8. Où creuser

- [Exception Filter](exception-filter.md) — le détail de la traduction exception → statut HTTP
- [OpenAPI](openapi.md) — la spec, et pourquoi `/hangfire` n'y figure pas
- [Hangfire — moteur de jobs récurrents](../../briques/hangfire.md) — le dashboard et son filtre d'autorisation
- [Keycloak Admin API](../../briques/keycloak-admin.md) — l'administration des comptes, hors pipeline
