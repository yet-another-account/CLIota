import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="cliota",
    version="0.0.1",
    author="eukaryote",
    description="A CLI wallet for Iota.",

    setup_requires=['pytest-runner'],
    tests_require=['pytest'],

    license="MIT",
    keywords="iota,faucet,cryptocurrency",
    url="",
    packages=find_packages('.', exclude=('test', 'test.*')),
    long_description=read('README.md'),
    install_requires=read('requirements.txt').split('\n'),
    entry_points={
        'console_scripts': [
            'cliota = cliota:main',
        ]
    },
    package_data={'': ['nodes.json']}
)
