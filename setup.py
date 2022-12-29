#!/usr/bin/env python

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

requirements = open("requirements.txt").read().split()
test_requirements = open("requirements_test.txt").read().split()
dev_requirements = open("requirements_dev.txt").read().split()

setup(  #
    author="Oren Ben-Kiki",
    author_email="oren@ben-kiki.org",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    description="Ninja Build Generation",
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    long_description_content_type='text/x-rst',
    include_package_data=True,
    keywords="ninja,make",
    name="ningen",
    packages=find_packages(include=["ningen"]),
    test_suite="tests",
    tests_require=test_requirements,
    extras_require = {"dev": dev_requirements},
    url="https://github.com/orenbenkiki/ningen.git",
    version="0.4.0",
)
