# Workflow — Mise à disposition des aliments

**Ajouté le :** 2026-07-23
**Feature associée :** `systemes/aliments/mise-a-disposition.md`
**Ticket :** NTR-55

> **Ce document explique comment le système fonctionne, de bout en bout.**
> Les deux annexes voisines décrivent chacune une brique isolée : `briques/hangfire.md`
> le **moteur de jobs**, `systemes/aliments/source-open-food-facts.md` la **source de données**. Ce document-ci
> est celui qui les assemble — c'est le point d'entrée à lire en premier.

---

## 1. Vue d'ensemble

La fonctionnalité a **deux volets indépendants**, qui ne communiquent jamais directement :

```
🕒 3h00 UTC, chaque nuit              👤 L'administrateur ouvre le back-office
   Hangfire déclenche le job             GET /api/v1/admin/system/health
            │                                        │
            ▼                                        ▼
    ┌───────────────────┐                  ┌────────────────────────┐
    │   REMPLISSAGE     │                  │      SUPERVISION       │
    │   OffImportJob    │                  │  JobMonitoringService  │
    └───────────────────┘                  └────────────────────────┘
            │                                        │
   écrit dans FoodItem                    lit l'état dans hangfire.hash
            │                                        │
            └──────────────► PostgreSQL ◄────────────┘
```

| Volet | Question à laquelle il répond | Résultat visible |
|---|---|---|
| **Remplissage** | « comment le catalogue d'aliments se remplit-il ? » | La recherche d'aliments trouve des produits |
| **Supervision** | « l'import a-t-il tourné, a-t-il réussi ? » | Le back-office affiche l'état des jobs |

**Le lien entre les deux passe par PostgreSQL.** Hangfire enregistre chaque exécution dans ses
propres tables ; la supervision relit ces traces. Aucun appel direct entre les deux volets —
c'est ce découplage qui rend l'historique fiable même après un redémarrage de l'application.

---

## 2. Qui fait quoi — les classes

L'organisation sépare **le moteur** (partagé par tous les jobs) et **chaque job métier** :

```
Infrastructure/
├── Scheduling/              ← la mécanique Hangfire — ce ne sont pas des jobs
│   ├── HangfireAdminAuthorizationFilter.cs
│   └── JobMonitoringService.cs
└── Jobs/
    └── OffImport/           ← un dossier par job, avec tout ce qui lui appartient
        ├── IOffImportJob.cs / OffImportJob.cs
        ├── OffDumpReader.cs
        └── OffProduct.cs / OffProductMapper.cs
```

> **Règle de rangement** : `Scheduling/` = le moteur, une seule fois. `Jobs/<NomDuJob>/` = un
> dossier par job. La purge RGPD (NTR-56) aura donc son propre `Jobs/RgpdPurge/`, sans se mélanger
> à l'import.

### Volet Remplissage — une chaîne de quatre maillons

```
OffDumpReader  ──►  OffProductMapper  ──►  OffProduct  ──►  OffImportJob
   (lire)              (traduire)          (transporter)      (ranger)
```

| Classe | Responsabilité unique |
|---|---|
| `OffDumpReader` | Télécharge le dump `.gz` et le décompresse **au fil de l'eau**, en livrant les lignes une par une. Le fichier n'est jamais chargé entièrement en mémoire. |
| `OffProductMapper` | Traduit une ligne JSON brute en objet exploitable : arrondit les valeurs, convertit les allergènes, **rejette** les produits inexploitables. Classe statique, sans état. |
| `OffProduct` | Simple porteur de données (record). Aucune logique. |
| `IOffImportJob` | Contrat — permet à Hangfire de résoudre le job via l'injection de dépendances. |
| `OffImportJob` | Orchestre : lit, fait traduire, regroupe par lots, décide créer/mettre à jour, persiste. |

### Volet Supervision — deux classes

