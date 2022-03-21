#!/bin/bash

export PATH=$PATH:/usr/local/bin
echo "`date` - stopping restapi wsgi server ...."
PID_FILE="/opt/ansible/app/restapi/restapi.wsi.audit.pid"
if [[ -f $PID_FILE ]]; then
  for pid in `cat $PID_FILE`; do
    echo "`date` - stopping restapi gateway worker pid >>>  $pid"
    kill -9 $pid
  done
else
    echo "`date` - missing ${PID_FILE}..."
fi
echo "`date` - restapi gateway service stopped"

