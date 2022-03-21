from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.security import Security
from com.mmc.common.infrastructure import Infrastructure
#from com.mmc.common.globals import Globals
from com.mmc.cicd.cicd_globals import CICDGlobals
from com.mmc.cicd.cicd_repo_pg import Repository
from com.mmc.cicd.deploy import Deploy

import logging, logging.config, sys

class FactoryApi(object, metaclass=Singleton):
	def __init__(self, securityToken):

		try:
			self.sec = Security()
			self.util = Utility()
			self.infra = Infrastructure()
			self.Globals = CICDGlobals()
			self.SECURITY_TOKEN=securityToken
			self.ENVIRONMENT = self.util.getACopy(self.infra.environment)

			self.repo = Repository(securityToken)
			#"enabling logging"
			self.LOGGER = logging.getLogger(__name__)
		except Exception as error:
			raise ValueError("an error occurred instantiating object Factory")

		#DbaasGgetAllApps
		# we would need to perform commit after a PG call is completed

	def __getAllAppList_donotuse(self, **kwargs):
		# we dont need this method, this is replaced by getApps4Onboarding 
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name
			myRequiredArgList = ['securityToken', 'opco', 'region']

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			self.sec.validateSecToken(myKwArgs['securityToken'])
			#DbaasGgetAllApps(self, securityToken, region, opco, dbTechnology)
			myDBResult = self.repo.dbaasGetAllApps(myKwArgs['securityToken'], myKwArgs['opco'], myKwArgs['region'])

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			#self.LOGGER.info("returning >> {result}".format(result = str(myDBResult)))

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getApps4Onboarding(self, **kwargs):
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken', 'opco', 'region', 'dbTechnology', 'userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getAllApps4OnBoarding with arguments >>> {args}'.format(args = str(myKwArgs)))

			myDBResult = self.repo.getAllApps4OnBoarding(myKwArgs['securityToken'], myKwArgs['opco'], myKwArgs['region'], myKwArgs['dbTechnology'], myKwArgs['userId'])

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			#self.LOGGER.info("returning >> {result}".format(result = str(myDBResult)))

			#self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAllAppsEnv4OnBoarding(self, **kwargs):
		"""
		Returns all avialble schmeas for given opco/region/db technology/appId
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken', 'opco', 'region','dbTechnology','appId','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs['appId'])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getAllAppsEnv4OnBoarding with arguments >>> {args}'.format(args = str(myKwArgs)))

			myDBResult = self.repo.getAllAppsEnv4OnBoarding(myKwArgs['securityToken'], myKwArgs['opco'], myKwArgs['region'], myKwArgs['dbTechnology'], myAppId, myKwArgs['userId'])

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			#self.LOGGER.info("returning >> {result}".format(result = str(myDBResult)))

			#self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAllAppEnvFromDbaas(self, **kwargs):
		"""
		Returns all app environment from dbaas for a given opco/region/dbtechnology/appid
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken', 'opco', 'region','dbTechnology','appId','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])
			
			myAppId = int(myKwArgs["appId"])
			
			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.self.dbaasGetAllUniqueEnvs(securityToken, opco, region, dbTechnology, appId) with arguments >>> {args}'.format(args = str(myKwArgs)))

			myDBResult = self.repo.dbaasGetAllUniqueEnvs(myKwArgs['securityToken'], myKwArgs['opco'], myKwArgs['region'], myKwArgs['dbTechnology'], myAppId)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			#self.LOGGER.info("returning >> {result}".format(result = str(myDBResult)))

			#self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAppDBInstList(self, **kwargs):
		"""
		returns all database names for a given application 
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken', 'appId','region','opco','dbTechnology','env','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "env", "type" : str, "value" : myKwArgs['env']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.dbaasGetAllDBInst with arguments >>> {args}'.format(args = str(myKwArgs)))

			myDBResult = self.repo.dbaasGetAllDBInst(myKwArgs['securityToken'], myKwArgs['opco'], myKwArgs['region'], myKwArgs['dbTechnology'], myKwArgs['appId'], myKwArgs['env'])

			self.LOGGER.info(" dbresult >> {result}".format(result = str(myDBResult)))

			# we need to return db name, db ver and os 
			if myKwArgs["dbTechnology"].lower() == 'oracle':
				#myDBLists = [''.join([db['DB_INSTANCE_NAME'],':',db['DB_VERSION'], ':', db['PLATFORM_NAME']]) for db in myDBResult]
				myAllDBInstances = [{"dbInstance" : db["DB_INSTANCE"], "hostName" : db["HOST_NAME"], "dbTechnology" : db["DB_TECHNOLOGY"], "prodNonProd" : db["PROD_NONPROD"], "env" : db["ENV"]} for db in myDBResult]

			self.LOGGER.info(" returning >> {result}".format(result = str(myAllDBInstances)))

			#self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myAllDBInstances)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getDBConnectStr(self, **kwargs):
		"""
		returns database connect string for a given opco/region/technology/hostname/dbinstance
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','opco','region','dbTechnology','hostName','dbInstance','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "hostName", "type" : str, "value" : myKwArgs['hostName']},
				{"arg" : "dbInstance", "type" : str, "value" : myKwArgs['dbInstance']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.dbaasGetDBInstURI with arguments >>> {args}'.format(args = str(myKwArgs)))
			
			#dbaasGetDBInstURI(self, securityToken, opco, region, dbTehnology, hostName, dbInstance)

			myDBResult = self.repo.dbaasGetDBInstURI(myKwArgs['securityToken'], myKwArgs['opco'], myKwArgs['region'], myKwArgs['dbTechnology'], myKwArgs['hostName'], myKwArgs['dbInstance'],)
			
			#self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			if myKwArgs["dbTechnology"].lower() == 'oracle':
				if myDBResult and "connectStr" in myDBResult and myDBResult["connectStr"]:
					myDBConnectStr = myDBResult["connectStr"]
					myData = [{"dbUri" : myDBConnectStr}]
					return self.util.buildResponse(self.Globals.success, self.Globals.success, myData)
				else:
					return self.util.buildResponse(self.Globals.unsuccess, 'db instance {dbInstance} connect string is missing '.format(dbInstance = myKwArgs['dbInstance']))

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getDBSchema2Add2App(self, **kwargs):
		"""
		Returns all available schema for a given opco/region/dbTechnology/dbinstance/appId/env
		All available schema from Dbass
		Return :
		application is already onboarded
		{
			"appExists": false,
			"schemas": [
				{"dbSchema": "<schema1>"},
				{"dbSchema": "<schema2>"},
				{"dbSchema": "<schema3>"}]
		}
		application is not onboarded
		{
			"appExists": false,
			"schemas": ["<schema1>","<schema2>","<schema3>"]
		}

		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','opco','region','dbTechnology','appId','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			if myKwArgs["dbTechnology"].lower() == self.Globals.TECHNOLOGY_ORACLE.lower():

				# technology is oracle, calling oracle get db schemas method from repository
				#def getDBSchema2Add2App(self, securityToken, opco, region, dbTechnology, appId, env, hostName, dbInstance)
				
				self.LOGGER.info('executing repo.getDBSchema2Add2App with arguments >>> {args}'.format(args = str(myKwArgs)))

				myDBResult = self.repo.getDBSchema2Add2App(myKwArgs['securityToken'], myKwArgs['opco'], myKwArgs['region'], myKwArgs['dbTechnology'], myAppId)

				self.repo.pg.commit(myKwArgs["securityToken"], self.repo.PG_CONN)

				if not myDBResult:
					mySchemaList = {}
				else:
					myAvailDBSchemaList = [{"dbSchema" : schema} for schema in myDBResult]
					mySchemaList = {"schemas" : myAvailDBSchemaList}

				"""
				if self.repo.isAppExists(myKwArgs['securityToken'], myKwArgs['appId']):
					mySchemaForJira = '; '.join(myAvailDBSchemaList["dbSchema"])
					#mySchemaList = {"appExists" : True, "schemas" : myAvailDBSchemaList["dbSchema"]}
					mySchemaList = {"appExists" : True, "schemas" : {{"dbSchema" : mySchemaForJira}}}
				else:
					mySchemaList = {"appExists" : False, "schemas" : myAvailDBSchemaList}
					#myAvailDBSchemaList.update({"appExists" : False, "schemas" : myAvailDBSchemaList})
				"""
				
			#self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			self.LOGGER.info('returning >>> {result}'.format(result = str(mySchemaList)))

			return self.util.buildResponse(self.Globals.success, self.Globals.success, mySchemaList)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAvailDBSchemaList(self, **kwargs):
		"""
		Returns all available schema for a given opco/region/dbTechnology/dbinstance/appId/env
		If app is already onboarded, will return all schema which is onboarded else get the available (schema common in all env) schema from dbaas
		Return :
		application is already onboarded
		{
			"appExists": false,
			"schemas": [
				{"dbSchema": "<schema1>"},
				{"dbSchema": "<schema2>"},
				{"dbSchema": "<schema3>"}]
		}
		application is not onboarded
		{
			"appExists": false,
			"schemas": ["<schema1>","<schema2>","<schema3>"]
		}

		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','opco','region','dbTechnology','appId','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			if myKwArgs["dbTechnology"].lower() == self.Globals.TECHNOLOGY_ORACLE.lower():

				# technology is oracle, calling oracle get db schemas method from repository
				#def getDBSchema4OnBoarding(self, securityToken, opco, region, dbTechnology, appId, env, hostName, dbInstance)
				
				self.LOGGER.info('executing repo.getDBSchema4OnBoarding with arguments >>> {args}'.format(args = str(myKwArgs)))

				myDBResult = self.repo.getDBSchema4OnBoarding(myKwArgs['securityToken'], myKwArgs['opco'], myKwArgs['region'], myKwArgs['dbTechnology'], myAppId)

				if not myDBResult:
					mySchemaList = {}

				if self.repo.isAppExists(myKwArgs["securityToken"], myKwArgs["appId"]):
					# we have app on boarded returning all schemas as 1 item in array
					mySchemaForJira = '; '.join(myDBResult)
					myAvailDBSchemaList = [{"dbSchema" : mySchemaForJira}]
				else:
					myAvailDBSchemaList = [{"dbSchema" : schema} for schema in myDBResult]
			
				mySchemaList = {"schemas" : myAvailDBSchemaList}
				"""
				if self.repo.isAppExists(myKwArgs['securityToken'], myKwArgs['appId']):
					mySchemaForJira = '; '.join(myAvailDBSchemaList["dbSchema"])
					#mySchemaList = {"appExists" : True, "schemas" : myAvailDBSchemaList["dbSchema"]}
					mySchemaList = {"appExists" : True, "schemas" : {{"dbSchema" : mySchemaForJira}}}
				else:
					mySchemaList = {"appExists" : False, "schemas" : myAvailDBSchemaList}
					#myAvailDBSchemaList.update({"appExists" : False, "schemas" : myAvailDBSchemaList})
				"""
				
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			self.LOGGER.info('returning >>> {result}'.format(result = str(mySchemaList)))

			return self.util.buildResponse(self.Globals.success, self.Globals.success, mySchemaList)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAppDBSchemaLists(self, **kwargs):
		"""
		Returns application schema from dbaas
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','opco','region','dbTechnology','appId','hostName','dbInstance','env','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "hostName", "type" : str, "value" : myKwArgs['appId']},
				{"arg" : "dbInstance", "type" : str, "value" : myKwArgs['appId']},
				{"arg" : "env", "type" : str, "value" : myKwArgs['appId']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			if myKwArgs["dbTechnology"].lower() == self.Globals.TECHNOLOGY_ORACLE.lower():

				# technology is oracle, calling oracle get db schemas method from repository
				# DbaasGetOraDBSchemas(securityToken, appName, opco, region, hostName, dbInstance, dbTechnology, env)
	
				self.LOGGER.info('executing repo.dbaasGetOraDBSchemas with arguments >>> {args}'.format(args = str(myKwArgs)))

				myDBResult = self.repo.dbaasGetOraDBSchemas(myKwArgs['securityToken'], myAppId, myKwArgs['opco'], myKwArgs['region'], myKwArgs['hostName'], myKwArgs["dbInstance"], myKwArgs["dbTechnology"])

				myDBSchemaList = [{"dbSchema" : schema['SCHEMA']} for schema in myDBResult]
	
			self.LOGGER.info('returning >>> {result}'.format(result = str(myDBSchemaList)))

			#self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBSchemaList)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getDbaasAppInfo(self, **kwargs):
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','opco','region','dbTechnology','appId','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.dbaasGetAppInfo with arguments >>> {args}'.format(args = str(myKwArgs)))

			myDBResult = self.repo.dbaasGetAppInfo(myKwArgs['securityToken'], myKwArgs['opco'], myKwArgs['region'], myKwArgs['dbTechnology'], myAppId)

			self.LOGGER.info('returning >>> {result}'.format(result = str(myDBResult)))

			#self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN) this is oracle connection call so not needed

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getCICDAppInfo(self, **kwargs):
		"""
		retrieves app information from cicd

		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','appId','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getAnAppDetails with arguments >>> {args}'.format(args = str(myKwArgs)))

			myAppDetails = self.repo.getAnAppDetails(myKwArgs['securityToken'], myAppId)

			self.LOGGER.info('returning >>> {result}'.format(result = str(myAppDetails)))

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myAppDetails)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def onBoardAppEnv(self, **kwargs):
		'''
		On board new application environment from a given Source (external source is set to Jira).

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = [
				'securityToken','jiraIssueId','appId','opco','region','dbTechnology','deployEnvOrder','env','hostName',
				'dbInstance','connString','dbSchemas','ownerIdList','notificationDL','userId'
			]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "jiraIssueId", "type" : str, "value" : myKwArgs['jiraIssueId']}, 
				{"arg" : "appId", "type" : int, "value" : myAppId}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']},
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "deployEnvOrder", "type" : list, "value" : myKwArgs['deployEnvOrder']},
				{"arg" : "env", "type" : str, "value" : myKwArgs['env']},
				{"arg" : "hostName", "type" : str, "value" : myKwArgs['hostName']},
				{"arg" : "connString", "type" : str, "value" : myKwArgs['connString']},
				{"arg" : "dbInstance", "type" : str, "value" : myKwArgs['dbInstance']},
				{"arg" : "dbSchemas", "type" : list, "value" : myKwArgs['dbSchemas']},
				{"arg" : "ownerIdList", "type" : list, "value" : myKwArgs['ownerIdList']},
				{"arg" : "notificationDL", "type" : list, "value" : myKwArgs['notificationDL']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			# retrieving app name and desc for a given app id from dbaas because Jira is not passing App Name and App Desc
			myDbassAppInfo = self.repo.dbaasGetAppInfo(myKwArgs['securityToken'], myKwArgs['opco'], myKwArgs['region'], myKwArgs['dbTechnology'], myAppId)
			if not myDbassAppInfo:
				raise ValueError("Invalid app id {app} (app not found in DBAAS)".format(app = str(appId)))

			myAppName = myDbassAppInfo[0]["APP_NAME"]
			myAppDesc = myDbassAppInfo[0]["APP_DESC"]

			# now Jira will pass appId and connectstr, commenting below block of codes
			"""
			# we need app id and connect string from Dbaas which is missing from jira call
			myDbaasAppDetail = self.repo.getDbaasAppInfo(myKwArgs['securityToken'], myKwArgs['opco'], myKwArgs['region'], myKwArgs['appName'])
			if not (myDbaasAppDetail and myDbaasAppDetail[0]["APP_ID"]):
				raise ValueError("unable to find app id for app >> {app}".format(app = myKwArgs["appName"]))

			myAppId = myDbaasAppDetail[0]["APP_ID"]

			# connect str
			myConnectStr = self.repo.dbaasGetDBIURIWoHost(myKwArgs['securityToken'], myKwArgs['dbInstance'], myKwArgs['dbTechnology'])	
			if not myConnectStr:
				raise ValueError("unable to find connect str for app >> {}".format("".join([myKwArgs['dbInstance'], ".", myKwArgs['dbTechnology']])))
			"""

			self.LOGGER.info('executing repo.onBoardCicdApp with arguments >>> {args}'.format(args = str(myKwArgs)))

			myDBResult = self.repo.onBoardCicdApp(\
				myKwArgs['securityToken'], 
				myKwArgs['jiraIssueId'],
				myAppId,
				myAppName,
				myAppDesc,
				#myKwArgs['appTag'],
				myKwArgs['opco'].lower(), 
				myKwArgs['region'].lower(), 
				myKwArgs['dbTechnology'].lower(), 
				myKwArgs['deployEnvOrder'], 
				myKwArgs['env'].lower(), 
				myKwArgs['hostName'].lower(), 
				myKwArgs['dbInstance'], 
				myKwArgs['connString'], 
				myKwArgs['dbSchemas'], 
				myKwArgs['ownerIdList'], 
				myKwArgs['notificationDL'], 
				myKwArgs['userId']
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = {}

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def __approveAppEnv__donotuse(self, **kwargs):
		'''
		Approve an application environment

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken', 'jiraIssueId','appId', 'env', 'userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "jiraIssueId", "type" : str, "value" : myKwArgs['jiraIssueId']}, 
				{"arg" : "appId", "type" : int, "value" : myKwArgs['appId']}, 
				{"arg" : "env", "type" : str, "value" : myKwArgs['env']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.approveAppEnv with arguments >>> {args}'.format(args = str(myKwArgs)))

			# need app id for given app name
			#myAppId = self.repo.getAppIdByName(myKwArgs['securityToken'], myKwArgs['appName'])

			#if not myAppId:
			#	raise ValueError("Invalid app {app} (does not exists) !!!".format(app = myKwArgs["appName"]))

			myDBResult = self.repo.approveAppEnv(\
				myKwArgs['securityToken'], 
				myKwArgs['jiraIssueId'], 
				myKwArgs['appId'], 
				myKwArgs['env'].lower(), 
				myKwArgs['userId']
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = {}

			# do we need to add jira comments here? why approve app env success comments was not added
			return self.util.buildResponse(self.Globals.success, 'app < {app} > has been successfully approved by user < {userId} >'.format(app = myKwArgs["appId"], userId = myKwArgs["userId"]), myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def approveChanges(self, **kwargs):
		'''
		Approve an application environment

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken', 'jiraIssueId','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "jiraIssueId", "type" : str, "value" : myKwArgs['jiraIssueId']}, 
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.approveChanges with arguments >>> {args}'.format(args = str(myKwArgs)))

			# need app id for given app name
			#myAppId = self.repo.getAppIdByName(myKwArgs['securityToken'], myKwArgs['appName'])

			#if not myAppId:
			#	raise ValueError("Invalid app {app} (does not exists) !!!".format(app = myKwArgs["appName"]))

			myDBResult = self.repo.approveChanges(\
				myKwArgs['securityToken'], 
				myKwArgs['jiraIssueId'], 
				myKwArgs['userId']
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = {}

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			# do we need to add jira comments here? why approve app env success comments was not added
			return self.util.buildResponse(self.Globals.success, 'Jira issue < {issue} > has been successfully approved by user < {userId} >'.format(issue = myKwArgs['jiraIssueId'], userId = myKwArgs["userId"]), myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def updAppDeployEnvOrder(self, **kwargs):
		'''
		update application deployment env order

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','appId','deployEnvOrder','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "deployEnvOrder", "type" : list, "value" : myKwArgs['deployEnvOrder']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.updAppDeployEnvOrder with arguments >>> {args}'.format(args = str(myKwArgs)))

			myDBResult = self.repo.updAppDeployEnvOrder(myKwArgs["securityToken"], myAppId, myKwArgs["deployEnvOrder"])

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = {}

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, 'app {app} deploy env order updated successfully !!!'.format(app = str(myKwArgs['appId'])), myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def __getMyAllApp_donot_use(self, **kwargs):
		'''
		Retrieves all (pending/active) application for a given userId 

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myRequiredArgList = ['securityToken','userId']
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			self.sec.validateSecToken(myKwArgs['securityToken'])

			self.LOGGER.info('executing repo.getAppDetailedStatus with arguments >>> {args}'.format(args = str(myKwArgs)))

			myDBResult = self.repo.getAppDetailedStatus(\
				myKwArgs['securityToken'], 
				myKwArgs['userId']
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)
	
	# modify onboarded cicd app

	def getMyPendingApp(self, **kwargs):
		'''
		Retrieves all pending application for a given userId 

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','opco','region','dbTechnology','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']},
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getMyAppList with arguments >>> {args}'.format(args = ''.join([str(myKwArgs),',', self.Globals.STATUS_PENDING])))
			
			#getMyAppList(self, securityToken, opco, region, dbTechnology, userId, appStatus = None)

			myDBResult = self.repo.getMyAppList(\
				myKwArgs['securityToken'],
				myKwArgs['opco'],
				myKwArgs['region'],
				myKwArgs['dbTechnology'],				 
				myKwArgs['userId'],
				self.Globals.STATUS_PENDING
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getMyAllApp(self, **kwargs):
		'''
		Retrieves all onboarded (valid status) application for a given userId 

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','opco','region','dbTechnology','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']},
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getMyAppList with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))
			
			#getMyAppList(self, securityToken, opco, region, dbTechnology, userId, appStatus = None)

			myDBResult = self.repo.getMyAppList(\
				myKwArgs['securityToken'],
				myKwArgs['opco'],
				myKwArgs['region'],
				myKwArgs['dbTechnology'],				 
				myKwArgs['userId'],
				self.Globals.STATUS_VALID
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getOnboardedAppEnv(self, **kwargs):
		"""
		retrieves list of env which is onboarded for given opco/region/technolgy/appId

		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','appId','opco','region','dbTechnology','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "appId", "type" : int, "value" : myKwArgs['appId']},
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']},
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getAllAppEnvInUse with arguments >>> {args}'.format(args = str(myKwArgs)))

			# need to validate if user has access to this ap

			myOnboardedAppEnvs = self.repo.getAllAppEnvInUse(myKwArgs['securityToken'], myKwArgs['appId'])

			self.LOGGER.info('returning >>> {result}'.format(result = str(myOnboardedAppEnvs)))

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myOnboardedAppEnvs)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getOnBoardedAppSchemaList(self, **kwargs):
		"""
		retrieves schema list which is on boarded for a given app

		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','appId','opco','region','dbTechnology','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']},
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getOnboardedAppSchema with arguments >>> {args}'.format(args = str(myKwArgs)))

			myDBResult = self.repo.getOnboardedAppSchema(myKwArgs['securityToken'], myAppId)

			myOnboardedAppSchema = [{"dbSchema" : schema} for schema in myDBResult]

			self.LOGGER.info('returning >>> {result}'.format(result = str(myOnboardedAppSchema)))

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myOnboardedAppSchema)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getSchema4OnboardingByAppId(self, **kwargs):
		'''
		Retrieves all schema available for onboarding by app id 

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','appId','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getDBSchema4OnBoardingByAppId with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))
			
			myDBResult = repo.getDBSchema4OnBoardingByAppId(myKwArgs["securityToken"], myAppId, myKwArgs["userId"])

			# Pending
			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def removeAppEnv(self, **kwargs):
		'''
		Remove an existing application environment 

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','jiraIssueId','opco','region','dbTechnology','appId','env','deployEnvOrder','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "jiraIssueId", "type" : str, "value" : myKwArgs['jiraIssueId']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']}, 
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "env", "type" : str, "value" : myKwArgs['env']},
				{"arg" : "deployEnvOrder", "type" : list, "value" : myKwArgs['deployEnvOrder']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.removeAppEnv with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))
			#removeAppEnv(self, securityToken, jiraIssueId, appId, env, userId)
			myDBResult = self.repo.removeAppEnv(myKwArgs["securityToken"], myKwArgs["jiraIssueId"], myAppId, myKwArgs["env"], myKwArgs["deployEnvOrder"], myKwArgs["userId"])

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def addNewSchema2App(self, **kwargs):
		'''
		Add new schema to an onboarded app 

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','jiraIssueId','opco','region','dbTechnology','appId','schemaList','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "jiraIssueId", "type" : str, "value" : myKwArgs['jiraIssueId']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']}, 
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "schemaList", "type" : list, "value" : myKwArgs['schemaList']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.addNewSchema2App with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))

			#addNewSchema2App(self, securityToken, jiraIssueId, appId, schemaList)
			myDBResult = self.repo.addNewSchema2App(myKwArgs["securityToken"], myKwArgs["jiraIssueId"], myAppId, myKwArgs["schemaList"], myKwArgs["userId"])

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def removeSchemaFromApp(self, **kwargs):
		'''
		Remove schmea from an onboarded app 

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','jiraIssueId','opco','region','dbTechnology','appId','schemaList','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "jiraIssueId", "type" : str, "value" : myKwArgs['jiraIssueId']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']}, 
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "schemaList", "type" : list, "value" : myKwArgs['schemaList']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.removeAppEnv with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))
			#removeSchemaFromApp(self, securityToken, jiraIssueId, appId, schemaList)
			myDBResult = self.repo.removeSchemaFromApp(myKwArgs["securityToken"], myKwArgs["jiraIssueId"], myAppId, myKwArgs["schemaList"], myKwArgs["userId"])

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def updAppDeployEnvOrder(self, **kwargs):
		'''
		Updated application deploy environment order 

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','jiraIssueId','opco','region','dbTechnology','appId','deployEnvOrder','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "jiraIssueId", "type" : str, "value" : myKwArgs['jiraIssueId']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']}, 
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "deployEnvOrder", "type" : list, "value" : myKwArgs['deployEnvOrder']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.updAppDeployEnvOrder with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))
			
			#def updAppDeployEnvOrder(self, securityToken, jiraIssueId, appId, deployEnvOrder, userId)
			myDBResult = self.repo.updAppDeployEnvOrder(myKwArgs["securityToken"], myKwArgs["jiraIssueId"], myAppId, myKwArgs["deployEnvOrder"], myKwArgs["userId"])

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	"""
	1. getSchema4OnboardingByAppId
	2. addSchmea2App
	3. removeSchemaFromApp
	4. Remove an enivronmen from exisiting app
	5. Change Deoloyment environment order

	create session request/token

	"""
	# Deployment

	def getAppDeployOrder(self, **kwargs):
		'''
		Returns depoy env order for a given app
		Arguments: 
			securityToken:
			opco
			region
			dbTechnology
			userId

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','appId','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getAppDeployOrder with arguments >>> {args}'.format(args = ''.join([str(myKwArgs),',', self.Globals.STATUS_ACTIVE])))
			
			#getMyAppList(self, securityToken, opco, region, dbTechnology, userId, appStatus = None)

			myDBResult = self.repo.getAppDeployOrder(myKwArgs['securityToken'], myKwArgs['appId'])

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getMyApp4Deployment(self, **kwargs):
		'''
		Returns all active app and 1st environment where deployment will be performed
		Arguments: 
			securityToken:
			opco
			region
			dbTechnology
			userId

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','opco','region','dbTechnology','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs['opco']},
				{"arg" : "region", "type" : str, "value" : myKwArgs['region']},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs['dbTechnology']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getMyAppList with arguments >>> {args}'.format(args = ''.join([str(myKwArgs),',', self.Globals.STATUS_ACTIVE])))
			
			#getMyAppList(self, securityToken, opco, region, dbTechnology, userId, appStatus = None)

			myDBResult = self.repo.getMyAppList(\
				myKwArgs['securityToken'],
				myKwArgs['opco'],
				myKwArgs['region'],
				myKwArgs['dbTechnology'],
				myKwArgs['userId'],
				self.Globals.STATUS_VALID
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getMyAppEnv4Deployment(self, **kwargs):
		'''
		Returns 1st env of an application where deployment can be initiated
		Arguments: 
			securityToken:
			appId:
			userId

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','appId','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs['appId'])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getAppStatusById/repo.getUserDeploy1stEnv with arguments >>> {args}'.format(args = ''.join([str(myKwArgs),',', self.Globals.STATUS_ACTIVE])))

			myAppStatus = self.repo.getAppStatusById(myKwArgs['securityToken'], myAppId)

			if myAppStatus not in self.Globals.STATUS_VALID:
				return self.util.buildResponse(self.Globals.unsuccess, 'app is not in valid state')

			self.LOGGER.info('executing repo.getUserDeploy1stEnv with arguments >>> {args}'.format(args = str(myKwArgs)))
			
			#getMyAppList(self, securityToken, opco, region, dbTechnology, userId, appStatus = None)

			myDBResult = self.repo.getUserDeploy1stEnv(myKwArgs['securityToken'], myKwArgs['appId'])

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, [{"env" : myDBResult}])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAppEnvContact(self, **kwargs):
		'''
		Returns contact details of an application environment
		Arguments: 
			securityToken:
			appId:
			userId

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','appId','env','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "env", "type" : str, "value" : myKwArgs['env']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getAnEnvContactDetails with arguments >>> {args}'.format(args = str(myKwArgs)))
			
			myDBResult = self.repo.getAnEnvContactDetails(myKwArgs['securityToken'], myAppId, myKwArgs['env'])

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAnEnvOwnerContact(self, **kwargs):
		'''
		Returns owner contact details of an application environment
		Arguments: 
			securityToken:
			appId:
			userId

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','appId','env','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "appId", "type" : int, "value" : myAppId},
				{"arg" : "env", "type" : str, "value" : myKwArgs['env']},
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getAnEnvContactByType with arguments >>> {args}'.format(args = str(myKwArgs)))
			
			myDBResult = self.repo.getAnEnvContactByType(myKwArgs['securityToken'], myAppId, myKwArgs['env'], "owner%")

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getMyAppForApproval(self, **kwargs):
		'''
		Retrieves all application which given user is authorized to approve 

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])
			
			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs['securityToken']}, 
				{"arg" : "userId", "type" : str, "value" : myKwArgs['userId']}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getMyAppForApproval with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))

			myDBResult = self.repo.getMyAppForApproval(\
				myKwArgs['securityToken'], 
				myKwArgs['userId']
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def __createNewDeployment(self, **kwargs):
		'''
		Create new deployment for an application 
		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','jiraIssueId','deployId','deploySource','deploySourceData','appId','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]}, 
				{"arg" : "jiraIssueId", "type" : str, "value" : myKwArgs["jiraIssueId"]}, 
				{"arg" : "deployId", "type" : str, "value" : myKwArgs["deployId"]}, 
				{"arg" : "deploySource", "type" : str, "value" : myKwArgs["deploySource"]}, 
				{"arg" : "deploySourceData", "type" : str, "value" : myKwArgs["deploySourceData"]}, 
				{"arg" : "appId", "type" : int, "value" : myAppId}, 
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing deploy.createNewDeployment with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))

			deploy = Deploy(myKwArgs['securityToken'])

			myDBResult = deploy.createNewDeployment(\
				myKwArgs["securityToken"], 
				myKwArgs["jiraIssueId"], 
				myKwArgs["deployId"], 
				myAppId, 
				myKwArgs["userId"],
				myKwArgs["deploySource"], 
				myKwArgs["deploySourceData"]
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			# commiting the transcation as this would leave connection in idle state if not committed (even a select statement needs to close the transaction)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def validateDeployRequest(self, **kwargs):
		'''
		Validate deployment (Validate and create new deployment, if deployment exists reprocess deployment)
		Arguments:
			securityToken : securityToken
			jiraIssueId : jiraIssueId
			deployId : deployId
			deploySource : deploySource
			deploySourceData : deploySourceData
			appId : app id
			userId : user id
		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','jiraIssueId','deployId','deploySource','deploySourceData','appId','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myAppId = int(myKwArgs["appId"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]}, 
				{"arg" : "jiraIssueId", "type" : str, "value" : myKwArgs["jiraIssueId"]}, 
				{"arg" : "deployId", "type" : str, "value" : myKwArgs["deployId"]}, 
				{"arg" : "deploySource", "type" : str, "value" : myKwArgs["deploySource"]}, 
				{"arg" : "deploySourceData", "type" : str, "value" : myKwArgs["deploySourceData"]}, 
				{"arg" : "appId", "type" : int, "value" : myAppId}, 
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing deploy.createNewDeployment with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))

			deploy = Deploy(myKwArgs['securityToken'])

			# checking if deployment exists
			myDeploymentExists = self.repo.isDeploymentExists(myKwArgs["securityToken"], myKwArgs["deployId"])

			if myDeploymentExists:
				self.LOGGER.debug("deployment {deployId} exisit, attempting to reprocess deployment files")
				myDBResult = deploy.reprocessDeployFiles(\
					myKwArgs["securityToken"], 
					myKwArgs["jiraIssueId"], 
					myKwArgs["deployId"],
					myKwArgs["deploySource"],
					myKwArgs["deploySourceData"],
					myKwArgs["userId"]
				)
			else:
				self.LOGGER.debug("attempting to create new deployment {deployId}")
				myDBResult = deploy.createNewDeployment(\
					myKwArgs["securityToken"], 
					myKwArgs["jiraIssueId"], 
					myKwArgs["deployId"], 
					myAppId, 
					myKwArgs["userId"],
					myKwArgs["deploySource"], 
					myKwArgs["deploySourceData"]
				)
			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def isDeploymentExists(self, **kwargs):
		'''
		checks if given deployment exists in cicd repository 

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ["securityToken", "deployId", "userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]}, 
				{"arg" : "deployId", "type" : str, "value" : myKwArgs["deployId"]}, 
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.isDeploymentExists with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))

			myDBResult = self.repo.isDeploymentExists(\
				myKwArgs["securityToken"], 
				myKwArgs["deployId"]
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)			
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getDeployServerDetails(self, **kwargs):
		'''
		Returns server details for a given jira id and environment, this is needed to populate CI in retro CO
		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ["securityToken", "jiraIssueId", "env", "userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])



			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]}, 
				{"arg" : "jiraIssueId", "type" : str, "value" : myKwArgs["jiraIssueId"]}, 
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]}, 
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getDeployServerDetails with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))

			myDBResult = self.repo.getDeployServerDetails(\
				myKwArgs["securityToken"], 
				myKwArgs["jiraIssueId"],
				myKwArgs["env"]							
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))
			
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAnAppEnvDetails(self, **kwargs):
		'''
		Returns an application environment details
		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ["securityToken", "appId", "env", "userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]}, 
				{"arg" : "appId", "type" : int, "value" : myKwArgs["appId"]}, 
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]}, 
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing repo.getAnEnvDetails with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))

			myDBResult = self.repo.getAnEnvDetails(\
				myKwArgs["securityToken"], 
				myKwArgs["appId"],
				myKwArgs["env"]							
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))
			
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def __reprocessDeployFiles(self, **kwargs):
		'''
		reprocess new deployment files 

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ["securityToken", "jiraIssueId", "deployId", "deploySource", "deploySourceData","userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]}, 
				{"arg" : "jiraIssueId", "type" : str, "value" : myKwArgs["jiraIssueId"]}, 
				{"arg" : "deployId", "type" : str, "value" : myKwArgs["deployId"]}, 
				{"arg" : "deploySource", "type" : str, "value" : myKwArgs["deploySource"]}, 
				{"arg" : "deploySourceData", "type" : str, "value" : myKwArgs["deploySourceData"]}, 
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing deploy.reprocessDeployFiles with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))

			deploy = Deploy(myKwArgs['securityToken'])

			myDBResult = deploy.reprocessDeployFiles(\
				myKwArgs["securityToken"], 
				myKwArgs["jiraIssueId"], 
				myKwArgs["deployId"],
				myKwArgs["deploySource"],
				myKwArgs["deploySourceData"],				
				myKwArgs["userId"]
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def cancelDeployment(self, **kwargs):
		'''
		Cancel a deployment which has not yet been started and still in validation steps 

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','jiraIssueId','deployId','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]}, 
				{"arg" : "jiraIssueId", "type" : str, "value" : myKwArgs["jiraIssueId"]}, 
				{"arg" : "deployId", "type" : str, "value" : myKwArgs["deployId"]}, 
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			self.LOGGER.info('executing deploy.cancelDeployment with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))

			deploy = Deploy(myKwArgs['securityToken'])

			myDBResult = deploy.cancelDeployment(\
				myKwArgs["securityToken"], 
				myKwArgs["jiraIssueId"], 
				myKwArgs["deployId"], 
				myKwArgs["userId"]
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def performDeployment(self, **kwargs):
		'''
		Perform a deployment in an environment 

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','jiraIssueId','deployId','env','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]}, 
				{"arg" : "jiraIssueId", "type" : str, "value" : myKwArgs["jiraIssueId"]}, 
				{"arg" : "deployId", "type" : str, "value" : myKwArgs["deployId"]}, 
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]},
				#{"arg" : "extRefDocId", "type" : str, "value" : myKwArgs["extRefDocId"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])

			if myKwArgs["env"].lower() == self.Globals.ENV_PROD.lower():
				if ("extRefDocId" not in myKwArgs) or (not myKwArgs["extRefDocId"]):
					raise ValueError("External reference doc argument is mandatory for deployment in Prod environment !!!")
				else:
					myExtRefDocId = myKwArgs["extRefDocId"]	
			else:
				myExtRefDocId = ""

			self.LOGGER.info('executing deploy.performDeployment with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))

			myDeployData = self.repo.getDeployData(myKwArgs["securityToken"], myKwArgs["deployId"])
			myAppEnvId = self.repo.getAppEnvId(myKwArgs["securityToken"], myDeployData["app_id"], myKwArgs["env"])

			deploy = Deploy(myKwArgs['securityToken'])

			myDBResult = deploy.performDeployment(\
				myKwArgs["securityToken"], 
				myKwArgs["jiraIssueId"], 
				myKwArgs["deployId"],
				myAppEnvId,
				myKwArgs["userId"],
				myExtRefDocId				
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))
		
			if myDBResult["status"] == self.Globals.unsuccess:
				#self.repo.pg.pg.rollback(myKwArgs["securityToken"],self.repo.PG_CONN)
				raise ValueError(myDBResult["message"])

			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult["data"])

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			self.repo.pg.commit(myKwArgs["securityToken"],self.repo.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def testOraSysMethod__(self, **kwargs):
		'''
		Cancel a deployment which has not yet been started and still in validation steps 

		'''
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.sec.validateSecToken(myKwArgs['securityToken'])

			myRequiredArgList = ['securityToken','opco','region','hostName','dbInstance','sysMethod','arguments','userId']

			self.util.valArguments(myRequiredArgList, myKwArgs, ["arguments"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]}, 
				{"arg" : "opco`", "type" : str, "value" : myKwArgs["opco"]}, 
				{"arg" : "region", "type" : str, "value" : myKwArgs["region"]}, 
				#{"arg" : "dbTechnology", "type" : str, "value" : "Oracle"}, 
				{"arg" : "hostName", "type" : str, "value" : myKwArgs["hostName"]}, 
				{"arg" : "dbInstance", "type" : str, "value" : myKwArgs["dbInstance"]}, 
				{"arg" : "sysMethod", "type" : str, "value" : myKwArgs["sysMethod"]},
				{"arg" : "arguments", "type" : dict, "value" : myKwArgs["arguments"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, ["arguments"])

			# creating new connection for this request
			from com.mmc.db.oracle_core import OracleCore
			from com.mmc.db.dbaas import Dbaas

			ora = OracleCore(myKwArgs["securityToken"])
			dbaas = Dbaas(myKwArgs["securityToken"])

			myDBConnArgs = {"securityToken" : myKwArgs["securityToken"], "opco" : myKwArgs["opco"], "region" : myKwArgs["region"], "dbTechnology" : "Oracle", "hostName" : myKwArgs["hostName"], "dbInstance" : myKwArgs["dbInstance"]}

			# retrieving userid, encpass and connectstring (dsn)
			myDeployAdminUser, myDeployAdminEncPass, myTargetConnectStr = dbaas.getDBConnDetails(**myDBConnArgs)
			
			# building dict used in ora.newConnection to get new connection
			myConnectionArg = {
				"userId" : myDeployAdminUser, 
				"userEncPass" : myDeployAdminEncPass, 
				"dsn" : myTargetConnectStr, 
				"tag" : f"python.dbass.oracle.{myModule}"
			}
			
			oraConnection = ora.newConnection(myKwArgs["securityToken"], myConnectionArg)

			self.LOGGER.info('executing OracleCore.execSysMethod with arguments >>> {args}'.format(args = ''.join([str(myKwArgs)])))

			myDBResult = ora.execSysMethod(\
				myKwArgs["securityToken"],
				oraConnection,
				myKwArgs["sysMethod"],
				myKwArgs["arguments"]
			)

			self.LOGGER.info('got result >>> {result}'.format(result = str(myDBResult)))

			if not myDBResult:
				myDBResult = []

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
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