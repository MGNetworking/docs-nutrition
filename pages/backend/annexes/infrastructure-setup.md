# Infrastructure Setup — Développement local et Production

> Ce document couvre l'infrastructure nécessaire pour faire tourner le projet en local et en production.
> Il complète `infrastructure-keycloak-admin.md` (Admin API RGPD) et `infrastructure-hangfire.md` (jobs planifiés).

---

## Section 1 — Environnement de développement local (Docker Compose)

### Architecture locale

L'API ASP.NET Core tourne en dehors de Docker (`dotnet run`). Docker Compose fournit uniquement les dépendances :

```text
┌─────────────────────────────────────────────────────────┐
│  Docker Compose                                         │
│                                                         │
│  app-db (PostgreSQL 16)   ← base de données de l'API   │
│  keycloak-db (PostgreSQL 16) ← base de données KC      │
│  keycloak (Keycloak 24)   ← authentification            │
│  redis (Redis 7)          ← cache FoodItem              │
└─────────────────────────────────────────────────────────┘
         ↑
  dotnet run (ASP.NET Core) — lit .env pour se connecter
```

### Fichiers à créer

```text
nutrition-api/
└── infra/
    ├── dev/
    │   ├── docker-compose.yml      ← orchestration locale
    │   └── .env.example            ← modèle variables (committé)
    │   # .env                      ← vraies valeurs (non committé — dans .gitignore)
    └── keycloak/
        └── realm-export-dev.json   ← config realm + utilisateurs de test (committé)
```

> **`.gitignore` — ajouter :** `infra/dev/.env`

---

### `infra/dev/docker-compose.yml`

```yaml
version: '3.9'

services:

  app-db:
    image: postgres:16-alpine
    container_name: nutrition-app-db
    environment:
      POSTGRES_DB: nutrition
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - app-db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d nutrition"]
      interval: 10s
      retries: 5

  keycloak-db:
    image: postgres:16-alpine
    container_name: nutrition-keycloak-db
    environment:
      POSTGRES_DB: keycloak
      POSTGRES_USER: ${KC_DB_USER}
      POSTGRES_PASSWORD: ${KC_DB_PASSWORD}
    volumes:
      - keycloak-db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${KC_DB_USER} -d keycloak"]
      interval: 10s
      retries: 5

  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    container_name: nutrition-keycloak
    command: start-dev --import-realm
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://keycloak-db:5432/keycloak
      KC_DB_USERNAME: ${KC_DB_USER}
      KC_DB_PASSWORD: ${KC_DB_PASSWORD}
      KEYCLOAK_ADMIN: ${KC_ADMIN_USER}
      KEYCLOAK_ADMIN_PASSWORD: ${KC_ADMIN_PASSWORD}
      KC_HOSTNAME_STRICT: "false"
      KC_HTTP_ENABLED: "true"
    volumes:
      - ../keycloak/realm-export-dev.json:/opt/keycloak/data/import/realm-export-dev.json
    ports:
      - "8080:8080"
    depends_on:
      keycloak-db:
        condition: service_healthy

  redis:
    image: redis:7-alpine
    container_name: nutrition-redis
    ports:
      - "6379:6379"

volumes:
  app-db-data:
  keycloak-db-data:
```

---

### `infra/dev/.env.example`

```dotenv
# ── PostgreSQL — Base de données API ──────────────────────────────────────────
POSTGRES_USER=nutrition_user
POSTGRES_PASSWORD=

# ── PostgreSQL — Base de données Keycloak ────────────────────────────────────
KC_DB_USER=keycloak_user
KC_DB_PASSWORD=

# ── Keycloak Admin Console ────────────────────────────────────────────────────
KC_ADMIN_USER=admin
KC_ADMIN_PASSWORD=

# ── ASP.NET Core — Connection strings ────────────────────────────────────────
ConnectionStrings__NutritionDb=Host=localhost;Port=5432;Database=nutrition;Username=nutrition_user;Password=
ConnectionStrings__Redis=localhost:6379

# ── ASP.NET Core — Keycloak Auth ──────────────────────────────────────────────
Keycloak__Authority=http://localhost:8080/realms/nutrition
Keycloak__Realm=nutrition
Keycloak__ClientId=nutrition-api
Keycloak__ServiceClientId=nutrition-api-service
Keycloak__ServiceClientSecret=
Keycloak__AdminBaseUrl=http://localhost:8080
```

> Copier `.env.example` en `.env` et remplir les mots de passe. Ne jamais committer `.env`.

---

### `infra/keycloak/realm-export-dev.json`

