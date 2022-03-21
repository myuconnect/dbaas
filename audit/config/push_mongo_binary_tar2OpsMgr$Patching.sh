#--------------------
#!/bin/bash
###########################################################
#AUTO PATCH UPLOAD TO OPS MANAGER SERVERS SCRIPT
#                               version : 2.0
#                               code written by :: Debasish Nayak
#                               For Testing purpose
# Use:          script.sh  <OPCO_REGION> <MONGOVERSION> <BTYPE>
# Arguments:  OPCO_REGION        - which ops manager you want to upload patch [ APAC / NAM_EMEA / AWS_PROD / AWS_STG / AWS_DEV ]
#             MONGOVERSION       - vesrion of mongo binary ( basically minor versions )
#             BTYPE              - Binary Type [ tgz or rpm ]
#--------------------
> /tmp/opsmanager_region_serverlist.txt
> /tmp/ops_managerURL.txt
> /tmp/downloaded_binary_files.txt
> /tmp/execution_logs.txt
> /tmp/Stepstofollow.txt
#--------------------
#####################################################
#COLOR CODING
#####################################################
pink="\x1b[35;49m"
red="\x1b[31;49m"
green="\x1b[32;49m"
cyan="\x1b[36;49m"
yellow="\x1b[33;49m"
white="\x1b[39;49;00m"
#####################################################
#======================================================================================
#-----------------------------------------------------
BINARYBASEPATH=/var/mongo/export/mongo_binaries
#====================================================
OPCO_REGION=$1
MONGOVERSION=$2
BTYPE=$3
TICKET_NO=$4
#====================================================
if [[ $# < 3 ]]
then
   echo -e "$white""===============================================================================""$white";
   echo -e "$red""script.sh  <OPCO_REGION> <MONGOVERSION> <BTYPE>""$white";
   echo -e "$white""===============================================================================""$white";
   exit 1
fi
#====================================================
if [[ -d "$BINARYBASEPATH" ]]
then
echo -e "$green""BINARY REPOSITORY FOLDER IS READY TO DOWNLOAD AND UPLOAD TO TARGET SERVERS""$white"
else
mkdir -p $BINARYBASEPATH
echo -e "$yellow""BINARY REPOSITORY FOLDER CREATED""$white"
fi
#====================================================
case "$OPCO_REGION" in
                "APAC")echo -e "$yellow""--------------SELECTED OPS MANAGER REGION IS APAC-------------""$white"
               echo "aume22v0001.mrshmc.com" >> /tmp/opsmanager_region_serverlist.txt
               echo "ausy21v0047.mrshmc.com" >> /tmp/opsmanager_region_serverlist.txt
               echo "ausy21v0048.mrshmc.com" >> /tmp/opsmanager_region_serverlist.txt
                           echo "http://ausy21v0047.mrshmc.com:8080" >> /tmp/ops_managerURL.txt
                       echo -e "$yellow""----------------------------------------------------------------""$white"
                           ;;
        "NAM_EMEA")echo -e "$yellow""-----------SELECTED OPS MANAGER REGION IS NAM_EMEA---------------""$white"
                           echo "usdf24v0098.mrshmc.com" >> /tmp/opsmanager_region_serverlist.txt
               echo "usdf24v0096.mrshmc.com" >> /tmp/opsmanager_region_serverlist.txt
               echo "usdf24v0097.mrshmc.com" >> /tmp/opsmanager_region_serverlist.txt
                           echo "http://usdf24v0098.mrshmc.com:8080" >> /tmp/ops_managerURL.txt
                           ;;
        "AWS_PROD")echo -e "$yellow""-----------SELECTED OPS MANAGER REGION IS AWS_PROD---------------""$white"
                           echo "ip-10-237-11-24.ec2.internal" >> /tmp/opsmanager_region_serverlist.txt
                           echo "ip-10-237-24-62.ec2.internal" >> /tmp/opsmanager_region_serverlist.txt
               echo "ip-10-237-40-29.ec2.internal" >> /tmp/opsmanager_region_serverlist.txt
                           echo "http://internal-mar-pd-lb08-2011873147.us-east-1.elb.amazonaws.com" >> /tmp/ops_managerURL.txt
                           ;;
    "AWS_STG")echo -e "$yellow""-----------SELECTED OPS MANAGER REGION IS AWS_STG---------------""$white"
              echo "ip-10-237-104-222.ec2.internal" >> /tmp/opsmanager_region_serverlist.txt
              echo "ip-10-237-72-193.ec2.internal" >> /tmp/opsmanager_region_serverlist.txt
              echo "ip-10-237-89-107.ec2.internal" >> /tmp/opsmanager_region_serverlist.txt
                          echo "http://internal-mar-sg-lb08-753894639.us-east-1.elb.amazonaws.com" >> /tmp/ops_managerURL.txt
                          ;;
    "AWS_DEV")echo -e "$yellow""-----------SELECTED OPS MANAGER REGION IS AWS_DEV---------------""$white"
              echo "ip-10-237-132-28.ec2.internal" >> /tmp/opsmanager_region_serverlist.txt
                          echo "http://10.237.132.28:8080" >> /tmp/ops_managerURL.txt
                          ;;
    "*")echo -e "$red""INVALID OPCO REGION NAME FOR OPS MANAGER,EXITING!!""$white"
        exit 1
        ;;
