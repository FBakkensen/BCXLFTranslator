from setuptools import setup, find_packages

setup(
    name='BCXLFTranslator',
    version='1.0.0',  # Major version bump for breaking change (removal of terminology functionality)
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'googletrans==4.0.2',  # Required for Google Translate functionality
        'aiohttp',  # Required by googletrans for async HTTP requests
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-asyncio',
        ],
    },
    entry_points={
        'console_scripts': [
            'bcxlftranslator=bcxlftranslator.main:main',
        ],
    },
    author='Your Name',
    description='A simple CLI for BCXLF translation using Google Translate.',
    url='',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
