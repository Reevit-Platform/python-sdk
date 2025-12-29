from setuptools import setup, find_packages

setup(
    name="reevit",
    version="0.3.2",
    description="Reevit Python SDK",
    author="Reevit",
    packages=find_packages(),
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
