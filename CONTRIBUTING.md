# Contributor Quick Start Guide

Welcome to py-shdc! This guide will help you get started with contributing to the project.

## 🚀 Quick Setup

1. **Fork and Clone**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/py-shdc.git
   cd py-shdc
   ```

2. **Set Up Development Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev,test]"
   ```

3. **Run Tests**:
   ```bash
   pytest
   ```

## 🔄 Development Workflow

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes and Test**:
   ```bash
   # Make your changes
   pytest  # Run tests
   black .  # Format code
   isort .  # Sort imports
   flake8 .  # Check linting
   ```

3. **Commit and Push**:
   ```bash
   git add .
   git commit -m "Add your feature description"
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request**:
   - Go to GitHub and create a PR
   - Ensure all CI checks pass

## 📦 Release Process (Maintainers Only)

### Automated Release via GitHub Actions

1. **Update Version Numbers**:
   ```bash
   # Install bump2version if not already installed
   pip install bump2version
   
   # Bump version (patch/minor/major)
   bump2version patch  # 1.0.0 → 1.0.1
   ```

2. **Push Changes**:
   ```bash
   git push origin main --tags
   ```

3. **Create GitHub Release**:
   - Go to [Releases](https://github.com/envopentech/py-shdc/releases)
   - Click "Create a new release"
   - Select the new tag (e.g., `v1.0.1`)
   - Add release notes
   - Click "Publish release"

4. **Automatic Process**:
   - ✅ GitHub Action triggers automatically
   - ✅ Package built and tested
   - ✅ Published to PyPI
   - ✅ Release artifacts uploaded

### Manual Testing (Optional)

Test releases using our helper script:

```bash
# Dry run (checks only)
python scripts/release.py --version 1.0.1 --dry-run

# Test on Test PyPI
python scripts/release.py --version 1.0.1 --test-pypi

# Full release
python scripts/release.py --version 1.0.1 --release
```

### Emergency Manual Release

If GitHub Actions fail, you can manually release:

```bash
# Build package
python -m build

# Check package
python -m twine check dist/*

# Upload to PyPI (requires API token)
python -m twine upload dist/*
```

## 🔧 Project Structure

```
py-shdc/
├── shdc/                    # Main package
│   ├── core/               # Core protocol implementation
│   ├── crypto/             # Cryptographic functions
│   ├── network/            # Network transport
│   ├── cli/                # Command-line tools
│   └── utils/              # Utilities
├── examples/               # Example applications
├── docs/                   # Documentation
├── tests/                  # Test files
├── scripts/                # Helper scripts
└── .github/workflows/      # CI/CD workflows
```

## 🧪 Testing

- **Unit Tests**: `pytest tests/`
- **Integration Tests**: `pytest test_integration.py`
- **Coverage**: `pytest --cov=shdc`
- **Linting**: `flake8`, `black`, `isort`, `mypy`

## 📚 Documentation

- **Build Docs**: `cd docs && make html`
- **Live Docs**: Available at [py-shdc.readthedocs.io](https://py-shdc.readthedocs.io/)
- **API Docs**: Auto-generated from docstrings

## 🔒 Security

- **Dependency Scanning**: Automatic via Dependabot
- **Security Linting**: Bandit in CI
- **Vulnerability Checks**: Safety checks in CI

## 💡 Tips

1. **Pre-commit Hooks**: Install for automatic formatting
   ```bash
   pre-commit install
   ```

2. **IDE Setup**: Use VS Code with Python extension for best experience

3. **Environment Variables**: Copy `.env.example` to `.env` for local config

4. **Debugging**: Use `python -m pdb` or your IDE's debugger

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/envopentech/py-shdc/issues)
- **Discussions**: [GitHub Discussions](https://github.com/envopentech/py-shdc/discussions)
- **Documentation**: [Read the Docs](https://py-shdc.readthedocs.io/)

## 📋 Checklist for New Contributors

- [ ] Read the [Code of Conduct](https://github.com/envopentech/py-shdc/blob/main/CODE_OF_CONDUCT.md)
- [ ] Set up development environment
- [ ] Run tests successfully
- [ ] Read the [Contributing Guidelines](https://github.com/envopentech/py-shdc/blob/main/CONTRIBUTING.md)
- [ ] Look at [Good First Issues](https://github.com/envopentech/py-shdc/labels/good%20first%20issue)

Happy contributing! 🎉
