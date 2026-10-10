# 🚀 Flask Password Generator API - GitOps & Monitoring Project

This project demonstrates a production-ready **GitOps** architecture deployed on a local Kubernetes cluster (MicroK8s). It features a Python Flask API application managed dynamically using **Helm Charts** and **Argo CD**, alongside a comprehensive cluster monitoring stack powered by **Prometheus & Grafana**.

---

## 📂 Project Structure

```text
my-k8s-monitoring-project/
├── app.py                      # Flask API source code (includes health check & metrics endpoints)
├── requirements.txt            # Python dependencies (Flask, prometheus-client, etc.)
├── Dockerfile                  # Application containerization configuration for Kubernetes
├── argocd-admin-rights.yaml    # ClusterRoleBinding manifest granting cluster-admin access to Argo CD
│
├── 📂 argocd-setup/               # Infrastructure and cluster configuration files for Argo CD
│   ├── argocd-cm.yaml          # ConfigMap enabling unauthenticated UI access (Anonymous Access)
│   ├── argocd-ingress.yaml     # Traefik Ingress route mapping the cluster to http://argocd.local
│   ├── argocd-rbac-bypass.yaml # Internal RBAC policies for core Argo CD controllers
│   └── infrastructure-stack.yaml # Umbrella Application manifest for the cluster Monitoring Stack
│
├── 📂 helm-chart/                  # Generic, reusable Helm template infrastructure (The Recipe)
│   ├── Chart.yaml              # Chart metadata (Name, version, description)
│   ├── values.yaml             # Default foundational configuration variables
│   └── 📂 templates/              # Dynamic Kubernetes manifest templates
│       ├── deployment.yaml     # Specifies Pod settings, Docker image target, and Liveness probes
│       └── service.yaml        # Exposes the application internally within the cluster
│
└── 📂 environments/                # Target environment-specific configurations
    └── 📂 Dev/
        └── values-dev.yaml     # Overrides default values for the Dev environment (e.g., 1 replica)
```

---

## ⚙️ Core Components Overview

### 1. Application Layer (app.py & Dockerfile)
* **app.py**: A lightweight Python Flask backend exposing three distinct endpoints:
  * `/generate`: Dynamically generates secure, randomized passwords.
  * `/health`: Health check endpoint utilized by the Kubernetes cluster layer (`livenessProbe`).
  * `/metrics`: Exposes key application performance metrics natively in Prometheus format.
* **Dockerfile**: Packages the source code into a secure, minimal container utilizing `python:3.9-slim`.

### 2. Templating Layer (helm-chart/)
Standardizes Kubernetes deployment specifications to handle multiple target environments seamlessly.
* The `deployment.yaml` template includes native Prometheus scraping annotations (`prometheus.io/scrape: "true"`). This instructs the cluster's Prometheus server to automatically discover and scrape application metrics upon startup.

### 3. Continuous Delivery Layer (environments/ & argocd-setup/)
Implements strict GitOps principles utilizing **Argo CD**. Manual terminal-based cluster changes are eliminated; the remote GitHub repository serves as the absolute **Source of Truth**.
* The `argo-password-api-dev.yaml` controller monitors your repository, pulls the generic Helm Chart, injects the `values-dev.yaml` configuration overrides, and syncs the desired state into the isolated `dev-apps` namespace.

---

## 🚀 Deployment Guide for External Users (How to Run This Project)

If you have cloned or forked this repository, follow these quick adjustment steps to spin up the entire cluster engine, GitOps UI, and monitoring stack on your local MicroK8s environment.

### 📌 Prerequisites
* An active **MicroK8s** local cluster installed on your machine.
* Core MicroK8s add-ons enabled: `dns`, `ingress`, `registry`.
* Local `kubectl` CLI context configured to connect to your cluster.

