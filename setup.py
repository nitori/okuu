#!/usr/bin/env python

from distutils.core import setup

setup(
    name='Okuu',
    version='1.0',
    description='HTTP information fetching library',
    author='Lars Peter Søndergaard',
    author_email='lps@chireiden.net',
    packages=['okuu'],
    py_modules=['okuu_danbooru', 'okuu_webpage', 'okuu_youtube'],
    install_requires=[
        'aiohttp>=0.18.4',
        'beautifulsoup4',
    ],
)
