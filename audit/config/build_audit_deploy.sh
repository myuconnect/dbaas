#!/bin/bash
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Script:       build_audit_deploy.sh
# Description:  Builds audit deployment files to be pushed to target hosts
#
# Usage:        ./build_audit_deploy.sh <username> <audit_tar_file> <target_host_files>
#               For e.g. 
#               ./build_audit_deploy.sh u111111 ./audit_deploy.tar.gz ./target_host_files.csv
#
#
# History
#================================================================================================================
# When      Who     What
#================================================================================================================
# 8/18/2020  Anil Singh  Initial creation
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

main(){
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

  echo -e "Deployment audit tar file file ${DEPLOY_HOME}/${DEPLOY_AUD_TAR_FILE} is created ...
Pls follow below command to push this file to target
---------------------------------------------------------------------------------------------------------
1. Create target hot file
    OnPrem: Create a file target_hosts.csv with all target host name
    AWS: Login to jump server usdf23v0466 then create a file target_hosts.csv with all target AWS host name

3. Run following command to push the files to target
  ./push_audit_deploy.sh <your_network_id> ${DEPLOY_HOME}/${DEPLOY_AUD_TAR_FILE} all_on_prem_mongo_hosts.txt

"
}
printUsage(){
  echo -e "$(basename $(readlink -nf $0)) "
  echo -e "For e.g. $(basename $(readlink -nf $0))"
}

#USERNAME=$1
echo -e "`date` starting..."
main
echo -e "`date` completed..."