esac
#====================================================
#======================================================================================
#curl -OL https://downloads.mongodb.com/linux/mongodb-linux-x86_64-enterprise-rhel70-4.4.6.tgz
#$ echo `curl -o /dev/null --silent -Iw '%{http_code}' https://downloads.mongodb.com/linux/mongodb-linux-x86_64-enterprise-rhel70-4.4.6.tgz`
#200
#$ echo `curl -o /dev/null --silent -Iw '%{http_code}' https://downloads.mongodb.com/linux/mongodb-linux-x86_64-enterprise-rhel70-4.4.7.tgz`
#403
#======================================================================================
if [[ -n $MONGOVERSION && -n $BTYPE ]];
then
echo -e "$yellow""CHECKING MONGOVERSION AVAILABILITY IN MONGO SUPPORT . . . . .""$white";
else
echo -e "$red""~~~~~~~  Value missing for either mongoversion or Binary Type  ~~~~~~~""$white";
fi
#======================================================================================
patchvalidation()
{
AVALUE=`curl -o /dev/null --silent -Iw '%{http_code}' https://downloads.mongodb.com/linux/mongodb-linux-x86_64-enterprise-rhel70-"$MONGOVERSION".$BTYPE`
case "$AVALUE" in
     "200")echo -e "$green""MONGO BINARY WITH VERSION $MONGOVERSION IS AVAIABLE AT MONGO SUPPORT & READY TO DOWNLOAD)""$white"
           DOWNLOADLINK=https://downloads.mongodb.com/linux/mongodb-linux-x86_64-enterprise-rhel70-"$MONGOVERSION"."$BTYPE"
                   ;;
         "403")echo -e "$red""CHECK BINARY VESION,URL NOT WORKING . . . . .!!""$white"
           exit 1
                   ;;
       "*")echo -e "$red""UNABLE TO ACCESS BINARY URL .. Please crosscheck mongo version,exiting!!!""$white"
           exit 1
               ;;
