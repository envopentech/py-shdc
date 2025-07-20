---
name: Release Request
about: Request a new release of py-shdc
title: 'Release v[VERSION]'
labels: 'release'
assignees: ''

---

## Release Information

**Version**: v[X.Y.Z]
**Release Type**: [patch/minor/major]

## Pre-Release Checklist

- [ ] All tests are passing
- [ ] Documentation is up to date
- [ ] CHANGELOG.md has been updated
- [ ] Version numbers updated in:
  - [ ] `pyproject.toml`
  - [ ] `setup.py`
  - [ ] `shdc/__init__.py`
- [ ] No security vulnerabilities detected
- [ ] Test PyPI release successful (if applicable)

## Changes

### Added
- 

### Changed
- 

### Deprecated
- 

### Removed
- 

### Fixed
- 

### Security
- 

## Release Process

1. **Prepare Release**:
   ```bash
   # Update version numbers
   bump2version [patch|minor|major]
   
   # Push changes and tags
   git push origin main --tags
   ```

2. **Create GitHub Release**:
   - Go to [Releases](https://github.com/envopentech/py-shdc/releases)
   - Click "Create a new release"
   - Select the tag created above
   - Add release notes from this issue
   - Publish release

3. **Verify Release**:
   - [ ] GitHub Action completed successfully
   - [ ] Package available on [PyPI](https://pypi.org/project/py-shdc/)
   - [ ] Installation works: `pip install py-shdc==[VERSION]`
   - [ ] Basic functionality test passes

## Post-Release

- [ ] Announce release (if applicable)
- [ ] Update dependent projects (if applicable)
- [ ] Close this issue
