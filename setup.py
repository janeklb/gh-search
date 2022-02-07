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
    "click~=8.0.3",
    "click-config-file~=0.6.0",
    "PyGithub~=1.54.1",
    "ruamel.yaml~=0.17.16",
]

dev_requires = [
    "black~=22.1.0",
    "coverage~=6.3.1",
    "flake8~=3.7.7",
    "isort~=5.10.1",
    "mypy~=0.931",
    "pip-tools~=5.3.1",
    "pytest-mock~=3.7.0",
    "pytest~=6.2.5",
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
    include_package_data=True,
    platforms="any",
    install_requires=install_requires,
    setup_requires=["pytest-runner"],
    tests_require=dev_requires,
    python_requires=">=3.7",
    extras_require={
        "dev": dev_requires,
    },
    entry_points={"console_scripts": ["gh-search=ghsearch.cli:cli"]},
)
