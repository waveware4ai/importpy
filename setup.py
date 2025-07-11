from setuptools import setup, find_packages

setup(
    name='importpy',
    version='0.1.1',
    author='14mhz',
    author_email='14mhz@hanmail.net',    
    description='This small package is used to import at module level instead of package level.',
    keywords='python import package mudule lazy',
    url='https://github.com/waveware4ai/importpy',
    long_description=open('README.md', 'r', encoding='UTF8').read(),
    long_description_content_type='text/markdown',
    license='Apache-2.0 license',
    python_requires='>=3.8',   
    packages=['importpy'],
)

