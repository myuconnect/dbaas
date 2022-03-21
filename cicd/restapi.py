from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.security import Security
from com.mmc.common.infrastructure import Infrastructure

from com.mmc.db.postgres_core import PGCore
from com.mmc.common.dbass import Dbass

class RestApi(object, metaclass=Singleton):

	def __init__(Self, securityToken):
		self.util = Utility()
		self.sec = Security()
		self.infra = Infrastructure()
		self.Globals = Globals()

		self.sec.validateSecToken(securityToken)

		self.ENVIRONMENT = self.util.getACopy(self.infra.environment)

		self.pgrepo = PgCore(securityToken)
		self.dbass = Dbass(securityToken)

	def onBoardCICDApp(self, **kwargs):
		# Rest API method to on board application
		try:
			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgs = ["securityToken", "appName", "region", "opco", "technology", "env", "envOwnerList"]

			self.LOGGER.debug("got arguments >>> {args}".format(args = str(myKwargs)))

			# validating required arguments
			self.util.valArguments(myRequiredArgs, myKwargs)

			
		except Exception as error:
			raise error
		pass

	def getAllDBFromRepo(self, securityToken, dbEnv, dbTechnology, opco, region):
		"""
		returns all database from repository for given env (prod/non-prod), db technology, opco and region
		"""
		try:
			myAllDatabases = self.dbass.getAllDBs(securityToken, dbEnv, dbTechnology, opco, region)

		except Exception as error:
			raise error

	def getAppEnv(self, securityToken, appId):
		# return all environment of this applicaion along with status
		pass

	def getAppEnvStatus(self, securityToken, appId, env):
		# return all environment of this applicaion along with status
		pass

	def getAppStatus(self, securityToken, appId):
		# return status of this application
		pass

