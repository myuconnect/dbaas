#!/bin/bash
###########################################################
#MongoDump backup Script
#code written by :: Debasish Nayak
#Mongodump backup ( modified on 29-OCT-21 )
#----------------------------------------------------------
#=======================
#Mongo Variables
MONGOPATH=/var/lib/mongodb-mms-automation/mongodb-linux-x86_64-4.2.11-ent/bin
MONGOUSER="svc-mer-dba_admin"
MONGOPASS="=NW:89d(X9fsQMD"
TIMESTAMP=`date +%F-%H%M`
HOST=$1
PORT=$2
DBNAME=$3
BKP_PATH=$4
RETENTION=$5
BACKUP_FILE=${BKP_PATH}/${DBNAME}_${TIMESTAMP}.gz
#############################################################
#=====================
if [[ $# < 5 ]]; then
    echo "==============================================================================="
    echo "$(basename $(readlink -nf $0)) <HOST> <PORT> <DBNAME> <BACKUP DESTINATION> <RETENTION_BACKUP_DAYS>"
    echo "For e.g. $(basename $(readlink -nf $0)) usdfw21383.mrshmc.com 27017 mydb /var/mongo/export 3"
    echo "==============================================================================="
    exit 1
fi
###########################################################
if [[ -n $HOST || -n $PORT || -n $DBNAME || -n $BKP_PATH || -n $RETENTION ]]; then
    echo "`date` - Parameter verified"
else
    echo "`date` - Parameter verfication failed !!"
    echo "==============================================================================="
    echo "$(basename $(readlink -nf $0)) <HOST> <PORT> <DBNAME> <BACKUP DESTINATION> <RETENTION_BACKUP_DAYS>"
    echo "For e.g. $(basename $(readlink -nf $0)) usdfw21383.mrshmc.com 27017 mydb /var/mongo/export 3"
    echo "==============================================================================="
    exit 1
fi
#=========================================================
echo "`date` - proceeding with backup"
$MONGOPATH/mongodump --host $HOST -u $MONGOUSER -p $MONGOPASS --port $PORT --authenticationDatabase admin -d $DBNAME  --gzip --archive=${BACKUP_FILE}
if [[ $? -ne 0 ]]; then
    echo "`date` - backup failed "
else
    echo "`date` - backup completed (backup file is >>> ${BACKUP_FILE})"
fi
#==========================================================