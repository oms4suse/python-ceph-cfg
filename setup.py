from ceph_cfg.__version__ import version
from sys import version_info

if version_info < (2, 6):
    import sys
    print "Please use a newer version of python"
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

# we want this module for nosetests
try:
    import multiprocessing
except ImportError:
    # its not critical if this fails though.
    pass

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
    data_files=[('share/doc/ceph-cfg-%s' % (version),['README.md','LICENSE','CHANGELOG.rst'])],
    tests_require=[
        'coverage >= 3.0',
        'nose >= 0.10.0',
        'mock',
    ],
    setup_requires=[
        'nose',
    ],
    test_suite = 'nose.collector',
    )
