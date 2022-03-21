from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.security import Security
from com.mmc.common.infrastructure import Infrastructure

from com.mmc.audit.aud_globals import AuditGlobals
from com.mmc.audit.mongo_repo import Repository
#from com.mmc.audit.scan import Scan
from com.mmc.audit.audit_reports import Reports
from bson import json_util
import logging, logging.config, sys, traceback

# we need to add module name along with traceback during rasie error

class FactoryApi(object, metaclass=Singleton):
	def __init__(self, securityToken):

		try:
			self.sec = Security()
			self.util = Utility()
			self.infra = Infrastructure()

			self.SECURITY_TOKEN=securityToken
			self.ENVIRONMENT = self.util.getACopy(self.infra.environment)

			self.repo = Repository(securityToken)
			self.Globals = AuditGlobals(securityToken)
			self.reports = Reports(securityToken)

			self.LOGGER = logging.getLogger(__name__)

		except Exception as error:
			raise ValueError("an error occurred instantiating object Factory")

		#DbaasGgetAllApps

	def test(self, **kwargs):
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name
			myRequiredArgList = ['securityToken', 'test']

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			self.sec.validateSecToken(myKwArgs['securityToken'])

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myKwArgs['test'])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def authenticate(self, **kwargs):
		"""
		generate Security token for a given user name and api key or password
		"""
		try:
			#self.LOGGER.info('got arguments, >>> {args}'.format(args = str(kwargs)))

			myKwArgs = self.util.getACopy(kwargs)

			myModule = sys._getframe().f_code.co_name
			myRequiredArgList = ['userId', 'password']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			mySecurityToken = self.sec.authenticate(myKwArgs["userId"], myKwArgs["password"])

			#if myDBResult["status"] == self.Globals.success:
			return self.util.buildResponse(self.Globals.success, self.Globals.success,{"securityToken" : mySecurityToken})
			#else:
			#	return self.util.buildResponse(self.Globals.success, myDBResult["message"])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def genUSerAppKey(self, **kwargs):
		"""
		generate app key for a given userid
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name
			myRequiredArgList = ['userId', 'password']

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppKey = self.sec.authenticate(myKwArgs["userId"], myKwArgs["password"])

			myDBResult = repo.newUserAppKey(appKey, myKwArgs["userId"], myKwArgs["password"], myAppKey)

			if myDBResult["status"] == self.Globals.success:
				return self.util.buildResponse(self.Globals.success, self.Globals.success,{"appKey" : myAppKey})
			else:
				return self.util.buildResponse(self.Globals.success, myDBResult["message"])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def transmitScan(self, **kwargs):
		"""
		transmits scan log to repository
		arguments:
			scanLocation : optional, string, location of scan log which need to be transmitted
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			myModule = sys._getframe().f_code.co_name

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["scanDoc"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "scanDoc", "type" : dict, "value" : myKwArgs["scanDoc"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			#self.LOGGER.debug(f'retrieving all scan files from location >>> {myScanLocLocation}')

			#myAllScanFiles = self.util.getFilesByPattern(myScanLocLocation, self.Globals.SCAN_HOST_FILE.format(host = "*", dt = "*"))

			#transmitting all scan files found in SCAN_DIR

			#self.LOGGER.debug(f'total {len(myAllScanFiles)} scan files found, files >>> {myAllScanFiles} ')

			hostScanData = self.util.getACopy(myKwArgs["scanDoc"])

			if not hostScanData:
				raise ValueError("Host scan data is empty !!!")

			"""
			# commenting below code, moving this code to repo, will create new if not exists
			if 	self.repo.isHostScanExists(myKwArgs["securityToken"], hostScanData["_id"]):
				#return self.util.buildResponse(self.Globals.unsuccess, f"Scan id {hostScanData['_id']} already exists !!!")
				raise ValueError(f"Scan id {hostScanData['_id']} already exists !!!")
			"""
			try:
				# retrieving host details from inventory
				self.LOGGER.debug("retrieving host details from inventory")

				myHostInvenotryDetails = self.repo.getHostFromInvenory(myKwArgs["securityToken"], hostScanData["hostName"])

				if not myHostInvenotryDetails:
					raise ValueError(f"Host {hostScanData['hostName']} information is missing from inventory (hosts.inventory) !!!")

				self.LOGGER.debug("retrieving sys config data for all db technology")

				mySysConfigData = self.repo.getSysConfig(myKwArgs["securityToken"], myHostInvenotryDetails["opco"])

				if not mySysConfigData:
					raise ValueError(f"Can not retrieve sys config data for opco '{myHostInvenotryDetails['opco']}'")

				myExcludeFSList = mySysConfigData["globalSettings"]["excludeFSStatsLinux"]

				#self.LOGGER.debug(f"exclude FS list >> {myExcludeFSList}")
				#building host scan data
				# building tenants summary which would be kept along with host data

				myHostTenants = []

				for tenant in hostScanData["tenants"]:
					#self.LOGGER.info(f"processing tenant >> {tenant}")
					# checking if scanning this tenant was successful
					if tenant["scanStatus"] == self.Globals.unsuccess:
						# we could not successfully scanned this tenant either due to invalid URI/password
						continue

					if "rsDetails" in tenant and tenant["rsDetails"]:
						myTenantName = self.repo.buildMongoTenant(\
							myKwArgs["securityToken"], myHostInvenotryDetails["opco"], myHostInvenotryDetails["region"], myHostInvenotryDetails["dcLocation"], myHostInvenotryDetails["env"], \
							hostScanData["hostName"], tenant["tenantPort"], tenant["rsDetails"])
					else:
						# this is mongo database standalone
						myTenantName = self.repo.buildMongoTenant(\
							myKwArgs["securityToken"], myHostInvenotryDetails["opco"], myHostInvenotryDetails["region"], myHostInvenotryDetails["dcLocation"], myHostInvenotryDetails["env"], \
							hostScanData["hostName"], tenant["tenantPort"])

					self.LOGGER.debug(f"tenant name {myTenantName} is found for tenant {tenant['tenantId']}")

					tenant.update({"tenantName" : myTenantName})

					myTenant = {
						"dbTechnology" : tenant["dbTechnology"],
						"tenantName" : tenant["tenantName"],
						"dbCluster" : tenant["dbCluster"],
						"tenantId" : tenant["tenantId"],
						"tenantPort" : tenant["tenantPort"],
						"env" : myHostInvenotryDetails["env"],
						"docker" : tenant["docker"],
						"configFile" : tenant["configFile"],
						"startedAt" : self.util.convStr2DateViaParser(tenant["startedAt"]) if isinstance(tenant["startedAt"],str) else tenant["startedAt"],
						"pid" : tenant["startedAt"],
						"osUser" : tenant["osUserDetails"],
						"members" : tenant["rsConfig"]["members"] if "rsConfig" in tenant and "members" in tenant["rsConfig"] else []
					}

					if tenant["docker"] == True and "dockerConfig" in tenant:
						myTenant.update({
							"dockerConfig" : tenant["dockerConfig"]
						})


					# tenant type ...
					# 	For mongo : mongo.rs, mongo.standalone
					#	For Postgres: postgres.standalone, postgres.replication
					if tenant["dbTechnology"] == self.Globals.DB_TYPE_MONGO:
						myTenantVersion = tenant["tenantVersion"]
						myTenantBits = tenant["dbBuildInfo"]["bits"]
					else:
						myTenantVersion = "".join(["N/A for ", tenant["dbTechnology"]])
						myTenantBits = "".join(["N/A for  ", tenant["dbTechnology"]])

					myTenant.update({"tenantVersion" : myTenantVersion})
					myTenant.update({"tenantBits" : myTenantBits})

					myHostTenants.append(myTenant)

					# we need all summary for tenant {"mongo" :2, "postgres" : 1}

				"""
				# this is being done in scan.py
				myTenantsSummary = {
					"total" : len(hostScanData["tenants"])
				}
				

				myMongoDockerTenants = [tenant["tenantName"] for tenant in hostScanData["tenants"] if tenant["dbTechnology"] == self.Globals.DB_TYPE_MONGO]
				myMongoNonDockerTenants = [tenant["tenantName"] for tenant in hostScanData["tenants"] if tenant["dbTechnology"] == self.Globals.DB_TYPE_MONGO]
				myPGDockerTenants = [tenant["tenantName"] for tenant in hostScanData["tenants"] if tenant["dbTechnology"] == self.Globals.DB_TYPE_POSTGRES]
				myPGNonDokcerTenants = [tenant["tenantName"] for tenant in hostScanData["tenants"] if tenant["dbTechnology"] == self.Globals.DB_TYPE_POSTGRES]
				myOracleTenants = [tenant["tenantName"] for tenant in hostScanData["tenants"] if tenant["dbTechnology"] == self.Globals.DB_TYPE_ORACLE]
				mySqlServerTenants = [tenant["tenantName"] for tenant in hostScanData["tenants"] if tenant["dbTechnology"] == self.Globals.DB_TYPE_SQLSERVER]
				myMySqlTenants = [tenant["tenantName"] for tenant in hostScanData["tenants"] if tenant["dbTechnology"] == self.Globals.DB_TYPE_MYSQL]
				myTeradataTenants = [tenant["tenantName"] for tenant in hostScanData["tenants"] if tenant["dbTechnology"] == self.Globals.DB_TYPE_TERADATA]

				if myMongoTenants:
					myTenantsSummary.update({self.Globals.DB_TYPE_MONGO : len(myMongoTenants)})
				if myPGTenants:
					myTenantsSummary.update({self.Globals.DB_TYPE_POSTGRES : len(myPGTenants)})
				if myOracleTenants:
					myTenantsSummary.update({self.Globals.DB_TYPE_ORACLE : len(myOracleTenants)})
				if mySqlServerTenants:
					myTenantsSummary.update({self.Globals.DB_TYPE_SQLSERVER : len(mySqlServerTenants)})
				if myMySqlTenants:
					myTenantsSummary.update({self.Globals.DB_TYPE_MYSQL : len(myMySqlTenants)})
				if myTeradataTenants:
					myTenantsSummary.update({self.Globals.DB_TYPE_TERADATA : len(myTeradataTenants)})
				"""
				# tenants summary is built, building host scan data
				myHostId = self.util.buildHostId(hostScanData["hostName"].lower(), myHostInvenotryDetails["region"], myHostInvenotryDetails["opco"]).lower()

				hostScanDoc = {
					"_id" : hostScanData["_id"],
					"hostId" : myHostId,
					"hostName" : hostScanData["hostName"].lower(),
					"env" : myHostInvenotryDetails["env"].lower(),
					"opco" : myHostInvenotryDetails["opco"].upper(),
					"region" : myHostInvenotryDetails["region"].upper(),
					"dcLocation" : myHostInvenotryDetails["dcLocation"].upper(),
					"domain" : myHostInvenotryDetails["domain"].upper(),
					"ipAddress": hostScanData["ipAddress"],
					"ipv6Address": hostScanData["ipv6Address"],
					"scanId" : hostScanData["_id"],
					"scanDate" : hostScanData["scanDate"],
					"scanStartTS" : hostScanData["scanStartTS"],
					"bootTime" : hostScanData["hostScan"]["bootTime"],
					"os" : hostScanData["hostScan"]["os"],
					"connections" : hostScanData["hostScan"]["connections"],
					"dbOSUsers" : hostScanData["hostScan"]["dbOSUsers"],
					"cpu" : hostScanData["hostScan"]["cpu"],
					"memory" : hostScanData["hostScan"]["memory"],
					"swap" : hostScanData["hostScan"]["swap"],
					"nicDetails" : hostScanData["hostScan"]["nicDetails"],
					"fs" : hostScanData["hostScan"]["fs"],
					"fsStats" : hostScanData["hostScan"]["fsStats"],
					"sensors" : hostScanData["hostScan"]["sensors"],
					"tenants" : myHostTenants,
					"tenantsSummary" : hostScanData["tenantsSummary"]
				}

				# saving host scan
				self.LOGGER.debug('saving host scan data ')

				myDBResult = self.repo.saveHostScan(myKwArgs["securityToken"], hostScanDoc)
				
				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError(f"An error [{myDBResult['message']} occurred while saving host {hostScanDoc['hostId']} scan, traceback >>> {traceback.format_exc()} !!!")

				self.LOGGER.info("host scan saved, result >> {result}".format(result = str(myDBResult)))

			except Exception as error:
				self.LOGGER.error(f"an error occurred while saving host scan data in factory >>> {error}")
				raise ValueError(f"an error occurred while saving host scan data in factory >>> {error}, traceback >>> {traceback.format_exc()} !!!")

			# building data for statistics
			myFSStats = [fs for fs in hostScanDoc["fs"] if fs["mountPoint"] not in myExcludeFSList]

			#self.LOGGER.debug(f"fs stats prepared for statistics >>> {myFSStats}")

			#if myFSStats:
			#	myFSStats = myFSStats[0]

			self.LOGGER.debug(f"fs stats >>> {myFSStats}")

			myHostStorageList = [fs["used"] for fs in myFSStats]

			myHostStorage = sum(myHostStorageList)

			myStorageStats = {
				"scanId" : hostScanData["_id"],
				"scanDate" : hostScanData["scanDate"],
				"statsType" : self.Globals.STATS_STORAGE,
				"opco" : myHostInvenotryDetails["opco"].upper(),
				"hostName" : hostScanData["hostName"].lower(),
				"fsStats" : myFSStats,
				"totalFSUsedMB" : myHostStorage/(1024*1024),
				"tenants" : []
			}

			# processing host tenant scan
			self.LOGGER.info(f"total tenants to be processed {len(hostScanData['tenants'])}")
			for tenant in hostScanData["tenants"]:
				self.LOGGER.info(f"processing tenant {tenant['tenantId']}")
				try:
					# updating host attribute to tenants
					tenant.update({
						"opco" : myHostInvenotryDetails["opco"].upper(),
						"region" : myHostInvenotryDetails["region"].upper(),
						"env" : myHostInvenotryDetails["env"].lower(),
						"hostId" : myHostId,
						"scanId" : hostScanData["_id"]
					})

					if tenant["dbTechnology"] == self.Globals.DB_TYPE_MONGO:
						# processing Mongo tenant
						if tenant["scanStatus"] == self.Globals.unsuccess:
							self.LOGGER.debug(f"found tenant scan which was unsuccessful, skipping !!! {tenant}")
							continue

						myDBResult = self.repo.saveMongoTenantScan(myKwArgs["securityToken"], tenant)

						self.LOGGER.info("Mongo tenant scan save db result >> {result}".format(result = str(myDBResult)))
						
						if myDBResult["status"] == self.Globals.unsuccess:
							raise ValueError(f"An error [{myDBResult['message']} occurred while saving tenant {tenant['tenantId']} scan data !!!")

						# updating tenant name, need this for processing statistics
						myTenantMemberData = self.repo.getTenantMemberDetails(myKwArgs["securityToken"], tenant["tenantId"])

						if myTenantMemberData:
							tenant.update({"tenantName" : myTenantMemberData["tenantName"]})

						# processing stats
						# 1. Storage
						#self.LOGGER.debug(f"db details >>> {tenant['dbDetails']}")
						allDBs = [{"db" : db["name"], "size" : db["sizeOnDisk"]} for db in tenant["dbDetails"]["dbs"]]
						myTenantDBSize = sum(db['size'] for db in allDBs)
						myStorageStats["tenants"].append({
							"tenantName" : tenant["tenantName"],
							"dbSizeMB" : myTenantDBSize/(1024*1024),
							"dbs" : allDBs
						})
						
						myDBResult = self.repo.saveStats(myKwArgs["securityToken"], myStorageStats)

						if myDBResult["status"] == self.Globals.unsuccess:
							raise ValueError(f"An error <{myDBResult['message']}> occurred while saving storage stats !!!")

						# updating tenant compliance
						self.LOGGER.info("updating tenant compliance for {tenant}")
						
						self.repo.updateTenantCompliances(myKwArgs["securityToken"], myTenantMemberData["tenantName"])

					if tenant["dbTechnology"] == self.Globals.DB_TYPE_POSTGRES:
						pass
						# processing Postgres tenant

				except Exception as error:
					self.LOGGER.error(error, exc_info = True)
					raise ValueError(f"An error occurred while processing Mongo host tenant {tenant['tenantName']} scan in factory >> {error} ")

			# completed processing all tenants in this scan, returing results
			#if "myDBResult" in locals():
			#	return self.util.buildResponse(self.Globals.success, self.Globals.success)
			#else:

			return self.util.buildResponse(self.Globals.success, self.Globals.success)

			
			#return self.util.buildResponse(self.Globals.success, self.Globals.success)

		except Exception as error:
			myErrorMsg = f'An error occurred while transmit scan in factory call >>> {error}, traceback >>> {traceback.format_exc()}'
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)
		finally:
			if "hostScanData" in locals():
				del hostScanData

	def transmitAudit(self, **kwargs):
		"""
		transmits audit to repository
		arguments:
			securityToken
			auditData
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["scanDoc"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "scanDoc", "type" : dict, "value" : myKwArgs["scanDoc"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			if myKwArgs["scanDoc"]["dbTechnology"] not in self.Globals.DB_TYPE_ALL:
				raise ValueError(f"Invalid db type {myKwArgs['dbTechnology']} !!!")

			if not myKwArgs["scanDoc"]["dbTechnology"] in [self.Globals.DB_TYPE_MONGO]:
				raise ValueError(f"Audit processing for {myKwArgs['dbTechnology']} is not yet implemented !!!")


			if not isinstance(myKwArgs["scanDoc"]["auditData"], list) or not isinstance(myKwArgs["scanDoc"]["auditData"], dict):
				myAuditData = self.util.convStrToDict(myKwArgs["scanDoc"]["auditData"])
			else:
				myAuditData = self.util.getACopy(myKwArgs["scanDoc"]["auditData"])

			self.LOGGER.debug("all validation passed, proceeding")

			# retrieving host attributes from inventory for this host
			myHostInvenotryDetails = self.repo.getHostFromInvenory(myKwArgs["securityToken"], myKwArgs["scanDoc"]["hostName"])

			if not myHostInvenotryDetails:
				raise ValueError(f"an error occurred while retrieving host {myKwArgs['scanDoc']['hostName']} details from inventory !!!")

			if not(isinstance(myAuditData, list)):
				myAuditData = [myAuditData]

			# updating opco, region, dcLocation, env to audit data
			myHostId = self.util.buildHostId(myKwArgs["scanDoc"]["hostName"].lower(), myHostInvenotryDetails["region"], myHostInvenotryDetails["opco"]).lower()
			
			for aud_ in myAuditData:
				aud_.update({
					"opco" : myHostInvenotryDetails["opco"],
					"region" : myHostInvenotryDetails["region"],
					"env" : myHostInvenotryDetails["env"],
					"dcLocation" : myHostInvenotryDetails["dcLocation"],
					"hostId" : myHostId
				})

			myDBResult = self.repo.saveAuditData(myKwArgs["securityToken"], myHostInvenotryDetails["opco"], myKwArgs["scanDoc"]["dbTechnology"], myAuditData)
			
			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"An error [{myDBResult['message']} occurred while saving audit data for scanId {myKwArgs['scanDoc']['tenantName']}.{myKwArgs['scanDoc']['hostName']} !!!")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, repr(myDBResult["data"]))

		except Exception as error:
			myErrorMsg = f'An error occurred while processing tenant audit scan in factory call >>> {error}, traceback >>> {traceback.format_exc()}'
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)
		finally:
			if "myAuditData" in locals():
				del myAuditData

	def transmitSummary(self, **kwargs):
		"""
		saves transmit summary
		arguments:
			securityToken
			scanSummaryDoc
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["scanSummaryDoc"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, ["scanSummaryDoc"])

			myArgValidationList = [
				{"arg" : "scanSummaryDoc", "type" : dict, "value" : myKwArgs["scanSummaryDoc"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.saveHostScanSummary with args {myKwArgs}")

			myDBResult = self.repo.saveHostScanSummary(myKwArgs["securityToken"], myKwArgs["scanSummaryDoc"])
			
			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"An error [{myDBResult['message']} occurred while saving scan summary !!!")

			return self.util.buildResponse(self.Globals.success, self.Globals.success, repr(myDBResult["data"]))

		except Exception as error:
			myErrorMsg = f'An error occurred while transmiting scan summary in factory call >>> {error}, traceback >>> {traceback.format_exc()}'
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAppDetaisByName(self, **kwargs):
		"""
		creates a new app or add env for an existing app in repository
		arguments:
			securityToken
			opco
			region
			env
			dbTechnology
			appName
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["opco","region","env","dbTechnology","appName","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				#{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "appName", "type" : str, "value" : myKwArgs["appName"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			# retrieving db host, port and uri details, we need tenant name and rs/cluster name 2 diff field
			# tenant name is uniquely identification of tenant and cluster name should match with replica set used in db
			# or host:port if no rs is defined in standalone db or on postGres

			myDBResult = self.repo.getAppDetailsByName(myKwArgs["securityToken"], \
				myKwArgs["opco"].upper(), myKwArgs["dbTechnology"].lower(), \
				myKwArgs["appName"], myKwArgs["env"].lower())

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"An error [{myDBResult['message']} occurred while retrieving applicaition details {myKwArgs['appName']} {myKwArgs['env']} !!!")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAppDetaisByID(self, **kwargs):
		"""
		creates a new app or add env for an existing app in repository
		arguments:
			securityToken
			appId
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["appId","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "appId", "type" : str, "value" : myKwArgs["appId"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			# retrieving db host, port and uri details, we need tenant name and rs/cluster name 2 diff field
			# tenant name is uniquely identification of tenant and cluster name should match with replica set used in db
			# or host:port if no rs is defined in standalone db or on postGres

			myDBResult = self.repo.getAppDetailsByID(myKwArgs["securityToken"], myKwArgs["appId"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"An error [{myDBResult['message']} occurred while retrieving applicaition details {myKwArgs['appName']} {myKwArgs['env']} !!!")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def onboardNewAppEnv(self, **kwargs):
		"""
		creates a new app or add env for an existing app in repository
		arguments:
			securityToken
			opco
			region
			env
			dbTechnology
			appName
			lob
			dbName
			notificationDl
			appOwnerDl
			busOwnerDL
			supportDL
			host
			port
			uri : Connect string
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = [
				"securityToken","opco","env","dbTechnology","tenantName","dbName",
				"appName","lob","appOwnerDL","appOwnerAdGrp","busOwnerDL",
				"envOwnerDL","envOwnerAdGrp","readOnlyAdGrp","readWriteAdGrp","serviceAccount","userId"
			]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, ["storageRequirement"])

			myArgValidationList = [
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]},
				{"arg" : "dbName", "type" : str, "value" : myKwArgs["dbName"]},
				{"arg" : "appName", "type" : str, "value" : myKwArgs["appName"]},
				{"arg" : "lob", "type" : str, "value" : myKwArgs["lob"]},
				{"arg" : "appOwnerDL", "type" : str, "value" : myKwArgs["appOwnerDL"]},
				{"arg" : "appOwnerAdGrp", "type" : str, "value" : myKwArgs["appOwnerAdGrp"]},
				{"arg" : "busOwnerDL", "type" : str, "value" : myKwArgs["busOwnerDL"]},
				{"arg" : "envOwnerDL", "type" : str, "value" : myKwArgs["envOwnerDL"]},
				{"arg" : "envOwnerAdGrp", "type" : str, "value" : myKwArgs["envOwnerAdGrp"]},
				{"arg" : "readOnlyAdGrp", "type" : str, "value" : myKwArgs["readOnlyAdGrp"]},
				{"arg" : "readWriteAdGrp", "type" : str, "value" : myKwArgs["readWriteAdGrp"]},				
				{"arg" : "serviceAccount", "type" : str, "value" : myKwArgs["serviceAccount"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, ["storageRequirement"])

			# retrieving db host, port and uri details, we need tenant name and rs/cluster name 2 diff field
			# tenant name is uniquely identification of tenant and cluster name should match with replica set used in db
			# or host:port if no rs is defined in standalone db or on postGres

			#myHostPort = "".join([myKwArgs["host"], ":", str(myKwArgs["port"])])
			#def createNewApp(self, securityToken, opco, region, env, dbTechnology, appName, lob, dbName, notificationDL, storageRequirement, hostPort, requestedBy)
			self.LOGGER.info(f"executing repo.onboardNewApp with arguments {myKwArgs}")

			myDBResult = self.repo.onboardAppEnv(**myKwArgs)

			self.LOGGER.debug("db result >> {myDBResult}")

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"An error [{myDBResult['message']} occurred while onboarding new applicaition env with arguments >>> {myKwArgs}!!!")
			
			return myDBResult

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def newApplication(self, **kwargs):
		"""
		Create a new application

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string)
			:param arg2: opco (string)
			:param arg3: dbTechnology (string)
			:param arg7: appName (string)
			:param arg8: lob (string)
			:param arg9: appOwnerDL (string)
			:param arg9: appOwnerAdGrp (string)
			:param arg10: busOwnerDL (string)
			:param arg15: userId (string) 
			:return: json
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				newApplication(**args)

		.. note::
			

		.. warning:: 


		.. seealso:: 


		"""		

		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug(f"got arguments >>> {kwargs}")

			myKwArgs = self.util.getACopy(kwargs)

			# validating securityToken
			self.sec.validateSecToken(myKwArgs["securityToken"])

			myRequiredArgList = ["securityToken","opco","appName","lob","dbTechnology","appOwnerDL","appOwnerAdGrp","busOwnerDL","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "appName", "type" : str, "value" : myKwArgs["appName"]},
				{"arg" : "lob", "type" : str, "value" : myKwArgs["lob"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "appOwnerDL", "type" : str, "value" : myKwArgs["appOwnerDL"]},
				{"arg" : "appOwnerAdGrp", "type" : str, "value" : myKwArgs["appOwnerAdGrp"]},
				{"arg" : "busOwnerDL", "type" : str, "value" : myKwArgs["busOwnerDL"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.newApplication with argument >> {myKwArgs}")

			myDBResult = self.repo.newApplication(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				return self.util.buildResponse(self.Globals.unsuccess, f"An error [{myDBResult['message']} occurred while creating new applicaition for >>> {myKwArgs}!!!")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success)

		except Exception as error:
			myErrorMsg = f'an error occurred >>> {error}'
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def addNewAppEnv(self, **kwargs):
		"""
		Add new environment 

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string)
			:param arg2: appId (string)
			:param arg3: env (string)
			:param arg4: tenantName (string)
			:param arg5: dbName (string)
			:param arg6: envOwnerDL (string)
			:param arg7: envOwnerAdGrp (string)
			:param arg8: serviceAccount (string)
			:param arg9: userId (string) 
			:return: json
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				addNewAppEnv(securityToken, appID, env, tenantName, dbName, envOwnerDL, envOwnerAdGrp, serviceAccount, userId)

		.. note::
			

		.. warning:: 


		.. seealso:: 


		"""		

		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug(f"got arguments >>> {kwargs}")

			myKwArgs = self.util.getACopy(kwargs)

			myKwArgs = self.util.getACopy(kwargs)

			# validating securityToken
			self.sec.validateSecToken(myKwArgs["securityToken"])

			myRequiredArgList = ["securityToken","appId","env","tenantName","dbName","envOwnerDL","envOwnerAdGrp","serviceAccount","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "appId", "type" : str, "value" : myKwArgs["appId"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]},
				{"arg" : "envOwnerDL", "type" : str, "value" : myKwArgs["envOwnerDL"]},
				{"arg" : "envOwnerAdGrp", "type" : str, "value" : myKwArgs["envOwnerAdGrp"]},
				{"arg" : "serviceAccount", "type" : str, "value" : myKwArgs["serviceAccount"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.addNewAppEnv with argument >> {myKwArgs}")

			myDBResult = self.repo.addNewAppEnv(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				return self.util.buildResponse(self.Globals.unsuccess, f"An error [{myDBResult['message']} occurred while creating new applicaition for >>> {myKwArgs}!!!")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def saveHostScan(self, securityToken, **kwargs):
		"""
		Saves host scan data in repository database
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = "".join([securityToken, str(kwargs)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myKwArgs = self.util.getACopy(kwargs)

			if "hostScanData" not in myKwArgs:
				raise ValueError("missing required arguments >> hostScanData !!!")
			myRequiredArgList = [
				"env","opco","region","dcLocation","domain","hostName","hostId","ipAddress","ipv6Address",
				"scanDate","scanStartTS","bootTime",
				"os","dbOSUsers","connections","cpu","memory","swap","nicDetails","fs","fsStats","connections"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs["hostScanData"], [])

			myArgValidationList = [
				{"arg" : "env", "type" : str, "value" : myKwArgs["hostScanData"]["env"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["hostScanData"]["opco"]},
				{"arg" : "region", "type" : str, "value" : myKwArgs["hostScanData"]["region"]},
				{"arg" : "dcLocation", "type" : str, "value" : myKwArgs["hostScanData"]["dcLocation"]},
				{"arg" : "domain", "type" : str, "value" : myKwArgs["hostScanData"]["domain"]},				
				{"arg" : "hostName", "type" : str, "value" : myKwArgs["hostScanData"]["hostName"]},
				{"arg" : "hostId", "type" : str, "value" : myKwArgs["hostScanData"]["hostId"]},
				{"arg" : "ipAddress", "type" : str, "value" : myKwArgs["hostScanData"]["ipAddress"]},
				{"arg" : "ipv6Address", "type" : str, "value" : myKwArgs["hostScanData"]["ipAddress"]},
				{"arg" : "scanDate", "type" : str, "value" : myKwArgs["hostScanData"]["scanDate"]},
				{"arg" : "scanStartTS", "type" : str, "value" : myKwArgs["hostScanData"]["scanStartTS"]},
				{"arg" : "bootTime", "type" : str, "value" : myKwArgs["hostScanData"]["bootTime"]},
				{"arg" : "os", "type" : dict, "value" : myKwArgs["hostScanData"]["os"]},
				{"arg" : "dbOSUsers", "type" : list, "value" : myKwArgs["hostScanData"]["dbOSUsers"]},
				{"arg" : "connections", "type" : list, "value" : myKwArgs["hostScanData"]["connections"]},
				{"arg" : "cpu", "type" : dict, "value" : myKwArgs["hostScanData"]["cpu"]},
				{"arg" : "memory", "type" : dict, "value" : myKwArgs["hostScanData"]["memory"]},
				{"arg" : "swap", "type" : dict, "value" : myKwArgs["hostScanData"]["swap"]},
				{"arg" : "nicDetails", "type" : list, "value" : myKwArgs["hostScanData"]["nicDetails"]},
				{"arg" : "fs", "type" : list, "value" : myKwArgs["hostScanData"]["fs"]},
				{"arg" : "fsStats", "type" : dict, "value" : myKwArgs["hostScanData"]["fsStats"]},
				{"arg" : "sensors", "type" : dict, "value" : myKwArgs["hostScanData"]["sensors"]},
				{"arg" : "tenantsSummary", "type" : dict, "value" : myKwArgs["hostScanData"]["tenantsSummary"]},
				{"arg" : "tenants", "type" : list, "value" : myKwArgs["hostScanData"]["tenants"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			# removing _id column if passed, _id column need to be generated by system
			if "_id" in myKwArgs["hostScanData"]:
				myKwArgs["hostScanData"].pop("_id")

			self.LOGGER.info('executing repo.saveHostScan with arguments >>> {args}'.format(args = str(myKwArgs)))

			myDBResult = self.repo.saveHostScan(securityToken, myKwArgs["hostScanData"])

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"An error [{myDBResult['message']} occurred while saving host scan for {myKwArgs['hostScanData']['hostId']} !!!")

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			# Since flask is not aware of this object id, we need to convert the object id to oid (json format)
			if self.util.isBsonObjectId(myDBResult["data"]):
				myDBResult.update({"data" : self.util.convBsonObjectId2Oid(myDBResult["data"])})

			return self.util.buildResponse(self.Globals.success, self.Globals.success, repr(myDBResult["data"]))

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def addNewDBVersion(self, securityToken, **kwargs):
		"""
		Saves new db verson
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = "".join([securityToken, str(kwargs)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["dbTechnology", "version", "releasedDate", "userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "version", "type" : str, "value" : myKwArgs["version"]},
				{"arg" : "releasedDate", "type" : str, "value" : myKwArgs["releasedDate"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.addNewDBVersion with arguments >>> {args}'.format(args = str(myKwArgs)))

			myDBResult = self.repo.addNewDBVersion(securityToken, \
				myKwArgs["dbTechnology"].lower(), myKwArgs["version"], myKwArgs["releasedDate"], myKwArgs["userId"],)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"An error [{myDBResult['message']} occurred while saving db version ({myKwArgs['dbTechnology']}, {myKwArgs['version']}) !!!")

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			myDBResult.update({"data" : repr(myDBResult["data"])})

			return myDBResult

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def updDBVersionEOL(self, securityToken, **kwargs):
		"""
		Saves new db verson
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = "".join([securityToken, str(kwargs)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["dbTechnology", "version", "eolDate", "eosDate", "userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "version", "type" : str, "value" : myKwArgs["version"]},
				{"arg" : "eolDate", "type" : str, "value" : myKwArgs["eolDate"]},
				{"arg" : "eosDate", "type" : str, "value" : myKwArgs["eosDate"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.updDBVersionEOL with arguments >>> {args}'.format(args = str(myKwArgs)))

			myDBResult = self.repo.updDBVersionEOL(securityToken, \
				myKwArgs["dbTechnology"].lower(), myKwArgs["version"], \
				myKwArgs["eolDate"], myKwArgs["eosDate"], myKwArgs["userId"])

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"An error [{myDBResult['message']} occurred while saving eol/eos date ({myKwArgs['dbTechnology']} version {myKwArgs['version']}) !!!")

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			return self.util.buildResponse(self.Globals.success, self.Globals.success, repr(myDBResult["data"]))

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAllVerDetails(self, **kwargs):
		"""
		Returns all version details for a given database technology
		arguments:
			securityToken
			appId
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["dbTechnology","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			myDBResult = self.repo.getAllVerDetails(myKwArgs["securityToken"], myKwArgs["dbTechnology"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"An error [{myDBResult['message']} occurred while database technology {dbTechnology} version details !!!")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getABaseVerDetails(self, **kwargs):
		"""
		Returns all version details for a given database technology and base version of passed version
		arguments:
			securityToken
			appId
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["dbTechnology","version","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "version", "type" : str, "value" : myKwArgs["version"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			myDBResult = self.repo.getABaseVerDetails(myKwArgs["securityToken"], myKwArgs["dbTechnology"], myKwArgs["version"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"An error [{myDBResult['message']} occurred while retrieving database technology {dbTechnology} version {version} details !!!")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAVerDetails(self, **kwargs):
		"""
		Returns version details for a given database technology and version
		arguments:
			securityToken
			appId
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["dbTechnology","version","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "version", "type" : str, "value" : myKwArgs["version"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing  repo.getAVerDetails with arguments >>> {myKwArgs}")
			
			myDBResult = self.repo.getAVerDetails(myKwArgs["securityToken"], myKwArgs["dbTechnology"], myKwArgs["version"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"An error [{myDBResult['message']} occurred while retrieving database technology {dbTechnology} version {version} details !!!")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getATenantDetails(self, **kwargs):
		"""
		Returns A tenants detials
		arguments:
			securityToken
			tenantName
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			if "tenantName" not in myKwArgs:
				raise ValueError("missing required arguments (tenantName) !!")

			self.LOGGER.info(f"executing  repo.getTenantDetails with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getTenantDetails(myKwArgs["securityToken"], myKwArgs["tenantName"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			"""
			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			"""
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getATenantInfo(self, **kwargs):
		"""
		Returns A tenants detials
		arguments:
			securityToken
			tenantName
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			if "tenantName" not in myKwArgs:
				raise ValueError("missing required arguments (tenantName) !!")

			self.LOGGER.info(f"executing  repo.getATenantInfo with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getATenantInfo(myKwArgs["securityToken"], myKwArgs["tenantName"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			"""
			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			"""
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getTenantDetailsRep(self, **kwargs):
		"""
		Returns tenants detials for a given opco/region/technology and its version and env
		arguments:
			securityToken
			opco
			region
			dbTechnology
			version
			env
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)
			myKwArgsKey = list(myKwArgs.keys())

			if not self.util.isAnyElemInListExistsInAList(["opco","region","dbTechnology","env"], myKwArgsKey):
				raise ValueError("either opco/region/dbTechnology/env argument must be passed !!")

			self.LOGGER.info(f"executing  repo.getTenantDetailsRep with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getTenantDetailsRep(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getTenantSmmaryRep(self, **kwargs):
		"""
		Returns tenants detials for a given opco/region/technology and its version and env
		arguments:
			securityToken
			opco
			region
			dbTechnology
			version
			env
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)
			myKwArgsKey = list(myKwArgs.keys())

			if not self.util.isAnyElemInListExistsInAList(["opco","region","dbTechnology","env"], myKwArgsKey):
				raise ValueError("either opco/region/dbTechnology/env argument must be passed !!")

			self.LOGGER.info(f"executing  repo.getTenantSmmary with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getTenantSmmaryRep(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAllOpsMgrUser(self, **kwargs):
		"""
		Returns Ops Manager admin user detials for a given opco/region 
		arguments:
			securityToken
			opco
			region
			opsMgrUrl
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				#{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			""" not needed, will pull all ops manager url from repository
			# validating opsMgrUrl if passed
			if "opsMgrUrl" in myKwArgs and myKwArgs["opsMgrUrl"] and myKwArgs["opsMgrUrl"].upper() != 'ALL':
				myUrlSplit = myKwArgs["opsMgrUrl"].split(":")
				if len(myUrlSplit) == 1:
					# we didnt get port in opsmgrlurl, adding default port and api url
					myOpsMgrUrl = "".join([myUrlSplit[0],":8080/api/public/v1.0"])
					myOpsMgrHost = myUrlSplit[0]
					myOpsMgrPort = 8080
				else:
					# we have port in url, retrieving host and port, this needed to check if target OpsManager port is open
					myOpsMgrHost = myUrlSplit[0]
					myOpsMgrPort = myUrlSplit[1].split("/")[0]
				# validaitng Ops magr port 
				if not self.util.isPortOpen(myOpsMgrHost, int(myOpsMgrPort)):
					self.util.buildResponse(self.Globals.unsuccess, f"OpsMgr {myKwArgs["opsMgrUrl"]} port is not open !!!")
			"""
			self.LOGGER.info(f"executing  repo.getOpsMgrAdminUserList with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getOpsMgrAdminUserList(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def genOpsMgrUserReport(self, **kwargs):
		"""
		Returns Ops Manager admin user detials for a given opco/region/opsMgr 
		arguments:
			securityToken
			opco
			region
			opsMgrUrl
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			#myRequiredArgList = ["securityToken", "opco", "region", "userId"]
			myRequiredArgList = ["securityToken", "opco", "userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				#{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			""" not needed, will pull all ops manager url from repository
			# validating opsMgrUrl if passed
			if "opsMgrUrl" in myKwArgs and myKwArgs["opsMgrUrl"] and myKwArgs["opsMgrUrl"].upper() != 'ALL':
				myUrlSplit = myKwArgs["opsMgrUrl"].split(":")
				if len(myUrlSplit) == 1:
					# we didnt get port in opsmgrlurl, adding default port and api url
					myOpsMgrUrl = "".join([myUrlSplit[0],":8080/api/public/v1.0"])
					myOpsMgrHost = myUrlSplit[0]
					myOpsMgrPort = 8080
				else:
					# we have port in url, retrieving host and port, this needed to check if target OpsManager port is open
					myOpsMgrHost = myUrlSplit[0]
					myOpsMgrPort = myUrlSplit[1].split("/")[0]
				# validaitng Ops magr port 
				if not self.util.isPortOpen(myOpsMgrHost, int(myOpsMgrPort)):
					self.util.buildResponse(self.Globals.unsuccess, f"OpsMgr {myKwArgs["opsMgrUrl"]} port is not open !!!")
			"""
			self.LOGGER.info(f"executing  reports.genOpsMgrUserReport with arguments >>> {myKwArgs}")

			myDBResult = self.reports.genOpsMgrUserReport(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAdminUserSummaryList(self, **kwargs):
		"""
		Returns Mongo root admin user detials for a given opco/dbTechnology 
		arguments:
			securityToken
			opco
			region
			dbTechnology
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken", "opco","dbTechnology", "userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},				
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			if myKwArgs["dbTechnology"] == self.Globals.DB_TYPE_MONGO:
				self.LOGGER.info(f"executing repo.getMongoRootUserSummaryList with arguments >>> {myKwArgs}")
				#myDBResult = self.repo.getMongoRootUserSummaryList(securityToken = myKwArgs["securityToken"], opco = myKwArgs["opco"], region = myKwArgs["region"])
				myDBResult = self.repo.getMongoRootUserSummaryList(securityToken = myKwArgs["securityToken"], opco = myKwArgs["opco"])
			else:
				return self.util.buildResponse(self.Globals.success, f"Super user report is not implemented for {myKwArgs['dbTechnolgoy']} !!!")

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def genAdminUserSummaryReport(self, **kwargs):
		"""
		Returns Ops Manager admin user detials for a given opco/region/opsMgr 
		arguments:
			securityToken
			opco
			region
			dbTechnology
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			#myRequiredArgList = ["opco", "region", "dbTechnology", "userId"]
			myRequiredArgList = ["securityToken", "opco", "dbTechnology", "recepient", "userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			#if myKwArgs["dbTechnology"] == self.Globals.DB_TYPE_MONGO:
			self.LOGGER.info(f"executing  reports.genAdminUserSummaryReport with arguments >>> {myKwArgs}")
			"""
			myDBResult = self.reports.genAdminUserSummaryReport(\
				securityToken = myKwArgs["securityToken"], \
				opco = myKwArgs["opco"], \
				#region = myKwArgs["region"], \
				dbTechnology = myKwArgs["dbTechnology"])
			#else:
			#	return self.util.buildResponse(self.Globals.success, f"Super user report is not implemented for {myKwArgs['dbTechnolgoy']} !!!")
			"""
			myDBResult = self.reports.genAdminUserSummaryReport(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAdminUserList(self, **kwargs):
		"""
		Returns Ops Manager admin user detials for a given opco/region/dbTechnology/tenants 
		arguments:
			securityToken
			opco
			region
			dbTechnology
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["opco", "dbTechnology", "tenants", "userId"]
			#myRequiredArgList = ["opco", "region", "dbTechnology", "tenants", "userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				#{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "tenants", "type" : list, "value" : myKwArgs["tenants"]},							
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			if myKwArgs["dbTechnology"] == self.Globals.DB_TYPE_MONGO:
				self.LOGGER.info(f"executing  repo.getMongoRootUserList with arguments >>> {myKwArgs}")
				myDBResult = self.repo.getMongoRootUserList(\
					securityToken = myKwArgs["securityToken"], \
					opco = myKwArgs["opco"], \
					#region = myKwArgs["region"], \
					tenants = myKwArgs["tenants"], \
					dbTechnology = myKwArgs["dbTechnology"])
			else:
				return self.util.buildResponse(self.Globals.success, f"Super user report is not implemented for {myKwArgs['dbTechnolgoy']} !!!")
			#else:
			#	return self.util.buildResponse(self.Globals.success, f"Super user report is not implemented for {myKwArgs['dbTechnolgoy']} !!!")

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def genTenantAdminUserReport(self, **kwargs):
		"""
		Generate reports (xlsx) admin user (super user/root) detials for a given opco/region/dbTechnology/tenants 
		arguments:
			securityToken
			opco
			region
			dbTechnology
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			#myRequiredArgList = ["opco", "region", "dbTechnology", "tenants", "userId"]
			myRequiredArgList = ["opco","dbTechnology", "tenants", "recepient", "userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "tenants", "type" : list, "value" : myKwArgs["tenants"]},
				{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			if myKwArgs["dbTechnology"] == self.Globals.DB_TYPE_MONGO:
				self.LOGGER.info(f"executing  reports.genAdminUserReport with arguments >>> {myKwArgs}")
				"""
				myDBResult = self.reports.genAdminUserReport(\
					securityToken = myKwArgs["securityToken"], \
					opco = myKwArgs["opco"], \
					tenants = myKwArgs["tenants"], \
					dbTechnology = myKwArgs["dbTechnology"],
					userId = myKwArgs["userId"]
				)
				"""
				myDBResult = self.reports.genTenantAdminUserReport(**myKwArgs)
			else:
				return self.util.buildResponse(self.Globals.success, f"Super user report is not implemented for {myKwArgs['dbTechnolgoy']} !!!")
			#else:
			#	return self.util.buildResponse(self.Globals.success, f"Super user report is not implemented for {myKwArgs['dbTechnolgoy']} !!!")

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def genMongoAuditReport(self, **kwargs):
		"""
		Returns tenants detials for a given opco/region/technology and its version and env
		arguments:
			securityToken
			opco
			region
			startDate
			endDate
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			#myRequiredArgList = ["opco", "region", "startDateStr", "endDateStr", "tenantNameList", "userId"]
			myRequiredArgList = ["securityToken","opco", "env", "tenantList", "startDate", "endDate", "userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				#{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "tenantList", "type" : list, "value" : myKwArgs["tenantList"]},
				{"arg" : "startDate", "type" : str, "value" : myKwArgs["startDate"]},
				{"arg" : "endDate", "type" : str, "value" : myKwArgs["endDate"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])
			## adding dbtechnology for mongo
			myKwArgs.update({"dbTechnology" : self.Globals.DB_TYPE_MONGO})

			self.LOGGER.info(f"executing  reports.genMongoAuditReport with arguments >>> {myKwArgs}")

			myDBResult = self.reports.genMongoAuditReport(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			#return self.util.buildResponse(self.Globals.success, myDBResult["message"], myDBResult["data"])
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def __addCompTaskDetail__(self, **kwargs):
		"""
		Adds compliance task details (annual dr test/restore drill) for a given opco/region/technology/env
		arguments:
			securityToken
			opco
			region
			dbTechnology
			task
			env
			hostPort
			supportingDoc
			when
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","region","dbTechnology","task","frequency","env","hostPort","supportingDoc","when","outcome","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "task", "type" : str, "value" : myKwArgs["task"]},
				{"arg" : "frequency", "type" : str, "value" : myKwArgs["frequency"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "hostPort", "type" : str, "value" : myKwArgs["hostPort"]},
				{"arg" : "supportingDoc", "type" : str, "value" : myKwArgs["supportingDoc"]},
				{"arg" : "when", "type" : str, "value" : myKwArgs["when"]},
				{"arg" : "outcome", "type" : str, "value" : myKwArgs["outcome"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			# validating task/frequency
			if myKwArgs["task"] not in self.Globals.VALID_ANNUAL_COMP_TASK:
				raise ValueError(f"Invalid compliance task {myKwArgs['task']} !!!")

			if myKwArgs["frequency"] not in self.Globals.VALID_FREQUENCY:
				raise ValueError(f"Invalid frequency {myKwArgs['frequency']} !!!")

			self.LOGGER.info(f"executing  repo.addCompTaskDetail with arguments >>> {myKwArgs}")

			myDBResult = self.repo.addCompTaskDetail(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def addCompTaskDetail(self, **kwargs):
		"""
		Adds compliance task details (annual dr test/restore drill) for a given opco/region/technology/env
		arguments:
			securityToken
			opco
			task
			env
			dbTechnology
			tenantIds
			supportingDoc
			when
			outcome
			otherData
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","tenantNames","task","supportingDoc","when","result","otherData","comments","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, ["otherData"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "tenantNames", "type" : list, "value" : myKwArgs["tenantNames"]},
				{"arg" : "task", "type" : str, "value" : myKwArgs["task"]},
				{"arg" : "supportingDoc", "type" : str, "value" : myKwArgs["supportingDoc"]},
				{"arg" : "when", "type" : str, "value" : myKwArgs["when"]},
				{"arg" : "result", "type" : str, "value" : myKwArgs["result"]},
				{"arg" : "comments", "type" : str, "value" : myKwArgs["comments"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, ["otherData"])

			# validating task/frequency
			if myKwArgs["task"] not in self.Globals.VALID_ANNUAL_COMP_TASK:
				raise ValueError(f"Invalid compliance task {myKwArgs['task']} !!!")

			self.LOGGER.info(f"executing  repo.addCompTaskDetail with arguments >>> {myKwArgs}")

			myDBResult = self.repo.addCompTaskDetail(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def updCompTasks(self, **kwargs):
		"""
		Update compliance task details attribute (supporting doc, when)

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string)
			:param arg5: compTaskIds (list) 
			:param arg5: supportingDoc (string) 
			:param arg5: when (string) 
			:param arg5: tag (string) 
			:param arg5: comments (string) 
			:param arg8: userId (string)			 
			:return: json
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				updCompTasks(\
					securityToken = 'securityToken', \
					compTaskIds = [id1,id2], \
					supportingDoc = 'ca/co#', \
					when = 'implementation date, \
					tag = 'user defined tag', \
					comments = 'user commentd', \
					userId = 'userId' \
				)

		.. note::
			

		.. warning:: 


		.. seealso:: 


		"""		

		try:
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(kwargs)])))

			# validating securityToken
			myKwArgs = self.util.getACopy(kwargs)

			if not "securityToken" in myKwArgs:
				raise ValueError("missing mandatory arguments 'securityToken' !!!")

			self.sec.validateSecToken(myKwArgs["securityToken"])

			myRequiredArgList = ["securityToken","compTaskIds","supportingDoc","when","tag","comments","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, ["tag"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "compTaskIds", "type" : list, "value" : myKwArgs["compTaskIds"]},
				{"arg" : "when", "type" : str, "value" : myKwArgs["when"]},
				{"arg" : "comments", "type" : str, "value" : myKwArgs["comments"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, ["tag"])

			self.LOGGER.info(f"executing  repo.updCompTasks with arguments >>> {myKwArgs}")

			myDBResult = self.repo.updCompTasks(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getDistinctCompYear(self, **kwargs):
		"""
		Returns Compliance task (DR Test/Restore drill etc details for a given opco/region/dbtechnology/year) 
		arguments:
			securityToken
			opco
			env
			task
			dbTechnology
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","region","env","dbTechnology","compliance","tenant","status","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "region", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "compliance", "type" : str, "value" : myKwArgs["compliance"]},
				{"arg" : "tenant", "type" : str, "value" : myKwArgs["tenant"]},
				{"arg" : "status", "type" : str, "value" : myKwArgs["status"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing  repo.getCompTaskDetail with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getCompTaskDetail(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getCompTaskDetail(self, **kwargs):
		"""
		Returns Compliance task (DR Test/Restore drill etc details for a given opco/region/dbtechnology/year) 
		arguments:
			securityToken
			opco
			region
			dbTechnology
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","region","env","dbTechnology","compliance","tenant","status","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, ["otherData"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "compliance", "type" : str, "value" : myKwArgs["compliance"]},
				{"arg" : "tenant", "type" : str, "value" : myKwArgs["tenant"]},
				{"arg" : "status", "type" : str, "value" : myKwArgs["status"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing  repo.getCompTaskDetail with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getCompTaskDetail(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getACompTaskDetail(self, **kwargs):
		"""
		Returns Compliance task (DR Test/Restore drill etc details for a given opco/region/dbtechnology/year) 
		arguments:
			securityToken
			opco
			region
			dbTechnology
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken", "compTaskId", "userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "compTaskId", "type" : str, "value" : myKwArgs["compTaskId"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing  repo.getACompTaskDetail with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getACompTaskDetail(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def genMonthlyMGMTPasswordReport(self, **kwargs):
		"""
		Generate Monthly MGMT Password compliance report
		arguments:
			securityToken
			opco
			dbTechnology
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)
			myKwArgsKey = list(myKwArgs.keys())

			if not self.util.isAnyElemInListExistsInAList(["opco","dbTechnology"], myKwArgsKey):
				raise ValueError("either opco/dbTechnology argument must be passed !!")

			self.LOGGER.info(f"executing  reports.genMonthlyMGMTPassReport with arguments >>> {myKwArgs}")

			myDBResult = self.reports.genMonthlyMGMTPassReport(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAllHostDetails(self, **kwargs):
		"""
		Returns tenants detials for a given opco/region/technology and its version and env
		arguments:
			securityToken
			opco
			region
			dbTechnology
			env
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)
			myKwArgsKey = list(myKwArgs.keys())

			if not self.util.isAnyElemInListExistsInAList(["opco","dbTechnology","inclEnvList","userId"], myKwArgsKey):
				raise ValueError("either opco/dbTechnology/inclEnvList/userId argument must be passed !!")

			# commenting this validation is not possible as all arguments are optional but would need 1 argument 
			"""
			myRequiredArgList = ["userId"]

			myArgValidationList = [
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "version", "type" : str, "value" : myKwArgs["version"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, ["opco","region","dbTechnology"])
			"""
			myDBResult = self.repo.getAllHostDetails(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def genAllHostDetailsReport(self, **kwargs):
		"""
		Returns tenants detials for a given opco/region/technology and its version and env
		arguments:
			securityToken
			opco
			region
			dbTechnology
			env
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)
			myKwArgsKey = list(myKwArgs.keys())

			if not self.util.isAnyElemInListExistsInAList(["opco","dbTechnology","inclEnvList","userId"], myKwArgsKey):
				raise ValueError("either opco/dbTechnology/inclEnvList/userId argument must be passed !!")

			# commenting this validation is not possible as all arguments are optional but would need 1 argument 
			"""
			myRequiredArgList = ["userId"]

			myArgValidationList = [
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "version", "type" : str, "value" : myKwArgs["version"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, ["opco","region","dbTechnology"])
			"""
			self.LOGGER.info(f"executing reports.genAllHostDetailsReport with arguments >>> {myKwArgs}")

			myDBResult = self.reports.genAllHostDetailsReport(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			#return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def genHostReport4MongoLicensing(self, **kwargs):
		"""
		Returns tenants detials for a given opco/region/technology and its version and env
		arguments:
			securityToken
			opco
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)
			myKwArgsKey = list(myKwArgs.keys())

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]},
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing reports.genHostReport4MongoLicensing with arguments >>> {myKwArgs}")

			myDBResult = self.reports.genHostReport4MongoLicensing(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			#return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getMongoLicensingData(self, **kwargs):
		"""
		Returns Mongo licnesing data

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string )
			:param arg2: opco (string )
			:param arg3: userId (string )
			:return: json
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				getMongoLiceningData('securityToken', opco, userId)

		.. note::
			

		.. warning:: 


		.. seealso:: 


		"""		
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)
			myKwArgsKey = list(myKwArgs.keys())

			myRequiredArgList = ["securityToken","opco","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getMongoLicensingData with arguments >>> {myKwArgs}")

			if "output" in myKwArgs:
				myDBResult = self.repo.getMongoLicensingData(myKwArgs["securityToken"], myKwArgs["opco"], myKwArgs["output"])
			else:
				myDBResult = self.repo.getMongoLicensingData(myKwArgs["securityToken"], myKwArgs["opco"])

			#self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getLdapUserdetails(self, **kwargs):
		"""
		Retrieve user details for a given employeeid or network id
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","userSearchAttr","userSearchAttrVal","returnValue","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, ["returnValue"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "userSearchAttr", "type" : str, "value" : myKwArgs["userSearchAttr"]},
				{"arg" : "userSearchAttrVal", "type" : str, "value" : myKwArgs["userSearchAttrVal"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, ["returnValue"])

			self.LOGGER.info(f"executing util.getLdapUserDetails with argument {myKwArgs}")

			# retrieving ldap details
			myDomain = self.util.getEnvKeyVal("DOMAIN")
			if not myDomain:
				myDomain = "CORP"

			myDBResult = self.getSysConfig(**{"securityToken" : myKwArgs["securityToken"], "opco" : "GLOBAL", "userId" : myKwArgs["userId"]})

			self.LOGGER.info(f"sys config data for ldap >>> {myDBResult}")

			if myDBResult["status"] == self.Globals.unSuccess:
				raise ValueError(f"An error occurred while retrieving GLOBAL config data >>> {myDBResult['message']} !!!")

			myLdapServerDetails = [ldap for ldap in myDBResult["data"]["ldapServers"] if ldap["domain"].upper() == myDomain.upper() ]
			#myLdapServerDetails = [ldap for ldap in myDBResult["ldapServers"] if ldap["domain"].upper() == myKwArgs["domain"].upper()]

			if not myLdapServerDetails:
				raise ValueError(f"Missing LDAP details for opco >>> {myDomain} !!!")

			myLdapServerDetails = myLdapServerDetails[0]

			myLdapServer = ""

			for server in myLdapServerDetails["servers"]:
				if self.util.isPortOpen(server.split(":")[0], int(server.split(":")[1])):
					myLdapServer = server
					break

			if not myLdapServer:
				raise ValueError(f"No valid ldap server found for domain {myDomain}, either server list is empty or port is not open !!!")

			myLdapServerDetails = {
				"server" : myLdapServer,
				"id" : myLdapServerDetails["id"],
				"enc" : myLdapServerDetails["enc"],
				"baseDC" : myLdapServerDetails["baseDC"]
			}

			myUserData = self.util.getLdapUserDetails(\
				myKwArgs["userSearchAttr"], \
				myKwArgs["userSearchAttrVal"], \
				myLdapServerDetails, \
				myKwArgs["returnValue"] if "returnValue" in myKwArgs and isinstance(myKwArgs["returnValue"], str) else "default")

			self.LOGGER.info(f"result >>> {myUserData}")
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myUserData)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def onBoardDBAdmin(self, **kwargs):
		"""
		On boards database admin id for a given opco/dbTechnology
		arguments:
			securityToken
			opco
			dbTechnology
			networkId
			dbLoginId
			onBoardDate
			supportingDoc
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","dbTechnology","employeeId","dbLoginId","onBoardDate","supportingDoc","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "employeeId", "type" : str, "value" : myKwArgs["employeeId"]},
				{"arg" : "dbLoginId", "type" : list, "value" : myKwArgs["dbLoginId"]},
				{"arg" : "supportingDoc", "type" : str, "value" : myKwArgs["supportingDoc"]},
				{"arg" : "onBoardDate", "type" : str, "value" : myKwArgs["onBoardDate"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, [])

			myADUserDetails = self.util.getLdapUserDetails('employeeId', myKwArgs["employeeId"])

			if not myADUserDetails:
				# user is not found, 
				return self.util.buildResponse(self.Globals.unsuccess, f"Could not find employee id {myKwArgs['emplolyeeId']} from ldap server {self.util.getEnvKeyVal('LDAP_SERVER')}!!!")
				#last name and first name must have been passed
				#if not self.util.isListItemExistsInAList(["firstName","lastName"], list(myKwArgs.keys())):
				#	return self.util.buildResponse(self.Globals.unsuccess, f"Could not find Network id {myKwArgs['networkId']}, missing firstName/lastName arguments !!!")

			self.LOGGER.info(f"executing  repo.onBoardDBAdmin with arguments >>> {myKwArgs}")

			myDBResult = self.repo.onBoardDBAdmin(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def offBoardDBAdminTech(self, **kwargs):
		"""
		Off board employess for a given db technology
		arguments:
			securityToken
			employeeId
			dbTechnology
			offBoardingDoc
			offBoardDate
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken", "employeeId", "dbTechnology", "offBoardingDoc", "offBoardDate", "userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "employeeId", "type" : str, "value" : myKwArgs["employeeId"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "offBoardingDoc", "type" : str, "value" : myKwArgs["offBoardingDoc"]},
				{"arg" : "offBoardDate", "type" : str, "value" : myKwArgs["offBoardDate"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, [])

			#myUserName = self.util.getADGrpUserName(myKwArgs["networkId"])

			#if not myUserName:
			#	return self.util.buildResponse(self.Globals.unsuccess, f"Invalid network id {myKwArgs['networkId']} !!!")

			self.LOGGER.info(f"executing  repo.offBoardDBAdminTech with arguments >>> {myKwArgs}")

			myDBResult = self.repo.offBoardDBAdminTech(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def offBoardDBAdmin(self, **kwargs):
		"""
		Offboard DB Admin
		arguments:
			securityToken
			employeeId
			offBoardDate
			supportingDoc
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","employeeId","offBoardingDoc","offBoardDate","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "employeeId", "type" : str, "value" : myKwArgs["employeeId"]},
				{"arg" : "offBoardingDoc", "type" : str, "value" : myKwArgs["offBoardingDoc"]},
				{"arg" : "offBoardDate", "type" : str, "value" : myKwArgs["offBoardDate"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, [])

			#myUserName = self.util.getADGrpUserName(myKwArgs["networkId"])

			#if not myUserName:
			#	return self.util.buildResponse(self.Globals.unsuccess, f"Invalid network id {myKwArgs['networkId']} !!!")

			self.LOGGER.info(f"executing  repo.offBoardDBAdmin with arguments >>> {myKwArgs}")

			myDBResult = self.repo.offBoardDBAdmin(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def modifyDBAdmin(self, **kwargs):
		"""
		Modify DB admin's attribute (contact)
		arguments:
			securityToken
			employeeId
			contact
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","employeeId","contact","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "employeeId", "type" : str, "value" : myKwArgs["employeeId"]},
				{"arg" : "contact", "type" : str, "value" : myKwArgs["contact"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing  repo.modifyDBAdmin with arguments >>> {myKwArgs}")

			myDBResult = self.repo.modifyDBAdmin(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getDBAdminRoster(self, **kwargs):
		"""
		On boards database admin id for a given opco/dbTechnology
		arguments:
			securityToken
			opco
			dbTechnology
			status
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			#myRequiredArgList = ["securityToken","opco","dbTechnology","status","consolidated","userId"]
			myRequiredArgList = ["securityToken","opco","dbTechnology","status","consolidated","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, ["consolidated"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "status", "type" : str, "value" : myKwArgs["status"]},
				#{"arg" : "consolidated", "type" : str, "value" : myKwArgs["consolidated"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, ["consolidated"])

			#myUserName = self.util.getADGrpUserName(myKwArgs["networkId"])

			#if not myUserName:
			#	return self.util.buildResponse(self.Globals.unsuccess, f"Invalid network id {myKwArgs['networkId']} !!!")

			self.LOGGER.info(f"executing  repo.getDBAdminRoster with arguments >>> {myKwArgs}")
			if "consolidated" not in myKwArgs:
				myKwArgs.update({"consolidated" : "yes"})

			myDBResult = self.repo.getDBAdminRoster(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getDBAdminDetails(self, **kwargs):
		"""
		On boards database admin id for a given opco/dbTechnology
		arguments:
			securityToken
			networkId
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","employeeId","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "employeeId", "type" : str, "value" : myKwArgs["employeeId"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing  repo.getDBAdminDetails with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getDBAdminDetails(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			#if myDBResult["status"] == self.Globals.unsuccess:
			#	raise ValueError(f"[{myDBResult['message']}]")
			
			#return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def genAdminRosterReport(self, **kwargs):
		"""
		Generate DB Admin roster report for a given opco/dbTechnology/status
		arguments:
			securityToken
			opco
			status
			dbTechnology
			recepient
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","status","dbTechnology","recepient","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "status", "type" : str, "value" : myKwArgs["status"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing reports.getDBAdminDetails with arguments >>> {myKwArgs}")

			myDBResult = self.reports.genAdminRosterReport(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			#return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAuditScanStatus(self, **kwargs):
		"""
		Returns audit scna status data for a given opco/startDate/endDate/userId
		arguments:
			securityToken
			opco
			startDate
			endDate
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","startDate","endDate"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "startDate", "type" : str, "value" : myKwArgs["startDate"]},
				{"arg" : "endDate", "type" : str, "value" : myKwArgs["endDate"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			#myKwArgs["startDate"] = self.util.convStr2DateViaParser(myKwArgs["startDate"])
			#myKwArgs["endDate"] = self.util.convStr2DateViaParser(myKwArgs["endDate"])

			self.LOGGER.info(f"executing repo.getAuditScanStatus with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getAuditScanStatus(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")

			#return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAuditScanStatus4WWW(self, **kwargs):
		"""
		Returns audit scna status data for a given opco/startDate/endDate/userId for WWW
		arguments:
			securityToken
			opco
			startDate
			endDate
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","startDate","endDate"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "startDate", "type" : str, "value" : myKwArgs["startDate"]},
				{"arg" : "endDate", "type" : str, "value" : myKwArgs["endDate"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			#myKwArgs["startDate"] = self.util.convStr2DateViaParser(myKwArgs["startDate"])
			#myKwArgs["endDate"] = self.util.convStr2DateViaParser(myKwArgs["endDate"])

			self.LOGGER.info(f"executing repo.getAuditScanStatus4WWW with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getAuditScanStatus4WWW(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")

			#return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAuditData(self, **kwargs):
		"""
		Returns audit scna status data for a given opco/startDate/endDate/userId
		arguments:
			securityToken
			opco
			dbTechnology
			tenantsList
			startDate
			endDate
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","dbTechnology","tenantList","startDate","endDate","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "tenantList", "type" : list, "value" : myKwArgs["tenantList"]},
				{"arg" : "startDate", "type" : str, "value" : myKwArgs["startDate"]},
				{"arg" : "endDate", "type" : str, "value" : myKwArgs["endDate"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			#getAuditEvent(self, securityToken, opco, env, dbTechnology, region, tenantList, startDate, endDate):
			self.LOGGER.info(f"executing repo.getAuditEvent with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getAuditEvent(\
				myKwArgs["securityToken"], \
				myKwArgs["opco"], \
				myKwArgs["env"], \
				myKwArgs["dbTechnology"], \
				myKwArgs["tenantList"], \
				myKwArgs["startDate"], \
				myKwArgs["endDate"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			#if myDBResult["status"] == self.Globals.unsuccess:
			#	raise ValueError(f"[{myDBResult['message']}]")

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)
			#return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAuditScanDetail(self, **kwargs):
		"""
		Returns audit scna status data for a given opco/startDate/endDate/userId
		arguments:
			securityToken
			hostName
			scanStartDate
			scanEndDate
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","hostName","scanStartDate","scanEndDate","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "hostName", "type" : str, "value" : myKwArgs["hostName"]},
				{"arg" : "scanStartDate", "type" : str, "value" : myKwArgs["scanStartDate"]},
				{"arg" : "scanEndDate", "type" : str, "value" : myKwArgs["scanEndDate"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.LOGGER.info(f"executing repo.getAuditScanDetail with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getAuditScanDetail(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")

			#return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def genAuditScanStatusReport(self, **kwargs):
		"""
		Generate DB Admin roster report for a given opco/dbTechnology/status
		arguments:
			securityToken
			opco
			status
			dbTechnology
			recepient
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","startDate","recepient","endDate"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				#{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				#{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "startDate", "type" : str, "value" : myKwArgs["startDate"]},
				{"arg" : "endDate", "type" : str, "value" : myKwArgs["endDate"]},
				{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			#myKwArgs["startDate"] = self.util.convStr2DateViaParser(myKwArgs["startDate"])
			#myKwArgs["endDate"] = self.util.convStr2DateViaParser(myKwArgs["endDate"])

			self.LOGGER.info(f"executing reports.genAuditScanStatusReport with arguments >>> {myKwArgs}")

			myDBResult = self.reports.genAuditScanStatusReport(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			#return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getHostInventory(self, **kwargs):
		"""
		Add host name and tenants to inventory
		Arguments:
			opco
			region
			dcLocation
			dbTechnology
			env
			tag
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","region","dcLocation","dbTechnology","env","tag","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "dcLocation", "type" : str, "value" : myKwArgs["dcLocation"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "tag", "type" : str, "value" : myKwArgs["tag"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getHostInventory with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getHostInventory(**myKwArgs)

			#self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			#return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAHostDetails(self, **kwargs):
		"""
		Retrieve a host details
		Arguments:
			securityToken
			hostName
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","hostName","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "hostName", "type" : str, "value" : myKwArgs["hostName"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getHostFromInvenory with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getHostFromInvenory(myKwArgs["securityToken"], myKwArgs["hostName"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def addHost2Inventory(self, **kwargs):
		"""
		Add host name and tenants to inventory
		Arguments:
			opco
			region
			dcLocation
			env
			host
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","region","dcLocation","domain","dbTechnology","env","tag","hostName","scanEnabled","cpu","memoryGB","swapGB","os","comments","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "dcLocation", "type" : str, "value" : myKwArgs["dcLocation"]},
				{"arg" : "domain", "type" : str, "value" : myKwArgs["domain"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "tag", "type" : str, "value" : myKwArgs["tag"]},
				{"arg" : "hostName", "type" : str, "value" : myKwArgs["hostName"]},
				{"arg" : "cpu", "type" : int, "value" : myKwArgs["cpu"]},
				{"arg" : "memoryGB", "type" : int, "value" : myKwArgs["memoryGB"]},
				{"arg" : "swapGB", "type" : int, "value" : myKwArgs["swapGB"]},				
				{"arg" : "os", "type" : str, "value" : myKwArgs["os"]},				
				{"arg" : "scanEnabled", "type" : str, "value" : myKwArgs["scanEnabled"]},
				#{"arg" : "licenseNeeded", "type" : str, "value" : myKwArgs["licenseNeeded"]},
				{"arg" : "comments", "type" : str, "value" : myKwArgs["comments"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.addHost2Inventory with arguments >>> {myKwArgs}")

			myDBResult = self.repo.addHost2Inventory(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			#return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def updateHostInventory(self, **kwargs):
		"""
		Update host attributes in inventory
		Arguments:
			hostName
			opco
			region
			dcLocation
			domain
			tag
			scanEnabled
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			#myRequiredArgList = ["securityToken","opco","region","domain","tag","scanEnabled","userId"]
			myRequiredArgList = ["securityToken","hostName","opco","region","domain","tag","scanEnabled","comments","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "hostName", "type" : str, "value" : myKwArgs["hostName"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "domain", "type" : str, "value" : myKwArgs["domain"]},
				{"arg" : "tag", "type" : str, "value" : myKwArgs["tag"]},
				{"arg" : "scanEnabled", "type" : str, "value" : myKwArgs["scanEnabled"]},
				{"arg" : "comments", "type" : str, "value" : myKwArgs["comments"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.updateHostInventory with arguments >>> {myKwArgs}")

			myDBResult = self.repo.updateHostInventory(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			#return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getTenantVerComplianceData(self, **kwargs):
		"""
		Retrieves tenants version complaince data
		Arguments:
			securityToken
			opco
			dbTechnology
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","dbTechnology","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getTenantVersionDetail with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getTenantVersionDetail(myKwArgs["securityToken"], myKwArgs["opco"], myKwArgs["dbTechnology"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			#return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getATenantMemberDetail(self, **kwargs):
		"""
		Retrieve tenant member details for a given tenant member id
		Arguments:
			securityToken
			tenantName
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","tenantMemberId","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "tenantMemberId", "type" : str, "value" : myKwArgs["tenantMemberId"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getTenantMemberDetails with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getTenantMemberDetails(myKwArgs["securityToken"], myKwArgs["tenantMemberId"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
	
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getATenantRoleDetails(self, **kwargs):
		"""
		Retrieve tenant role details
		Arguments:
			securityToken
			tenantName
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","tenantName","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getTenantRoles with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getTenantRoles(myKwArgs["securityToken"], myKwArgs["tenantName"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
	
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getATenantRoleDetails(self, **kwargs):
		"""
		Retrieve tenant role details
		Arguments:
			securityToken
			tenantName
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","tenantName","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getTenantRoles with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getTenantRoles(myKwArgs["securityToken"], myKwArgs["tenantName"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
	
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getATenantUserDetails(self, **kwargs):
		"""
		Retrieve tenant user details
		Arguments:
			securityToken
			tenantName
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","tenantName","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getATenantUsers with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getATenantUsers(myKwArgs["securityToken"], myKwArgs["tenantName"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
	
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getATenantDBDetails(self, **kwargs):
		"""
		Retrieve tenant database details
		Arguments:
			securityToken
			tenantName
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","tenantName","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getTenantDBDetails with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getTenantDBDetails(myKwArgs["securityToken"], myKwArgs["tenantName"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
	
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def genTenantVerCompReport(self, **kwargs):
		"""
		Add host name and tenants to inventory
		Arguments:
			securityToken
			opco
			dbTechnology
			recepient
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","dbTechnology","recepient","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing reports.genTenantVerCompReport with arguments >>> {myKwArgs}")

			myDBResult = self.reports.genTenantVerCompReport(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"[{myDBResult['message']}]")
			
			#return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)

			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getTenantsInventory(self, **kwargs):
		"""
		Add host name and tenants to inventory
		Arguments:
			securityToken
			opco
			region
			dbTechnology
			env
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","region","dbTechnology","env","status","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, ["output"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "status", "type" : str, "value" : myKwArgs["status"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, ["output"])
			myOutput = ""
			if "output" in myKwArgs:
				if not isinstance(myKwArgs["output"], list):
					myOutput = [myKwArgs["output"]]
				else:
					myOutput = myKwArgs["output"]

			self.LOGGER.info(f"executing repo.getTenantsInventory with arguments >>> {myKwArgs}")

			if myOutput:
				myDBResult = self.repo.getTenantsInventory(myKwArgs["securityToken"], myKwArgs["opco"], myKwArgs["region"], myKwArgs["dbTechnology"], myKwArgs["env"], myKwArgs["status"], myOutput)
			else:
				myDBResult = self.repo.getTenantsInventory(myKwArgs["securityToken"], myKwArgs["opco"], myKwArgs["region"], myKwArgs["dbTechnology"], myKwArgs["env"], myKwArgs["status"])

			#self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAllTenantsName(self, **kwargs):
		"""
		Retrieve all tenants name (id and dbCluster)
		Arguments:
			securityToken
			opco
			region
			dbTechnology
			env
			status
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","region","dbTechnology","env","status","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "status", "type" : str, "value" : myKwArgs["status"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getAllTenantsName with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getAllTenantsName(myKwArgs["securityToken"], myKwArgs["opco"], myKwArgs["region"], myKwArgs["dbTechnology"], myKwArgs["env"], myKwArgs["status"])
			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def newDBChangeReq(self, **kwargs):
		"""
		Add host name and tenants to inventory
		Arguments:
			securityToken
			opco
			dbTechnology
			env
			tenantName
			when
			op
			supportingDoc
			comments
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			myRequiredArgList = ["securityToken","opco","dbTechnology","env","tenantName","when","op","supportingDoc","comments","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]},
				{"arg" : "when", "type" : str, "value" : myKwArgs["when"]},
				{"arg" : "op", "type" : str, "value" : myKwArgs["op"]},
				{"arg" : "supportingDoc", "type" : str, "value" : myKwArgs["supportingDoc"]},
				{"arg" : "comments", "type" : str, "value" : myKwArgs["comments"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.addDBChangeReq with arguments >>> {myKwArgs}")

			myDBResult = self.repo.addDBChangeReq(**myKwArgs)
			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getDBChangeReq(self, **kwargs):
		"""
		Retrieve database change request
		Arguments:
			securityToken
			dbTechnology
			tenantName
			when
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","dbTechnology","tenantName","when","supportingDoc","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, ["when","supportingdoc","userId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]}
			]

			self.util.valArguments2(myArgValidationList, ["when","supportingDoc","userId"])

			self.LOGGER.info(f"executing repo.getDBChangeReq with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getDBChangeReq(**myKwArgs)
			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getHostChangeHist(self, **kwargs):
		"""
		Retrieve Host change history
		Arguments:
			securityToken
			opco
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","hostName","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "hostName", "type" : str, "value" : myKwArgs["hostName"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getHostChangeHist with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getHostChangeHist(myKwArgs["securityToken"], myKwArgs["hostName"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getTenantChangeHist(self, **kwargs):
		"""
		Retrieve Host change history
		Arguments:
			securityToken
			opco
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","tenantName","tenantId","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, ["tenantId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			if "limit" in myKwArgs:
				myLimit = myKwArgs["limit"]
			else:
				myLimit = self.Globals.DEFAULT_LIMIT_HISTORY_OUTPUT

			self.util.valArguments2(myArgValidationList, ["tenantId"])

			self.LOGGER.info(f"executing repo.getTenantChangeHist with arguments >>> {myKwArgs}")

			if "tenantId" in myKwArgs:
				myDBResult = self.repo.getTenantChangeHist(myKwArgs["securityToken"], myKwArgs["tenantName"], myLimit, myKwArgs["tenantId"])
			else:
				myDBResult = self.repo.getTenantChangeHist(myKwArgs["securityToken"], myKwArgs["tenantName"], myLimit)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def decomHost(self, **kwargs):
		"""
		Decom host
		Arguments:
			securityToken
			hostName
			decomDoc
			decomDate
			comments
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments

			myRequiredArgList = ["securityToken","hostName","decomDoc","decomDate","comments","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "hostName", "type" : str, "value" : myKwArgs["hostName"]},
				{"arg" : "decomDoc", "type" : str, "value" : myKwArgs["decomDoc"]},
				{"arg" : "decomDate", "type" : str, "value" : myKwArgs["decomDate"]},
				{"arg" : "comments", "type" : str, "value" : myKwArgs["comments"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.decomHost with arguments >>> {myKwArgs}")

			myDBResult = self.repo.decomHost(**myKwArgs)
			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def decomTenant(self, **kwargs):
		"""
		Decom tenant
		Arguments:
			securityToken
			tenantName
			decomDoc
			decomDate
			comments
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments

			self.sec.validateSecToken(myKwArgs["securityToken"])

			myRequiredArgList = ["securityToken","tenantName","decomDoc","decomDate","comments","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]},
				{"arg" : "decomDoc", "type" : str, "value" : myKwArgs["decomDoc"]},
				{"arg" : "decomDate", "type" : str, "value" : myKwArgs["decomDate"]},
				{"arg" : "comments", "type" : str, "value" : myKwArgs["comments"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.decomTenant with arguments >>> {myKwArgs}")

			myDBResult = self.repo.decomTenant(**myKwArgs)
			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def updateTenant(self, **kwargs):
		"""
		modify tenant attribute i.e. HA/DR/Backup/Usage/URI
		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string )
			:param arg2: tenantName (string )
			:param arg3: haMethod (string )
			:param arg5: backupMethod (string )
			:param arg5: backupServer (string )
			:param arg6: uri (string )
			:param arg6: usage (string )
			:return: json
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				getSchedEvent(securityToken, eventDoc)

		.. note::
			

		.. warning:: 


		.. seealso:: 


		"""			

		try:
			myModuleName = sys._getframe().f_code.co_name
			
			self.LOGGER.debug("got arguments >>> {kwargs}")
			
			myKwArgs = self.util.getACopy(kwargs)

			if not "securityToken" in myKwArgs:
				raise ValueError("missing mandatory arguments 'securityToken' !!!")

			# validating arguments
			self.sec.validateSecToken(myKwArgs["securityToken"])

			myRequiredArgList = ["securityToken","tenantName","haMethod","backupMethod","backupServers","usage","uri","licensingNeeded","userId"]

			# checking for required arguments
			self.util.valArguments(myRequiredArgList, myKwArgs, ["drMethod","drServers","dedicatedFor"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]},
				{"arg" : "haMethod", "type" : str, "value" : myKwArgs["haMethod"]},
				{"arg" : "backupMethod", "type" : str, "value" : myKwArgs["backupMethod"]},
				{"arg" : "backupServers", "type" : str, "value" : myKwArgs["backupServers"]},
				{"arg" : "uri", "type" : str, "value" : myKwArgs["uri"]},
				{"arg" : "usage", "type" : str, "value" : myKwArgs["usage"]},
				{"arg" : "licensingNeeded", "type" : str, "value" : myKwArgs["licensingNeeded"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, ["drMethod","drServers","dedicatedFor"])

			self.LOGGER.info(f"executing repo.updateTenant with arguments >>> {myKwArgs}")

			myDBResult = self.repo.updateTenant(**myKwArgs)
			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getDashboardData(self, **kwargs):
		"""
		Retrieve dashboard data needed for home page
		Arguments:
			securityToken
			opco
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","opco","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getDashboardData with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getDashboardData(**myKwArgs)
			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def buildTenantCompliance(self, **kwargs):
		"""
		Retrieve dashboard data needed for home page
		Arguments:
			securityToken
			opco
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","tenantName","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.buildTenantCompliance with arguments >>> {myKwArgs}")

			myDBResult = self.repo.buildTenantCompliance(myKwArgs["securityToken"], myKwArgs["tenantName"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getLatestTenantCompliance(self, **kwargs):
		"""
		Retrieves latest tenant compliances
		Arguments:
			securityToken
			opco
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","tenantName","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "compStatus", "type" : str, "value" : myKwArgs["compStatus"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getLatestTenantCompliance with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getLatestTenantCompliance(myKwArgs["securityToken"], myKwArgs["opco"], myKwArgs["dbTechnology"], myKwArgs["compStatus"], myKwArgs["tenantName"])

			#self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getATenantCompliance(self, **kwargs):
		"""
		Retrieves tenant compliances for a given run date
		Arguments:
			securityToken
			opco
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","tenantName","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]},
				{"arg" : "runDate", "type" : str, "value" : myKwArgs["runDate"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getATenantCompliance with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getATenantCompliance(myKwArgs["securityToken"], myKwArgs["tenantName"], myKwArgs["runDate"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)


	def getDBEstateData(self, **kwargs):
		"""
		Retrieves tenant compliances for a given run date
		Arguments:
			securityToken
			opco
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getDBEstateData with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getDBEstateData(myKwArgs["securityToken"], myKwArgs["userId"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getDBEstateDecomData(self, **kwargs):
		"""
		Retrieves tenant compliances for a given run date
		Arguments:
			securityToken
			opco
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getDBEstateDecomData with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getDBEstateDecomData(myKwArgs["securityToken"], myKwArgs["userId"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getDBConfigKey(self, **kwargs):
		"""
		Retrieves db config key for a given technology
		Arguments:
			securityToken
			dbTechnology
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","dbTechnology","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getDBConfigKey with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getDBConfigKey(myKwArgs["securityToken"], myKwArgs["dbTechnology"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def searchDBComp(self, **kwargs):
		"""
		Retrieves db config key for a given technology
		Arguments:
			securityToken
			tenants
			searchComp
			searchCompValue
			searchIn
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","tenants","searchComp","searchCompValue","searchIn","userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "tenants", "type" : list, "value" : myKwArgs["tenants"]},
				{"arg" : "searchComp", "type" : str, "value" : myKwArgs["searchComp"]},
				{"arg" : "searchCompValue", "type" : str, "value" : myKwArgs["searchCompValue"]},
				{"arg" : "searchIn", "type" : str, "value" : myKwArgs["searchIn"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.searchDBComp with arguments >>> {myKwArgs}")

			myDBResult = self.repo.searchDBComp(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, json_util.dumps(myDBResult["data"]))

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getScanAuth(self, **kwargs):
		"""
		Retrieves Scan token authentication
		Arguments:
			securityToken
			hostName
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","hostName","userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "hostName", "type" : str, "value" : myKwArgs["hostName"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.__getScanAuth with arguments >>> {myKwArgs}")

			myDBResult = self.repo._Repository__getScanAuth(myKwArgs["securityToken"], myKwArgs["hostName"], myKwArgs["dbTechnology"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getSysConfig(self, **kwargs):
		"""
		Retrieves config details for a given opco
		Arguments:
			securityToken
			opco
			userId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","opco","userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getSysConfig with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getSysConfig(myKwArgs["securityToken"], myKwArgs["opco"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getPendingAppDBs(self, **kwargs):
		"""
		Retrieves Scan token authentication
		Arguments:
			securityToken
			tenantName
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","tenantName","userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "tenantName", "type" : str, "value" : myKwArgs["tenantName"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getPendingAppDBs with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getPendingAppDBs(myKwArgs["securityToken"], myKwArgs["tenantName"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAllAppDetails(self, **kwargs):
		"""
		Returns all app details for a given Opco and db technology

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string)
			:param arg2: opco (string)
			:param arg4: dbTechnology (string)			
			:return: json
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				getAllAppDetails(securityToken, opco, dbTechnology)

		.. note::
			

		.. warning:: 


		.. seealso:: 


		"""		

		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","opco","dbTechnology","userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getAllAppDetails with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getAllAppDetails(myKwArgs["securityToken"], myKwArgs["opco"], myKwArgs["dbTechnology"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAnAppDetails(self, **kwargs):
		"""
		Returns all app details for a given Opco and db technology

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string)
			:param arg2: appId (string)
			:return: json
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				getAnAppDetails(securityToken, appId)

		.. note::
			

		.. warning:: 


		.. seealso:: 


		"""		

		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","appId","userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "appId", "type" : str, "value" : myKwArgs["appId"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getAnAppDetails with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getAnAppDetails(myKwArgs["securityToken"], myKwArgs["appId"])

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getLdapEntityDetails(self, **kwargs):
		"""
		Returns all app details for a given Opco and db technology

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string)
			:param arg2: domain (string)
			:param arg3: entityType (string)
			:param arg4: entity (string)
			:param arg5: userId (string)
			:return: json
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				getLdapEntityDetails(securityToken, domain, entityType, entityValue)

		.. note::
			

		.. warning:: 


		.. seealso:: 


		"""		

		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","domain","searchAttr","entityType","entity","userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "domain", "type" : str, "value" : myKwArgs["domain"]},
				{"arg" : "searchAttr", "type" : str, "value" : myKwArgs["searchAttr"]},
				{"arg" : "entityType", "type" : str, "value" : myKwArgs["entityType"]},
				{"arg" : "entity", "type" : str, "value" : myKwArgs["entity"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getLdapEntityDetails with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getLdapEntityDetails(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def saveUserFeedback(self, **kwargs):
		"""
		Save user feedback/issue/enhancement request

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string)
			:param arg2: category (string)
			:param arg3: response (string)
			:param arg4: userId (string)
			:return: json
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				saveUserFeedback(securityToken, category, response, userId)

		.. note::
			

		.. warning:: 


		.. seealso:: 


		"""		

		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","category","response","userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "category", "type" : str, "value" : myKwArgs["category"]},
				{"arg" : "response", "type" : str, "value" : myKwArgs["response"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.saveUserFeedback with arguments >>> {myKwArgs}")

			myDBResult = self.repo.saveUserFeedback(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))
			
			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getOtherInfo(self, **kwargs):
		"""
		Retrieves other information

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string)
			:return: json
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				getOtherInfo(securityToken)

		.. note::
			

		.. warning:: 


		.. seealso:: 


		"""		

		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getOtherInfo with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getOtherInfo(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def isTenantPortOpenFromRestApi(self, **kwargs):
		"""
		Checks if port is open from REST API server

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string)
			:return: json
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				isTenantPortOpenFromRestApi(securityToken)

		.. note::
			

		.. warning:: 


		.. seealso:: 


		"""		

		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","dbTechnology","userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "portStatus", "type" : str, "value" : myKwArgs["portStatus"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.isTenantPortOpenFromRestApi with arguments >>> {myKwArgs}")

			myDBResult = self.repo.isTenantPortOpenFromRestApi(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getUIUserDetails(self, **kwargs):
		"""
		Returns the details of WWW users

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string)
			:param arg2: wwwUserId (string)
			:param arg3: userId (string)						
			:return: json
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				getUIUserDetails(securityToken, wwwUserId, userId)

		.. note::
			

		.. warning:: 


		.. seealso:: 


		"""		

		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","wwwUserId","userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "wwwUserId", "type" : str, "value" : myKwArgs["wwwUserId"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getUIUserDetails with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getUIUserDetails(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def logSessionRequest(self, **kwargs):
		"""
		Logs user request made in WWW

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string)
			:param arg3: request (dict)
			:param arg3: userId (string)						
			:return: json
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				logSessionRequest(securityToken, request, userId)

		.. note::
			if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
				myRequest.update({"remoteAddr" : request.environ['REMOTE_ADDR']})
				#self.PYTHON_VER = request.get_json
			else:
				myRequest.update({"remoteAddr" : request.environ['HTTP_X_FORWARDED_FOR']})
				#self.REMOTE_ADDR = request.environ['HTTP_X_FORWARDED_FOR'] # if behind a proxy
			# updating access list

			myRequest.update({"accessRoute" : list(request.access_route)})

			request = { 
				"ts" : "",
				"userId" : "",
				"ipAddress" : "",
				"accessRoute" : "",
				"request" : "auth.login/auth.logout/access"
				"route" : "",
				"comments" : ""
			}
		.. warning:: 


		.. seealso:: 


		"""		

		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","request", "userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "request", "type" : dict, "value" : myKwArgs["request"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.logSessionRequest with arguments >>> {myKwArgs}")

			myDBResult = self.repo.logSessionRequest(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			return self.util.buildResponse(self.Globals.success, self.Globals.success)

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getMongoMemUsageData(self, **kwargs):
		"""
		Logs user request made in WWW

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string)
			:param arg2: opco (string)
			:param arg3: env (string)			
			:param arg4: userId (string)
			:return: json
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				getMongoMemUsageData(securityToken, request, userId)

		.. note::
		.. warning:: 
		.. seealso:: 

		"""		

		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			self.LOGGER.debug('validating arguments !!')

			if "securityToken" not in kwargs:
				return self.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.sec.validateSecToken(kwargs["securityToken"])

			myKwArgs = self.util.getACopy(kwargs)

			# checking for required arguments
			myRequiredArgList = ["securityToken","opco", "env", "userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info(f"executing repo.getMongoMemUsageData with arguments >>> {myKwArgs}")

			myDBResult = self.repo.getMongoMemUsageData(**myKwArgs)

			self.LOGGER.debug("db result >> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			myErrorMsg = 'error >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

if __name__ == '__main__':
	print("testing cicd repo class method ....")
	sec = Security()
	mySecToken = sec.authenticate('DMZPROD01\\svc-dev-deploy-app','eXokNzl5NEUzOWdXNCkp')
	api = FactoryApi(mySecToken)

	#request
	#{'securityToken' : '','args' : {}}
	#response

	"""
	API
		transmitScan - Completed
		transmitAudit - Completed
		createNewApp - Completed
		getAppDetailsByID - Completed
		getAppDetailsByName - Completed
		addNewDBVersion - Completed
		updDBVersionEOL - Completed
		getAllVerDetails - Completed
		getABaseVerDetails - Completed
		getAVerDetails - Completed		
		getTenantDetailsRep (by opco/region/technology) -- Completed
		getTenantSmmaryRep (by opco/region/technology) -- Completed
		addRestoreDrill -- Completed
		getRestoreDrillDetails -- Completed		
		addDRTestDetail -- 
		getDRTestDetail -- 
		addDBUserPassChgDetail
		onBoardDBAdmin
		offBoardAdmin
		getRSDetails
		getHostSummary 	(Report summary of all hosts for a given OPCO/REGION/DBTechnology/Version)
			hostname, fs size, cpu, memory, docker dbinstance count, non docker db instance count, docker memory allocation 
			
		getHostTenants
		genMongoAudit -- Completed
		genAdHocAudit -- Completed
		genSuperUserReport -- Completed
		genPasswordComplianceReport
		# ops manager
		getAllAdminUserLists 	--> Completed (report all admin user list from all ops manager deployment)
		getBackupSchedule 		--> report all backup schedule for all deployment in 
		spaceUtilization (for a given tenant and date range)
	"""