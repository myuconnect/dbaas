#! /bin/sh
# downloading latest Python and its required modules
echo -e "do not user this file, this will download file in html format, you would need file in tar.gz format"
echo -e "Pls download at your local machine and transfer it to linux host"

if [[ -z $1 ]]; then
	echo -e "missing required arguments !! (usage: $(basename $(readlink -nf $0)) <target_loc> )"
	exit 1
fi

TARGET_LOC=$1
if [[ ! -d $TARGET_LOC ]]; then
	echo -e "'${TARGET_LOC}' does not exists !!"
	exit 1
fi
if [[ ! -d ${TARGET_LOC}/modules ]]; then
	mkdir -p ${TARGET_LOC}/modules
fi

echo -e "downloading Python "
wget https://www.python.org/ftp/python/3.9.0/Python-3.9.0.tgz --output-document=${TARGET_LOC}/Python-3.9.0.tgz

echo -e "`date +%Y-%m-%d\ %H:%M:%S` - downloading required Python modules ..."
TARGET_LOC="${TARGET_LOC}/modules"

wget https://pypi.org/project/setuptools/#files -O setuptools-50.3.2.zip --output-document=${TARGET_LOC}/setuptools-50.3.2.zip
wget https://pypi.org/project/cffi/#files -O cffi-1.14.3.tar.gz --output-document=${TARGET_LOC}/cffi-1.14.3.tar.gz
wget https://pypi.org/project/six/#files -O six-1.15.0.tar.gz --output-document=${TARGET_LOC}/six-1.15.0.tar.gz
wget https://pypi.org/project/smmap/#files -O smmap-3.0.4.tar.gz --output-document=${TARGET_LOC}/smmap-3.0.4.tar.gz
wget https://pypi.org/project/exitstatus/#files -O exitstatus-2.0.1.tar.gz --output-document=${TARGET_LOC}/exitstatus-2.0.1.tar.gz
wget https://pypi.org/project/click/ -O click-7.1.2.tar.gz --output-document=${TARGET_LOC}/click-7.1.2.tar.gz
wget https://pypi.org/project/pycparser/#files -O pycparser-2.20.tar.gz --output-document=${TARGET_LOC}/pycparser-2.20.tar.gz
wget https://pypi.org/project/psutil/#files -O psutil-5.7.3.tar.gz --output-document=${TARGET_LOC}/psutil-5.7.3.tar.gz 
wget https://pypi.org/project/pytest/#files -O pytest-6.1.2.tar.gz --output-document=${TARGET_LOC}/pytest-6.1.2.tar.gz
wget https://pypi.org/project/cryptography/#files -O cryptography-3.2.1.tar.gz --output-document=${TARGET_LOC}/cryptography-3.2.1.tar.gz 
wget https://pypi.org/project/configparser/#files -O configparser-5.0.1.tar.gz --output-document=${TARGET_LOC}/configparser-5.0.1.tar.gz
wget https://pypi.org/project/readline/#files -O readline-6.2.4.1.tar.gz --output-document=${TARGET_LOC}/readline-6.2.4.1.tar.gz
wget https://pypi.org/project/coverage/#files -O coverage-5.3.tar.gz --output-document=${TARGET_LOC}/coverage-5.3.tar.gz
wget https://pypi.org/project/pyasn1/#files -O pyasn1-0.4.8.tar.gz --output-document=${TARGET_LOC}/pyasn1-0.4.8.tar.gz
wget https://pypi.org/project/GitPython/#files -O GitPython-3.1.11.tar.gz --output-document=${TARGET_LOC}/GitPython-3.1.11.tar.gz
wget https://pypi.org/project/simple-crypt/#files -O simple-crypt-4.1.7.tar.gz --output-document=${TARGET_LOC}/simple-crypt-4.1.7.tar.gz
wget https://pypi.org/project/PyYAML/#files -O PyYAML-5.3.1.tar.gz --output-document=${TARGET_LOC}/PyYAML-5.3.1.tar.gz
wget https://pypi.org/project/ldap3/#files -O ldap3-2.8.1.tar.gz --output-document=${TARGET_LOC}/ldap3-2.8.1.tar.gz
wget https://github.com/mongodb/mongo-python-driver/archive/3.9.0b1.tar.gz --output-document=${TARGET_LOC}/pymongo-3.90b1.tar.gz
wget https://pypi.org/project/cx-Oracle/#files -O cx_Oracle-8.0.1.tar.gz --output-document=${TARGET_LOC}/cx_Oracle-8.0.1.tar.gz
wget https://pypi.org/project/psycopg2/#files -O psycopg2-2.8.6.tar.gz --output-document=${TARGET_LOC}/psycopg2-2.8.6.tar.gz
wget https://pypi.org/project/psymssql/#files -O pymssql-2.1.5.tar.gz --output-document=${TARGET_LOC}/pymssql-2.1.5.tar.gz
wget https://pypi.org/project/docker/#files -O docker-4.3.1.tar.gz --output-document=${TARGET_LOC}/docker-4.3.1.tar.gz
wget https://pypi.org/project/jira/#files -O jira-2.0.0.tar.gz  --output-document=${TARGET_LOC}/jira-2.0.0.tar.gz 

echo -e "`date +%Y-%m-%d\ %H:%M:%S` - completed"

