#!/usr/bin/env bash
############################################################
# Run "make ${1:-test}" inside a python virtual env
############################################################
script_file="${BASH_SOURCE[0]##*/}"
script_base="$( cd "$( echo "${BASH_SOURCE[0]%/*}/.." )" && pwd )"
script_path="$( cd "$( echo "${BASH_SOURCE[0]%/*}" )" && pwd )"


# main function
function main() {
  VENV_NAME="${VENV_NAME:-.venv}"
  DELIMITER="----------------------------------------------------------------------"
  EXIT_CODE=0

  cd -P "${script_base}" && pwd
  echo ""
  if [[ -d "${VENV_NAME}" ]] && [[ -e "${VENV_NAME}/bin/activate" ]]; then
    echo `date +"%Y-%m-%d %H:%M:%S"` "Activating existing ${VENV_NAME} ..."
    source "${VENV_NAME}/bin/activate"
    env|sort
    echo ""
  fi
  if [[ "${VIRTUAL_ENV}" != "" ]]; then
    echo `date +"%Y-%m-%d %H:%M:%S"` "Running '$@' in venv [${VIRTUAL_ENV}]"
    echo "${DELIMITER}"
    make $@
    EXIT_CODE=$?
  else
    rm -rf ${script_base}/${VENV_NAME}
    echo `date +"%Y-%m-%d %H:%M:%S"` "Creating python venv [${VENV_NAME}]"
    echo "${DELIMITER}"
    virtualenv ${script_base}/${VENV_NAME}
    source ${script_base}/${VENV_NAME}/bin/activate
    env|sort

    if [[ "${VIRTUAL_ENV}" == "${script_base}/${VENV_NAME}" ]]; then
      echo "${DELIMITER}"
      make $@
      EXIT_CODE=$?
    fi
  fi

  VENV_PATH="${VIRTUAL_ENV//${PWD}\//}"
  echo ""
  echo "Exit code = ${EXIT_CODE}"
  echo "${DELIMITER}"
  echo "Python environment: ${VIRTUAL_ENV}"
  echo "- Activate command: source ${VENV_PATH}/bin/activate"
  echo ""
  exit ${EXIT_CODE}
}

# log_error() func: exits with non-zero code on error unless $2 specified
function log_error() {
  log_trace "$1" "ERROR" $2
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


if ! [[ -x "$(which virtualenv)" ]]; then
  log_error "Cannot find command 'virtualenv'."
fi

# prevent from calling 'source $0' to close the console
[[ $0 != "${BASH_SOURCE}" ]] || main "$@"
