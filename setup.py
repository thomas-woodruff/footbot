from setuptools import find_packages, setup

setup(
    name="footbot",
    version="0.1.0",
    url='https://github.com/thomas-woodruff/footbot',
    author='thomas-woodruff',
    license='All rights reserved.',
    packages=find_packages(),
    package_data={'': ['*.sql', '*.json']},
    include_package_data=True,
)