Ce fichier est **généré par Keycloak** puis commité. Il contient :
- Configuration du realm `nutrition`
- Client `nutrition-api` (public, Authorization Code + PKCE)
- Client `nutrition-api-service` (confidential, service account, rôle `manage-users`)
- Rôles realm : `user`, `admin`
- Utilisateurs de test préconfigurés (hashes inclus à l'export)

**Utilisateurs de test inclus dans le realm export :**

| Email | Mot de passe | Rôle |
|---|---|---|
| `testuser@example.com` | `Test1234!` | `user` |
| `admin@example.com` | `Admin1234!` | `user` + `admin` |

**Générer le fichier (première fois) :**

```bash
# 1. Démarrer Keycloak sans import pour la configuration initiale
docker compose up keycloak-db keycloak -d
# Ouvrir http://localhost:8080 — configurer realm, clients, rôles, utilisateurs de test

# 2. Exporter le realm configuré
#    Admin Console → Realm settings → Action → Partial export
#    Cocher : "Export groups and roles" + "Export clients" + "Export users"
#    Sauvegarder sous infra/keycloak/realm-export-dev.json

# 3. Vérifier l'import automatique (depuis ce point, docker compose up charge le realm)
docker compose down && docker compose up -d
```

> Les futures modifications du realm (nouveau client, rôle) doivent être ré-exportées et le fichier mis à jour dans le repo.

---

### Démarrage complet

```bash
cd infra/dev
cp .env.example .env          # remplir les mots de passe
docker compose up -d          # démarre app-db, keycloak-db, keycloak, redis

# Vérifier que les 4 conteneurs sont healthy
docker compose ps

# Appliquer les migrations EF Core (depuis la racine du projet)
dotnet ef database update --project src/NutritionApi.Infrastructure

# Lancer l'API
dotnet run --project src/NutritionApi.API
```

Admin Console Keycloak : `http://localhost:8080` — identifiants définis dans `.env` (`KC_ADMIN_USER` / `KC_ADMIN_PASSWORD`).

---

### Seed de données PostgreSQL

Le schéma est créé par les migrations EF Core. Aucune donnée utilisateur n'est seedée (elle est créée via l'API avec les utilisateurs de test Keycloak).

Pour des FoodItems de démonstration (optionnel) : ajouter un script `infra/dev/seed-fooditems.sql` exécuté manuellement après `database update`. Le job Hangfire d'import OFF alimente la table `FoodItem` en production.

---

## Section 2 — Production (K3s)

### Périmètre de ce projet

PostgreSQL, Keycloak et Redis sont déployés et gérés par un **projet d'infrastructure séparé** (K3s). Ce projet contient uniquement :
- Le `Dockerfile` pour builder l'image de l'API
- La configuration de connexion de l'API vers les services K3s
- Les manifests K8s de l'API elle-même (Deployment + Service + Ingress)

```text
K3s cluster (projet infra séparé)
├── PostgreSQL  ←─┐
├── Keycloak    ←─┤  nutrition-api se connecte via variables d'environnement
└── Redis       ←─┘
        ↑
  nutrition-api (Deployment — ce projet)
```

---

### Fichiers à créer

```text
nutrition-api/
├── Dockerfile                              ← build de l'image API
└── infra/
    └── k8s/
        ├── configmap.yaml                  ← variables non-sensibles (committé)
        ├── secret.yaml.example             ← structure uniquement, valeurs vides (committé)
        ├── deployment.yaml                 ← Deployment nutrition-api
        ├── service.yaml                    ← Service ClusterIP
        └── ingress.yaml                    ← Ingress TLS
```

> **`.gitignore` — ajouter :** `infra/k8s/secret.yaml` (garder uniquement `secret.yaml.example`)

---

### `Dockerfile`

```dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS base
WORKDIR /app
EXPOSE 8080

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY ["src/NutritionApi.API/NutritionApi.API.csproj", "src/NutritionApi.API/"]
COPY ["src/NutritionApi.Application/NutritionApi.Application.csproj", "src/NutritionApi.Application/"]
COPY ["src/NutritionApi.Infrastructure/NutritionApi.Infrastructure.csproj", "src/NutritionApi.Infrastructure/"]
COPY ["src/NutritionApi.Domain/NutritionApi.Domain.csproj", "src/NutritionApi.Domain/"]
RUN dotnet restore "src/NutritionApi.API/NutritionApi.API.csproj"
COPY . .
RUN dotnet publish "src/NutritionApi.API/NutritionApi.API.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
ENTRYPOINT ["dotnet", "NutritionApi.API.dll"]
```

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
  ConnectionStrings__Redis: "<redis-service-k3s>:6379"
```

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
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 10
```

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

### Vue d'ensemble

Chaque push sur `main` déclenche le pipeline :

```
push main
  → build image Docker
  → push sur GitHub Container Registry (GHCR)
  → kubectl set image sur le cluster K3s
  → rollout status (succès ou rollback)
```

### Fichier créé dans ce projet

```text
.github/
└── workflows/
    └── deploy.yml     ← committé dans le repo
```

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
> Fichier créé dans le repo `nutrition-api`.

```text
.github/
└── workflows/
    ├── ci.yml        ← build + tests (PR)
    └── deploy.yml    ← déploiement (push main)
```

#### `.github/workflows/ci.yml`

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

> **Testcontainers vs service PostgreSQL GitHub Actions** — les tests d'intégration avec `Testcontainers` démarrent leur propre conteneur PostgreSQL. Si tu utilises Testcontainers, supprimer le bloc `services:` du workflow et retirer la variable `ConnectionStrings__NutritionDb` — Testcontainers gère la connexion lui-même.

---

### Ordre global — quand faire quoi

| Étape | Quand |
|---|---|
| `ci.yml` — pipeline tests | Dès le premier commit sur une branche feature |
| STORY-040 : Dockerfile + manifests K8s | Après que l'API tourne localement |
| Section 2 — premier déploiement manuel | Après STORY-040, pour vérifier que les manifests sont corrects |
| STORY-041 : `deploy.yml` | Après le premier déploiement manuel validé |
| Tout push sur `main` | Déploiement automatique via le pipeline |

---

*Références : `infrastructure-keycloak-admin.md` (Admin API RGPD) · `infrastructure-hangfire.md` (jobs Hangfire)*
