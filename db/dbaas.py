from com.mmc.common.singleton import Singleton
from com.mmc.common.globals import Globals
from com.mmc.common.utility import Utility
from com.mmc.common.security import Security
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.db.oraglobals import OracleGlobals
from com.mmc.db.oracle_core import OracleCore
from com.mmc.db.orautil import OraUtil
from com.mmc.db.dbutil import DBUtil

#from com.mmc.dbass.dbass_config import DbassConfig

import logging, logging.config, sys


class Dbaas(object, metaclass=Singleton):
	"""
	Dbaas repository methods
	"""
	def __init__(self, securityToken):
		self.SECURITY_TOKEN = securityToken

		self.sec = Security()
		self.infra = Infrastructure()
		self.util = Utility()
		self.Globals = Globals() 
		self.dbGlobals = OracleGlobals()
		self.oraUtil = OraUtil(securityToken)
		self.dbUtil = DBUtil(securityToken)

		# dbass variables (these variable value must match with value stored in dbass)
		self.DB_TECHNOLOGY_ORACLE = 'Oracle'


		#self.SECU
		self.LOGGER = logging.getLogger(__name__)
		self.LOGGER.info("instantiating Oracle core class")

		self.ENVIRONMENT = self.util.getACopy(self.infra.environment)

		# validating dbass config 
		if "dbass" not in self.ENVIRONMENT:
			raise ValueError("missing dbass config in bootstrap !!!")

		if "legacyRepo" not in self.ENVIRONMENT["dbass"]:
			raise ValueError("Dbass boottrap error - missing legacy repo infromation in dbass config !!!")

		# will use following to connect to dbass repo to get metadata
		self.DB_USERID = self.ENVIRONMENT["dbass"]["legacyRepo"]["user"]
		self.DB_ENCPASS = self.ENVIRONMENT["dbass"]["legacyRepo"]["userEncPass"]
		self.DB_TECHNOLOGY = self.ENVIRONMENT["dbass"]["legacyRepo"]["dbTechnology"]
		self.DB_HOST = self.ENVIRONMENT["dbass"]["legacyRepo"]["host"]
		self.DB_PORT = self.ENVIRONMENT["dbass"]["legacyRepo"]["port"]
		self.DB_SERVICE = self.ENVIRONMENT["dbass"]["legacyRepo"]["service"]
		self.DB_CONN_STR = self.ENVIRONMENT["dbass"]["legacyRepo"]["connectStr"]

		self.DEPLOY_USER_PROD = self.ENVIRONMENT["boot"]["deploy"]["oracle"]["prod"]["user"]
		self.DEPLOY_ENCPASS_PROD = self.ENVIRONMENT["boot"]["deploy"]["oracle"]["prod"]["userEncPass"]

		self.DEPLOY_USER_NON_PROD = self.ENVIRONMENT["boot"]["deploy"]["oracle"]["non-prod"]["user"]
		self.DEPLOY_ENCPASS_NON_PROD = self.ENVIRONMENT["boot"]["deploy"]["oracle"]["non-prod"]["userEncPass"]

		if self.DB_TECHNOLOGY.lower() == "oracle":
			#self.db = OracleCore(self.SECURITY_TOKEN, self.DB_USERID, self.DB_ENCPASS, self.DB_CONN_STR)
			self.db = OracleCore(self.SECURITY_TOKEN)
			self.CONN_ARG = {
				"userId" : self.DB_USERID,
				"userEncPass" :  self.DB_ENCPASS,
				"dsn" : self.DB_CONN_STR
			}
			self.ORA_CONN = self.__newDbassConn(self.SECURITY_TOKEN, "python.dbass.oracle.__init__")

			#self.conn = self.db.newConnection(self.SECURITY_TOKEN, self.DB_USERID, self.DB_ENCPASS,self.DB_CONN_STR, 'python.dbass.oracle')

		#if not self.db and self.conn:
		#	raise ValueError("error initializing connection to database for legacy db type >>> {dbtype}".format(dbtype = self.DB_TYPE))

	def __repr__(self):
		return "(%s, %s)" % (self.__class__, self.SECURITY_TOKEN)

	def __str__(self):
		return "(%s, %s)" % (self.__class__, self.SECURITY_TOKEN)

	def __newDbassConn(self, securityToken, connTag):
		"""
		will return new dbass connection and also poplate instance variable 
		"""
		print('initializing connection for >>> {tag}'.format(tag = connTag))

		#myConnection = self.db.newConnection(self.SECURITY_TOKEN, self.DB_USERID, self.DB_ENCPASS,self.DB_CONN_STR, 'python.dbass.oracle.{tag}'.format(tag = connTag))
		myConnArg = self.util.getACopy(self.CONN_ARG)
		myConnArg.update({"tag" : "python.dbass.oracle.{tag}".format(tag = connTag)})

		myConnection = self.db.newConnection(self.SECURITY_TOKEN, myConnArg)

		return myConnection
	
	def getAllApplications(self, **kwargs):
		"""
		Retrieve all database from DBDOC for a given opco, region and db technology
		dbEnv : prod/non-prod
		e.g. getAllApplications(myToken, 'prod','Oracle','MARSH','NAM','Oracle')
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ['securityToken','opco','region','dbTechnology']
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))

			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)

			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)

			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getAllApps', myDBVersion)
			
			mySqlCriteria = {
				"OPCO" : myKwArgs["opco"], 
				"REGION" : myKwArgs["region"], 
				"DB_TECHNOLOGY" : myKwArgs["dbTechnology"]
			}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(mySqlCriteria)))

			myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, mySqlCriteria)

			#self.LOGGER.info("closing connection")

			#self.db.closeConnection(myKwArgs["securityToken"], myConnection)

			self.LOGGER.info("returning results >>> {result}".format(result = myDBResult))

			return myDBResult["data"]
			
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving databases for a given opco/region/technology !!!".format(error = str(error)), exc_info = True)
			raise error

	def getAllAppEnv(self, **kwargs):
		"""
		Returns all environment for a given application
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myRequiredArgList = ['securityToken','opco','region','dbTechnology','appId']

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			self.sec.validateSecToken(myKwArgs['securityToken'])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))

			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)

			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)

			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getAllAppEnvFromRepo', myDBVersion)

			mySqlCriteria = {
				"OPCO" : myKwArgs["opco"], 
				"REGION" : myKwArgs["region"], 
				"DB_TECHNOLOGY" : myKwArgs["dbTechnology"], 
				"APP_ID" : myKwArgs["appId"]
			}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(mySqlCriteria)))

			myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, mySqlCriteria)

			# will remove duplicate env which from results
			#myAllEnv = [env ["ENV"] for env in myDBResult]
			#myAllEnv = {"ENV" : list(set(myAllEnv))}

			self.LOGGER.info("db result >>> {result}".format(result = myDBResult))

			return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error('an error occurred >>> {error}'.format(error = str(error)),exc_info = True)
			raise error

	def __isValidOraDBInstance__donotuse(self, **kwargs):
		"""
		Checks if given Oracld database instance is a valid db instance
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myRequiredArgList = ['securityToken','dbInstance']

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			self.sec.validateSecToken(myKwArgs['securityToken'])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))

			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)

			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'isValidOraDBInstance', myDBVersion)
			myArguments = {"DB_INSTANCE_NAME" : myKwArgs["dbInstance"]}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(myArguments)))

			myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, myArguments)

			#self.LOGGER.info("closing connection")

			#self.db.closeConnection(myKwArgs["securityToken"], myConnection)

			self.LOGGER.info("db result >>> {result}".format(result = myDBResult))

			if myDBResult["data"] and "TOTAL" in myDBResult["data"] and myDBResult["data"]["TOTAL"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error('an error occurred >>> {error}'.format(error = str(error)),exc_info = True)
			raise error

	def isValidOraDBInst(self, **kwargs):
		"""
		Checks if given Oracld database instance is a valid db instance
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myRequiredArgList = ['securityToken','opco','region','appId','hostName','dbInstance','env']

			#myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgList, kwargs, ['connection'])

			self.sec.validateSecToken(kwargs['securityToken'])

			self.LOGGER.info('preparing variable(s) for sql execution')

			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)
			
			"""
			if not ("connection" in kwargs and kwargs["connection"]):
				# validating connection
				myConnection = 
				#myConnection = self.__newDbassConn(kwargs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
			else:
				myConnection = kwargs["connection"]
			"""

			myDBVersion = self.db.getDBVersion(kwargs["securityToken"], self.ORA_CONN)
			mySql = self.dbUtil.getSqlForTag(kwargs["securityToken"], 'isValidOraDBInst', myDBVersion)

			# checking if given dbinstance is valid
			myArguments = {
				"APP_ID" : kwargs["appId"],
				"OPCO" : kwargs["opco"].upper(),
				"REGION" : kwargs["region"].upper(),
				"DB_TECHNOLOGY" : self.Globals.DBASS_TECHNOLOGY_ORACLE,
				"ENV" : kwargs["env"].upper(),
				"HOST_NAME" : kwargs["hostName"]
			}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(myArguments)))

			myDBResult = self.db.execSelectSql(kwargs["securityToken"], self.ORA_CONN, mySql, myArguments)
	
			self.LOGGER.info("db result >>> {result}".format(result = myDBResult))

			"""
			if not ("connection" in kwargs and kwargs["connection"]):
				self.LOGGER.info("closing connection")
				self.db.closeConnection(kwargs["securityToken"], myConnection)
			"""

			# closing connection if we created new connection in this module

			if myDBResult["data"] and "TOTAL" in myDBResult["data"] and myDBResult["data"]["TOTAL"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error('an error occurred >>> {error}'.format(error = str(error)),exc_info = True)
			raise error

	def isValidOraDBSchema(self, **kwargs):
		"""
		Checks if given db technology, instance and shcema is a valid db instance schema
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = str(kwargs)))

			myModule = sys._getframe().f_code.co_name

			myRequiredArgList = ['securityToken','opco','region','appId','hostName','dbInstance','dbSchemas','env']

			#myKwArgs = self.util.getACopy(kwargs) (cant pickle connection object, commenting)

			self.util.valArguments(myRequiredArgList, kwargs, [])

			self.sec.validateSecToken(kwargs['securityToken'])

			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)

			"""
			if not ("connection" in kwargs and kwargs["connection"]):
				#myConnection = self.__newDbassConn(kwargs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
				myConnection = self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)
			else:
				myConnection = kwargs["connection"]
			"""

			# checking if this db instance is valid
			myAppDbInstArg = {
				'securityToken' : kwargs["securityToken"],
				#'connection' : myConnection,
				'opco' : kwargs["opco"].upper(),
				'region' : kwargs["region"].upper(),
				'appId' : kwargs["appId"],
				'hostName' : kwargs["hostName"],
				'dbInstance' : kwargs["dbInstance"],
				'env' : kwargs["env"].upper()
			}

			#if self.isValidOraDBInstance(**myDbInstanceArg):
			if self.isValidOraDBInst(**myAppDbInstArg):
				# db instance is valid
				#myDBConnArgs = {"securityToken" : kwargs["securityToken"], "dbInstance" : kwargs["dbInstance"], "dbTechnology" : self.DB_TECHNOLOGY_ORACLE}
				#myTargetUser, myTargetUserEncPass, myTargetConnectStr = self.getDBConnDetails(**myDBConnArgs)

				#if not (myTargetUser, myTargetUserEncPass, myTargetConnectStr):
				#	return False

				#myConnection = self.db.newConnection(kwargs["securityToken"], myTargetUser, myTargetUserEncPass,myTargetConnectStr, 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
				self.LOGGER.info('db instance is valid, checking db schema ....')

				myDBVersion = self.db.getDBVersion(kwargs["securityToken"], self.ORA_CONN)
				mySql = self.dbUtil.getSqlForTag(kwargs["securityToken"], 'isValidOraDBSchema', myDBVersion)

				#myTargetConn = self.db.newConnection(kwargs["securityToken"], myTargetUser, myTargetUserEncPass, myTargetConnectStr, 'python.dbass.oracle.{curMod}'.format(curMod = myModule))

				mySchemaList = [dbSchemas] if not isinstance(kwargs["dbSchemas"], list) else kwargs["dbSchemas"]

				myValidSchema = True

				for schema in mySchemaList:
					mySqlCriteria = {
						"OPCO" : kwargs["opco"],
						"REGION" : kwargs["region"],
						"APP_ID" : kwargs["appId"],
						"DB_TECHNOLOGY" : self.Globals.DBASS_TECHNOLOGY_ORACLE,
						"DB_INSTANCE" : kwargs["dbInstance"],
						"ENV" : kwargs["env"],
						"HOST_NAME" : kwargs["hostName"],
						"SCHEMA_NAME" : schema
					}

					myDBResult = self.db.execSelectSql(kwargs["securityToken"], self.ORA_CONN, mySql, mySqlCriteria)

					self.LOGGER.info("db results >>> {results}".format(results = str(myDBResult)))

					if myDBResult["data"] and "TOTAL" in myDBResult["data"] and myDBResult["data"]["TOTAL"] == 0:
						myValidSchema = False
						break
				# closing connection if created in this module
				"""
				if not ("connection" in kwargs and kwargs["connection"]):
					self.LOGGER.info("closing connection")
					self.db.closeConnection(kwargs["securityToken"], myConnection)
				"""
				self.LOGGER.info("schema validation >>> {results}".format(results = str(myValidSchema)))
				
				return myValidSchema

			else:
				self.LOGGER.info("db instance is not valid, returing False ")
				return False

		except Exception as error:
			self.LOGGER.error('an error occurred >>> {error}'.format(error = str(error)),exc_info = True)
			raise error

	def getAppInfo(self, **kwargs):
		"""
		Retrieve application info for a given opco/region/app id
		e.g. getAppId(\
			securityToken = 'secToken', 
			opco = 'OPCO',
			region = 'REGION',
			appId = 'appId')
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ['securityToken','opco','region','dbTechnology','appId']
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)

			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
			
			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], "getAnAppDetail", myDBVersion)
			
			mySqlCriteria = {
				"OPCO" : myKwArgs["opco"], 
				"REGION" : myKwArgs["region"], 
				"DB_TECHNOLOGY" : myKwArgs["dbTechnology"], 
				"APP_ID": myKwArgs["appId"]
			}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(mySqlCriteria)))

			myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, mySqlCriteria)

			self.LOGGER.info("returning results >>> {result}".format(result = myDBResult))

			return myDBResult["data"]
			
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving application name for a given opco/region/app id !!!".format(error = str(error)), exc_info = True)
			raise error

	def getAppInfoByAppId(self, **kwargs):
		"""
		Retrieve application info for a given app id
		e.g. getAppId(\
			securityToken = 'secToken', 
			opco = 'OPCO',
			region = 'REGION',
			appId = 'appId')
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ['securityToken','appId']
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)

			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
			
			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], "getAnAppDetailByAppId", myDBVersion)
			
			mySqlCriteria = {"APP_ID": myKwArgs["appId"]}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(mySqlCriteria)))

			myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, mySqlCriteria)

			self.LOGGER.info("returning results >>> {result}".format(result = myDBResult))

			return myDBResult["data"]
			
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving application name for a given opco/region/app id !!!".format(error = str(error)), exc_info = True)
			raise error

	def getAllDBInstances(self, **kwargs):
		"""
		Retrieve all database for a given appId/opco/region/db technology/env
		e.g. getAllDBInstances(\
			securityToken = 'secToken', 
			appId = 'appId',
			opco = 'OPCO',
			region = 'REGION',
			dbTechnology = 'db technology',
			env : 'env')
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ['securityToken','appId','opco','region','dbTechnology','env']
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)

			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
			
			"""
			if myKwArgs["dbEnv"].lower() == 'prod':
				mySqlTag = 'getValidProdDBFromRepo'
			else:
				mySqlTag = 'getValidNonProdDBFromRepo'
			"""

			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], "getAppDBInstance", myDBVersion)
			
			myArguments = {"APP_ID": myKwArgs["appId"], "OPCO" : myKwArgs["opco"].upper(), "REGION" : myKwArgs["region"].upper(), "DB_TECHNOLOGY" : myKwArgs["dbTechnology"], "ENV" : myKwArgs["env"].upper()}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(myArguments)))

			myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, myArguments)

			"""
			self.LOGGER.info("closing connection")

			self.db.closeConnection(myKwArgs["securityToken"], myConnection)
			"""

			self.LOGGER.info("returning results >>> {result}".format(result = myDBResult))

			return myDBResult["data"]
			
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving databases for a given opco/region/technology !!!".format(error = str(error)), exc_info = True)
			raise error

	def getDBConnectStr(self, **kwargs):
		"""
		Retrieve connect string for a given database instance name
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ["securityToken", "opco", "region", "dbTechnology", "hostName", "dbInstance"]
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)

			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)

			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getDBUri', myDBVersion)

			mySqlCriteria = {
				"OPCO" : myKwArgs["opco"], 
				"REGION" : myKwArgs["region"], 
				"DB_TECHNOLOGY" : myKwArgs["dbTechnology"], 
				"HOST_NAME" : myKwArgs["hostName"], 
				"DB_INSTANCE" : myKwArgs["dbInstance"]
			}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(mySqlCriteria)))

			myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, mySqlCriteria)

			"""
			self.LOGGER.info("closing connection")
			self.db.closeConnection(myKwArgs["securityToken"], myConnection)
			"""
			self.LOGGER.info("got db connection info >>> {result}".format(result = myDBResult))

			if myKwArgs["dbTechnology"].lower() == 'oracle':
				if myDBResult["data"] and "CONNECTION_INFO" in myDBResult["data"][0] and myDBResult["data"][0]["CONNECTION_INFO"]:
					# fixing connect str for oracle (remove any char before word '(DESCRIPTION')
					myDBInfo = myDBResult["data"][0]
					myStartPos = myDBInfo["CONNECTION_INFO"].upper().find('(DESCRIPTION')
					myFixedConnStr = myDBInfo["CONNECTION_INFO"][myStartPos:].replace('\r', '').replace('\n', '').replace(' ','')

					myConnectStr = {"connectStr" : myFixedConnStr, "env" : myDBInfo["ENV"]}

					return myConnectStr
			
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving db connection string !!!".format(error = str(error)), exc_info = True)
			raise error

	def getDBConnectStr4DBInst(self, **kwargs):
		"""
		Retrieve connect string for a given opco/region/dbtechnology/db (instance)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ["securityToken","opco","region","dbTechnology","dbInstance"]
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)

			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)

			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getDBUri4DBInst', myDBVersion)

			mySqlCriteria = {
				"OPCO" : myKwArgs["opco"], 
				"REGION" : myKwArgs["region"], 
				"DB_TECHNOLOGY" : myKwArgs["dbTechnology"], 
				"DB_INSTANCE" : myKwArgs["dbInstance"]
			}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(mySqlCriteria)))

			myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, mySqlCriteria)

			"""
			self.LOGGER.info("closing connection")
			self.db.closeConnection(myKwArgs["securityToken"], myConnection)
			"""
			self.LOGGER.info("got db connection info >>> {result}".format(result = myDBResult))

			if myKwArgs["dbTechnology"].lower() == 'oracle':
				if myDBResult["data"] and "CONNECTION_INFO" in myDBResult["data"][0] and myDBResult["data"][0]["CONNECTION_INFO"]:
					# fixing connect str for oracle (remove any char before word '(DESCRIPTION')
					myDBInfo = myDBResult["data"][0]
					myStartPos = myDBInfo["CONNECTION_INFO"].upper().find('(DESCRIPTION')
					myFixedConnStr = myDBInfo["CONNECTION_INFO"][myStartPos:]

					myConnectStr = {"connectStr" : myFixedConnStr, "env" : myDBInfo["ENV"]}

					return myConnectStr
			
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving db connection string !!!".format(error = str(error)), exc_info = True)
			raise error

	def getDBConnDetails(self, **kwargs):
		"""
		returns target db credential (user and enc pass)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ["securityToken", "opco", "region", "dbTechnology", "hostName", "dbInstance"]
			
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			self.LOGGER.info('retrieving target db dsn')
	
			myConnectStrArgs = {
				"securityToken" : myKwArgs["securityToken"], 
				"opco" : myKwArgs["opco"],
				"region" : myKwArgs["region"],
				"dbTechnology" : myKwArgs["dbTechnology"],
				"hostName" : myKwArgs["hostName"], 
				"dbInstance" : myKwArgs["dbInstance"]
			}
			
			myResult = self.getDBConnectStr(**myConnectStrArgs)
			# {"connectStr" : myFixedConnStr, "env" : myDBInfo["ENV"]}
			if not (myResult and "connectStr" in myResult and myResult["connectStr"]):
				raise ValueError("connection string for database {dbInstance} is missing !!! ".format(dbInstance = myKwArgs["dbInstance"]))

			myTargetConnectStr = myResult["connectStr"]
			myTargetEnv = myResult["env"]

			if myTargetEnv.lower() == "prod":
				myTargetUser = self.DEPLOY_USER_PROD
				myTargetUserEncPass = self.DEPLOY_ENCPASS_PROD
			else:
				myTargetUser = self.DEPLOY_USER_NON_PROD
				myTargetUserEncPass = self.DEPLOY_ENCPASS_NON_PROD

			return (myTargetUser, myTargetUserEncPass, myTargetConnectStr)

		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving db conection details !!!".format(error = str(error)), exc_info = True)
			raise error

	def getOraDBSchemas(self, **kwargs):
		"""
		Retrieve all db schemas for a given db name from dbdoc/dbmon
		e.g. getAllOraDBSchemas(myToken, appId, opco, region, dbInstance, env, hostname)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ["securityToken","opco","region","dbTechnology","appId","env","hostName","dbInstance"]
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)

			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getDBInstSchemas', myDBVersion)
			myArguments = {
				"APP_Id" : myKwArgs["appId"],
				"OPCO" : myKwArgs["opco"].upper(),
				"REGION" : myKwArgs["region"].upper(),
				"HOST_NAME" : myKwArgs["hostName"],
				"DB_INSTANCE" : myKwArgs["dbInstance"],
				"DB_TECHNOLOGY" : myKwArgs["dbTechnology"],
				"ENV"  : myKwArgs["env"].upper()
			}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(myArguments)))
			
			myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, myArguments)

			"""
			self.LOGGER.info("closing connection")

			self.db.closeConnection(myKwArgs["securityToken"], myConnection)
			"""

			self.LOGGER.info("returning results >>> {result}".format(result = myDBResult))
			# following is format of data being returned
			# [{'SCHEMA': 'OMCB_PEGAR_OWNER'}, {'SCHEMA': 'QA1_OLTBS00_OWNER'}..]
			return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving db schemas !!!".format(error = str(error)), exc_info = True)
			raise error

	def getOraDBCommonShemas(self, **kwargs):
		"""
		Retrieve all db schemas for a given db name from dbdoc/dbmon
		e.g. getAllOraDBSchemas(myToken, appId, opco, region, dbInstance, env, hostname)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ["securityToken","opco","region","dbTechnology","appId"]
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)

			mySqlCriteria = {
				"APP_Id" : myKwArgs["appId"],
				"OPCO" : myKwArgs["opco"].upper(),
				"REGION" : myKwArgs["region"].upper(),
				"DB_TECHNOLOGY" : myKwArgs["dbTechnology"]
			}

			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getDBInstSchemas', myDBVersion)

			# we need to get all the environment for this app
			
			myAllEnvironment = self.getAllAppEnv(**myKwArgs)
			
			# getting all schemas for all env
			myAllSchemas = []
			
			for env in myAllEnvironment:
				
				mySqlCriteria.update({"ENV" : env["ENV"].upper(), "HOST_NAME" : env["HOST_NAME"], "DB_INSTANCE" : env["DB_INSTANCE"]})

				self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(mySqlCriteria)))
				
				myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, mySqlCriteria)

				myEnvSchemas = [schema ["SCHEMA"] for schema in myDBResult["data"]]

				myAllSchemas.extend(myEnvSchemas)

			myAllSchemas = list(set(myAllSchemas))
			myAllSchemas.sort()

			myAllSchemas = [{"SCHEMA" : schema} for schema in myAllSchemas]

			self.LOGGER.info("returning results >>> {result}".format(result = myAllSchemas))
			return myAllSchemas 

		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving db schemas !!!".format(error = str(error)), exc_info = True)
			raise error

	def __getAllObjects__donotuse_dup(self, **kwargs):
		"""
		Retrieve all objects from a given db/instance and its db/schemas 
		e.g. getAllDBSchemas(myToken, dbName, schemaName)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ["securityToken","dbInstance","schemaName","dbTechnology"]
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			myDBConnArgs = {"securityToken" : myKwArgs["securityToken"], "dbInstance" : myKwArgs["dbInstance"], "dbTechnology" : myKwArgs["dbTechnology"]}
			myTargetUser, myTargetUserEncPass, myTargetConnectStr = self.getDBConnDetails(**myDBConnArgs)

			try:
				self.LOGGER.info('preparing variable(s) for sql execution')

				self.ORA_CONN = self.db.newConnection(myKwArgs["securityToken"], myTargetUser, myTargetUserEncPass,myTargetConnectStr, 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
				myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
				mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getSchemaObj', myDBVersion)
				myArguments = {}

				self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(myArguments)))
				
				myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, {})

				self.LOGGER.info("closing connection")

				self.db.closeConnection(myKwArgs["securityToken"], self.ORA_CONN)

				self.LOGGER.info("returning results >>> {result}".format(result = myDBResult))
				# following is format of data being returned
				# [{'SCHEMA': 'OMCB_PEGAR_OWNER'}, {'SCHEMA': 'QA1_OLTBS00_OWNER'}..]
				return myDBResult 

			except Exception as error:
				raise ValueError("an error << {error} >> occurred while executing sql << {sql} >>!!!".format(error = str(error), sql = mySql) )
		
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving schema objects !!!".format(error = str(error)), exc_info = True)
			raise error
	
	def getOraRoles__donotuse(self, **kwargs):
		"""
		Do not use this method rather OracleCore.execSysMethod(self, securityToken, conn, methodTag, arguments)
		Retrieve all db rols for a given database (roles will be fetched directly from database)
		e.g. getAllRoles(myToken, dbInstance)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ["securityToken","hostName","dbInstance"]
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			myDBConnArgs = {"securityToken" : myKwArgs["securityToken"], "hostName" : myKwArgs["hostName"], "dbInstance" : myKwArgs["dbInstance"], "dbTechnology" : self.DB_TECHNOLOGY_ORACLE}
			myTargetUser, myTargetUserEncPass, myTargetConnectStr = self.getDBConnDetails(**myDBConnArgs)

			try:
				self.LOGGER.info('preparing variable(s) for sql execution')

				self.ORA_CONN = self.db.newConnection(myKwArgs["securityToken"], myTargetUser, myTargetUserEncPass,myTargetConnectStr, 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
				myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
				mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getSchemaObj', myDBVersion)
				myArguments = {}

				myTargetConn = self.db.newConnection(myKwArgs["securityToken"], myTargetUser, myTargetUserEncPass, myTargetConnectStr,'python.dbass.oracle.{curMod}'.format(curMod = myModule))

				myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], myTargetConn, self.dbGlobals.GET_ALL_ROLES_SQL, myArguments)

				self.db.closeConnection(myKwArgs["securityToken"], myTargetConn)

				self.LOGGER.info("db results >>> {results}".format(results = str(myDBResult)))
				
				return myDBResult

			except Exception as error:
				raise ValueError("an error << {error} >> occurred while executing sql << {sql} >>!!!".format(error = str(error), sql = mySql) )
		
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving all roles !!!".format(error = str(error)), exc_info = True)
			raise error

	def getOraSysRoles__donotuse(self, **kwargs):
		"""
		Do not use this method rather OracleCore.execSysMethod(self, securityToken, conn, methodTag, arguments)
		Retrieve all db system rols for a given database (roles will be fetched directly from database)
		e.g. getAllSysRoles(myToken, dbInstance)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ["securityToken","hostName","dbInstance","dbTechnology"]
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			myDBConnArgs = {"securityToken" : myKwArgs["securityToken"], "hostName" : myKwArgs["hostName"], "dbInstance" : myKwArgs["dbInstance"], "dbTechnology" : self.DB_TECHNOLOGY_ORACLE}
			myTargetUser, myTargetUserEncPass, myTargetConnectStr = self.getDBConnDetails(**myDBConnArgs)

			try:
				self.LOGGER.info('preparing variable(s) for sql execution')

				myOraConn = self.db.newConnection(myKwArgs["securityToken"], myTargetUser, myTargetUserEncPass, myTargetConnectStr, 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
				myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], myOraConn)
				mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getAllSysRoles', myDBVersion)

				myTargetConn = self.db.newConnection(myKwArgs["securityToken"], myTargetUser, myTargetUserEncPass, myTargetConnectStr, 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
				myArguments = {}

				myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], myTargetConn, mySql, myArguments)

				self.db.closeConnection(myKwArgs["securityToken"], myTargetConn)

				self.LOGGER.info("db results >>> {results}".format(results = str(myDBResult)))
				
				return myDBResult

			except Exception as error:
				raise ValueError("an error << {error} >> occurred while executing sql << {sql} >>!!!".format(error = str(error), sql = mySql) )
		
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving sys roles !!!".format(error = str(error)), exc_info = True)
			raise error

	def __getAllSchemaPublicRoles__donotuse(self, **kwargs):
		"""
		Retrieve all public roles for a given database (roles will be fetched directly from database)
		e.g. getAllSchemaPublicRoles(myToken, dbInstance)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ['securityToken','dbInstance','dbTechnology']
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			myDBConnArgs = {"securityToken" : myKwArgs["securityToken"], "dbInstance" : myKwArgs["dbInstance"], "dbTechnology" : myKwArgs["dbTechnology"]}
			myTargetUser, myTargetUserEncPass, myTargetConnectStr = self.getDBConnDetails(**myDBConnArgs)

			try:
				self.LOGGER.info('preparing variable(s) for sql execution')

				self.ORA_CONN = self.db.newConnection(myKwArgs["securityToken"], myTargetUser, myTargetUserEncPass,myTargetConnectStr, 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
				myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
				mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getPublicRoles', myDBVersion)

				myTargetConn = self.db.newConnection(myKwArgs["securityToken"], myTargetUser, myTargetUserEncPass, myTargetConnectStr, 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
				myArguments = {}

				myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], myTargetConn, mySql, myArguments)

				self.db.closeConnection(myKwArgs["securityToken"], myTargetConn)

				self.LOGGER.info("db results >>> {results}".format(results = str(myDBResult)))
				
				return myDBResult

			except Exception as error:
				raise ValueError("an error << {error} >> occurred while executing sql << {sql} >>!!!".format(error = str(error), sql = mySql) )
		
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving schema public roles !!!".format(error = str(error)), exc_info = True)
			raise error

	def getOraSchemaRoles__donotuse(self, **kwargs):
		"""
		Do not use this method rather OracleCore.execSysMethod(self, securityToken, conn, methodTag, arguments)
		Retrieve all rols for a given database and schema (roles will be fetched directly from database)
		e.g. getOraSchemaRoles(myToken, dbInstance, schemaName)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))
			myModule = sys._getframe().f_code.co_name

			myRequiredArgs = ["securityToken","hostName","dbInstance","schemaName"]

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			myDBConnArgs = {"securityToken" : myKwArgs["securityToken"], "hostName" : myKwArgs["hostName"], "dbInstance" : myKwArgs["dbInstance"], "dbTechnology" : self.DB_TECHNOLOGY_ORACLE}
			myTargetUser, myTargetUserEncPass, myTargetConnectStr = self.getDBConnDetails(**myDBConnArgs)

			try:
				self.LOGGER.info('preparing variable(s) for sql execution')

				self.ORA_CONN = self.db.newConnection(myKwArgs["securityToken"], myTargetUser, myTargetUserEncPass,myTargetConnectStr, 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
				myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
				mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getSchemaRoles', myDBVersion)

				myTargetConn = self.db.newConnection(myKwArgs["securityToken"], myTargetUser, myTargetUserEncPass, myTargetConnectStr, 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
				myArguments = {"OWNER" : myKwArgs["schemaName"]}

				myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], myTargetConn, mySql, myArguments)

				self.db.closeConnection(myKwArgs["securityToken"], myTargetConn)

				self.LOGGER.info("db results >>> {results}".format(results = str(myDBResult)))
				
				return myDBResult

			except Exception as error:
				raise ValueError("an error << {error} >> occurred while executing sql << {sql} >>!!!".format(error = str(error), sql = mySql) )
		
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving schema roles !!!".format(error = str(error)), exc_info = True)
			raise error

	def getOracSchemaObjs__dnotuse(self, **kwargs):
		"""
		Do not use this method rather OracleCore.execSysMethod(self, securityToken, conn, methodTag, arguments)
		Retrieve all objects for a given schema
		e.g. getAllObjects(myToken, dbInstance, schemaName)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ["securityToken","hostName","dbInstance","schemaName"]
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			myDBConnArgs = {"securityToken" : myKwArgs["securityToken"], "hostName" : myKwArgs["hostName"], "dbInstance" : myKwArgs["dbInstance"]}
			myTargetUser, myTargetUserEncPass, myTargetConnectStr = self.getDBConnDetails(**myDBConnArgs)

			try:
				self.LOGGER.info('preparing variable(s) for sql execution')

				self.ORA_CONN = self.db.newConnection(myKwArgs["securityToken"], myTargetUser, myTargetUserEncPass,myTargetConnectStr, 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
				myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
				mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getSchemaObj', myDBVersion)

				myTargetConn = self.db.newConnection(myKwArgs["securityToken"], myTargetUser, myTargetUserEncPass, myTargetConnectStr, 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
				myArguments = {"OWNER" : myKwArgs["schemaName"]}

				myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], myTargetConn, mySql, myArguments)

				self.db.closeConnection(myKwArgs["securityToken"], myTargetConn)

				self.LOGGER.info("db results >>> {results}".format(results = str(myDBResult)))
				
				return myDBResult

			except Exception as error:
				raise ValueError("an error << {error} >> occurred while executing sql << {sql} >>!!!".format(error = str(error), sql = mySql) )
		
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving schema objects !!!".format(error = str(error)), exc_info = True)
			raise error

	def getAllOraTBSDetails__donotuse(self, **kwargs):
		"""
		Do not use this method rather OracleCore.execSysMethod(self, securityToken, conn, methodTag, arguments)
		Retrieve tablespace details (size, free) for a given tablespace or for all ('ALL')
		e.g. getTBSDetails(myToken, dbInstance, tablespaceName)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))

			myRequiredArgs = ["securityToken","hostName","dbInstance"]
			myModule = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			myDBConnArgs = {"securityToken" : myKwArgs["securityToken"], "hostName" : myKwArgs["hostName"], "dbInstance" : myKwArgs["dbInstance"], "dbTechnology" : myKwArgs["dbTechnology"]}
			myTargetUser, myTargetUserEncPass, myTargetConnectStr = self.getDBConnDetails(**myDBConnArgs)

			try:
				self.LOGGER.info('preparing variable(s) for sql execution')

				self.ORA_CONN = self.db.newConnection(myKwArgs["securityToken"], myTargetUser, myTargetUserEncPass,myTargetConnectStr, 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
				myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
				mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getTBSSizeInfo', myDBVersion)

				myTargetConn = self.db.newConnection(myKwArgs["securityToken"], myTargetUser, myTargetUserEncPass, myTargetConnectStr, 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
				myArguments = {}

				myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], myTargetConn, mySql, myArguments)

				self.db.closeConnection(myKwArgs["securityToken"], myTargetConn)

				self.LOGGER.info("db results >>> {results}".format(results = str(myDBResult)))
				
				return myDBResult

			except Exception as error:
				raise ValueError("an error << {error} >> occurred while executing sql << {sql} >>!!!".format(error = str(error), sql = mySql) )
		
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving tablespace details !!!".format(error = str(error)), exc_info = True)
			raise error

	def getActiveDBAList(self, **kwargs):
		"""
		returns valid dba list
		opco: all/opco name MARS/MERCR/GC
		region: all/nam/emea/apac/latm
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))
			myModule = sys._getframe().f_code.co_name

			myRequiredArgs = ["securityToken"]

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)

			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getAciveAdminList', myDBVersion)
			myArguments = {}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(myArguments)))

			myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, myArguments)

			self.LOGGER.info("closing connection")

			#self.db.closeConnection(myKwArgs["securityToken"], self.ORA_CONN)

			self.LOGGER.info("returning results >>> {result}".format(result = myDBResult))

			return myDBResult["data"]
			
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving active admin lists !!!".format(error = str(error)), exc_info = True)
			raise error

	def getActiveDBAList4DBTech(self, **kwargs):
		"""
		returns valid dba list for a given db technology, need to call adhoc proc (pending)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))
			myModule = sys._getframe().f_code.co_name

			myRequiredArgs = ["securityToken","dbTechnology"]

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)
			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getAciveAdminListForDbTech', myDBVersion)
			myArguments = {"DB_TECHNOLOGY" : dbTechnology}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(myArguments)))

			myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, myArguments)

			#self.LOGGER.info("closing connection")

			#self.db.closeConnection(myKwArgs["securityToken"], myConnection)

			self.LOGGER.info("returning results >>> {result}".format(result = myDBResult))

			return myDBResult["data"]
			
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving inactive admin lists for a given technology !!!".format(error = str(error)), exc_info = True)
			raise error

	def getInActiveDBAList(self, **kwargs):
		"""
		returns all database technology inactive/terminated dba list, need to call adhoc proc (pending)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))
			myModule = sys._getframe().f_code.co_name

			myRequiredArgs = ["securityToken"]

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)

			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getInactiveAdminList', myDBVersion)
			myArguments = {}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(myArguments)))

			myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, myArguments)

			#self.LOGGER.info("closing connection")

			#self.db.closeConnection(myKwArgs["securityToken"], myConnection)

			self.LOGGER.info("returning results >>> {result}".format(result = myDBResult))

			return myDBResult["data"]
			
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving inactive admin lists !!!".format(error = str(error)), exc_info = True)
			raise error

	def getAllDBInstUri(self, **kwargs):
		"""
		Retrieve all database tns from DBDOC
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))
			myModule = sys._getframe().f_code.co_name

			myRequiredArgs = ["securityToken"]

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)
			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getAllDBUri', myDBVersion)
			myArguments = {}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(myArguments)))

			myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, myArguments)

			#self.LOGGER.info("closing connection")

			#self.db.closeConnection(myKwArgs["securityToken"], myConnection)

			self.LOGGER.info("returning results >>> {result}".format(result = myDBResult))

			return myDBResult["data"]
			
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving all database uri !!!".format(error = str(error)), exc_info = True)
			raise error

	def getAllDBInstUri4Tech(self, **kwargs):
		"""
		Retrieve all database tns from DBDOC
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = str(kwargs)))
			
			myModule = sys._getframe().f_code.co_name

			myRequiredArgs = ["securityToken","dbTechnology"]

			myKwArgs = self.util.getACopy(kwargs)

			self.util.valArguments(myRequiredArgs, myKwArgs)

			self.sec.validateSecToken(myKwArgs["securityToken"])

			self.LOGGER.info('preparing variable(s) for sql execution')

			#myConnection = self.__newDbassConn(myKwArgs["securityToken"], 'python.dbass.oracle.{curMod}'.format(curMod = myModule))
			self.ORA_CONN = self.db.validatConnection(self.SECURITY_TOKEN, self.CONN_ARG, "python.dbass.oracle.{tag}".format(tag = myModule), self.ORA_CONN)
			myDBVersion = self.db.getDBVersion(myKwArgs["securityToken"], self.ORA_CONN)
			mySql = self.dbUtil.getSqlForTag(myKwArgs["securityToken"], 'getAllDBValidUri4Tech', myDBVersion)
			myArguments = {"DB_TECHNOLOGY" : myKwArgs["dbTechnology"]}

			self.LOGGER.info('executing sql with arguments >>> {sql}, {args}'.format(sql = mySql, args = str(myArguments)))

			myDBResult = self.db.execSelectSql(myKwArgs["securityToken"], self.ORA_CONN, mySql, myArguments)

			#self.LOGGER.info("closing connection")

			#self.db.closeConnection(myKwArgs["securityToken"], myConnection)

			self.LOGGER.info("returning results >>> {result}".format(result = myDBResult))

			return myDBResult["data"]
			
		except Exception as error:
			self.LOGGER.error("an error << {error} >> occurred while retrieving all database uri for a given technology !!!".format(error = str(error)), exc_info = True)
			raise error

if __name__ == "__main__":
	sec = Security()
	myToken = sec.authenticate('DMZPROD01\\svc-dev-deploy-app','eXokNzl5NEUzOWdXNCkp')

	dbass = Dbaas(myToken)
	"""
	myInactiveDBAList = dbass.getInActiveDBAList(myToken)
	myActiveDBAList = dbass.getActiveDBAList(myToken)
	print("inactive dba pending >>>", myInactiveDBAList)
	"""
	myOpco = 'marsh'
	myRegion = 'nam'

	print('all applications ...')
	myApps = dbass.getAllApplications(**{"securityToken" : myToken, "opco" : myOpco,"region" : myRegion})
	print('All applications >>>', myApps)

	myAppName = 'CANSYS'
	#myAppId = 197
	myDBTechnology = 'Oracle'
	myEnv = "dev"

	print('retrieving application id for >>> {appName}'.format(appName = myAppName))
	myAppId = dbass.getAppId(**{"securityToken" : myToken, "opco" : myOpco,"region" : myRegion, "appId" : myAppId})
	print('application id for >>>', myAppId)

	print('retrieving database instances for app > {app}'.format(app = myAppName))
	myAllDBs = dbass.getAllDBInstances(**{"securityToken" : myToken, "appId" : myAppId, "opco" : myOpco, "region" : myRegion, "dbTechnology" : myDBTechnology, "env" : myEnv})
	print('total {total} databases found for {app} '.format(total = len(myAllDBs), app = ''.join([myAppName, '.', myOpco, '.', myRegion, '.', myDBTechnology])))
	print('databases >>> ', myAllDBs)

	myDBInstance = 'oltd147'
	myHostName = 'usdfw23db26v'

	print('retrieving db schemas for app > {app}'.format(app = ''.join([myOpco,'.',myRegion,'.',myDBTechnology,'.',myEnv,'.', myAppName, '.', str(myAppId), '.', myHostName,'.',myDBInstance])))
	mySchemaResult = dbass.getOraDBSchemas(**{"securityToken" : myToken, "appId" : myAppId, "opco" : myOpco, "region" : myRegion, "hostName" : myHostName, "dbInstance" : myDBInstance, "dbTechnology" : myDBTechnology, "env" : myEnv})
	print('total {total} db/schema found for {app}'.format(total = len(mySchemaResult), app = ''.join([myOpco,'.',myRegion,'.',myDBTechnology,'.',myEnv,'.',myAppId,'.',myHostName,'.',myDBInstance])))
	myAllDBSchemas = [schema["SCHEMA"] for schema in mySchemaResult]
	print('db/schemas >>> ', myAllDBSchemas)

	print('validating instance/schema we got here >> ', myDBInstance, myAllDBSchemas)
	isValidSchema = dbass.isValidOraDBSchema(**{"securityToken" : myToken, "appId" : myAppId, "opco" : myOpco, "region" : myRegion, "hostName" : myHostName, "dbInstance" : myDBInstance, "dbSchemas" : myAllDBSchemas, "env" : myEnv})
	print('Valid schema >>>', isValidSchema)

	print('retrieving connection details >> ', myHostName, myDBInstance, myDBTechnology)
	#"securityToken","hostName","dbInstance","dbTechnology"
	isValidSchema = dbass.getDBConnDetails(**{"securityToken" : myToken, "hostName" : myHostName, "dbInstance" : myDBInstance, "dbTechnology" : myDBTechnology})
	print('connection details >>>', isValidSchema)

"""
myTns = cx_Oracle.makedsn('usfkl21db98v.mrshmc.com',1521,'oltp55')
ora = Dbaas(myToken)
myInactiveDBAList = ora.getInActiveDBAList()
myActiveDBAList = ora.getActiveDBAList()
"""


