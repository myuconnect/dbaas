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
	"method" : "getDBEstateDecomData",
	"userId" : "",
	"apiKey" : "",
	"args" : {}
}
myResponse = post(myURL, headers=myHeaders, json=myArguments)
print(myResponse)
if myResponse.ok:
	if myResponse.json()["status"] == "UnSuccess":
		print(f"An error occurred while retrieving DBEstate decom data from repository >>> {myResponse.json()['message']} !!!")
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
		file.write("opco,dbTechnology,hostName,variant,tenatnId,dbType,dbVersion,clusterName,port,instanceType,decomDate,decomDoc,decomComments\n")
		for data_ in myRawData:
			print(f"processing data {data_}")
			myLineData = "".join([\
				f'{myEnclosedChar}', data_["opco"], \
				f'{myEnclosedChar}{mySep}{myEnclosedChar}', data_["dbTechnology"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["hostName"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["variant"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["tenantId"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["dbType"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["dbVersion"], \
				#f'{myEnclosedChar},{myEnclosedChar}', data_["memberStatus"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["clusterName"], \
				f'{myEnclosedChar},{myEnclosedChar}', str(data_["port"]), \
				f'{myEnclosedChar},{myEnclosedChar}', data_["instanceType"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["decomDate"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["decomDoc"], \
				f'{myEnclosedChar},{myEnclosedChar}', data_["decomComments"], \
				f'{myEnclosedChar}', "\n"])
			file.write(myLineData)
