---
name: Release
about: Template for creating a new release
title: 'Release v[VERSION]'
labels: release
assignees: ''

---

## Release Checklist

### Pre-Release
- [ ] All planned features for this release are complete
- [ ] All tests are passing
- [ ] Documentation is updated
- [ ] Version number is decided (following semantic versioning)

### Release Preparation
- [ ] Create release branch: `git checkout -b release/v[VERSION]`
- [ ] Update version in `app/config.py` if needed
- [ ] Update CHANGELOG.md with release notes
- [ ] Test the release branch thoroughly
- [ ] Create PR for release branch

### Release Process
- [ ] Merge release PR to main
- [ ] Create GitHub release with tag `v[VERSION]`
- [ ] Verify Docker images are built and pushed
- [ ] Test deployed version
- [ ] Announce release to team

### Post-Release
- [ ] Monitor for any issues
- [ ] Update any deployment environments
- [ ] Clean up release branch: `git branch -d release/v[VERSION]`

## Release Notes Template

### 🚀 New Features
- 

### 🐛 Bug Fixes
- 

### 🔧 Improvements
- 

### 📚 Documentation
- 

### 🛠️ Technical Changes
- 

### 🔒 Security
- 

### ⚠️ Breaking Changes
- 

### 🗑️ Deprecated
- 

## Deployment Information

**Docker Images:**
- `username/calculaud-be:v[VERSION]`
- `username/calculaud-be:[VERSION]`
- `username/calculaud-be:latest`

**Supported Platforms:**
- linux/amd64