from requests import post
import sys, os

if len(sys.argv) < 2:
	raise ValueError(f"usage: {sys.argv[0]} <output_csv_file_name> !!!")

myOutFile = sys.argv[1]
if os.path.dirname(myOutFile):
	if not os.path.isdir(os.path.dirname(myOutFile)):
		raise ValueError(f"Invalid file name directory {os.path.dirname(myOutFile)}!!!")

myHeaders = {'Content-Type': 'application/json'}
myURL = "http://usdfw21as383v:8000/api/audit/processRequest"
myArguments =  {
	"method" : "getDBEstateData",
	"userId" : "mgd\\U1195200_app",
	"apiKey" : "8SdgfrTAQ6qwiyu32--IuvJ8uWIkWbSb-j8lv6aGGcxEp5mAPNQHgg44l5zsTVxvVoh7RduYZMK2WhPvw",
	"args" : {}
}
myResponse = post(myURL, headers=myHeaders, json=myArguments)
print(myResponse)
if myResponse.ok:
	if myResponse.json()["status"] == "UnSuccess":
		print(f"An error occurred while retrieving DBEstate data from repository >>> {myResponse.json()['message']} !!!")
		sys.exit(-1)
	print(f"call was successful ...")
	myRawData = myResponse.json()["data"]
	if not myRawData:
		sys.exit(-1)
		print("no data found, exiting !!!")

	print(f"count >>> {len(myRawData)}")
	print(f"raw data >>> {len(myRawData)}")
	print("we got data proceeding ... ")
	myEnclosedChar = '"'
	mySep = ','
	#print(f"raw data >>> {myRawData}")
	with open(myOutFile, "w") as file:
		file.write("opco,dbTechnology,hostName,variant,tenatnId,dbType,dbVersion,memberStatus,clusterName,port,instanceType,databseRole,isClustered,patchCompliance,env,physMemory,totalCPUs,dbSizeMB,encAtRest,encTechnique,backupMethod,isExternalFacing,sslEnabled,databaseTier,auditCompliance,isDBaaS,dbaasVendor,lastChangeDate\n")
		for data_ in myRawData:
			print(f"processing data {data_}")
			myLineData = "".join([\
				f'{myEnclosedChar}', data_["opco"], \
				f'{myEnclosedChar}{mySep}{myEnclosedChar}', data_["dbTechnology"], \
				#f'{myEnclosedChar}{mySep}{myEnclosedChar}', data_["region"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["hostName"], \
				#f'{myEnclosedChar},{myEnclosedChar}', data_["ipAddress"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["variant"], \
				#f'{myEnclosedChar},{myEnclosedChar}', data_["dbId"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["tenantId"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["dbType"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["dbVersion"], \
				#f'{myEnclosedChar},{myEnclosedChar}', data_["tenantStatus"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["memberStatus"], \
				#f'{myEnclosedChar},{myEnclosedChar}', data_["tenantId"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["clusterName"], \
				#f'{myEnclosedChar},{myEnclosedChar}',data_["tenantStatus"], \
				#f'{myEnclosedChar},{myEnclosedChar}',data_["memberStatus"], \
				f'{myEnclosedChar},{myEnclosedChar}', str(data_["port"]), \
				#f'{myEnclosedChar},{myEnclosedChar}', data_["tenantName"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["instanceType"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["databaseRole"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["isClustered"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["patchCompliance"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["env"], \
				f'{myEnclosedChar},{myEnclosedChar}', str(data_["physMemory"]), \
				f'{myEnclosedChar},{myEnclosedChar}', str(data_["totalCPUs"]), \
				f'{myEnclosedChar},{myEnclosedChar}', str(data_["dbSizeMB"]), \
				#f'{myEnclosedChar},{myEnclosedChar}', data_["isEncAtRest"], \ this need to be retrieved from congfig (pending)
				f'{myEnclosedChar},{myEnclosedChar}', "YES", \
				f'{myEnclosedChar},{myEnclosedChar}', data_["encTechnique"], \
				#f'{myEnclosedChar},{myEnclosedChar}', data_["backupMethodology"], \ this need to be aligned with manually maintained backup technology (pending)
				f'{myEnclosedChar},{myEnclosedChar}', "opsMgr", \
				f'{myEnclosedChar},{myEnclosedChar}', data_["isExternalFacing"], \
				#f'{myEnclosedChar},{myEnclosedChar}', data_["isSSLEnabled"], \ this need to be retrieved from congfig (pending)
				f'{myEnclosedChar},{myEnclosedChar}', "NO", \
				f'{myEnclosedChar},{myEnclosedChar}', data_["databaseTier"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["auditCompliance"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["isDBaaS"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["dbaasVendor"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["lastChangeDate"], \
				f'{myEnclosedChar}', "\n"])
			file.write(myLineData)
