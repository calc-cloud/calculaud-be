# calculaud-be

[![CI](https://github.com/calc-cloud/calculaud-be/actions/workflows/ci.yml/badge.svg)](https://github.com/calc-cloud/calculaud-be/actions/workflows/ci.yml)
[![CD](https://github.com/calc-cloud/calculaud-be/actions/workflows/cd.yml/badge.svg)](https://github.com/calc-cloud/calculaud-be/actions/workflows/cd.yml)
[![Release](https://github.com/calc-cloud/calculaud-be/actions/workflows/release.yml/badge.svg)](https://github.com/calc-cloud/calculaud-be/actions/workflows/release.yml)

Procurement Management System backend built with FastAPI.

## Deployment

This project supports multiple deployment platforms via automated CI/CD with Helm charts and Docker containers.

### Supported Platforms

- **AWS EKS**: NodePort service with ALB integration
- **OpenShift**: Native Routes for ingress
- **Docker**: Standalone container deployment

### Deployment Configuration

Configure GitHub secrets for automated deployment:
- `ECR_REPOSITORY`: AWS ECR repository URL
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`: AWS credentials
- Environment-specific database and auth configurations

### How It Works

The CI/CD pipeline consists of three workflows:

**CI Pipeline** (`ci.yml`):
- Runs on all pushes and pull requests
- Performs code quality checks: linting (flake8), formatting (black), import sorting (isort)
- Runs all tests (pytest)
- Must pass before merging PRs

**CD Pipeline** (`cd.yml`):
- Runs on pushes to `main` branch only
- Waits for CI workflow to complete successfully
- Builds and pushes Docker image to ECR
- Deploys to staging environment using Helm
- Supports EKS and OpenShift platforms

**Release Pipeline** (`release.yml`):
- Runs when a GitHub release is published
- Waits for CI workflow to complete successfully
- Builds and tags Docker image for production
- Deploys to production environment via Helm
- Creates versioned releases with proper tagging

### Manual Deployment

**Kubernetes/Helm**:
```bash
# Deploy to staging
./scripts/deploy-staging.sh

# Deploy to production  
./scripts/deploy-production.sh
```

**Docker**:
```bash
docker build -t calculaud-be .
docker run -p 8000:8000 calculaud-be
```

## 🚀 Release Process

### Creating a New Release

1. **Prepare Release Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b release/v1.0.0
   ```

2. **Update Version** (if needed)
   - Update version in `app/config.py`
   - Update any documentation

3. **Create Pull Request**
   ```bash
   git add .
   git commit -m "chore: prepare release v1.0.0"
   git push -u origin release/v1.0.0
   ```
   - Create PR from release branch to main
   - Wait for CI to pass and get approval

4. **Merge and Create GitHub Release**
   - Merge PR to main
   - Go to GitHub → Releases → "Create a new release"
   - Choose tag: `v1.0.0` (will be created)
   - Release title: `v1.0.0`
   - Use the template from `.github/release_template.md`
   - Click "Publish release"

5. **Automatic Deployment**
   - Release workflow automatically triggers
   - Docker images are built and pushed with proper tags
   - Check Actions tab for deployment status

### Configuration

**Helm Values**:
- `values.yaml.template`: Universal template for all environments
- `values-onprem.yaml`: OpenShift-specific configuration
- Environment variables injected via GitHub Actions

**Key Configuration**:
- `DATABASE_URL`: PostgreSQL connection string
- `S3_BUCKET` / `S3_ACCESS_KEY` / `S3_SECRET_KEY`: AWS S3 storage
- `AUTH_OIDC_URL` / `AUTH_AUDIENCE`: Authentication (other endpoints auto-discovered)
- Platform-specific ingress (Routes vs NodePort)

**Health Checks**:
- `/health/live`: Liveness probe
- `/health/ready`: Readiness probe  
- `/health/startup`: Startup probe
- `/health/`: Detailed monitoring endpoint

### Development

See [CLAUDE.md](CLAUDE.md) for development guidelines and setup instructions.