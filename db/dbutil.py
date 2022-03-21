from com.mmc.common.singleton import Singleton
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.globals import Globals
from com.mmc.common.security import Security
from com.mmc.db.oraglobals import OracleGlobals

#from cx_Oracle import *

import logging, logging.config, sys, inspect, warnings, cx_Oracle


class DBUtil(object, metaclass=Singleton):
	"""
	db util class for all db technology
	"""
	def __init__(self, securityToken):

		self.securityToken = securityToken

		self.sec = Security()
		#print("validating sec token from mongo", securityToken)
		self.sec.validateSecToken(securityToken)

		self.infra = Infrastructure()
		self.util = Utility()
		self.Globals = Globals()
		self.oraGlobals = OracleGlobals()
		
		self.LOGGER = logging.getLogger(__name__)
		self.LOGGER.info("instantiating DB util class")

		self.CLASS_NAME = self.__class__.__name__
		self.ENVIRONMENT = self.util.getACopy(self.infra.environment)

	def getSqlForTag(self, securityToken, sqlTag, dbVersion=None):
		"""
		returns sql for a given sqlTag (sqlTag is stored in oraGlobals)
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', sqlTag, ',', str(dbVersion)])))

			self.sec.validateSecToken(securityToken)

			if not(sqlTag in self.oraGlobals.SQLS):
				raise ValueError("sql not found for sqltag >>> {tag}".format(tag = sqlTag))

			mySqlTagData = self.oraGlobals.SQLS[sqlTag]

			if not mySqlTagData:
				raise ValueError("sql is missing for sql tag >>> {tag}".format(tag = sqlTag))

			# checking if db version arg is passed
			if dbVersion:
				myVersionTag = str(dbVersion.split('.')[0])
			else:
				myVersionTag = ""

			# got sql tag data, will check if given db version is available, if not will return default sql for given tag
			self.LOGGER.info('sql tag data found for sqltag {tag} >>> {sqlData}'.format(tag = sqlTag, sqlData = mySqlTagData))

			if myVersionTag in mySqlTagData:
				mySql = mySqlTagData[myVersionTag]
				self.LOGGER.debug('sql is avalable for requested db version {ver}'.format(ver = dbVersion))
			else:
				mySql = mySqlTagData['default']
				self.LOGGER.debug('returning default tag sql as db version {ver} tag sql is not avalable'.format(ver = dbVersion))

			return mySql

		except Exception as error:
			self.LOGGER.error('an error occurred while retrieving sql for a tag')
			raise error
