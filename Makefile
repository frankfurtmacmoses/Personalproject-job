# Makefile for cyberint-watchmen
.PHONY: all build clean clean-all cmd cover dev-setup docker list setup show test unittest pytest functest venv

PROJECT := watchmen
# predefined/default environment variables
BUILD_ENV ?= dev
CHECK_STACK ?= true
PREFIX_NAME ?= CyberInt
STACK_NAME ?= watchmen

GITHUB_REPO := cyberint-watchmen
GITHUB_CORP := Infoblox-CTO

BUILDS_DIR := builds
BUILDS_ALL := $(BUILDS_DIR)/$(PROJECT)-lambdas.zip
COVERAGE_DIR := htmlcov
COVERAGE_REPORT := $(COVERAGE_DIR)/index.html
COVERAGE_ARGS := --cov=. --cov-report=term --cov-report=html --cov-fail-under=97

SYSTOOLS := cp find jq ln rm pip tar tee virtualenv xargs zip
PYTEST_ARGS := --flakes --pep8 --pylint -s -vv
PYVENV_NAME ?= .venv
MAKE_VENV := tools/make_venv.sh
MAKE_PUBLISH := tools/publish-builds.sh
MAKE_CF := tools/deploy-cf.sh
MAKE_DEPLOY := tools/deploy.sh
MAKE_RUN := tools/run.sh

# set AWS default region for moto3 testing
AWS_DEFAULT_REGION ?= us-east-1

DOCKER_USER := infobloxcto
DOCKER_IMAG := $(PROJECT)
DOCKER_TAGS := $(DOCKER_USER)/$(DOCKER_IMAG)
DOCKER_DENV := $(wildcard /.dockerenv)
DOCKER_PATH := $(shell which docker)

# returns "" if all undefined; otherwise, there is defined.
ifdef_any_of = $(filter-out undefined,$(foreach v,$(1),$(origin $(v))))
# usage:
#   * checking if any defined
#     - ifneq ($(call ifdef_any_of,VAR1 VAR2),)
#   * checking if none defined
#     - ifeq ($(call ifdef_any_of,VAR1 VAR2),)

# returns "" if all defined; otherwise, there is undefined.
ifany_undef = $(filter undefined,$(foreach v,$(1),$(origin $(v))))
# usage:
#   * checking if any undefined
#     - ifneq ($(call ifany_undef,VAR1 VAR2),)
#   * checking if both defined
#     - ifeq ($(call ifany_undef,VAR1 VAR2),)

# Don't need to start docker in 2 situations:
ifneq ("$(DOCKER_DENV)","")  # assume inside docker container
    DONT_RUN_DOCKER := true
endif
ifeq ("$(DOCKER_PATH)","")   # docker command is NOT installed
    DONT_RUN_DOCKER := true
endif

# Don't need to start virtualenv in 2 situations:
ifneq ("$(DOCKER_DENV)","")  # assume inside docker container
	DONT_RUN_PYVENV := true
endif
ifneq ("$(VIRTUAL_ENV)","")  # assume python venv is activated
	DONT_RUN_PYVENV := true
endif


all: clean-all dev-setup test

list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs

