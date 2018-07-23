#!/usr/bin/env bash
##############################################################################
# Deploy AWS Lambda Function
#
# Command line arguments:
#   $1 - target feature identifier, e.g. dataUploader, sketchVectorProcessor
#   $2 - deployment alias/tag, e.g. dev (default), prod, test
#   $3 - build number (optional, default to datetime stamp '%Y%m%d_%H%M%S')
#   $4 - build zip file name (optional or 's3')
#
# or with
#   $3 = '--create' to create aws lambda function per the identifier
#
# or
#   $1 = 'list' to list all aws lambda functions
#
# Expecting the runtime host is assigned with proper AWS Role;
# or from ~/.aws or the following environment variables (see check_depends)
#   AWS_ACCESS_KEY_ID
#   AWS_SECRET_ACCESS_KEY
#   AWS_DEFAULT_REGION (optional)
#   S3_BUCKET (optional)
# and git workspace having ".git" folder with optional
#   GIT_REVISION_TAG (or using current commit sha)
#   BUILD_NUMBER (or using UTC datetime stamp)
#
##############################################################################
set -eo pipefail
script_file="${BASH_SOURCE[0]##*/}"
script_base="$( cd "$( echo "${BASH_SOURCE[0]%/*}/.." )" && pwd )"
script_path="${script_base}/tools/${script_file}"
builds_path="${script_base}/builds"

set +u
ARG_FEAID="${1:-dataUploader}"
ARG_ALIAS="${2:-dev}"
ARG_BUILD="${3}"
ARG_ZFILE="${4}"

PROJECT="${PROJECT:-reaper}"
BUILD_ARTIFACT=${BUILD_ARTIFACT:-${PROJECT}-${ARG_FEAID}.zip}
BUILD_UTCTIME="$(TZ=UTC date +'%Y%m%d-%H%M%S')"
BUILD_NUMBER="${BUILD_NUMBER:-${BUILD_UTCTIME}}"
ARG_ZFILE="${ARG_ZFILE:-${BUILD_ARTIFACT}}"
ARG_BUILD="${ARG_BUILD:-${BUILD_NUMBER}}"

CONFIGURATION="${script_base}/tools/deploy-${PROJECT}.json"
BUILDS_DIR="${BUILDS_DIR:-${builds_path}}"
BUILDS_S3_PATH="${PROJECT}/builds"
DEPLOY_DATA="${script_base}/tools/aws_${ARG_FEAID}_${ARG_ALIAS}.json"
DEPLOY_RESPONSE="${script_base}/tools/aws_${ARG_FEAID}_${ARG_ALIAS}.out"
DEPLOY_SOURCE="aws_lambda_function_code_source.zip"
DEPLOY_VERIFY="aws_lambda_function_code_verify.zip"
DEPLOY_NAME="${GIT_REVISION_TAG:-None}"
HAS_ERROR="false"
S3_BUCKET="${S3_BUCKET:-cyber-intel}"
S3_PREFIX="${S3_PREFIX:-${PROJECT}/builds}"
set -u


