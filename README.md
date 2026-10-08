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

### 1. Application Layer (`app.py` & `Dockerfile`)
* **`app.py`**: A lightweight Python Flask backend exposing three distinct endpoints:
  * `/generate`: Dynamically generates secure, randomized passwords.
  * `/health`: Health check endpoint utilized by the Kubernetes cluster layer (`livenessProbe`).
  * `/metrics`: Exposes key application performance metrics natively in Prometheus format.
* **`Dockerfile`**: Packages the source code into a secure, minimal container utilizing `python:3.9-slim`.

### 2. Templating Layer (`helm-chart/`)
Standardizes Kubernetes deployment specifications to handle multiple target environments seamlessly.
* The `deployment.yaml` template includes native Prometheus scraping annotations (`prometheus.io/scrape: "true"`). This instructs the cluster's Prometheus server to automatically discover and scrape application metrics upon startup.

### 3. Continuous Delivery Layer (`environments/` & `argocd-setup/`)
Implements strict GitOps principles utilizing **Argo CD**. Manual terminal-based cluster changes are eliminated; the remote GitHub repository serves as the absolute **Source of Truth**.
* The `argo-password-api-dev.yaml` controller monitors your repository, pulls the generic Helm Chart, injects the `values-dev.yaml` configuration overrides, and syncs the desired state into the isolated `dev-apps` namespace.

---

## 🚀 Deployment Guide

### 📌 Prerequisites
* An active **MicroK8s** local cluster.
* Core MicroK8s add-ons enabled: `dns`, `ingress`, `registry`.
* Local `kubectl` CLI context configured to connect to your cluster.

### 🛠️ Step 1: Initialize Infrastructure & Permissions (One-Time Setup)
To allow Argo CD to manage cluster resources globally and initialize custom security objects, run the following:
```bash
# 1. Grant global cluster-admin permissions to the Argo CD controller layer
microk8s kubectl apply -f argocd-admin-rights.yaml
microk8s kubectl create clusterrolebinding argocd-all-admin --clusterrole=cluster-admin --group=system:serviceaccounts:argocd

# 2. Deploy Ingress routing and configuration updates
microk8s kubectl apply -f argocd-setup/argocd-ingress.yaml
microk8s kubectl apply -f argocd-setup/argocd-cm.yaml
microk8s kubectl apply -f argocd-setup/argocd-rbac-bypass.yaml
```

### 🐳 Step 2: Build and Push the Application Image
The Kubernetes nodes need to pull the application from your local MicroK8s container registry listening on port 32000:
```bash
docker build -t localhost:32000/password-api:1.0.0 .
docker push localhost:32000/password-api:1.0.0
```

### 🤖 Step 3: Sync to GitHub & Trigger GitOps Engine
Argo CD evaluates the state of the live cluster exclusively against the code pushed to GitHub. Sync your local commits to your main branch:
```bash
git add .
git commit -m "deploy: infrastructure and helm setup ready"
git push origin main
```

Now, create the required environments and trigger the deployment apps:
```bash
# 1. Create target isolated namespaces
microk8s kubectl create namespace dev-apps
microk8s kubectl create namespace monitoring

# 2. Apply the application deployment manifests to the cluster
microk8s kubectl apply -f argocd-setup/argo-password-api-dev.yaml
microk8s kubectl apply -f argocd-setup/infrastructure-stack.yaml
```

---

## 📊 Verification & Workflow

1. **Verify Pod Status via CLI:**
   ```bash
   microk8s kubectl get pods -n dev-apps
   ```
2. **Access the GitOps dashboard:** Open your browser and navigate to [http://argocd.local](http://argocd.local). Both applications (`password-api-dev` and `kube-prometheus-stack`) will be displayed as fully synchronized and operating normally (**`Synced` & `Healthy`**).
3. **Day-to-Day Lifecycle Workflow:** From this point forward, any architectural modification—such as scaling out replica counts, modifying ingress hosts, or upgrading server configurations—is executed solely by updating the codebase on GitHub. Argo CD will instantly detect the structural variance and reconcile your live cluster automatically within seconds.
