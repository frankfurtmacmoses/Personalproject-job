# Makefile at repository root
#
# Author: Jason Zhu <jason_zhuyx@hotmail.com> (https://github.com/dockerian)
#
# Dependencies:
#   * Python 2.7 virtualenv or Python 3 venv module (if USE_PYTHON3=true)
#   * setup.py, setup.cfg, .pylintrc
#   * tools/make_venv.sh
#   * docker and tools/run.sh (to build docker image and run in container)
#   * $(PROJECT)/requirements-dev.txt (for dev and testing)
#   * $(PROJECT)/requirements.txt (for production)
#   * $(SYSTOOLS)
#
.PHONY: clean clean-cache

# Project name at top level of the repository
PROJECT := watchmen

############################################################
# Makefile variables and functions
############################################################
DOCKER_USER := infobloxcto
DOCKER_NAME := watchmen
DOCKER_IMAG := $(DOCKER_USER)/$(DOCKER_NAME)
DOCKER_TAGS := $(DOCKER_USER)/$(DOCKER_NAME)
DOCKER_DENV := $(wildcard /.dockerenv)
DOCKER_PATH := $(shell which docker)

BUILD_ENV ?= test
CLOUD_FORMATION := cloudformation
CONFIG_DIR := configs
COVERAGE_DIR := htmlcov
COVERAGE_REPORT := $(COVERAGE_DIR)/index.html
ENDPOINTS_JSON := endpoints.json
FEEDS_TO_CHECK_JSON := feeds_to_check.json
JUPITER := jupiter
MANHATTAN := manhattan
PROCESS := process
PROJECT := watchmen
S3_PROD_BUCKET := cyber-intel
S3_SAAS_BUCKET := ib-cyberint-prod-deploys
S3_SAAS_TEST_BUCKET := cyber-intel-saas-test
S3_TEST_BUCKET := cyber-intel-test
SNS_ATG_PATH := $(CLOUD_FORMATION)/sns/atg.yaml
SNS_ATG_S3_PATH := $(CLOUD_FORMATION)/sns_atg.yaml
SNS_SAAS_PATH := $(CLOUD_FORMATION)/sns/saas.yaml
SNS_SAAS_S3_PATH := $(CLOUD_FORMATION)/sns_saas.yaml
SYSTOOLS := find rm python tee xargs zip

USE_PYTHON3 := true
PIPLIST_ALL := $(PROJECT)/requirements.txt
PIPLIST_DEV := $(PROJECT)/requirements-dev.txt
PY_LIB_PATH := $(shell python -c "import site; print(site.getsitepackages()[0])")
PYTEST_ARGS := --flakes --pep8 --pylint -s -vv --cov-report term-missing
NOSE_2_ARGS := --output-buffer -v --with-coverage --coverage $(PROJECT) --coverage-report html --coverage-report term
UTTEST_ARGS := --buffer --catch --failfast --verbose
# Python venv (virtual env) directory name (without full path)
PYVENV_NAME ?= .venv

MAKE_BUILD := tools/build.sh
MAKE_DEPLOY := cloudformation/deploy-cf.sh
MAKE_VENV := tools/make_venv.sh
MAKE_RUN := tools/run.sh

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
ifneq ("$(DOCKER_DENV)", "")  # assume inside docker container
	DONT_RUN_DOCKER := true
endif
ifeq ("$(DOCKER_PATH)", "")   # docker command is NOT installed
	DONT_RUN_DOCKER := true
endif

# Don't need venv insider docker (in most situations)
ifneq ("$(DOCKER_DENV)", "")  # assume inside docker container
	DONT_RUN_PYVENV := true
endif
# Don't start venv (virtual env) if it is already activated:
ifneq ("$(VIRTUAL_ENV)", "")  # assume python venv is activated
	DONT_RUN_PYVENV := true
endif


############################################################
# Makefile targets
############################################################
.PHONY: list
list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | \
	awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | \
	sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs

.PHONY: check-tools
check-tools:
	@echo
	@echo "--- Checking for presence of required tools: $(SYSTOOLS)"
	$(foreach tool,$(SYSTOOLS),\
	$(if $(shell which $(tool)),$(echo "boo"),\
	$(error "ERROR: Cannot find '$(tool)' in system $$PATH")))
	@echo
	@echo "- DONE: $@"

