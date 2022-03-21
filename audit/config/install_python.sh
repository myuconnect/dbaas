#!/bin/bash
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Script: 		install_python.sh
# Description: 	Install Python binary (version) and requird python modules on host. Python binary tar
#				file along with python modules must be present. This file must be run as "root"
#				
# Usag: 		./install_python.sh <Python_tar_file> <python_modules_tar_file> <staging_dir> <python_version
#				For e.g. 
#				./install_python.sh /tmp/staging/Python3.9.0.tar.gz /tmp/staging/python_modules.tar.gz \
#				 	/home/mongo/staging "3.9.0" 
#
# History
#================================================================================================================
# When			Who			What
#================================================================================================================
# 10/12/2020	Anil Singh	Initial creation
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

init(){
	#PYTARFILE="Python-3.9.0.tgz"
	#PYMODULETARFILE="python_modules.tar"
	REQUIRED_SPACE_MB=200
	#TEMPLOCATION="/tmp"
	# validatging if we got all files

	CURRENT_LOC=$PWD
	echo -e "-----------------------------------------------------------------------"
	# validating python ver and python
	printf "`date +%Y-%m-%d\ %H:%M:%S` - validating python ver/file  : "
	PYTHON_FILE=$(basename ${PYTARFILE})
	#echo -e 
	if [[ `echo ${PYTHON_FILE} | cut -c1-10` != "Python-`echo ${PYTHON_VER} | cut -c1-3`" ]]; then
		printf " - Invalid Python file ${PYTARFILE} for version ${PYTHON_VER}\n"
		exit 1
	fi
	printf " - Success \n"

	# validating location var
	printf "`date +%Y-%m-%d\ %H:%M:%S` - validating stg loc          : "
	#if [[ -z $STAGING_LOC ]]; then
	if [[ ! -d $STAGING_LOC ]]; then
		printf " - Error (staging location $STAGING_LOC does not exists ) \n"
		#echo -e  "Location variable is not set, exiting !!!"
		exit 1
	fi
	printf " - Success \n"

	# checking if all files are available
	printf "`date +%Y-%m-%d\ %H:%M:%S` - validating tar file(s)      : "
	if [[ ! -f ${PYTARFILE} ]]; then
		#echo -e  "file ${TEMPLOCATION}/${PYTARFILE} is missing !!!"
		printf " - Error (file ${PYTARFILE} is missing) \n"
		exit 1
	fi

	if [[ ! -f ${PYMODULETARFILE} ]]; then
		#echo -e  "file ${TEMPLOCATION}/${PYMODULETARFILE} is missing !!!"
		printf " - Error (file ${PYMODULETARFILE} is missing) \n"
		exit 1
	fi
	printf " - Success \n"	

	# validating space required, calculating space needed in /tmp
	printf "`date +%Y-%m-%d\ %H:%M:%S` - validating space            : "
	AVAIL_SPACE=`df ${STAGING_LOC} | awk 'NR>1 { print $4/(1024)}'`

	if [[ `echo $REQUIRED_SPACE_MB '<' $AVAIL_SPACE | bc -l` -eq 0 ]]; then
		#echo -e " - Error (required ${REQUIRED_SPACE_MB}, available space ${AVAIL_SPACE} )"
		printf " - Error (${STAGING_LOC} --> required ${REQUIRED_SPACE_MB}, available space ${AVAIL_SPACE} ) \n"
		exit 1
	fi
	printf " - Success \n"

	# validating current directory
	printf "`date +%Y-%m-%d\ %H:%M:%S` - validating current dir      : "
	CURRENT_LOC=$PWD
	cd ${STAGING_LOC}
	if [[ ${PWD} != ${STAGING_LOC} ]]; then
		#echo -e  "Current working directory '{PWD}' is not matching with location '${LOCATION}', exiting !!!"
		printf " - Error (current directory '{PWD}' is not matching with location '${STAGING_LOC}' ) \n"
		exit 1
	fi
	printf " - Success \n"
	echo -e "current location is >>> $PWD"
	
	echo -e "-----------------------------------------------------------------------"

	PYTHON_EXEC_FILE="/usr/local/bin/python`echo ${PYTHON_VER} | cut -c1-3`"
	
	return 0
}

