#!/usr/bin/env python3

import setuptools


setuptools.setup(
    name='mesonwrap',
    version='0.0.4',
    author='The Meson development team',
    license='Apache 2',
    url='https://github.com/mesonbuild/wrapweb',
    packages=['mesonwrap', 'wrapweb'],
    scripts=['mesonwrap.py'],
)
