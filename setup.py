#!/usr/bin/env python3

import setuptools
import unittest


def discover_tests():
    test_loader = unittest.TestLoader()
    return test_loader.discover('.', pattern='*_test.py')


setuptools.setup(
    name='mesonwrap',
    version='0.0.4',
    author='The Meson development team',
    license='Apache 2',
    url='https://github.com/mesonbuild/wrapweb',
    packages=['mesonwrap', 'wrapweb'],
    package_data={
        'wrapweb': ['templates/*.html'],
    },
    install_requires=[
        'Flask',
        'GitPython',
        'PyGithub',
    ],
    scripts=['mesonwrap.py'],
    test_suite='setup.discover_tests',
)