extractTarFiles(){
	# we have all files, extracting it
	#echo -e "removing directory ${STAGING_LOC}/python_modules ${STAGING_LOC}/`echo $PYTHON_FILE | cut -c1-12`"
	#rm -fR ${STAGING_LOC}/python_modules ${STAGING_LOC}/`echo $PYTHON_FILE | cut -c1-12`
	printf "`date +%Y-%m-%d\ %H:%M:%S` -extracting tar file ${PYTARFILE} to $PWD  : "
	cd $STAGING_LOC
	tar -xvzf ${PYTARFILE} --overwrite
	if [[ $? != 0 ]]; then
		printf "error extracting file ${PYTARFILE} to $PWD \n"
		exit 1
	else
		printf "completed \n"
	fi	
	printf "`date +%Y-%m-%d\ %H:%M:%S` - extracting tar file ${PYMODULETARFILE} to $PWD  : "
	tar -xvzf ${PYMODULETARFILE} --overwrite
	if [[ $? != 0 ]]; then
		printf "error extracting file ${PYMODULETARFILE} to $PWD \n"
		exit 1
	else
		printf "completed \n"
	fi	
	echo -e "`date +%Y-%m-%d\ %H:%M:%S` - all files extracted... "
	echo -e "`date +%Y-%m-%d\ %H:%M:%S` - creating pymodules repo file "
	PYMODULE_FILE="${STAGING_LOC}/python_modules/pymodules.csv"
	
	# docker dependencies : websocket_Client, idna, chardet, oauth,certifi
	echo -e "setuptools_scm
toml
pycparser
py
six
wheel
distro
pyasn1
pbr
cffi
click
idna
chardet
oauthlib
certifi
urllib3
coverage
readline
exitstatus
requests
attrs
websocket_client
configparser
smmap
psutil
python-dateutil
gitdb
PyYAML
ldap3
GitPython
Cython
numpy
pytz
bz2file
pandas
cx_Oracle
psycopg2
pymongo
docker
" > ${PYMODULE_FILE}

	return 0
}

