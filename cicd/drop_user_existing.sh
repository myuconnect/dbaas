oracle@usdfw21db27v:NOSID>crontab -l|grep -i drop
#  Drop User Job
00 3 * * * /opt/oracle/scripts/wrappers/run_drop_user_scripts.sh 1>/dev/null 2>&                                                                                                                                                             1
oracle@usdfw21db27v:NOSID>
oracle@usdfw21db27v:NOSID>
oracle@usdfw21db27v:NOSID>cat /opt/oracle/scripts/wrappers/run_drop_user_scripts.sh
#!/usr/bin/ksh

#
#  One line is required for each database on the server
#

/opt/oracle/scripts/dropusers/drop_users.sh /var/oracle/admin/oltp120 oltp120 PROD MARSH_USER_PROFILE
/opt/oracle/scripts/dropusers/drop_users.sh /var/oracle/admin/oltp95 oltp95 PROD MARSH_USER_PROFILE
#/opt/oracle/scripts/dropusers/drop_users.sh /var/oracle/admin/oltp127 oltp127 PROD MARSH_USER_PROFILE


/opt/oracle/scripts/dropusers/drop_users.sh /var/oracle/admin/oltp120 oltp120 PROD MARSH_PROD_PROFILE
/opt/oracle/scripts/dropusers/drop_users.sh /var/oracle/admin/oltp95 oltp95 PROD MARSH_PROD_PROFILE
#/opt/oracle/scripts/dropusers/drop_users.sh /var/oracle/admin/oltp127 oltp127 PROD MARSH_PROD_PROFILE

/opt/oracle/scripts/dropusers/drop_users.sh /var/oracle/admin/oltp120 oltp120 PROD MARSH_DBA_PROFILE
/opt/oracle/scripts/dropusers/drop_users.sh /var/oracle/admin/oltp95 oltp95 PROD MARSH_DBA_PROFILE
#/opt/oracle/scripts/dropusers/drop_users.sh /var/oracle/admin/oltp127 oltp127 PROD MARSH_DBA_PROFILE

exit 0
oracle@usdfw21db27v:NOSID>cat /opt/oracle/scripts/dropusers/drop_users.sh
#!/bin/ksh
#
# Script Name: drop_users.sh
# Script Purpose: Drop users with specific non-DBA profile whose account has been expired for 100 days or more for a database on this machine.
# Usage:  drop_users.sh <DB_ADMIN_DIR> <DBNAME> <DEV/MOD/PROD> <PROFILE>
#
# Parmeters:  DB_ADMIN_DIR      - Admin Directory of the database
#             DBNAME            - Name of the instance
#             DEV/MOD/PROD      - Database type to determine which RMAN catalog to use for reporting
#             PROFILE           - Profile of users to be dropped
#
#
# 8/27/2008  Gennady Barenbaum   V1.0 Created
# 5/23/2017  Nick Pranger        V2.0 Updated to drop users that have been expired or locked for 90 days rather than 100 days
#                                       Also modified to allow for dropping of individual DBA accounts that have not been accessed
#                                       Both of these changes have been made to match the new Security Policy released in spring 2017
#
#
#set -x

#
# CD to the script directory
#
cd `dirname $0`

#
# FUNCTIONS
#


#
# Check for an index rebuild flag indicating another rebuild is already running
# Set the rebuild flag if no other rebuilds are running
#

