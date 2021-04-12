
__author__ = 'matth'

from distutils.core import setup
from setuptools import find_packages

setup(
    name='py-exe-builder',
    version='0.2',
    packages = find_packages(),
    license='Apache License, Version 2.0',
    description='Uses py2exe to create small exe stubs that leverage a full python installation, rather than packing the required pyc files in to the executable.',
    long_description=open('README.md').read(),
    url='http://www.j5int.com/',
    author='j5 International',
    author_email='support@j5int.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: Developers',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires = ["py2exe"],
)
