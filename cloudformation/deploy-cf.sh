#!/usr/bin/env bash
######################################################################
# Deploy CloudFormation stack
#
# Environment variables:
#   BUCKET: e.g. 'cyber-intel-test' (default), 'cyber-intel'
#   BUILD_ENV: e.g. 'dev' (default), 'preprod' (test), 'beta', 'prod'
#   ACCOUNT: e.g. 'saas' or 'atg'
######################################################################
set +x
script_file="$( readlink "${BASH_SOURCE[0]}" 2>/dev/null || echo ${BASH_SOURCE[0]} )"
script_name="${script_file##*/}"
script_base="$( cd "$( echo "${script_file%/*}/.." )" && pwd )"
script_path="$( cd "$( echo "${script_file%/*}" )" && pwd )"

deploy_path="${script_base}/cloudformation"
builds_path="${script_base}/builds"

commit_sha="$(git log --pretty=format:'%h' -n 1)"
ymd_utc="$(TZ=UTC date +'%Y%m%d')"
aws_s3_path="watchmen/builds/${ymd_utc}_${commit_sha}"

PROJECT="watchmen"
ACCOUNT="${ACCOUNT}"
FEATURE="${FEATURE:-${PROJECT}}"
BUCKET="${BUCKET:-cyber-intel-test}"
BUILD_ENV="${BUILD_ENV:-test}"
BUILD_PACKAGE="${FEATURE}-lambdas-${BUILD_ENV}.zip"
CF_STACK_NAME="CyberInt-${FEATURE}-${BUILD_ENV}"
DEPLOY_FILE="${DEPLOY_FILE}"

DRY_RUN_ONLY="${DRY_RUN_ONLY:-false}"

function main() {
  echo ""
  cd -P "${script_path}" && echo "PWD: $(pwd)"

  set +u
  if [[ "${DRY_RUN_ONLY}" =~ (1|enable|on|true|yes) ]]; then
    DRY_RUN_ONLY="true"
  fi

  check_depends
  if [[ "$1" == "check" ]] || [[ "$@" =~ (--check) ]] ; then
    check_cf_stack_status "${cf_name}" enable_stdout
    return
  fi

  check_stacks
  if [[ "$1" == "list" ]] || [[ "$@" =~ (--list) ]] ; then
    do_list_stacks; return
  fi
  set -u

  do_build_and_upload
  do_deployment
}

# check_depends(): verifies preset environment variables exist
function check_depends() {
  local conf_aws=""
  local tool_set="awk aws jq sleep"

  set +u
  echo ""
  echo "......................................................................."
  echo "Checking dependencies: ${tool_set}"

  for tool in ${tool_set}; do
    if ! [[ -x "$(which ${tool})" ]]; then
      log_error "Cannot find command '${tool}'"
    fi
  done
}

function check_stacks() {
  local list_cmd="aws cloudformation list-stacks"
  echo ""
  echo "Checking list of aws cloudformation stacks ..."
  if [[ "${conf_aws}" == "" ]]; then
    conf_aws=$(${list_cmd} || true)
  fi

  if [[ "${conf_aws}" == "" ]]; then
    log_error 'Cannot access to `'"${list_cmd}"'`.'
  fi

  stacks_list="${conf_aws}"
}

# check stack status
#   - args: $1: cloudformation stack name
#           $2: a string flag to turn on stdout, e.g. 1|enable|on|true|yes
#   --- return: set CF_STACK_STATUS
function check_cf_stack_status() {
  local cf_name="${1:-${CF_STACK_NAME}}"
  local on_echo="${2:-false}"
  local aws_cli="aws cloudformation"
  local aws_cmd="${aws_cli} describe-stacks"
  local cmd_arg="--stack-name ${cf_name}"
  local cmd_out="$(${aws_cmd} ${cmd_arg} 2>/dev/null)"
  local s_query='.Stacks[]|select(.StackName=="'${cf_name}'")|.StackStatus'
  local cf_stat="$(echo ${cmd_out}|jq -M -r ${s_query})"

  echo ""
  echo "Checking CloudFormation stack [${CF_STACK_NAME}] ..."

  if [[ "${cf_stat}" != "" ]] && [[ "${on_echo}" =~ (1|enable|on|true|yes) ]]; then
    echo "......................................................................."
    echo "${cmd_out}" | jq -M -r '.Stacks[0]'
    echo "......................................................................."
    log_debug "Status == ${cf_stat}"
    echo ""
  fi

  CF_STACK_STATUS="${cf_stat}"
}

