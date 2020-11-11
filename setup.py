from setuptools import setup

with open("README.md", "r") as f:
	long_description = f.read()

setup(
	name="IliasDownloaderUniMA",
	version='0.5.0',
	packages=['IliasDownloaderUniMA'],
	author='Jonathan Helgert',
	author_email='jhelgert@mail.uni-mannheim.de',
	description='A simple package to download files from ilias.uni-mannheim.de',
	long_description=long_description,
	long_description_content_type="text/markdown",
	python_requires='>=3.8',
	classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
	install_requires=[
		"dateparser",
		"bs4",
		"requests",
		"python-dateutil",
		"lxml",
	]
)