function main() {
  shopt -s nocasematch
  for arg in $@ ; do
    if [[ "${arg}" =~ (help|/h|-\?|\/\?) ]] || [[ "${arg}" == "-h" ]]; then
      usage; return
    fi
  done
  if [[ "$@" =~ (--help|/help|-\?|/\?) ]]; then
    usage; return
  fi

  check_depends

  if [[ "$1" =~ "list" ]]; then
    list_functions; return
  fi

  check_deploy_args

  if [[ "${ARG_BUILD}" =~ "--create" ]]; then
    create_function; return
  fi
  set -u

  check_git_commit_sha_or_tag

  check_deploy_code

  check_function  # checking if the function exists

  deploy_code
  deploy_config
  deploy_publish
  deploy_tag

  echo "-----------------------------------------------------------------------"
  echo "- DONE: deployed ${ARG_FEAID} [${ARG_ALIAS}]"
  echo ""
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

# check_depends(): verifies preset environment variables exist
function check_depends() {
  local conf_aws=""
  local tool_set="aws jq tree"
  set +u
  echo "......................................................................."
  echo "Checking dependencies: ${tool_set}"
  for tool in ${tool_set}; do
    if ! [[ -x "$(which ${tool})" ]]; then
      log_error "Cannot find command '${tool}'"
    fi
  done

  # check download tool
  # see https://daniel.haxx.se/docs/curl-vs-wget.html
  echo "Checking download tool: curl or wget"
  if [[ ! -x "$(which curl)" ]] && [[ ! -x "$(which wget)" ]]; then
    log_trace "Cannot find download tool: 'curl' or 'wget'" "WARNING"
  fi

  if [[ ! -e "${CONFIGURATION}" ]]; then
    log_error "Cannot find deployment config file: '${CONFIGURATION}'"
  fi

  if [[ "${conf_aws}" == "" ]]; then
    echo "Checking list of aws lambda functions ..."
    conf_aws=$(aws lambda list-functions)
  fi

  if [[ "${conf_aws}" == "" ]]; then
    log_error 'Cannot access to `aws lambda list-functions`.'
  fi

  set +u
  echo "......................................................................."
  echo "BUILDS_DIR=${BUILDS_DIR}"
  echo "CONFIGURATION=${CONFIGURATION}"
  echo "S3_BUCKET=${S3_BUCKET}"
  echo "S3_PREFIX=${S3_PREFIX}"

  set -u
}

# check_deploy_args(): verifies command line arguments
function check_deploy_args() {
  set +u
  echo "......................................................................."
  echo "Checking arguments for target: ${ARG_FEAID}"
  ALF_DEFN="$(jq -r .functions.${ARG_FEAID}.name ${CONFIGURATION})"
  ALF_NAME="$(jq -r .functions.${ARG_FEAID}.name_${ARG_ALIAS} ${CONFIGURATION})"
  ALF_DESC="$(jq -r .functions.${ARG_FEAID}.description ${CONFIGURATION})"
  ALF_ZIPF="$(jq -r .functions.${ARG_FEAID}.zip ${CONFIGURATION})"
  ENV_NAME="$(jq -r .env.${ARG_ALIAS}.name ${CONFIGURATION})"
  ENV_S3BK="$(jq -r .env.${ARG_ALIAS}.s3_bucket ${CONFIGURATION})"

  # check if the function name exists
  echo "Checking function name ..."
  if [[ "${ALF_NAME}" == "null" ]] || [[ "${ALF_NAME}" == "" ]]; then
    if [[ "${ALF_DEFN}" == "null" ]] || [[ "${ALF_DEFN}" == "" ]]; then
      log_error "Cannot find AWS Lambda Function for target: ${ARG_FEAID}"
    elif [[ "${ARG_ALIAS}" != "prod" ]]; then
      ALF_NAME="${ALF_DEFN}-${ARG_ALIAS}"
    else
      ALF_NAME="${ALF_DEFN}"
    fi
  fi

  # check if target function description exists
  echo "Checking function description ..."
  if [[ "${ALF_DESC}" == "null" ]] || [[ "${ALF_DESC}" == "" ]]; then
    log_error "Cannot find AWS Lambda Function description for target: ${ARG_FEAID}"
  fi

  echo "Checking function alias/tag ..."
  # check if the function alias/tag exists
  if [[ "${ENV_NAME}" == "null" ]] || [[ "${ENV_NAME}" == "" ]]; then
    log_error "Cannot deploy for env tag or alias: ${ARG_ALIAS}"
  fi

  # check build number
  if [[ "${ARG_BUILD}" == "-" ]] || [[ "${ARG_BUILD}" == "" ]]; then
    ARG_BUILD="${BUILD_UTCTIME}"
  elif [[ ! "${ARG_BUILD}" =~ "${BUILD_UTCTIME}" ]]; then
    ARG_BUILD="${ARG_BUILD}.${BUILD_UTCTIME}"
  fi

  # check s3 bucket setting
  echo "Checking s3 bucket ..."
  if [[ "${S3_BUCKET}" == "" ]]; then
    if [[ "${ENV_S3BK}" != "null" ]] && [[ "${ENV_S3BK}" != "" ]]; then
      S3_BUCKET="${ENV_S3BK}"
    fi
  fi

  # check zip file options
  echo "Checking build artifact ..."
  if [[ "${ARG_ZFILE}" =~ ^[Ss]3$ ]] && [[ "${S3_BUCKET}" != "" ]]; then
      echo "Caution: using s3 path for updating function code."
      if [[ "${ALF_ZIPF}" != "null" ]] && [[ "${ALF_ZIPF}" != "" ]]; then
        S3_PREFIX="${BUILDS_S3_PATH}/${ALF_ZIPF}"
        ARG_ZCODE="--s3-bucket ${S3_BUCKET} --s3-key ${S3_PREFIX}"
        echo " - s3 bucket: ${S3_BUCKET}"
        echo " - s3 key: ${S3_PREFIX}"
      else
        usage
        log_error "Cannot find s3 key setting for target: ${ARG_FEAID}"
      fi
  else
    echo "Checking ${ARG_ZFILE} or ${ALF_ZIPF} ..."
    if [[ -e "${ARG_ZFILE}" ]]; then
      ARG_ZFILE="$(abspath ${ARG_ZFILE})"
      ARG_ZCODE="--zip-file fileb://${ARG_ZFILE}"
      echo " - use path: ${ARG_ZFILE}"
    elif [[ -e "${BUILDS_DIR}/${ARG_ZFILE}" ]]; then
      ARG_ZFILE=${BUILDS_DIR}/${ARG_ZFILE}
      ARG_ZCODE="--zip-file fileb://${ARG_ZFILE}"
      echo " - use file: ${ARG_ZFILE}"
    elif [[ -e "${BUILDS_DIR}/${ALF_ZIPF}" ]]; then
      ARG_ZFILE=${BUILDS_DIR}/${ALF_ZIPF}
      ARG_ZCODE="--zip-file fileb://${ARG_ZFILE}"
      echo " - use code: ${ARG_ZFILE}"
    else
      usage
      log_error "Cannot find zip file for target: ${ARG_FEAID}"
    fi
  fi

  set -u
}

# check_deploy_code(): copies the deploying code for final verification
function check_deploy_code() {
  rm -rf "${DEPLOY_SOURCE}"
  rm -rf "${DEPLOY_VERIFY}"

  if [[ "${ARG_ZFILE}" =~ ^[Ss]3$ ]] && [[ "${S3_PREFIX}" != "" ]]; then
    local s3_cli="aws s3 cp"
    local s3_opt="--acl public-read-write"
    local s3_url="s3://${S3_BUCKET}/${S3_PREFIX}"
    local s3_cmd="${s3_cli} ${s3_url} ${DEPLOY_SOURCE} ${s3_opt}"
    set +u
    echo "......................................................................."
    echo "Checking function code at ${s3_url}"
    # echo -e "aws-cli\$ ${s3_cmd}"
    # set -x
    ${s3_cmd}
    check_return_code $? "${s3_cli} ${s3_url}"
    # { set +x; } 2>/dev/null
    set -u
  else
    cp "${ARG_ZFILE}" "$DEPLOY_SOURCE"
  fi
}

# check_function(): check existing AWS Lambda function
function check_function() {
  # alternatively using 'aws lambda get-function' to return an extra property
  # of '.Code.Location' for a 10-min available function code zip URL
  local aws_cli="aws lambda get-function-configuration" # --qualifier $LATEST
  local aws_cmd="${aws_cli} --function-name ${ALF_NAME} --output json"
  set +u
  echo "......................................................................."
  echo "Checking function ${ALF_NAME} ..."
  echo ""
  ${aws_cmd} > "${DEPLOY_RESPONSE}"
  cat "${DEPLOY_RESPONSE}"
  check_return_code $? "${aws_cli}"
  check_response "pre-deploy"
  set -u
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
  local prefix_ymd="${BUILD_UTCTIME}"

  if [[ "${commit_dts}" != "" ]]; then
    prefix_ymd="${commit_dts:0:4}${commit_dts:5:2}${commit_dts:8:2}"
    log_trace "Set yyyymmdd prefix [${prefix_ymd}] from committer's date [${commit_dts}]"
  else
    TZ=UTC git log --pretty=format:'%h %aE %aI [%cI] %s'
    log_error "Cannot get git committer's date."
  fi

  if [[ "${DEPLOY_NAME}" != "None" ]]; then
    if [[ "${DEPLOY_NAME}" != "${commit_tag}" ]]; then
      git describe --tags --abbrev
      log_error "GIT_REVISION_TAG [${DEPLOY_NAME}] does not match '${commit_tag}' for current revision [${commit_sha}]"
    elif [[ "${commit_sha}" != "" ]]; then
      DEPLOY_NAME="${prefix_ymd}_${commit_tag}"
      log_trace "Using revision tag in description: ${DEPLOY_NAME}" DEBUG
    fi
  elif [[ "${commit_sha}" != "" ]]; then
    DEPLOY_NAME="${prefix_ymd}_${commit_sha}"
    log_trace "Using commit sha in description: ${DEPLOY_NAME}" DEBUG
  else
    log_error "Cannot get GIT_REVISION_TAG or git commit sha."
  fi
}

# check_lambda_code(): verifies AWS Lambda Function code
function check_lambda_code() {
  set +u
  echo "......................................................................."
  echo "Downloading AWS Lambda Function code ..."
  echo "  - name: ${ALF_NAME}"
  local aws_cli="aws lambda get-function --qualifier ${ALF_VERSION}"
  local aws_cmd="${aws_cli} --function-name ${ALF_NAME} --output json"
  local aws_url="$(${aws_cmd} | jq -r .Code.Location)"
  echo "  - code: ${aws_url}"
  echo ""
  if [[ "${aws_url}" == "" ]]; then
    log_fatal "get download URL of the function code"
  fi

  local cmd_opt=""
  if [[ -x "$(which curl)" ]]; then
    cmd_opt="curl -o"
  elif [[ -x "$(which wget)" ]]; then
    cmd_opt="wget -O"
  fi
  if [[ "${cmd_opt}" == "" ]]; then
    local msg="Skipped: Verifying AWS Lambda Function code [no download tool]"
    log_trace msg "WARNING"
    return
  fi
  ${cmd_opt} ${DEPLOY_VERIFY} ${aws_url}

  check_lambda_diff
  set -u
}

# check_lambda_diff(): compares source and deployed function code
function check_lambda_diff() {
  local src="${DEPLOY_SOURCE}"
  local dst="${DEPLOY_VERIFY}"
  local err="Downloaded function code is different from source"

  if [[ -f "${src}" ]] && [[ -f "${dst}" ]]; then
    local cmd_diff="diff ${src} ${dst}"
    local msg_diff="${cmd_diff}\n\t${err}: \n\t${src}\n\t${dst}"
    ${cmd_diff} 1>/dev/null 2>&1 || log_error "${msg_diff}"
  elif [[ ! -f "${dst}" ]]; then
    log_error "Cannot find downloaded function code - ${dst}"
  else
    log_error "Cannot find source function code - ${src}"
  fi
}

# check_response(): check function configuration changes
#   - $1: phase of the process, e.g. "create", "publish"
function check_response() {
  local arg="$1"
  local old="${DEPLOY_DATA}"
  local new="${DEPLOY_RESPONSE}"
  set +u
  echo "......................................................................."
  echo "Checking function configuration changes ..."
  if [[ ! -e "${new}" ]] || [[ ! -e "${old}" ]]; then
    echo "Skipped: comparing '${new}' to '${old}'"
    return
  fi

  local old_value=""
  local new_value=""
  if [[ "${arg}" == "publish" ]]; then
    for v in Description LastModified Version; do
      old_value="$(jq -r .$v ${old})"
      new_value="$(jq -r .$v ${new})"
      if [[ "${new_value}" == "null" ]]; then
        new_value=""
      fi
      if [[ "${old_value}" == "null" ]]; then
        old_value=""
      fi
      if [[ "${new_value}" == "${old_value}" ]]; then
        log_error "The function '.$v' [${old_value}] should have changed"
      fi
    done
  fi

  local def_props="Handler KMSKeyArn MemorySize Runtime Role Timeout"
  local old_names=$(jq -r ".Environment.Variables|keys[]" "${old}")
  local new_names=$(jq -r ".Environment.Variables|keys[]" "${new}")
  local env_names=$( (echo ${old_names}; echo ${new_names}) |sort -du )
  local env_props=""
  local vpc_props=""

  if [[ "${arg}" != "pre-deploy" ]]; then
    for env in ${env_names}; do
      if [[ ! "${env}" =~ (API_KEY) ]] && [[ ! "${env}" =~ (PASSWORD) ]]; then
        env_props="${env_props} Environment.Variables.${env}"
      fi
    done
  fi

  for cfg in SecurityGroupIds SubnetIds VpcId; do
    vpc_props="${vpc_props} VpcConfig.${cfg}"
  done

  echo "  - props: ${def_props} ${env_props} ${vpc_props}"
  for v in ${def_props} ${env_props} ${vpc_props}; do
    old_value="$(jq -r .$v ${old})"
    new_value="$(jq -r .$v ${new})"
    if [[ "${new_value}" == "null" ]]; then
      new_value=""
    fi
    if [[ "${old_value}" == "null" ]]; then
      old_value=""
    fi
    if [[ "${new_value}" != "${old_value}" ]]; then
      local msg="value '${old_value}' does not match to '${new_value}' in lamabda"
      log_error "The config '.$v' ${msg}"
    fi
  done

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

# create_function(): create aws lambda function
function create_function() {
  local aws_arg="$(get_command_args ${DEPLOY_DATA})"
  local aws_cli="aws lambda create-function --output json"
  local aws_cmd="${aws_cli} ${aws_arg}"
  set +u
  echo "......................................................................."
  echo "Check command-line options for '${ALF_NAME}' [${ARG_ALIAS}]:"
  echo -e "${aws_arg//  --/\\ \\n --}"
  echo "......................................................................."
  echo "Creating function ..."
  echo "  - desc: ${ALF_DESC}"
  echo "  - name: ${ALF_NAME}"
  echo ""
  echo -e "  - exec:\n\n${aws_cmd}"
  echo ""
  echo "${aws_cmd}" | bash - > "${DEPLOY_RESPONSE}"
  check_return_code $? "${aws_cli}"
  cat "${DEPLOY_RESPONSE}"
  check_response "create"
  cp -f "${DEPLOY_RESPONSE}" "${DEPLOY_DATA}"
  rm -rf "${DEPLOY_RESPONSE}"
  echo ""
  echo "Sync'd: ${DEPLOY_DATA}"
  echo "-----------------------------------------------------------------------"
  echo "- DONE: created ${ALF_NAME}]"
  echo ""
  set -u
}

# deploy_code(): updates function code by zip file
function deploy_code() {
  local aws_cli="aws lambda update-function-code"
  local aws_cmd="${aws_cli} --function-name ${ALF_NAME} ${ARG_ZCODE}"
  set +u
  echo "......................................................................."
  echo "Updating function code ..."
  echo "  - code: ${ARG_ZCODE}"
  echo "  - name: ${ALF_NAME}"
  echo ""
  ${aws_cmd}
  check_return_code $? "${aws_cli}"
  set -u
}

# deploy_config(): updates function configuration
function deploy_config() {
  local aws_arg="$(get_command_args ${DEPLOY_DATA})"
  echo "......................................................................."
  echo "Check command-line options for '${ALF_NAME}' [${ARG_ALIAS}]:"
  echo -e "${aws_arg//  --/\\ \\n --}"

  local aws_cli="aws lambda update-function-configuration --output json"
  local aws_tag="${ALF_DESC}__${ARG_ALIAS}_${DEPLOY_NAME}_Build-${ARG_BUILD}"
  local aws_cmd="${aws_cli} ${aws_arg}"
  set +u
<<AWS_CLI_EXAMPLE
  aws lambda update-function-configuration \
  --function-name ${ALF_NAME} \
  --code ${ALF_CODE} \
  --description "${ALF_DESC}_${ARG_ALIAS}_${ARG_BUILD}" \
  --environment Variables=${ENV_VARS} \
  --handler ${ALF_HANDLER} \
  --kms-key-arn ${KMS_KEY_ARN} \
  --memory-size ${ALF_MEMORY_SIZE} \
  --role ${ALF_ROLE} \
  --runtime ${ALF_RUNTIME} \
  --timeout ${ALF_TIMEOUT} \
  --vpc-config "SubnetIds=${SUBNET_IDS},SecurityGroupIds=${SECURITY_GROUP_IDS}"
AWS_CLI_EXAMPLE

  echo "......................................................................."
  echo "Updating function configuration ..."
  echo "  - desc: ${aws_tag}"
  echo "  - name: ${ALF_NAME}"
  echo ""
  echo "${aws_cmd}" | bash - > "${DEPLOY_RESPONSE}"
  # ${aws_cli} \
  # --description "${aws_tag}" \
  # --function-name ${ALF_NAME}

  check_return_code $? "${aws_cli}"
  set -u
}

# deploy_publish(): publishes the function to a new version
function deploy_publish() {
  local aws_cli="aws lambda publish-version"
  local aws_cmd="${aws_cli} --function-name ${ALF_NAME} --output json"
  set +u
  echo "......................................................................."
  echo "Publishing function ${ALF_NAME} for ${ARG_ALIAS} ..."
  echo ""
  echo "cmd: ${aws_cmd}"
  echo ""
  ${aws_cmd} > "${DEPLOY_RESPONSE}"
  cat "${DEPLOY_RESPONSE}"
  check_return_code $? "${aws_cli}"
  check_response "publish"
  set -u
}

# deploy_tag(): publishes the alias/tag
function deploy_tag() {
  ALF_VERSION="$(jq -r .Version ${DEPLOY_RESPONSE})"
  ALF_DESCTAG="$(jq -r .Description ${DEPLOY_RESPONSE})"

  local aws_cli="aws lambda get-alias"
  local aws_opt="--function-name ${ALF_NAME} --name ${ARG_ALIAS}"
  local aws_cmd="${aws_cli} ${aws_opt}"
  local sub_cmd="update"
  set +u
  echo "......................................................................."
  echo "Checking function alias: ${ARG_ALIAS} ..."
  $aws_cmd || sub_cmd="create"

  aws_cli="aws lambda ${sub_cmd}-alias"
  aws_opt="--function-version ${ALF_VERSION} --name ${ARG_ALIAS}"
  aws_opt="--function-name ${ALF_NAME} ${aws_opt}"
  aws_cmd="${aws_cli} ${aws_opt}"

  echo "......................................................................."
  echo "Publishing the latest version to ${ARG_ALIAS} ..."
  echo "  - name: ${ALF_NAME}"
  echo "  - description: ${ALF_DESCTAG}"
  echo "  - alias/tag: ${ARG_ALIAS}"
  echo "  - version: ${ALF_VERSION}"
  echo ""
  echo "cmd: ${aws_cmd} --description \"${ALF_DESCTAG}\""
  echo ""
  ${aws_cmd} --description "${ALF_DESCTAG}"

  check_return_code $? "${aws_cli}"
  check_lambda_code
  echo ""
  echo "Delete: downloaded files ..."
  rm -rf "${DEPLOY_RESPONSE}"
  rm -rf "${DEPLOY_SOURCE}"
  rm -rf "${DEPLOY_VERIFY}"
  set -u
}

# get_command_args(): get args for `create-function`
function get_command_args() {
  local ALF_HANDLER="$(jq -r '.Handler' $1)"
  local ALF_MEMORY_SIZE="$(jq -r '.MemorySize' $1)"
  local ALF_ROLE="$(jq -r '.Role' $1)"
  local ALF_RUNTIME="$(jq -r '.Runtime' $1)"
  local ALF_TIMEOUT="$(jq -r '.Timeout' $1)"
  local DESCRIPTION="${ALF_DESC}__${ARG_ALIAS}_${DEPLOY_NAME}_Build-${ARG_BUILD}"
  local ENV_VARS=$(jq -r ".Environment.Variables|to_entries|map(\"\(.key)='\(.value|tostring)'\")|join(\",\")" $1)
  local KMS_KEY_ARN="$(jq -r '.KMSKeyArn' $1)"
  local ALF_CODE="S3Bucket=${S3_BUCKET},S3Key=${BUILDS_S3_PATH/${ALF_ZIPF}}"
  local SUBNET_IDS="$(jq -r '.VpcConfig.SubnetIds|join(",")' $1)"
  local SECURITY_GROUP_IDS="$(jq -r '.VpcConfig.SecurityGroupIds|join(",")' $1)"
  local TRACING_MODE="$(jq -r '.TracingConfig.Mode' $1)"
  local VPC_ID="$(jq -r '.VpcConfig.VpcId' $1)"

  local aws_opt="${ARG_ZCODE}"
  if [[ "${ARG_ZFILE}" =~ ^[Ss]3$ ]] && [[ "${S3_BUCKET}" != "" ]]; then
    aws_opt="--code ${ALF_CODE}"
  fi

  if [[ "${ARG_BUILD}" == "--create" ]]; then
    DESCRIPTION="${ALF_DESC}"
  else
    aws_opt=""
  fi

  local aws_vpc="SubnetIds=${SUBNET_IDS},SecurityGroupIds=${SECURITY_GROUP_IDS}"
  local aws_arg=" --function-name ${ALF_NAME} \
  --description \"${DESCRIPTION}\" \
  --environment Variables=\"{${ENV_VARS}}\" \
  --handler ${ALF_HANDLER} \
  --memory-size ${ALF_MEMORY_SIZE} \
  --role ${ALF_ROLE} \
  --runtime ${ALF_RUNTIME} \
  --timeout ${ALF_TIMEOUT} \
  --vpc-config ${aws_vpc} \
  ${aws_opt} \
  "

  if [[ "${KMS_KEY_ARN}" != "" ]] && [[ "${KMS_KEY_ARN}" != "null" ]]; then
    aws_arg="${aws_arg}--kms-key-arn ${KMS_KEY_ARN} \
  "
  fi
  if [[ "${TRACING_MODE}" != "" ]] && [[ "${TRACING_MODE}" != "null" ]]; then
    aws_arg="${aws_arg}--tracing-config Mode=${TRACING_MODE} \
  "
  fi
  echo "${aws_arg}"
}

# list_functions(): display deployed functions
function list_functions() {
  echo "......................................................................."
  for func in $(jq -r '.functions|keys[]' "${CONFIGURATION}"); do
    local defn="$(jq -r .functions.${func}.name ${CONFIGURATION})"
    local name="$(jq -r .functions.${func}.name_${ARG_ALIAS} ${CONFIGURATION})"
    if [[ "${name}" == "null" ]] || [[ "${name}" == "" ]]; then
      name="${defn}"
    fi
    local aws_cli="aws lambda get-function-configuration"
    local aws_cmd="${aws_cli} --function-name ${name}"
    echo "${name} [${ARG_ALIAS}]: "
    ${aws_cmd}
    echo ""
  done
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

[[ $0 != "${BASH_SOURCE}" ]] || main "$@"
