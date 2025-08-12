# GitHub Repository Configuration Commands

This file contains all the commands needed to configure your GitHub repository with GitHub Environments for deployment. **DO NOT RUN THESE COMMANDS YET** - review and customize them first.

## Overview

This setup uses GitHub Environments (`staging`, `testing`) with environment-scoped secrets and variables for clean, secure deployment configuration.

## Prerequisites

1. Install GitHub CLI: `brew install gh` (macOS) or equivalent
2. Authenticate: `gh auth login`
3. Navigate to your repository directory

## Step 1: Setup AWS OIDC Integration (Recommended)

For secure AWS authentication without long-lived access keys, set up OIDC integration:

```bash
# Create IAM role for GitHub Actions (run this in AWS CLI)
aws iam create-role --role-name github-actions-build-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Federated": "arn:aws:iam::<ACCOUNT>:oidc-provider/token.actions.githubusercontent.com"
        },
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {
          "StringEquals": {
            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
          },
          "StringLike": {
            "token.actions.githubusercontent.com:sub": "repo:<OWNER>/<REPO>:*"
          }
        }
      }
    ]
  }'

# Attach ECR permissions to the role
aws iam attach-role-policy \
  --role-name github-actions-build-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

# If you need to create OIDC provider (run once per AWS account)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --client-id-list sts.amazonaws.com
```

**Note**: Replace `<ACCOUNT>`, `<OWNER>`, `<REPO>` with your actual values.

## Step 2: Create GitHub Environments

```bash
# Create staging environment
gh api repos/:owner/:repo/environments/staging --method PUT \
  --field deployment_branch_policy='{"protected_branches":true,"custom_branch_policies":false}'

# Create testing environment  
gh api repos/:owner/:repo/environments/testing --method PUT \
  --field deployment_branch_policy='{"protected_branches":false,"custom_branch_policies":false}'
```

## Step 3: Configure Staging Environment

### Staging Environment Variables (Public)
```bash
# Core configuration
gh variable set ECR_REPOSITORY --env staging --body "<ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/calculaud-be"
gh variable set AWS_REGION --env staging --body "us-east-1"
gh variable set AWS_BUILD_ROLE_ARN --env staging --body "arn:aws:iam::<ACCOUNT>:role/github-actions-build-role"

# Environment settings
gh variable set REPLICA_COUNT --env staging --body "2"
gh variable set DEBUG --env staging --body "false"

# Database configuration is now provided as full DATABASE_URL secret (see secrets section)

# S3 configuration (non-sensitive)
gh variable set S3_BUCKET --env staging --body "calculaud-staging-files"
gh variable set S3_BUCKET_URL --env staging --body "https://calculaud-staging-files.s3.us-east-1.amazonaws.com"
gh variable set S3_KEY_PREFIX --env staging --body "files/"

# Authentication configuration (non-sensitive URLs and identifiers)
gh variable set AUTH_JWKS_URL --env staging --body "https://your-auth-provider/.well-known/jwks.json"
gh variable set AUTH_ISSUER --env staging --body "https://your-auth-provider/"
gh variable set AUTH_AUDIENCE --env staging --body "calculaud-api"
gh variable set AUTH_TOKEN_URL --env staging --body "https://your-auth-provider/oauth/token"
gh variable set AUTH_OIDC_URL --env staging --body "https://your-auth-provider/"
gh variable set OAUTH_CLIENT_ID --env staging --body "calculaud-staging-client"

# Infrastructure configuration
gh variable set INGRESS_ENABLED --env staging --body "true"
gh variable set INGRESS_CLASS --env staging --body "alb"
gh variable set DOMAIN --env staging --body "api-staging.calculaud.com"
gh variable set SSL_CERT_ARN --env staging --body "arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT-ID"
gh variable set SERVICE_ACCOUNT_ROLE_ARN --env staging --body "arn:aws:iam::ACCOUNT:role/calculaud-staging-service-role"

# Resource configuration
gh variable set RESOURCES_REQUEST_MEMORY --env staging --body "512Mi"
gh variable set RESOURCES_REQUEST_CPU --env staging --body "200m"
gh variable set RESOURCES_LIMIT_MEMORY --env staging --body "2Gi"
gh variable set RESOURCES_LIMIT_CPU --env staging --body "1000m"

# Autoscaling configuration
gh variable set AUTOSCALING_ENABLED --env staging --body "true"
gh variable set AUTOSCALING_MIN_REPLICAS --env staging --body "2"
gh variable set AUTOSCALING_MAX_REPLICAS --env staging --body "8"

# Health check configuration
gh variable set HEALTHCHECK_LIVENESS_INITIAL_DELAY --env staging --body "30"
gh variable set HEALTHCHECK_READINESS_FAILURE_THRESHOLD --env staging --body "3"

# Application configuration
gh variable set LOG_LEVEL --env staging --body "INFO"
gh variable set WORKERS --env staging --body "4"
gh variable set MAX_FILE_SIZE_MB --env staging --body "256"
gh variable set DEFAULT_PAGE_SIZE --env staging --body "50"

# Optional existing secret name
gh variable set EXISTING_SECRET --env staging --body "calculaud-staging-secrets"
```

