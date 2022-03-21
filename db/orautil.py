from com.mmc.common.singleton import Singleton
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.globals import Globals
from com.mmc.common.security import Security
from com.mmc.db.oraglobals import OracleGlobals

#from cx_Oracle import *

import logging, logging.config, sys, inspect, warnings, cx_Oracle


class OraUtil(object, metaclass=Singleton):
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
		self.LOGGER.info("instantiating Oracle core util class")

		self.CLASS_NAME = self.__class__.__name__
		self.ENVIRONMENT = self.util.getACopy(self.infra.environment)

		self.ORACLE_CLIENT_VERSION = cx_Oracle.clientversion()
		self.CX_ORACLE_VERSION = cx_Oracle.version
		self.CX_ORACLE_BUILDTIME = cx_Oracle.buildtime

	def createDsn(self, host, port, service):
		# create tns/dsn
		return cx_Oracle.makedsn(host,port,service)

	def convert2Date(self, year, month, date):
		# returns datetime object
		return Date(year, month, date)

	def convEpoch2Date(self, epochSeconds):
		# returns datetime object
		return cx_Oracle.DateFromTicks(epochSeconds)

	def convert2TS(self, year, month, date, hour, minute, second):
		#returns datetimeobject
		return Date(year, month, date, hour, minute, second)

	def convEpoch2TS(self, epochSeconds):
		#returns datetimeobject
		return cx_Oracle.DateFromTicks(epochSeconds)

	def mogrify(self, sql, param):
		pass

	def getConnAttr(self, connection):
		myConnObj = self.reverseDNS(connection)
		return(
			{
				"version" : connection.version,
				"user" : connection.username,
				"host" : myConnObj["host"],
				"port" : myConnObj["port"],
				"sid" : myConnObj["sid"],
				"service_name" : myConnObj["service_name"],
				"tns" : connection.tnsentry,
				"encoding" : connection.encoding
			}
		)

	def reverseDNS(self, connection):
		"""
		returns host/port/sid/service_name from connection object, we should use re 
		"""

		myConnectStr = connection.dsn.replace(" ","")
		
		# removing all kw
		myKWList = ["(DESCRIPTION=","(ADDRESS=","ADDRESS_LIST=","(PROTOCOL=TCP)","(CONNECT_DATA="]
		for kw in myKWList:
			myConnectStr = myConnectStr.replace(kw,"")


		print("connect string after replacing kw", myConnectStr)

		# replacing "(" and split it with ")"
		myConnectStr = myConnectStr.replace("(","")
		print("connect string after replacing '(' ", myConnectStr)

		myConnObjList = myConnectStr.split(")")
		print("connect string list after split ", myConnObjList)

		myConnObj = {"host" : "", "port" : "", "sid" : "", "service_name" : ""}
		for obj in myConnObjList:
			if obj.lower().startswith("host"):
				myConnObj.update({"host" : obj.split("=")[1] })

			if obj.lower().startswith("port"):
				myConnObj.update({"port" : obj.split("=")[1] })

			if obj.lower().startswith("sid"):
				myConnObj.update({"sid" : obj.split("=")[1] })

			if obj.lower().startswith("service_name"):
				myConnObj.update({"service_name" : obj.split("=")[1] })

		print("returning conn obj >>>", myConnObj)

		return myConnObj

	def convSqlResult2DictGen(self, sqlCursor):
		"""
		convert cursor's output to dict (key/pair) as a generator, this method should be used when dealing with large sets of data
		"""
		columns = [i[0] for i in sqlCursor.description]
		for row in sqlCursor:
			yield dict(zip(columns, row)) # returning as a generator

		#return [dict(zip(columns, row)) for row in cursor]

	def convSqlResult2Dict(self, sqlCursor):
		"""
		convert cursor's output to dict (key/pair)
		"""

		columns = [i[0] for i in sqlCursor.description]
		myData = [dict(zip(columns, row)) for row in sqlCursor]

		return myData

	def parseSql(self, connection, sqlStatement):
		"""
		parse given sql with connection
		"""
		try:
			with connection.cursor() as cur:
				cur.parse(sqlStatement)

		except cx_Oracle.DatabaseError as error:
			self.LOGGER.error("an error {error} occurred parsing sql >>> {sql}".format(error = str(error), sql = sqlStatement), exc_info = True)
			raise error

	def isValidSql(self, connection, sqlStatement):
		"""
		validating if passed sql is valid sql for a given connection
		"""
		try:
			with connection.cursor() as cur:
				cur.parse(sqlStatement)
				return True

		except cx_Oracle.DatabaseError as error:
			self.LOGGER.error("an error {error} occurred while parsing (invalid) sql >>> {sql}".format(error = str(error), sql = sqlStatement), exc_info = True)
			return False

	def isOraConnAlive(self, connection):
		try:
			connection.ping()
			return True
		except Exception as error:
			return False

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

	def getSqlTagDetails(self, securityToken, sqlTag):
		"""
		returns sql tag details as stored in oraGlobals
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', sqlTag])))

			self.sec.validateSecToken(securityToken)

			if not(sqlTag in self.oraGlobals.SQLS):
				raise ValueError("sql not found for sqltag >>> {tag}".format(tag = sqlTag))

			mySqlTagData = self.oraGlobals.SQLS[sqlTag]

			if not mySqlTagData:
				raise ValueError("sql is missing for sql tag >>> {tag}".format(tag = sqlTag))

			# got sql tag data, will check if given db version is available, if not will return default sql for given tag
			self.LOGGER.info('sql tag data found for sqltag {tag} >>> {sqlData}'.format(tag = sqlTag, sqlData = mySqlTagData))

			return mySqlTagData

		except Exception as error:
			self.LOGGER.error('an error occurred while retrieving sql for a tag')
			raise error