fn_check_drop_flag ()
{
  if [ ! -f ${DB_LOG_DIR}/DROP_USERS_RUNNING_* ] ; then
    touch ${DB_LOG_DIR}/DROP_USERS_RUNNING_${DBNAME}
    chown oracle:dba ${DB_LOG_DIR}/DROP_USERS_RUNNING_${DBNAME}
  else
    echo " A drop user script is currently running against ${DBNAME}, please try again later."  | ${LOG_CMD_MAIN}

    export TS=`date '+%d-%b-%Y %H:%M'`
    export DROP_FINISH_DATE=`date '+%d-%b-%Y %H:%M'`

    export DROP_SUCC_FAIL='REDUNDANT'
    export DROP_FAIL_STAT='Index Rebuild already running'
    fn_finish_status

    echo "******************************************************************"
    echo " " | ${LOG_CMD_MAIN}
    echo "\n\tFinish Time: ${TS}\n" | ${LOG_CMD_MAIN}
    echo "\n\tExiting Script: ${SCRIPT_NAME}\n" | ${LOG_CMD_MAIN}
    echo " " | ${LOG_CMD_MAIN}
    echo "******************************************************************"
    exit 0
  fi

}


#
# Write the final finish time status block out to the drop log
#

fn_write_finish_time ()
{

  export TS=`date '+%d-%b-%Y %H:%M'`

  echo "******************************************************************"
  echo " " | ${LOG_CMD_MAIN}
  echo "\n\tFinish Time: ${TS}\n" | ${LOG_CMD_MAIN}
  echo "\n\tExiting Script: ${SCRIPT_NAME}\n" | ${LOG_CMD_MAIN}
  echo " " | ${LOG_CMD_MAIN}
  echo "******************************************************************"
}



#
# Clear the drop flag after the drop is complete
#

fn_clear_drop_flag ()
{
  if [ -f ${DB_LOG_DIR}/DROP_USERS_RUNNING_* ] ; then
    ${RM} -f ${DB_LOG_DIR}/DROP_USERS_RUNNING_${DBNAME}
    echo " Drop Users done for ${DBNAME}!"  | ${LOG_CMD_MAIN}
  fi
}


#
# Check the status of database. Proceed only when status = 'OPEN'
#

fn_check_dbstatus ()
{
  echo " " | ${LOG_CMD_MAIN}
  echo " Checking database status!" | ${LOG_CMD_MAIN}
  echo " " | ${LOG_CMD_MAIN}

  $SQLPLUS << EOT > /dev/null

    connect ${DBADMINID}/${DBADMINPWD}

    whenever sqlerror exit sql.sqlcode
    whenever oserror exit 9

    set feedback off
    set pause off
    set trimspool on
    set heading off
    spool ${DB_LOG_DIR}/db_drop_status.log
    select status from v\$instance;
    spool off
  exit
EOT

  grep "OPEN" ${DB_LOG_DIR}/db_drop_status.log

  if [ $? -ne 0 ]; then
    export TS=`date '+%d-%b-%Y %H:%M'`
    echo " " | ${LOG_CMD_MAIN}
    echo " Could not validate that database ${ORACLE_SID} is open, do not perform user drops. Aborting!" | ${LOG_CMD_MAIN}
    echo " Drop users job FAILED at ${TS}." | ${LOG_CMD_MAIN}
    echo " " | ${LOG_CMD_MAIN}
    fn_clear_drop_flag
    export DROP_SUCC_FAIL='FAILED'
    export DROP_FAIL_STAT='Database is not open cannot perform user drops!'
    fn_finish_status
    exit 1
  else
    echo " " | ${LOG_CMD_MAIN}
    echo " Database ($ORACLE_SID) is open for user drops!" | ${LOG_CMD_MAIN}
    echo " " | ${LOG_CMD_MAIN}
  fi
  ${RM} -f ${DB_LOG_DIR}/db_drop_status.log
}


#
# Print out the variables set in run to primary log
#

