#!/bin/bash
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Script: 		passless_auth.sh
# Description: 	Enable password less authentication by copying public key to target host for a given user
#				
# Usage: 		./passless_auth.sh <target_hosts_file> <user_id> <user_email_id>
#				For e.g. 
#				./passless_auth.sh ./all_hosts.csv u111111 john.smith@marsh.com
#
# History
#========================================================================================================
# When			Who			What
#========================================================================================================
# 03/01/2020	Anil Singh	Initial creation
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

main() {
	# generate public key
	#ssh-keygen -t rsa -b 4096 -C "anil.singh@marsh.com"
	ssh-keygen -t rsa -b 4096 -C "${USER_EMAIL}"

	# copy public key to target server

	while read -r target_host; do
		if [[ ! -z $target_host ]]; then
	        echo -e "copying public key to $target_host"
	        #sshpass -e ssh-copy-id ${USER_ID}@${target_host}
	        ssh-copy-id ${USER_ID}@${target_host}
	    fi
	done <${TARGET_HOST_FILE}
}

print_usage(){
	echo -e "usage: $(basename $(readlink -nf $0)) <target_host_file> <user_id> <user_email_id>"
	echo -e "for e.g.: $(basename $(readlink -nf $0)) target_host_files u1111111 john.smith@marsh.com"
}

if [[ $# -ne 3 ]]; then
	echo -e "missing mandatory arguments !!!"
	print_usage
	exit 1
fi

TARGET_HOST_FILE=$1
USER_ID=$2
USER_EMAIL=$3

if [[ -z $TARGET_HOST_FILE || -z $USER_ID || -z $USER_EMAIL ]]; then
	print_usage	
	exit 1
fi

echo -e "`date` - starting "
#read -p "Pls enter password for ${USER} : " -s SSHPASS # *MUST* be SSHPASS
#export SSHPASS

main
echo -e "`date` - completed "

OmSa1BabaNamah01
