#!/bin/bash
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Script:       push_audit_deploy.sh
# Description:  Pushes audit deployment files to target
#
# Usage:     ./push_audit_deploy.sh <username> <audit_tar_file> <target_host_files>
#       For e.g. 
#       ./push_audit_deploy.sh u111111 ./audit_deploy.tar.gz ./target_host_files.csv
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

  echo -e "lsting files to be pushed"
  for x in "${AUDIT_TAR_FILE} run_audit.sh deploy_audit.sh"; do    
    ls -altr $x | awk '{print $6"   " $7"   " $8"   " $9}'; 
  done

  echo -e "pushing files to target servers ..."
  #DEPLOY_FILES="$AUDIT_TAR_FILE run_audit.sh"
  
  while read -r target; do
  	if [[ ! -z $target ]]; then
	  	echo -e "pushing deployment files to >>> ${target}:/tmp/${USERNAME}"
	  	#scp -p $(cat ${DEPLOY_FILES_REPO}) ${USERNAME}@${line}:/tmp/.
      ssh -q ${USERNAME}@${target} mkdir -p /tmp/${USERNAME} </dev/null # redirecting input from /dev/null to stop exiting out of the loop
      ssh -q ${USERNAME}@${target} rm -f /tmp/${USERNAME}/* </dev/null # redirecting input from /dev/null to stop exiting out of the loop
	  	scp -q -p ${AUDIT_TAR_FILE} run_audit.sh deploy_audit.sh ${USERNAME}@${target}:/tmp/${USERNAME}/.
	  	#ssh -q ${USERNAME}@${target} chown mongo /tmp/run_audit.sh /tmp/${AUDIT_TAR_FILE}
	 fi
  done <${AUDIT_TARGET_HOST_FILE}

  echo "pushing it to jump server ${JUMP_SERVER}:/tmp/${USERNAME}"
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
  echo -e "$(basename $(readlink -nf $0)) <username> <aud_deploy_tar_file> <target_host_file> "
  echo -e "For e.g. $(basename $(readlink -nf $0)) u1111111 deploy_audit.tar.gz target_host_file.csv"
}

if [[ $# -ne 3 ]]; then
  echo -e "missing mandatory arguments "
  printUsage
  exit 1
fi

if [[ -z $1 || -z $2 || -z $3 ]]; then
  echo -e "missing mandatory arguments "
  printUsage
  exit 1
fi

USERNAME=$1
AUDIT_TAR_FILE=$2
AUDIT_TARGET_HOST_FILE=$3
JUMP_SERVER="usdf23v0466"

if [[ ! -f ${AUDIT_TAR_FILE} ]]; then
  echo -e "Audit deployment tar file ${AUDIT_TAR_FILE} missing !!!"
fi

if [[ ! -f ${AUDIT_TARGET_HOST_FILE} || -s ${AUDIT_TARGET_HOST_FILE} ]]; then
  echo -e "Target host file is ${AUDIT_TARGET_HOST_FILE} missing or empty !!!"
fi

echo -e "`date` starting"
main
echo -e "`date` complete"
