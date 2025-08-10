# On-Premises Infrastructure Prerequisites

This document outlines the external infrastructure components that must be available before deploying Calculaud Backend on-premises.

## 🗄️ Required External Services

### 1. PostgreSQL Database

**Minimum Requirements:**
- PostgreSQL 12+ (recommended: PostgreSQL 15+)
- Available from Kubernetes cluster network
- Database and user created for Calculaud

**Setup Example:**
```sql
-- Create database and user
CREATE DATABASE calculaud;
CREATE USER calculaud WITH ENCRYPTED PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE calculaud TO calculaud;

-- Grant schema privileges (after Alembic creates tables)
\c calculaud
GRANT ALL ON SCHEMA public TO calculaud;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO calculaud;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO calculaud;
```

**Configuration Required:**
```yaml
# In ConfigMap
postgres-host: "postgres.yourdomain.local"
postgres-port: "5432"
postgres-database: "calculaud"
postgres-username: "calculaud"

# In Secret
postgres-password: "your-secure-password"
```

### 2. S3-Compatible Storage

**Requirements:**
- External S3-compatible storage service
- Bucket created for Calculaud files
- Access credentials with read/write permissions

**Configuration Required:**
```yaml
# In ConfigMap
s3-endpoint-url: "https://your-s3-service.domain.com"
s3-bucket-name: "calculaud-files"
s3-use-ssl: "true"

# In Secret
s3-access-key-id: "your-access-key"
s3-secret-access-key: "your-secret-key"
```

## 🔐 Optional: Authentication Provider

**Requirements:**
- External OIDC/OAuth2 provider configured
- Client application registered for Calculaud
- JWKS endpoint accessible from cluster

**Configuration Required:**
```yaml
# In ConfigMap
auth-jwks-url: "https://your-auth-provider.com/.well-known/jwks.json"
auth-issuer: "https://your-auth-provider.com/"
auth-audience: "calculaud-api"
auth-client-id: "calculaud-client"

```

## 🌐 Network Requirements

### Connectivity
- Kubernetes cluster can reach PostgreSQL and S3 services
- If using external auth, cluster can reach auth provider
- Firewall rules allow required ports

### DNS Resolution
- Hostnames resolve from within Kubernetes cluster
- Consider using Kubernetes Services or ExternalName services for service discovery

### Ports
- PostgreSQL: 5432
- S3-compatible storage: varies
- Auth Provider: varies

## 🏗️ Kubernetes Infrastructure

### Storage Classes
- At least one storage class available for persistent volumes
- Examples: `local-path`, `nfs-client`, `hostpath`

**Check available storage classes:**
```bash
kubectl get storageclass
```

### Ingress Controller (Optional)
- NGINX Ingress Controller
- Traefik
- HAProxy Ingress

**Check available ingress classes:**
```bash
kubectl get ingressclass
```

### Load Balancer (Optional)
- MetalLB for bare-metal clusters
- Cloud provider load balancers
- HAProxy/NGINX for manual load balancing

## 📋 Pre-Deployment Checklist

### Database Readiness
- [ ] PostgreSQL server running and accessible
- [ ] Database `calculaud` created
- [ ] User `calculaud` created with proper permissions
- [ ] Network connectivity from Kubernetes cluster confirmed
- [ ] Credentials secured

### Storage Readiness
- [ ] S3-compatible storage service running
- [ ] Bucket created for Calculaud files
- [ ] Access keys created with read/write permissions
- [ ] Network connectivity from Kubernetes cluster confirmed
- [ ] SSL/TLS properly configured (if using HTTPS)

### Authentication Readiness (Optional)
- [ ] OIDC/OAuth2 provider configured
- [ ] Realm/tenant created for Calculaud
- [ ] Client application registered
- [ ] Scopes and permissions configured
- [ ] JWKS endpoint accessible from cluster

### Kubernetes Readiness
- [ ] Cluster has sufficient resources (4GB+ RAM, 20GB+ storage)
- [ ] Storage class available for persistent volumes
- [ ] kubectl access configured
- [ ] Helm 3.8+ installed
- [ ] Namespace planned (default: `calculaud`)

### Network Readiness
- [ ] DNS resolution working for all service hostnames
- [ ] Firewall rules allow required traffic
- [ ] SSL certificates in place (if using HTTPS)
- [ ] Network policies reviewed (if applicable)

## 🚀 Deployment Flow

Once all prerequisites are met:

1. **Deploy Application**:
   ```bash
   cd k8s/scripts
   ./deploy.sh -e onprem -n calculaud
   ```

2. **Run Migrations**:
   ```bash
   ./migrate.sh -n calculaud
   ```

3. **Verify Deployment**:
   ```bash
   kubectl get pods,svc -n calculaud
   kubectl logs -f deployment/calculaud-be -n calculaud
   ```

## 🆘 Troubleshooting

### Common Issues

**Database Connection:**
```bash
# Test from within cluster
kubectl run -it --rm postgres-test --image=postgres:15-alpine --restart=Never -- \
  psql -h postgres.yourdomain.local -U calculaud -d calculaud
```

**S3 Storage Connection:**
```bash
# Test from within cluster using curl
kubectl run -it --rm s3-test --image=curlimages/curl --restart=Never -- \
  curl -I https://your-s3-service.domain.com
```

**DNS Resolution:**
```bash
# Test DNS from within cluster
kubectl run -it --rm dns-test --image=busybox --restart=Never -- \
  nslookup postgres.yourdomain.local
```

For additional support, see the main deployment documentation in `k8s/README.md`.