| Classe | Responsabilité unique |
|---|---|
| `JobMonitoringService` | Répond « quels jobs sont planifiés, quand ont-ils tourné, quand repassent-ils ? » via une requête SQL sur `hangfire.hash`. |
| `HangfireAdminAuthorizationFilter` | Garde-barrière du tableau de bord `/hangfire` : authentifié **et** rôle `admin`. |

---

## 3. Le parcours d'un produit — du fichier OFF à la base

### Étape par étape

1. **Déclenchement** — Hangfire appelle `OffImportJob.RunAsync()` à 03h00 UTC.
2. **Lecture** — `OffDumpReader` ouvre le flux HTTP, décompresse le gzip, et rend chaque ligne
   JSON (un produit = une ligne, format JSONL).
3. **Traduction** — chaque ligne passe par `OffProductMapper.TryMap()` :
   - extraction de `code`, `product_name`, `nutriments`, `allergens_tags` ;
   - **arrondi** des macros au plus proche (`6.3 → 6`, `57.5 → 58`) — le modèle les stocke en entiers ;
   - **conversion des allergènes** via une table `en:milk → Allergen.Milk` (14 allergènes UE) ;
   - **retourne `null`** si le produit est inexploitable → il est compté « ignoré » et **la boucle continue**.
4. **Accumulation** — les produits valides s'empilent jusqu'à atteindre la taille de lot (1 000 par défaut).
5. **Persistance du lot** (`PersistBatchAsync`) :
   - dédoublonnage par code-barres à l'intérieur du lot ;
   - **une seule requête** demande quels codes existent déjà (`GetByOffIdsAsync`) ;
   - existe → `FoodItem.UpdateFromImport(...)` ; sinon → nouveau `FoodItem` ajouté au lot ;
   - `AddRangeAsync` puis `SaveChangesAsync` — une écriture groupée.
6. **Bilan** — en fin de parcours, journalisation : *« X produits importés, Y ignorés »*.
7. **Invalidation du cache** — si au moins un produit a été importé, toutes les recherches en
   cache sont supprimées (`InvalidateAllSearchesAsync`) : elles portaient sur l'ancien catalogue.
   Voir `systemes/aliments/workflow-cache-recherche.md`.

### Ce qui fait rejeter un produit

| Cas | Comportement |
|---|---|
| JSON invalide | ignoré, l'import continue |
| Code-barres ou nom absent / vide | ignoré — inexploitable par le catalogue |
| Valeur nutritionnelle négative | ignoré — donnée aberrante |
| Nutriments absents | **accepté**, valeurs à 0 |
| Allergène inconnu du référentiel | **accepté**, l'allergène seul est ignoré |

> Principe directeur : **une ligne défectueuse ne doit jamais interrompre un import de 3 millions
> de produits.** Seule une panne réseau propage une exception — et déclenche alors le retry Hangfire.

---

## 4. Le parcours de la supervision — de l'exécution à l'API

```
OffImportJob s'exécute
        │
        ▼
Hangfire écrit l'état dans PostgreSQL (schéma hangfire)
        │
        ▼
JobMonitoringService lit hangfire.hash (clé recurring-job:import-off)
        │
        ▼
AdminService.GetSystemHealthAsync() assemble la réponse
        │
        ▼
GET /admin/system/health → { foodItemsCount, lastImportAt, hangfireJobs[] }
```

**Pourquoi `hangfire.hash` et non l'historique brut** — les tables `job`/`state` contiennent
l'historique des exécutions, mais ne donnent **ni la prochaine exécution planifiée, ni la liste
des jobs récurrents**. Les deux vivent dans `hash`, sous la clé `recurring-job:<id>`.

**Réponse type** (job enregistré, jamais exécuté) :

```json
{
  "foodItemsCount": 5,
  "lastImportAt": null,
  "hangfireJobs": [
    { "jobName": "import-off", "lastRun": null, "nextRun": "2026-07-24T03:00:00Z", "status": "Scheduled" }
  ]
}
```

