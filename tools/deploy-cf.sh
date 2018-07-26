#!/usr/bin/env bash
##############################################################################
# Deploy AWS CloudFormation stack
#
# Command line arguments:
#   $1 - main stack name of cloudformation
#   $2 - deployment alias/tag, e.g.: dev (default), prod, test
#   $3 - cloudformation template file (local path, s3 prefix, or s3:// file)
#   $4 - parameter file (local path, s3 prefix, or s3:// file)
#
# Other options
#   $1 == '--list' to list stacks (any excluding Status contains 'DELETE')
#   $3 == '--delete' to delete stack ${PREFIX_NAME}-$1-$2
# or
#   $@ =~ '--test' to print command only (same as DRY_RUN_ONLY=1)
#   $@ =~ '--s3' to use s3 files (same as USE_S3=1)
#
# Expecting the runtime host is assigned with proper AWS Role;
# or from ~/.aws or the following environment variables (see check_depends)
#   AWS_ACCESS_KEY_ID
#   AWS_SECRET_ACCESS_KEY
#   AWS_DEFAULT_REGION (optional)
#   S3_BUCKET (optional, default 'cyber-intel')
#   S3_PREFIX (optional, default 'watchmen')
#   S3_PREFIX_BUILDS (optional, default '${S3_PREFIX}/builds')
#   PREFIX_NAME (optional, default 'CyberInt')
#   STACK_NAME (optional, default 'Watchmen')
#   BUILD_ENV (optional, default to $2 or 'dev')
# and git workspace having ".git" folder with optional
#   GIT_REVISION_TAG (or using current commit sha)
#
##############################################################################
set -eo pipefail
script_file="${BASH_SOURCE[0]##*/}"
script_base="$( cd "$( echo "${BASH_SOURCE[0]%/*}/.." )" && pwd )"
script_path="${script_base}/tools/${script_file}"
builds_path="${script_base}/builds"
config_path="${script_base}/cloudformation"
cfmain_file="cloudformation.json"
prefix_name="${PREFIX_NAME:-CyberInt}"
stacks_list="[]"

# step 0: predefine environment variables
BUILD_ENV="${BUILD_ENV:-dev}"
CHECK_STACK="${CHECK_STACK:-false}"
CHECK_STACK_ONLY="${CHECK_STACK_ONLY:-false}"
STACK_NAME="${STACK_NAME:-Watchmen}"
S3_BUCKET="${S3_BUCKET:-cyber-intel}"
S3_PREFIX="${S3_PREFIX:-watchmen}"
S3_PREFIX_BUILDS="${S3_PREFIX_BUILDS:-${S3_PREFIX}/builds}"
DATA_S3_BUCKET="${DATA_S3_BUCKET:-${S3_BUCKET}}"
DEPLOY_TAG="${GIT_REVISION_TAG:-None}"
DRY_RUN_ONLY="${DRY_RUN_ONLY:-false}"
USE_S3="${USE_S3:-false}"


