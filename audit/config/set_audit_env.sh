export ENV=$1
export APP_NAME=AUDIT
export AUDIT_HOME=/opt/ansible/app/audit
export APP_CONFIG=${AUDIT_HOME}/config
export APP_LOG=${AUDIT_HOME}/log
if [[ ${ENV}=="dev" ]]; then
        export PYTHONPATH=/opt/ansible/app/source
elif [[ ${ENV}=="PROD" ]]; then
        export PYTHONPATH=/opt/ansible/app/bin
fi
export REGION="NAM"
export OPCO="MARSH"
export DC_LOCATION="Dallas"
export DOMAIN="CORP"

export GIT_PYTHON_REFRESH=quiet