#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup configuration for playwright-simple library.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="playwright-simple",
    version="1.0.0",
    description="A simple and intuitive library for writing Playwright tests, designed for QAs without deep programming knowledge",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ForgeFast Team",
    author_email="dev@forgefast.com",
    url="https://github.com/forgefast/playwright-simple",
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "types-PyYAML>=6.0.0",
        ],
        "odoo": [
            # No additional Python dependencies required
            # Odoo is a web application, accessed via Playwright
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
    ],
    keywords="playwright testing automation qa e2e",
    project_urls={
        "Documentation": "https://github.com/forgefast/playwright-simple/blob/main/docs/README.md",
        "Source": "https://github.com/forgefast/playwright-simple",
        "Tracker": "https://github.com/forgefast/playwright-simple/issues",
    },
)


