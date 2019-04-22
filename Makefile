.PHONY: clean-pyc clean-build clean
PACKAGE_NAME=netsocadmin
package_branch=$(shell echo -n ${DRONE_BRANCH} | tr -c '[:alnum:]-' '-')
package_version=${DRONE_BUILD_NUMBER}+${package_branch}
url_package_version=$(shell echo -n ${package_version} | sed "s/+/%2B/g")
DEB_BASENAME=${PACKAGE_NAME}_${package_version}

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "test - run tests quickly with the default Python"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "dist - package"
	@echo "install - install the package to the active Python's site-packages"

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr deb_dist
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -f .coverage
	rm -fr htmlcov/

test:
	tox

coverage:
	coverage run -m --source ${PACKAGE_NAME} tests.test_netsocadmin
	coverage report -m
	coverage html

dist: clean
	python3.7 setup.py sdist bdist_wheel

install: clean
	pip install .
