# Environnement local et production

> Ce document couvre l'infrastructure nécessaire pour faire tourner le projet en local et en production.
> Il complète [Keycloak Admin API — Connexion et opérations](keycloak-admin.md) (Admin API RGPD) et [Hangfire — moteur de jobs récurrents](hangfire.md) (jobs planifiés).

---

## Section 1 — Environnement de développement local (docker-compose)

> **Réécrit le 2026-07-23** d'après le code réel — la version précédente décrivait une
> arborescence `infra/dev/` et une base Keycloak séparée qui n'ont jamais existé.

### Architecture locale

Trois services conteneurisés, l'API tournant **sur le poste** (`dotnet run`) et s'y connectant
via `localhost` :

```
        dotnet run (host, port 5099)
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
 PostgreSQL      Redis        Keycloak
localhost:5445  :6336      :8778 (admin)
```

**Les ports externes sont volontairement décalés** (5445, 6336, 8778) pour ne pas entrer en
conflit avec des instances déjà présentes sur le poste. Les ports internes aux conteneurs restent
standards (5432, 6379, 8080).

Keycloak tourne en `start-dev` avec une base H2 embarquée et **sans volume** : le realm est
réimporté à chaque recréation du conteneur, ce qui garantit un environnement reproductible.

### Fichiers réels

```
nutrition-api/
├── docker-compose.yml            ← 3 services + profil « full »
├── Dockerfile.migrations         ← conteneur one-shot des migrations EF Core
├── seed-dev.sql                  ← données métier de développement
├── keycloak/
│   └── realm-export.json         ← realm, client, rôles, comptes de test
├── scripts/
│   ├── lib.sh                    ← fonctions partagées, sourcé par les autres
│   ├── dev-up.sh                 ← démarre les services, migre, seede
│   ├── dev-down.sh               ← arrête (conserve les données)
│   ├── dev-reset.sh              ← remet à zéro (supprime les volumes)
│   ├── docker-up.sh              ← stack complète, API conteneurisée
│   └── test-integration.sh       ← même pile + tests de niveau 3
└── src/NutritionApi.Api/
    └── Dockerfile                ← image de l'API
```

> Il n'y a **ni fichier `.env`, ni dossier `infra/`** : les valeurs de développement sont écrites
> directement dans `docker-compose.yml` (elles ne sont pas des secrets) et la configuration de
> l'API vit dans `appsettings.Development.json` / `appsettings.Docker.json`.

#### `lib.sh` — ce que les scripts partagent

`lib.sh` n'est jamais exécuté directement : les autres scripts le **sourcent** en première ligne.
C'est ce qui explique qu'ils se ressemblent autant, et pourquoi ils échouent tous de la même façon.

| Fonction | Rôle |
|---|---|
| `require_docker` | vérifie que le démon répond, avec un message explicite plutôt qu'une erreur brute |
| `require_dotnet_ef` | vérifie la présence de l'outil EF Core, et rappelle la commande d'installation |
| `wait_healthy <conteneur> <timeout>` | attend le passage à `healthy`, échoue en nommant la commande de diagnostic |
| `info` `success` `warn` `fail` | sortie uniforme, **couleurs désactivées** quand la sortie n'est pas un terminal — les journaux CI restent lisibles |

Il pose aussi `set -euo pipefail` et calcule `REPO_ROOT`, ce qui rend les scripts appelables depuis
n'importe quel répertoire.

`wait_healthy` mérite l'attention : c'est elle qui rend les scripts fiables. Sans elle, `dev-up.sh`
appliquerait les migrations avant que PostgreSQL n'accepte les connexions. Les tests de niveau 3
reprennent la même logique côté C#, dans `DockerContainer.WaitHealthyAsync`.

### Démarrage — la voie normale

```bash
./scripts/dev-up.sh
```

Le script enchaîne tout : démarrage des trois services, **attente effective des healthchecks**,
application des migrations EF Core, puis chargement de `seed-dev.sql`. Il affiche en fin
d'exécution les accès et les comptes de test.

```bash
dotnet run --project src/NutritionApi.Api      # API sur http://localhost:5099
```

| Script | Effet |
|---|---|
| `./scripts/dev-up.sh` | Démarre, migre, seede — **conserve** les données existantes |
| `./scripts/dev-down.sh` | Arrête les services, **conserve** les volumes |
| `./scripts/dev-reset.sh` | Arrête et **supprime les volumes** — repart d'une base vierge |
| `./scripts/docker-up.sh` | Stack complète avec l'API conteneurisée (`--rebuild` pour forcer le build) |

