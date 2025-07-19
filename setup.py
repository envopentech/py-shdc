from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Core dependencies - keep minimal for production use
install_requires = [
    "cryptography>=41.0.0",
    "dataclasses-json>=0.6.0",
    "typing-extensions>=4.7.0; python_version<'3.10'",
]

setup(
    name="py-shdc",
    version="1.0.0",
    author="Argo Nickerson",
    author_email="argo@envopen.org",
    description="Python implementation of the Smart Home Device Communications Protocol (SHDC)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="LGPL-3.0-or-later",
    url="https://github.com/envopentech/py-shdc",
    project_urls={
        "Homepage": "https://github.com/envopentech/py-shdc",
        "Documentation": "https://py-shdc.readthedocs.io/",
        "Repository": "https://github.com/envopentech/py-shdc.git",
        "Issues": "https://github.com/envopentech/py-shdc/issues",
        "Changelog": "https://github.com/envopentech/py-shdc/blob/main/CHANGELOG.md",
    },
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "shdc": ["py.typed"],
    },
    keywords=[
        "smart-home", "iot", "protocol", "communication", "security", 
        "cryptography", "automation", "networking", "embedded", "devices"
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Home Automation",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
        "Topic :: System :: Hardware",
        "Environment :: No Input/Output (Daemon)",
        "Natural Language :: English",
    ],
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
            "myst-parser>=2.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "shdc-hub=shdc.cli.hub:main",
            "shdc-sensor=shdc.cli.sensor:main",
        ],
    },
)