### Staging Environment Secrets (Private)
```bash
# Database connection (provide full DATABASE_URL)
gh secret set DATABASE_URL --env staging --body "postgresql://calculaud_staging:your-staging-db-password@calculaud-staging.cluster-xxx.us-east-1.rds.amazonaws.com:5432/calculaud_staging"

# S3 credentials
gh secret set S3_ACCESS_KEY --env staging --body "your-staging-s3-access-key"
gh secret set S3_SECRET_KEY --env staging --body "your-staging-s3-secret-key"

# Kubeconfig for cluster access
gh secret set KUBECONFIG --env staging --body "$(base64 -i ~/.kube/staging-config)"
```

## Step 4: Configure Testing Environment

### Testing Environment Variables (Public)
```bash
# Core configuration (shared with staging)
gh variable set ECR_REPOSITORY --env testing --body "<ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/calculaud-be"
gh variable set AWS_REGION --env testing --body "us-east-1"
gh variable set AWS_BUILD_ROLE_ARN --env testing --body "arn:aws:iam::<ACCOUNT>:role/github-actions-build-role"

# Environment settings (minimal for testing)
gh variable set REPLICA_COUNT --env testing --body "1"
gh variable set DEBUG --env testing --body "true"

# Database configuration is now provided as full DATABASE_URL secret (see secrets section)

# S3 configuration (shared test bucket)
gh variable set S3_BUCKET --env testing --body "calculaud-test-files"
gh variable set S3_BUCKET_URL --env testing --body "https://calculaud-test-files.s3.us-east-1.amazonaws.com"

# Authentication configuration (test environment)
gh variable set AUTH_JWKS_URL --env testing --body "https://your-test-auth-provider/.well-known/jwks.json"
gh variable set AUTH_ISSUER --env testing --body "https://your-test-auth-provider/"
gh variable set AUTH_AUDIENCE --env testing --body "calculaud-test-api"
gh variable set AUTH_TOKEN_URL --env testing --body "https://your-test-auth-provider/oauth/token"
gh variable set AUTH_OIDC_URL --env testing --body "https://your-test-auth-provider/"
gh variable set OAUTH_CLIENT_ID --env testing --body "calculaud-test-client"

# Infrastructure configuration (minimal for testing)
gh variable set INGRESS_ENABLED --env testing --body "false"

# Resource configuration (minimal for cost efficiency)
gh variable set RESOURCES_REQUEST_MEMORY --env testing --body "128Mi"
gh variable set RESOURCES_REQUEST_CPU --env testing --body "50m"
gh variable set RESOURCES_LIMIT_MEMORY --env testing --body "512Mi"
gh variable set RESOURCES_LIMIT_CPU --env testing --body "500m"

# Health check configuration (faster for testing)
gh variable set HEALTHCHECK_LIVENESS_INITIAL_DELAY --env testing --body "20"
gh variable set HEALTHCHECK_READINESS_FAILURE_THRESHOLD --env testing --body "2"

# Application configuration (testing optimized)
gh variable set LOG_LEVEL --env testing --body "DEBUG"
gh variable set WORKERS --env testing --body "1"
gh variable set MAX_FILE_SIZE_MB --env testing --body "128"
gh variable set DEFAULT_PAGE_SIZE --env testing --body "20"

# Optional existing secret name (empty for testing)
gh variable set EXISTING_SECRET --env testing --body ""
```

### Testing Environment Secrets (Private)
```bash
# Database connection (provide full DATABASE_URL)
gh secret set DATABASE_URL --env testing --body "postgresql://calculaud_test:your-test-db-password@calculaud-test.cluster-xxx.us-east-1.rds.amazonaws.com:5432/calculaud_test"

# S3 credentials (shared test bucket)
gh secret set S3_ACCESS_KEY --env testing --body "your-test-s3-access-key"
gh secret set S3_SECRET_KEY --env testing --body "your-test-s3-secret-key"
```

## Step 5: Environment Protection Rules (Optional)