### Les deux modes d'exécution

| Mode | Commande | Port API | Configuration |
|---|---|---|---|
| **Dev** (API sur le poste) | `dev-up.sh` + `dotnet run` | **5099** | `appsettings.Development.json` |
| **Docker** (API conteneurisée) | `docker-up.sh` | **5100** | `appsettings.Docker.json` (`ASPNETCORE_ENVIRONMENT=Docker`) |

Le mode Docker s'appuie sur le **profil `full`** de docker-compose, qui ajoute deux services :
`migrations` (conteneur one-shot) puis `api`, laquelle ne démarre qu'une fois **les migrations
terminées avec succès** et Redis et Keycloak déclarés sains.

> Choisir l'environnement Postman correspondant au mode utilisé — un port erroné donne des
> requêtes qui n'aboutissent pas.

### Accès et comptes de test

| Service | Accès |
|---|---|
| **API** | `http://localhost:5099` (dev) · `http://localhost:5100` (Docker) |
| **Swagger UI** | `http://localhost:5099/swagger` — spec brute sur `/swagger/v1/swagger.json` |
| **Dashboard Hangfire** | `http://localhost:5099/hangfire` — **rôle `admin` requis** |
| PostgreSQL | `localhost:5445` — base `nutrition_dev`, `postgres` / `postgres` |
| Redis | `localhost:6336` |
| Keycloak | `http://localhost:8778` — console admin `admin` / `admin` |

> **Swagger et le dashboard Hangfire sont des pages web** : ils s'ouvrent au navigateur, pas dans
> Postman. La collection ne contient d'eux que des vérifications de statut (accès refusé à un
> non-admin, spec bien générée) — leur contenu n'y est pas exploitable.
>
> Swagger est monté **uniquement hors production** (`if (!app.Environment.IsProduction())` dans
> `Program.cs`). Le dashboard Hangfire, lui, existe dans tous les environnements, protégé par
> `HangfireAdminAuthorizationFilter`.

| Compte | Rôle Keycloak | Abonnement |
|---|---|---|
| `test-user` | `user` | Free |
| `test-pro` | `user` | Pro |
| `test-admin` | `admin` | Free |

Mot de passe commun : `test`. Ces comptes sont définis dans `keycloak/realm-export.json` et
leurs profils correspondants sont créés par `seed-dev.sql`.

### Points d'attention

**Les migrations ne sont jamais appliquées au démarrage de l'application.** Elles passent par
`dotnet ef database update` (via `dev-up.sh`) ou par le conteneur `migrations`. Raison : en
production, plusieurs pods les appliqueraient simultanément, un échec deviendrait une panne de
démarrage, et l'application conserverait des privilèges DDL en permanence.

**`KC_HOSTNAME` est figé sur `http://localhost:8778`.** Sans cela, Keycloak déduit l'issuer des
jetons de l'en-tête `Host` : un jeton obtenu depuis le poste porterait `localhost:8778` alors que
l'API conteneurisée attendrait `keycloak:8080`, et la validation échouerait.
`KC_HOSTNAME_BACKCHANNEL_DYNAMIC` laisse les appels internes (récupération des clés de signature)
utiliser le nom de service Docker.

**Le healthcheck Keycloak interroge le port 9000**, pas le 8080 : c'est là qu'est exposé
`/health/ready`. L'image ne contenant ni `curl` ni `wget`, le test passe par `/dev/tcp` de bash.

**Versions d'images figées** (`postgres:16`, `redis:7`, `keycloak:26.0`) — à maintenir alignées
avec les manifests K3s de production. C'est le **seul** alignement exigé entre les environnements.

### Données de développement

`seed-dev.sql` charge des données métier (utilisateurs correspondant aux comptes Keycloak,
aliments, plans). Il est rejoué à chaque `dev-up.sh`.

Le catalogue `FoodItem` réel est alimenté par le job d'import Open Food Facts — voir
[Workflow — Mise à disposition des aliments](../systemes/aliments/workflow-import.md).


## Section 2 — Production (K3s)

