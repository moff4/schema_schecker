#!/usr/bin/env python3
import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='schema_checker',
    version='1.1.0',
    author='Komissarov Andrey',
    author_email='Komissar.off.andrey@gmail.com',
    description='Another schema validator :)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/moff4/schema_schecker',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)
