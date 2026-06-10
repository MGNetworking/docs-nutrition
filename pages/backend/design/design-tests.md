# Stratégie de Tests du Projet

## Objectif

L'objectif est de structurer les tests du projet selon plusieurs niveaux de responsabilité afin d'éviter :

* La duplication inutile des tests.
* Les temps d'exécution excessifs dans la CI/CD.
* La maintenance complexe des suites de tests.
* Le sur-test des mêmes comportements à plusieurs niveaux.

Chaque niveau de test répond à une question différente.

---

# Niveau 1 : Tests Unitaires

## Question à laquelle ils répondent

> Mon code fonctionne-t-il correctement de manière isolée ?

Les tests unitaires vérifient une unité de code unique :

* Classe métier (Domain)
* Service applicatif
* Validator
* Value Object
* Extension
* Middleware (isolé)
* Contrôleur (avec dépendances mockées)

Aucune dépendance externe n'est utilisée.

## Architecture

```text
Classe testée
    ↓
Dépendances mockées
```

Exemple :

```text
DietPlanService
    ↓
Repository mocké
```

ou

```text
Controller
    ↓
Service mocké
```

## Cas particulier : HttpContext

Dans les tests unitaires des contrôleurs :

```text
Pas de pipeline ASP.NET
Pas de middleware
Pas d'authentification réelle
```

Le contexte HTTP est reconstruit manuellement :

```csharp
var context = new DefaultHttpContext();

context.Items["UserId"] = userId;

context.User = new ClaimsPrincipal(
    new ClaimsIdentity(
        new[]
        {
            new Claim("sub", "keycloak-user-123")
        },
        "TestAuth"));
```

Cela permet de bypasser volontairement les middlewares.

## Ce que les tests unitaires ne doivent pas vérifier

* Keycloak
* JWT réel
* PostgreSQL
* Docker
* Kubernetes
* Réseau
* Configuration système

---

# Niveau 2 : Tests d'Intégration Interne

## Question à laquelle ils répondent

> La pipeline ASP.NET Core fonctionne-t-elle correctement ?

Ces tests vérifient l'intégration des composants internes de l'application.

## Architecture

```text
HTTP Request
    ↓
Authentication
    ↓
Middleware
    ↓
Controller
    ↓
Service
    ↓
HTTP Response
```

## Exemple

```text
GET /api/diet-plans
Authorization: Bearer JWT_TEST
```

Scénario :

```text
JWT accepté
    ↓
Middleware exécuté
    ↓
UserId injecté dans HttpContext
    ↓
Controller appelé
    ↓
200 OK
```

## Objectifs

Valider :

* Routing
* Authentication ASP.NET
* Middleware personnalisé
* Contrôleurs
* Sérialisation JSON
* Gestion des erreurs

## Ce qui n'est pas testé ici

```text
Pas de Keycloak réel
Pas de PostgreSQL réel
Pas de Docker
Pas de Kubernetes
```

Les dépendances externes peuvent être remplacées par :

* Mocks
* Fakes
* InMemory Providers

## Outil recommandé

```csharp
WebApplicationFactory<Program>
```

---

# Niveau 3 : Tests d'Intégration Externe

## Question à laquelle ils répondent

> Mon application communique-t-elle correctement avec ses dépendances réelles ?

Ces tests valident les interactions réelles avec les composants externes.

## Architecture

### Exemple Keycloak

```text
Keycloak
    ↓
API
```

### Exemple PostgreSQL

```text
API
    ↓
PostgreSQL
```

### Exemple complet

```text
Keycloak
    ↓
API
    ↓
PostgreSQL
```

## Scénario

```text
Token émis par Keycloak
        ↓
JWT validé par l'API
        ↓
Middleware exécuté
        ↓
Controller appelé
        ↓
Lecture PostgreSQL
        ↓
200 OK
```

## Objectifs

Valider :

* Configuration JWT
* Issuer
* Audience
* Signature
* Connexion PostgreSQL
* Réseau entre composants
* Configuration Docker

Ces tests servent principalement à détecter les problèmes de configuration ou d'intégration réelle.

---

# Niveau 4 : Smoke Tests Kubernetes / Environnement Déployé

## Question à laquelle ils répondent

> Le système déployé fonctionne-t-il réellement ?

Ici l'application est déjà déployée.

## Architecture

```text
Client
    ↓
Ingress
    ↓
Service
    ↓
Pod API
    ↓
Keycloak
    ↓
PostgreSQL
```

## Scénarios typiques

### Health Check

```text
GET /health
    ↓
200 OK
```

### Endpoint authentifié

```text
JWT valide
    ↓
Endpoint sécurisé
    ↓
200 OK
```

### Vérification base de données

```text
API
    ↓
PostgreSQL
    ↓
Connexion valide
```

## Ce que l'on cherche à vérifier

* Déploiement correct
* Configuration Kubernetes correcte
* Connectivité réseau
* Secrets
* ConfigMaps
* Ingress
* Services
* Pods

Le but n'est pas de refaire tous les tests métier déjà réalisés aux niveaux précédents.

---

# Répartition Recommandée pour ce Projet

L'objectif est d'obtenir une bonne couverture sans explosion du temps d'exécution.

Exemple cible :

```text
400 Tests Unitaires

10 à 20 Tests d'Intégration Interne

5 à 10 Tests d'Intégration Externe

2 à 5 Smoke Tests Kubernetes
```

---

# Principe Fondamental

Chaque niveau doit répondre à une question différente.

| Niveau                   | Question                                                                     |
| ------------------------ | ---------------------------------------------------------------------------- |
| Test Unitaire            | Mon code fonctionne-t-il ?                                                   |
| Intégration Interne      | Ma pipeline ASP.NET fonctionne-t-elle ?                                      |
| Intégration Externe      | Mon application communique-t-elle correctement avec Keycloak et PostgreSQL ? |
| Kubernetes / Smoke Tests | Mon système déployé fonctionne-t-il réellement ?                             |

Un test ne doit pas être dupliqué à tous les niveaux.

Chaque niveau couvre un risque spécifique du système.
