from setuptools import find_packages, setup


with open("readme.md", "r", encoding="utf-8") as f:
	long_description = f.read()

install_requires = [
	"notifiers",
	"mailgun_api @ git+https://github.com/accessibleapps/mailgun-API.git",
]


setup(
	name="logsetup",
	version="1.0",
	author="Carter Temm",
	author_email="cartertemm@gmail.com",
	description="Python log initialization made easy",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/cartertemm/logsetup",
	install_requires=install_requires,
	packages=find_packages(),
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Programming Language :: Python :: 3",
		"Topic :: Software Development :: Libraries :: Python Modules",
		"Topic :: System :: Logging",
	]
)