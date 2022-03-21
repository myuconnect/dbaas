#!/bin/bash
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Script: 		deploy_audit.sh
# Description: 	Deploys audit source code on target host
#				
# Usage: 		./deploy_audit.sh
#				For e.g. 
#				./deploy_audit.sh
#
# History
#========================================================================================================
# When			Who			What
#========================================================================================================
# 03/01/2020	Anil Singh	Initial creation
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

main(){
	#BASE_DIR=/opt/mongo
	#DEPLOY_TAR_FILE="/tmp/deploy_audit.tar.gz"
	echo -e "`date` - upgrade meta file : ${UPGRADE_METADATA_FILE}"
	echo -e "`date` - Audit home : ${AUDIT_HOME}"
	echo -e "`date` - checking if new update is pushed to this server ..."
	#echo "`date` - checking for file >> ${UPDATE_TAR_FILE}"

	CUR_DIR=$PWD
	TAR_FILE_STAT=`stat --printf=%y ${DEPLOY_AUDIT_TAR_FILE} | cut -d. -f1`
	# checking if this tar file was already deployed
	#echo -e "`date` - starting Audit deployment ..."

	if test -f ${DEPLOY_AUDIT_TAR_FILE}; then
		#echo -e "new deployment archive file found ${DEPLOY_AUDIT_TAR_FILE}, extracting "
		echo -e "`date` - new update found  `ls -altr ${DEPLOY_AUDIT_TAR_FILE}` "
		echo -e "`date` - extracting audit tar file ${DEPLOY_AUDIT_TAR_FILE} to staging ${BASE_DIR}/staging "
		if test -d ${AUDIT_HOME}; then
			echo -e "`date` - Audit home dir exists, will replace .py and .json files"
			rm -fR ${BASE_DIR}/staging
			rm -fR ${BASE_DIR}/static/config
			mkdir -p ${BASE_DIR}/staging
			mkdir -p ${BASE_DIR}/static/config
			if [[ -d ${BASE_DIR}/app/audit/config ]]; then
				cp -p ${BASE_DIR}/app/audit/config/* ${BASE_DIR}/static/config/.
			fi
			cd ${BASE_DIR}/staging
			rm -fR app
			tar -xvzf ${DEPLOY_AUDIT_TAR_FILE}
			echo -e " finished extracting, updating upgrade metadata ..."
			echo -e "copying files to destination ..."
			cp -p ${BASE_DIR}/staging/app/com/mmc/audit/*.py ${BASE_DIR}/app/com/mmc/audit/.
			cp -p ${BASE_DIR}/staging/app/com/mmc/db/*.py ${BASE_DIR}/app/com/mmc/db/.
			cp -p ${BASE_DIR}/staging/app/com/mmc/common/*.py ${BASE_DIR}/app/com/mmc/common/.
			cp -p ${BASE_DIR}/staging/app/audit/config/*.json ${BASE_DIR}/app/audit/config/.
			cp -p ${BASE_DIR}/static/config/* ${BASE_DIR}/app/audit/config/.
		else
			echo -e "Audit home dir does not exists, appears to be fresh install, will extrtact file in ${BASE_DIR}"
			cd $BASE_DIR
			tar -xvzf ${DEPLOY_AUDIT_TAR_FILE}
			echo -e "completed extracting file to base dir ${BASE_DIR}"
			echo -e "copying run_audit file to ${BASE_DIR}"
			cp -p ${AUDIT_HOME}/config/run_audit.sh ${BASE_DIR}/.
		fi
		echo -e "'`date`' '${UPDATE_TAR_FILE}' '${TAR_FILE_STAT}'" >> ${UPGRADE_METADATA_FILE}
		echo -e "changing ownership to mongo"
		#chown -R mongo {BASE_DIR}
		echo -e "Pls remove ${DEPLOY_AUDIT_TAR_FILE} to stop deploying files accidently !!!"
		echo -e "-----------------------Deploying Audit Config------------------------------------------"
		echo -e "Following steps are needed for fresh deployment only"
		echo -e "1. Ensure target host is registered in repository"
		echo -e "2. BASE_DIR must be set (root directory of audit framework is installed)"
		echo -e "3. SMTP_SERVER, LDAP_SERVER env variable must be set correctly"		
		echo -e "3. schedule a cronjob to run run_audit.sh every day after 12AM"
		echo -e "for e.g. : "
		echo -e "# Audit frame work job (<your name> - <todays date>) "
		echo -e "20 01 * * 0-6 ${BASE_DIR}/run_audit.sh >> ${BASE_DIR}/app/audit/log/run_audit.log 2>&1"
		echo -e "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"	
	fi
}
printUsage(){
  echo -e "$(basename $(readlink -nf $0)) <aud_deploy_tar_file> <installation_dir> "
  echo -e "For e.g. $(basename $(readlink -nf $0)) /tmp/u1167965/deploy_audit.tar.gz"
}

echo -e "`date` - Validating arguments ..."

if [[ $# -ne 2 ]]; then
  echo -e "missing mandatory arguments "
  printUsage
  exit 1
fi

DEPLOY_AUDIT_TAR_FILE=$1
BASE_DIR=$2

#[ ! -f "$DEPLOY_AUDIT_TAR_FILE" ] && echo -e "audit deployment file ${DEPLOY_AUDIT_TAR_FILE} is missing !!!"; exit 1;
#[ ! -d "$BASE_DIR" ] && echo -e "Invalid installation dir !!!" ; exit 1;

if [[ ! -f $DEPLOY_AUDIT_TAR_FILE ]]; then
	echo -e "audit deployment file ${DEPLOY_AUDIT_TAR_FILE} is missing, aborting !!!"
	exit 1
fi
if [[ ! -d $BASE_DIR ]]; then
	echo -e "Installation directory ${BASE_DIR} does not exists, aborting !!!"
	exit 1
fi
echo -e "`date` - arguments received ..."
echo -e "`date` -     Deployment tar file : ${DEPLOY_AUDIT_TAR_FILE}"
echo -e "`date` -     Installation Dir : ${BASE_DIR}"

echo -e "`date` - Starting deployment"
UPGRADE_METADATA_FILE="${BASE_DIR}/app/audit/log/upgrade_stats.log"
AUDIT_HOME="${BASE_DIR}/app/audit"
echo -e "`date` - Using following variables ..."
echo -e "`date` - upgrade meta file : ${UPGRADE_METADATA_FILE}"
echo -e "`date` - audit home : ${AUDIT_HOME}"
main
echo -e "`date` - Deployment completed"
