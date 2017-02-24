#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

requirements = [
    'transitions',
    'voicelabs'
]

test_requirements = [
    'elasticsearch==5.0.1',
    'elasticsearch-dsl==5.0.0'
]

setup(
    name='alexafsm',
    version='0.1.0',
    description="Finite-state machine library for building complex Alexa conversations",
    long_description=readme + '\n\n' + history,
    author="Allen AI",
    author_email='a-dialog-research@allenai.org',
    url='https://github.com/allenai/alexafsm',
    packages=[
        'alexafsm',
    ],
    package_dir={'alexafsm':
                 'alexafsm'},
    include_package_data=True,
    install_requires=requirements,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='alexafsm, alexa skill, finite-state machine, fsm, dialog, dialog state management',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
