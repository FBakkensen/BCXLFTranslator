from setuptools import setup, find_packages

setup(
    name='BCXLFTranslator',
    version='0.1.0',
    py_modules=['main'],
    install_requires=[
        'argparse',
    ],
    entry_points={
        'console_scripts': [
            'bcxlftranslator=main:main',
        ],
    },
    author='Your Name',
    description='A simple CLI for BCXLF translation.',
    url='',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
