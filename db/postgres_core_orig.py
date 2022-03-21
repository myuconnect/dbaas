from com.mmc.common.singleton import Singleton
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.globals import Globals
from com.mmc.common.security import Security
#from psycopg2.extensions import register_adapter

import psycopg2, psycopg2.extras, logging, logging.config, sys, inspect, warnings

class PGCore(object, metaclass=Singleton):
	#def __init__(self, securityToken, userId, userEncPass, host, port, database):
	def __init__(self, securityToken):

		self.util = Utility()
		self.sec = Security()
		self.infra = Infrastructure()
		self.Globals = Globals()

		self.sec.validateSecToken(securityToken)

		self.ENVIRONMENT = self.util.getACopy(self.infra.environment)
		self.__bootStrapPG(securityToken) # populating PG_BOOTSTRAP_CFG
		self.LOGGER = logging.getLogger(__name__)

		self.CUR_ARRAY_SIZE = 1000
		self.MAX_PG_RETRIES = 0 # need to pull setting from pg_init.json section in ENVIRONMENT
		self.CONN_STATUS_READY = psycopg2.extensions.STATUS_READY # this value # is # 1
		self.CONN_STATUS_BEGIN = psycopg2.extensions.STATUS_BEGIN # this value is # 2
		self.CONN_STATUS_PREPARED = psycopg2.extensions.STATUS_PREPARED # this value is # 5

		self.TRAN_STATUS_IDLE = psycopg2.extensions.TRANSACTION_STATUS_IDLE # 0
		self.TRAN_STATUS_ACTIVE = psycopg2.extensions.TRANSACTION_STATUS_ACTIVE # 1
		self.TRAN_STATUS_INTRANS = psycopg2.extensions.TRANSACTION_STATUS_INTRANS # 2
		self.TRAN_STATUS_INERROR = psycopg2.extensions.TRANSACTION_STATUS_INERROR # 3
		self.TRAN_STATUS_UNKNOWN = psycopg2.extensions.TRANSACTION_STATUS_UNKNOWN # 4

		# converting all dict class to json so we can insert/update dict object as json in Postgres
		psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)

		"""
		import psycopg2.extensions
		psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
		psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
		"""

	def __bootStrapPG(self, securityToken):
		"""
		boot straping pg connection, reading config from bootstrap.json -> (pg.json)
		"""
		try:
			self.sec.validateSecToken(securityToken)
			if not "pg" in self.ENVIRONMENT:
				raise ValueError("Bootstrap error, PG config is missing !!")

			self.PG_BOOTSTRAP_CFG = self.ENVIRONMENT["pg"]

		except Exception as error:
			raise error

	def getCurrTransStatus(self, securityToken, pgConn):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken), ",", str(pgConn)])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			# will check if passed connection is a valid connection
			return pgConn.info.transaction_status

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def isValidPGConn(self, securityToken, connection):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken), ',', str(connection)])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			# will check if passed connection is a valid connection
			isValidConn = isinstance(connection, psycopg2.extensions.connection)

			self.LOGGER.debug(f"returning {isValidConn}")

			return isValidConn

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def __setSessionAttr(self, securityToken, pgConn):
		"""
		Sets PG connection attribute as configured in 
		"""
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken)])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			if not( self.getCurrTransStatus(securityToken, pgConn) == self.CONN_STATUS_READY):
				# connection is in progress, would not set session attribute, this has already been set
				return

			for key, val in self.PG_BOOTSTRAP_CFG["connection"].items():
				self.LOGGER.info("setting parameter {param} for this connection to {val}".format(param = key, val = val))
				if key == "autocommit":
					pgConn.autocommit = val
				if key == "client_encoding":
					pgConn.set_client_encoding(val)
				if key == "isolation_level":
					pgConn.set_isolation_level(val)

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def getCurrentDB(self, securityToken, pgConn):
		"""
		Returns current database for current connection. Pls refer to instance var PG_CONN_ATTR for more info on connection
		attribute. 
		"""
		try:
			myDBResult = self.execSelectSql(securityToken, pgConn, "select current_database()")
			return  myDBResult[0]["current_database"]

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def __getConnAttr(self, securityToken, connection):
		try:
			# retrieving connection attribute
			return {
				"current_database" : self.getCurrentDB(securityToken, connection),
				"encoding" : connection.encoding, 
				"autoCommit": connection.autocommit,
				"dsn" : connection.dsn,
				"pid" : connection.get_backend_pid()
			}

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def __setCursorAttr(self, securityToken, cursor):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken), ',', str(cursor)])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			for key, val in self.PG_BOOTSTRAP_CFG["cursor"].items():
				self.LOGGER.info("setting parameter {param} for cursor to {val}".format(param = key, val = val))
				if key == "arraysize":
					cursor.arraysize = val
				if key == "itersize":
					cursor.itersize = val

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def newConnection(self, securityToken, connArg):
		"""
		creates new connection
		"""
		try:
			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			#self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ",", userId, ",", userEncPass, ",", host, ",", str(port), ",", database])))
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ",", str(connArg) ])))

			self.sec.validateSecToken(securityToken)

			myConnArg = self.util.getACopy(connArg)
			
			self.CONN_ARG = self.util.getACopy(connArg)

			"""
			{
				"user" : userId,
				"password" : "",
				"host" : host,
				"port" : port,
				"database" : database
			}
			"""
			
			self.LOGGER.info("creating new connection with arguments >>> {args}".format(args = str(myConnArg)))
			myConnArg.update({"password" : self.sec._Security__decryptText(myConnArg["userEncPass"])})
			# replacing userEncPass with password
			myConnArg.pop("userEncPass")

			myConnection = psycopg2.connect(**myConnArg)
				
			self.LOGGER.info("new connection created >>> {conn}".format(conn = str(myConnection)))

			self.CONN_ORIG_ATTR = self.__getConnAttr(securityToken, myConnection) # storing conn attribute before changing it
			self.LOGGER.info("connection original attribute >>> {attr}".format(attr = str(self.CONN_ORIG_ATTR)))

			#self.__initNewConn(securityToken) # populating self.PG_CONN_INFO

			self.LOGGER.info("setting session attribute ")
			self.__setSessionAttr(securityToken, myConnection)

			self.PG_CONN_ATTR = self.__getConnAttr(securityToken, myConnection) # current connection attribute
			self.LOGGER.info("current connection attribute >>> {attr}".format(attr = str(self.PG_CONN_ATTR)))

			#self.LOGGER.info("creating new connection ...")
			#self.newConnection(securityToken, myConnArg["userEncPass"]) # creating self.PG_CONN

			return myConnection

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def validateConn(self, securityToken, connArg, connection = None):
		"""
		validate the connection, if not alive/closed, recreate the connection
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ",", str(connArg), ",", str(connection) ])))

			self.sec.validateSecToken(securityToken)

			# if conneciton  is not passed, will send a new connection

			if not connection:
				return self.newConnection(securityToken, connArg)

			if not self.isValidPGConn(securityToken, connection):
				raise ValueError(f"Invalid connection object {connection}")
			
			# adding timeout to connection object if none found
			if "connect_timeout" not in connArg:
				connArg.update({"connect_timeout" : 3})

			# closing connection if transaction status is unknown
			myTranStatus = connection.get_transaction_status()

			self.LOGGER.debug(f"current transaction status is {myTranStatus}")

			if myTranStatus == self.TRAN_STATUS_UNKNOWN:
				self.LOGGER.debug("transaction status is unknown, closing")
				# connection lost, closing connection
				connection.close()
				return self.newConnection(securityToken, connArg)

			# checking if connection is alive, if yes then return the same connection object else send a new one

			isConnAlive = self.isPgConnAlive(securityToken, connection)
			
			if isConnAlive:
				# connection is alive, returning same connection  object
				self.LOGGER.debug(f"connection is alive, returning same connection object (not creating new conn obj), connection :{connection}, isConnAlive : {isConnAlive} ")
				self.LOGGER.debug(f"checking isolation level to ensure connection is good [{connection}]")

				try:
					"""
					self.execSql(securityToken, connection, "select 1",{})
					self.LOGGER.debug("passed connection is good, returning same connection object")
					"""
					# if this doesnt work then relaoad the bootstrap.json which will have keep alive set 
					myIsolationLevel = connection.isolation_level
					self.LOGGER.debug(f"current isolation level is {myIsolationLevel}")
					return connection

				except psycopg2.OperationalError as error:
					# this is due to conn was closed by server
					self.LOGGER.debug("passed connection was not good, returning new connection object")
					return self.newConnection(securityToken, connArg)

				except Exception as error:
					self.LOGGER.debug(f"an error occurred while querying the database with [{connection}]")
					raise error
				
			else:
				self.LOGGER.debug(f" connection [{connection}] alive status (isConnAlive : [{isConnAlive}]), closing given connection and returning new conn object ")
				connection.close()
				return self.newConnection(securityToken, connArg)

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def __initNewConn__donotuse(self, securityToken):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken)])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			myConnDB = self.execSelectSql(securityToken, "select current_database()")
			myAvailableDB = self.execSelectSql(securityToken, "select datname from pg_database")
			myDSN = self.PG_CONN.dsn

			self.PG_CONN_INFO = {
				"connectedDB" : myConnDB,
				"availableDB" : myAvailableDB,
				"dsn" : myDSN
			}

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def __closeConnection(self, securityToken, pgConn):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken), ",", pgConn])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			# close the connection if it is open

			if self.isPgConnAlive(securityToken, pgConn):
				if pgConn.status == self.CONN_STATUS_BEGIN:
					raise ValueError("there are uncommitted changes in this transaction, Pls commit/rollback before closing conneciton") 
				self.pgConn.close()

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def resetConnection(self, securityToken, pgConn):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken), ",", str(pgConn)])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			# reset connection, any uncommitted work will be rolledback
			if self.isPgConnAlive(securityToken, pgConn):
				pgConn.reset()

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def commit(self, securityToken, pgConn):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken), ",", str(pgConn) ])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			# reset connection, any uncommitted work will be rolledback
			if pgConn and self.isPgConnAlive(securityToken, pgConn):
				pgConn.commit()

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def rollback(self, securityToken, pgConn):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken), ",", str(pgConn) ])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			# reset connection, any uncommitted work will be rolledback
			if pgConn and self.isPgConnAlive(securityToken, pgConn):
				pgConn.rollback()

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def isPgConnAlive(self, securityToken, connection):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken), ",", str(connection)])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)
			
			if not connection:
				return False
			# psycopg2.InterfaceError: connection already closed
			# connection pooling https://pynative.com/psycopg2-python-postgresql-connection-pooling/
			# check if given connection is closed ?
			if not self.isValidPGConn(securityToken, connection):
				return False
				#raise ValueError(f"Invalid connection object {connection}")

			"""
			if not connection:
				return False
			"""

			# https://github.com/psycopg/psycopg2/blob/9e6c3322d8640bca7007a222973d87d8ea60057c/lib/pool.py#L103

			if not connection.closed:
				status = connection.get_transaction_status()
				#if status in [self.TRAN_STATUS_UNKNOWN, self.TRAN_STATUS_IDLE]: (commenting becuause only unknow connection should ne treated as not alive amnd therefor closed)
				if status in [self.TRAN_STATUS_UNKNOWN]:
					# server connection lost
					#connection.close()
					self.LOGGER.debug(f"connection status is {status}, returning False")
					return False
				else:
					self.LOGGER.debug(f"connection status is {status}, returning True")
					return True
			else:
				self.LOGGER.debug(f"connection is not closed, returning True")
				return True

			""" replacing below block with above
			if connection.closed == 0:
				# client has not closed the connection, checking if connection to db is still alive, sorry performing a trip to DB
				try:
					connection.isolation_level
				except OperationalError as error:
					return False
				except Exception as error:
					return False
				try:
					with connection.cursor() as pgCursor:
						pgCursor.execute('SELECT 1')
				except Exception as error:
					#print('error',error)
					return False
				return True
			else:
				return False
			"""
		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def getConectionStatus(self, securityToken, pgConn):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken), ",", str(pgConn) ])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			# return connection status
			return pgConn.status

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def __parseSqlWBind(self, securityToken, cursor, sqlArg, sqlParamArg):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken)])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			# need param in tuple
			#if isinstance(sqlParamArg, list):
				#return cursor.mogrify(sqlArg, tuple([row[0] for row in sqlParamArg]))
			#	return cursor.mogrify(sqlArg, tuple([row for row in sqlParamArg]))
			#else:
			return cursor.mogrify(sqlArg, sqlParamArg)
				

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def convertResult2Dict(self, securityToken, columns, results):
		"""
		This method converts the resultset from postgres to dictionary
		interates the data and maps the columns to the values in result set and converts to dictionary
		:param columns: List - column names this can be your cursor.description
		:param results: List / Tupple - result set from when query is executed
		:return: list of dictionary- mapped with table column name and to its values
		"""
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken)])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			allResults = []
			columns = [col.name for col in columns]

			if type(results) is list:
				for value in results:
					allResults.append(dict(zip(columns, value)))
			elif type(results) is tuple:
				allResults.append(dict(zip(columns, results)))

			return allResults

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def __convertCur2Dict(self, securityToken, cursorArg):
		"""
		This method converts the resultset from postgres to dictionary
		interates the data and maps the columns to the values in result set and converts to dictionary
		:param columns: List - column names this can be your cursor.description
		:param results: List / Tupple - result set from when query is executed
		:return: list of dictionary- mapped with table column name and to its values
		"""
		try:
			# logging arguments
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken)])))
			myModuleName = sys._getframe().f_code.co_name

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			#if not self.isValidPGConn(cursorArg):
			#	raise valueError("cursor must be a valid postgres cursor")

			myAllColRaw = cursorArg.description
			# checking if we got a result sets
			if myAllColRaw:
				myAllColumns = [col.name for col in myAllColRaw]
				myResults = cursorArg.fetchall()

				myDictResults = []

				if type(myResults) is list:
					for value in myResults:
						myDictResults.append(dict(zip(myAllColumns, value)))
				elif type(myResults) is tuple:
					myDictResults.append(dict(zip(myAllColumns, myResults)))

				return myDictResults

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def execSelectSqlPgDict(self, securityToken, pgConn, sqlArg, sqlParamArg = None ):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken), ",", str(pgConn), sqlArg, ",", str(sqlParamArg)])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			if not sqlArg.lstrip().lower().startswith('select'):
				raise ValueError("Not a valid Select sql, sql must start with SELECT !!!")

			# execute select sql statement and return the result as dict
			if not self.isValidPGConn(securityToken, pgConn):
				raise ValueError("invalid connection !!!")

			for sqlTry in range(0,3):
				# will try maximum 3 time if an error occurred
				try:
					with pgConn.cursor(cursor_factory=psycopg2.extras.DictCursor) as pgCursor:

						# binding argument to sql, if argument passed
						if sqlParamArg:
							pgSql = self.__parseSqlWBind(securityToken, pgCursor, sqlArg, sqlParamArg)
						else:
							pgSql = sqlArg

						self.LOGGER.info("executing pgsql >>> {sql}".format(sql = pgSql))
						
						pgCursor.execute(pgSql)

						self.LOGGER.info("total records found >>> {total}".format(total = str(pgCursor.rowcount)))
						
						myData = pgCursor.fetchall()
						
						break

				except psycopg2.OperationalError:
					self.LOGGER.error(f"an error {error} occurred during execution of sql (transaction abortd), rolling back" , exc_info = True)
					#checking if we reched maximum try
					if i < 3:
						pass
					else:
						raise
				except Exception as error:
					self.LOGGER.error(f"an error {error} occurred during execution of sql (transaction abortd), rolling back" , exc_info = True)
					raise error

			if 'myData' in locals():
				return myData
			else:
				return []

		except psycopg2.errors.InFailedSqlTransaction as error:
			self.LOGGER.error("an error {error} occurred during execution of sql (transaction abortd), rolling back".format(error = str(error)) , exc_info = True)
			self.rollback(securityToken, pgConn)

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred, rolling back aborted transaction ".format(error = str(error)) , exc_info = True)
			self.rollback(securityToken, pgConn)
			raise error

	def execSelectSql(self, securityToken, pgConn, sqlArg, sqlParamArg = None ):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken), ",", str(pgConn), ",", sqlArg, ",", str(sqlParamArg)])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			if not sqlArg.lstrip().lower().startswith('select'):
				raise ValueError("Not a valid Select sql, sql must start with SELECT !!!")

			# execute select sql statement and return the result as dict
			if not self.isValidPGConn(securityToken, pgConn):
				raise ValueError("invalid connection !!!")

			with pgConn.cursor() as pgCursor:

				# binding argument to sql, if argument passed
				if sqlParamArg:
					pgSql = self.__parseSqlWBind(securityToken, pgCursor, sqlArg, sqlParamArg)
				else:
					pgSql = sqlArg

				self.LOGGER.info("setting cursor default attribute ")

				self.__setCursorAttr(securityToken, pgCursor)

				self.LOGGER.info("executing pgsql >>> {sql}".format(sql = pgSql))
				
				pgCursor.execute(pgSql)

				self.LOGGER.info("total records found >>> {total}".format(total = str(pgCursor.rowcount)))
				# converting results to dict

				myData = self.__convertCur2Dict(securityToken, pgCursor)
				return myData

		except psycopg2.errors.InFailedSqlTransaction as error:
			self.LOGGER.error("an error {error} occurred during execution of sql (transaction abortd), rolling back".format(error = str(error)) , exc_info = True)
			self.rollback(securityToken, pgConn)
		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred, rolling back aborted transaction ".format(error = str(error)) , exc_info = True)
			self.rollback(securityToken, pgConn)
			raise error

	def execDMLSql(self, securityToken, pgConn, sqlArg, sqlParamArg = None ):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken), ",", str(pgConn), ",", sqlArg, ",", str(sqlParamArg)])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			if not (sqlArg.lstrip().lower().startswith('insert') or sqlArg.lstrip().lower().startswith('update') or sqlArg.lstrip().lower().startswith('delete')):
				raise ValueError("Not a valid DML sql, sql must start with INSERT/UPDATE/DELETE !!!")


			#if not (sqlArg.lstrip().lower().startswith('update') or sqlArg.lstrip().lower().startswith('delete')):
			#	if 

			# execute select sql statement and return the result as dict
			if not self.isValidPGConn(securityToken, pgConn):
				raise ValueError("invalid connection !!!")

			with pgConn.cursor() as pgCursor:

				# setting cursor specific default attribute
				self.__setCursorAttr(securityToken, pgCursor)

				# binding argument to sql, if argument passed
				if sqlParamArg:
					pgSql = self.__parseSqlWBind(securityToken, pgCursor, sqlArg, sqlParamArg)
				else:
					pgSql = sqlArg

				self.LOGGER.info("executing pgsql >>> {sql}".format(sql = pgSql))
				
				pgCursor.execute(pgSql)

				self.LOGGER.info("total records affected by this sql >>> {total}".format(total = str(pgCursor.rowcount)))

				return self.util.buildResponse(self.Globals.success, self.Globals.success)

		except psycopg2.errors.InFailedSqlTransaction as error:
			self.LOGGER.error("an error {error} occurred during execution of sql (transaction abortd), rolling back".format(error = str(error)) , exc_info = True)
			self.rollback(securityToken, pgConn)

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred, rolling back aborted transaction ".format(error = str(error)) , exc_info = True)
			self.rollback(securityToken, pgConn)
			raise error

	def execSql(self, securityToken, pgConn, sqlArg, sqlParamArg = None, retryCount = 0 ):
		try:

			# logging arguments
			myModuleName = sys._getframe().f_code.co_name
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken), ",", str(pgConn), ",", sqlArg, ",", str(sqlParamArg)])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			# checking if connection is alive, if not will attempt reconnecting 
			if not self.isPgConnAlive(securityToken, pgConn):
				#self.LOGGER.debug("connection is not alive, attempting to reconnect")

				# will try to reconnect if connection argument details are available
				#if 	hasattr(self, 'CONN_ARG'):
				#	self.LOGGER.debug("found connection argument for this connection, attempting to validate connection")
				#	self.validateConn(securityToken, self.CONN_ARG, pgConn)
				#else:
				raise ValueError("Invalid PG connection !!!")

			# execute sql statement
			sqlTry = 0
			for sqlTry in range(0,3):
				# will try maximum 3 time if an error occurred
				try:
					with pgConn.cursor() as pgCursor:

						# setting cursor specific default attribute
						self.__setCursorAttr(securityToken, pgCursor)

						# binding argument to sql, if argument passed
						if sqlParamArg:
							pgSql = self.__parseSqlWBind(securityToken, pgCursor, sqlArg, sqlParamArg)
						else:
							pgSql = sqlArg

						self.LOGGER.info("executing pgsql >>> {sql}".format(sql = pgSql))
						
						pgCursor.execute(pgSql)

						self.LOGGER.info("total records affected by this sql >>> {total}".format(total = str(pgCursor.rowcount)))
							
						myData = self.__convertCur2Dict(securityToken, pgCursor)

						break

				except psycopg2.OperationalError as error:
					self.LOGGER.error(f"an error {error} occurred during execution of sql (transaction abortd), rolling back" , exc_info = True)
					#checking if we reched maximum try
					if sqlTry < 3:
						pass
					else:
						raise
				except Exception as error:
					self.LOGGER.error(f"an error {error} occurred during execution of sql (transaction abortd), rolling back" , exc_info = True)
					raise error

			if 'myData' in locals():
				self.LOGGER.debug(f"returning data >>> {myData}")
				return self.util.buildResponse(self.Globals.success, self.Globals.success, myData)
			else:
				return self.util.buildResponse(self.Globals.success, self.Globals.success, [])

			#http://initd.org/psycopg/docs/errors.html
			# https://pynative.com/psycopg2-python-postgresql-connection-pooling/ # we need connection pooling
		except (psycopg2.DatabaseError, psycopg2.OperationalError) as error:
			self.LOGGER.error(f"an error {error} occurred ", exc_info = True)
			raise error
			""" Need to fix this
			if retryCount >= self.MAX_PG_RETRIES:
				raise error
			else:
				retryCount += 1
				self.LOGGER.error("got error {}. retrying {}".format(str(error).strip(), retryCount))
				self.util.sleep(1)
				self.resetConnection(securityToken, self.PG_CONN)
				self.execSql(securityToken, pgConn, sqlArg, sqlParamArg, retryCount)
			"""
		except psycopg2.errors.InFailedSqlTransaction as error:
			self.LOGGER.error("an error {error} occurred during execution of sql (transaction abortd), rolling back".format(error = str(error)) , exc_info = True)
			self.rollback(securityToken, pgConn)
			raise error

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred, rolling back aborted transaction ".format(error = str(error)) , exc_info = True)
			self.rollback(securityToken, pgConn)
			raise error
			
	def copyDataFromFileToDB(self):
		pass 
		"""
		>>> f = StringIO("42\tfoo\n74\tbar\n")
		>>> cur.copy_from(f, 'test', columns=('num', 'data'))
		>>> cur.execute("select * from test where id > 5;")
		>>> cur.fetchall()
		[(6, 42, 'foo'), (7, 74, 'bar')]
		"""

	def copyDataFromFileToDB(self):
		pass
		#cur.copy_to(sys.stdout, 'test', sep="|")

	def copyExpert(self):
		pass
		#copy_expert(sql, file, size=8192)

	def callProc(self):
		pass
		# call stored proc method

	def is_master(self, securityToken, pgConn):

		"""
		returns if connection is made to primary or standby server
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(securityToken), ",", str(pgConn), ",", sqlArg, ",", str(sqlParamArg)])))

			# validating securityToken
			self.sec.validateSecToken(securityToken)

			# checking if connection is alive, if not will attempt reconnecting 
			if not self.isPgConnAlive(securityToken, pgConn):
				raise ValueError("invalid pg connection >>> {conn}".format(conn = str(pgConn)))

			myDBResult = self.execSql("select pg_is_in_recovery();")

			if row and row[0]:
				return False
			return True

		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred, rolling back aborted transaction ".format(error = str(error)) , exc_info = True)
			raise error

