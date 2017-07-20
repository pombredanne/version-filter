#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'semantic_version==2.6.0',
]

test_requirements = [
    'pytest',
]

setup(
    name='version_filter',
    version='0.5.0',
    description="A semantic and regex version filtering/masking library.",
    long_description=readme + '\n\n' + history,
    author="Dropseed",
    author_email='python@dropseed.io',
    url='https://github.com/dropseedlabs/version-filter',
    packages=[
        'version_filter',
    ],
    package_dir={'version_filter':
                 'version_filter'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='version_filter',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
