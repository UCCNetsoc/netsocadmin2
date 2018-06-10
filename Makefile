.PHONY: clean-pyc clean-build clean
package_branch=$(shell echo -n ${DRONE_BRANCH} | tr -c '[:alnum:]-' '-')
package_version=${DRONE_BUILD_NUMBER}+${package_branch}
url_package_version=$(shell echo -n ${package_version} | sed "s/+/%2B/g")

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "test - run tests quickly with the default Python"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "release - package a release"
	@echo "dist - package"
	@echo "upload - package and upload a release to the object store"
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
	coverage run -m --source netsocadmin tests.test_netsocadmin
	coverage report -m
	coverage html

release: clean

	DEBEMAIL="UCC Netsoc <admin@netsoc.co>" dch --newversion "${package_version}" \
		--distribution unstable \
		"Netsoc Admin package"
	dpkg-buildpackage -uc -us


dist: clean
	python3.5 setup.py sdist bdist_wheel

install: clean
	pip install .

upload: clean
	pip install minio
	ls -alt ./.ci
	python3.5 ./.ci/object_store_upload.py \
		--obj-store-location ${CI_OBJ_LOCATION} \
		--project-name ${DRONE_REPO} \
		--access-key ${CI_OBJ_ACCESS_KEY} \
		--secret-key ${CI_OBJ_SECRET_KEY} \
		--file-location "${ARTIFACTS}/*.deb"