esac
}
#===================================================
case "$BTYPE" in
                 "tgz")echo -e "$yellow""----------------------------------------------------------------""$white"
               patchvalidation
               cd $BINARYBASEPATH
               curl -OL $DOWNLOADLINK
               ls -ltr $BINARYBASEPATH/*$MONGOVERSION*.$BTYPE
               for i in `ls -ltr $BINARYBASEPATH/*$MONGOVERSION*.$BTYPE|awk '{print $9}'`;do chmod 777 $i;done
               ;;
                 "rpm")echo -e "$yellow""----------------------------------------------------------------""$white";
                           echo -e "$cyan"" RPM BINARY DOWNLOAD FUNCTION WILL BE ADDED SOON ""$white"
                           ;;
                 "*")echo -e "$red""Please provide information about Binary Type i.e. "tgz" or "rpm" to download . . .!!!""$white"
                         exit 1
                     ;;
esac
#==================================================
ls -ltr $BINARYBASEPATH/*$MONGOVERSION*.$BTYPE|awk '{print $9}' >> /tmp/downloaded_binary_files.txt
for FILENAME in `cat /tmp/downloaded_binary_files.txt`;
do
if [[ -f $FILENAME ]]
then
FILEAVAILABLE=1
AFILENAME=$FILENAME
echo -e "$green""FILE DOWNLOADED AND AVAIABLE :: $AFILENAME ""$white"
else
FILEAVAILABLE=0
echo -e "$red""UNABLE TO FIND THE FILE, PLEASE CHECK IF IT WAS DOWNLOADED OR NOT""$white"
fi
done
#=================================================
echo "FOR TESTING SHOWING AFILENAME VALUE :: $AFILENAME";
#=================================================
sftp_binaries_to_targets()
{
cd $BINARYBASEPATH
TARGET_SERVER=$1
sftp -q mongo@$TARGET_SERVER << EOF
cd /tmp
put $AFILENAME
ls -l *$MONGOVERSION*.$BTYPE
EOF
}
#=================================================
copyfilefrom_tmp_to_mongo_binarypath()
{
TARGET_SERVER=$1
TBPATH=$2
ssh -q mongo@$TARGET_SERVER << EOF
cp /tmp/*$MONGOVERSION*.$BTYPE $TBPATH;
hostname;ls -ltr $TBPATH/*$MONGOVERSION*.$BTYPE;

EOF
}
#=================================================
if [[ -n $OPCO_REGION ]];
then
COPYOPCO_REGION=$OPCO_REGION
else
echo -e "$red""Please provide valid OPCO_REGION, seems input value wrong { $OPCO_REGION }""$white"
fi
#=================================================
if [[ $COPYOPCO_REGION == "APAC" ]];
then
for i in `cat /tmp/opsmanager_region_serverlist.txt`;do sftp_binaries_to_targets $i;done;
for i in `cat /tmp/opsmanager_region_serverlist.txt`;do copyfilefrom_tmp_to_mongo_binarypath $i /opt/mongo/mms/mongodb-releases;done >> /tmp/execution_logs.txt 2>&1
else
for i in `cat /tmp/opsmanager_region_serverlist.txt`;do sftp_binaries_to_targets $i;done;
for i in `cat /tmp/opsmanager_region_serverlist.txt`;do copyfilefrom_tmp_to_mongo_binarypath $i /opt/mongo/software;done >> /tmp/execution_logs.txt 2>&1
fi
#=================================================
chmod 777 /tmp/execution_logs.txt
errorcount=`grep "No such file" /tmp/execution_logs.txt|wc -l`
if [[ $errorcount == 0 ]];
then
echo -e "$green""All above steps got completed,please visit Ops manager and proceed for following steps.""$white"
echo -e "$cyan""----------------------------------------------------------------------------------------------""$white"
cat /tmp/execution_logs.txt;
echo -e "$cyan""----------------------------------------------------------------------------------------------""$white"
echo -n "URL :: ";cat /tmp/ops_managerURL.txt
echo -e "$cyan""----------------------------------------------------------------------------------------------""$white"
echo "LOGIN TO OPS MANAGER URL >> NAVIGATE TO 'Admin' tab { you will see a new page } >>" >> /tmp/Stepstofollow.txt
echo "Click on 'General' tab >> Click on 'Version Manifest' { you will some information }" >> /tmp/Stepstofollow.txt
echo ">> Click on a sub tab 'Update MongoDB Version Manifest from MongoDB, Inc.' >> Excpected result 'Manifest successfully updated!" >> /tmp/Stepstofollow.txt
echo ">> IF it is not showing, please check if uploaded files are correct or not, else check file permission." >> /tmp/Stepstofollow.txt
cat /tmp/Stepstofollow.txt;
echo -e "$cyan""----------------------------------------------------------------------------------------------""$white"
else
echo -e "$red""Seems some error in exection of file copying,please crosscheck""$white"
cat /tmp/execution_logs.txt
fi
#==================================================
#==================================================
