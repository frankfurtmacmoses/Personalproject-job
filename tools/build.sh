#!/usr/bin/env bash
######################################################################
# Build AWS Lambda Function
#
# Command line arguments:
#   $1 - target feature identifier, e.g. dataUploader
#        or using "all" (optionally omitted) to pack all code
#
# Dependencies:
#   tools/deploy-watchmen.json
#
######################################################################
set -eo pipefail
script_file="${BASH_SOURCE[0]##*/}"
script_base="$( cd "$( echo "${BASH_SOURCE[0]%/*}/.." )" && pwd )"
script_path="${script_base}/tools/${script_file}"
builds_path="${script_base}/builds"

PROJECT="watchmen"
ARG_FEAID="${1:-all}"
CONFIGURATION="${script_base}/tools/deploy-${PROJECT}.json"
DEFAULT_BUILD="${PROJECT}-lambdas"
DEFAULT_ARTIFACT="${DEFAULT_BUILD}.zip"
SOURCE_DIR="${script_base}/${PROJECT}"
REQUIREMENTS="${SOURCE_DIR}/requirements.txt"
BUILDS_DIR="${BUILDS_DIR:-${builds_path}}"
README="${BUILDS_DIR}/BUILD-INFO.txt"


function main() {
  set +u
  shopt -s nocasematch
  for arg in $@ ; do
    if [[ "${arg}" =~ (help|/h|-\?|\/\?) ]] || [[ "${arg}" == "-h" ]]; then
      usage; return
    fi
  done
  if [[ "$@" =~ (--help|/help|-\?|/\?) ]]; then
    usage; return
  fi
  set -u

  check_depends
  check_deploy_args

  echo ""
  echo "--- Building ${ALF_DEFN} ---"
  build

  check_git_commit

  echo ""
  echo "${PROJECT} ${ARG_FEAID} package is ready: ${builds_path}/${ALF_ZIPF}"
  echo "--------------------------------------------------------------------"
  echo ""
}

function build() {
  cd -P "${script_base}" && pwd
  rm -rf ${builds_path}/${ALF_DEFN}
  rm -rf ${builds_path}/${ALF_ZIPF}
  mkdir -p ${builds_path}
  pip install -r "${REQUIREMENTS}" -t ${builds_path}/${ALF_DEFN}
  cp -rf ${SOURCE_DIR} ${builds_path}/${ALF_DEFN}
  cp -rf ${SOURCE_DIR}/main.py ${builds_path}/${ALF_DEFN}/handler.py
  rm -rf ${builds_path}/${ALF_DEFN}/${PROJECT}/logging.yaml
  cd ${builds_path}/${ALF_DEFN} && zip -r ../${ALF_ZIPF} .
  cd -P "${script_base}" && pwd
  rm -rf ${builds_path}/${ALF_DEFN}
}

# check_depends(): verifies preset environment variables exist
function check_depends() {
  local conf_aws=""
  local tool_set="aws git jq tee tree"
  set +u
  echo "......................................................................."
  echo "Checking dependencies: ${tool_set}"
  for tool in ${tool_set}; do
    if ! [[ -x "$(which ${tool})" ]]; then
      log_error "Cannot find command '${tool}'"
    fi
  done

  if [[ ! -e "${CONFIGURATION}" ]]; then
    log_error "Cannot find deployment config file: '${CONFIGURATION}'"
  fi

  ALF_META="$(jq -r .functions.${ARG_FEAID} ${CONFIGURATION})"
  if [[ "${ALF_META}" == "null" ]] || [[ "${ALF_META}" == "" ]]; then
    echo "Checking build target in: "`jq -r ".functions|keys[]" ${CONFIGURATION}`
    echo ""
    if [[ "${ARG_FEAID}" != "all" ]]; then
      log_error "Cannot find a valid build target: ${ARG_FEAID}"
    fi
  fi
  set -u
}

# check_deploy_args(): verifies command line arguments
function check_deploy_args() {
  if [[ "${ARG_FEAID}" == "all" ]]; then
    echo "Using default build artifact: ${DEFAULT_ARTIFACT}"
    ALF_DEFN="${DEFAULT_BUILD}"
    ALF_ZIPF="${DEFAULT_ARTIFACT}"
    return
  fi

  set +u
  echo "......................................................................."
  echo "Checking arguments for target: ${ARG_FEAID}"
  ALF_DEFN="$(jq -r .functions.${ARG_FEAID}.name ${CONFIGURATION})"
  ALF_DESC="$(jq -r .functions.${ARG_FEAID}.description ${CONFIGURATION})"
  ALF_ZIPF="$(jq -r .functions.${ARG_FEAID}.zip ${CONFIGURATION})"

  # check if target function description exists
  echo "Checking function description ..."
  if [[ "${ALF_DESC}" == "null" ]] || [[ "${ALF_DESC}" == "" ]]; then
    log_error "Cannot find AWS Lambda Function description for target: ${ARG_FEAID}"
  fi
  set -u
}

# check_git_commit(): check git commit and create build description
function check_git_commit() {
  echo ""
  echo "--- Checking build description ---"
  cd -P "${script_base}" && pwd
  local commit_sha="$(git rev-parse --short HEAD)"

  if [[ "${commit_sha}" != "" ]]; then
    git show ${commit_sha} --raw | tee "${README}"
    echo "----------------------------------------" >> "${README}"
    git branch -v >> "${README}"
  fi
}

# check_return_code(): checks exit code from last command
function check_return_code() {
  local return_code="${1:-0}"
  local action_name="${2:-AWS CLI}"

  if [[ "${return_code}" != "0" ]]; then
    log_fatal "${action_name} [code: ${return_code}]" ${return_code}
  else
    echo "Success: ${action_name}"
    echo ""
  fi
}

# log_error() func: exits with non-zero code on error unless $2 specified
function log_error() {
  log_trace "$1" "ERROR" $2
}

# log_fatal() func: exits with non-zero code on fatal failure unless $2 specified
function log_fatal() {
  log_trace "$1" "FATAL" $2
}

# log_trace() func: print message at level of INFO, DEBUG, WARNING, or ERROR
function log_trace() {
  local err_text="${1:-Here}"
  local err_name="${2:-INFO}"
  local err_code="${3:-1}"

  if [[ "${err_name}" == "ERROR" ]] || [[ "${err_name}" == "FATAL" ]]; then
    HAS_ERROR="true"
    echo -e "\n${err_name}: ${err_text}" >&2
    exit ${err_code}
  else
    echo -e "\n${err_name}: ${err_text}"
  fi
}

# usage() func: show help
function usage() {
  local headers="0"
  echo ""
  echo "USAGE: ${script_file} --help"
  echo ""
  # echo "$(cat ${script_path} | grep -e '^#   \$[1-9] - ')"
  while IFS='' read -r line || [[ -n "${line}" ]]; do
    if [[ "${headers}" == "0" ]] && [[ "${line}" =~ (^#[#=-\\*]{59}) ]]; then
      headers="1"
      echo "${line}"
    elif [[ "${headers}" == "1" ]] && [[ "${line}" =~ (^#[#=-\\*]{59}) ]]; then
      headers="0"
      echo "${line}"
    elif [[ "${headers}" == "1" ]]; then
      echo "${line}"
    fi
  done < "${script_path}"
}


[[ $0 != "${BASH_SOURCE}" ]] || main "$@"
