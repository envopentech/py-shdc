# PyPI Publishing Setup Guide

This guide explains how to set up automated PyPI publishing for the py-shdc project using GitHub Actions.

## Overview

The project includes two GitHub workflows:

1. **`tests.yml`** - Runs comprehensive tests, linting, and security checks on every push/PR
2. **`publish-to-pypi.yml`** - Automatically builds and publishes packages to PyPI on releases

## Setup Instructions

### 1. Configure PyPI Trusted Publishing

**Recommended Approach**: Use PyPI's trusted publishing feature (no API tokens needed!)

#### Step 1: Create PyPI Project
1. Go to [PyPI](https://pypi.org/) and create an account if you don't have one
2. Create a new project with the name `py-shdc` (or reserve the name)

#### Step 2: Configure Trusted Publishing
1. Go to your PyPI project settings
2. Navigate to "Publishing" → "Trusted publishers"
3. Add a new trusted publisher with these settings:
   - **PyPI Project Name**: `py-shdc`
   - **Owner**: `envopentech`
   - **Repository name**: `py-shdc`
   - **Workflow filename**: `publish-to-pypi.yml`
   - **Environment name**: `pypi`

#### Step 3: Configure Test PyPI (Optional but Recommended)
1. Go to [Test PyPI](https://test.pypi.org/) and create an account
2. Create a project with the name `py-shdc`
3. Configure trusted publishing with:
   - **PyPI Project Name**: `py-shdc`
   - **Owner**: `envopentech`
   - **Repository name**: `py-shdc`
   - **Workflow filename**: `publish-to-pypi.yml`
   - **Environment name**: `testpypi`

### 2. Configure GitHub Repository Environments

#### Step 1: Create Environments
1. Go to your GitHub repository: `https://github.com/envopentech/py-shdc`
2. Navigate to Settings → Environments
3. Create two environments:
   - **Name**: `pypi`
     - **Deployment protection rules**: Add yourself as required reviewer (optional)
   - **Name**: `testpypi`
     - **Deployment protection rules**: None needed for testing

#### Step 2: Environment URLs (Optional)
- Set environment URL for `pypi` to: `https://pypi.org/p/py-shdc`
- Set environment URL for `testpypi` to: `https://test.pypi.org/p/py-shdc`

### 3. Alternative: API Token Method

If you prefer using API tokens instead of trusted publishing:

#### Step 1: Generate API Tokens
1. **PyPI Token**:
   - Go to PyPI → Account Settings → API tokens
   - Create a token with scope limited to `py-shdc` project
   - Copy the token (starts with `pypi-`)

2. **Test PyPI Token**:
   - Go to Test PyPI → Account Settings → API tokens
   - Create a token with scope limited to `py-shdc` project
   - Copy the token (starts with `pypi-`)

#### Step 2: Add Secrets to GitHub
1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Add repository secrets:
   - **Name**: `PYPI_API_TOKEN`, **Value**: Your PyPI token
   - **Name**: `TEST_PYPI_API_TOKEN`, **Value**: Your Test PyPI token

#### Step 3: Modify Workflow
Update `.github/workflows/publish-to-pypi.yml` to use tokens instead of trusted publishing:

```yaml
# Replace the publish steps with:
- name: Publish distribution 📦 to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    password: ${{ secrets.PYPI_API_TOKEN }}

- name: Publish distribution 📦 to TestPyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    repository-url: https://test.pypi.org/legacy/
    password: ${{ secrets.TEST_PYPI_API_TOKEN }}
```

## Usage

### Automatic Publishing on Release

1. **Create a Release**:
   ```bash
   # Update version in pyproject.toml and setup.py
   git add .
   git commit -m "Bump version to 1.0.1"
   git tag v1.0.1
   git push origin main --tags
   ```

2. **Create GitHub Release**:
   - Go to GitHub → Releases → "Create a new release"
   - Choose the tag you just created (e.g., `v1.0.1`)
   - Add release notes
   - Click "Publish release"

3. **Automatic Process**:
   - GitHub Action will automatically trigger
   - Package will be built and tested
   - Published to PyPI
   - Signed with Sigstore
   - Artifacts uploaded to GitHub release

### Manual Testing with Test PyPI

1. **Manual Trigger**:
   - Go to GitHub → Actions → "Publish to PyPI"
   - Click "Run workflow"
   - Check "Publish to Test PyPI instead of PyPI"
   - Click "Run workflow"

2. **Test Installation**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ py-shdc
   ```

### Version Management

The project version is defined in two places and must be kept in sync:
- `pyproject.toml` → `project.version`
- `setup.py` → `version`

**Best Practice**: Use a version bumping tool like `bump2version`:

```bash
pip install bump2version
echo '[bumpversion]
current_version = 1.0.0
commit = True
tag = True

[bumpversion:file:pyproject.toml]
search = version = "{current_version}"
replace = version = "{new_version}"

[bumpversion:file:setup.py]
search = version="{current_version}"
replace = version="{new_version}"' > .bumpversion.cfg

# Then bump versions with:
bump2version patch  # 1.0.0 → 1.0.1
bump2version minor  # 1.0.1 → 1.1.0
bump2version major  # 1.1.0 → 2.0.0
```

## Security Features

### Included Security Measures

1. **Trusted Publishing**: No long-lived secrets in GitHub
2. **Sigstore Signing**: All releases are cryptographically signed
3. **Environment Protection**: Manual approval for production releases (optional)
4. **Security Scanning**: Bandit and Safety checks in CI

### Additional Recommendations

1. **Enable Branch Protection**:
   - Require PR reviews
   - Require status checks to pass
   - Require branches to be up to date

2. **Enable Dependabot**:
   ```yaml
   # .github/dependabot.yml
   version: 2
   updates:
     - package-ecosystem: "pip"
       directory: "/"
       schedule:
         interval: "weekly"
   ```

3. **Monitor Releases**:
   - Set up notifications for new releases
   - Monitor PyPI download statistics
   - Watch for security advisories

## Troubleshooting

### Common Issues

1. **"Project does not exist" Error**:
   - Ensure the project name exists on PyPI
   - Check trusted publishing configuration
   - Verify environment names match exactly

2. **Permission Denied**:
   - Check GitHub repository permissions
   - Verify environment configuration
   - Ensure tokens have correct scope (if using tokens)

3. **Build Failures**:
   - Check the tests workflow passes first
   - Verify package builds locally: `python -m build`
   - Check for missing dependencies in `pyproject.toml`

4. **Version Conflicts**:
   - Ensure version numbers are unique
   - Check that version exists in both `pyproject.toml` and `setup.py`
   - Verify tag format matches release version

### Support

For issues with:
- **PyPI**: Check [PyPI Help](https://pypi.org/help/)
- **GitHub Actions**: Check [GitHub Actions Documentation](https://docs.github.com/en/actions)
- **Trusted Publishing**: Check [PyPA Documentation](https://docs.pypi.org/trusted-publishers/)

## Next Steps

1. Set up the PyPI project and trusted publishing
2. Configure GitHub environments
3. Test with a patch release to Test PyPI
4. Create your first official release
5. Monitor and maintain the publishing pipeline

The workflow is now ready to automatically handle your PyPI releases! 🚀