> 🔲 **Cible, non réalisée.** Aucun déploiement n'a encore eu lieu : les manifests K8s n'existent
> pas dans le dépôt. Cette section décrit la conception visée. Les seuls éléments déjà présents
> sont les deux Dockerfile (API et migrations).

### Périmètre de ce projet

PostgreSQL, Keycloak et Redis sont déployés et gérés par un **projet d'infrastructure séparé** (K3s). Ce projet contient uniquement :
- Le `Dockerfile` pour builder l'image de l'API
- La configuration de connexion de l'API vers les services K3s
- Les manifests K8s de l'API elle-même (Deployment + Service + Ingress)

```
K3s cluster (projet infra séparé)
├── PostgreSQL
├── Keycloak
└── Redis
        ↑
  nutrition-api (Deployment — ce projet)
```

---

### Fichiers

> **État au 2026-07-23** — le `Dockerfile` **existe déjà** ; les manifests K8s restent à créer.

```
nutrition-api/
├── src/NutritionApi.Api/Dockerfile   ✅ existe (image de l'API)
├── Dockerfile.migrations             ✅ existe (migrations one-shot)
└── infra/                            🔲 à créer
    └── k8s/
        ├── configmap.yaml
        ├── secret.yaml.example
        ├── deployment.yaml
        ├── service.yaml
        └── ingress.yaml
```

> **`.gitignore` — ajouter :** `infra/k8s/secret.yaml` (garder uniquement `secret.yaml.example`)

---

### `src/NutritionApi.Api/Dockerfile` — existant

Le Dockerfile réel diffère de l'ébauche initiale : il **existe déjà**, se trouve **dans le
dossier du projet API** (et non à la racine), et le nom du projet est `NutritionApi.Api` — pas
`NutritionApi.API`.

```dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS base
USER $APP_UID
WORKDIR /app
EXPOSE 8080
EXPOSE 8081

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
ARG BUILD_CONFIGURATION=Release
WORKDIR /src
COPY ["src/NutritionApi.Api/NutritionApi.Api.csproj", "src/NutritionApi.Api/"]
COPY ["src/NutritionApi.Application/NutritionApi.Application.csproj", "src/NutritionApi.Application/"]
COPY ["src/NutritionApi.Domain/NutritionApi.Domain.csproj", "src/NutritionApi.Domain/"]
COPY ["src/NutritionApi.Infrastructure/NutritionApi.Infrastructure.csproj", "src/NutritionApi.Infrastructure/"]
RUN dotnet restore "src/NutritionApi.Api/NutritionApi.Api.csproj"
COPY . .
RUN dotnet build "src/NutritionApi.Api/NutritionApi.Api.csproj" -c $BUILD_CONFIGURATION -o /app/build

FROM build AS publish
ARG BUILD_CONFIGURATION=Release
RUN dotnet publish "src/NutritionApi.Api/NutritionApi.Api.csproj" -c $BUILD_CONFIGURATION -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "NutritionApi.Api.dll"]
```

> Le **contexte de build est la racine du dépôt**, pas le dossier du Dockerfile — les chemins
> `COPY` partent de `src/`. C'est ainsi que `docker-compose.yml` l'invoque
> (`context: .` + `dockerfile: src/NutritionApi.Api/Dockerfile`).

> **Les migrations ont leur propre image** (`Dockerfile.migrations`), exécutée en conteneur
> one-shot avant le démarrage de l'API — l'application n'applique jamais les migrations
> elle-même.

---

### `infra/k8s/configmap.yaml` — variables non-sensibles

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nutrition-api-config
  namespace: nutrition
data:
  ASPNETCORE_ENVIRONMENT: Production
  Keycloak__Authority: "https://<keycloak-k3s-domain>/realms/nutrition"
  Keycloak__Realm: nutrition
  Keycloak__ClientId: nutrition-api
  Keycloak__ServiceClientId: nutrition-api-service
  Keycloak__AdminBaseUrl: "https://<keycloak-k3s-domain>"
  Redis__ConnectionString: "<redis-service-k3s>:6379"
