#!/bin/bash
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Script:       build_push_audit_deploy.sh
# Description:  Builds and push audit deployment files to its destination
#
# Usage:        ./build_push_audit_deploy.sh <username> <target_host_files>
#               For e.g. 
#               ./build_audit_deploy.sh u111111 ./target_host_files.csv
#
#
# History
#================================================================================================================
# When      Who     What
#================================================================================================================
# 3/01/2021  Anil Singh  Initial creation
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
main(){
  CURR_DIR=$(pwd)
  echo -e "`date` - building audit deployment file"
  build_aud_deploy
  retVal=$?
  if [[ $retval -ne 1 ]]; then
    cd $CURR_DIR
    echo -e "`date` - pushing audit deployment file to target"
    push_aud_deploy
  else
    exit
  fi
}

build_aud_deploy(){
  DEPLOY_HOME=/opt/ansible/deploy

  # archive fle which will be generated
  DEPLOY_AUD_TAR_FILE=deploy_audit.tar.gz
  #export DEPLOY_CFG_TAR_FILE=deploy_audit_config.tar.gz

  # source dir from where files will be copied from
  SOURCE_COM_BASE_DIR=/opt/ansible/app/source
  SOURCE_CONFIG_DIR=/opt/ansible/app

  # temporary files which will be used for processing
  #DEPLOY_FILES_REPO=files.txtx`
  #AUDIT_TARGET_HOST_FILE=target_hosts.txt

  echo -e "creating deployment directory ..."

  rm -fR $DEPLOY_HOME/app
  mkdir -p $DEPLOY_HOME/app/audit/config
  mkdir -p $DEPLOY_HOME/app/common/config
  mkdir -p $DEPLOY_HOME/app/audit/log
  mkdir -p $DEPLOY_HOME/app/com/mmc/audit
  mkdir -p $DEPLOY_HOME/app/com/mmc/common
  mkdir -p $DEPLOY_HOME/app/com/mmc/db

  echo -e "renaming existing audit deployment file"
  if [[ -f ${DEPLOY_HOME}/${DEPLOY_AUD_TAR_FILE} ]]; then
    mv ${DEPLOY_HOME}/${DEPLOY_AUD_TAR_FILE} ${DEPLOY_HOME}/${DEPLOY_AUD_TAR_FILE}.`date +%m%d%Y:%H:%M:%S`
  fi

  echo -e "copying audit source file ...."
  AUDIT_SOURCE_FILES="aud_globals.py scan.py mongo_scan.py audit_reports.py mongo_schedule.py"

  for file in $AUDIT_SOURCE_FILES; do
    echo -e "  copying ${SOURCE_COM_BASE_DIR}/com/mmc/audit/${file} to ${DEPLOY_HOME}/app/com/mmc/audit"
    cp -p ${SOURCE_COM_BASE_DIR}/com/mmc/audit/${file} $DEPLOY_HOME/app/com/mmc/audit/.
  done

  echo -e "copying audit config file ...."

  AUDIT_CONFIG_FILES="logging.json audit.json dbconfig.json run_audit.sh deploy_audit.sh push_audit_deploy.sh audit.env"

  for file in $AUDIT_CONFIG_FILES; do
    echo -e "  copying ${SOURCE_CONFIG_DIR}/audit/config/$file to ${DEPLOY_HOME}/app/audit/config/."
    cp -p ${SOURCE_CONFIG_DIR}/audit/config/$file $DEPLOY_HOME/app/audit/config/.
  done
  
  cp -p ${DEPLOY_HOME}/static/bootstrap.json $DEPLOY_HOME/app/audit/config/.
  cp -p ${DEPLOY_HOME}/static/api_vault.json $DEPLOY_HOME/app/audit/config/.

  COMMON_SOURCE_FILES="singleton.py globals.py infrastructure.py error.py security.py utility.py"
  #COMMON_SOURCE_DIR="${SOURCE_COM_BASE_DIR}/app/com/mmc/common/"

  echo -e "copying common source file(s) [${COMMON_SOURCE_FILES}]...."

  #for x in `ls -altr ${SOURCE_COM_BASE_DIR}/com/mmc/common/*.py | awk '{print $9}'`; do
  for file in ${COMMON_SOURCE_FILES}; do
    echo -e "  copying <${COMMON_SOURCE_DIR}${file}> to ${DEPLOY_HOME}/app/com/mmc/common/."
    cp -p ${SOURCE_COM_BASE_DIR}/com/mmc/common/${file} ${DEPLOY_HOME}/app/com/mmc/common/.
  done

  echo -e "copying common config file ...."
  for file in `ls -altr ${SOURCE_CONFIG_DIR}/common/config/logging.json | awk '{print $9}'`; do
    echo -e "  copying <$file> to ${DEPLOY_HOME}/app/common/config/."
    cp -p $file ${DEPLOY_HOME}/app/common/config/.
  done

  echo -e "copying db source file...."

  for file in `ls -altr ${SOURCE_COM_BASE_DIR}/com/mmc/db/*.py | awk '{print $9}'`; do
    echo -e "  copying <$file> to ${DEPLOY_HOME}/app/com/mmc/db/."
    cp -p $file ${DEPLOY_HOME}/app/com/mmc/db/.
  done

  echo -e "copying files completed ..."

  echo -e "deleting .pyc files from deploy directory ..."
  rm -fR ${DEPLOY_HOME}/com/mmc/common/__pycache__*
  rm -fR ${DEPLOY_HOME}/com/mmc/audit/__pycache__*
  rm -fR ${DEPLOY_HOME}/com/mmc/db/__pycache__*

  echo -e "creating tar file, changing dir to ${DEPLOY_HOME} "
  current_dir=$(pwd)
  cd ${DEPLOY_HOME}

  tar -cvzf ${DEPLOY_HOME}/${DEPLOY_AUD_TAR_FILE} app/

  echo -e "copying run_audit.sh/ file ..."
  cp -p /opt/ansible/app/audit/config/run_audit.sh ${DEPLOY_HOME}

  echo -e "copying deploy_audit.sh file ..."
  cp -p /opt/ansible/app/audit/config/deploy_audit.sh ${DEPLOY_HOME}

  chmod +777 ${DEPLOY_HOME}/${DEPLOY_AUD_TAR_FILE}
  AUDIT_TAR_FILE="${DEPLOY_HOME}/${DEPLOY_AUD_TAR_FILE}"
}
push_aud_deploy(){

  echo -e "lsting files to be pushed"
  for x in "${AUDIT_TAR_FILE} run_audit.sh deploy_audit.sh"; do    
    ls -altr $x | awk '{print $6"   " $7"   " $8"   " $9}';
  done
  echo -e "current working dir is >>> ${pwd}"
  echo -e "pushing files to destination ..."
  echo -e "list of target servers ... "
  echo -e "`cat $AUDIT_TARGET_HOST_FILE`"
  #DEPLOY_FILES="$AUDIT_TAR_FILE run_audit.sh"
  
  while read -r target; do
    [[ "$target" =~ ^[[:space:]]*# ]] && continue
    if [[ ! -z $target ]]; then
      echo -e "pushing deployment files to >>> ${target}:/tmp/${USERNAME}"
      #scp -p $(cat ${DEPLOY_FILES_REPO}) ${USERNAME}@${line}:/tmp/.
      ssh -o ConnectTimeout=5 -q ${USERNAME}@${target} mkdir -p /tmp/${USERNAME} </dev/null # redirecting input from /dev/null to stop exiting out of the loop
      if [[ $? -ne 0 ]]; then
        echo -e "skipping server ${target}, connection was unsuccessful"
      else
        ssh -o ConnectTimeout=5 -q ${USERNAME}@${target} rm -f /tmp/${USERNAME}/* </dev/null # redirecting input from /dev/null to stop exiting out of the loop
        scp -o ConnectTimeout=5 -q -p ${AUDIT_TAR_FILE} run_audit.sh deploy_audit.sh ${USERNAME}@${target}:/tmp/${USERNAME}/.
      fi
      #ssh -q ${USERNAME}@${target} chown mongo /tmp/run_audit.sh /tmp/${AUDIT_TAR_FILE}
  fi
  done <${AUDIT_TARGET_HOST_FILE}

  echo "pushing it to jump server ${JUMP_SERVER}"
  scp -q -p push_audit_deploy2aws.sh ${USERNAME}@${JUMP_SERVER}:/tmp/.

  echo -e "completed ..."

  echo -e "Pls use following command on all target hosts to deploy the files being pushed ..."
  echo -e ""
  echo -e "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
  echo -e "log into to target server, sudo to mongo/postgres"
  echo -e ""
  #echo -e "mkdir -p /opt/mongo/staging"
  #echo -e "cd /opt/mongo/staging"
  #echo -e "-----------------------Deploy Audit Binary------------------------------------------"
  echo -e "Pls run /tmp/<networkid>/deploy_audit.sh /tmp/<networkid>/deploy_audit.tar.gz on target"
}

printUsage(){
  echo -e "$(basename $(readlink -nf $0)) <username> <target_host_file> <installation_dir>"
  echo -e "For e.g. $(basename $(readlink -nf $0)) u1111111 all_on_prem_mongo_hosts.txt /opt/mongo"
}

if [[ $# -ne 2 ]]; then
  echo -e "missing mandatory arguments "
  printUsage
  exit 1
fi

if [[ -z $1 || -z $2 ]]; then
  echo -e "missing mandatory arguments "
  printUsage
  exit 1
fi

USERNAME=$1
AUDIT_TARGET_HOST_FILE=$2
JUMP_SERVER="usdf23v0466"

if [[ ! -f ${AUDIT_TARGET_HOST_FILE} ]]; then
  echo -e "Target host file is ${AUDIT_TARGET_HOST_FILE} missing !!!"
  exit 1
fi

echo -e "`date` starting"
main
echo -e "`date` completed"