fn_log_vars ()
{
  echo "SQLPLUS: ${SQLPLUS}" | ${LOG_CMD_MAIN}
  echo "ORACLE_SID: ${ORACLE_SID}" | ${LOG_CMD_MAIN}
  echo "ORACLE_HOME: ${ORACLE_HOME}" | ${LOG_CMD_MAIN}
  echo "ORACLE_USER: ${ORACLE_USER}" | ${LOG_CMD_MAIN}
  echo "DB_REGION: ${DB_REGION}" | ${LOG_CMD_MAIN}
  echo "SERVER: ${SERVER}" | ${LOG_CMD_MAIN}
  echo "SCRIPT: ${SCRIPT_NAME}" | ${LOG_CMD_MAIN}
  echo "STATUS OWNER ID: ${STATID}" | ${LOG_CMD_MAIN}
  echo "STATUS DATABASE: ${STATSID}" | ${LOG_CMD_MAIN}
  echo "RM: ${RM}" | ${LOG_CMD_MAIN}
}


#
# Run the drop user command using SQL*Plus
#

fn_run_drop()
{
  export TS=`date '+%d-%b-%Y %H:%M'`
  echo " " | ${LOG_CMD_MAIN}
  echo " Initiated Drop Users for ${DBNAME} at ${TS}!" | ${LOG_CMD_MAIN}
  echo " " | ${LOG_CMD_MAIN}

  PROFILE_EXIST=`echo "select decode(count(*),0,'NONE') as "cnt" from dba_profiles where profile = '${PROFILE}';" | sqlplus -s ${DBADMINID}/${DBADMINPWD} | grep "NONE"`

  if [ $? -eq 0 ]; then
      echo " " | ${LOG_CMD_MAIN}
      echo " Profile ${PROFILE} does not exist" | ${LOG_CMD_MAIN}
      echo " " | ${LOG_CMD_MAIN}
      fn_clear_drop_flag
      export DROP_SUCC_FAIL='FAILED'
      export DROP_FAIL_STAT='Profile ${PROFILE} does not exist, cannot perform user drops!'
      fn_finish_status
      exit 1
  else
      echo " " | ${LOG_CMD_MAIN}
      echo " Dropping users with ${PROFILE} profile!" | ${LOG_CMD_MAIN}
      echo " " | ${LOG_CMD_MAIN}
  fi

  ${RM} -f ${EXPIRED_USERS}

  $SQLPLUS << EOT > /dev/null
  connect ${DBADMINID}/${DBADMINPWD}

  whenever sqlerror exit sql.sqlcode
  whenever oserror exit 9

  set feedback off
  set trimspool on
  set heading off
  set verify off
  set pagesize 0
  set echo off
  spool ${EXPIRED_USERS}
  select username
    from dba_users
   where ((expiry_date < (sysdate - 90)
           or (expiry_date is null and created < (sysdate - 90)))
          or (account_status like '%LOCKED%' and lock_date < (sysdate - 90)))
     and username not in ('SYSTEM', 'SYS', 'SYSMAN', 'PUBLIC', 'DBSNMP', 'AUDITOR', 'DBA_ADMIN')
     and profile not in (select distinct profile
                           from dba_profiles
                          where resource_type = 'PASSWORD'
                           and resource_name = 'PASSWORD_LIFE_TIME'
                            and limit in ('UNLIMITED', 'DEFAULT'))
     and username <> 'XS\$NULL'
     and profile = '${PROFILE}';
  spool off
  exit
EOT

  VALUE_RET=0

  for USER in `cat ${EXPIRED_USERS}`
  do
    echo " " | ${LOG_CMD_MAIN}
    echo " Dropping user ${USER}" | ${LOG_CMD_MAIN}
    echo " " | ${LOG_CMD_MAIN}

    HAS_OBJECTS=`echo "select decode(count(*),0,'NONE') as "cnt" from dba_objects where owner = '${USER}' and object_type in ('TABLE', 'PROCEDURE', 'FUNCTION', 'PACKAGE', 'VIEW');" | sqlplus -s ${DBADMINID}/${DBADMINPWD} | grep "NONE"`

    if [ $? -ne 0 ]; then
      echo " " | ${LOG_CMD_MAIN}
      echo "   User ${USER} owns some objects.  Not dropping." | ${LOG_CMD_MAIN}
      echo " " | ${LOG_CMD_MAIN}
      HAS_OBJECTS='YES'
      VALUE_RET=1
    else
      HAS_OBJECTS='NO'
    fi

    if [ ${HAS_OBJECTS} = 'NO' ]; then
        fn_create_audit

# Dropping user with cascade option in case user has synonyms.

        $SQLPLUS << EOT > /dev/null
        connect ${DBADMINID}/${DBADMINPWD};

        whenever sqlerror exit sql.sqlcode
        whenever oserror exit 9

        drop user ${USER} cascade;
        exit
EOT

      if [ $? -ne 0 ]; then
          VALUE_RET=1
          echo " " | ${LOG_CMD_MAIN}
          echo " Error dropping ${USER} user" | ${LOG_CMD_MAIN}
          echo " " | ${LOG_CMD_MAIN}
      fi

    fi
  done

  cat ${CURR_LOG} | ${LOG_CMD_MAIN}

  export TS=`date '+%d-%b-%Y %H:%M'`
  export DROP_FINISH_DATE=`date '+%d-%b-%Y %H:%M'`

  if [ ${VALUE_RET} = 0 ] ; then
    echo " " | ${LOG_CMD_MAIN}
    echo " Drop users job SUCCESSFULL for ${DBNAME} on ${TS}!" | ${LOG_CMD_MAIN}
    echo " " | ${LOG_CMD_MAIN}
    export DROP_SUCC_FAIL='SUCCESSFUL'
    export DROP_FAIL_STAT='Drop users successful'
    fn_finish_status
  else
    echo " " | ${LOG_CMD_MAIN}
    echo " Drop users job FAILED for ${DBNAME} on ${TS}!" | ${LOG_CMD_MAIN}
    echo " " | ${LOG_CMD_MAIN}
    fn_clear_drop_flag
    export DROP_SUCC_FAIL='FAILED'
    export DROP_FAIL_STAT='Drop users failed'
    fn_finish_status
    exit 1
  fi

}