```

> **La clé est bien `Redis__ConnectionString`** — le code lit `configuration["Redis:ConnectionString"]`
> (`Infrastructure/DependencyInjection.cs`), pas la section `ConnectionStrings`. Avec un autre nom,
> la valeur est `null` et l'API échoue au démarrage sur `ConfigurationOptions.Parse`.
> *(Corrigé après relecture du code — la clé documentée précédemment était erronée.)*

---

### `infra/k8s/secret.yaml.example` — structure (valeurs vides, committé)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: nutrition-api-secret
  namespace: nutrition
type: Opaque
stringData:
  ConnectionStrings__NutritionDb: ""    # Host=<pg-k3s>;Port=5432;Database=nutrition;Username=...;Password=...
  Keycloak__ServiceClientSecret: ""     # secret du client nutrition-api-service sur Keycloak K3s
```

**Création du secret réel (CLI uniquement — jamais committé) :**

```bash
kubectl create secret generic nutrition-api-secret \
  --namespace=nutrition \
  --from-literal=ConnectionStrings__NutritionDb="Host=<pg-k3s>;Port=5432;Database=nutrition;Username=...;Password=..." \
  --from-literal=Keycloak__ServiceClientSecret="<secret>"
```

---

### `infra/k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nutrition-api
  namespace: nutrition
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nutrition-api
  template:
    metadata:
      labels:
        app: nutrition-api
    spec:
      containers:
        - name: nutrition-api
          image: <registry>/nutrition-api:latest
          ports:
            - containerPort: 8080
          envFrom:
            - configMapRef:
                name: nutrition-api-config
            - secretRef:
                name: nutrition-api-secret
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 10
```

> ✅ **Livré le 2026-08-02 — NTR-88.** Les deux points de terminaison existent, le `readinessProbe`
> ci-dessus est donc opérant.
>
> Le chemin de la readiness est bien `/health/ready` (état des dépendances) et non `/health`
> (l'application répond).
>
> ⚠️ **Ne jamais brancher la `livenessProbe` sur `/health/ready`.** Une instance qui attend ses clés
> de signature serait tuée au lieu de patienter, et l'on retrouverait la boucle de redémarrage que le
> découpage en deux sondes supprime précisément. La vivacité vise `/health`, qui ne consulte rien.
>
> Prévoir en plus un `startupProbe` sur `/health` : il couvre le démarrage à froid sans gonfler
> l'`initialDelaySeconds` de la vivacité, qui s'appliquerait sinon toute la vie du pod. Budget mesuré
> lors d'un essai : **175 secondes** pour qu'une instance démarrée sans Keycloak redevienne prête
> après le retour de celui-ci, l'essentiel étant l'import du realm.

---

### `infra/k8s/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nutrition-api-service
  namespace: nutrition
spec:
  selector:
    app: nutrition-api
  ports:
    - port: 80
      targetPort: 8080
```

---

### `infra/k8s/ingress.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nutrition-api-ingress
  namespace: nutrition
  annotations:
    kubernetes.io/ingress.class: traefik    # K3s utilise Traefik par défaut
spec:
  tls:
    - hosts:
        - api.nutrition.example.com
      secretName: nutrition-api-tls
  rules:
    - host: api.nutrition.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nutrition-api-service
                port:
                  number: 80
```

---

### Premier déploiement manuel (vérification)

```bash
# Prérequis : kubectl configuré sur le cluster K3s + secrets créés manuellement

kubectl apply -f infra/k8s/configmap.yaml
kubectl apply -f infra/k8s/deployment.yaml
kubectl apply -f infra/k8s/service.yaml
kubectl apply -f infra/k8s/ingress.yaml

