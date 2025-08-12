# Calculaud Backend - Quick Reference

## Deployment Commands

### AWS EKS
```bash
# Deploy application (assumes EKS cluster exists)
./k8s/scripts/deploy.sh -e eks -n calculaud-prod

# Run migrations
./k8s/scripts/migrate.sh -n calculaud-prod
```

### On-Premises Kubernetes
```bash
# Deploy application (assumes K8s cluster exists)
./k8s/scripts/deploy.sh -e onprem -n calculaud

# Run migrations
./k8s/scripts/migrate.sh -n calculaud
```

### Air-Gapped Deployment
```bash
# Create deployment package (with internet)
./k8s/scripts/package-for-onprem.sh

# Install on target system (without internet)
tar -xzf calculaud-onprem-*.tar.gz
cd calculaud-onprem-*
./install.sh
```

## Access Points

| Service | EKS | On-Prem K8s |
|---------|-----|-------------|
| **Application** | ALB DNS | NodePort/Ingress/Port-Forward |
| **API Docs** | `/docs` | `/docs` |
| **MinIO Console** | N/A | NodePort/Port-Forward (port 9001) |
| **Health Checks** | `/health` | `/health` |

## Configuration Approach

| Environment | Configuration | Purpose |
|-------------|--------------|---------|
| **Staging** | GitHub Environment + `values.yaml.template` | Production-like testing with dedicated resources |
| **Testing** | GitHub Environment + `values.yaml.template` | Lightweight PR testing with shared resources |
| **On-Premises** | `values-onprem.yaml` | Local deployment with external services |

**Key Features:**
- **GitHub Environments**: Environment-scoped secrets and variables
- **Universal Template**: Single `values.yaml.template` for staging/testing
- **Clean Configuration**: No prefixed secrets (`DATABASE_URL` vs `STAGING_DATABASE_URL`)

## Common Commands

### Kubernetes Debugging
```bash
# Check pod status
kubectl get pods -n calculaud -o wide

# View logs
kubectl logs -f deployment/calculaud-be -n calculaud

# Describe pod
kubectl describe pod <pod-name> -n calculaud

# Execute in pod
kubectl exec -it <pod-name> -n calculaud -- /bin/bash

# Port forward
kubectl port-forward svc/calculaud-be 8000:80 -n calculaud
```


### Database Operations
```bash
# Kubernetes - Run migrations
./k8s/scripts/migrate.sh -n calculaud

# Manual database access (K8s)
kubectl exec -it postgres-0 -n calculaud -- psql -U calculaud calculaud
```

## Health Check Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/health` | Overall health status |
| `/health/live` | Liveness probe (Kubernetes) |
| `/health/ready` | Readiness probe (Kubernetes) |
| `/health/startup` | Startup probe (Kubernetes) |
| `/docs` | API documentation |
| `/metrics` | Prometheus metrics |

## Configuration Keys

### Required Environment Variables
```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# S3/MinIO
S3_ACCESS_KEY_ID=access-key
S3_SECRET_ACCESS_KEY=secret-key
S3_BUCKET_NAME=bucket-name
S3_ENDPOINT_URL=http://minio:9000  # for MinIO

# Authentication
AUTH_JWKS_URL=https://auth/.well-known/jwks.json
AUTH_ISSUER=https://auth/
AUTH_AUDIENCE=calculaud-api
```

### Resource Requirements

| Environment | CPU Request | Memory Request | CPU Limit | Memory Limit |
|-------------|-------------|----------------|-----------|--------------|
| **Development** | 100m | 256Mi | 500m | 512Mi |
| **Production** | 200m | 512Mi | 1000m | 1Gi |
| **EKS** | 250m | 512Mi | 1500m | 2Gi |

## Troubleshooting Quick Fixes

### ImagePullBackOff
```bash
# Check image
docker images | grep calculaud-be

# Fix: Update image name in values file or build locally
docker build -t calculaud/calculaud-be:latest .
```

### CrashLoopBackOff
```bash
# Check logs
kubectl logs <pod-name> -n calculaud --previous

# Common fix: Check environment variables and database connectivity
```

### Database Connection Failed
```bash
# Test connectivity
kubectl exec -it <app-pod> -n calculaud -- nc -zv postgres 5432

# Fix: Verify DATABASE_URL format and credentials
```

### MinIO/S3 Access Issues
```bash
# Test MinIO health
curl http://localhost:9000/minio/health/live

# Fix: Check credentials and endpoint URL
```

## Port Mappings

### Kubernetes NodePort Defaults
- **Application**: 30080
- **Grafana**: 32000
- **Prometheus**: 32001

## Quick Setup Scripts

### Complete EKS Setup (2 minutes)
```bash
#!/bin/bash
# Assumes EKS cluster with ALB, EBS CSI, etc. already configured
./k8s/scripts/deploy.sh -e eks -n calculaud-prod
./k8s/scripts/migrate.sh -n calculaud-prod
```

### Complete On-Prem Setup (2 minutes)
```bash
#!/bin/bash
# Assumes K8s cluster with storage, ingress, etc. already configured
./k8s/scripts/deploy.sh -e onprem -n calculaud
./k8s/scripts/migrate.sh -n calculaud
```

## Emergency Procedures

### Scale Down (Maintenance)
```bash
# Kubernetes
kubectl scale deployment calculaud-be --replicas=0 -n calculaud

```

### Scale Up (Resume)
```bash
# Kubernetes
kubectl scale deployment calculaud-be --replicas=3 -n calculaud

```

### Emergency Backup
```bash
# Kubernetes
kubectl exec postgres-0 -n calculaud -- pg_dump -U calculaud calculaud | gzip > emergency-backup.sql.gz

```

## Support Information

- **Main Documentation**: `docs/DEPLOYMENT_GUIDE.md`
- **Kubernetes Guide**: `k8s/README.md`
- **Development Guide**: `CLAUDE.md`
- **Health Checks**: `http://localhost:8000/health`
- **API Documentation**: `http://localhost:8000/docs`