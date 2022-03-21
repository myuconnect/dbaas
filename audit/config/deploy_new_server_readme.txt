# Install Python
1. Copy python_software.tar to destination server (/tmp directory

a. extract this file to your local home folder
	tar -xvf /tmp/python_software.tar 
	OR 
	tar zxvf Python-3.8.6.tgz
b. change dir to Python-3.6.8

2. Extract Python software

tar -xvf /tmp/Python-3.6.8.tgz

3. Configure/Install Python (/usr/local dir)

	a. install required packages
		packages="gcc glibc glibc-common gd gd-devel libffi-devel zlib-devel python-devel python3-devel redhat-rpm-config openssl-devel"
		for pkg in $packages; do 
		  echo "checking package >>> $pkg" 
		  result=echo`rpm -qa | grep -i $pkg 1>/dev/null` 
		  echo "result >> $result" 
		  if [[ -z "$result" ]]; then
		    echo "package $pkg is not installed, isntalling"
		    if [[ $? != 0 ]]; then
		      echo "an error $pkg could not be installed, exiting !!!"
		  else
		    echo "package ${pkg} is installed"
		  fi
		done
		OR
		yum groupinstall "Development tools" -y

	b. Configure python
		cd Python-3.6.8
		./configure --prefix=/usr/local --enable-optimizations --with-ensurepip=install
		OR
		./configure --enable-optimizations --with-ensurepip=install

	c. sudo make altinstall

4. Install Python devel package

cd ~/software
sudo yum install gcc python-devel
sudo yum install gcc python3-devel
sudo yum install redhat-rpm-config gcc libffi-devel python-devel openssl-devel

# Install Modules
1. Extract dir (python source)

mkdir pymodules
cd pymodules
for x in `ls *.tar.gz`; do; tar -xvf ${x}; done
for x in `ls *.zip`; do; unzip ${x}; done

2. create a file pymodules_dir.csv with followin contents
setuptools-41.0.1/
pycparser-2.19/
six-1.12.0/
pyasn1-0.4.5/
cffi-1.12.3/
click-3.3/
coverage-4.5.3/
readline-6.2.4.1/
configparser-3.7.4/
PyYAML-5.1.1/
cx_Oracle-7.1.3/
exitstatus-1.3.0/
smmap2-2.0.5/
gitdb2-2.0.5/
GitPython-2.1.11/
ldap3-2.6/
psutil-5.6.3/
psycopg2-2.8.2/
py-dateutil-2.2/
PyGreSQL-5.1/
pymongo-3.8.0/
configparser-5.0.0/
docker-4.3.1.
jira-2.0.0/		???
#pytest-4.6.2/		???
#pytest-cov-2.7.1/	???

3. Execute following commands to install module or install it manually sudo /usr/local/bin/python3.6 setup.py install
help("modules") --> to list all python modules

while read -r line; do
	echo "processing ${line}"
	curDir=$(pwd)
	if [[ -d "./${line}" && -f "${line}/setup.py" ]]; then
		#[ -d ".${line}" ] && cd ${line} && [ -f "${line}/setup.py" ] && echo "installing" && `sudo /usr/local/bin/python3.6 setup.py install`
		cd ${line}
		echo "installing" 
		sudo /usr/local/bin/python3.6 setup.py install
	fi
	cd ${curDir}
done <pymodules_dir.csv

4. List all packages installed
	import pkg_resources
	installed_packages = pkg_resources.working_set
	installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])
	print(installed_packages_list)

#### Deploy app (common/db/audit) from ansible
# from Ansible server as ansible user