# Vérifier
kubectl get pods -n nutrition
kubectl logs -n nutrition deployment/nutrition-api
```

Ce déploiement initial est manuel. À partir du suivant, GitHub Actions prend le relais (voir Section 3).

---

## Section 3 — CI/CD GitHub Actions (déploiement automatique sur K3s)

> 🔲 **Cible, non réalisée** pour la partie déploiement. Les workflows de test existent et
> tournent ; les étapes de build d'image, de publication et de `kubectl` restent **commentées**
> dans `ci-deploy.yml`, faute de cluster et de registre.

### Workflows réellement présents

```
.github/workflows/
├── ci-pr.yml            ✅ PR vers dev   — 3 jobs : niveaux 1-2, niveau 3, couverture fusionnée
├── ci-release.yml       ✅ PR vers main  — build + tests + couverture + rapport PR
├── ci-deploy.yml        ⚠️ PR vers prod  — build Release ; déploiement encore commenté
└── release-please.yml   ✅ push main     — tag vX.Y.Z + CHANGELOG
```

> `ci-pr.yml` n'a **aucune définition de service** propre : son job `integration-tests` appelle
> `./scripts/test-integration.sh`, qui monte le `docker-compose.yml` du projet. C'est délibéré — le
> niveau 3 doit éprouver la configuration Docker du dépôt, pas celle du workflow. Voir
> [Écrire un test de niveau 3](../qualite/tests-niveau-3.md).

> Son troisième job, `coverage`, attend les deux autres, fusionne leurs rapports et exécute
> `./scripts/check-coverage.sh`. C'est ce contrôle qui fait échouer la pull request sur la
> couverture ; les seuils sont déclarés dans `tests/coverage.runsettings`, seule source.
> `ci-unit.yml` et `ci-integration.yml` ont été réunis dans ce fichier le 2026-08-02 (NTR-168) :
> deux workflows sur le même événement ne pouvaient pas s'attendre, donc aucun ne pouvait produire
> un chiffre de couverture unique.

> Il n'existe **pas** de `deploy.yml` : le déploiement est prévu dans `ci-deploy.yml`, déclenché
> par la transition `dev → prod` (et non par un push sur `main`).

### Vue d'ensemble de la cible

Le déploiement, une fois activé, suivra :

```
PR dev → prod
  → build image Docker
  → push sur le registre de conteneurs
  → kubectl set image sur le cluster K3s
  → rollout status (succès ou rollback)
```

> Le détail des transitions de branches et des workflows associés vit dans le `CONTRIBUTING.md`
> du dépôt `nutrition-api` — source de vérité sur ce point.

---

### Étape 1 — Configuration serveur (une seule fois, avant le premier déploiement automatique)

#### 1a. Créer un Service Account K3s dédié au déploiement

Sur le serveur K3s, créer un compte de service limité au namespace `nutrition` :

```bash
# Sur le serveur K3s
kubectl create serviceaccount github-actions-deployer -n nutrition

kubectl create rolebinding github-actions-deployer-binding \
  --clusterrole=edit \
  --serviceaccount=nutrition:github-actions-deployer \
  --namespace=nutrition
```

> `clusterrole=edit` donne le droit de mettre à jour les Deployments dans `nutrition` sans accès cluster-admin.

#### 1b. Extraire le kubeconfig du Service Account

```bash
# Récupérer le token du Service Account
TOKEN=$(kubectl create token github-actions-deployer -n nutrition --duration=87600h)