# step 2: main entrypoint to start with parsing command line arguments
function main() {
  ARG_STACK="${1:-${STACK_NAME}}"
  ARG_ALIAS="${2:-${BUILD_ENV}}"
  ARG_PARAM="cloudformation_config_${ARG_ALIAS}.json"

  BUILD_ENV="${ARG_ALIAS}"
  CF_STACK_NAME="${prefix_name}-${ARG_STACK}-${ARG_ALIAS}"
  CF_RESPONSE="${CF_STACK_NAME}.json"
  USE_ARG3="false"
  USE_ARG4="false"
  USE_PARAMETERS_FILE="true"  # default to use parameter file until not found
  USE_PARAMETERS_ON_S3="false"  # default to use local path until found on s3
  HAS_ERROR="false"

  shopt -s nocasematch
  for arg in $@ ; do
    if [[ "${arg}" =~ (help|/h|-\?|\/\?) ]] || [[ "${arg}" == "-h" ]]; then
      usage; return
    fi
  done
  if [[ "$@" =~ (--help|/help|-\?|/\?) ]]; then
    usage; return
  fi

  do_cleanup
  check_cmdline_args $@
  check_depends

  # resolving BUILD_NAME value as partial s3 prefix
  check_git_commit_sha_or_tag

  set +u
  if [[ "$1" == "list" ]] || [[ "$@" =~ (--list) ]] ; then
    do_list_stacks; return
  fi
  if [[ "$3" =~ "delete" ]]; then
    do_delete_stack "${CF_STACK_NAME}"; do_cleanup; return
  fi
  set -u

  if [[ "${CHECK_STACK_ONLY}" != "true" ]]; then
    S3_PREFIX_CFT="${S3_PREFIX_BUILDS}/cloudformation"
    CONFIGURATION="${3:-${config_path}/${cfmain_file}}"
    PARAMETERFILE="${4:-${config_path}/${ARG_PARAM}}"

    check_cloudformation_parameter_file
    check_deploy_args $@

    do_deployment "${CF_STACK_NAME}"
  fi

  do_cleanup
  do_summary
}

# abspath(): output a relative path to absolute path
function abspath() {
  set +u
  local thePath
  if [[ ! "$1" =~ ^/ ]]; then thePath="$PWD/$1"; else thePath="$1"; fi
  echo "$thePath"|(
  IFS=/
  read -a parr
  declare -a outp
  for i in "${parr[@]}";do
    case "$i" in
    ''|.) continue ;;
    ..)
      len=${#outp[@]}
      if ((len!=0));then unset outp[$((len-1))]; else continue; fi
      ;;
    *)
      len=${#outp[@]}
      outp[$len]="$i"
      ;;
    esac
  done
  echo /"${outp[*]}"
  )
  set -u
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

  if [[ "${cf_stat}" != "" ]] && [[ "${on_echo}" =~ (1|enable|on|true|yes) ]]; then
    echo "......................................................................."
    echo "${cmd_out}" | jq -M -r '.Stacks[0]'
    echo "......................................................................."
    log_debug "Status == ${cf_stat}"
    echo ""
  fi

  CF_STACK_STATUS="${cf_stat}"
}

function check_cf_stack_status_complete() {
  set +u
  local cf_name="${1:-${CF_STACK_NAME}}"
  local timeout="${2:-499}"
  local elapsed="$(date +%s)"
  local seconds="10"
  echo ""
  echo `date +'%Y-%m-%d %H:%M:%S'` "Checking complete status for stack: ${cf_name}"
  set -u

  until [[ $timeout -lt 0 ]]; do
    check_cf_stack_status "${cf_name}"  # no stdout

    if [[ "${CF_STACK_STATUS}" == "" ]]; then
      log_trace "Cannot get status for stack '${cf_name}'."
      break
    elif [[ "${CF_STACK_STATUS}" =~ (ROLLBACK) ]]; then
        log_trace "The stack '${cf_name}' failed as in '${CF_STACK_STATUS}'."
        break
    elif [[ "${CF_STACK_STATUS}" =~ (.+_COMPLETE$) ]]; then
      log_trace "The stack '${cf_name}' status: '${CF_STACK_STATUS}'."
      break
    fi
    # Note: since there is about 1~2 seconds lag in checking stack status
    #       actual timeout would be ${timeout} + 1 * ${timeout}/${seconds}
    local msg="sleeping ${seconds} [${CF_STACK_STATUS}] timeout: ${timeout}"
    echo `date +'%Y-%m-%d %H:%M:%S'` "- ${msg} ..."
    timeout=$(( timeout - ${seconds} ))
    sleep $(( $seconds - 1 ))
  done
  elapsed=$(( $(date +%s) - ${elapsed} ))
  echo ""
  echo "`date +'%Y-%m-%d %H:%M:%S'` Elapsed: ${elapsed} [timeout: ${timeout}]"
  log_trace "Stack Status: ${CF_STACK_STATUS}"
  echo ""
}