#
# Remove old logs from database LOG directory
#

fn_cleanup_logs ()
{
  echo " " | ${LOG_CMD_MAIN}
  echo " Removing old Drop Users logs for ${DBNAME}!" | $LOG_CMD_MAIN
  echo " " | ${LOG_CMD_MAIN}
  find ${DB_LOG_DIR} -name "*drop_users*.log" -type f -mtime +7 -print -exec ${RM} -f {} \;> /dev/null
  find ${DB_LOG_DIR} -name "*report*.log" -type f -mtime +7 -print -exec ${RM} -f {} \;> /dev/null
  chmod 660 ${DB_LOG_DIR}/*.*
}



#
# Insert the row for drop status into the status table at the start of the job
#

fn_start_status ()
{
  echo " " | ${LOG_CMD_MAIN}
  echo " Inserting row into drop status table!" | ${LOG_CMD_MAIN}
  echo " " | ${LOG_CMD_MAIN}

  $SQLPLUS << EOT > ${DB_LOG_DIR}/db_drop_status.log
    connect ${STATID}/${STATPWD}@${STATSID}

    whenever sqlerror exit sql.sqlcode
    whenever oserror exit 9

    insert into drop_users_status_table
      (instance_name,
       server,
       db_type,
       profile,
       start_time,
       drop_status,
         db_region)
    values
      ('${ORACLE_SID}',
       '${SERVER}',
       '${PGM_LOC}',
       '${PROFILE}',
       TO_DATE('${DROP_START_DATE}', 'dd-mon-yyyy HH24:MI'),
       'STILL RUNNING',
         '${DB_REGION}');
    commit;
  exit
EOT

  grep "ERROR" ${DB_LOG_DIR}/db_drop_status.log

  if [ $? -eq 0 ]; then
    echo " " | ${LOG_CMD_MAIN}
    echo " FAILED when inserting row into drop status table!" | ${LOG_CMD_MAIN}
    echo " " | ${LOG_CMD_MAIN}
  fi

  ${RM} -f ${DB_LOG_DIR}/db_drop_status.log
}



#
# Insert row for each dropped user into the audit table
#

fn_create_audit ()
{
  echo " " | ${LOG_CMD_MAIN}
  echo " Inserting row into audit table!" | ${LOG_CMD_MAIN}
  echo " " | ${LOG_CMD_MAIN}

  $SQLPLUS << EOT > ${DB_LOG_DIR}/db_audit_status.log
    connect ${STATID}/${STATPWD}@${STATSID}

    whenever sqlerror exit sql.sqlcode
    whenever oserror exit 9

    insert into dropped_users
      (instance_name,
       server,
       db_type,
       username,
         profile,
       drop_date)
    values
      ('${ORACLE_SID}',
       '${SERVER}',
       '${PGM_LOC}',
         '${USER}',
       '${PROFILE}',
       sysdate);
    commit;
  exit
EOT

  grep "ERROR" ${DB_LOG_DIR}/db_audit_status.log

  if [ $? -eq 0 ]; then
    echo " " | ${LOG_CMD_MAIN}
    echo " FAILED when inserting row into drop audit table!" | ${LOG_CMD_MAIN}
    echo " " | ${LOG_CMD_MAIN}
  fi

  ${RM} -f ${DB_LOG_DIR}/db_audit_status.log
}


#
# Update the row for drop status at the end of the job
#

fn_finish_status ()
{
  echo " " | ${LOG_CMD_MAIN}
  echo " Updating row in drop status table!" | ${LOG_CMD_MAIN}
  echo " " | ${LOG_CMD_MAIN}

  $SQLPLUS << EOT > ${DB_LOG_DIR}/db_drop_status.log
    connect ${STATID}/${STATPWD}@${STATSID}

    whenever sqlerror exit sql.sqlcode
    whenever oserror exit 9

    update drop_users_status_table
       set finish_time = TO_DATE('${DROP_FINISH_DATE}', 'dd-mon-yyyy HH24:MI'),
           drop_status = '${DROP_SUCC_FAIL}',
           drop_status_message = '${DROP_FAIL_STAT}'
     where instance_name = '${ORACLE_SID}'
       and server = '${SERVER}'
       and db_type = '${PGM_LOC}'
       and profile = '${PROFILE}'
       and start_time = TO_DATE('${DROP_START_DATE}', 'dd-mon-yyyy HH24:MI')
       and db_region = '${DB_REGION}';
    commit;
  exit
EOT

  grep "ERROR" ${DB_LOG_DIR}/db_drop_status.log

  if [ $? -eq 0 ]; then
    echo " " | ${LOG_CMD_MAIN}
    echo " FAILED when updating row in rebuild status table!" | ${LOG_CMD_MAIN}
    echo " " | ${LOG_CMD_MAIN}
  fi

  ${RM} -f ${DB_LOG_DIR}/db_drop_status.log
}



#
#  MAIN CODE
#



#
# Check input variables
#

  if [ -z $1 ]; then
    echo "Database admin directory was not passed correctly."
    echo "Correct format for calling is : "
    echo "drop_users.sh <DB_ADMIN_DIR> <DBNAME> <DEV/MOD/PROD> <PROFILE>."
    echo "Aborting!"
    exit 1
  fi

  if [ -z $2 ]; then
    echo "DB Name was not passed correctly."
    echo "Correct format for calling is : "
    echo "drop_users.sh <DB_ADMIN_DIR> <DBNAME> <DEV/MOD/PROD> <PROFILE>."
    echo "Aborting!"
    exit 1
  fi

  if [ -z $3 ]; then
   echo "DB Level (DEV/MOD/PROD) was not passed correctly."
    echo "Correct format for calling is : "
    echo "drop_users.sh <DB_ADMIN_DIR> <DBNAME> <DEV/MOD/PROD> <PROFILE>."
    echo "Aborting!"
    exit 1
  else
    case $3 in
       DEV) ;;
       MOD) ;;
      PROD) ;;
         *) echo "DB Level (DEV/MOD/PROD) was not passed correctly."
            echo "Correct format for calling is : "
            echo "drop_users.sh <DB_ADMIN_DIR> <DBNAME> <DEV/MOD/PROD> <PROFILE>."
            echo "Aborting!"
            exit 1;;
    esac
  fi

  if [ -z $4 ]; then
    echo "Profile was not passed correctly."
    echo "Correct format for calling is : "
    echo "drop_users.sh <DB_ADMIN_DIR> <DBNAME> <DEV/MOD/PROD> <PROFILE>."
    echo "Aborting!"
    exit 1
  fi

#
# Set up Script Variables and Environment
#

  export DBADMIN=$1
  export DBNAME=$2
  export PGM_LOC=$3
  export PROFILE=$4
  export DB_REGION=NA

  . ${DBADMIN}/.${DBNAME}_env

  . `dirname $0`/../.server_environ

  . ${DBADMIN}/.${DBNAME}_env

  DB_LOG_DIR=${DBADMIN}/logs
  EXPIRED_USERS=${DB_LOG_DIR}/expired_users.cfg

  if [ ! -d ${DB_LOG_DIR} ]; then
     mkdir -p ${DB_LOG_DIR}
     if [ $? -ne 0 ]; then
        echo " Error creating log directory ${DB_LOG_DIR}. Aborting!/n"
        exit 1
     fi
  fi

#
# The following code sets up one master output file that everything goes to
#

export DROP_FILE_DATE=`date '+%b.%d.%y-%H.%M'`

OUTF=${DB_LOG_DIR}/call_drop_users_${PROFILE}.sh.out
SCRIPT_NAME=drop_users

{
  export TS=`date '+%d-%b-%Y %H:%M'`
  export DROP_START_DATE=`date '+%d-%b-%Y %H:%M'`

  MAIN_LOG=${DB_LOG_DIR}/${SCRIPT_NAME}_${DBNAME}_${PROFILE}_`date +%Y%m%d%H%M`.log
  CURR_LOG=${DB_LOG_DIR}/${SCRIPT_NAME}_${DBNAME}_${PROFILE}.log
  LOG_CMD_MAIN="tee -a ${MAIN_LOG}"

  echo "`date` ----------------Beginning of Script------------"

  echo "******************************************************************"
  echo "\n\tScript Name: ${SCRIPT_NAME}\n" | ${LOG_CMD_MAIN}
  echo "\n\tStart Time: ${TS}\n" | ${LOG_CMD_MAIN}
  echo "\n\tMain Log: ${MAIN_LOG}\n" | ${LOG_CMD_MAIN}
  echo " " | ${LOG_CMD_MAIN}
  echo "******************************************************************"

  export TS=`date '+%d-%b-%Y %H:%M'`
  SQLPLUS="$ORACLE_HOME/bin/sqlplus -s /nolog"
  ORACLE_USER=`whoami`
  SQL_FILE=${DB_LOG_DIR}/drop_users.sql

  ${RM} -f ${CURR_LOG}
  touch ${CURR_LOG}
  cat /dev/null > ${CURR_LOG}

#
#  Run Script
#

  fn_start_status

  export TS=`date '+%d-%b-%Y %H:%M'`

  echo " Starting Drop Users on ${DBNAME} at ${TS}." | ${LOG_CMD_MAIN}
  echo " " | ${LOG_CMD_MAIN}

  fn_check_dbstatus

  fn_check_drop_flag

  fn_log_vars

  fn_run_drop

  fn_cleanup_logs

  fn_clear_drop_flag

  fn_write_finish_time

} > ${OUTF}
exit 0


oracle@usdfw21db27v:NOSID>