# Récupérer le CA et le serveur
CA=$(kubectl config view --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')
SERVER=$(kubectl config view --raw -o jsonpath='{.clusters[0].cluster.server}')

# Construire le kubeconfig minimal
cat <<EOF > kubeconfig-github-actions.yaml
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: ${CA}
    server: ${SERVER}
  name: k3s
contexts:
- context:
    cluster: k3s
    user: github-actions-deployer
    namespace: nutrition
  name: nutrition
current-context: nutrition
users:
- name: github-actions-deployer
  user:
    token: ${TOKEN}
EOF

# Encoder en base64 pour GitHub Secrets
base64 -w 0 kubeconfig-github-actions.yaml
# → copier la sortie dans le secret GitHub KUBECONFIG_B64

# Supprimer le fichier local immédiatement
rm kubeconfig-github-actions.yaml
```

#### 1c. Ajouter les secrets dans le dépôt GitHub

Dans `GitHub → Settings → Secrets and variables → Actions` :

| Secret | Valeur |
|---|---|
| `KUBECONFIG_B64` | Sortie base64 de l'étape 1b |

> `GITHUB_TOKEN` est fourni automatiquement par GitHub Actions — pas besoin de le créer. Il suffit pour pousser sur GHCR.

#### 1d. Activer GHCR pour le dépôt

Dans `GitHub → Settings → Packages` : s'assurer que le dépôt a accès à GitHub Container Registry. Par défaut c'est activé — aucune configuration manuelle requise.

#### 1e. Vérifier que le namespace et les secrets K3s existent

```bash
kubectl get namespace nutrition
kubectl get secret nutrition-api-secret -n nutrition
kubectl get secret nutrition-api-tls -n nutrition    # certificat TLS pour l'Ingress
```

Si l'un de ces éléments manque, se référer à la Section 2 pour les créer avant de lancer le pipeline.

---

### Étape 2 — Workflow GitHub Actions

#### `.github/workflows/deploy.yml`

```yaml
name: Build & Deploy

on:
  push:
    branches:
      - main

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/nutrition-api

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write     # nécessaire pour pousser sur GHCR

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

      - name: Setup kubectl
        uses: azure/setup-kubectl@v3

      - name: Configure kubeconfig
        run: |
          mkdir -p $HOME/.kube
          echo "${{ secrets.KUBECONFIG_B64 }}" | base64 -d > $HOME/.kube/config
          chmod 600 $HOME/.kube/config

      - name: Deploy to K3s
        run: |
          kubectl set image deployment/nutrition-api \
            nutrition-api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
            -n nutrition
          kubectl rollout status deployment/nutrition-api -n nutrition --timeout=120s

      - name: Verify deployment
        run: kubectl get pods -n nutrition
```

---

### Étape 3 — Pipeline CI tests (build + tests sur PR)

> Distinct du pipeline de déploiement — se déclenche sur chaque Pull Request avant merge.
> Fichiers présents dans le repo `nutrition-api`.

```
.github/workflows/
├── ci-pr.yml            PR vers dev
├── ci-release.yml       PR vers main
├── ci-deploy.yml        PR vers prod
└── release-please.yml   push sur main
```

> ⚠️ Le fichier `ci.yml` ci-dessous est l'**ébauche initiale**, conservée à titre de référence.
> Les workflows réellement en place sont ceux listés au-dessus, différenciés par transition de
> branche — voir `CONTRIBUTING.md`.

#### `.github/workflows/ci.yml` (ébauche initiale)

```yaml
name: CI

on:
  pull_request:
    branches:
      - main

jobs:
  build-and-test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: nutrition_test
          POSTGRES_USER: nutrition_user
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-retries 5

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup .NET 10
        uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '10.x'

      - name: Restore
        run: dotnet restore

      - name: Build
        run: dotnet build --no-restore --configuration Release

      - name: Tests unitaires
        run: dotnet test --no-build --configuration Release --filter "Category=Unit" --logger "trx;LogFileName=unit-tests.trx"

      - name: Tests intégration
        env:
          ConnectionStrings__NutritionDb: "Host=localhost;Port=5432;Database=nutrition_test;Username=nutrition_user;Password=test_password"
        run: dotnet test --no-build --configuration Release --filter "Category=Integration" --logger "trx;LogFileName=integration-tests.trx"

      - name: Publier les résultats de tests
        uses: dorny/test-reporter@v1
        if: always()
        with:
          name: Résultats tests
          path: '**/*.trx'
          reporter: dotnet-trx
```

> **docker-compose vs service PostgreSQL GitHub Actions** — les tests d'intégration de niveau 3 s'appuient sur le `docker-compose.yml` du projet (PostgreSQL, Redis, Keycloak), réutilisé en CI. Le bloc `services:` du workflow fait donc double emploi : monter les trois services via docker-compose et pointer la configuration dessus. Décision d'architecture du 2026-07-21 — voir [Niveaux de tests — définitions et périmètres](../qualite/niveaux-de-tests.md).

---

### Ordre global — quand faire quoi

| Étape | Quand | État |
|---|---|---|
| Workflows de tests (`ci-pr`, `ci-release`) | Dès le premier commit sur une branche feature | ✅ en place |
| Intégration externe et couverture fusionnée (jobs de `ci-pr`) | Avec les tests de niveau 3 — NTR-28, puis NTR-168 | ✅ en place |
| `Dockerfile` de l'API et des migrations | Après que l'API tourne localement | ✅ en place |
| Manifests K8s (`infra/k8s/`) | Avant le premier déploiement | 🔲 à créer |
| Section 2 — premier déploiement manuel | Après les manifests, pour vérifier qu'ils sont corrects | 🔲 |
| Activation du déploiement dans `ci-deploy.yml` | Après le premier déploiement manuel validé | 🔲 étapes commentées |
| PR `dev → prod` | Déploiement automatique via le pipeline | 🔲 |

> Les références `STORY-040` / `STORY-041` de la version initiale de ce document ne correspondent
> à aucun ticket : le projet est suivi dans Jira sous le préfixe `NTR` (epic **NTR-80 — DevOps &
> Environnement**).

---

*Références : [Keycloak Admin API — Connexion et opérations](keycloak-admin.md) (Admin API RGPD) · [Hangfire — moteur de jobs récurrents](hangfire.md) (jobs Hangfire)*