function deploy_stack() {
  local _cmd_="${1:-create}"
  local _env_="${BUILD_ENV}"
  local _yml_="${DEPLOY_FILE}"
  local _acct_="${ACCOUNT}"
  local _chk_="aws cloudformation validate-template --template-body file://${_yml_}"
  local _cli_="aws cloudformation ${_cmd_}-stack
    --capabilities CAPABILITY_NAMED_IAM
    --stack-name ${CF_STACK_NAME}
    --parameters ParameterKey=Env,ParameterValue=${_env_} ParameterKey=Account,ParameterValue=${_acct_} ParameterKey=BuildsPrefix,ParameterValue=${aws_s3_path}
    --template-body file://${_yml_}
"

  echo ""
  cd -P "${script_path}" && echo "PWD: $(pwd)"

  echo ""
  echo "Validating CloudFormation template: ${_yml_}"
  echo "......................................................................."
  ${_chk_} || log_fatal "CloudFormation template has error"

  echo ""
  echo "Deploying cyberint-${PROJECT} [${_env_}] ${_acct_}"
  echo "......................................................................."
  echo "${_cli_}"

  if [[ "${DRY_RUN_ONLY}" == "true" ]]; then
    echo "-----------------------------------------------------------------------"
    echo "- NOTE: Use above command line in deployment process."
    return
  fi

  ${_cli_}
}

function do_build_and_upload() {
  local _build_file="${builds_path}/${BUILD_PACKAGE}"
  local _build_tool="${script_base}/tools/build.sh"
  local _aws_s3_cmd="aws s3 cp"
  local _aws_s3_dir="s3://${BUCKET}/${aws_s3_path}"
  local _aws_s3_url="${_aws_s3_dir}/${BUILD_PACKAGE}"
  local _aws_s3_cli="${_aws_s3_cmd} ${_build_file}
    ${_aws_s3_url}"

  if ! [[ -e "${_build_file}" ]]; then
    BUILD_ENV=${BUILD_ENV} ${_build_tool}
  fi

  echo ""
  echo "Uploading ${BUILD_PACKAGE} [${BUILD_ENV}]"
  echo "......................................................................."
  echo "${_aws_s3_cli}"
  echo ""

  ${_aws_s3_cli} || log_error "Failed to upload."

  _aws_s3_cli="${_aws_s3_cmd} ${builds_path}/BUILD-INFO.txt
    ${_aws_s3_dir}/BUILD-INFO.txt"
  echo ""
  echo "Uploading build information file"
  echo "......................................................................."
  echo "${_aws_s3_cli}"
  echo ""

  ${_aws_s3_cli}

  _aws_s3_cli="${_aws_s3_cmd} ${deploy_path}/${DEPLOY_FILE}
    ${_aws_s3_dir}/${DEPLOY_FILE}"
  echo ""
  echo "Uploading CloudFormation template"
  echo "......................................................................."
  echo "${_aws_s3_cli}"
  echo ""

  ${_aws_s3_cli}
}

# do_deployment(): deploy cloudformation stack
function do_deployment() {
  local cf_name="${1:-${CF_STACK_NAME}}"
  set +u
  echo ""
  echo "Checking description for stack: ${cf_name}"
  set -u

  check_cf_stack_status "${cf_name}" enable_stdout

  if [[ "${CF_STACK_STATUS}" != "" ]]; then
    if [[ ! "${CF_STACK_STATUS}" =~ (.+_COMPLETE$) ]]; then
      log_error "The stack '${cf_name}' is in status '${CF_STACK_STATUS}'."
    else
      log_trace "Updating stack [${cf_name}] ..."
      deploy_stack update
    fi
  else
    log_trace "Creating stack [${cf_name}] ..."
    deploy_stack create
  fi
}

# do_list_stacks(): display deployed stacks
function do_list_stacks() {
  local aws_cli="aws cloudformation"
  local aws_cmd="${aws_cli} list-stacks"
  local filters="[ .StackSummaries[]|select(.StackStatus|tostring|contains(\"DELETE\")|not) ]"
  local cmd_out="echo ${stacks_list}"
  set +u
  echo ""
  echo "Getting list of cloudformation stacks"
  echo "......................................................................."
  echo "${stacks_list}" | jq -M -r "${filters}"
  echo ""
  set -u
}


# log_debug() func: print message as debug warning
function log_debug() {
  log_trace "$1" "${2:-DEBUG}"
}

# log_error() func: exits with non-zero code on error unless $2 specified
function log_error() {
  set +u
  log_trace "$1" "ERROR" $2
}

# log_fatal() func: exits with non-zero code on fatal failure unless $2 specified
function log_fatal() {
  set +u
  log_trace "$1" "FATAL" $2
}

# log_trace() func: print message at level of INFO, DEBUG, WARNING, or ERROR
function log_trace() {
  set +u
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
  done < "${script_file}"
}


set +u
shopt -s nocasematch
for arg in $@ ; do
  if [[ "${arg}" =~ (help|/h|-\?|\/\?) ]] || [[ "${arg}" == "-h" ]]; then
    usage; exit
  fi
done
if [[ "$@" =~ (--help|/help|-\?|/\?) ]]; then
  usage; exit
fi
set -u



[[ $0 != "${BASH_SOURCE}" ]] || main "$@"
