from ceph_cfg.__version__ import version
from sys import version_info

if version_info < (2, 6):
    import sys
    print("Please use a newer version of python")
    sys.exit(1)



try:
    from setuptools import setup, find_packages
except ImportError:
	try:
            from distutils.core import setup
	except ImportError:
            from ez_setup import use_setuptools
            use_setuptools()
            from setuptools import setup, find_packages


from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def run_tests(self):
        import shlex
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


setup(name='ceph_cfg',
    version=version,
    description="library for configuring ceph",
    long_description="""This library is inteded to provide an abstraction for 
    python tools for configuring ceph. It was intended to be used for salt but
    as it grew it became clear that this library could be used with or without
    salt""",
    author="O M Synge",
    author_email="osynge@suse.com",
    license='Apache License (2.0)',
    install_requires=[],
    url = 'https://github.com/oms4suse/python-ceph-cfg.git',
    packages = ['ceph_cfg'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research'
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        ],

    scripts=[],
    tests_require=[
        'coverage >= 3.0',
        'pytest >=2.1.3',
        'mock >=1.0b1',
        ],
    cmdclass = {'test': PyTest},
    )