installPython(){
	echo -e "`date +%Y-%m-%d\ %H:%M:%S` - starting installation of required RPM for python"
	# installing development packages
	echo -e "`date +%Y-%m-%d\ %H:%M:%S` - installing required packages (development tools)..."
	#yum groupinstall "Development tools" -y 1> /dev/null
	yum groupinstall "Development tools" -y 1> /dev/null
	if [[ $? != 0 ]]; then
		echo -e "development tools installatino was unsuccessful, exiting ! "
		exit 1
	fi
	
	# installing packages
	packages="gcc xz-devel glibc bzip2-devel glibc-common gd gd-devel libffi-devel zlib-devel python-devel python3-devel redhat-rpm-config openssl-devel readline-devel sqlite-devel libffi-devel openldap openldap-devel"
	echo "`date +%Y-%m-%d\ %H:%M:%S` - installing required RPM packages ($packages)..."
	yum install $packages -y
	if [[ $? != 0 ]]; then
		echo -e "Either one or all [$packages] could not be installed, exiting !!! "
		exit 1
	else
		echo "`date +%Y-%m-%d\ %H:%M:%S` -    $packages is installed"
	fi
	#echo -e "`date +%Y-%m-%d\ %H:%M:%S` -    installing $packages ...." 

	#for pkg in $packages; do 

	#	echo -e "`date +%Y-%m-%d\ %H:%M:%S` -    checking package >>> ${pkg}" 
	#	result=echo "`rpm -qa | grep -i $pkg 1>/dev/null`" 
	#	echo -e "result >> ${result}" 

	#	if [[ -z ${result} ]]; then
			# package is not installed, installing
	#		echo -e "`date +%Y-%m-%d\ %H:%M:%S` -    package $pkg is not installed, installing"
	#    else
	#    	yum install $pkg -y
	#		if [[ $? != 0 ]]; then
	#			echo -e "an error $pkg could not be installed, exiting !!! "
	#  		else
	#    		echo "`date +%Y-%m-%d\ %H:%M:%S` -    package ${pkg} is installed"
	#    	fi
	#    fi
	#done

	# configuring python source code
	echo -e  "`date +%Y-%m-%d\ %H:%M:%S` -    configuring Python executables !!!"
	cd "${STAGING_LOC}/Python-${PYTHON_VER}"
	./configure --prefix=/usr/local --enable-optimizations --enable-loadable-sqlite-extensions --with-ensurepip=install --with-bz2=/usr/local/include

	if [[ $? != 0 ]]; then
		echo -e  "`date +%Y-%m-%d\ %H:%M:%S` -    configure python unsuccessful, exiting !!!"
		exit 1
	fi

	# make install
	echo -e  "`date +%Y-%m-%d\ %H:%M:%S` -    creating Python executables !!!"
	make altinstall
	if [[ $? -ne 0 ]]; then
		echo -e "`date +%Y-%m-%d\ %H:%M:%S` -    error, creating python executables !!! "
		exit 1
	fi
	echo -e  "`date +%Y-%m-%d\ %H:%M:%S` -    Python executables created !!!"

	#removing Python3.6.8 directory
	#rm -fR ${TEMPLOCATION}/${PYTARFILE}
	# installing Python modules

	cd ../
	return 0
}

installPyModules(){

	#extracting Python to temp file
	# changing to python modules directory
	PYTHONWARNINGS="ignore"
	cd ${STAGING_LOC}/python_modules
	if [[ $? -ne 0 ]]; then
		echo -e "can not change the directory to python_modules !!!"
		return 1
	fi
	echo -e "`date +%Y-%m-%d\ %H:%M:%S` - installing required python modules"
	echo -e "`date +%Y-%m-%d\ %H:%M:%S` -      extracting all pymodules files"

	# extracting all Python modules (tar and zip files)
	#for x in `ls *.tar.gz`; do
	# tar -xvf ${x}; done
	#echo -e "`date +%Y-%m-%d\ %H:%M:%S` -      extracting *.zip files ... "

	#for x in `ls *.zip`; do
	#  unzip ${x}
	#done

	for file in `ls` ; do
		echo -e "extracting file : $file"
		if [[ $file == *.tar.gz ]]; then
			tar -xvzf ${file} --overwrite 
			if [[ $? -ne 0 ]]; then
				echo -e "an error occurred while extracting tar file ${file}"
				return 1
			fi
		elif [[ $file == *.zip ]]; then
			unzip -o ${file} 
			if [[ $? -ne 0 ]]; then
				echo -e "an error occurred while extracting zip file ${file}"
				retun 1
			fi
		fi
	done

	#echo -e "`date +%Y-%m-%d\ %H:%M:%S` -      extracting *.zip files ... "
	
	# installing Python modules
	while read -r moduleDir; do
		printf "`date +%Y-%m-%d\ %H:%M:%S` -      installing ${moduleDir} "
		#curDir=${pwd}
		# checking if given directory exists along with setup.py in that directory
		cd ${moduleDir}* >/dev/null
		if [[ $? -ne 0 ]]; then
			echo -e "can not change directory to ${moduleDir}*, skiping !!!"
			#exit 1
		else
			if [[ -f setup.py ]]; then
				$PYTHON_EXEC_FILE setup.py install --quiet
				if [[ $? -ne 0 ]]; then
					printf " error \n"
					#exit 1
				else
					printf " completed \n"
				fi
			else
				printf " - error (setup.py is missing) \n"
			fi
		fi
		# changing it to previous directory
		cd ${STAGING_LOC}/python_modules
	done <${PYMODULE_FILE}
	allModules="setuptools
py
six
distro
websocket
wheel
pyasn1
pbr
cffi
click
idna
chardet
oauthlib
certifi
sqlite3
coverage
readline
exitstatus
requests
urllib3
configparser
smmap
psutil
dateutil
configparser
yaml
ldap3
gitdb
git
Cython
numpy
pytz
bz2
pandas
cx_Oracle
psycopg2
pymongo
docker"
	#echo -e "jira requires defusedxml, oauthlib, request-aouthlib, equests, setuptools, six, oauthlib, requests, cryptogramohy3.2, pyjwt "
	echo -e "validating python modules"
	for module in $allModules; do
		printf "$module    :"
		$PYTHON_EXEC_FILE -c "import $module" 
		if [[ $? -ne 0 ]]; then
			printf " not installed \n"
		else
			printf " installed \n"
		fi
	done
}

