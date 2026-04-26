from setuptools import setup , find_packages

with open('./requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name = "Chess_SQL",
    version = "1.0.1",
    author = "Sai Teja",
    packages = find_packages(),
    install_requires = requirements
)