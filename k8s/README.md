# Calculaud Backend - Kubernetes Deployment

This directory contains Kubernetes manifests and Helm charts for deploying the Calculaud Backend application.

## 📚 Documentation

- **[Complete Deployment Guide](../docs/DEPLOYMENT_GUIDE.md)** - Comprehensive guide for all deployment scenarios
- **[Quick Reference](../docs/QUICK_REFERENCE.md)** - Commands and troubleshooting reference
- **[Development Guide](../CLAUDE.md)** - Development and contribution guidelines

## 📁 Directory Structure

```
k8s/
├── manifests/           # Raw Kubernetes YAML files
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── postgresql.yaml  # Optional: in-cluster PostgreSQL
├── helm/
│   └── calculaud-be/    # Helm chart
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-dev.yaml
│       ├── values-prod.yaml
│       └── templates/
└── scripts/
    ├── deploy.sh        # Deployment script
    └── migrate.sh       # Database migration script
```

## 🚀 Quick Start

### Prerequisites

- Kubernetes cluster (1.19+)
- `kubectl` configured to access your cluster
- `helm` (v3.8+)
- Docker image: `calculaud/calculaud-be` pushed to your registry

### 1. Deploy to Development

```bash
# Deploy with default development settings
./k8s/scripts/deploy.sh -e dev

# Or deploy with custom values
./k8s/scripts/deploy.sh -e dev -f my-custom-values.yaml
```

### 2. Run Database Migrations

```bash
# Run Alembic migrations
./k8s/scripts/migrate.sh -n calculaud

# Check current migration status
./k8s/scripts/migrate.sh -c current
```

### 3. Deploy to Production

```bash
# Deploy to production environment
./k8s/scripts/deploy.sh -e prod -n calculaud-prod

# Run migrations in production
./k8s/scripts/migrate.sh -n calculaud-prod
```

## 🔧 Configuration

### Environment-Specific Values

The Helm chart supports different environments through values files:

- `values.yaml` - Default configuration
- `values-dev.yaml` - Development overrides
- `values-prod.yaml` - Production overrides

### Key Configuration Options

#### Database Configuration

```yaml
postgresql:
  # Use in-cluster PostgreSQL
  enabled: true
  password: "your-secure-password"
  
  # Or use external database
  enabled: false
  external:
    host: "your-postgres-host"
    username: "calculaud"
    password: "your-password"
    database: "calculaud"
```

#### S3 Configuration

```yaml
s3:
  accessKeyId: "your-access-key"
  secretAccessKey: "your-secret-key"
  bucketName: "calculaud-files"
  region: "us-east-1"
  # For S3-compatible storage (MinIO, etc.)
  endpointUrl: "https://your-s3-endpoint"
```

#### Authentication Configuration

```yaml
auth:
  jwksUrl: "https://your-auth-provider/.well-known/jwks.json"
  issuer: "https://your-auth-provider/"
  audience: "calculaud-api"
```

#### Ingress Configuration

```yaml
ingress:
  enabled: true
  className: "nginx"  # or "openshift-default" for OpenShift
  hosts:
    - host: api.calculaud.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: calculaud-tls
      hosts:
        - api.calculaud.com
```

## 🏗️ Platform-Specific Deployment

### AWS EKS (Recommended for Cloud)

**Prerequisites**: 
- EKS cluster configured with kubectl access
- AWS Load Balancer Controller installed
- EBS CSI driver configured  
- External Secrets Operator (optional)
- Proper IAM roles and policies

**Quick Setup**:
```bash
# Deploy application
./scripts/deploy.sh -e eks -n calculaud-prod

# Run migrations
./scripts/migrate.sh -n calculaud-prod
```

**Manual Setup**:
```bash
# Deploy with EKS-optimized configuration
helm upgrade --install calculaud-be helm/calculaud-be \
  -f helm/calculaud-be/values-eks.yaml \
  --namespace calculaud-prod \
  --create-namespace

# Run migrations
./scripts/migrate.sh -n calculaud-prod
```

**Features**:
- Application Load Balancer (ALB) integration
- EBS persistent storage
- AWS Secrets Manager integration
- CloudWatch monitoring and logging
- IRSA for secure AWS service access

### On-Premises (Recommended for Self-Hosted)

**Prerequisites**:
- Kubernetes cluster (1.24+) with kubectl access
- Storage class configured (e.g., local-path, NFS)
- Ingress controller (optional but recommended)
- Load balancer solution (optional but recommended)

**Quick Setup**:
```bash
# Deploy application
./scripts/deploy.sh -e onprem -n calculaud

# Run migrations
./scripts/migrate.sh -n calculaud
```

**Manual Setup**:
```bash
# Deploy with on-premises configuration
helm upgrade --install calculaud-be helm/calculaud-be \
  -f helm/calculaud-be/values-onprem.yaml \
  --namespace calculaud \
  --create-namespace

# Run migrations
./scripts/migrate.sh -n calculaud
```

**Features**:
- Flexible storage options (local, NFS, etc.)
- NodePort, Ingress, or LoadBalancer access
- Embedded PostgreSQL and MinIO S3-compatible storage
- Optional monitoring integration


### Air-Gapped/Offline Deployment

**Create Package** (with internet access):
```bash
./scripts/package-for-onprem.sh
```

**Deploy Package** (without internet):
```bash
# Transfer calculaud-onprem-*.tar.gz to target system
tar -xzf calculaud-onprem-*.tar.gz
cd calculaud-onprem-*
./install.sh
```

### OpenShift

```bash
# Deploy with OpenShift-specific settings
helm upgrade --install calculaud-be helm/calculaud-be \
  --set ingress.enabled=false \
  --set openshift.route.enabled=true
```

## 📊 Monitoring & Health Checks

The application provides comprehensive health check endpoints:

- `/health` - Detailed health status
- `/health/live` - Kubernetes liveness probe
- `/health/ready` - Kubernetes readiness probe  
- `/health/startup` - Kubernetes startup probe

### Monitoring Integration

```yaml
# Enable Prometheus metrics
metrics:
  enabled: true

# Pod annotations for scraping
podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"
```

## 🔒 Security

### Pod Security Context

```yaml
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000

securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1000
  capabilities:
    drop:
    - ALL
```

### Secret Management

For production deployments, consider using external secret management:

```yaml
# Use existing secret instead of creating one
existingSecret: "calculaud-prod-secrets"

# For AWS Secrets Manager
serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::ACCOUNT:role/calculaud-secrets-role"
```

## 🔄 Scaling & Performance

### Horizontal Pod Autoscaling

```yaml
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 75
```

### Resource Management

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "200m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## 🚨 Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n calculaud -l app.kubernetes.io/name=calculaud-be
```

### View Application Logs

```bash
kubectl logs -f deployment/calculaud-be -n calculaud
```

### Check Health Status

```bash
kubectl port-forward svc/calculaud-be 8080:80 -n calculaud
curl http://localhost:8080/health
```

### Database Connection Issues

```bash
# Check database connectivity
./k8s/scripts/migrate.sh -c current

# View migration job logs
kubectl logs job/calculaud-migration -n calculaud
```

### Common Issues

1. **ImagePullBackOff**: Update image repository/tag in values
2. **CrashLoopBackOff**: Check environment variables and secrets
3. **Service Unavailable**: Verify readiness probe endpoints
4. **Database Connection**: Check DATABASE_URL secret configuration

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL on Kubernetes](https://kubernetes.io/docs/tutorials/stateful-application/postgresql/)