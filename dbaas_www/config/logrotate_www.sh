#/bin/bash
echo -e "`date` - restapi log files rotation started"
#kill -USR1 $(cat /opt/ansible/app/restapi/restapi.wsi.audit.pid)
/sbin/logrotate -vf /opt/ansible/app/restapi/logrotate_restapi.conf
echo -e "`date` - restapi log files rotation completed"

echo -e "`date` - performing restapi hosekeeping tasks"
echo -e "`date` -   listing log files older than a week"
find /opt/ansible/app/restapi/log -name "*.log" -type f -mtime +7 -exec ls -altr {} \;
echo -e "`date` -   deleting log files older than a week"
find /opt/ansible/app/restapi/log/ -name "*.log" -type f -mtime +7 -exec rm -f {} \;

echo -e "`date` - housekeeping tasks completed, exiting !!!"
