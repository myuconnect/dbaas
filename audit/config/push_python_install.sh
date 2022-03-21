#!/bin/bash
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Script: 		push_python_install.sh
# Description: 	Pushes pythong binary and python modules along with install_python.sh to destination
#				Pls do not forget to enable password less login for all target hosts of target user,
#				hint >> use passless_auth.sh to enable password less entry
#				Ensure latest python modules tar file is created
#					$ tar -cvzf python_modules.tar.gz python_modules
#
# Usage: 		./push_python_install.sh <target_hosts_file> <target_user_id>
#				For e.g. 
#				./push_python_install.sh ./all_hosts.csv u111111
#
# History
#========================================================================================================
# When			Who			What
#========================================================================================================
# 07/01/2020	Anil Singh	Initial creation
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

print_usage(){
	echo -e "usage: $(basename $(readlink -nf $0)) <target_host_file> <target_user>"
	echo -e "for e.g.: $(basename $(readlink -nf $0)) target_host_files u1111111"
}

main(){
	DEPLOY_FILES_INFO=deploy_files_info.csv
	echo "python_modules.tar.gz
	Python-3.9.0.tgz
	install_python.sh
	">${DEPLOY_FILES_INFO}

	# checking if all files are available to be pushed
	echo -e ""
	echo -e "checking files availability ..."
	echo "---------------------------------------"

	while read -r file; do
		printf "${file} .... "
		if [[ ! -z $file ]]; then
			if [[ ! -f $file ]]; then
				printf "  (missing) \n"
				echo -e "exiting !!!"
				exit 1
			else
				printf "  (present) \n"
			fi
		fi
	done <${DEPLOY_FILES_INFO}
	echo "---------------------------------------"
	echo -e ""
	echo -e "`date +%Y-%m-%d\ %H:%M:%S` - All files are present, pushing files to destination /tmp/staging..."
	#while read -r target; do
	for target in `cat ${DEPLOY_TAREGT_HOST_FILE}`; do
		# ignoring empty line
		[[ "$target" =~ ^[[:space:]]*# ]] && continue
		if [[ ! -z $target ]]; then
			echo "pushing deployment files to >>> ${target}"
			if [[ $? -ne 0 ]]; then
		        echo -e "skipping server ${target}, connection was unsuccessful"
		    else
				ssh -o ConnectTimeout=5 -q ${TARGET_USER}@${target} mkdir -p /tmp/staging
				scp -q -p $(cat ${DEPLOY_FILES_INFO}) ${TARGET_USER}@${target}:/tmp/staging/.
				if [[ $? -ne 0 ]]; then
					echo "an error occurred while copying files to target $target"
					echo -e "exiting !!!"
					exit 1
				fi
			fi
		fi
	#done <${DEPLOY_TAREGT_HOST_FILE}
	done

	echo -e "`date +%Y-%m-%d\ %H:%M:%S` - completed ..."

	echo -e "Pls use following command on all target hosts to deploy the files being pushed ..."
	echo -e ""
	echo -e "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
	echo -e "log into to target server, sudo to root and execute following command"
	echo -e "--------------------------------------------------------------------------------------------------------------------------------"
	echo -e "mkdir -p /home/mongo/staging # atleast 400mb free space is needed"
	echo -e "nohup /tmp/staging/install_python.sh \"/tmp/staging/Python-3.9.0.tgz\" \"/tmp/staging/python_modules.tar.gz\" \"/home/mongo/staging\" \"3.9.0\" >/tmp/staging/install_python.log & "
	echo -e ""
	echo -e "Once installation is compled (check for error in /tmp/staging/install_python), Pls execute following command to remove staging directory and staged files"
	echo -e "rm -fR  "
	echo -e "rm -f /tmp/staging/Python-3.9.0.tz /tmp/staging/python_modules.tar.gz /tmp/staging/install_python.sh "	
}

# main starts here
if [[ $# -ne 2 ]]; then
	echo -e "missing mandatory arguments !!!"
	print_usage
	exit 1
fi
DEPLOY_TAREGT_HOST_FILE=$1
TARGET_USER=$2

if [[ -z $DEPLOY_TAREGT_HOST_FILE || -z $TARGET_USER ]]; then
	print_usage	
	exit 1
fi

if [[ ! -f $DEPLOY_TAREGT_HOST_FILE ]]; then
	echo -e "Invalid host file (missing) !!!"
	exit 1
fi

main
MaaTujheSalam01

#/tmp/u1167965/deploy_audit.sh /tmp/u1167965/deploy_audit.tar.gz