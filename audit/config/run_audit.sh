#!/bin/bash
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Script: 		run_audit.sh
# Description: 	Executes Audit Scan frame work 
#				
# Usage: 		./run_audit.sh
#				For e.g. 
#				./run_audit.sh
#
# History
#====================================================================================================================
# When			Who			What
#====================================================================================================================
# 03/01/2020	Anil Singh	Initial creation
# 04/01/2021	Anil Singh	Included BASE_DIR environment variable to choose different location for AUDIT Home
#
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
main(){
	#export PATH=$PATH:/usr/local/bin:/bin:/usr/bin:/usr/X11R6/bin:/usr/local/sbin:/sbin:/usr/sbin
	export BASE_DIR=/opt/mongo
	export ENV_FILE="audit.env"
	export APP_NAME="AUDIT"
	export AUDIT_HOME=${BASE_DIR}/app/audit
	export APP_CONFIG=${AUDIT_HOME}/config
	export APP_LOG=${AUDIT_HOME}/log

	if [[ ! -d ${BASE_DIR} ]]; then
		echo -e "Base dir ${BASE_DIR} does not exists, aborting !!!"
		exit 1
	fi

	if [[ ! -f ${APP_CONFIG}/${ENV_FILE} ]]; then
		echo -e "Config file ${APP_CONFIG}/${ENV_FILE} is missing !!!"
		exit
	fi

	source ${APP_CONFIG}/${ENV_FILE}

	#$PYTHON ${BASE_DIR}/app/com/mmc/audit/scan.py

	#export RUN_LOG_FILE=/opt/mongo/app/audit/log/run_audit_$(date -d"-0 days" +\%Y\%m\%d_\%H\%M\%S).log
	export ERROR_MAIL_RECPT="${NOTIFICATION_DL}"

	echo -e "`date` - validating environment variables...."
	myVarValidation="Valid"

	if [[ -z $ENV ]]; then echo -e " ENV not set" && myVarValidation="Not Valid"; fi 
	if [[ -z $REST_ENV ]]; then echo -e " REST_ENV not set" && myVarValidation="Not Valid"; fi 
	if [[ -z $BASE_DIR ]]; then echo -e " BASE_DIR not set" && myVarValidation="Not Valid"; fi 
	if [[ -z $APP_NAME ]]; then echo -e " APP_NAME not set" && myVarValidation="Not Valid"; fi 
	if [[ -z $AUDIT_HOME ]]; then echo -e " AUDIT_HOME not set" && myVarValidation="Not Valid"; fi 
	if [[ -z $APP_CONFIG ]]; then echo -e " APP_CONFIG not set" && myVarValidation="Not Valid"; fi 
	if [[ -z $PYTHONPATH ]]; then echo -e " PYTHONPATH not set" && myVarValidation="Not Valid"; fi 
	#if [[ -z $REGION ]]; then echo -e " REGION not set" && myVarValidation="Not Valid"; fi 
	#if [[ -z $OPCO ]]; then echo -e " OPCO not set" && myVarValidation="Not Valid"		; fi 
	#if [[ -z $DC_LOCATION ]]; then echo -e " DC_LOCATION not set" && myVarValidation="Not Valid"; fi 
	#if [[ -z $DOMAIN ]]; then echo -e " DOMAIN not set" && myVarValidation="Not Valid"; fi 
	if [[ -z $GIT_PYTHON_REFRESH ]]; then echo -e " GIT_PYTHON_REFRESH not set" && myVarValidation="Not Valid"; fi 
	if [[ -z $PYTHON ]]; then echo -e " PYTHON not set" && myVarValidation="Not Valid"; fi 
	if [[ -z $ERROR_MAIL_RECPT ]]; then echo -e " ERROR_MAIL_RECPT not set" && myVarValidation="Not Valid"; fi 

	if [[ ${myVarValidation} == "Not Valid" ]]; then
		echo -e "`date` - validation failed, mandatory env variable(s) are not set, sending email, aborting !!!"

		EMAIL_CONTENTS="Attn Team,

	An error occurred while running the scan on server `hostname` on `date` ... \n

	Either one or all mandatory env variables are missing .... \n

	ENV/REST_ENV/BASE_DIR/APP_NAME/AUDIT_HOME/APP_CONFIG/PYTHONPATH/REGION/OPCO/DC_LOCATION/DOMAIN/GIT_PYTHON_REFRESH/PYTHON/ERROR_MAIL_RECPT

	Pls ensure above variables are exported in /opt/mongo/run_audit.sh  
	"
		#mail -s "Audit frame work job - run error " ${ERROR_MAIL_RECPT} <${AUDIT_HOME}/log/run_scan.log
		echo -e $EMAIL_CONTENTS | mail -s "Audit frame work job - run error " ${ERROR_MAIL_RECPT}
		exit 1
	fi

	echo -e "`date` - validation completed successfully, proceeding with execution .."
	echo -e "`date` - executing ${BASE_DIR}/app/com/mmc/audit/scan.py"

	#touch ${AUDIT_HOME}/log/run_audit.log

	#$PYTHON ${BASE_DIR}/app/com/mmc/audit/scan.py >> ${AUDIT_HOME}/log/run_scan`date +%m%d%Y_%H%M%S`.log
	$PYTHON ${BASE_DIR}/app/com/mmc/audit/scan.py > ${AUDIT_HOME}/log/audit_scan_`date +%m%d%Y_%H%M%S`.log
	retval=$?
	echo -e "`date` - completed executing ${BASE_DIR}/app/com/mmc/audit/scan.py, return code is >>> ${retval}"

	#EMAIL_CONTENTS="Attn Team,

	#An error occurred while running the scan on server `hostname` on `date`
	#Pls check ${AUDIT_HOME}/log/run_audit.log file or $AUDIT_HOME/log/audit.log.* for more information 
	#"
	if [[ ${}retval} -ne 0 ]]; then
			mail -s "Audit frame work job - run error (`hostname`) " ${ERROR_MAIL_RECPT} <${AUDIT_HOME}/log/run_scan.log
	fi

	#ERROR_RUN=`grep -i "err" ${AUDIT_HOME}/log/run_scan.log`

	if [[ ! -z ${ERROR_RUN} ]]; then
		mail -s "Audit frame work job - Error" ${ERROR_MAIL_RECPT} < ${AUDIT_HOME}/log/run_scan.log
	fi 
	# moving run_audit file log to include current datetimestamp
	mv ${AUDIT_HOME}/log/run_scan.log ${AUDIT_HOME}/log/run_scan.log.`date +%m%d%Y_%H%M%S`
}
printUsage(){
  echo -e "$(basename $(readlink -nf $0)) <base_app_dir>"
  echo -e "For e.g. $(basename $(readlink -nf $0)) /opt/mongo"
}

echo -e "`date` - starting execution"
#echo -e "`date` - validating arguments"
#if [[ $# -ne 1 ]]; then
#  echo -e "missing mandatory arguments "
#  printUsage
#  exit 1
#fi
#export BASE_DIR=$1
main
echo -e "`date` - audit frame work scan/transmit process completed"