cd /opt/ansible/app
cp -p /opt/ansible/app/source/com/mmc/common/*.py /opt/ansible/app/audit/deploy/com/mmc/common/.
cp -p /opt/ansible/app/source/com/mmc/audit/*.py /opt/ansible/app/audit/deploy/com/mmc/audit/.
cp -p /opt/ansible/app/source/com/mmc/db/*.py /opt/ansible/app/audit/deploy/com/mmc/db/.

tar -cvzf com_audit.tgz com/

cd /opt/ansible/app

1. create relevant directory
	
export BASE_DIR="/opt/mongo"
mkdir -p ${BASE_DIR}/app/audit/conifg
mkdir -p ${BASE_DIR}/app/audit/log
mkdir -p ${BASE_DIR}/app/com/mmc/common
mkdir -p ${BASE_DIR}/app/com/mmc/db
mkdir -p ${BASE_DIR}/app/com/mmc/audit

2. Copy Common/db files to target folder

pycparser
six-1.12.0/
pyasn1-0.4.5/
cffi-1.12.3/
click-3.3/
coverage-4.5.3/
readline-6.2.4.1/
configparser-3.7.4/
PyYAML-5.1.1/
cx_Oracle-7.1.3/
exitstatus-1.3.0/
smmap2-2.0.5/
gitdb2-2.0.5/
GitPython-2.1.11/
jira-2.0.0/
ldap3-2.6/
psutil-5.6.3/
psycopg2-2.8.2/
py-dateutil-2.2/
PyGreSQL-5.1/
pymongo-3.8.0/
pytest-4.6.2/
pytest-cov-2.7.1/

1. Scp downloaded tar file
2. Extract to a directory
3. Configure/Install
	cd Python-x.x.x
	#./configure --prefix=/usr/local
	./configure --prefix=/usr/local --enable-optimizations
	#./configure --prefix=/opt/rh/rh-python36 --enable-optimizations
	#./configure --prefix=/usr/local --enable-shared --enable-optimizations LDFLAGS="-Wl,-rpath /usr/local/lib"	
	#make && make altinstall
	sudo make altinstall

	sudo yum install gcc python-devel
	sudo yum install redhat-rpm-config gcc libffi-devel python-devel openssl-devel
	
	sudo yum install rh-python36-runtime-2.0-1.el7.x86_64.rpm
	sudo yum install rh-python36-python-libs-3.6.3-1.el7.x86_64.rpm
	sudo yum install rh-python36-python-devel-3.6.3-3.el7.x86_64.rpm  --skip-broken

	python3.6 and pip3.6 is available
4. Install python development

	sudo yum install gcc python-devel
	sudo yum install redhat-rpm-config gcc libffi-devel python-devel openssl-devel
	sudo yum install rh-python36-runtime-2.0-1.el7.x86_64.rpm
	sudo yum install rh-python36-python-libs-3.6.3-1.el7.x86_64.rpm
	sudo yum install rh-python36-python-devel-3.6.3-3.el7.x86_64.rpm  --skip-broken

	# start by registering python2 as an alternative
	alternatives --install /usr/bin/python python /usr/bin/python2 50
	# register python3.5 as an alternative
	alternatives --install /usr/bin/python python /usr/bin/python3.5 60
	# Select the python to use
	alternatives --config python

5. Copy file rh-python36-python-devel-3.6.3-3.el7.x86_64.rpm 
   sudo yum install rh-python36-python-devel-3.6.3-3.el7.x86_64.rpm  --skip-broken

6. Download all modules and copy it to target server
	a. pydateutil --> needs "six" (named) module

	dependancies:
		https://pypi.org/six
		https://pypi.org/simple/WTForms/
		https://pypi.org/simple/pyasn1/
		https://pypi.org/simple/SQLAlchemy/
		https://pypi.org/simple/coverage/		
		https://pypi.org/simple/click
		https://pypi.org/simple/pyasn1
		simple/coverage
		readline
		jira
		git
		
6. extract all modules in a dir
	for x in `ls; do
	  tar -xvf ${x}
	done
7. change to it directory, run following command
for x in `ls -altr | grep drw | awk '{print $9}'`; do
	cd $x
	echo "installing $x"
	sudo /usr/local/bin/python3.6  ./setup.py install
	echo "$x installed"
	cd ..
done

	sudo /usr/local/bin/python3.6 setup.py install


py-dateutil -< needs six module
exit status - > done
psutil		-> done
configparser -> done
pymongo 	--> done
yaml 		--> done
cryptography --> https://pypi.org/simple/cffi/

pycparser

# Deploy
1. create directory on base

export BASE_DIR=/opt/mongo/software

mkdir -p ${BASE_DIR}/com/mmc/audit/source 
mkdir -p ${BASE_DIR}/com/mmc/audit/bin 
mkdir -p ${BASE_DIR}/com/mmc/audit/log 
mkdir -p ${BASE_DIR}/com/mmc/audit/config

mkdir -p ${BASE_DIR}/com/mmc/common/source 
mkdir -p ${BASE_DIR}/com/mmc/common/bin 
mkdir -p ${BASE_DIR}/com/mmc/common/log 
mkdir -p ${BASE_DIR}/com/mmc/common/config




import base64
data = "this is test"
data_encode = base64.b64encode(a.encode())
data_decode =  base64.b64decode(data_encode)