### 🛠️ Step 1: Adjust the Git Source of Truth (Crucial)
Because Argo CD pulls blueprints directly from Git, you must point the Umbrella manifests to your own repository clone:
1. Open `argocd-setup/infrastructure-stack.yaml` and change the `repoURL` value to match your GitHub repository URL.
2. Open `argocd-setup/argo-password-api-dev.yaml` (or your custom application manifest) and update its `repoURL` to match your repository as well.

### 🛠️ Step 2: Initialize Infrastructure & Permissions
Execute the bootstrapping sequence to grant cluster roles to Argo CD and set up web entry routes:

```bash
# 1. Grant global cluster-admin permissions to the Argo CD controller layer
microk8s kubectl apply -f argocd-admin-rights.yaml
microk8s kubectl create clusterrolebinding argocd-all-admin --clusterrole=cluster-admin --group=system:serviceaccounts:argocd

# 2. Deploy Ingress routing and configuration updates
microk8s kubectl apply -f argocd-setup/argocd-ingress.yaml
microk8s kubectl apply -f argocd-setup/argocd-cm.yaml
microk8s kubectl apply -f argocd-setup/argocd-rbac-bypass.yaml
```

### 🐳 Step 3: Build and Push the Application Image Locally
Build your custom Python Flask API payload and push it directly into your local MicroK8s container registry listening on port 32000:

```bash
# Build the local container recipe
docker build -t localhost:32000/password-api:1.0.0 .

# Push the compiled image into the microk8s registry pool
docker push localhost:32000/password-api:1.0.0
```

### 🤖 Step 4: Sync Changes to Git & Trigger Deployment
Commit your localized repository updates (`repoURL` adjustments) and push them to your remote repository branch so the GitOps controller can parse them:

```bash
git add .
git commit -m "deploy: localized infrastructure repository targets"
git push origin main
```

Now, create the required target cluster namespaces and trigger the Root Application deployment:

```bash
# 1. Create target isolated namespaces
microk8s kubectl create namespace dev-apps
microk8s kubectl create namespace monitoring

# 2. Apply the deployment manifests to activate the GitOps pipeline engine
microk8s kubectl apply -f argocd-setup/argo-password-api-dev.yaml
microk8s kubectl apply -f argocd-setup/infrastructure-stack.yaml
```

---

## 📊 Verification & Local Domain Access

