cp -p /opt/mongo/app/audit/config/audit.env /tmp/.
rm -fR /opt/mongo/app/
/tmp/deploy_audit.sh
cp -p /tmp/audit.env /opt/mongo/app/audit/config/
more /opt/mongo/app/audit/config/audit.env

#"__system","mms-automation","mms-monitor","mms-monitoring-agent","mms-automation-agent","mms-backup","mms-backup-agent"

# replace the .py files
rm -fR /opt/mongo/app/com
cd /opt/mongo/app
tar 