clean clean-cache:
	@echo
	@echo "--- Removing pyc and log files"
	find . -name '.DS_Store' -type f -delete
	find . -name \*.pyc -type f -delete -o -name \*.log -delete
	rm -Rf .cache
	rm -Rf .vscode
	rm -Rf $(PROJECT)/.cache
	rm -Rf $(PROJECT)/tests/__pycache__
	@echo
	@echo "--- Removing coverage files"
	find . -name '.coverage' -type f -delete
	rm -rf .coveragerc
	rm -rf cover
	rm -rf $(PROJECT)/cover
	rm -rf $(COVERAGE_DIR)
	@echo
	@echo "--- Removing *.egg-info"
	rm -Rf *.egg-info
	rm -Rf $(PROJECT)/*.egg-info
	@echo
	@echo "--- Removing tox virtualenv"
	rm -Rf $(PROJECT)/.tox*
	@echo
ifneq ("$(VIRTUAL_ENV)","")
	@echo "--- Cleaning up pip list in $(VIRTUAL_ENV) ..."
	pip freeze | grep -v "^-e" | xargs pip uninstall -y || true
else
	@echo "--- Removing virtual env"
	rm -Rf $(PROJECT)/.venv*
endif
	@echo
	@echo "--- Removing build"
	rm -rf $(PROJECT)_build.tee
	rm -rf $(BUILDS_DIR)
	@echo
	@echo "- DONE: $@"

clean-all: clean-cache
	@echo
ifeq ("$(wildcard /.dockerenv)","")
	# not in a docker container
	@echo "--- Removing docker image $(DOCKER_TAGS)"
	docker rm -f $(shell docker ps -a|grep $(DOCKER_IMAG)|awk '{print $1}') 2>/dev/null || true
	docker rmi -f $(shell docker images -a|grep $(DOCKER_TAGS) 2>&1|awk '{print $1}') 2>/dev/null || true
	rm -rf docker_build.tee
endif
	@echo
	find . -name '*.tee' -type f -delete
	@echo "--- Uninstalling $(PROJECT)"
	pip uninstall $(PROJECT) -y 2>/dev/null; true
	rm -Rf database/*.bak
	@echo
	@echo "- DONE: $@"

check-tools:
	@echo
	@echo "--- Checking for presence of required tools: $(SYSTOOLS)"
	$(foreach tool,$(SYSTOOLS),\
	$(if $(shell which $(tool)),$(echo "boo"),\
	$(error "ERROR: Cannot find '$(tool)' in system $$PATH")))
	@echo
	@echo "- DONE: $@"


# build targets
$(PROJECT)_build.tee:
	@echo
ifeq ("$(DONT_RUN_PYVENV)", "true")
	tools/build.sh all | tee $(PROJECT)_build.tee
	@echo "- DONE: $@"
else
	VENV_NAME=$(PYVENV_NAME) $(MAKE_VENV) "$@"
endif

build: test-all build-lambdas
	@echo ""
	@echo "- DONE: $@"
	@echo ""

build-lambdas: $(PROJECT)_build.tee
	@echo ""
	@echo "- DIST: $(BUILDS_ALL)"
	@echo ""
	@echo "- DONE: $@"
	@echo ""

deploy-cf: build
	@echo
	@echo "--- Publising AWS cloudformation [$(BUILD_ENV)] ---"
	BUILD_ENV=$(BUILD_ENV) $(MAKE_PUBLISH)
	@echo
	@echo "--- Deploying AWS cloudformation [$(BUILD_ENV)] ---"
	CHECK_STACK=$(CHECK_STACK) PREFIX_NAME="$(PREFIX_NAME)" $(MAKE_CF) "$(STACK_NAME)" "$(BUILD_ENV)"
	@echo "- DONE: $@"

deploy-cf-prod: build
	@echo
	@echo "--- Publising AWS cloudformation [prod] ---"
	BUILD_ENV=prod $(MAKE_PUBLISH)
	@echo
	@echo "--- Deploying AWS cloudformation [prod] ---"
	CHECK_STACK=$(CHECK_STACK) PREFIX_NAME="$(PREFIX_NAME)" $(MAKE_CF) "$(STACK_NAME)" prod
	@echo "- DONE: $@"

deploy-cf-test: build
	@echo
	@echo "--- Publising AWS cloudformation [test] ---"
	BUILD_ENV=test $(MAKE_PUBLISH)
	@echo
	@echo "--- Deploying AWS cloudformation [test] ---"
	CHECK_STACK=$(CHECK_STACK) PREFIX_NAME="$(PREFIX_NAME)" $(MAKE_CF) "$(STACK_NAME)" test
@echo "- DONE: $@"

# setup and dev-setup targets
$(PYVENV_NAME)/bin/activate: check-tools $(PROJECT)/requirements-dev.txt
	@echo
ifeq ("$(VIRTUAL_ENV)", "")
	@echo "Checking python venv: $(PYVENV_NAME)"
	@echo "----------------------------------------------------------------------"
	test -d $(PYVENV_NAME) || virtualenv --no-site-packages $(PYVENV_NAME)
	@echo
	@echo "--- Installing required dev packages [$(PYVENV_NAME)] ..."
	$(PYVENV_NAME)/bin/pip install -Ur $(PROJECT)/requirements-dev.txt
	@echo
	$(PYVENV_NAME)/bin/pip list
	# touch $(PYVENV_NAME)/bin/activate
else
	@echo "--- Cleaning up pip list in $(VIRTUAL_ENV) ..."
	pip freeze | grep -v "^-e" | xargs pip uninstall -y || true
	@echo
	@echo "--- Setting up $(PROJECT) develop ..."
	python setup.py develop
	@echo
	@echo "--- Installing required dev packages ..."
	# running setup.py in upper level of `$(PROJECT)` folder to register the package
	pip install -r $(PROJECT)/requirements-dev.txt
	@echo
	pip list
endif
	@echo
	@echo "- DONE: $@"

dev-setup: $(PYVENV_NAME)/bin/activate
	@echo "----------------------------------------------------------------------"
	@echo "Python environment: $(PYVENV_NAME)"
	@echo "- Activate command: source $(PYVENV_NAME)/bin/activate"
	@echo



setup:
	@echo
	@echo "--- Starting setup ..."
	python setup.py install
	cd $(PROJECT) && pip install -r requirements.txt
	@echo
	@echo "- DONE: $@"


# test targets
coverage-only show:
ifeq ("$(wildcard /.dockerenv)","")
	@echo "--- Opening $(COVERAGE_REPORT)"
ifeq ($(OS), Windows_NT) # Windows
	start "$(COVERAGE_REPORT)"
else ifeq ($(shell uname),Darwin) # Mac OS
	open "$(COVERAGE_REPORT)"
else
	nohup xdg-open "$(COVERAGE_REPORT)" >/dev/null 2>&1 &
endif
else
	@echo ""
	@echo "Cannot open test coverage in the container."
endif

coverage cover: test coverage-only

python-test unittest: clean-cache check-tools
	@echo
ifeq ("$(DONT_RUN_PYVENV)", "true")
	@echo "--- Starting unittest discover ..."
	@echo
	# python -m unittest discover --buffer --catch --failfast --verbose
	AWS_DEFAULT_REGION=$(AWS_DEFAULT_REGION) \
	python -m unittest discover -bcfv
	@echo
	@echo "- DONE: $@"
else
	VENV_NAME=$(PYVENV_NAME) $(MAKE_VENV) dev-setup "$@"
endif

nosetest nosetests: clean-cache check-tools
	@echo
ifeq ("$(DONT_RUN_PYVENV)", "true")
	@echo "--- Starting nosetests ..."
	@echo
	# nosetests must be in the same path with setup.cfg
	AWS_DEFAULT_REGION=$(AWS_DEFAULT_REGION) \
	nosetests
	@echo "......................................................................"
	@echo "See coverage report: cover/index.html"
	@echo
	@echo "- DONE: $@"
else
	VENV_NAME=$(PYVENV_NAME) $(MAKE_VENV) dev-setup "$@"
endif

functest: clean-cache check-tools
	@echo
ifeq ("$(DONT_RUN_PYVENV)", "true")
	@echo "--- Starting pytest for functional tests ..."
	@echo
	AWS_DEFAULT_REGION=$(AWS_DEFAULT_REGION) \
	pytest -c setup.cfg -m "functest" $(PYTEST_ARGS) --cov-fail-under=20
	@echo
	@echo "- DONE: $@"
else
	VENV_NAME=$(PYVENV_NAME) $(MAKE_VENV) "$@"
endif

test pytest: clean-cache check-tools
	@echo
ifeq ("$(DONT_RUN_PYVENV)", "true")
	@echo "--- Starting pytest for unit tests ..."
	@echo
	AWS_DEFAULT_REGION=$(AWS_DEFAULT_REGION) \
	pytest -c setup.cfg -m "not functest" $(PYTEST_ARGS)

	@echo
	@echo "- DONE: $@"
else
	VENV_NAME=$(PYVENV_NAME) $(MAKE_VENV) "$@"
endif

test-all-only:
	@echo
ifeq ("$(DONT_RUN_PYVENV)", "true")
	# @echo "--- Setup $(PROJECT) develop [$@] ..."
	# python setup.py develop
	# @echo
	pip list
	@echo
	@echo "--- Starting pytest for all tests ..."
	AWS_DEFAULT_REGION=$(AWS_DEFAULT_REGION) \
	pytest -c setup.cfg $(PYTEST_ARGS)
else
	VENV_NAME=$(PYVENV_NAME) $(MAKE_VENV) "$@"
endif

test-all: clean-all dev-setup test-all-only
	@echo
	@echo "- DONE: $@"


dvenv:
	@echo
ifeq ("$(DONT_RUN_PYVENV)", "true")
	@echo "----------------------------------------------------------------------"
	@echo "Python environment: $(VIRTUAL_ENV)"
	@echo "- Activate command: source $(VIRTUAL_ENV)/bin/activate"
	@echo "- Deactivating cmd: deactivate"
	@echo "----------------------------------------------------------------------"
else
	@echo "Cleaning up python venv: $(PYVENV_NAME)"
	rm -rf $(PYVENV_NAME)
endif
	@echo ""
	@echo "- DONE: $@"
	@echo ""

venv: check-tools
	@echo
ifeq ("$(VIRTUAL_ENV)", "")
	@echo "Preparing for venv: [$(PYVENV_NAME)] ..."
	virtualenv --no-site-packages $(PYVENV_NAME)
	@echo "----------------------------------------------------------------------"
	@echo "Python environment: $(PYVENV_NAME)"
	@echo "- Activate command: source $(PYVENV_NAME)/bin/activate"
else
	@echo "----------------------------------------------------------------------"
	@echo "- Activated python venv: $(VIRTUAL_ENV)"
endif
	@echo "----------------------------------------------------------------------"
	@echo "- DONE: $@"
	@echo ""
