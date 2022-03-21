from com.mmc.database.oracle_core import OracleCore
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.common.security import Security
from com.mmc.common.utility import Utility

if __name__ == "__main__":
	infra = Infrastructure()
	sec = Security()
	util = Utility()

	secToken = sec.authenticate("us02p01\\u1167965","QmFiYVNhaUNoYXJuYW0wMQ==")

	myEnvironment = util.getACopy(infra.environment)

	myNonProdDeployUser = myEnvironment["boot"]["deploy"]["oracle"]["non-prod"]["user"]
	myNonProdDeployEncPass = myEnvironment["boot"]["deploy"]["oracle"]["non-prod"]["userEncPass"]

	myProdDeployUser = myEnvironment["boot"]["deploy"]["oracle"]["prod"]["user"]
	myProdDeployEncPass = myEnvironment["boot"]["deploy"]["oracle"]["non-prod"]["userEncPass"]

	#myNonProdDeployPass = sec._Security__decryptText(myEnvironment["boot"]["deploy"]["oracle"]["non-prod"]["userEncPass"])
	#myProdDeployPass = sec._Security__decryptText(myEnvironment["boot"]["deploy"]["oracle"]["non-prod"]["userEncPass"])

	#myNonProdDeployEncPass = myEnvironment["boot"]["deploy"]["oracle"]["non-prod"]["userEncPass"]
	#myProdDeployEncPass = myEnvironment["boot"]["deploy"]["oracle"]["non-prod"]["userEncPass"]


	#repository connectivity (DBDOC)
	myTnsRepository = "(DESCRIPTION = (ADDRESS_LIST = (ADDRESS = (PROTOCOL = TCP)(HOST = usfkl21db98v.mrshmc.com)(PORT = 1521))) (CONNECT_DATA = (SERVICE_NAME = oltp55)))"
	# hardcoding dba_admin password, this need to be replaced with deploy_user and its enc pass once privilege is granted to select data in dbdocs
	myRepDeployAdmin = "dba_admin"
	myRepDeployAdminEncPass = "REJBOF9KdWxfMjAxOV9QYWNpZmlj"
	myRepoOraObj = OracleCore(secToken, myRepDeployAdmin, myRepDeployAdminEncPass, myTnsRepository)
	
	myAllDBTns = myRepoOraObj.getAllDBTns()
	myAllTermAdminLists = myRepoOraObj.getInActiveDBAList()
	print("Terminated admin lists >>>",myAllTermAdminLists)

	for admin in myAllTermAdminLists:
		
		print("processing >>> {user}".format(user = str(admin)))

		if admin["ENV"] == "PROD":
			myDeployEncPass = myProdDeployEncPass
		else:
			myDeployEncPass = myNonProdDeployEncPass

		# we need to find tns for this database
		myTnsList = [tns for tns in myAllDBTns if tns["DB_NAME"].lower() == admin["DB_NAME"].lower()]
		if len(myTnsList) > 1:
			print("more than one tns found for this database, skipping !!!")
			continue

		if not myTnsList:
			print("did not find tns for this database, skipping !!!")
			continue

		# we found tns for this user, instantiating ora conn object for this database
		myTargetTNS = myTnsList[0]["CONNECTION_INFO"]
		myTargetDB = OracleCore(myProdDeployUser, myProdDeployPass, myTargetTNS)

		# will check if user exists in this database 
		if not myTargetDB.isUserExists(secToken, user):
			print("user {user} not found using connection >>> {tns}".format(tns = myTargetTNS))
			continue

		try:
			if myTargetDB.isUserOwnAnyObjects(admin["USER_NAME"]):
				myOperation = "Lock User"
				print("user {user} has objects in its schema, performing operation >>> {op}".format(user = admin["USER_NAME"], op = myOperation))
				#myTargetDB.lockUser(admin["USER_NAME"])
				print("lock user was successful !")
			else:
				myOperation = "Drop User"
				print("user does not own any objects in its schema, performing operatrion >>> {op}".format(user = admin["USER_NAME"], op = myOperation))
				#myTargetDB.dropUser(admin["USER_NAME"])
				print("drop user was successful !")
		except Exception as error:
			print("an error occurred while performing operation >>> {op} !!!".format(op = myOperation))
