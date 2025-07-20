#!/usr/bin/env python3
"""
Release helper script for py-shdc

This script helps automate the release process by:
1. Checking that all version numbers are in sync
2. Running tests
3. Building the package
4. Optionally pushing to Test PyPI

Usage:
    python scripts/release.py --version 1.0.1 --dry-run
    python scripts/release.py --version 1.0.1 --test-pypi
    python scripts/release.py --version 1.0.1 --release
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def check_version_consistency(version):
    """Check that version is consistent across all files."""
    project_root = Path(__file__).parent.parent

    # Check pyproject.toml
    pyproject_file = project_root / "pyproject.toml"
    with open(pyproject_file) as f:
        content = f.read()
        if f'version = "{version}"' not in content:
            print(f"❌ Version {version} not found in pyproject.toml")
            return False

    # Check setup.py
    setup_file = project_root / "setup.py"
    with open(setup_file) as f:
        content = f.read()
        if f'version="{version}"' not in content:
            print(f"❌ Version {version} not found in setup.py")
            return False

    # Check __init__.py
    init_file = project_root / "shdc" / "__init__.py"
    with open(init_file) as f:
        content = f.read()
        if f'__version__ = "{version}"' not in content:
            print(f"❌ Version {version} not found in shdc/__init__.py")
            return False

    print(f"✅ Version {version} is consistent across all files")
    return True


def run_tests():
    """Run the test suite."""
    print("Running tests...")
    result = run_command("python -m pytest", check=False)
    if result.returncode != 0:
        print("❌ Tests failed")
        return False
    print("✅ All tests passed")
    return True


def run_linting():
    """Run code quality checks."""
    print("Running linting...")

    commands = [
        "python -m flake8 shdc/ --count --select=E9,F63,F7,F82 --show-source --statistics",
        "python -m black --check shdc/",
        "python -m isort --check-only shdc/",
        "python -m mypy shdc/",
    ]

    for cmd in commands:
        result = run_command(cmd, check=False)
        if result.returncode != 0:
            print(f"❌ Linting failed: {cmd}")
            return False

    print("✅ All linting checks passed")
    return True


def build_package():
    """Build the package."""
    print("Building package...")
    run_command("python -m build --clean")
    print("✅ Package built successfully")


def check_package():
    """Check the built package."""
    print("Checking package...")
    run_command("python -m twine check dist/*")
    print("✅ Package checks passed")


def upload_to_test_pypi():
    """Upload to Test PyPI."""
    print("Uploading to Test PyPI...")
    run_command("python -m twine upload --repository testpypi dist/*")
    print("✅ Uploaded to Test PyPI")


def main():
    parser = argparse.ArgumentParser(description="Release helper for py-shdc")
    parser.add_argument("--version", required=True, help="Version to release")
    parser.add_argument(
        "--dry-run", action="store_true", help="Run checks without building/uploading"
    )
    parser.add_argument("--test-pypi", action="store_true", help="Upload to Test PyPI")
    parser.add_argument(
        "--release", action="store_true", help="Create release tag and push"
    )

    args = parser.parse_args()

    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print(f"🚀 Preparing release {args.version}")

    # Check version consistency
    if not check_version_consistency(args.version):
        print("❌ Version inconsistency detected. Please update all version numbers.")
        sys.exit(1)

    # Run tests
    if not run_tests():
        print("❌ Tests failed. Please fix before releasing.")
        sys.exit(1)

    # Run linting
    if not run_linting():
        print("❌ Code quality checks failed. Please fix before releasing.")
        sys.exit(1)

    if args.dry_run:
        print("✅ Dry run completed successfully. Ready for release!")
        return

    # Build package
    build_package()
    check_package()

    if args.test_pypi:
        upload_to_test_pypi()
        print(f"🎉 Version {args.version} uploaded to Test PyPI!")
        print("Test installation with:")
        print(
            f"pip install --index-url https://test.pypi.org/simple/ py-shdc=={args.version}"
        )

    if args.release:
        # Create and push tag
        tag = f"v{args.version}"
        run_command(f"git tag {tag}")
        run_command(f"git push origin {tag}")
        print(f"🏷️  Tag {tag} created and pushed")
        print("🎉 Release process initiated!")
        print(
            "Create a GitHub release at: https://github.com/envopentech/py-shdc/releases"
        )


if __name__ == "__main__":
    main()
