if [ $# -eq 0 ]; then
	echo "usage: $0 <weeknum> <requestor name>"
	exit 1
fi

if [ -z $ENV ]; then
	echo "you must set environment by calling 'setenv_audit.sh <dev/prod>' before executing this process"
	exit 1
fi

weekNum=$1
requestor="${2}"
IFS=","
RUN_LOG_FILE=/opt/ansible/app/audit/log/manual_close_comp_${weekNum}_$(date -d"-0 days" +\%Y\%m\%d_\%H\%M\%S).log
ALL_MONGO_TENANTS="mongo.rs.LIS_PROD.ausy21v0050.28020,mongo.rs.LIS_PROD.ausy21v0049.28020,apac.marsh.aume22v0003.mrshmc.com,mongo.rs.rs_em_prem_prd01.gbbe21v0193.27020,mongo.rs.rs_em_prem_prd01.gbbe21v0194.27020,mongo.rs.rs_em_prem_prd01.gbbe21v0195.27020,mongo.rs.rs_em_prem_prd01.gbex22v0002.27020,mongo.rs.rs_em_prem_prd01.gbex22v0003.27020,mongo.rs.rep_prod01.usdf21v0126.27013,mongo.rs.rep_prod01.usdf21v0127.27013,mongo.rs.rep_prod01.usfkl22db10v.27013,mongo.rs.rep_prod01.usfkl22db10v.27013,mongo.rs.rep_prod01.usfkl21db130v.27013,mongo.rs.rep_prod01.gbbe21v0190.27013" 
#EMEA_TENANTS="mongo.rs.LIS_PROD.ausy21v0050.28020,mongo.rs.LIS_PROD.ausy21v0049.28020,apac.marsh.aume22v0003.mrshmc.com" 
#NAM_TENANTS="mongo.rs.LIS_PROD.ausy21v0050.28020,mongo.rs.LIS_PROD.ausy21v0049.28020,apac.marsh.aume22v0003.mrshmc.com" 

echo "auto closing compliance 'mongo_005/06/07/08/09/10' - APAC/EMEA/NAM region (Mongo)" > ${RUN_LOG_FILE}
for tenant in $ALL_MONGO_TENANTS; do
	python app/source/com/mmc/audit/scan_util.py ${requestor} "Weekly submision audit report completed" ${weekNum} "$tenant" "mongo_005" >> ${RUN_LOG_FILE}
	python app/source/com/mmc/audit/scan_util.py ${requestor} "Monthly review of admin user in Ops Manager completed" ${weekNum} "$tenant" "mongo_006" >> ${RUN_LOG_FILE}
	python app/source/com/mmc/audit/scan_util.py ${requestor} "Monthly backup review completed" ${weekNum} "$tenant" "mongo_007" >> ${RUN_LOG_FILE}
	python app/source/com/mmc/audit/scan_util.py ${requestor} "Monthly DR configuration review completed" ${weekNum} "$tenant" "mongo_008" >> ${RUN_LOG_FILE}
	python app/source/com/mmc/audit/scan_util.py ${requestor} "Monthly review of admin list completed" ${weekNum} "$tenant" "mongo_009" >> ${RUN_LOG_FILE}
	python app/source/com/mmc/audit/scan_util.py ${requestor} "Monthly database patching completed" ${weekNum} "$tenant" "mongo_010" >> ${RUN_LOG_FILE}
done

echo "auto closing task completed for week ${weekNum}" >> ${RUN_LOG_FILE}