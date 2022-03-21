from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.security import Security
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.common.globals import Globals

import logging, logging.config, sys, importlib

class Factory(object, metaclass=Singleton):
	def __init__(self, securityToken):
		self.util = Utility()
		self.infra = Infrastructure()
		self.Globals = Globals()

		self.ENVIRONMENT = self.util.getACopy(self.infra.environment)
		#self.PYTHONPATH = self.ENVIRONMENT["root"][""]
		self.FACTORY_METADATA = self.util.getACopy(self.ENVIRONMENT["factory"])

		self.LOGGER = logging.getLogger(__name__)

		try:
			# loading factory metadata
			self.LOGGER.info("loading factory metadata ...")

			self.SECURITY_TOKEN = securityToken
			self.sec = Security()
			self.sec.validateSecToken(securityToken)

			# loading trusted proxies
			from com.mmc.db.postgres_core import PGCore

			if self.util.getEnvKeyVal("ENV") == "prod":
				myPgEnv = self.util.getEnvKeyVal("ENV")
			else:
				myPgEnv = "non-prod"

			# we need repostory info to instantiate PG class
			myPgRepoConn = {
				"user" : self.infra.environment["boot"]["repository"][myPgEnv]["user"],
				"userEncPass" : self.infra.environment["boot"]["repository"][myPgEnv]["userEncPass"],
				"host" : self.infra.environment["boot"]["repository"][myPgEnv]["host"],
				"port" : self.infra.environment["boot"]["repository"][myPgEnv]["port"],
				"database" : self.infra.environment["boot"]["repository"][myPgEnv]["db"]
			}
			#self.pg = PGCore(securityToken, self.PG_REPO["user"], self.PG_REPO["encPass"],self.PG_REPO["host"], self.PG_REPO["port"], self.PG_REPO["db"])

			myPG = PGCore(securityToken)
			myPgConn = myPG.newConnection(securityToken, myPgRepoConn)

			self.TRUSTED_PROXIES = myPG.execSql(securityToken, myPgConn, "select remote_address from app.trusted_proxies;",{})

			self.LOGGER.info("found trusted proxies >>> {proxies}".format(proxies = str(self.TRUSTED_PROXIES)))

			del myPG, myPgConn, myPgRepoConn, myPgEnv

		except Exception as error:
			self.LOGGER.error('an error occurred while instantiating factory _init__ >>> {error}'.format(error = str(error)), exc_info = True)

	def __getRestApiMetadata(self, securityToken, restApiMethod):
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', str(restApiMethod)])))

			self.sec.validateSecToken(securityToken)

			self.LOGGER.debug('factory metadata >> {factory}'.format(factory = str(self.FACTORY_METADATA)))
			if restApiMethod not in self.FACTORY_METADATA:
				raise ValueError("Invalid rest api >>> {restApi}".format(restApi = restApiMethod))

			return self.FACTORY_METADATA[restApiMethod]

		except Exception as error:
			self.LOGGER.error('an error occurred while retrieving api factory metadata >>> {error}'.format(error = str(error)), exc_info = True)
			raise error

	def __validateArgs(self, securityToken, restApiMethod, methodArgDict):
		"""
		validate argument received for factory rest api call
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', str(methodArgDict)])))

			self.sec.validateSecToken(securityToken)

			#myKwArgs = self.util.getACopy(kwargs)

			myFactoryMetadata = self.__getRestApiMetadata(securityToken, restApiMethod)

			myRequiredArgList = myFactoryMetadata["args"]
			#myPassedArgs = list(myKwArgs.keys())

			self.util.valArguments(myRequiredArgList, methodArgDict, [])

		except Exception as error:
			self.LOGGER.error('an error occurred while validating factory api args  >>> {error}'.format(error = str(error)), exc_info = True)
			raise error

	def __loadFactoryCls(self, securityToken, module, cls):
		try:
			self.LOGGER.debug('got arguments >> {args}'.format(args = ''.join([securityToken, ',', module, ',', cls ])))

			self.sec.validateSecToken(securityToken)

			self.LOGGER.info('sys path present during dynamic import of module >>> {sysPath}'.format(sysPath = str(sys.path)))
			print('sys path >>>', sys.path)
			"""
			Ensure module to be loaded does not have extn .py.
			importlib.util module is helpful in debugging the dynamic loading of module
			"""
			print('loading module >>', module)
			myModule = importlib.import_module(module)
			myClsInstance = getattr(myModule, cls)(securityToken)

			return myClsInstance

		except Exception as error:
			self.LOGGER.error('an error occurred while loading api factory module/cls >>> {error}'.format(error = str(error)), exc_info = True)
			raise error

	def __callFactoryMethod(self, securityToken, restApiMetadata, **kwarg):
		"""
		Call factory method as requested
		"""
		try:
			self.LOGGER.debug('got arguments >> {args}'.format(args = ''.join([securityToken, ',', str(restApiMetadata), ',', str(kwargs)] )))

			self.sec.validateSecToken(securityToken)

			myModule = __import__(restApiMetadata['module'])
			myClsInstance = getattr(myModule, restApiMetadata['cls'])
			
			#myCls = self.__loadFactoryMethod(securityToken, restApiMetadata['module'], restApiMetadata['cls'])

			myMethod = getattr(myClsInstance, method)

			myResult = myMethod(**kwarg)

			self.LOGGER.info('returning result >>> {result}'.format(result = str(myResult)))

			return myResult

		except Exception as error:
			self.LOGGER.error('an error occurred while calling factory mehtod {method} >>> {error}'.format(method = str(restApiMetadata), error = str(error)), exc_info = True)
			raise error

	def __validateAccess(self, request):
		"""
		Validates the connection against repository trusted_proxies
		"""
	def __validateRequest(self, request):
		"""
		validate request
		"""
		try:
			self.LOGGER.debug('got arguments >> {args}'.format(args = ''.join([str(request)] )))

			#self.sec.validateSecToken(securityToken)

			# validating request
			if not isinstance(request, dict):
				return self.util.buildResponse(\
					self.Globals.unsuccess, 'cicd_arg_001 - arg validation error (invalid request, expecting json, got >> {got})  !!!'.format(got = str(type(request))) )

			if "securityToken" not in request or "method" not in request or "args" not in request:
				return self.util.buildResponse(\
					self.Globals.unsuccess, 'cicd_arg_002 - arg validation error (Missing mandatory arg - method/securityToken/param) !!!' )

			# if securitytoken,userid is not present in 'args', injecting 
			try:

				# injecting securityToken if missing in args, since we already got securityToken as an argument
				if not "securityToken" in request["args"]:
					request["args"].update({"securityToken" : request["securityToken"]})

				if not "userId" in request["args"]:
					request["args"].update({"userId" : request["userId"]})

			except Exception as error:
				self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
				myResponse = self.util.buildResponse(self.Globals.unsuccess, 'cicd_arg_003 - arg validation error (Missing mandatory arg for method {method}) !!!'.format(method = request['method']) )
				return myResponse

			# validating args
			self.__validateArgs(request["securityToken"], request["method"], request["args"])

		except Exception as error:
			self.LOGGER.error("an error occurred while validating factory request >>> {error}".format(error = str(error)), exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, 'system error - {error}'.format(error = str(error)))

	def processRequest(self, request):
		# process rest api request
		try:
			# validation starts here
			self.LOGGER.debug('got args >>> {args}'.format(args = str(request)))

			self.LOGGER.debug('validating request arguments, request >>'.format(request = str(request)))

			self.__validateRequest(request)
			#print('request >>>', request)

			# generating securitytoke for this request

			# searhing requested method in factory metadata
			self.LOGGER.debug('retrieving rest api metadata for this request')

			myFactoryMeta = self.__getRestApiMetadata(request["securityToken"],request["method"])

			self.LOGGER.debug('got rest api metadata >> {metadata}'.format(metadata = str(myFactoryMeta)))

			myArguments = request["args"]

			self.LOGGER.info('found method in repository, will load/execute as requested')

			# loading requested module
			self.LOGGER.debug('loading module >>> {module}'.format(module = myFactoryMeta['module']))

			myFactoryCls = self.__loadFactoryCls(request['securityToken'], myFactoryMeta['module'], myFactoryMeta['cls'])
			
			# instantiating class
			self.LOGGER.debug('instantiating class >>> {cls}'.format(cls = myFactoryMeta['cls']))

			myFactoryMethod = getattr(myFactoryCls, myFactoryMeta["method"])
			
			# calling factory method
			self.LOGGER.debug('calling method with arg >>> {methodArgs}'.format(methodArgs = ''.join([myFactoryMeta['method'], '<', str(request["args"]), '>'])))

			myRequestArgs = self.util.getACopy(request["args"])

			myResult = myFactoryMethod(**myRequestArgs)

			self.LOGGER.debug('returing execution results >> {result}'.format(result = myResult))

			return myResult

		except Exception as error:
			self.LOGGER.error(f'an error occurred while processing factory request >>> {error}', exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, f'an error occurred while processing factory request >>> {error}')

if __name__ == '__main__':
	mySecToken = "SDFASDFL@#FSDFSDFFWQRT%LKSGKSA:G%_!@#%@#@#FSDGFASDF?<?><:)_+**SDF"
	factory = Factory(mySecToken)
	myRequest = {
		"securityToken" : "SDFASDFL@#FSDFSDFFWQRT%LKSGKSA:G%_!@#%@#@#FSDGFASDF?<?><:)_+**SDF",
		"method" : "getAllDBs",
		"userId" : "u1081706",
		"args" : {
			"region" : "NAM", 
			"opco" : "MARSH", 
			"dbTechnology": 
			"Oracle", 
			"env": "Dev"}
	}
	myResult = factory.processRequest(myRequest)
	print('result >>>', myResult)