printUsage(){
	echo -e "$(basename $(readlink -nf $0)) <python_software_file_wpath> <python_module_file_wpath> <target_staging_dir> <python_ver>"
	echo -e "For e.g. $(basename $(readlink -nf $0)) \"/tmp/staging/Python-3.9.0.tgz\" \"/tmp/staging/python_modules.tar.gz\" \"/opt/mongo/staging\" \"3.9.0\""
}

main(){
	init
	retval=$?
	if [[ $retval -ne 0 ]]; then
		echo -e "error, exiting !!!"
		exit $retval	
	fi
	extractTarFiles
	retval=$?
	if [[ $retval -ne 0 ]]; then
		echo -e "error, exiting !!!"
		exit $retval	
	fi
	# installing Python
	# commenting below block to force the installation
	#if [[ -f  $PYTHON_EXEC_FILE ]]; then
	#	echo -e "Python version ${PYTHON_VER} is already installed, skipping !!!"
	#else
	
	installPython
	retval=$?
	if [[ $retval -ne 0 ]]; then
		echo -e "error, exiting !!!"
		exit $retval	
	fi
	#fi

	installPyModules
	retval=$?
	if [[ $retval -ne 0 ]]; then
		echo -e "error, exiting !!!"
		exit $retval	
	fi

	#commenting housekeeping
	#cd $CURRENT_LOC
	#echo -e "deleting Python tar file and Python module file"
	#rm -f ${PYTARFILE}
	#rm -f ${PYMODULETARFILE}
}
# Main starts here
# arguments <python_software_file_wpath> <python_modules_file_wpath> <target_staging_loc> <python_ver> <python_exec>
if [[ $# -ne 4 ]]; then
	echo -e "missing mandatory arguments "
	printUsage
	exit 1
fi
PYTARFILE=$1
PYMODULETARFILE=$2
STAGING_LOC=$3
PYTHON_VER=$4
#PYTHON_EXEC=$5
echo -e "got arguments...."
echo -e "PYTARFILE : $PYTARFILE"
echo -e "PYMODULETARFILE : $PYMODULETARFILE"
echo -e "STAGING_LOC : $STAGING_LOC"
echo -e "PYTHON_VER : $PYTHON_VER"
#echo -e "PYTHON_EXEC : $PYTHON_EXEC"

main
# check if an python module is installed for a host
# 	ssh u1167965@usdf23v0355.mrshmc.com "ls -altr /tmp/distro* && /usr/local/bin/python3.9 -c \"import distro\" && if [[ $? -eq 0 ]]; then echo \"installed\"; else; echo \"not installed\"; fi"
# ssh u1167965@${target} "cd /tmp && tar -xvf distro-1.5.0.tar.gz && cd /tmp/distro-1.5.0 && /usr/local/bin/python3.9 setup.py"

#wget https://www.python.org/ftp/python/3.9.0/Python-3.9.0.tgz

# another way to check dependency using easy_install
# cd tarsource dire && easy_install -z . / -N