#!/bin/bash
setEnvironment()
{
  if [ $# -eq 0 ]; then
          echo "usage: $0 <env dev/prod>"
          exit 1
  fi

  export ENV=$1

  if [ -z $ENV ] || [[ ( $ENV != "dev" && $ENV != "prod" ) ]]; then
          echo "environment must be dev/prod, usage: $0 <env dev/prod> "
          exit 1
  fi
  #[[ $_ != $0 ]] && echo "Script is being sourced" || echo "Script is a subshell"
  (return 0 2>/dev/null) && sourced=1 || sourced=0
  if [ $sourced -eq 0 ]; then
    me=$(basename $0)
    echo "script $me is not being sourced, you must source this script to set env for this session !!!"
  elif [ $sourced -eq 1 ]; then
    me=$(basename $BASH_SOURCE)
    echo "script $me is being sourced !!!"
  fi

  echo "sourced >>> $sourced"
  echo "setting ${env} environment for FLASK "

  if [ $ENV=="dev" ]; then
          export PYTHONPATH=/opt/ansible/app/source
  elif [ $ENV=="prod" ]; then
          export PYTHONPATH=/opt/ansible/app/bin
  fi
  export REGION="NAM"
  export OPCO="MARSH"
  export DC_LOCATION="Dallas"
  export DOMAIN="CORP"
  export FLASK_APP="flask"
  export FLASK_HOME="/opt/ansible/app/common"
  export FLASK_CONFIG="${FLASK_HOME}/config"
  export FLASK_LOG="${FLASK_HOME}/log"
  export FLASK_BIN_PATH="/opt/ansible/app/source/com/mmc/common"
  export FLASK_MAIN_FILE="flask_main.py"
  export GIT_PYTHON_REFRESH=quiet

  echo "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
  echo " "
  echo "ME          : ${me}"
  echo "ENV         : ${ENV}"
  echo "REGION      : ${REGION}"
  echo "OPCO        : ${OPCO}"
  echo "DC_LOCATION : ${DC_LOCATION}"
  echo "PYTHONPATH  : ${PYTHONPATH}"
  echo "FLASK_APP   : ${FLASK_APP}"
  echo "FLASK_CONFIG: ${FLASK_CONFIG}"
  echo "FLASK_LOG   : ${FLASK_LOG}"
  echo " "
  echo "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
}

me=`basename "$0"`
me=`"$(basename "$(test -L "$0" && readlink "$0" || echo "$0")")"`
echo "executing ${me} ..."
setEnvironment
echo "execution of ${me} completed "

