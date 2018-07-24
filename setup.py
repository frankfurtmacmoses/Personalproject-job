"""
setup for watchmen project
"""
import os

from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, 'README.md')) as f:
    README = f.read()

BASE = 'watchmen/' if os.path.isdir(os.path.join(HERE, 'watchmen')) else ''

PREQ = os.path.join(HERE, BASE + "requirements.txt")
PREQ_DEV = os.path.join(HERE, BASE + "requirements-dev.txt")

setup(
    name='watchmen',
    version='0.0.1',
    description='CyberIntel Watchmen',
    long_description=README,
    classifiers=[
        "Programming Language :: Python",
    ],
    author='CyberIntel Dev',
    author_email='dhanshew@infoblox.com',
    url='',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[i.strip() for i in open(PREQ).readlines()],
    tests_require=[i.strip() for i in open(PREQ_DEV).readlines()],
    test_suite="tests",
    entry_points="",
)
