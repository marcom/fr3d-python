#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='fr3d',
    version='0.0.1',
    packages=find_packages(include=['fr3d', 'fr3d.*']),
    include_package_data=True,
    url='',
    license='LICENSE.txt',
    install_requires=["numpy", "scipy"],
    description='Python implementation of FR3D',
    long_description="",
    data_files=[('fr3d/classifiers', ['fr3d/classifiers/template.html','fr3d/classifiers/H_bonding_Atoms_from_Isostericity_Table.csv'])]
)
