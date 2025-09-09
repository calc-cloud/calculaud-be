# Calculaud Backend - Kubernetes Deployment

This directory contains Helm charts for deploying the Calculaud Backend application.

## 📚 Documentation

- **[Complete Deployment Guide](../docs/DEPLOYMENT_GUIDE.md)** - Comprehensive guide for all deployment scenarios
- **[Quick Reference](../docs/QUICK_REFERENCE.md)** - Commands and troubleshooting reference
- **[Development Guide](../CLAUDE.md)** - Development and contribution guidelines

## 📁 Directory Structure

```
k8s/
├── helm/
│   └── calculaud-be/    # Helm chart
│       ├── Chart.yaml
│       ├── values.yaml              # Base values with platform options
│       ├── values.yaml.template     # Template for EKS environments
│       ├── values-onprem.yaml       # OpenShift-specific values
│       └── templates/
│           ├── deployment.yaml
│           ├── service.yaml
│           ├── ingress.yaml         # AWS ALB (EKS only)
│           └── route.yaml           # OpenShift Routes (OpenShift only)
└── scripts/
    ├── deploy.sh                    # Platform-aware deployment
    ├── migrate.sh                   # Database migrations
    └── package-for-onprem.sh        # Air-gapped deployment packaging
```

## 🚀 Platform-Specific Deployments

### AWS EKS Deployment

**Prerequisites:**
- EKS cluster with AWS Load Balancer Controller
- `kubectl` configured for EKS
- `helm` (v3.8+)
- ACM SSL certificate (for HTTPS)

```bash
# Deploy to staging (uses ALB ingress)
./k8s/scripts/deploy.sh -e staging -n calculaud-staging

# Deploy to PR environment
./k8s/scripts/deploy.sh -e testing -n calculaud-pr-123

# Run migrations
./k8s/scripts/migrate.sh -n calculaud-staging
```

**Features:** Internal AWS ALB ingress with path-based routing, VPC-only access, EKS-optimized resource limits, automatic SSL termination, health checks.

### On-Premises OpenShift Deployment  

**Prerequisites:**
- OpenShift cluster (4.10+)
- `oc`/`kubectl` configured for OpenShift
- `helm` (v3.8+)
- External PostgreSQL and S3-compatible storage

```bash
# Deploy to OpenShift (uses Routes)
./k8s/scripts/deploy.sh -e onprem -n calculaud

# Run migrations
./k8s/scripts/migrate.sh -n calculaud
```

**Features:** Native OpenShift Routes, HAProxy load balancing, edge TLS termination, external service integration.

# Run migrations in production
./k8s/scripts/migrate.sh -n calculaud-prod
```

## 🔧 Configuration

### Environment-Specific Values

The Helm chart supports different environments through values files:

- `values.yaml` - Default configuration  
- `values.yaml.template` - Template for EKS environments
- `values-onprem.yaml` - OpenShift-specific configuration

### Key Configuration Options

#### Database Configuration

**External PostgreSQL Required:**
```yaml
# Database connection via environment variable
database:
  # Provide full DATABASE_URL externally
  url: "postgresql://username:password@host:5432/database"
```

All deployments require external PostgreSQL - no in-cluster database is provided.

#### S3 Configuration

```yaml
s3:
  accessKeyId: "your-access-key"
  secretAccessKey: "your-secret-key"
  bucketName: "calculaud-files"
  region: "us-east-1"
  # For external S3-compatible storage
  endpointUrl: "https://your-s3-endpoint"
```

#### Authentication Configuration

```yaml
auth:
  jwksUrl: "https://your-auth-provider/.well-known/jwks.json"
  issuer: "https://your-auth-provider/"
  audience: "calculaud-api"
```

#### Access Configuration

**EKS - Internal ALB Ingress:**
```yaml
ingress:
  enabled: true
  className: "alb"
  annotations:
    alb.ingress.kubernetes.io/scheme: internal  # VPC-only access
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/ssl-redirect: '443'
service:
  type: ClusterIP  # Used with ALB ingress
  port: 80
```

**Note**: Internal ALB requires VPN, Direct Connect, or bastion host access.

**OpenShift - Routes:**
```yaml
route:
  enabled: true
  host: "calculaud.your-domain.com"
  tls:
    termination: edge
```

## 🏗️ Platform-Specific Deployment

### AWS EKS (Recommended for Cloud)

**Prerequisites**: 
- EKS cluster configured with kubectl access
- AWS Load Balancer Controller installed
- EBS CSI driver configured (for persistent storage)
- External PostgreSQL database
- AWS S3 bucket for file storage
- Proper IAM roles and policies (if using IRSA)
- SSL certificate in AWS Certificate Manager (for HTTPS)

**Quick Setup**:
```bash
# Deploy application  
./k8s/scripts/deploy.sh -e eks -n calculaud-prod

# Run migrations
./k8s/scripts/migrate.sh -n calculaud-prod
```

**Manual Setup**:
```bash
# Deploy with EKS configuration using values template
envsubst < k8s/helm/calculaud-be/values.yaml.template > values-generated.yaml
helm upgrade --install calculaud-be k8s/helm/calculaud-be \
  -f values-generated.yaml \
  --namespace calculaud-prod \
  --create-namespace

# Run migrations
./k8s/scripts/migrate.sh -n calculaud-prod
```

**Features**:
- Internal ALB ingress with path-based routing (/staging, /{branch-name})
- VPC-only access for enhanced security
- Automatic SSL termination and health checks
- EBS persistent storage for logs and temp files
- ECR integration for container images
- CloudWatch monitoring and logging support
- IRSA support for secure AWS service access (optional)

**Path-Based Routing with Shared Internal ALB**:
- **Staging**: `https://internal-alb-url/staging` (priority: 100)
- **PR Environments**: `https://internal-alb-url/{branch-name}` (priority: 200)
- All environments share the same internal ALB via ingress groups
- **Access**: Requires VPN, Direct Connect, or bastion host

### On-Premises (Recommended for Self-Hosted)

**Prerequisites**:
- Kubernetes cluster (1.24+) with kubectl access
- Storage class configured (e.g., local-path, NFS)
- Ingress controller (optional but recommended)
- Load balancer solution (optional but recommended)

**Quick Setup**:
```bash
# Deploy application
./k8s/scripts/deploy.sh -e onprem -n calculaud

# Run migrations  
./k8s/scripts/migrate.sh -n calculaud
```

**Manual Setup**:
```bash
# Deploy with on-premises configuration
helm upgrade --install calculaud-be k8s/helm/calculaud-be \
  -f k8s/helm/calculaud-be/values-onprem.yaml \
  --namespace calculaud \
  --create-namespace

# Run migrations
./k8s/scripts/migrate.sh -n calculaud
```

**Features**:
- Flexible storage options (local, NFS, etc.)
- OpenShift Routes for external access
- External PostgreSQL and S3-compatible storage required  
- Optional monitoring integration


### Air-Gapped/Offline Deployment

**Create Package** (with internet access):
```bash
./k8s/scripts/package-for-onprem.sh
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
helm upgrade --install calculaud-be k8s/helm/calculaud-be \
  -f k8s/helm/calculaud-be/values-onprem.yaml \
  --namespace calculaud \
  --create-namespace
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