if __name__ == "__main__":
	sec = Security()
	mySecToken = sec.authenticate('DMZPROD01\\svc-dev-deploy-app','eXokNzl5NEUzOWdXNCkp')
	
	pg = PGCore(mySecToken, 'svc-dev-deploy-app', 'eXokNzl5NEUzOWdXNCkp', 'usdf23v0801', 5535, 'deploy_repo')
	
	#result = pg.execDMLSql(mySecToken, 'insert into app.app_owner(app_id, owner_id, status) values (%s, %s, %s)', ('test_app','test_owner','ACTIVE'))
	mysql = 'insert into app.app(name, opco, status) values (%s, %s, %s) returning _id'
	myarg = ('test_app_11','MARS','ACTIVE')
	result = pg.execSql(mySecToken, mysql, myarg)
	print('insert result >>>', result)
	pg.commit(mySecToken)

	#result = pg.execSql(mySecToken, "SELECT currval(pg_get_serial_sequence('{tableName}', '{pkColumn}')".format(tableName = "app.app", pkColumn = "_id"))
	#print("result", result)

	result = pg.execSql(mySecToken, "select 'exists' as status from app.app where name = %(appName)s", {"appName" : 'test_app'})
	print("result", result)

	#data = pg.execSelectSql(mySecToken,'select * from app.app')
	data = pg.execSql(mySecToken,'select * from app.app')
	print(data)
