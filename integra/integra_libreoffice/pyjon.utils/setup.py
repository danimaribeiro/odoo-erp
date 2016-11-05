# -*- encoding: utf-8 -*-
from setuptools import setup, find_packages

version = '0.8'

setup(
    name='pyjon.utils',
    version=version,
    description=(
        "Useful tools library with classes to do singletons, "
        "dynamic function pointers..."
    ),
    long_description=open("README.rst").read(),
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='',
    author='Florent Aide',
    author_email='florent.aide@gmail.com',
    url='',
    license='MIT',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['pyjon'],
    include_package_data=True,
    zip_safe=False,
    test_suite='nose.collector',
    install_requires=[
        'setuptools',
        'six',
        # -*- Extra requirements: -*-
    ],
    entry_points="""
    # -*- Entry points: -*-
    """,
)