**Le nom du job est un contrat.** `AdminService` dérive `lastImportAt` en cherchant le job nommé
`import-off` (constante `IJobMonitoringService.ImportOffJobName`). Enregistrer le job sous un
autre nom ferait rester `lastImportAt` à `null` **en permanence, sans aucune erreur visible**.

---

## 5. Les décisions et leurs raisons

| Décision | Raison |
|---|---|
| **Traitement par lots** (1 000, configurable) | 3 M+ de produits traités un par un = autant d'allers-retours SQL. Le lot ramène cela à une lecture et une écriture groupées. |
| **Un scope DI neuf par lot** | Sans cela, le `ChangeTracker` d'EF Core accumule tous les produits en mémoire jusqu'à saturation. Le scope est détruit après chaque lot → **mémoire constante**, quelle que soit la taille du dump. |
| **Lecture en streaming** | Le dump pèse plusieurs Go compressés : il ne peut pas être chargé en mémoire. |
| **Produits invalides ignorés** | Un import massif doit être tolérant aux données sales, sinon un seul produit corrompu annule la nuit entière. |
| **Arrondi des macros** | Le modèle `FoodItem` stocke les macros en entiers ; OFF publie des décimaux. Perte assumée et documentée. |
| **Allergènes inconnus ignorés** | OFF publie des tags hors des 14 allergènes UE. Le produit reste importé, seul le tag inconnu est écarté. |
| **Identifiant `import-off`** | Le contrat `IJobMonitoringService` fait foi (et non `off-import`, qui figurait dans une version antérieure de la doc). |
| **URL du dump en configuration** | Section `OpenFoodFacts` — jamais d'URL en dur, comme Redis ou la chaîne de connexion. |
| **Invalidation du cache en fin d'import** | Le catalogue vient de changer : les recherches mémorisées portent sur des données périmées. Sans cela, une entrée créée juste avant 03h00 serait servie près de 24 h avec l'ancien catalogue. Déclenchée **seulement si au moins un produit a été importé**. |

---

## 6. État de confiance — ce qui est vérifié, ce qui ne l'est pas

| Élément | Niveau de vérification |
|---|---|
| `OffProductMapper` | ✅ **19 tests automatisés** — arrondi, allergènes (connus / inconnus / doublons), rejets, nombres en texte |
| Routes `/admin/**` | ✅ vérifié manuellement — passées de 500 à 200 |
| Enregistrement et supervision du job | ✅ vérifié manuellement — `import-off` visible avec sa prochaine exécution |
| `JobMonitoringService` | ⚠️ tests automatisés **en attente** (nécessite une base réelle) — stubs en place |
| `OffImportJob` | ⚠️ **jamais exécuté sur un dump réel** — la logique n'a pas encore avalé de vrai fichier |
| `OffDumpReader` | ⚠️ non testé (dépend du réseau) |

> Le risque résiduel est concentré sur l'**import réel** : la mécanique est en place et raisonnée,
> mais elle n'a pas encore été éprouvée de bout en bout sur un fichier Open Food Facts.

---

## 7. Configuration

```json
"OpenFoodFacts": {
  "DumpUrl": "https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz",
  "BatchSize": 1000
}
```

---

## 8. Où creuser

| Sujet | Document |
|---|---|
| Le moteur de jobs (Hangfire, dashboard, tables) | `briques/hangfire.md` |
| La source de données (pourquoi un dump, quels champs) | `systemes/aliments/source-open-food-facts.md` |
| Le besoin métier et le périmètre | `systemes/aliments/mise-a-disposition.md` |
| La recherche d'aliments qui consomme le catalogue | `systemes/aliments/index.md` |
| Le cache des recherches, invalidé en fin d'import | `systemes/aliments/workflow-cache-recherche.md` |
| L'endpoint de santé système | `systemes/administration/index.md` |
