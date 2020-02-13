from setuptools import setup, find_packages

with open('requirements.txt', 'r') as f:
	requirements = f.read().splitlines()

setup(
	name='mcmtest',
	version='0.0.1',
	author='Alp Akpinar',
	author_email='aakpinar@bu.edu',
	description='Package for local McM test submissions using HTCondor.',
	packages=find_packages(),	
	install_requires=requirements,
	scripts=['mcmtest/execute/mcmsubmit']
)


