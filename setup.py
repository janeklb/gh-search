import os

from setuptools import setup, find_packages


def get_version():
    # Versioning approach adopted as suggested in https://packaging.python.org/en/latest/single_source_version/
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(curr_dir, 'version.txt')) as version_file:
        return version_file.read().strip()


install_requires = [
    'click~=7.1.2',
    'PyGithub~=1.54.1',
]

dev_requires = [
    'black~=20.8b1',
    'flake8~=3.7.7',
    'isort~=5.6.4',
    'mypy~=0.761',
    'pytest~=4.4.2',
    'pytest-mock~=1.10.4',
    'coverage~=4.4.1',
    'pip-tools~=5.3.1',
]


setup(
    name="gh-search",
    version=get_version(),
    url="git@github.com:janeklb/gh-search.git",
    author="Janek Lasocki-Biczysko",
    author_email="janek.lb@gmail.net",
    description="Github search from the cli",
    packages=find_packages(),
    include_package_data=True,
    platforms="any",
    install_requires=install_requires,
    setup_requires=["pytest-runner"],
    tests_require=dev_requires,
    extras_require={
        'dev': dev_requires,
    },
    entry_points={
        'console_scripts': [
            'gh-search=ghsearch.main:cli'
        ]
    }
)
