from setuptools import setup, find_packages

setup(
    name="tooltrust-sdk",
    version="0.1.4",
    packages=find_packages(),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "tooltrust=tooltrust.cli:main",
        ],
    },
)