"""
connection
>>> import psycopg2
>>> conn = psycopg2.connect(host="usdf23v0801",port=5535,user="svc-dev-deploy-app",password="yz$79y4E39gW4))",database="deploy_repo")
>>> conn
<connection object at 0x7f127ba8eb40; dsn: 'user=svc-dev-deploy-app password=xxx dbname=deploy_repo host=usdf23v0801 port=5535', closed: 0>

# passing static value
>>> cur.execute("SELECT (%s % 2) = 0 AS even", (10,))       # WRONG 
>>> cur.execute("SELECT (%s %% 2) = 0 AS even", (10,))      # correct
"""

# named arguments
"""
>>> cur.execute(" ""
...     INSERT INTO some_table (an_int, a_date, another_date, a_string)
...     VALUES (%(int)s, %(date)s, %(date)s, %(str)s);
...     " "",
...     {'int': 10, 'str': "O'Reilly", 'date': datetime.date(2005, 11, 18)})
"""

"""
The Python string operator % must not be used: the execute() method accepts a tuple or dictionary of values as second parameter. Never use % or + to merge values into queries:

>>> cur.execute("INSERT INTO numbers VALUES (%s, %s)" % (10, 20)) # WRONG
>>> cur.execute("INSERT INTO numbers VALUES (%s, %s)", (10, 20))  # correct
For positional variables binding, the second argument must always be a sequence, even if it contains a single variable (remember that Python requires a comma to create a single element tuple):

>>> cur.execute("INSERT INTO foo VALUES (%s)", "bar")    # WRONG
>>> cur.execute("INSERT INTO foo VALUES (%s)", ("bar"))  # WRONG
>>> cur.execute("INSERT INTO foo VALUES (%s)", ("bar",)) # correct
>>> cur.execute("INSERT INTO foo VALUES (%s)", ["bar"])  # correct
The placeholder must not be quoted. Psycopg will add quotes where needed:

>>> cur.execute("INSERT INTO numbers VALUES ('%s')", (10,)) # WRONG
>>> cur.execute("INSERT INTO numbers VALUES (%s)", (10,))   # correct
The variables placeholder must always be a %s, even if a different placeholder (such as a %d for integers or %f for floats) may look more appropriate:

>>> cur.execute("INSERT INTO numbers VALUES (%d)", (10,))   # WRONG
>>> cur.execute("INSERT INTO numbers VALUES (%s)", (10,))   # correct
"""

"""
The correct way to pass variables in a SQL command is using the second argument of the execute() method:

>>> SQL = "INSERT INTO authors (name) VALUES (%s);" # Note: no quotes
>>> data = ("O'Reilly", )
>>> cur.execute(SQL, data) # Note: no % operator
"""

"""
Values containing backslashes and LIKE
Unlike in Python, the backslash (\\) is not used as an escape character except in patterns used with LIKE and ILIKE where they are needed to escape the % and _ characters.

This can lead to confusing situations:

>>> path = r'C:\\Users\\Bobby.Tables'
>>> cur.execute('INSERT INTO mytable(path) VALUES (%s)', (path,))
>>> cur.execute('SELECT * FROM mytable WHERE path LIKE %s', (path,))
>>> cur.fetchall()
[]
The solution is to specify an ESCAPE character of '' (empty string) in your LIKE query:

>>> cur.execute("SELECT * FROM mytable WHERE path LIKE %s ESCAPE ''", (path,))

from psycopg2 import sql

cur.execute(
    sql.SQL("insert into {} values (%s, %s)")
        .format(sql.Identifier('my_table')),
    [10, 20])
"""