# check cloudformation parameter file
function check_cloudformation_parameter_file() {
  if [[ "${PARAMETERFILE}" =~ (^s3://([^\/]+)/(.+)$) ]]; then return; fi

  local src="${script_base}/cloudformation"
  local cfg="${builds_path}/cloudformation/cf_${BUILD_ENV}_${BUILD_NAME}.json"

  log_trace "Copying parameter file [${BUILD_ENV}] to ${cfg}"
  if [[ "${BUILD_ENV}" == "prod" ]]; then
    src="${src}/cloudformation_config_prod.json"
  else
    src="${src}/cloudformation_config.json"
  fi

  # replacing place-holder for parameter values
  create_cloudformation_parameter_file "${src}" "${cfg}"

  PARAMETERFILE="${cfg}"
}

# check command line arguments
function check_cmdline_args() {
  set +u
  if [[ "${USE_S3}" =~ (1|enable|on|true|yes) ]]; then
    if [[ "$3" != "" ]]; then USE_ARG3="true"; fi
    if [[ "$4" != "" ]]; then USE_ARG4="true"; fi
    USE_S3="true"
  fi
  if [[ "${DRY_RUN_ONLY}" =~ (1|enable|on|true|yes) ]]; then
    DRY_RUN_ONLY="true"
  fi
  if [[ "${CHECK_STACK_ONLY}" =~ (1|enable|on|true|yes) ]]; then
    CHECK_STACK_ONLY="true"
    CHECK_STACK="true"
  fi
  if [[ "${CHECK_STACK}" =~ (1|enable|on|true|yes) ]]; then
    CHECK_STACK="true"
  fi
  set -u
}

# check_depends(): verifies preset environment variables exist
function check_depends() {
  local conf_aws=""
  local list_cmd="aws cloudformation list-stacks"
  local tool_set="awk aws jq sleep"
  set +u
  echo "......................................................................."
  echo "Checking dependencies: ${tool_set}"
  for tool in ${tool_set}; do
    if ! [[ -x "$(which ${tool})" ]]; then
      log_error "Cannot find command '${tool}'"
    fi
  done

  if [[ "${DRY_RUN_ONLY}" == "true" ]]; then return; fi

  echo ""
  echo "Checking list of aws cloudformation list-stacks ..."
  if [[ "${conf_aws}" == "" ]]; then
    conf_aws=$(${list_cmd} || true)
  fi

  if [[ "${conf_aws}" == "" ]]; then
    log_error 'Cannot access to `'"${list_cmd}"'`.'
  fi

  stacks_list="${conf_aws}"
}

# check_deploy_args(): verifies command line arguments
function check_deploy_args() {
  shopt -s nocasematch

  if [[ "${CONFIGURATION}" =~ (^s3://([^\/]+)/(.+)$) ]]; then
    S3_BUCKET="${BASH_REMATCH[2]}"
    CONFIGURATION="${BASH_REMATCH[3]}"
    USE_S3="true"
  elif [[ "${USE_S3}" == "true" ]]; then
    if [[ "${USE_ARG3}" != "true" ]]; then
      CONFIGURATION="${S3_PREFIX_CFT}/${cfmain_file}"
    fi
  else
    CONFIGURATION="$(abspath "${CONFIGURATION}")"
  fi

  if [[ "${PARAMETERFILE}" =~ (^s3://([^\/]+)/(.+)$) ]]; then
    local bucket="${BASH_REMATCH[2]}"
    local prefix="${BASH_REMATCH[3]}"
    if [[ "${USE_S3}" != "true" ]] || [[ "${S3_BUCKET}" != "${bucket}" ]]; then
      echo ""
      echo "......................................................................."
      log_debug "Configuration = ${CONFIGURATION} [bucket=${S3_BUCKET}]"
      log_debug "   Parameters = ${PARAMETERFILE} [bucket=${bucket}]"
      log_error "Must be using same s3:// protocol and from the same s3 bucket [${S3_BUCKET}]."
    fi
    PARAMETERFILE="${prefix}"
    USE_PARAMETERS_ON_S3="true"
  elif [[ ! -e "${PARAMETERFILE}" ]]; then
    # assuming on s3 since not found locally
    if [[ "${USE_S3}" == "true" ]] && [[ "${USE_ARG4}" != "true" ]]; then
      PARAMETERFILE="${S3_PREFIX_CFT}/${ARG_PARAM}"
      USE_PARAMETERS_ON_S3="true"
    fi
  else
    PARAMETERFILE="$(abspath "${PARAMETERFILE}")"
  fi

  if [[ "${USE_S3}" == "true" ]]; then
    local s3ls_cmd="aws s3 ls s3://${S3_BUCKET}"
    local s3ls_out="$(${s3ls_cmd})"
    if [[ "${s3ls_out}" == "" ]]; then
      log_error 'Cannot access to `'"${s3ls_cmd}"'`.'
    fi

    local conf_cmd="aws s3 ls s3://${S3_BUCKET}/${CONFIGURATION}"
    local conf_siz="$(${conf_cmd} | awk '{print $3}')"
    if [[ "${conf_siz}" == "" ]] || [[ "${conf_siz}" == "0" ]]; then
      log_error "Cannot find 's3://${S3_BUCKET}/${CONFIGURATION}'."
    fi
  else
    if [[ ! -e "${CONFIGURATION}" ]]; then
      log_error "Cannot find deployment config file: '${CONFIGURATION}'"
    fi
  fi

  if [[ "${USE_PARAMETERS_ON_S3}" == "true" ]]; then
    local list_cmd="aws s3 ls s3://${S3_BUCKET}/${PARAMETERFILE}"
    local list_siz="$(${list_cmd} | awk '{print $3}')"
    if [[ "${list_siz}" == "" ]] || [[ "${list_siz}" == "0" ]]; then
      log_trace "Cannot find 's3://${S3_BUCKET}/${PARAMETERFILE}'." WARN
      USE_PARAMETERS_FILE="false"
    fi
  elif [[ ! -e "${PARAMETERFILE}" ]]; then
    log_trace "Cannot find deployment parameter file: '${PARAMETERFILE}'" WARN
    USE_PARAMETERS_FILE="false"
  fi

  set +u
  echo "......................................................................."
  if [[ "${USE_S3}" == "true" ]]; then
    echo "    S3_BUCKET = ${S3_BUCKET}"
  fi
  echo "CONFIGURATION = ${CONFIGURATION}"
  echo "   PARAMETERS = ${PARAMETERFILE}"
  echo "......................................................................."
  set -u

  do_cleanup
}

# check_git_commit_sha_or_tag(): get git commit sha or revision tag
function check_git_commit_sha_or_tag() {
  echo ""
  echo "--- Checking git commit sha or revision tag ---"
  cd -P "${script_base}" && pwd
  # see https://git-scm.com/docs/pretty-formats
  local commit_sha="$(git rev-parse --short HEAD)"
  local commit_tag="$(git describe --tags --abbrev 2>/dev/null)"
  local commit_dts="$(TZ=UTC git log --oneline --no-walk --pretty=format:'%cI' 2>/dev/null)"
  local prefix_ymd="$(TZ=UTC date +'%Y%m%d-%H%M%S')"

  if [[ "${commit_dts}" != "" ]]; then
    prefix_ymd="${commit_dts:0:4}${commit_dts:5:2}${commit_dts:8:2}"
    log_trace "Set yyyymmdd prefix [${prefix_ymd}] from committer's date [${commit_dts}]"
  else
    TZ=UTC git log --oneline --no-walk --pretty=format:'%h %aE %aI [%cI] %s'
    log_error "Cannot get git committer's date."
  fi

  if [[ "${DEPLOY_TAG}" != "None" ]]; then
    if [[ "${DEPLOY_TAG}" != "${commit_tag}" ]]; then
      git describe --tags --abbrev
      log_error "GIT_REVISION_TAG [${DEPLOY_TAG}] does not match '${commit_tag}' for current revision [${commit_sha}]"
    fi
    # NOTE: The s3 partial prefix must match to where set in 'publish-builds.sh'
    BUILD_NAME="${prefix_ymd}_${commit_tag}"
    log_trace "Using revision tag and commit sha for s3 build prefix: ${BUILD_NAME}"
  elif [[ "${commit_sha}" != "" ]]; then
    BUILD_NAME="${prefix_ymd}_${commit_sha}"
    log_trace "Using commit sha for s3 build prefix: ${BUILD_NAME}"
  else
    log_error "Cannot get GIT_REVISION_TAG or git commit sha."
  fi

  S3_PREFIX_BUILDS="${S3_PREFIX_BUILDS}/${BUILD_NAME}"
  log_trace "Set s3 build prefix: ${S3_PREFIX_BUILDS}"
}

# check_response(): check function configuration changes
#   - $1: phase of the process, e.g. "create", "publish"
function check_response() {
  if [[ ! -e "${CF_RESPONSE}" ]]; then return; fi

  set +u
  echo ""
  echo "Checking response from aws cloudformation cli ..."
  echo "......................................................................."
  local stack_id="$(cat "${CF_RESPONSE}"|jq -r '.StackId')"

  if [[ "${stack_id}" != "" ]]; then
    log_debug "StackId == ${stack_id}"
  else
    cat "${CF_RESPONSE}"
    echo "......................................................................."
    log_trace "Cannot find StackId" WARN
  fi
  echo ""
  set -u
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

# check_s3_file(): check if s3:// file exists
function check_s3_file() {
  if [[ "$1" == "" ]]; then return; fi
  aws s3 ls $1
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

  log_trace "Populating values in ${cfg}"
  echo "......................................................................."
  echo "       S3_BUCKET = ${S3_BUCKET}"
  echo "S3_PREFIX_BUILDS = ${S3_PREFIX_BUILDS}"
  echo "  DATA_S3_BUCKET = ${DATA_S3_BUCKET}"
  echo "       BUILD_ENV = ${BUILD_ENV}"
  echo ""

  while IFS='' read -r line || [[ -n "${line}" ]]; do
    line="${line//__BUILD_ENV__/${BUILD_ENV}}"
    line="${line//__DATA_S3_BUCKET__/${DATA_S3_BUCKET}}"
    line="${line//__WATCHMEN_BUILDS_PREFIX__/${S3_PREFIX_BUILDS}}"
    line="${line//__S3_BUCKET__/${S3_BUCKET}}"
    echo "${line}"
  done < "${src}" > "${dst}"
}

# do_cleanup(): clean up temporary files
function do_cleanup() {
  if [[ -e "${CF_RESPONSE}" ]] && [[ "${CF_RESPONSE}" =~ (.json$) ]]; then
    rm -rf "${CF_RESPONSE}"
  fi
}

# do_delete_stack(): delete a cloudformation stack
function do_delete_stack() {
  local cf_name="${1:-${CF_STACK_NAME}}"
  local aws_cli="aws cloudformation"
  local aws_cmd="${aws_cli} delete-stack"
  local cmd_arg="--stack-name ${cf_name}"
  local cmd_opt="--client-request-token ${cf_name}"
  set +u
  echo ""
  echo "Deleting cloudformation stack ..."
  echo -e "  - name: ${cf_name}"
  echo -e "  - exec:\n\n${aws_cmd} ${cmd_arg} ${cmd_opt}"
  echo ""
  set -u

  if [[ "${DRY_RUN_ONLY}" == "true" ]]; then return; fi

  ${aws_cmd} ${cmd_arg} ${cmd_opt}

  check_return_code $? "${aws_cmd}"
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
      do_deploy_stack update "${cf_name}"
    fi
  else
    log_trace "Creating stack [${cf_name}] ..."
    do_deploy_stack create "${cf_name}"
  fi
}

# do_deploy_stack(): deploy a new cloudformation stack
function do_deploy_stack() {
  if [[ "$1" != "create" ]] && [[ "$1" != "update" ]]; then
    log_error "Invalid command for 'aws cloudformation' cli: $1-stack"
  fi

  local arg_cmd="${1:-update}"
  local cf_name="${2:-${CF_STACK_NAME}}"
  local aws_cli="aws cloudformation"
  local aws_cmd="${aws_cli} ${arg_cmd}-stack"
  local aws_arg="--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM"
  local cmd_arg="--stack-name ${cf_name} ${aws_arg}"
  local cmd_opt="--template-body file://${CONFIGURATION}"
  local aws_url="https://${S3_BUCKET}.s3.amazonaws.com"

  if [[ "${USE_S3}" == "true" ]]; then
    cmd_opt="--template-url ${aws_url}/${CONFIGURATION}"
  fi

  if [[ "${USE_PARAMETERS_FILE}" == "true" ]]; then
    if [[ "${USE_PARAMETERS_ON_S3}" == "true" ]]; then
      cmd_opt="${cmd_opt} --parameters ${aws_url}/${PARAMETERFILE}"
    else
      cmd_opt="${cmd_opt} --parameters file://${PARAMETERFILE}"
      echo "......................................................................."
      cat ${PARAMETERFILE}
    fi
  else
    cmd_kv1="ParameterKey=Environment,ParameterValue=${BUILD_ENV}"
    cmd_kv2="ParameterKey=WatchmenDataBucket,ParameterValue=${DATA_S3_BUCKET}"
    cmd_kv3="ParameterKey=WatchmenBucket,ParameterValue=${S3_BUCKET}"
    cmd_kv4="ParameterKey=WatchmenBuildsPrefix,ParameterValue=${S3_PREFIX}"
    cmd_opt="${cmd_opt} --parameters ${cmd_kv1} ${cmd_kv2} ${cmd_kv3} ${cmd_kv4}"
  fi

  local cmdline="${aws_cmd} ${cmd_arg} ${cmd_opt}"
  local cmdname="$([[ "$1" == "create" ]] && echo "Creating" || echo "Updating")"
  set +u
  echo "......................................................................."
  echo "${cmdname} cloudformation stack ..."
  echo -e "  - name: ${cf_name}"
  echo -e "  - exec:\n\n${cmdline}"
  echo ""
  set -u

  if [[ "${DRY_RUN_ONLY}" == "true" ]]; then
    echo "-----------------------------------------------------------------------"
    echo "- NOTE: Use above command line in deployment process."
    return
  fi

  ${cmdline} > "${CF_RESPONSE}"

  check_return_code $? "${aws_cmd}"

  check_response
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

# print out summary info
function do_summary() {
  local action="${1:-deployed stack}"
  echo ""
  if [[ "${DRY_RUN_ONLY}" == "true" ]]; then
    echo "- DONE"
    return
  fi
  echo "-----------------------------------------------------------------------"
  echo "- DONE: ${action} [${CF_STACK_NAME}]"
  echo ""
}

# log_debug() func: print message as debug warning
function log_debug() {
  log_trace "$1" "${2:-DEBUG}"
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


set +u
[[ "$1=None" == "=None" ]] && usage && exit
set -u

ARGS=""
# step 1: pre-processing optional arguments
for arg in $@; do
  if [[ "${arg}" =~ "--s3" ]]; then
    USE_S3="true"
  elif [[ "${arg}" =~ "--test" ]]; then
    DRY_RUN_ONLY="true"
  elif [[ "${arg}" =~ "--stage" ]]; then
    if [[ "${arg}" =~ "--stage-only" ]]; then
      CHECK_STACK_ONLY="true"
    fi
    CHECK_STACK="true"
  else
    ARGS="${ARGS} "${arg}""
  fi
done

# main entrance, preventing from source
[[ $0 != "${BASH_SOURCE}" ]] || main ${ARGS}
