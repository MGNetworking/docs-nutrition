# Règles de découpage des tickets — NTR

> Fichier de référence pour la restructuration et la rédaction des tickets Jira.
> Issu des observations faites sur NTR-40, NTR-41, NTR-53 en juin 2026.

---

## Principe fondamental

**1 responsabilité = 1 ticket.**

Une responsabilité est une raison unique de changer. Si un ticket peut changer pour deux raisons distinctes (ex : "la règle métier change" ET "le service change"), il doit être découpé.

---

## Règle 1 — Séparer les couches d'architecture

Chaque ticket doit appartenir à **une seule couche** :

| Couche | Ce qu'elle contient | Ce qu'elle NE contient PAS |
|---|---|---|
| **Domain** | Entités, Value Objects, invariants, règles métier internes à l'agrégat | Orchestration, appels repository, DTOs |
| **Application** | Orchestration des use cases, validation des règles cross-agrégats | Règles domaine, accès DB direct, HTTP |
| **Infrastructure** | Repositories EF Core, cache Redis, jobs Hangfire | Règles métier, orchestration |
| **API** | Controllers, routing, sérialisation HTTP | Logique métier, accès DB |

**Symptôme d'une violation :** un ticket mentionne à la fois "calculer BMR" (Domain/Application) et "créer un endpoint" (API).

---

## Règle 2 — Séparer interface et implémentation

Un ticket qui déclare une interface (`IXxxService`, `IXxxRepository`) est distinct du ticket qui l'implémente (`XxxService`, `XxxRepository`).

**Pourquoi :** l'interface est un contrat stable. L'implémentation peut changer indépendamment.

**Structure attendue :**
```
[ Ticket A ] Déclarer IDietRepository
[ Ticket B ] Implémenter DietRepository (EF Core)
```

---

## Règle 3 — Séparer commande et requête (CQS)

Une **commande** modifie l'état (Create, Update, Delete, Archive, Launch).
Une **requête** lit l'état (Get, List, Search, Resolve).

Elles n'ont pas les mêmes dépendances ni les mêmes cas d'erreur — les mettre dans le même ticket crée de la confusion.

**Exemple de violation :** NTR-41 mélange `ArchiveAsync` (commande) et `GetActiveAtDateAsync` (requête).

**Structure attendue :**
```
[ Ticket A ] Archiver une Diet → commande write
[ Ticket B ] Résoudre la Diet active à une date → requête read, réutilisable
```

---

## Règle 4 — Règles Domain ≠ Orchestration Application

Les règles métier (invariants, gardes, calculs) appartiennent au **Domain**.
L'orchestration (fetch → appel domaine → save → retour DTO) appartient à l'**Application**.

Un ticket Application ne doit pas décrire les règles métier — il doit décrire le **cas d'usage** que le service orchestre.

**Exemple de violation :** NTR-40 décrit "Vérifier qu'aucune Diet n'est déjà active" comme une tâche applicative, alors que la règle est dans `Diet.ChangeDietStatus()` (Domain).

**Formulation correcte pour un ticket Application :**
> "Implémenter `LaunchAsync` : orchestrer le lancement d'un DietPlan vers une Diet active."

**Formulation incorrecte :**
> "Vérifier qu'aucune Diet n'est déjà active, calculer BMR, créer le snapshot."

---

## Règle 5 — Un ticket = une classe ou une méthode identifiable

Un ticket doit être traçable jusqu'à **une classe** ou **un groupe de méthodes cohérentes** dans le code.

**Trop large (à éviter) :**
> NTR-53 : "Implémenter les repositories EF Core" → 7 repositories dans un ticket.

**Mieux :**
```
[ NTR-53a ] Implémenter DietRepository (EF Core) — méthodes : GetByIdAsync, GetActiveByUserIdAsync, GetActiveAtDateAsync, GetByUserIdAsync, AddAsync, UpdateAsync
[ NTR-53b ] Implémenter DietPlanRepository (EF Core) — méthodes : ...
[ NTR-53c ] Implémenter MealRepository (EF Core) — méthodes : ...
```

---

## Règle 6 — Critères d'acceptation obligatoires

Tout ticket doit avoir **les trois critères** :

```markdown
**Critères d'acceptation :**
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts (exceptions attendues listées)
- [ ] Tests unitaires (TDD) créés ou mis à jour
```

Pour les tickets Infrastructure (repositories), ajouter :
```markdown
- [ ] Tests d'intégration couverts (Testcontainers — NTR-28)
```

---

## Règle 7 — Référencer les contrats existants

Un ticket d'implémentation doit référencer l'interface qu'il implémente.

```markdown
**Prérequis :** lire `IDietRepository.cs` — contrat à respecter.
**Méthodes à implémenter :**
- `GetByIdAsync(Guid id)`
- `GetActiveByUserIdAsync(Guid userId)`
- `GetActiveAtDateAsync(Guid userId, DateOnly date)`
- `GetByUserIdAsync(Guid userId)`
- `AddAsync(Diet diet)`
- `UpdateAsync(Diet diet)`
```

---

## Règle 8 — Responsabilités transverses = ticket dédié

Une méthode utilisée par plusieurs services ou features (ex : `GetActiveAtDateAsync`) ne doit pas être glissée dans un ticket feature. Elle mérite son propre ticket ou doit être explicitement listée dans le ticket repository correspondant.

---

## Template de ticket bien structuré

```markdown
**Prérequis :** lire [fichier design ou interface concernée]

**Objectif :** [une phrase — ce que ce ticket accomplit]

**Périmètre :**
- [Classe ou méthode 1]
- [Classe ou méthode 2]

**Cas d'erreur attendus :**
- [Exception 1] si [condition]
- [Exception 2] si [condition]

**Critères d'acceptation :**
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts
- [ ] Tests unitaires (TDD) créés ou mis à jour
```
