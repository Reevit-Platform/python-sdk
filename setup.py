import os

from setuptools import setup, find_packages

# Load the version without importing the package (which would require
# runtime dependencies like requests at build time).
_version = {}
with open(os.path.join(os.path.dirname(__file__), "reevit", "_version.py")) as f:
    exec(f.read(), _version)

with open(os.path.join(os.path.dirname(__file__), "README.md"), encoding="utf-8") as f:
    _long_description = f.read()

setup(
    name="reevit",
    version=_version["__version__"],
    description="Reevit Python SDK",
    long_description=_long_description,
    long_description_content_type="text/markdown",
    author="Reevit",
    license="MIT",
    url="https://github.com/Reevit-Platform/python-sdk",
    project_urls={
        "Documentation": "https://docs.reevit.io",
    },
    packages=find_packages(exclude=("tests", "tests.*")),
    install_requires=[
        "requests>=2.25.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
