# Calculaud Backend - Deployment Guide

Deploy Calculaud Backend to AWS EKS or on-premises Kubernetes environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS EKS Deployment](#aws-eks-deployment)
3. [On-Premises Deployment](#on-premises-deployment)
4. [Air-Gapped Deployment](#air-gapped-deployment)
5. [Configuration](#configuration)
6. [Security](#security)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Common Requirements
- Docker 20.10+ and Docker Compose 2.0+
- kubectl 1.24+
- Helm 3.8+
- At least 4GB RAM and 20GB disk space (application only - external PostgreSQL and S3 storage required)
- Network connectivity (for initial setup)

### Environment-Specific Requirements

#### AWS EKS
- AWS CLI 2.0+
- eksctl 0.150+
- Valid AWS credentials with EKS permissions
- VPC and subnets configured

#### On-Premises OpenShift
- OpenShift cluster (4.10+) with oc/kubectl configured
- Storage class configured
- OpenShift Routes API available (native - no external ingress controller needed)
- External PostgreSQL and S3-compatible storage

## AWS EKS Deployment

**Prerequisites:** EKS cluster with EBS CSI driver and proper IAM roles.

### Key Features
- **NodePort Service:** Simple NodePort service for external access (no ingress controller required)
- **Auto-scaling:** Kubernetes HPA with EKS cluster autoscaler
- **Direct Access:** Access via any node IP on port 30080
- **No External Dependencies:** Zero additional AWS permissions needed

### Deploy Application
```bash
# Deploy to staging
./k8s/scripts/deploy.sh -e staging -n calculaud-staging

# Deploy to PR environment  
./k8s/scripts/deploy.sh -e pr -n calculaud-feature-user-auth

# Run migrations
./k8s/scripts/migrate.sh -n calculaud-staging
```

### Configuration
Uses GitHub Environments with `envsubst` templating:
- **staging**: Production-like environment for main branch
- **testing**: Lightweight PR environment with shared resources
- **Template**: `k8s/helm/calculaud-be/values.yaml.template`

**Setup**: Configure GitHub Environments in Repository → Settings → Environments. See `docs/github-setup-commands.md` for detailed setup.

### Features
- Auto-scaling (HPA/VPA), NodePort service access, EBS volumes, CloudWatch integration
- **Staging**: Main branch, dedicated resources
- **PR**: Feature branches, minimal resources, shared test DB

### PR Deployment
Deploy via GitHub Actions → "Deploy to Kubernetes" → Select `pr` environment and branch. Access via port-forward: `kubectl port-forward svc/calculaud-be 8000:80 -n <namespace>`

## On-Premises OpenShift Deployment

**Prerequisites:** OpenShift cluster with storage class. External PostgreSQL and S3-compatible storage required.

### Key Features
- **Native OpenShift Routes:** Uses OpenShift Routes directly (no external ingress controller needed)
- **Edge TLS Termination:** Automatic HTTPS with OpenShift router
- **HAProxy Load Balancing:** Built-in load balancing and health checks
- **External Services:** Designed for external PostgreSQL and S3 storage

### Deploy Application
```bash
# Deploy and migrate
./k8s/scripts/deploy.sh -e onprem -n calculaud
./k8s/scripts/migrate.sh -n calculaud
```

**Configuration:** Edit `k8s/helm/calculaud-be/values-onprem.yaml` for:
- External PostgreSQL connection details
- S3-compatible storage configuration
- OpenShift Route hostname
- Resource limits for your environment

**Access:** OpenShift Route provides direct HTTPS access at configured hostname (default: `calculaud.local.domain`)

## Air-Gapped Deployment

```bash
# Create package (with internet)
./k8s/scripts/package-for-onprem.sh

# Transfer and install (air-gapped)
tar -xzf calculaud-onprem-*.tar.gz && cd calculaud-onprem-* && ./install.sh
```

## Configuration

**Environment Variables:** Configure DATABASE_URL, S3 credentials, AUTH_JWKS_URL/ISSUER/AUDIENCE, and app settings (DEBUG, LOG_LEVEL, WORKERS).

**Secrets:** 
- **AWS**: Use AWS Secrets Manager with External Secrets Operator
- **On-premises**: Use Kubernetes secrets: `kubectl create secret generic calculaud-secrets --from-literal=database-password=xxx`

**Validation:** Check health endpoints: `curl http://localhost:8000/health`

## Security

- **HTTPS/TLS**: Configure in ingress with TLS certificates
- **Network Policies**: Restrict pod-to-pod communication
- **Pod Security**: Run as non-root (1000), read-only filesystem, no privilege escalation
- **Resource Limits**: Set memory/CPU requests and limits  
- **Data Encryption**: Enable for secrets, database, and S3
- **RBAC**: Configure ServiceAccount with minimal permissions

## Monitoring

- **Metrics**: `/metrics` endpoint for Prometheus scraping
- **Logs**: FluentBit → CloudWatch (EKS) or ELK stack (on-premises)  
- **Health Checks**: `/health`, `/health/live`, `/health/ready`, `/health/startup`

## Troubleshooting

### Common Issues

**ImagePullBackOff:** Check image name/tag in values file, registry credentials, image existence
**CrashLoopBackOff:** Check logs (`kubectl logs <pod> -n calculaud`), database connection, env vars, resources
**Database Connection:** Verify DATABASE_URL, credentials, network connectivity
**S3 Issues:** Check credentials, endpoint URL, bucket permissions
**Ingress Problems:** Verify ingress controller, annotations, service endpoints, DNS

### Debug Commands

```bash
# Basic debugging
kubectl get pods -n calculaud -o wide
kubectl describe pod <pod-name> -n calculaud  
kubectl logs -f deployment/calculaud-be -n calculaud
kubectl exec -it <pod-name> -n calculaud -- /bin/bash

# Performance monitoring
kubectl top pods -n calculaud
```

**Troubleshooting Steps:**
1. Check application logs and health endpoints (`/health`)
2. Verify configuration and connectivity  
3. Monitor resource usage (CPU/memory)
4. Review README.md, k8s/README.md, CLAUDE.md for guidance