### Add Protection Rules for Staging Environment
```bash
# Require review for staging deployments
gh api repos/:owner/:repo/environments/staging/deployment_protection_rules --method POST \
  --field type="required_reviewers" \
  --field reviewers='[{"type":"User","id":"YOUR_USER_ID"}]'

# Add wait timer for staging deployments
gh api repos/:owner/:repo/environments/staging/deployment_protection_rules --method POST \
  --field type="wait_timer" \
  --field wait_timer=5
```

## Step 6: Configure Branch Protection Rules

### Main Branch Protection
Enforce CI checks and pull request requirements before merging to main:

```bash
# Enable branch protection with required CI checks
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["CI / lint_and_test"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"dismiss_stale_reviews":true,"required_approving_review_count":1}' \
  --field restrictions=null
```

### Additional Branch Protection Settings (Optional)
```bash
# Require conversation resolution
gh api repos/:owner/:repo/branches/main/protection/required_conversation_resolution --method PUT

# Require signed commits (optional)
gh api repos/:owner/:repo/branches/main/protection/required_signatures --method POST

# Enable auto-delete of head branches after merge (repository setting)
gh api repos/:owner/:repo --method PATCH --field delete_branch_on_merge=true
```

### Branch Protection Features:
- ✅ **No direct pushes to main** - All changes via pull requests
- ✅ **CI must pass** - "CI / lint_and_test" check required 
- ✅ **Up-to-date branches** - PR branch must be current with main
- ✅ **Review requirement** - At least 1 approval needed
- ✅ **Admin enforcement** - Rules apply to repository admins too

## Step 7: Verify Configuration

```bash
# List environments
gh api repos/:owner/:repo/environments

# Check branch protection rules
gh api repos/:owner/:repo/branches/main/protection

# List staging environment variables
gh variable list --env staging

# List staging environment secrets  
gh secret list --env staging

# List testing environment variables
gh variable list --env testing

# List testing environment secrets
gh secret list --env testing
```

## Configuration Notes

### GitHub Environments Structure:

1. **Environment Scoped**: 
   - Secrets and variables are automatically injected based on workflow environment
   - Same variable names across environments, different values
   - Example: `DATABASE_URL` has different values in `staging` vs `testing` environments

2. **Clear Separation**:
   - **Variables** (public): Configuration that's not sensitive (URLs, resource limits, feature flags)
   - **Secrets** (private): Credentials and sensitive data (passwords, API keys)
   - **Environment-specific**: Each environment has its own isolated configuration

3. **Single Template**: 
   - One `values.yaml.template` works for all environments
   - Environment-specific behavior controlled through variable values

### Security Benefits:

- ✅ Environment-scoped access (testing secrets not accessible in staging jobs)
- ✅ Clear separation of secrets vs public configuration  
- ✅ Built-in audit trail and access controls
- ✅ Protection rules for production environments

### Customization Required:

1. Replace `<ACCOUNT>`, `<REGION>`, `<CERT-ID>` with your actual values
2. Replace `your-auth-provider` with your actual auth provider URLs
3. Replace database hostnames with your actual endpoints
4. Replace bucket names with your actual S3 bucket names
5. Adjust resource limits based on your needs
6. Replace `YOUR_USER_ID` with your actual GitHub user ID for protection rules

## Troubleshooting

### Test Environment Access
```bash
# Test access to staging environment
gh api repos/:owner/:repo/environments/staging

# Test access to testing environment  
gh api repos/:owner/:repo/environments/testing
```

### Branch Protection Issues
```bash
# Check branch protection status
gh api repos/:owner/:repo/branches/main/protection

# If status checks don't appear in protection rules:
# 1. Ensure CI workflow has run at least once on a PR
# 2. Check exact status check names in a PR's "Checks" tab
# 3. The format is usually: "[Workflow Name] / [Job Name]"

# Temporarily disable protection (emergency use only)
gh api repos/:owner/:repo/branches/main/protection --method DELETE
```

### Variable/Secret Management
```bash
# Update a variable
gh variable set VARIABLE_NAME --env ENVIRONMENT_NAME --body "new-value"

# Update a secret
gh secret set SECRET_NAME --env ENVIRONMENT_NAME --body "new-secret-value"

# Delete a variable
gh variable delete VARIABLE_NAME --env ENVIRONMENT_NAME

# Delete a secret
gh secret delete SECRET_NAME --env ENVIRONMENT_NAME
```

### Testing Your Setup
```bash
# Test branch protection by creating a failing PR:
# 1. Create a test PR with failing tests
# 2. Verify merge button is disabled until CI passes  
# 3. Fix tests, confirm merge becomes available
# 4. Verify staging deployment after merge to main
```