### 1. Configure Local DNS Resolution (Hosts File)
To route web traffic from your browser to the local cluster controllers, add the following mappings to your local operating system `/etc/hosts` (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` (Windows) file:

```text
# Replace 127.0.0.1 with your microk8s node IP address if running on a remote VM
127.0.0.1 argocd.local
127.0.0.1 grafana.local
```

### 2. Verify Workloads
* **Argo CD UI Dashboard:** Open your web browser and navigate to `http://argocd.local`. The system operates under secure anonymous administrative permissions for seamless local testing.
* **Grafana Telemetry Metrics:** Navigate to `http://grafana.local` to view native infrastructure metric graphs. (Default admin login: `admin` / `prom-operator`).

---

## 🪐 Project Architecture & GitOps Framework

This project leverages the advanced **App of Apps** pattern combined with declarative GitOps patterns via Argo CD to maintain a reliable system state inside the MicroK8s environment.

### 📐 Declarative Architecture: The "App of Apps" Pattern

To avoid manual deployments and achieve true multi-application synchronization, we implemented a single **Bootstrap (or Umbrella) Application**.

```text
                       [ Private GitHub Repository ]
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │  Root App of Apps      │
                        │ (App Control Registry) │
                        └────────────┬───────────┘
                                     │
                     ┌───────────────┴───────────────┐
                     ▼                               ▼
       ┌──────────────────────────┐    ┌──────────────────────────┐
       │   kube-prometheus-stack  │    │     password-api-dev     │
       │ (Official Helm Registry) │    │  (Custom Flask Payload)  │
       └──────────────────────────┘    └──────────────────────────┘
```

#### How it works:
1. **The Root Application:** Argo CD monitors a dedicated deployment directory (`argocd-setup/`). This directory contains the configuration manifests for other applications.
2. **Child Application Discovery:** When a new `Application` file (like `infrastructure-stack.yaml` or `password-api-dev.yaml`) is pushed to Git, the Root Application automatically detects it.
3. **Decoupled Sourcing:** This allows us to handle multi-source tracking smoothly:
   * **kube-prometheus-stack** fetches directly from the official Prometheus community Helm charts registry.
   * **password-api-dev** acts as our custom local workspace payload, driving custom internal Flask logic.
4. **Self-Healing & Pruning:** Automated policies are configured (`selfHeal: true`, `prune: true`) to actively overwrite any manual overrides made inside the cluster, ensuring Git remains the absolute **Source of Truth**.

---
## 🛠️ MicroK8s (m8k) Core Operations Cheat Sheet

This section documents the essential maintenance, networking, and cluster infrastructure commands utilized during the development, stabilization, and deployment phases of the monitoring architecture.

### 1. Cluster Lifecycle Management
Commands used to control, verify, and initialize the local Kubernetes server workspace.

```bash
# Check the overall health of the cluster and verify which add-ons are enabled
microk8s status --wait-ready

# Safely shut down all core Kubernetes services running on your host machine
microk8s stop

# Fire up the local Kubernetes infrastructure and initialize running components
microk8s start

# Force a complete system restart of the MicroK8s container runtime engine layers
sudo snap restart microk8s
```

### 2. Network & Core Infrastructure Services
Internal networking tools applied to resolve domain resolution blocks and reset invalid localized node tokens.

```bash
# Enable the internal DNS server to allow Pods to resolve domain names and access the internet
microk8s enable dns

# RECOVERY: Regenerate dynamic TLS certs to sync with your machine's updated local IP address
sudo microk8s refresh-certs --cert server.crt
```

### 3. Resource Inspection & Discovery
Telemetry queries to audit running workloads, evaluate environmental errors, and inspect local routing components.

```bash
# List all active system nodes and confirm if the host computer is in 'Ready' status
microk8s kubectl get nodes

# Audit every single pod running across all namespaces to check for errors or crashes
microk8s kubectl get pods -A

# Fetch all operational internal network discovery endpoints inside the monitoring workspace
microk8s kubectl get svc -n monitoring

# Permanently destroy an expired or misconfigured test pod by its specific resource handle
microk8s kubectl delete pod busybox -n default
```

### 4. Application Rollout & Declarative GitOps
Declarative manifest commands used to enforce configuration overrides and sync state updates.

```bash
# Deploy or update target structural manifests from your local directory configuration
microk8s kubectl apply -f argocd-setup/argocd-ingress.yaml

# Hard-reset an operational controller to force-wipe its cache and read updated variables
microk8s rollout restart deployment/argocd-server -n argocd
```

### 5. Troubleshooting & Diagnostics
Direct pipeline logs used to inspect low-level operational crashes within isolated namespaces.

```bash
# Stream the last 50 telemetry log entries from a specific infrastructure container engine
microk8s logs -n argocd deployment/argocd-repo-server --tail=50
```

### 🔐 6. Target Administrative Credential Reset (Template)
Safe structural block used to securely bootstrap credentials manually when programmatic API channels are blocked by TLS restrictions.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: argocd-secret
  namespace: argocd
type: Opaque
data:
  # CRITICAL: Replace the placeholder string below with your securely generated Base64 password hash
  admin.password: <YOUR_BASE64_HASHED_PASSWORD>
  admin.passwordMtime: MjAyNi0xMC0wOVQwMzowMjowMFo=
```
<img width="1095" height="531" alt="2026-10-10_ArgoCD" src="https://github.com/user-attachments/assets/218329b5-896e-4bfc-8c84-2d04c2b60dba" />


```
