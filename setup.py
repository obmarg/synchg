
from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup
import synchg

setup(
    name='SyncHg',
    version=synchg.__version__,
    url='http://github.com/obmarg/synchg/',
    license='BSD',
    author='Graeme Coupar',
    author_email='grambo@grambo.me.uk',
    description='A simple script & library to handle syncing remote '
                'mercuial repositories',
    long_description=open('README.rst').read(),
    # if you would be using a package instead use packages instead
    # of py_modules:
    packages=['synchg'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'plumbum',
        'clint'
    ],
    entry_points={
        'console_scripts': [
            'synchg = synchg.script:run'
            ]
        },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
        'Topic :: Software Development :: Version Control',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
