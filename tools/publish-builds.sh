#!/usr/bin/env bash
############################################################
# Publish builds distribution to S3 buckets
#
# Arguments
#   $1 : component (e.g. 'reportable') to publish (optional)
#   -no-build-prefix : use S3_PREFIX path without build tag
#
# Expecting the following environment variables
#   AWS_ACCESS_KEY_ID
#   AWS_DEFAULT_REGION (optional)
#   AWS_SECRET_ACCESS_KEY
#   BUILD_ENV (optional, default to 'dev')
#   S3_BUCKET (optional, e.g. "cyber-intel")
#   S3_PREFIX (optional, e.g. "watchmen")
# and git workspace having ".git" folder with optional
#   GIT_REVISION_TAG (or using current commit sha)
#
############################################################
set -euo pipefail
script_file="${BASH_SOURCE[0]##*/}"
script_base="$( cd "$( echo "${BASH_SOURCE[0]%/*}/.." )" && pwd )"
script_path="${script_base}/tools/${script_file}"
builds_path="${script_base}/builds"

PUBLISH_DATA="${1:-None}"
PROJECT="${PROJECT:-watchmen}"
CONFIGURATION="${script_base}/tools/deploy-${PROJECT}.json"
S3_BUCKET="${S3_BUCKET:-cyber-intel}"
S3_PREFIX="${S3_PREFIX:-${PROJECT}}"
S3_PREFIX_BUILDS="${S3_PREFIX}/builds"
DATA_S3_BUCKET="${DATA_S3_BUCKET:-${S3_BUCKET}}"
BUILD_DIR="${BUILD_DIR:-${builds_path}}"
BUILD_ENV="${BUILD_ENV:-dev}"
GIT_REVISION_TAG="${GIT_REVISION_TAG:-None}"
USE_BUILD_PREFIX="${USE_BUILD_PREFIX:-true}"
HAS_ERROR="false"


function main() {
  shopt -s nocasematch
  if [[ "$@" =~ (help|-h|/h|-\?|\/\?) ]]; then
    usage; return
  fi

  if [[ "${USE_BUILD_PREFIX}" =~ (1|enable|on|true|yes) ]]; then
    USE_BUILD_PREFIX="true"
  fi
  if [[ "$@" =~ (-no-build-prefix) ]] || [[ "${USE_BUILD_PREFIX}" != "true" ]]; then
    log_trace "Overwriting '${S3_PREFIX_BUILDS}' without commit sha or tag prefix." WARNING
    USE_BUILD_PREFIX="false"
  fi

  check_depends

  if [[ "$@" =~ (-no-build-prefix) ]]; then
    USE_BUILD_PREFIX="false"
  fi
  check_git_commit_sha_or_tag
  copy_cloudformation_templates
  publish_builds

  echo "----------------------------------------------------------------------"
  echo "- DONE: publish succeeded."
}

# check_depends(): verifies preset environment variables exist
function check_depends() {
  local conf_aws=""
  local tool_set="aws git jq tree"
  set +u
  echo "......................................................................"
  echo "Checking dependencies: ${tool_set}"
  for tool in ${tool_set}; do
    if ! [[ -x "$(which ${tool})" ]]; then
      log_error "Cannot find command '${tool}'"
    fi
  done

  if [[ ! -e "${CONFIGURATION}" ]]; then
    log_error "Cannot find deployment config file: '${CONFIGURATION}'"
  fi

  local env_vars="S3_BUCKET S3_PREFIX BUILD_DIR"
  for var in ${env_vars}; do
    if [[ "${!var}" == "" ]]; then
      log_error "Environment variable '${var}' is not set"
    fi
  done

  if [[ "${conf_aws}" == "" ]]; then
    echo "Checking access: aws s3 ls ${S3_BUCKET}/${S3_PREFIX} ..."
    conf_aws=$(aws s3 ls ${S3_BUCKET}/${S3_PREFIX})
  fi

  if [[ "${conf_aws}" == "" ]]; then
    log_error 'Cannot access to `aws s3 ls '"${S3_BUCKET}/${S3_PREFIX}"'`.'
  fi

  set +u
  echo "......................................................................"
  echo "AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}"
  echo "BUILD_DIR = ${BUILD_DIR}"
  echo "S3_BUCKET = ${S3_BUCKET}"
  echo "S3_PREFIX = ${S3_PREFIX}"
  echo ""
  set -u
}

