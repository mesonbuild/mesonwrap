#!/usr/bin/env python3

import setuptools
import unittest


def discover_tests():
    test_loader = unittest.TestLoader()
    return test_loader.discover('.', pattern='*_test.py')


if __name__ == '__main__':
    setuptools.setup(
        name='mesonwrap',
        version='0.0.6',
        author='The Meson development team',
        license='Apache 2',
        url='https://github.com/mesonbuild/wrapweb',
        packages=[
            'mesonwrap',
            'mesonwrap.tools',
            'wrapweb',
        ],
        package_data={
            'wrapweb': ['templates/*.html'],
        },
        install_requires=[
            'Flask',
            'GitPython',
            'PyGithub',
        ],
        entry_points={
            'console_scripts': [
                'mesonwrap=mesonwrap.cli:Command',
            ],
        },
        test_suite='setup.discover_tests',
    )
