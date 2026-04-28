from setuptools import setup, find_packages

setup(
    name="arc_code",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "arc-code=arc_code.main:main",
        ],
    },
    python_requires=">=3.8",
)