"""Setup configuration for Zettelkasten CLI tool."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="zettelkasten",
    version="0.1.0",
    author="Your Name",
    description="A CLI tool for managing Zettelkasten notes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "pydantic>=2.0.0",
        "textual>=0.40.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "zk=zettelkasten.cli:main",
        ],
    },
)

