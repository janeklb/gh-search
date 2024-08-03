import os

from setuptools import setup, find_packages


def get_version():
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(curr_dir, "version.txt")) as version_file:
        return version_file.read().strip()


def get_readme():
    this_directory = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
        return f.read()


install_requires = [
    "click~=8.1.7",
    "click-config-file~=0.6.0",
    "PyGithub~=2.3.0",
    "ruamel.yaml~=0.18.6",
]

dev_requires = [
    "black~=24.8.0",
    "coverage~=7.6.0",
    "flake8~=7.1.0",
    "isort~=5.13.2",
    "mypy~=1.11.1",
    "pip-tools~=7.4.1",
    "pytest-mock~=3.14.0",
    "pytest~=8.3.2",
]


setup(
    name="gh-search",
    version=get_version(),
    url="https://github.com/janeklb/gh-search",
    author="Janek Lasocki-Biczysko",
    description="Github search from the cli",
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude="tests"),
    classifiers=[
        "Programming Language :: Python :: 3.12",
    ],
    install_requires=install_requires,
    setup_requires=["pytest-runner"],
    tests_require=dev_requires,
    python_requires=">=3.12",
    extras_require={
        "dev": dev_requires,
    },
    entry_points={"console_scripts": ["gh-search=ghsearch.cli:cli"]},
)