clean clean-cache:
	@echo
	@echo "--- Removing pyc and log files"
	find . -name '.DS_Store' -type f -delete
	find . -name \*.pyc -type f -delete -o -name \*.log -delete
	find . -name '__pycache__' -type d -delete
	rm -Rf .cache
	rm -Rf .pytest_cache
	rm -Rf $(PROJECT)/.cache
	rm -rf log*.txt
	@echo
	@echo "--- Removing coverage files"
	find . -name '.coverage' -type f -delete
	find . -name '$(COVERAGE_DIR)' -type d | xargs rm -rf
	rm -rf cover
	rm -rf $(PROJECT)/cover
	rm -rf cover
	@echo
	@echo "--- Removing *.egg-info"
	rm -Rf *.egg-info
	rm -Rf $(PROJECT)/*.egg-info
	@echo
	@echo "--- Removing tox virtualenv"
	rm -Rf $(PROJECT)/.tox*
	rm -Rf .tox
	@echo
	@echo "--- Removing build"
	rm -rf $(PROJECT)_build.tee
	rm -rf build*
	@echo
	@echo "- DONE: $@"

clean-all: clean-cache
	@echo
ifeq ("$(DOCKER_DENV)", "")
	# not in a docker container
	@echo "--- Removing docker image $(DOCKER_TAGS)"
	docker rm -f $(shell docker ps -a|grep $(DOCKER_NAME)|awk '{print $1}') 2>/dev/null || true
	docker rmi -f $(shell docker images -a|grep $(DOCKER_TAGS) 2>&1|awk '{print $1}') 2>/dev/null || true
	rm -rf docker_build.tee
endif
	@echo
ifneq ("$(VIRTUAL_ENV)", "")
	@echo "--- Cleaning up pip list in $(VIRTUAL_ENV) ..."
	python -m pip freeze | grep -v '^-e' | grep -v '^#' | grep -v 'pkg-resources' | xargs pip uninstall -y || true
	@echo ''
	@echo '**********************************************************************'
	@echo '* Please `deactivate` '"$(PYVENV_NAME) before cleaning all eggs and virtual env *"
	@echo '**********************************************************************'
else
	@echo "--- Removing virtual env"
	rm -rf *.tee
	rm -Rf $(PYVENV_NAME)
	rm -Rf .venv*
	rm -Rf .eggs
endif
	@echo
	@echo "- DONE: $@"


############################################################
# Makefile targets for venv (virtual env)
############################################################
$(PYVENV_NAME).tee: $(PIPLIST_DEV) $(PIPLIST_ALL)
	@make dev-setup-venv
	@echo
	@echo "- DONE: $(PYVENV_NAME)"

.PHONY: dev-setup-venv dev-setup
dev-setup-venv dev-setup: clean-cache check-tools
	@echo
ifneq ("$(VIRTUAL_ENV)", "")
	@echo "--- Cleaning up pip list in $(VIRTUAL_ENV) ..."
	python -m pip install --upgrade pip || true
	python -m pip freeze | grep -v '^-e' | grep -v '^#' | grep -v 'pkg-resources' | xargs pip uninstall -y || true
	@echo
	@echo "--- Setting up $(PROJECT) develop ..."
	# disabling setup.py due to easy_install issue on ubuntu
	# python setup.py develop
	@echo
	@echo "--- Installing required dev packages ..."
	# running setup.py in upper level of `$(PROJECT)` folder to register the package
	python -m pip install -r $(PIPLIST_ALL) | tee $(PYVENV_NAME).tee
	python -m pip install -r $(PIPLIST_DEV) | tee $(PYVENV_NAME).tee
	@echo
	python -m pip list
else
	@echo "Checking python venv: $(PYVENV_NAME)"
	@echo "----------------------------------------------------------------------"
	USE_PYTHON3=$(USE_PYTHON3) VENV_NAME=$(PYVENV_NAME) $(MAKE_VENV) "$@"
	# @touch $(PYVENV_NAME).tee
	@echo
endif
	@echo
	@echo "- DONE: $@"

.PHONY: setup test-setup
setup test-setup: $(PYVENV_NAME).tee
	@echo "----------------------------------------------------------------------"
	@echo "Python environment: $(PYVENV_NAME)"
	@echo "- Activate command: source $(PYVENV_NAME)/bin/activate"
	@echo

.PHONY: venv-clean dvenv
venv-clean dvenv:
	@echo
ifneq ("$(VIRTUAL_ENV)", "")
	@echo "----------------------------------------------------------------------"
	@echo "Python environment: $(VIRTUAL_ENV)"
	@echo "- Activate command: source $(VIRTUAL_ENV)/bin/activate"
	@echo "- Deactivating cmd: deactivate"
	@echo "----------------------------------------------------------------------"
else
	@echo "Cleaning up python venv: $(PYVENV_NAME)"
	rm -rf $(PYVENV_NAME)
	rm -Rf .eggs
endif
	@echo ""
	@echo "- DONE: $@"
	@echo ""

.PHONY: venv
venv: check-tools
	@echo
ifeq ("$(VIRTUAL_ENV)", "")
	@echo "Preparing for venv: [$(PYVENV_NAME)] ..."
	python3 -m venv $(PYVENV_NAME)
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

############################################################
# Makefile targets for testing
############################################################
.PHONY: coverage-only show
coverage-only show:
	@echo ""
ifeq ("$(DOCKER_DENV)", "")
	@echo "--- Opening $(COVERAGE_REPORT)"
ifeq ($(OS), Windows_NT) # Windows
	start "$(COVERAGE_REPORT)"
else ifeq ($(shell uname),Darwin) # Mac OS
	open "$(COVERAGE_REPORT)"
else
	nohup xdg-open "$(COVERAGE_REPORT)" >/dev/null 2>&1 &
endif
else
	@echo "- WARNING: Cannot open test coverage in the container."
endif

.PHONY: coverage cover
coverage cover: test coverage-only

bdd:
	@echo
ifeq ("$(DONT_RUN_PYVENV)", "true")
	@echo "--- Starting feature test ..."
	@echo
	PYTHONPATH=. behave tests/features
else
	USE_PYTHON3=$(USE_PYTHON3) VENV_NAME=$(PYVENV_NAME) $(MAKE_VENV) "$@"
endif
	@echo
	@echo "- DONE: $@"

functest: clean-cache check-tools
	@echo
ifeq ("$(DONT_RUN_PYVENV)", "true")
	@echo "--- Starting pytest for functional tests ..."
	@echo
	PYTHONPATH=. pytest -c setup.cfg -m "functest" $(PYTEST_ARGS) --cov-fail-under=20
	@echo
	@echo "- DONE: $@"
else
	USE_PYTHON3=$(USE_PYTHON3) VENV_NAME=$(PYVENV_NAME) $(MAKE_VENV) "$@"
endif

nosetest nosetests: clean-cache check-tools test-setup
	@echo
ifeq ("$(DONT_RUN_PYVENV)", "true")
	@echo "--- Starting nose2 tests ..."
	@echo
	PYTHONPATH=. nose2 $(NOSE_2_ARGS)
	@echo "......................................................................"
	@echo "See coverage report: $(COVERAGE_REPORT)"
	@echo
	@echo "- DONE: $@"
else
	USE_PYTHON3=$(USE_PYTHON3) VENV_NAME=$(PYVENV_NAME) $(MAKE_VENV) dev-setup "$@"
endif

python-test unittest: clean-cache check-tools test-setup
	@echo
ifeq ("$(DONT_RUN_PYVENV)", "true")
	@echo "--- Starting unittest discover ..."
	@echo
	# python -m unittest discover ${UTTEST_ARGS}
	PYTHONPATH=. python -m unittest discover -bcfv
	@echo
	@echo "- DONE: $@"
else
	USE_PYTHON3=$(USE_PYTHON3) VENV_NAME=$(PYVENV_NAME) $(MAKE_VENV) dev-setup "$@"
endif

pytest test: clean-cache check-tools test-setup test-only
	@echo
	@echo "- DONE: $@"

test-all: clean-all dev-setup-venv test-all-only
	@echo
	@echo "- DONE: $@"

test-all-only:
	@echo
ifeq ("$(DONT_RUN_PYVENV)", "true")
	# @echo "--- Setup $(PROJECT) develop [$@] ..."
	# python setup.py develop
	# @echo
	python -m pip list
	@echo
	@echo "--- Starting pytest for all tests ..."
	PYTHONPATH=. pytest -c setup.cfg $(PYTEST_ARGS)
	@echo
	@echo "- DONE: $@"
else
	USE_PYTHON3=$(USE_PYTHON3) VENV_NAME=$(PYVENV_NAME) $(MAKE_VENV) "$@"
endif

test-only:
	@echo
ifeq ("$(DONT_RUN_PYVENV)", "true")
	@echo "--- Python lib: $(PY_LIB_PATH)"
	@echo
	@echo "--- Starting pytest for unit tests ..."
	@echo
	PYTHONPATH=. pytest -c setup.cfg -m 'not functest' $(PYTEST_ARGS)
	@echo
	@echo "- DONE: $@"
else
	USE_PYTHON3=$(USE_PYTHON3) VENV_NAME=$(PYVENV_NAME) $(MAKE_VENV) "$@"
endif


############################################################
# build and deploy targets
############################################################
build: clean-cache build-only
build-only:
	@echo
	BUILD_ENV=$(BUILD_ENV) USE_PYTHON3=$(USE_PYTHON3) $(MAKE_BUILD)
	@echo
	@echo "- DONE: $@"

build-test: clean-cache build-test-only
build-test-only:
	@echo
	BUILD_ENV=test USE_PYTHON3=$(USE_PYTHON3) $(MAKE_BUILD)
	@echo
	@echo "- DONE: $@"

deploy-atg-test: clean
	@echo
	aws s3 cp $(SNS_ATG_PATH) s3://$(S3_TEST_BUCKET)/$(PROJECT)/$(SNS_ATG_S3_PATH)
	@echo
	BUILD_ENV=test ACCOUNT=atg BUCKET=cyber-intel-test FEATURE=watchmen DEPLOY_FILE=cf_atg.yaml $(MAKE_DEPLOY)
	@echo
	@echo "- DONE :$@"

deploy-atg-prod: clean
	@echo
	aws s3 cp $(SNS_ATG_PATH) s3://$(S3_PROD_BUCKET)/$(PROJECT)/$(SNS_ATG_S3_PATH)
	@echo
	BUILD_ENV=prod ACCOUNT=atg BUCKET=cyber-intel FEATURE=watchmen DEPLOY_FILE=cf_atg.yaml $(MAKE_DEPLOY)
	@echo
	@echo "- DONE :$@"

deploy-cyberintel-test: clean
	@echo
	BUILD_ENV=test ACCOUNT=cyberintel BUCKET=cyberintel-test FEATURE=watchmen-cyberintel DEPLOY_FILE=cf_cyberintel.yaml $(MAKE_DEPLOY)
	@echo
	@echo "- DONE :$@"

deploy-cyberintel-prod: clean
	@echo
	BUILD_ENV=prod ACCOUNT=cyberintel BUCKET=cyber-intel-prod FEATURE=watchmen-cyberintel DEPLOY_FILE=cf_cyberintel.yaml $(MAKE_DEPLOY)
	@echo
	@echo "- DONE: $@"

deploy-saas-test: clean
	@echo
	aws s3 cp $(SNS_SAAS_PATH) s3://$(S3_SAAS_TEST_BUCKET)/$(PROJECT)/$(SNS_SAAS_S3_PATH)
	@echo
	BUILD_ENV=test ACCOUNT=atg BUCKET=cyber-intel-saas-test FEATURE=watchmen-saas DEPLOY_FILE=cf_saas.yaml $(MAKE_DEPLOY)
	@echo
	@echo "- DONE :$@"

deploy-saas-prod: clean
	@echo
	aws s3 cp $(SNS_SAAS_PATH) s3://$(S3_SAAS_BUCKET)/$(PROJECT)/$(SNS_SAAS_S3_PATH)
	@echo
	DRY_RUN_ONLY=true BUILD_ENV=prod ACCOUNT=saas BUCKET=ib-cyberint-prod-deploys FEATURE=watchmen DEPLOY_FILE=cf_saas.yaml $(MAKE_DEPLOY)
	@echo
	@echo "- DONE: $@"

deploy-endpoints-test:
	@echo "--- Deploying endpoints.json to test S3 folder..."
	aws s3 cp $(PROJECT)/$(PROCESS)/$(CONFIG_DIR)/$(ENDPOINTS_JSON) s3://$(S3_TEST_BUCKET)/$(PROJECT)/$(JUPITER)/$(ENDPOINTS_JSON)
	@echo "--- Done."

deploy-endpoints-prod:
	@echo "--- Deploying endpoints.json to prod S3 folder..."
	aws s3 cp $(PROJECT)/$(PROCESS)/$(CONFIG_DIR)/$(ENDPOINTS_JSON) s3://$(S3_PROD_BUCKET)/$(PROJECT)/$(JUPITER)/$(ENDPOINTS_JSON)
	@echo "--- Done."

deploy-feeds-to-check-test:
	@echo "--- Deploying feeds_to_check.json to test S3 folder..."
	aws s3 cp $(PROJECT)/$(PROCESS)/$(CONFIG_DIR)/$(FEEDS_TO_CHECK_JSON) s3://$(S3_TEST_BUCKET)/$(PROJECT)/$(MANHATTAN)/$(FEEDS_TO_CHECK_JSON)
	@echo "--- Done."

deploy-feeds-to-check-prod:
	@echo "--- Deploying feeds_to_check.json to prod S3 folder..."
	aws s3 cp $(PROJECT)/$(PROCESS)/$(CONFIG_DIR)/$(FEEDS_TO_CHECK_JSON) s3://$(S3_PROD_BUCKET)/$(PROJECT)/$(MANHATTAN)/$(FEEDS_TO_CHECK_JSON)
	@echo "--- Done."
