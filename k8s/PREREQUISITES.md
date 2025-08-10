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

**Options:**
- MinIO (recommended for on-premises)
- AWS S3
- Compatible alternatives (Ceph, etc.)

**MinIO Setup Example:**
```bash
# Install MinIO server
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# Create storage directory
sudo mkdir -p /opt/minio/data

# Create service user
sudo useradd -r -s /bin/false minio

# Start MinIO (for production, use systemd service)
MINIO_ROOT_USER=admin MINIO_ROOT_PASSWORD=your-secure-password \
minio server /opt/minio/data --address :9000 --console-address :9001
```

**Bucket Setup:**
```bash
# Install MinIO client
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc

# Configure client
mc alias set local http://localhost:9000 admin your-secure-password

# Create bucket
mc mb local/calculaud-files

# Create access key for application
mc admin user add local calculaud-app your-app-password
mc admin policy set local readwrite user=calculaud-app
```

**Configuration Required:**
```yaml
# In ConfigMap
s3-endpoint-url: "https://minio.yourdomain.local:9000"
s3-bucket-name: "calculaud-files"
s3-use-ssl: "true"  # false for HTTP

# In Secret
s3-access-key-id: "calculaud-app"
s3-secret-access-key: "your-app-password"
```

## 🔐 Optional: Authentication Provider

### OIDC/OAuth2 Provider

**Options:**
- Keycloak (open source)
- Auth0
- Azure AD
- Google Workspace
- Custom OIDC provider

**Keycloak Setup Example:**
```bash
# Using Docker
docker run -d \
  --name keycloak \
  -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:latest \
  start-dev
```

**Configuration Required:**
```yaml
# In ConfigMap
auth-jwks-url: "https://keycloak.yourdomain.local/auth/realms/calculaud/.well-known/openid_configuration"
auth-issuer: "https://keycloak.yourdomain.local/auth/realms/calculaud"
auth-audience: "calculaud-api"
auth-client-id: "calculaud-client"

# In Secret (if using confidential client)
auth-client-secret: "your-client-secret"
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
- MinIO: 9000 (API), 9001 (Console)
- Auth Provider: varies (8080 for Keycloak)

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

1. **Configure Services**:
   ```bash
   cd k8s/config
   cp configmap-template.yaml configmap.yaml
   cp secret-template.yaml secret.yaml
   # Edit with your service endpoints and credentials
   ```

2. **Apply Configuration**:
   ```bash
   ./apply-config.sh -n calculaud
   ```

3. **Deploy Application**:
   ```bash
   cd ../scripts
   ./deploy.sh -e onprem -n calculaud
   ```

4. **Run Migrations**:
   ```bash
   ./migrate.sh -n calculaud
   ```

5. **Verify Deployment**:
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
# Test from within cluster  
kubectl run -it --rm s3-test --image=minio/mc --restart=Never -- \
  mc alias set test https://s3.yourdomain.local access-key secret-key
kubectl exec s3-test -- mc ls test/calculaud-files
```

**DNS Resolution:**
```bash
# Test DNS from within cluster
kubectl run -it --rm dns-test --image=busybox --restart=Never -- \
  nslookup postgres.yourdomain.local
```

For additional support, see the main deployment documentation in `k8s/README.md`.