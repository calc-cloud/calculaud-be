# calculaud-be

[![CI](https://github.com/calc-cloud/calculaud-be/actions/workflows/ci.yml/badge.svg)](https://github.com/calc-cloud/calculaud-be/actions/workflows/ci.yml)
[![CD](https://github.com/calc-cloud/calculaud-be/actions/workflows/cd.yml/badge.svg)](https://github.com/calc-cloud/calculaud-be/actions/workflows/cd.yml)
[![Release](https://github.com/calc-cloud/calculaud-be/actions/workflows/release.yml/badge.svg)](https://github.com/calc-cloud/calculaud-be/actions/workflows/release.yml)

Procurement Management System backend built with FastAPI.

## Docker Deployment

This project includes automated Docker image building and publishing to DockerHub via GitHub Actions.

### Setup Instructions

1. **Configure GitHub Secrets**
   
   Go to your repository Settings → Secrets and variables → Actions, and add:
   - `DOCKERHUB_USERNAME`: Your DockerHub username
   - `DOCKERHUB_TOKEN`: Your DockerHub access token (not password)

2. **Configure Repository Variables** (Optional)
   
   Go to your repository Settings → Secrets and variables → Actions → Variables tab:
   - `DOCKER_IMAGE_NAME`: Custom image name (defaults to repository name)

3. **Generate DockerHub Access Token**
   
   1. Go to DockerHub → Account Settings → Security
   2. Click "New Access Token"
   3. Give it a descriptive name (e.g., "GitHub Actions")
   4. Copy the token and add it as `DOCKERHUB_TOKEN` secret

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
- Builds production-optimized Docker image
- Pushes to DockerHub with development tags:
  - `latest` (for main branch)
  - `main-{timestamp}` (for main branch with timestamp)
  - `{git-sha}` (for specific commits)

**Release Pipeline** (`release.yml`):
- Runs when a GitHub release is published
- Waits for CI workflow to complete successfully
- Builds production-optimized Docker image with version
- Pushes to DockerHub with release tags:
  - `v{version}` (e.g., `v1.0.0`)
  - `{version}` (e.g., `1.0.0`)
  - `latest` (updated to release version)

### Manual Deployment

You can also trigger the CD deployment manually:
1. Go to Actions → CD - Build and Deploy
2. Click "Run workflow"
3. Optionally specify a custom tag

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

### Release Tags

Each release creates multiple Docker tags:
- `youruser/calculaud-be:v1.0.0`
- `youruser/calculaud-be:1.0.0`
- `youruser/calculaud-be:latest` (updated to release)

### Running Locally

```bash
# Build the image
docker build -t calculaud-be .

# Run the container
docker run -p 8000:8000 calculaud-be
```

### Environment Variables

The application supports these environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `AWS_ACCESS_KEY_ID`: AWS credentials for S3
- `AWS_SECRET_ACCESS_KEY`: AWS credentials for S3
- `S3_BUCKET_NAME`: S3 bucket name
- `AUTH_JWKS_URL`: Authentication JWKS URL
- `AUTH_ISSUER`: Authentication issuer
- `AUTH_AUDIENCE`: Authentication audience

### Docker Image Features

- Non-root user for security
- Health check endpoint at `/health`
- Optimized layer caching
- AMD64 architecture support

### Development

See [CLAUDE.md](CLAUDE.md) for development guidelines and setup instructions.