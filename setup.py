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
    "click~=7.1.2",
    "PyGithub~=1.54.1",
]

dev_requires = [
    "black~=20.8b1",
    "flake8~=3.7.7",
    "isort~=5.6.4",
    "mypy~=0.761",
    "pytest~=4.4.2",
    "pytest-mock~=1.10.4",
    "coverage~=4.4.1",
    "pip-tools~=5.3.1",
]


setup(
    name="gh-search",
    version=get_version(),
    url="https://github.com/janeklb/gh-search",
    author="Janek Lasocki-Biczysko",
    author_email="janek.lb@gmail.net",
    description="Github search from the cli",
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude="tests"),
    include_package_data=True,
    platforms="any",
    install_requires=install_requires,
    setup_requires=["pytest-runner"],
    tests_require=dev_requires,
    extras_require={
        "dev": dev_requires,
    },
    entry_points={"console_scripts": ["gh-search=ghsearch.cli:cli"]},
)
