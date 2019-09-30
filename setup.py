#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requirements = [
    # TODO: put package requirements here
    'wheel',
]

# When running `pip install .` this ensures all requirements are installed in one go
try:
    with open('requirements.txt') as f:
        requirements.extend(f.readlines())
except FileNotFoundError:
    # tox doesn't like this for some reason
    pass

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='netsocadmin',
    version='1.0.0',
    description='NetsocAdmin',
    long_description='NetsocAdmin',
    author='UCC Netsoc',
    author_email='admin@netsoc.co',
    url='https://github.com/UCCNetworkingSociety/netsocadmin2',
    py_modules=['netsocadmin'],

    # Example for a module that's a directory with __init__.py etc.
    # You'd have this *instead* of py_modules.
    packages=[
        'netsocadmin',
    ],
    package_dir={'netsocadmin': 'netsocadmin'},

    scripts=[
        # 'bin/netsocadmin',
    ],
    install_requires=requirements,
    dependency_links=[],
    tests_require=test_requirements,
    test_suite='tests',
    include_package_data=True,
    zip_safe=False,
    keywords='netsocadmin',
    classifiers=[
    ],
)
