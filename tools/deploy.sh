#!/usr/bin/env bash
######################################################################
# Deploy container to ECR repository
#
# Environment variables:
#   BUILD_ENV: Environment to be deployed in e.g. 'test', 'prod'
#   DOCKER_IMAGE: Docker image built locally
#   ECRO_REPO: Name of ECR repository
#
######################################################################
set +x
script_file="$( readlink "${BASH_SOURCE[0]}" 2>/dev/null || echo ${BASH_SOURCE[0]} )"
script_name="${script_file##*/}"
script_base="$( cd "$( echo "${script_file%/*}/.." )" && pwd )"
script_path="$( cd "$( echo "${script_file%/*}" )" && pwd )"

BUILD_ENV="${BUILD_ENV:-test}"
DOCKER_IMAG="${DOCKER_IMAG:-infobloxcto/cybersvc}"
ECR_REPO="${ECR_REPO:-405093580753.dkr.ecr.us-east-1.amazonaws.com/cyberintel/coeus}"

TODAY="$(date +%Y-%m-%d)"

function main() {
  tag_container
  push_container
}

function push_container() {
  local docker_cli="docker push"
  local cmd_push_env="${docker_cli} ${ECR_REPO}:${BUILD_ENV}"
  echo "Pushing up ${ECR_REPO}"
  ${cmd_push_env}
  if [[ "${BUILD_ENV}" == "prod" ]]; then
      local cmd_push_today="${docker_cli} ${ECR_REPO}:${TODAY}"
      ${cmd_push_today}
  fi
  echo ""
}

function tag_container() {
  local docker_cli="docker tag"
  # The prod on the local container stands for the production ready container
  local cmd_tag_env="${docker_cli} ${DOCKER_IMAG}:prod ${ECR_REPO}:${BUILD_ENV}"
  echo "Tagging ${DOCKER_IMAG} local container for ${BUILD_ENV} environment in ${ECR_REPO} repository"
  ${cmd_tag_env}
  echo ""
  if [[ "${BUILD_ENV}" == "prod" ]]; then
    # For rollbacks tag with the date stamp in format (YYYY-MM-DD)
    local cmd_tag_date="${docker_cli} ${DOCKER_IMAG}:prod ${ECR_REPO}:${TODAY}"
    ${cmd_tag_date}
    echo ""
  fi
}

[[ $0 != "${BASH_SOURCE}" ]] || main
