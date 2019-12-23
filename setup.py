#!/usr/bin/env python
from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="tfont",
    description="A font object model that serializes to JSON & compiles to OpenType.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Adrien Tétar",
    author_email="adri-from-59@hotmail.fr",
    url="https://github.com/adrientetar/tfont",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages("src"),
    install_requires=[
        "fonttools>=3.24.0",
    ],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Text Processing :: Fonts",
        "License :: OSI Approved :: MIT License",
    ],
)
