"""
Configuration d'installation pour Artifact-Scythe
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the Readme file for more info
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="scythe",
    version="0.1.0",
    author="Eliel MENGUE",
    author_email="mengueeliel712@gmail.com",
    description="CLI tools for cleaning artifacts and builds",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/elielMengue/scythe",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "scythe=scythe.cli:cli",
        ],
    },
)