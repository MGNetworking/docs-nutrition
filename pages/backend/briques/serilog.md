# Serilog — journalisation structurée

**Ajouté le :** 2026-08-02
**Type :** Interne
**Ticket :** NTR-137

> **Portée de ce document : Serilog, et lui seul.**
> ➜ Pour ce que l'observabilité cherche à obtenir dans son ensemble — journaux, métriques et
> traces —, lire [Observabilité](../systemes/plateforme/observabilite.md).

---

## 1. Le modèle mental — trois étages

Sans cette distinction, le choix « ASP.NET Core ou Serilog » paraît être une alternative. Ce n'en
est pas une : les deux occupent des étages différents.

| Étage | Rôle | Ce qui l'occupe ici |
|---|---|---|
| **Abstraction** | `_logger.LogWarning(…)` dans le code. Ne fait rien, transmet. | `ILogger` d'ASP.NET Core — **inchangé** |
| **Fournisseur** | Reçoit le message, le met en forme, l'écrit. | **Serilog**, en remplacement de ceux d'ASP.NET Core |
| **Destination** | Où le texte atterrit. Serilog les appelle des *sinks*. | la console, et rien d'autre pour l'instant |

**Conséquence pratique : aucun code applicatif ne connaît Serilog.** Les 19 appels de
journalisation du projet passent par `ILogger` et ne changeraient pas si Serilog était retiré.

## 2. Pourquoi Serilog, et ce qui a été écarté

Le mécanisme d'ASP.NET Core sait produire du JSON en une ligne de configuration. Il aurait suffi.

| Ce qui a fait pencher pour Serilog | |
|---|---|
| Les *sinks* | ASP.NET Core n'écrit que sur la console et le débogueur. Serilog atteint fichier, Seq, Elasticsearch, base de données. |
| L'affinité avec Seq | Seq, l'un des trois candidats du §5 de l'epic, est écrit par l'auteur de Serilog. Retenir Seq n'entraînerait aucune réécriture. |
| La configuration par fichier | Niveaux, filtres et destinations se règlent dans `appsettings.json`, sans recompiler. |
| L'usage | C'est la bibliothèque de journalisation tierce dominante dans l'écosystème .NET d'entreprise. |

> **Seq n'est pas une obligation.** C'est un sink parmi des dizaines. Serilog sans backend écrit sur
> la console, exactement comme le ferait le mécanisme intégré.

**Ce qui a été écarté :** le sink fichier avec rotation quotidienne. Il survivrait au redémarrage
d'un pod, ce qui répond en partie au problème central du §2 de l'epic. Mais écrire les journaux
dans un fichier à l'intérieur d'un pod va contre la pratique établie sous Kubernetes — sortie
standard, puis collecteur —, oblige à gérer un volume, une rotation et un nettoyage, et ne rend pas
les journaux requêtables pour autant.

## 3. Configuration

Tout est dans la section `Serilog`. **La section `Logging` n'est plus lue** : elle a été supprimée
pour qu'aucun réglage n'y soit fait sans effet.

| Clé | Rôle |
|---|---|
| `MinimumLevel:Default` | Niveau plancher — `Information` |
| `MinimumLevel:Override` | Niveau par catégorie. `Microsoft.EntityFrameworkCore.Database.Command` est rabaissé à `Warning` : en `Information`, EF Core journalise **chaque requête SQL** — verbeux et coûteux. |
| `WriteTo` | Les destinations. Une seule : la console. |
| `Enrich` | `FromLogContext`, qui fait remonter les propriétés attachées par les portées. |

**Production** — `CompactJsonFormatter` : une ligne JSON par entrée, requêtable.
**Développement** — un gabarit texte lisible, avec l'heure, le niveau, la catégorie et les propriétés.

## 4. Ce que porte chaque entrée

| Propriété | Origine |
|---|---|
| `@tr` — identifiant de trace | Serilog le capture **de lui-même** depuis l'activité en cours. C'est le même que celui des traces OpenTelemetry et que le `traceId` publié au client en cas d'erreur. |
| `@sp` — identifiant d'étape | idem |
| `UserId` | Ouvert en portée par `UserResolutionMiddleware`, seul endroit du pipeline à connaître l'identifiant applicatif |
| `SourceContext` | La classe qui a écrit l'entrée |

Les entrées écrites hors d'une requête HTTP — démarrage, services de fond — n'ont pas
d'identifiant de trace : elles n'appartiennent à aucune requête.

## 5. Ce qui n'est pas fait

| Sujet | Statut |
|---|---|
| Destination de collecte | **Non branchée** — le backend n'est pas arrêté, voir le §5 de l'epic |
| Conservation après redémarrage d'un pod | Non résolue — la console disparaît avec le conteneur |
| Portée `UserId` sur les requêtes anonymes | Sans objet — il n'y a pas d'utilisateur à nommer |

## 6. État de confiance

| Marque | Élément |
|---|---|
| ✅ | Serilog est bien le fournisseur actif, et ses entrées portent l'identifiant de trace — deux cas de niveau 2 |
| ⚠️ | La portée `UserId` **n'est pas éprouvée** : aucun code en aval du middleware ne journalise aujourd'hui, il n'y a donc aucune entrée sur laquelle la vérifier |
| ❌ | Le format JSON de production n'a pas été observé — le développement et les tests utilisent l'autre sortie |

## 7. Voir aussi

- [Observabilité](../systemes/plateforme/observabilite.md) — l'ensemble : journaux, métriques, traces
- [Exception Filter](../systemes/plateforme/exception-filter.md) — le `traceId` publié au client
- [Pipeline HTTP](../systemes/plateforme/pipeline-http.md) — `RequestLoggingMiddleware` et l'ordre des middlewares