# check_files() func verifies distribution files
#   - $1: path to distribution folder
function check_files() {
  set +u
  local dist_path="${1:-${BUILD_DIR}}"
  local func_keys="$(jq -r '.functions|keys[]' ${CONFIGURATION})"
  local func_zips=""

  for key in ${func_keys}; do
    local file="$(jq -r .functions.${key}.zip ${CONFIGURATION})"
    if [[ -e "${dist_path}/${file}" ]]; then
      func_zips="${file} ${func_zips}"
    fi
  done

  if [[ "${func_zips}" == "" ]]; then
    log_error "Cannot find build for any of the functions: \n${func_keys}"
  fi

  echo -e "\nChecking dist folder ${dist_path}/..."
  tree "${dist_path}" 2>/dev/null || true
  ls -al ${dist_path}/*
  set -u
}

# check_git_commit_sha_or_tag(): check git commit and create build description
function check_git_commit_sha_or_tag() {
  echo ""
  echo "--- Checking git commit sha or revision tag ---"
  cd -P "${script_base}" && pwd
  # see https://git-scm.com/docs/pretty-formats
  local commit_sha="$(git rev-parse --short HEAD)"
  local commit_tag="$(git describe --tags --abbrev 2>/dev/null)"
  local build_info="$(git log ${commit_sha} --oneline --no-walk --pretty=format:'%f' 2>/dev/null)"
  local commit_dts="$(TZ=UTC git log --oneline --no-walk --pretty=format:'%cI' 2>/dev/null)"
  local prefix_ymd="$(TZ=UTC date +'%Y%m%d-%H%M%S')"

  if [[ "${commit_dts}" != "" ]]; then
    prefix_ymd="${commit_dts:0:4}${commit_dts:5:2}${commit_dts:8:2}"
    log_trace "Set yyyymmdd prefix [${prefix_ymd}] from committer's date [${commit_dts}]"
  else
    TZ=UTC git log --oneline --no-walk --pretty=format:'%h %aE %aI [%cI] %s'
    log_trace "Cannot get git committer's date." WARNING
  fi

  if [[ "${GIT_REVISION_TAG}" != "None" ]]; then
    if [[ "${GIT_REVISION_TAG}" != "${commit_tag}" ]]; then
      git describe --tags --abbrev
      log_error "GIT_REVISION_TAG [${GIT_REVISION_TAG}] does not match '${commit_tag}' for current revision [${commit_sha}]"
    else
      BUILD_TAG="${prefix_ymd}_${commit_tag}"
      if [[ "${USE_BUILD_PREFIX}" == "true" ]]; then
        log_trace "Use revision tag for s3 build prefix: ${S3_PREFIX_BUILDS}/${BUILD_TAG}"
        S3_PREFIX_BUILDS="${S3_PREFIX_BUILDS}/${BUILD_TAG}"
      fi
    fi
  elif [[ "${commit_sha}" != "" ]]; then
    BUILD_TAG="${prefix_ymd}_${commit_sha}"
    if [[ "${USE_BUILD_PREFIX}" == "true" ]]; then
      log_trace "Use commit sha for s3 build prefix: ${S3_PREFIX_BUILDS}/${BUILD_TAG}"
      S3_PREFIX_BUILDS="${S3_PREFIX_BUILDS}/${BUILD_TAG}"
    fi
  elif [[ "${USE_BUILD_PREFIX}" == "true" ]]; then
    log_error "Cannot get GIT_REVISION_TAG or git commit sha."
  else
    log_trace "Use current time for build tag: ${BUILD_TAG}"
    BUILD_TAG="${prefix_ymd}"
  fi

  log_trace "Creating build distribution document ..."
  local build_file="${BUILD_DIR}/${BUILD_TAG}_${build_info}.txt"
  mkdir -p "${BUILD_DIR}"
  git show ${commit_sha} --raw | tee "${build_file}"
  echo "----------------------------------------" >> "${build_file}"
  git branch -v >> "${build_file}"
}

# check_return_code(): checks exit code from last command
function check_return_code() {
  local return_code="${1:-0}"
  local action_name="${2:-AWS S3 CLI}"

  if [[ "${return_code}" != "0" ]]; then
    log_fatal "${action_name} [code: ${return_code}]" ${return_code}
  else
    echo "Success: ${action_name}"
    echo ""
  fi
}

# copying cloudformation to builds folder
function copy_cloudformation_templates() {
  local dir="${BUILD_DIR}/cloudformation"
  local cfg="${BUILD_DIR}/cloudformation/cf_${BUILD_ENV}_${BUILD_TAG}.json"
  local src="${script_base}/cloudformation"
  local dst=""
  echo -e "\nCopying cloudformation to ${dir} ..."
  rm -rf "${dir}"
  mkdir -p "${dir}"

  echo "- copying parameter file [${BUILD_ENV}] to ${cfg}"
  if [[ "${BUILD_ENV}" == "prod" ]]; then
    src="${src}/cloudformation_config_prod.json"
  else
    src="${src}/cloudformation_config.json"
  fi

  # replacing place-holder for parameter values
  create_cloudformation_parameter_file "${src}" "${cfg}"

  for file in cloudformation.json; do
    echo "- copying cloudformation.json"
    cp -rf "${script_base}/cloudformation/${file}" "${dir}/${file}"
  done
}

# creating parameter file
# args: $1 - input file with place holders of parameter values
#       $2 - output file with replaced parameter values
function create_cloudformation_parameter_file() {
  local src="${1:-${script_base}/cloudformation/cloudformation_config.json}"
  local dst="${2:-${builds_path}/cloudformation/cf_${BUILD_ENV}_${BUILD_TAG}.json}"

  if [[ ! -e "${src}" ]]; then
    log_error "Cannot find parameter template file: ${src}"
  fi

  while IFS='' read -r line || [[ -n "${line}" ]]; do
    line="${line//__BUILD_ENV__/${BUILD_ENV}}"
    line="${line//__DATA_S3_BUCKET__/${DATA_S3_BUCKET}}"
    line="${line//__WATCHMEN_BUILDS_PREFIX__/${S3_PREFIX}}"
    line="${line//__S3_BUCKET__/${S3_BUCKET}}"
    echo "${line}"
  done < "${src}" > "${dst}"
}

# publish ${PROJECT} build dist to s3
function publish_builds() {
  local s3_url="s3://${S3_BUCKET}/${S3_PREFIX_BUILDS}"
  local s3_cmd="aws s3 cp ${BUILD_DIR} ${s3_url} --recursivex"

  check_files "${BUILD_DIR}"

  echo -e "\nPublishing ${PROJECT} dist to ${s3_url} ...\n\$ ${s3_cmd}\n"
  ${s3_cmd}

  check_return_code $? "${s3_cmd}"

  echo ""
  echo "- info: ${PROJECT} build published."
  echo "source: ${BUILD_DIR}"
  echo "target: ${s3_url}"
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
