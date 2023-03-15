# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='yasmon',
    version='0.1.0',
    description='Python system monitor with callbacks and logging',
    long_description=readme,
    author='Michał Ł. Mika',
    author_email='hzkn22@mika.sh',
    url='https://github.com/m1ka05/',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    entry_points = {
        'console_scripts': ['yasmon=yasmon:main'],
    }
)
