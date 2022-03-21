from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.security import Security
from com.mmc.common.globals import Globals

# > 3.x
from urllib.parse import quote_plus
# 2.X
# from urllib import quote_plus

import logging, logging.config, sys, os

class Infrastructure(object, metaclass=Singleton):
	def __init__(self):
		try:
			self.util = Utility()
			self.sec = Security()
			self.Globals = Globals()
			self.environment = {}

			# validating/building path
			#print("bootstraping started @ {now}".format(now = self.util.getCurrentDateTime()))
			print("initializing ... ")
			
			# initializing environment var(s)			
			self.__initEnvironment()

			#validating bootstrap files
			# we should first load bootstrap then pick the file under "suppBotstrapFiles", load the contents of these
			#  files as header specified in environment

			# loading main bootstrap files
			self.environment.update({"app_bootstrap_file" : self.__valBootStrapFile("bootstrap.json")})
			# loading main bootstrap file		
			self.environment["boot"] = self.util.readJsonFile(self.environment["app_bootstrap_file"])

			#self.util.buildPath(self.ENVIRONMENT["boot"]["APP_CONFIG"], self.ENVIRONMENT["boot"]["keyFile"]

			self.environment["boot"].update(\
				{ "KEY_FILE_PATH" : self.util.buildPath(self.environment["app_config_loc"], self.environment["boot"]["keyFile"]) }
			)

			#print(self.environment["boot"])
			
			# checking if any other bootstrap files need to be loaded
			for indx, component in enumerate(self.environment["boot"]["suppBootstrapFiles"]):
				comp = list(component.keys())[0]
				compBootFile = list(component.values())[0]
				compBootFileWPath = self.__valBootStrapFile(compBootFile)
				print("comp boot file", compBootFileWPath)
				self.environment.update({comp : self.util.readJsonFile(compBootFileWPath)})
				self.environment["boot"]["suppBootstrapFiles"][indx].update({comp : compBootFileWPath})

			# changind the log dir as determined in APP_LOG 

			if self.environment["app_log_loc"]:
				# we have found app_log_loc, will use this value for logging destination
				for handler in self.environment["logging"]["handlers"]:
					 if "filename" in self.environment["logging"]["handlers"][handler]:
					 	# found logfile name, will strip the path if specified and then change the path as it is determined in self.environment['app_log_loc']
					 	myLogFileNameInLogging = self.util.getFileName(self.environment["logging"]["handlers"][handler]["filename"])
					 	myLogFileName = self.util.buildPath(self.environment["app_log_loc"], myLogFileNameInLogging)
					 	#print(self.environment["logging"]["handlers"][handler]["filename"])
					 	#self.environment["logging"]["handlers"][handler]["filename"].update({"filename":myLogFileName})
					 	self.environment["logging"]["handlers"][handler].update({"filename":myLogFileName})

			# load current host information
			#self.environment.update({"hostInfo" : self.util.getHostInfo()})
			#self.environment.update({"env" : os.environ})

			# validating configuration
			self.__valConfig()

			# configuring logging, we would need json format for logging
			self.__initLogging()
			self.LOGGER.info("infrastructure is ready")

			# updating current pid to environment variable
			self.environment.update({"myPid" : self.util.getCurrentPID()})

			self.LOGGER.info("my infrastructure information >>> {info}".format(info = str(self.environment)))

			print("infrastrucrure is ready ")

		except Exception as error:
			print("bootstrap error, exiting !!!!")
			raise(error)

	def __repr__(self):
		return "(%s)" % (self.__class__)

	def __str__(self):
		return "(%s)" % (self.__class__)

	def __valBootStrapFile(self, file):
		try:
			# will add config loc as default path if path is missing in bootstrap file name
			if not self.util.getFileDirName(file):
				bootStrapFileWPath = self.util.buildPath(self.environment["app_config_loc"], file)
			else:
				bootStrapFileWPath = file

			if not self.util.isFileExists(bootStrapFileWPath):
				print("boostrap file {file} is missing !!!".format(file=bootStrapFileWPath))
				sys.exit(-1)

			return bootStrapFileWPath

		except Exception as error:
			raise error

	def __initEnvironment(self):
		try:
			# initializing environment
			if not self.util.getEnvKeyVal("APP_NAME"):
				#self.util.setEnvKeyVal("APP_NAME")
				print("APP_NAME environmet is not set, pls ensure setenv.sh is being run or set environment manually, exiting !!!")
				sys.exit(-1)
			else:
				self.environment.update({"app_name" : self.util.getEnvKeyVal("APP_NAME")})

			self.environment.update({"app_home_key" : ''.join([self.environment["app_name"],"_HOME"]) })

			if not self.util.getEnvKeyVal(self.environment["app_home_key"]):
				print("APP_HOME environmet is not set, pls ensure setenv.sh is being run or set environment manually, exiting !!!")
				sys.exit(-1)
			else:
				self.environment.update({"app_home_loc" : self.util.getEnvKeyVal(self.environment["app_home_key"])})
			
			if not self.util.getEnvKeyVal("APP_CONFIG"):
				self.environment.update({"app_config_loc" : self.util.buildPath(self.environment["app_home_loc"],"config")})
				#print("env >>", self.environment)
				self.util.setEnvKeyVal("APP_CONFIG", self.environment["app_config_loc"])
			else:
				#print(str(self.util.getEnvKeyVal("APP_CONFIG")))
				self.environment.update({"app_config_loc" : self.util.getEnvKeyVal("APP_CONFIG")})

			if not self.util.getEnvKeyVal("APP_LOG"):
				self.environment.update({"app_log_loc" : self.util.buildPath(self.environment["app_home_loc"],"logs")})
				#print("env >>", self.environment)
				self.util.setEnvKeyVal("APP_LOG", self.environment["app_log_loc"])
			else:
				#print(str(self.util.getEnvKeyVal("APP_CONFIG")))
				self.environment.update({"app_log_loc" : self.util.getEnvKeyVal("APP_LOG")})

			# we need to set the pythonpath to APP_HOME_LOC/<env>
			
		except Exception as error:
			print(error)
			print("an error occurred while initiailizing environment >>> {error}".format(error = error))
			raise error
			#sys.exit(-1)

	def __valConfig(self):
		# validating required modules
		try:
			print("validating required module(s) ")
			self.__valRequiredModule(self.environment["boot"]["requiredModules"])
		except Exception as error:
			print(str(error))
			

		# check repository db availability
		'''
		try:
			#myConn = MongoClient.connect(self.environment["dbRepositoryURI"])
			print("validating repository database ")

			#myMongoUri = self.__buildRepMongoDBUri()
			
			#myConn = MongoClient(myMongoUri)
			#myServerInfo = myConn.server_info()
			#self.environment["dbConfig"]["repository"]["mongo"]["dbRepositoryUri"] = myMongoUri

		except ConnectionFailure as error:
			print("connection failure error {error} ".format(error=error))
			raise error
			#raise connError
		except ConfigurationError as error:
			print("configuration error {error} ".format(error=error))
			raise error
		except ServerSelectionTimeoutError as error:
			print("server selection timeout error {error} ".format(error=error))
			raise error
			#raise connError
		except OperationFailure as error:
			print("operation failure error {error} ".format(error=error))
			raise error
		except Exception as error:
			#raise error
			print("can not connect to repository database, error >>> {error}".format(error = str(error)))
			raise error
	'''

	def __buildRepMongoDBUri__(self):
		try:
			myRepCfgData = self.util.getACopy(self.environment["dbConfig"]["repository"]["mongo"])

			#with open(self.util.buildPath(self.environment["app_config_loc"], "key")) as keyFile:
			#	key = keyFile.read()

			key = self.sec._Security__getKey(\
				myRepCfgData["owner"]["userId"], \
				self.util.buildPath(self.environment["app_config_loc"], self.environment["boot"]["keyFile"]))

			#print("key", key)
			dec_pass = self.sec._Security__decryptText(key, myRepCfgData["owner"]["encPass"])
			#print("dec_pass",dec_pass)
			if isinstance(dec_pass, bytes):
				dec_pass = dec_pass.decode()

			if myRepCfgData["owner"]["userType"].lower() == "ldap":
				myMongoUri = self.util.getACopy(self.Globals.template["mongoURiLdapTemplate"])
				myRepMongoUri =  myMongoUri.format(\
					userName = quote_plus(myRepCfgData["owner"]["userId"]), userPass = quote_plus(dec_pass), hosts = myRepCfgData["hosts"])
	
			elif myRepCfgData["owner"]["userType"].lower() == "internal":
				myMongoUri = self.util.getACopy(self.Globals.template["mongoUriTemplate"])
				myRepMongoUri =  myMongoUri.format(\
					userName = quote_plus(myRepCfgData["owner"]["userId"]), userPass = quote_plus(dec_pass), hosts = myRepCfgData["hosts"], authDb = myRepCfgData["authDb"], authMech = myRepCfgData["authMech"])

			#, replSetName = myRepCfgRawData["replica_set"]

			if "replicaSet" in self.environment["dbConfig"]["repository"]["mongo"]:
				myRepMongoUri = ''.join([myRepMongoUri, '&replicaSet={repl}'.format(repl= self.environment["dbConfig"]["repository"]["mongo"]["replicaSet"])])

			return myRepMongoUri

		except Exception as error:
			raise error

	def __valRequiredModule(self, moduleList):
		try:
			missingPkgs = []
			print("checking required modules >>> ", str(moduleList))
			for pkg in moduleList:
				try:
					myModule = __import__(pkg)
				except Exception as error:
					#print(str(error))
					missingPkgs.append(pkg)
			if missingPkgs:
				print("missing module(s) >>> {missing}, exiting !!!".format(missing = missingPkgs))
				sys.exit(-1)

		except Exception as err:
			print("an error [{error}] occurred while validating modules ".format(error=err))
			raise error
			sys.exit(-1)

	def __initLogging(self):
		try:
			from com.mmc.common.utility import JsonFormatter
			#self.environment["logging"]
			logging.config.dictConfig(self.environment["logging"])
			#print("logging", self.environment["logging"])
			self.LOGGER = logging.getLogger()
			#print(dir(self.LOGGER))
			self.LOGGER.info("logger is ready")
		except Exception as error:
  			#logging.error("Exception occurred", exc_info=True)
			raise error


if __name__ == "__main__":
	infra = Infrastructure()
	logger = logging.getLogger(__name__)
	logger.info("this is after instantiation")
"""
import logging
import logging.config
import json
ATTR_TO_JSON = ['created', 'filename', 'funcName', 'levelname', 'lineno', 'module', 'msecs', 'msg', 'name', 'pathname', 'process', 'processName', 'relativeCreated', 'thread', 'threadName']
class JsonFormatter:
    def format(self, record):
        obj = {attr: getattr(record, attr)
                  for attr in ATTR_TO_JSON}
        return json.dumps(obj, indent=4)

handler = logging.StreamHandler()
handler.formatter = JsonFormatter()
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.error("Hello")

"""