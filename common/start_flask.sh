startFlask()
{
        echo "--------------------------------------------------------------"
        echo "Today is >>> `date`"
        echo "setting environment"
        . /opt/ansible/setenv_flask.sh "dev"
        if [[ -f ${FLASK_BIN_PATH}/${FLASK_MAIN_FILE} ]]; then
                echo "starting flask web services endpoint"
                nohup python ${FLASK_BIN_PATH}/${FLASK_MAIN_FILE} > ${FLASK_LOG}/flask_main.log 2> ${FLASK_LOG}/flask_main.err &
                retCode=$?
                if [[ ${retCode} -ne 0 ]]; then
                        echo "an error occured while submitting flask job in background, error code >> ${retCode} !!"
                        return -1
                fi
                echo "flask web services started in background with pid >> `ps -ef | grep -i "flask" | awk '{print $2}'`"
                echo "--------------------------------------------------------------"
        else
                echo "Flask file ${FLASK_BIN_PATH}/${FLASK_MAIN_FILE} is missing, aborting !!"
                echo "--------------------------------------------------------------"
        fi
}

echo "Starting ...."
startFlask
echo "Completed "
