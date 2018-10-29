#!/usr/bin/env python3
from setuptools import setup

setup(
    name="tap-kit",
    version="0.1.1",
    description="Framework for quickly developing singer taps with minimal custom code",
    author="Simon Data",
    url="http://simondata.com",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_kit"],
    install_requires=[
        "singer-python==5.2.0",
        'requests==2.18.4',
        "pendulum==1.2.0",
    ],
    packages=["tap_kit"],
    include_package_data=True,
)
