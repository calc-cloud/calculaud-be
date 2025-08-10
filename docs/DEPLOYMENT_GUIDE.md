# Calculaud Backend - Complete Deployment Guide

This comprehensive guide covers deploying the Calculaud Backend to AWS EKS and on-premises Kubernetes environments. Both deployments assume that the Kubernetes clusters are already provisioned and configured.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS EKS Deployment](#aws-eks-deployment)
3. [On-Premises Kubernetes Deployment](#on-premises-kubernetes-deployment)
4. [Air-Gapped/Offline Deployment](#air-gappedoffline-deployment)
5. [Configuration Management](#configuration-management)
6. [Security Best Practices](#security-best-practices)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Backup and Recovery](#backup-and-recovery)
9. [Troubleshooting](#troubleshooting)

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

#### On-Premises
- Kubernetes cluster (1.24+) with kubectl configured
- Storage class configured
- Ingress controller (recommended)
- Load balancer solution (recommended)

## AWS EKS Deployment

### Quick Start

Assumes you have an existing EKS cluster with:
- AWS Load Balancer Controller installed
- EBS CSI driver configured
- External Secrets Operator (optional)
- Proper IAM roles and policies

1. **Deploy Application**:
   ```bash
   # Deploy to EKS
   ./k8s/scripts/deploy.sh -e eks -n calculaud-prod
   ```

2. **Run Database Migrations**:
   ```bash
   ./k8s/scripts/migrate.sh -n calculaud-prod
   ```

### EKS Configuration

#### Step 1: Configure Application Secrets

Create secrets in AWS Secrets Manager:

```bash
# Database credentials
aws secretsmanager create-secret \
    --name "calculaud/prod/database" \
    --secret-string '{"username":"calculaud_admin","password":"your-secure-password","host":"your-rds-endpoint","database":"calculaud_prod"}'

# S3 credentials (if not using IRSA)
aws secretsmanager create-secret \
    --name "calculaud/prod/s3" \
    --secret-string '{"accessKeyId":"your-access-key","secretAccessKey":"your-secret-key"}'

# Auth configuration
aws secretsmanager create-secret \
    --name "calculaud/prod/auth" \
    --secret-string '{"clientId":"your-client-id","clientSecret":"your-client-secret"}'
```

#### Step 2: Customize EKS Configuration

Edit `k8s/helm/calculaud-be/values-eks.yaml`:

```yaml
# Update with your values
image:
  repository: "<ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/calculaud-be"

postgresql:
  external:
    host: "calculaud-prod.cluster-xxx.us-east-1.rds.amazonaws.com"

s3:
  bucketName: "calculaud-prod-files"
  region: "us-east-1"

auth:
  jwksUrl: "https://your-auth-provider/.well-known/jwks.json"
  issuer: "https://your-auth-provider/"
```

#### Step 3: Deploy Application

```bash
# Build and push Docker image to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com
docker build -t <ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com/calculaud-be:latest .
docker push <ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com/calculaud-be:latest

# Deploy to EKS
./k8s/scripts/deploy.sh -e eks -n calculaud-prod

# Run migrations
./k8s/scripts/migrate.sh -n calculaud-prod
```

### EKS-Specific Features

- **Auto-scaling**: Configured with HPA and VPA
- **Load Balancing**: ALB with SSL termination
- **Storage**: EBS volumes with automatic provisioning
- **Monitoring**: CloudWatch integration
- **Security**: IRSA for secure AWS access

## On-Premises Kubernetes Deployment

### Quick Start

Assumes you have an existing Kubernetes cluster with:
- Storage class configured
- Ingress controller (optional but recommended)
- Load balancer solution (optional but recommended)

1. **Deploy Application**:
   ```bash
   ./k8s/scripts/deploy.sh -e onprem -n calculaud
   ```

2. **Run Database Migrations**:
   ```bash
   ./k8s/scripts/migrate.sh -n calculaud
   ```

### On-Premises Configuration

Edit `k8s/helm/calculaud-be/values-onprem.yaml`:

```yaml
# Service configuration for on-premises access
service:
  type: NodePort  # or LoadBalancer if MetalLB is configured
  nodePort: 30080

# Ingress configuration
ingress:
  enabled: true  # if NGINX Ingress is installed
  hosts:
    - host: calculaud.local.domain

# MinIO for S3-compatible storage
minio:
  enabled: true
  persistence:
    size: 100Gi

# PostgreSQL configuration
postgresql:
  enabled: true
  persistence:
    size: 50Gi
```

### Deploy Application

```bash
# Deploy to on-premises Kubernetes
./k8s/scripts/deploy.sh -e onprem -n calculaud

# Run migrations
./k8s/scripts/migrate.sh -n calculaud

# Check status
kubectl get pods -n calculaud
```

### On-Premises Access Options

1. **NodePort**: Access via `http://<node-ip>:30080`
2. **LoadBalancer**: Access via assigned external IP
3. **Ingress**: Access via configured domain name
4. **Port Forward**: `kubectl port-forward svc/calculaud-be 8000:80 -n calculaud`

## Air-Gapped/Offline Deployment

For environments without internet access, use the packaging script to create a complete deployment package.

### Creating Deployment Package

1. **Create Package** (with internet access):
   ```bash
   ./k8s/scripts/package-for-onprem.sh
   ```

2. **Custom Package Options**:
   ```bash
   # Skip Docker images (if already available)
   ./k8s/scripts/package-for-onprem.sh --skip-docker

   # Include sample data
   ./k8s/scripts/package-for-onprem.sh --include-data

   # Custom output name
   ./k8s/scripts/package-for-onprem.sh -o my-custom-package.tar.gz
   ```

3. **Package Contents**:
   - Docker images (compressed)
   - Application source code
   - Kubernetes Helm charts
   - Configuration templates
   - Installation scripts
   - Documentation

### Deploying from Package

1. **Transfer Package** to target environment:
   ```bash
   # Using SCP
   scp calculaud-onprem-*.tar.gz user@target-server:/opt/
   
   # Or use USB/external drive for air-gapped environments
   ```

2. **Extract and Install**:
   ```bash
   # Extract package
   tar -xzf calculaud-onprem-*.tar.gz
   cd calculaud-onprem-*
   
   # Run automated installer
   ./install.sh
   ```

3. **Manual Installation**:
   ```bash
   # Load Docker images
   cd docker-images
   ./load-images.sh
   cd ..
   
   # Deploy to Kubernetes
   ./k8s/scripts/deploy.sh -e onprem -n calculaud
   ./k8s/scripts/migrate.sh -n calculaud
   ```

## Configuration Management

### Environment Variables

Key environment variables by category:

#### Database Configuration
```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
POSTGRES_PASSWORD=secure-password
```

#### S3 Storage Configuration
```env
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key
S3_REGION=us-east-1
S3_BUCKET_NAME=calculaud-files
S3_ENDPOINT_URL=http://minio:9000  # for MinIO
```

#### Authentication Configuration
```env
AUTH_JWKS_URL=https://auth-provider/.well-known/jwks.json
AUTH_ISSUER=https://auth-provider/
AUTH_AUDIENCE=calculaud-api
```

#### Application Configuration
```env
APP_NAME="Procurement Management System"
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=INFO
WORKERS=4
```

### Secrets Management

#### AWS EKS
Use AWS Secrets Manager with External Secrets Operator:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        secretRef:
          accessKeyID:
            name: aws-creds
            key: access-key-id
          secretAccessKey:
            name: aws-creds
            key: secret-access-key
```

#### On-Premises
Use Kubernetes secrets or external secret management:

```bash
# Create secret
kubectl create secret generic calculaud-secrets \
  --from-literal=database-password=secure-password \
  --from-literal=s3-access-key=access-key \
  --namespace calculaud
```

### Configuration Validation

Use the built-in health checks to validate configuration:

```bash
# Check application health
curl http://localhost:8000/health

# Detailed health information
curl http://localhost:8000/health/ready
```

## Security Best Practices

### Network Security

1. **Use HTTPS/TLS**:
   ```yaml
   # In ingress configuration
   tls:
     - secretName: calculaud-tls
       hosts:
         - api.calculaud.com
   ```

2. **Network Policies** (if supported):
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: calculaud-network-policy
   spec:
     podSelector:
       matchLabels:
         app.kubernetes.io/name: calculaud-be
     ingress:
     - from:
       - podSelector:
           matchLabels:
             app.kubernetes.io/name: nginx-ingress
     egress:
     - to:
       - podSelector:
           matchLabels:
             app.kubernetes.io/name: postgresql
   ```

### Pod Security

1. **Security Context**:
   ```yaml
   securityContext:
     runAsNonRoot: true
     runAsUser: 1000
     allowPrivilegeEscalation: false
     readOnlyRootFilesystem: true
   ```

2. **Resource Limits**:
   ```yaml
   resources:
     requests:
       memory: "256Mi"
       cpu: "100m"
     limits:
       memory: "1Gi"
       cpu: "1000m"
   ```

### Data Security

1. **Encrypt Secrets**: Use external secret management
2. **Database Encryption**: Enable at-rest and in-transit encryption
3. **S3 Encryption**: Enable bucket encryption
4. **Backup Encryption**: Encrypt backup files

### Access Control

1. **RBAC Configuration**:
   ```yaml
   apiVersion: v1
   kind: ServiceAccount
   metadata:
     name: calculaud-sa
   ---
   apiVersion: rbac.authorization.k8s.io/v1
   kind: Role
   metadata:
     name: calculaud-role
   rules:
   - apiGroups: [""]
     resources: ["configmaps", "secrets"]
     verbs: ["get", "list"]
   ```

2. **Authentication**: Configure with enterprise auth providers
3. **Authorization**: Implement role-based access in application

## Monitoring and Logging

### Prometheus Metrics

The application exposes metrics at `/metrics` endpoint:

```yaml
# ServiceMonitor for Prometheus Operator
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: calculaud-metrics
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: calculaud-be
  endpoints:
  - port: http
    path: /metrics
```

### Log Aggregation

#### EKS with CloudWatch
```yaml
# FluentBit configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
data:
  fluent-bit.conf: |
    [SERVICE]
        Parsers_File parsers.conf
    [INPUT]
        Name tail
        Path /var/log/containers/calculaud-*.log
        Parser docker
    [OUTPUT]
        Name cloudwatch_logs
        Match *
        region us-east-1
        log_group_name /calculaud/application
```

#### On-Premises with ELK Stack
```bash
# Install ELK stack
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch --namespace logging --create-namespace
helm install kibana elastic/kibana --namespace logging
helm install filebeat elastic/filebeat --namespace logging
```

### Health Checks

The application provides multiple health check endpoints:

- `/health` - Overall health status
- `/health/live` - Liveness probe
- `/health/ready` - Readiness probe
- `/health/startup` - Startup probe

Configure Kubernetes probes:
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

## Backup and Recovery

### Database Backup

#### Automated Backup with CronJob
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:15-alpine
            command:
            - /bin/bash
            - -c
            - |
              pg_dump -h postgres -U calculaud calculaud | gzip > /backups/backup-$(date +%Y%m%d-%H%M%S).sql.gz
              find /backups -name "backup-*.sql.gz" -mtime +7 -delete
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            volumeMounts:
            - name: backup-storage
              mountPath: /backups
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

#### Manual Backup
```bash
# Docker Compose
./docker-compose.scripts.sh backup

# Kubernetes
kubectl exec -it postgres-0 -- pg_dump -U calculaud calculaud | gzip > backup-$(date +%Y%m%d).sql.gz
```

### File Storage Backup

#### S3/MinIO Backup
```bash
# Using MinIO client
mc mirror minio/calculaud-files /backup/files/

# Using AWS CLI
aws s3 sync s3://calculaud-files /backup/files/
```

### Disaster Recovery

1. **Database Recovery**:
   ```bash
   # Restore from backup
   gunzip -c backup-20240101.sql.gz | psql -h postgres -U calculaud calculaud
   ```

2. **Configuration Recovery**:
   - Keep configuration files in version control
   - Document environment-specific values
   - Automate deployment with scripts

3. **Testing Recovery**:
   - Regular recovery drills
   - Automated backup verification
   - Document recovery procedures

## Troubleshooting

### Common Issues

#### 1. ImagePullBackOff
```bash
# Check image availability
docker images | grep calculaud-be

# Verify image repository configuration
kubectl describe pod <pod-name> -n calculaud
```

**Solutions**:
- Verify image name and tag in values file
- Check container registry credentials
- Ensure image exists in registry

#### 2. CrashLoopBackOff
```bash
# Check application logs
kubectl logs <pod-name> -n calculaud

# Check previous container logs
kubectl logs <pod-name> -n calculaud --previous
```

**Common Causes**:
- Database connection issues
- Missing environment variables
- Configuration errors
- Resource constraints

#### 3. Database Connection Failed
```bash
# Check database connectivity
kubectl exec -it <app-pod> -n calculaud -- curl postgres:5432

# Test database connection
kubectl exec -it postgres-0 -n calculaud -- psql -U calculaud -d calculaud -c "SELECT version();"
```

**Solutions**:
- Verify DATABASE_URL format
- Check database credentials
- Ensure database is running and accessible
- Verify network policies

#### 4. S3/MinIO Connection Issues
```bash
# Check MinIO connectivity
kubectl exec -it <app-pod> -n calculaud -- curl http://minio:9000/minio/health/live

# Test S3 access
aws s3 ls s3://calculaud-files --endpoint-url http://minio:9000
```

**Solutions**:
- Verify S3 credentials and endpoint
- Check bucket permissions
- Ensure MinIO is running (for on-premises)

#### 5. Ingress Not Working
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress configuration
kubectl describe ingress calculaud-ingress -n calculaud

# Check service endpoints
kubectl get endpoints calculaud-be -n calculaud
```

**Solutions**:
- Install/configure ingress controller
- Verify ingress annotations
- Check service selector labels
- Verify DNS configuration

### Debugging Commands

#### Kubernetes
```bash
# Get pod status
kubectl get pods -n calculaud -o wide

# Describe pod for events
kubectl describe pod <pod-name> -n calculaud

# Check logs
kubectl logs -f deployment/calculaud-be -n calculaud

# Execute commands in pod
kubectl exec -it <pod-name> -n calculaud -- /bin/bash

# Port forward for local access
kubectl port-forward svc/calculaud-be 8000:80 -n calculaud

# Check resource usage
kubectl top pods -n calculaud
```

#### Docker Compose
```bash
# Check container status
docker-compose -f docker-compose.onprem.yml ps

# View logs
docker-compose -f docker-compose.onprem.yml logs calculaud-app

# Execute commands in container
docker-compose -f docker-compose.onprem.yml exec calculaud-app /bin/bash

# Check resource usage
docker stats
```

### Performance Issues

#### 1. Slow Response Times
- Check resource limits and requests
- Monitor database performance
- Review application logs for slow queries
- Check network latency

#### 2. High Memory Usage
```bash
# Check memory limits
kubectl describe pod <pod-name> -n calculaud | grep -A 5 Limits

# Monitor memory usage
kubectl top pod <pod-name> -n calculaud
```

**Solutions**:
- Increase memory limits
- Optimize application code
- Review database query efficiency

#### 3. Database Performance
```bash
# Check PostgreSQL performance
kubectl exec -it postgres-0 -n calculaud -- psql -U calculaud -d calculaud -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;"
```

### Getting Help

1. **Check application logs** first for specific error messages
2. **Review configuration** for typos or missing values
3. **Verify connectivity** between components
4. **Check resource constraints** (CPU, memory, storage)
5. **Consult health check endpoints** for detailed status
6. **Use debugging commands** to inspect system state

For additional support:
- Review the main README.md
- Check the k8s/README.md for Kubernetes-specific guidance
- Consult the CLAUDE.md for development guidelines