from com.mmc.common.singleton import Singleton
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.globals import Globals
from com.mmc.common.security import Security
from com.mmc.db.oraglobals import OracleGlobals
from com.mmc.db.orautil import OraUtil

from cx_Oracle import *

import logging, logging.config, sys, inspect, warnings, time, decimal #, os


class OracleCore(object, metaclass=Singleton):
	def __init__(self, securityToken):
		#os.environ.update([('NLS_LANG', '.UTF8'),('ORA_NCHAR_LITERAL_REPLACE', 'TRUE'),])

		self.SECURITY_TOKEN = securityToken

		self.sec = Security()
		#print("validating sec token from mongo", securityToken)
		self.sec.validateSecToken(securityToken)

		self.infra = Infrastructure()
		self.util = Utility()
		self.Globals = Globals()
		self.oraGlobals = OracleGlobals()
		self.oraUtil = OraUtil(securityToken)

		self.LOGGER = logging.getLogger(__name__)
		self.LOGGER.info("instantiating Oracle core class")

		self.CLASS_NAME = self.__class__.__name__
		self.ENVIRONMENT = self.util.getACopy(self.infra.environment)

		self.DEFAULT_ENCODING="utf-8"

		# conn AUTH
		self.PRELIM_AUTH = PRELIM_AUTH # for startup and shutdown
		self.SYSASM = SYSASM
		self.SYSBKP = SYSBKP
		self.SYSDBA = SYSDBA
		self.SYSDGD = SYSDGD

		self.DBSHUTDOWN_ABORT = DBSHUTDOWN_ABORT
		self.DBSHUTDOWN_FINAL = DBSHUTDOWN_FINAL
		self.DBSHUTDOWN_IMMEDIATE = DBSHUTDOWN_IMMEDIATE
		self.DBSHUTDOWN_TRANSACTIONAL = DBSHUTDOWN_TRANSACTIONAL
		self.DBSHUTDOWN_TRANSACTIONAL_LOCAL = DBSHUTDOWN_TRANSACTIONAL_LOCAL

		self.CONN_DEFAULT_TIMEOUT = 5000 # in milliseconds

		# moving conn from onstructor to a method
		#self.conn = self.__newconn(userId, userEncPass, dsn)
		#print("conn established >>>", str(self.conn))
		#self.setModule("Python CICD")

		#self.CONN_INFO = self.oraUtil.getConnAttr(self.conn)
		#print("conn info >>>", self.CONN_INFO)

		#self.CONN_DB_DETAILS = {}

		# will run all sql which is needed for this conn, like db name, instance name
		#self.__initDBConn()

		#print("conn db details >>>",self.CONN_DB_DETAILS)

	def __enter__(self):
		self.CONN_START_TIME = time.clock()

	def __exit__(self):
		self.LOGGER.info("total elapsed time for this conn >>> {time}".format(time = time.clock() - self.CONN_START_TIME))		

	def __repr__(self):
		return "(%s, %s)" % (self.__class__, self.SECURITY_TOKEN)

	def __str__(self):
		return "(%s, %s)" % (self.__class__, self.SECURITY_TOKEN)

	def createDsn(self, host, port, service, sid = None):
		pass

	def __initDBConn(self, securityToken, conn):
		"""
		executes all the sql and store in instance variable for later use in this conn
		"""
		self.sec.validateSecToken(securityToken)

		if self.isOraConnAlive(securityToken, conn):
			
			print("initializing db conn ...")

			# loading comp data for this conn
			for comp in self.oraGlobals.GLOBAL_INIT_DB_SQLS:
				self.LOGGER.info("executing comp {comp} sql for init db conn >>> {sql}".format(comp = comp["comp"], sql = comp["sql"]))
				
				myResult = self.execSelectSql(securityToken, conn, comp["sql"], comp["sqlArg"])
				myCompData = myResult["data"]
				myCompDB = myCompData[0]["NAME"].lower()

				if myCompDB in self.oraGlobals.INIT_DB_PROC:
					# init task found for this database 									
					myDBInitSteps = self.oraGlobals.INIT_DB_PROC[myCompDB]
					self.LOGGER.info("found init task(s) for database >>> {db}".format(db = myCompDB))

					# executing all tasks associated with this db, (sorting by step)
					for step in self.util.sortDictInListByKey(myDBInitSteps,"step"):

						self.LOGGER.info("found init step for database {db} >>> {step}".format(db = myCompDB, step = str(step)))
		
						if step["callType"] == "procedure":
							self.LOGGER.info("step is procedure, executing >>> {proc}".format(proc = "".join([str(step["procedure"]), ",", str(step["param"])])))
							self.execProcedure(securityToken, conn, step["procedure"], step["param"]) 

						#self.CONN_DB_DETAILS.update({comp["comp"] : myCompData[0]})
				else:
					self.LOGGER.info("no init task found for database >> {db} ".format(db = myCompDB))

			# setting connection attribute
			self.LOGGER.info("setting call time out to >>> {ms}".format(ms = str(self.oraGlobals.CALL_TIMEOUT)))
			conn.callTimeout = self.oraGlobals.CALL_TIMEOUT
			conn.clientinfo = 'python.oracle_core.api'

			self.LOGGER.info("conn initialized for db >>> {db}".format(db = myCompDB))
			print("conn initialized ....")
			## initializing db specific task for this session, if stated in ora globals 
			#self.__initDBTasks()

	def __initDBTasks__(self, securityToken, conn):
		"""
		initialize db specific initialize tasks as specified in oraGlobals
		"""
		try:
			self.sec.validateSecToken(securityToken)
			if self.isOraConnAlive(securityToken, conn):
				
				print("initializing db tasks ...")
				
				# performing initial task immediately after a conn is established, this is mainly needed when connecting to dbdocs
				# as there is a dependancy on user_data_window table which is populated by calling a proc


				if self.CONN_DB_DETAILS["DB"]["NAME"].lower() in self.oraGlobals.INIT_DB_PROC:
					
					print("this db has init task need to be executed >>> ", self.CONN_DB_DETAILS["DB"]["NAME"])
					myDBInitSteps = self.oraGlobals.INIT_DB_PROC[self.CONN_DB_DETAILS["DB"]["NAME"].lower()]

					print("found init task(s) for database >>> {db}".format(db = self.CONN_DB_DETAILS["DB"]["NAME"]))

				# executing all the tasks associated with this db, (sorting by step)
				for step in self.util.sortDictInListByKey(myDBInitSteps,"step"):

					print("found init step for conn >>> {conn}".format(conn = str(self.conn)))
					if step["callType"] == "procedure":
						print("found procedure for execution >>> {proc}".format(proc = "".join([str(step["procedure"]), ",", str(step["param"])])))
						self.execProcedure(step["procedure"], step["param"]) 

		except DatabaseError as error:
			self.LOGGER.error("an error {error} occurred while initializing db task for new conn >>> {conn}".\
				format(error = str(error), conn = cnnection.dsn), exc_info = True)
			raise error

	def validatConnection(self, securityToken, connArg, connTag, oraConn):
		"""
		validate oracle connection, if connection is close, will create a new connection
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug('got arguments >> {arg}'.format(arg = ''.join([securityToken, ',', str(connArg), ',', str(oraConn) ])))

			self.sec.validateSecToken(securityToken)
			
			if not(oraConn and self.isOraConnAlive(securityToken, oraConn)):
				myOraConnArg = self.util.getACopy(connArg)
				myOraConnArg.update({"tag" : "python.dbass.oracle.{tag}".format(tag = connTag)})
				return self.newConnection(securityToken, myOraConnArg)
			else:
				return oraConn

		except Exception as error:
			self.LOGGER.error("an error {error} occurred while validating oracle connection >>> {conn}".\
				format(error = str(error), conn = "".join([str(connArg), ":", str(oraConn)])), exc_info = True)
			raise error

	def getConnVersion(self, securityToken, oraConn):
		"""
		Returns Oracle database version to which this connection belongs to
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug('got arguments >> {arg}'.format(arg = ''.join([securityToken, ',', str(oraConn)])))

			self.sec.validateSecToken(securityToken)

			if self.isOraConnAlive(securityToken, oraConn):
				return oraConn.version.split(".")
			else:
				return "n/a"

		except Exception as error:
			self.LOGGER.error("an error {error} occurred while retrieving connection version >>> {conn}".\
				format(error = str(error), conn = str(oraConn)), exc_info = True)

	def getConnInfo(self, securityToken, oraConn):
		"""
		Returns oracle conneciton information
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug('got arguments >> {arg}'.format(arg = ''.join([securityToken, ',', str(oraConn)])))

			self.sec.validateSecToken(securityToken)

			if self.isOraConnAlive(securityToken, oraConn):
				return {
					"version" : oraConn.version,
					"user" : oraConn.username,
					"tnsEntry" : oraConn.tnsentry,
					"dsn" : oraConn.dsn,
					"ianaCharSet" : oraConn.nencoding,
					"encoding" : oraConn.encoding,
					"module" : oraConn.module,
					"currentSchema" : oraConn.current_schema,
					"callTimeOut" : oraConn.callTimeout
				}

		except Exception as error:
			self.LOGGER.error("an error {error} occurred while retrieving oracle connection information >>> {conn}".\
				format(error = str(error), conn = str(oraConn)), exc_info = True)

	def setCurrentSchema(self, securityToken, oraConn, schema):
		"""
		Sets the current schema for a given connection
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug('got arguments >> {arg}'.format(arg = ''.join([securityToken, ',', str(oraConn)])))

			self.sec.validateSecToken(securityToken)

			if self.isOraConnAlive(securityToken, oraConn):
				self.LOGGER.info("connection is alive, setting current schema to >> {schema}".format(schema = schema))
				oraConn.current_schema = schema

		except Exception as error:
			self.LOGGER.error("an error {error} occurred while setting current schema >>> {schema}".\
				format(error = str(error), schema = schema), exc_info = True)

	def newConnection(self, securityToken, connArg):
		"""
		cx_Oracle.conn(
			user=None, password=None, dsn=None, 
			mode=cx_Oracle.DEFAULT_AUTH, handle=0, pool=None, threaded=False, events=False, cclass=None, 
			purity=cx_Oracle.ATTR_PURITY_DEFAULT, newpassword=None, 
			encoding=None, nencoding=None, edition=None, appcontext=[], 
			tag=None, matchanytag=False, shardingkey=[], supershardingkey=[])
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug('got arguments >> {arg}'.format(arg = ''.join([securityToken, ',', str(connArg)])))

			self.sec.validateSecToken(securityToken)

			#userPass = self.sec._Security__decryptText(userEncPass)

			#removing tab and new line from dsn
			#myDSN = dsn.replace('\r','').replace('\n','')
			myRequiredArgList = ['userId','userEncPass','dsn','tag']
			self.util.valArguments(myRequiredArgList, connArg, [])

			"""
			myArgKeys = list(connArg.keys())
			if not(all(myArgKeys) in myRequiredArg):
				raise ValueError("missing mandatory arguments, expecting {expect}, got {got}".format(expect = str(myRequiredArg), got = list(connArg.keys())))
			"""

			myUserId = connArg["userId"]
			myUserEncPass = connArg["userEncPass"]
			myConnDSN = connArg["dsn"]
			myConnTag = connArg["tag"]

			myStartPos = myConnDSN.upper().find('(DESCRIPTION')
			myDSN = myConnDSN[myStartPos:]

			self.LOGGER.debug('establishing connection using dns >>> {dns}'.format(dns = myDSN))
			myOraConn = connect(myUserId, self.sec._Security__decryptText(myUserEncPass), myDSN)

			self.LOGGER.debug('setting module to >> {module}'.format(module = myConnTag))
			self.setModule(securityToken, myOraConn, myConnTag)

			#self.CONN_INFO = self.oraUtil.getConnAttr(self.conn)
			#print("conn info >>>", self.CONN_INFO)

			#self.CONN_DB_DETAILS = {}

			# will run all sql which is needed for this conn, like db name, instance name
			self.LOGGER.debug('performing init task for this connection ...')
			self.__initDBConn(securityToken, myOraConn)

			self.LOGGER.debug('returning connection object')

			return myOraConn

		except DatabaseError as error:
			self.LOGGER.error("an error {error} occurred while creating new conn for dsn >>> {dsn}".\
				format(error = str(error), dsn = str(connArg)), exc_info = True)
			raise error

	def getDBVersion(self, securityToken, oraConn):
		"""
		retrieves database instance version for a given connection
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug('got arguments >> {arg}'.format(arg = ''.join([securityToken, ',', str(oraConn)])))

			self.sec.validateSecToken(securityToken)

			mySqlTag = 'getDBVer'
			mySql = self.oraUtil.getSqlForTag(securityToken, mySqlTag)

			if mySql:
				myDBResult = self.execSelectSql(securityToken, oraConn, mySql,{})
			else:
				raise ValueError('missing sql for tag >>> {tag}'.format(tag = str(mySqlTag)))

			if myDBResult["data"]:
				return myDBResult["data"][0]["VERSION"]

		except DatabaseError as error:
			self.LOGGER.error("an error {error} occurred while creating new conn for dsn >>> {dsn}".\
				format(error = str(error), dsn = dsn), exc_info = True)
			raise error

	def closeConnection(self, securityToken, oraConn):
		"""
		close current conn
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug('got arguments >> {arg}'.format(arg = ''.join([securityToken, ',', str(oraConn)])))

			self.sec.validateSecToken(securityToken)

			if self.isOraConnAlive(securityToken, oraConn):
				oraConn.close()

		except DatabaseError as error:
			self.LOGGER.error("an error occurred while setting module for conn >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getConnInfo(self, securityToken, oraConn):
		"""
		returns conn information as dict
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug('got arguments >> {arg}'.format(arg = ''.join([securityToken, ',', str(oraConn)])))

			self.sec.validateSecToken(securityToken)

			return self.orautil.getConnAttr(oraConn)

		except DatabaseError as error:
			self.LOGGER.error("an error occurred while setting module for conn >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isOraConnAlive(self, securityToken, oraConn):
		"""
		checking if passed connection is alive
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug('got arguments >> {arg}'.format(arg = ''.join([securityToken, ',', str(oraConn)])))

			self.sec.validateSecToken(securityToken)

			oraConn.ping()

			return True

		except Exception as error:
			return False

	def setModule(self, securityToken, oraConn, module):
		"""	
		sets client identifier for this conn
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug('got arguments >> {arg}'.format(arg = ''.join([securityToken, ',', str(oraConn), ',', module])))

			self.sec.validateSecToken(securityToken)

			if self.isOraConnAlive(securityToken, oraConn):
				if not module:
					oraConn.module = self.Globals.defaultModule
				else:
					oraConn.module = module[:60]

		except DatabaseError as error:
			self.LOGGER.error("an error occurred while setting module for conn >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def setClientIdentifier(self, securityToken, oraConn, clientIdentifier):
		"""	
		sets client identifier for this conn
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug('got arguments >> {arg}'.format(arg = ''.join([securityToken, ',', str(oraConn) ])))

			self.sec.validateSecToken(securityToken)

			if self.isOraConnAlive(securityToken, oraConn):
				self.oraConn.client_identifier = client_identifier[:60]

		except DatabaseError as error:
			self.LOGGER.error("error while setting client identifier for conn >>> ", self.conn, str(error), exc_info = True)
			raise error

	def commitWork(self, securityToken, oraConn):
		"""
		commit work for given conn
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug('got arguments >> {arg}'.format(arg = ''.join([securityToken, ',', str(oraConn) ])))

			self.sec.validateSecToken(securityToken)
		
			if self.isOraConnAlive(securityToken, oraConn):
				oraConn.commit()

		except DatabaseError as error:
			self.LOGGER.error("error occurred while performing rollback >>> ", self.conn, str(error), exc_info = True)
			raise error

	def rollbackWork(self, securityToken, oraConn):
		"""
		rollback for given conn
		"""		
		try:
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug('got arguments >> {arg}'.format(arg = ''.join([securityToken, ',', str(oraConn) ])))

			self.sec.validateSecToken(securityToken)
		
			if self.isOraConnAlive(securityToken, oraConn):
				oraConn.rollback()

		except DatabaseError as error:
			self.LOGGER.error("error occurred while performing rollback >>> ", self.conn, str(error), exc_info = True)
			raise error

	def OutConverter(self, value):
		"""
		Convert Null to empty string in select output, this is to be called from outTypeHandler
		"""
		if value is None:
			return ''
		else:
			return value

	def outputTypeHandler(self, cursor, name, defaultType, size, precision, scale):
		"""
		Output type to handle CLOB and BLOB data during read, will pass this method to cursor.outputtype
		"""
		#if defaultType == cx_Oracle.CLOB:
		#	return cursor.var(cx_Oracle.LONG_STRING, arraysize=cursor.arraysize)
		#if defaultType == cx_Oracle.BLOB:
		#	return cursor.var(cx_Oracle.LONG_BINARY, arraysize=cursor.arraysize)

		if defaultType == CLOB:
			return cursor.var(LONG_STRING, arraysize=cursor.arraysize)
		if defaultType == BLOB:
			return cursor.var(LONG_BINARY, arraysize=cursor.arraysize)
		#if defaultType == cx_Oracle.NUMBER:
		""" commenting as this is returning decimal objects
		if defaultType == NUMBER:
			return cursor.var(decimal.Decimal, arraysize=cursor.arraysize)
		"""
		#if defaultType in (cx_Oracle.STRING, cx_Oracle.FIXED_CHAR):
		if defaultType in (STRING, FIXED_CHAR):
			return cursor.var(str, size, cursor.arraysize, outconverter=self.OutConverter)

	def execSelectSql(self, securityToken, oraConn, selectSql, sqlParam = None):
		"""
		execute select sql with parameters passed
		Named Param (e.g.):
			named_params = {'dept_id':50, 'sal':1000}
			query1 = cursor.execute('SELECT * FROM employees WHERE department_id=:dept_id AND salary>:sal', named_params)
			query2 = cursor.execute('SELECT * FROM employees WHERE department_id=:dept_id AND salary>:sal', dept_id=50, sal=1000)
		"""
		try:
			# checking sqlParam argument, this is named argument which must be in dict format

			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', str(oraConn), ',', selectSql, ',', str(sqlParam)])))

			self.sec.validateSecToken(securityToken)

			if not oraConn:
				raise ValueError('expecting a valid connection, got None !!')

			if not self.isOraConnAlive(securityToken, oraConn):
				raise ValueError("conn << {conn} >> is not alive".format(conn = oraConn.dsn))

			if sqlParam and not(isinstance(sqlParam, dict)):
				raise ValueError("Select sql named arguments must be in dict/key pair value {'key' : 'value'}")

			myStartTime = self.util.getStartTimeSecs()

			myDBResult = ""

			# passing outputTypeHandler method to conn.outputtypehandler
			oraConn.outputtypehandler = self.outputTypeHandler

			with oraConn.cursor() as cur:

				# setting array size for this cursor
				cur.arraysize = 1000 # (default is 100)
				cur.execute(selectSql, sqlParam)

				# check the bind variable passed by using cur.bindnames(), this will return array/list
				myData = self.oraUtil.convSqlResult2Dict(cur)
				myTotalRows = cur.rowcount

			# returning result sets

			if len(myData) > self.oraGlobals.SELECT_LIMIT_ROWS:
				self.LOGGER.info("returning result sets >>> rows : {rows}".format(rows = len(myData)))
			else:
				self.LOGGER.info("returning result sets >>> rows : {rows}, results : {results}".format(\
					rows = len(myData), results = str(myData)))

			myFormattedElapsedTime = self.util.formatElapsedTime(self.util.getElapsedTimeSecs(myStartTime))

			self.LOGGER.info("SELECT sql << {sql} >> executed successfully, elapsed time >>> {time}".format(\
				sql = "".join([selectSql, ",", str(sqlParam)]), time = myFormattedElapsedTime))

			myDBResult = {"data" : myData, "stats" : {"elapsed" : myFormattedElapsedTime, "rows" : myTotalRows}}

			return myDBResult

		except DatabaseError as error:
			#self.LOGGER.error(f"insufficient privilege while executing sql {selectSql} using dsn {oraConn.dsn} !!!")
			raise error
		except Exception as error:
			self.LOGGER.error("an error {error} occurred while executing sql < {sql} > using conn >>> {conn}".\
				format(error = str(error), sql = selectSql, conn = oraConn.dsn), exc_info = True)
			raise error

	def execDDLSql(self, securityToken, oraConn, ddlSql, sqlParam):
		"""
		execute DDL sql with parameters passed
		Named Param (e.g.):
			named_params = {'dept_id':50, 'sal':1000}
			query1 = cursor.execute('SELECT * FROM employees WHERE department_id=:dept_id AND salary>:sal', named_params)
			query2 = cursor.execute('SELECT * FROM employees WHERE department_id=:dept_id AND salary>:sal', dept_id=50, sal=1000)
		"""
		try:
			# checking sqlParam argument, this is named argument which must be in dict format

			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', str(oraConn), ',', ddlSql, ',', str(sqlParam)])))

			self.sec.validateSecToken(securityToken)

			if sqlParam and not(isinstance(sqlParam, dict)):
				raise ValueError("DDL sql named arguments must be in dict/key pair value {'key' : 'value'}")

			myStartTime = self.util.getStartTimeSecs()

			with oraConn.cursor() as cur:
				cur.execute(ddlSql, sqlParam)

				myTotalRows = cur.rowcount

			myFormattedElapsedTime = self.util.formatElapsedTime(self.util.getElapsedTimeSecs(myStartTime))

			self.LOGGER.info("DDL sql << {ddl} >> executed successfully, elapsed time >>> {time}".format(\
				ddl = "".join([ddlSql, ",", str(sqlParam)]), time = myFormattedElapsedTime))

			myDBResult = {"data" : None, "stats" : {"elapsed" : myFormattedElapsedTime, "rows" : myTotalRows}}

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error {error} occurred while executing sql < {sql} > using conn >>> {conn}".\
				format(error = str(error), sql = ddlSql, conn = oraConn.dsn), exc_info = True)
			raise error

	def execDMLSql(self, securityToken, oraConn, dmlSql, sqlParam):
		"""
		execute DML sql with parameters passed
		Limit is 2GB
		Named Param (e.g.):
			sql = "INSERT INTO dept (deptno, dname, loc) VALUES (:deptno, :dname, :loc)"
			try:
				cursor.execute (sql,{ 'deptno':50, 'dname': 'MARKETING', 'loc': 'LONDON'})
				OR
				cursor.execute (sql,deptno=50, dname='MARKETING', loc='LONDON')
			except DatabaseError, exception:
				printf ('Failed to insert row')
				printException (exception)
			exit (1)
		"""
		try:
			# checking sqlParam argument, this is named argument which must be in dict format

			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', str(oraConn), ',', dmlSql, ',', str(sqlParam)])))
			
			self.sec.validateSecToken(securityToken)

			if not (isinstance(sqlParam, list) or isinstance(sqlParam, dict)):
				raise ValueError("DML sql named argument must be either dict (key pair value {'key' : 'value'}) or dict stored in list !!!")

			# validating sql before executing
			self.parseSql(dmlSql)

			myStartTime = self.util.getStartTimeSecs()

			# executing sql using executemany
			with self.oraConn.cursor() as cur:

				mySqlStatement = cur.statement

				if isinstance(sqlParam, list):
					cur.executemany(dmlSql, sqlParam)
				else:
					cur.execute(dmlSql, sqlParam)
				
				myTotalRows = cur.rowcount
				# retrieving total number of rows afftected by this dml

			myFormattedElapsedTime = self.util.formatElapsedTime(self.util.getElapsedTimeSecs(myStartTime))

			self.LOGGER.info("DML sql << {dml} >> executed successfully, elapsed time >>> {time}, total row affected >> {total}".format(\
				dml = "".join([dmlSql, ",", str(sqlParam)]), time = myFormattedElapsedTime, total = myTotalRows))

			#self.LOGGER.info(f"total rows {myTotalRows} changed by sql statement <{mySqlStatement}> ")

			myDBResult = {"data" : None, "stats" : {"elapsed" : myFormattedElapsedTime, "rows" : myTotalRows}}

			return myDBResult

			#return {"rows" : myTotalRows}

		except Exception as error:
			self.LOGGER.error("an error {error} occurred while executing sql < {sql} > using conn >>> {conn}".\
				format(error = str(error), sql = dmlSql, conn = oraConn.dsn), exc_info = True)
			raise error

	def execProcedure(self, securityToken, oraConn, procName, paramArg = {}):
		"""
		execute procedure with parameter passed, parameter must be in list
		utl_recomp must be run by user which have sysdba privilege
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', str(oraConn), ',', procName, ',', str(paramArg)])))

			self.sec.validateSecToken(securityToken)

			if not oraConn:
				raise ValueError('expecting a valid connection, got None !!')


			if not self.isOraConnAlive(securityToken, oraConn):
				raise ValueError("conn << {conn} >> is not alive".format(conn = oraConn.dsn))

			with oraConn.cursor() as curProc:
				myDBResult = curProc.callproc(procName, keywordParameters = paramArg)

			return myDBResult

		except DatabaseError as error:
			self.LOGGER.error("an error {error} occurred while executing procedure/arguments >>> {proc}, {args}".\
				format(error = str(error), proc = procName, args = str(paramArg)), exc_info = True)
			raise error

	def execProc1(self, securityToken, oraConn, procName, arguments= []):
		"""
		execute procedure with parameter passed, parameter must be in list (arguments is an array here)
		utl_recomp must be run by user which have sysdba privilege
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', str(oraConn), ',', procName, ',', str(arguments)])))

			self.sec.validateSecToken(securityToken)

			if not oraConn:
				raise ValueError('expecting a valid connection, got None !!')


			if not self.isOraConnAlive(securityToken, oraConn):
				raise ValueError("conn << {conn} >> is not alive".format(conn = oraConn.dsn))

			with oraConn.cursor() as curProc:
				myDBResult = curProc.callproc(procName, arguments)

			return myDBResult

		except DatabaseError as error:
			self.LOGGER.error("an error {error} occurred while executing procedure/arguments >>> {proc}, {args}".\
				format(error = str(error), proc = procName, args = str(arguments)), exc_info = True)
			raise error

	# batch load --> https://cx-oracle.readthedocs.io/en/latest/user_guide/batch_statement.html
	# setinputsizes
	def execFunction(self, securityToken, oraConn, funcName, returnValType, paramArg = {}):
		"""
		execute function with parameter passed, parameter must be in list
		"""
		try:
			self.sec.validateSecToken(securityToken)

			if self.isOraConnAlive(securityToken, oraConn):
				with oraConn.cursor() as curFunc:
					# creating return value variable as passed in
					if returnValType.lower() == 'number':
						myRetval = curFunc.var(NUMBER)
					elif returnValType.lower() == 'boolean':
						myRetval = curFunc.var(BOOLEAN)
					elif returnValType.lower() == 'datetime':
						myRetval = curFunc.var(DATETIME)
					elif returnValType.lower() in ['varchar','varchar2','char','str','string']:
						myRetval = curFunc.var(STRING)

					myDBResult = curFunc.callfunc(funcName, myRetval, keywordParameters = paramArg)

			return myRetval

		except DatabaseError as error:
			self.LOGGER.error("an error {error} occurred while executing function >>> {proc}".\
				format(error = str(error), proc = ''.join([procName, '(', paramArg, ')'])), exc_info = True)
			raise error

	def execBlock(self, securityToken, oraConn, block, inParamArg = None, outParamVarType = None):
		"""
		execute anonymous block. All variable used in block ({var}) must be provided
		"""
		try:
			self.sec.validateSecToken(securityToken)

			if self.isOraConnAlive(securityToken, oraConn):
				with oraConn.cursor() as curBlock:
					myReturnData = curBlock.var(outParamVarType)
					curBlock.execute(block, inParamArg, outParam)
					return myReturnData.getvalue()

		except DatabaseError as error:
			self.LOGGER.error("an error {error} occurred while executing procedure >>> {proc}".\
				format(error = str(error), proc = ''.join([procName, '(', paramArg, ')'])), exc_info = True)
			raise error

	##### Backup method

	## expdp
	def expdpBackupTbs(self, securityToken, oraConn, JobName, backupObjects):
		pass
	def expdpBackupObj(self, securityToken, jiraIssueId, oraConn, JobName, backupMode, backupObjects):
		"""
		Perform expdp backup
		Arguments:
			securityToken : Security token
			jiraIssueId : jira issue id
			oraConn : connection object
			jobName : Job name to be submitted
			backupMode: Backup mode 
							(schema, table, tablespace)
			backupObject : Object need to be backed up
				if backupmode == 'schema':
					{"schemas" : [schemea1,schema2, .... schemaN], "includeData" : True/False}
				if backupmode == 'table':
					{"table" : [table1,table2, .... tableN], "includeData" : True/False, "dataQuery" : ""}


		handle := DBMS_DATAPUMP.OPEN(<operation>,<job_mode>,<remote_link>,<job_name>,<version>);
			operation = ['EXPORT','IMPORT','SQL_FILE']
			job_mode = ['FULL','SCHEMA','TABLE','TABLESPACE','TRANSPORTABLE']
			remote_link = 'name of database link to remote database name'
			job_name = (max 30 char)

			## An opaque handle for the job. This handle is used as input to the following procedures: 
			## 	ADD_FILE, CREATE_JOB_VIEW, DATA_FILTER, DETACH, GET_STATUS, LOG_ENTRY, LOG_ERROR,METADATA_FILTER, METADATA_REMAP, METADATA_TRANSFORM, 
			## 	SET_PARALLEL,SET_PARAMETER, START_JOB,STOP_JOB, and WAIT_FOR_JOB
		
		handle := DBMS_DATAPUMP.OPEN('EXPORT','SCHEMA',NULL,'EXAMPLE1','LATEST');
		DBMS_DATAPUMP.ADD_FILE(handle,'example1.dmp','DMPDIR');
		DBMS_DATAPUMP.METADATA_FILTER(handle,'SCHEMA_EXPR','IN (''HR'')');
		DBMS_DATAPUMP.START_JOB(handle);

		-- This sample exports the <PROCEDURE_NAME> procedure in the HR schema.
		set serverout on
		declare
		  dp_handle NUMBER;
		  job_status VARCHAR2(30);

		begin
		  dp_handle := dbms_datapump.open (operation => 'EXPORT',
		                                   job_mode => 'SCHEMA');

		  dbms_datapump.add_file (handle => dp_handle,
		                          filename => '<DUMP_NAME>.exp',
		                          directory => '<DIRECTORY_NAME>',
		                          filetype => SYS.DBMS_DATAPUMP.KU$_FILE_TYPE_DUMP_FILE);

		  dbms_datapump.add_file (handle => dp_handle,
		                          filename => '<LOG_FILE>.log',
		                          directory => '<DIRECTORY_NAME>', 
		                          filetype => SYS.DBMS_DATAPUMP.KU$_FILE_TYPE_LOG_FILE);

		  dbms_datapump.metadata_filter (handle => dp_handle,
		                                 name => 'SCHEMA_EXPR',
		                                 value => 'IN (''HR'')');

		  dbms_datapump.metadata_filter (handle => dp_handle,
		                                 name => 'INCLUDE_PATH_EXPR', 
		                                 value => 'IN (''PROCEDURE'')');

		  dbms_datapump.metadata_filter (handle => dp_handle,
		                                 name => 'NAME_EXPR',
		                                 value => 'IN (''<PROCEDURE_NAME>'')',
		                                 object_type => 'PROCEDURE');

		  dbms_datapump.start_job (dp_handle);

		  dbms_datapump.wait_for_job (handle => dp_handle,
		                              job_state => job_status);

		  dbms_datapump.metadata_filter(handle => h1, name => 'EXCLUDE_PATH_LIST', value => 'STATISTICS');
		  dbms_output.put_line ('DataPump Export - '||to_char(sysdate,'DD/MM/YYYY HH24:MI:SS')||' Status '||job_status);

		  dbms_datapump.detach (handle => dp_handle);
		end;

		/

		"""
		try:
			# validatesecurity token
			self.validateSecToken(securityToken)

			# validation
			self.VALID_BACKUP_OBJ_TYPES = ['table','schema','procedure','package','function','view','tablespace']
			myAllBackupObjTypes = [obj["objectType"].lower() for obj in backupObjects]
			myInvalidObjType = [obj for obj in myAllBackupObjTypes if not (obj.lower() not in self.VALID_BACKUP_OBJ_TYPES)]

			if not myInvalidObjType:
				raise ValueError(f"Invalid backup object type {myInvalidObjType}")

			"""
			if backupMode.lower().split(".")[:1] == "schema":
				myExpdpParamArg = {"operation" : "EXPORT", "job_name" : "job_name" : jobName, "job_mode" : "SCHEMA"}
				myBackupFilter =  {"name" : "SCHEMA_LIST", "value" : ",".join(backupObjs)}
				
			if backupMode.lower().split(".")[:1] == "table":
				myExpdpParamArg = {"operation" : "EXPORT", "job_name" : "job_name" : jobName, "job_mode" : "TABLE"}
				myBackupFilter =  {"name" : "NAME_LIST", "value" : ",".join(backupObjs)}

			if backupMode.lower().split(".")[:1] == "query":
				myExpdpParamArg = {"operation" : "EXPORT", "job_name" : "job_name" : jobName, "job_mode" : "TABLE"}
				myBackupFilter =  {"name" : "NAME_LIST", "value" : ",".join(backupObjs)}

			if backupMode.lower().split(".")[:1] == "tablespace":
				myExpdpParamArg = {"operation" : "EXPORT", "job_name" : "job_name" : jobName, "job_mode" : "TABLESPACE"}

			if backupMode.lower() == "transportable":
				myExpdpParamArg = {"operation" : "EXPORT", "job_name" : "job_name" : jobName, "job_mode" : "TRANSPORTABLE"}
			"""
			# create handle for this job


			# Processing backup 
			#https://support.oracle.com/epmos/faces/SearchDocDisplay?_adf.ctrl-state=sdye4xi6g_4&_afrLoop=398192888736935#FIX
			
			# validating the size of the objects need to be backed up
			if backupMode.lower()  == "schema":
				for schema in backupObjects["schema"]:
					if self.execSysMethod(securityToken, oraConn, "getSchemaSizeMB", {"OWNER" : schema["schemas"]}) > self.Globals.ORA_SCHMEA_EXPDP_SIZE_LIMIT:
						backupObjects["schema"].pop(schema)

			elif backupMode.lower()  == "table":
				[objSizeMB.append(self.execSysMethod(securityToken, oraConn, "getObjectSizeMB", {"OWNER" : obj["owner"], "OBJECT_TYPE" : "TABLE", "OBJECT_NAME" : table})) for table in backupObjects["tables"] ]

			for size in objSizeMB:
				if size > self.Globals.ORA_EXPDP_BACKUP_SIZE_THRESHOLD:
					self.LOGGER.info()
					return
			# if schema/table size is more than the threshold set in config, we will not perform the backup

			for obj in backupObjects:

				if backupMode.lower() == "schema":
					
					myExpdpParamArg = {"operation" : "EXPORT", "job_name" : jobName, "job_mode" : "SCHEMA"}
					myBackupFilter =  {"name" : "SCHEMA_LIST", "value" : ",".join(backupObjs)}
					if obj["includeData"] == True:
						myDataFilter = {"include_rows" : 1} 
					else:
						myDataFilter = {"include_rows" : 0}

				elif obj["objectType"].lower() == 'table':
					myExpdpParamArg = {"operation" : "EXPORT", "job_name" : jobName, "job_mode" : "TABLE"}
					myBackupFilter =  {"name" : "NAME_LIST", "value" : ",".join(backupObjs)}
					if obj["includeData"] == True:
						myDataFilter = {"include_rows" : 1}
					else:
						myDataFilter = {"include_rows" : 0}

				elif backupMode.lower() == "tablespace":
					myExpdpParamArg = {"operation" : "EXPORT", "job_name" : jobName, "job_mode" : "TABLESPACE"}

				else:
					#procedure, package
					pass

				#execProcedure(self, securityToken, oraConn, procName, paramArg = {})
				myHandle = self.execFunction(securityToken, "dbms_datapump.open", myExpdpParamArg)
				# get distinct backup mode specified 
				
				myDBResult = self.getMyDatabaseInfo(securityToken, oraConn)

				mySetParameters = [
					{"name" : "flashback_scn", "value" : myDBResult[0]["CURRENT_SCN"]},
					{"handle" : myHandle, "name" : "compression", "value" : "ALL"},
				]

				myBackupFile = "".join([jiraIssueId,".deploy.",obj["backupMode"].lower(), ".", obj["owner"],".",obj["objectType"], ".%U.dmp"])
				myBackupFileSplit = self.util.splitFileAndExtn(myBackupFile)
				myBackupLogFile = "".join([myBackupFileSplit[0],".log"])

				# adding file (dump)
				myArguments = {"handle" : myHandle, "filename" : myBackupFile, "filetype" : "DBMS_DATAPUMP.KU$_FILE_TYPE_DUMP_FILE"}
				self.execProcedure(securityToken, oraConn, 'dbms_datapump.add_file', myArguments)

				# adding file (log)
				myArguments = {"handle" : myHandle, "filename" : myBackupLogFile, "filetype" : "DBMS_DATAPUMP.KU$_FILE_TYPE_LOG_FILE"}
				self.execProcedure(securityToken, oraConn, 'dbms_datapump.add_file', myArguments)

				# setting all parameters as stated above in begining
				for param in mySetParameters:
					param.update({"handle" : myHandle})
					self.execProcedure(securityToken, oraConn, 'dbms_datapump.set_parameter', myArguments)

				# setting parallelism
				
				# getting size of object is being backed up to determine to use paralle degree or not
				for obj in backupObjects:
					myObjSize = self.getObjectSizeMB(securityToken, oraConn, obj["owner"], obj["objectName"], obj["objectType"])
					myTotalObjSize = myTotalSize + myObjSize

				# if we are exceeding the object size, we would need enable parallelism
				
				if myTotalObjSize >= self.EXPDP_SIZE_THRESHOLD_PARALLEL:
					myArguments = {"handle" : myHandle, "degree" : parallel}
					self.execProcedure(securityToken, oraConn, "dbms_datapump.set_parallel", myArguments)

					myBackupFileName = "".join([myBackupFileSplit[0],"_%U",".dmp"])
				else:
					myBackupFileName = "".join([myBackupFileSplit[0],".dmp"])

				if obj["objectType"] ==  	"schema":
					pass
				elif obj["objectType"] == "table":
					pass
				elif obj["objectType"] == "package":
					pass
				elif obj["objectType"] == "procedure":
					pass
				elif obj["objectType"] == "function":
					pass
				elif obj["objectType"] == "view":
					pass
				else:
					pass

			# start job (in RAC starting job on local node only)
			myArguments = {"handle" : myHandle, "cluster_ok" : 0}
			self.execProcedure(securityToken, oraConn, 'dbms_datapump.start_job', myArguments)

			# wait for job to wait for this job to be completed
			myArguments = {"handle" : myHandle}
			self.execProcedure(securityToken, oraConn, 'dbms_datapump.wait_for_job', myArguments)

			return

		except Exception as error:
			raise error

	def getSchemaSize(securityToken, conn, schema):
		"""
		Returns schema size in "MB" 
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', str(conn). str(objDetails)])))
			
			self.sec.validateSecToken(securityToken)

			mySqlTag = 'getSchemaSizeMB'

			mySql = self.oraUtil.getSqlForTag(securityToken, mySqlTag)

			mySqlCriteria = {"OWNER" : schema}

			myDBResult = self.execSelectSql(securityToken, conn, mySql, mySqlCriteria)

			return myDBResult["data"]
			
		except Exception as error:
			self.LOGGER.error("an error {error} occurred while retrieving granted privilege (conn: {conn} !!!".\
				format(error = str(error), conn = conn.dsn), exc_info = True)
			raise error

	def __expdpAddBackupFile(self, securityToken, jobHandle, fileName):
		"""
		Add a backup datafile to job handle, this is the file where all the expdp backup is written to
		"""

	def __dropOrphanedJobMasterTab(self, securityToken, job_owner):
		"""
		drop orphaned job master table for this user
			select 'DROP TABLE '||owner_name||'.'||job_name||' PURGE' stat
				from dba_datapump_jobs 
				where owner_name = USER 
				and instr(v_job_name, upper(job_name) ) > 0 
				and state = 'NOT RUNNING' 
				and attached_sessions = 0 
		"""
		pass
	def getExpdpBackupStatus(self, securityToken, oraConn, handle):
		"""
		BEGIN
			percent_done := 0;
			job_state := 'UNDEFINED';
			while (job_state != 'COMPLETED') and (job_state != 'STOPPED') loop
				dbms_datapump.get_status(h1, dbms_datapump.ku$_status_job_error + dbms_datapump.ku$_status_job_status +	dbms_datapump.ku$_status_wip, -1, job_state, sts);

				js := sts.job_status;

				-- If the percentage done changed, display the new value.

				if js.percent_done != percent_done
				then
					dbms_output.put_line('*** Job percent done = ' || to_char(js.percent_done));
					percent_done := js.percent_done;
					end if;

				-- If any work-in-progress (WIP) or error messages were received for the job,
				-- display them.

				if (bitand(sts.mask,dbms_datapump.ku$_status_wip) != 0)
				then
					le := sts.wip;
				else
					if (bitand(sts.mask,dbms_datapump.ku$_status_job_error) != 0)
					then
						le := sts.error;
					else
						le := null;
					end if;
				end if;
				if le is not null
				then
					ind := le.FIRST;
					while ind is not null loop
						dbms_output.put_line(le(ind).LogText);
						ind := le.NEXT(ind);
					end loop;
				end if;
			end loop;

			-- Indicate that the job finished and detach from it.

			dbms_output.put_line('Job has completed');
			dbms_output.put_line('Final job state = ' || job_state);
			dbms_datapump.detach(h1);
		END;
		/
		"""

	### Database method (retrivien database object information)

	def isObjExists(self, securityToken, conn, owner, objType, objName):
		"""
		checks whether passed objects exists in target database
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', str(conn), owner, ',', objType, ',', objName])))
			
			self.sec.validateSecToken(securityToken)

			myDBVersion = self.getDBVersion(securityToken, conn)

			# retrieving method tag details
			mySqlTagData = self.oraUtil.getSqlTagDetails(securityToken, "isSchemaObjExists")

			#print('sqltag data >> ', mySqlTagData)

			if myDBVersion in mySqlTagData:
				mySql = mySqlTagData[myDBVersion]
			else:
				mySql = mySqlTagData["default"]
			myArguments = {"OWNER" : owner.upper(), "OBJECT_TYPE" : objType.upper(), "OBJECT_NAME" : objName}

			myDBResult = self.execSelectSql(securityToken, conn, mySql, myArguments)

			if myDBResult["data"]:
				return True
			else:
				return False

		except Exception as error:
			self.LOGGER.error(f"an error {error} occurred while chekcing the existing of object {owner}.{objType}.{objName} using conn: {conn.dsn} !!!", exc_info = True)
			raise error

	def execSysMethod(self, securityToken, conn, methodTag, arguments):
		"""
		Executes the method associated with tag as passed an argument
		Arguments:
			securityToken:
			methodTag : method tag (tag must exists in oraglobals)
			arguments : dict - all arguments as dict
		Returns: Returns the results sets as decribed in with associated method tag, if return is stated as 'RESULT' raw result sets are returned
			where as boolean is returned if return is stated as 'EXISTENCE' in oraglobals
		"""
		try:

			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', str(conn), methodTag, ',', str(arguments)])))
			
			self.sec.validateSecToken(securityToken)

			# we need db version for this connection
			myDBVersion = self.getDBVersion(securityToken, conn)

			# retrieving method tag details
			mySqlTagData = self.oraUtil.getSqlTagDetails(securityToken, methodTag)

			#print('sqltag data >> ', mySqlTagData)

			if myDBVersion in mySqlTagData:
				mySql = mySqlTagData[myDBVersion]
			else:
				mySql = mySqlTagData["default"]

			#print('sql >>>', mySql)
			
			if not ( list(set(mySqlTagData["criteria"])) == list(set(arguments.keys())) ):
				raise ValueError(f"Missing mandatory argument(s), expecting {mySqlTagData['criteria']}, got {list(arguments.keys())} ")

			if not mySqlTagData:
				raise ValueError(f"Invalid sql methodtag {methodTag} !!!")

			# checking sql type, if sqltype key is not found, we assume this is 'select statement' 
			if "sqlType" in mySqlTagData:
				mySqlType = mySqlTagData["sqlType"]
			else:
				mySqlType = "select"

			# executing select statement, if return key is 'EXISTENCE' will return boolean based on results, else return the results 
			if mySqlType == "select":
				myDBResult = self.execSelectSql(securityToken, conn, mySql, arguments)
				if myDBResult["data"]:
					myDBResult = myDBResult["data"]

				if mySqlTagData["return"] == "EXISTENCE":
					if  myDBResult:
						myDBResult = True
					else:
						myDBResult = False

			# executing dml
			if mySqlType == "dml":
				myDBResult = self.execDMLSql(securityToken, conn, mySql, arguments)

			# executing ddl
			if mySqlType in ["ddl","dcl"]:
				myDBResult = self.execDDLSql(securityToken, conn, mySql, arguments)

			return myDBResult
			
		except Exception as error:
			self.LOGGER.error(f"an error {error} occurred while excuting method associated with tag {methodTag} using conn: {conn.dsn} !!!", exc_info = True)
			raise error

if __name__ == "__main__":
	sec = Security()
	mySecToken = sec.authenticate('DMZPROD01\\svc-dev-deploy-app','eXokNzl5NEUzOWdXNCkp')
	ora = OracleCore(mySecToken)
	oraConnArg = {'userId' : 'deploy_admin','userEncPass' : 'TWFyc2hfdXNlcl9hZG1pbl8yMA==','dsn' : '(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=usdfw23db26v.mrshmc.com)(PORT=1521))(CONNECT_DATA=(SERVER=DEDICATED)(SERVICE_NAME=oltd147)))','tag':'testing connection'}
	con = ora.newConnection(mySecToken,oraConnArg)
	print('got new connection >>>', con)
	print('executing oracle sys method')
	myUser = 'DEPLOY_ADMIN'
	print(f'user exists ({myUser}) >>', ora.execSysMethod(mySecToken, con, 'isUserExists',{'USER_NAME' : myUser}))
	print(f'user info ({myUser}) >>', ora.execSysMethod(mySecToken, con, 'getUserInfo',{'USER_NAME' : myUser}))
	#print('user (ext) info >>', ora.execSysMethod(mySecToken, con, 'getUserExtInfo',{'USER_NAME' : 'DEPLOY_ADMIN'}))

	print(f'schema object summary ({myUser}) >>', ora.execSysMethod(mySecToken, con, 'getAllSchemaObjSummary',{}))

	myUser = 'DB_MON_OWNER'
	print(f'user object count ({myUser}) >>', ora.execSysMethod(mySecToken, con, 'getUserObjCnt',{'OWNER' : myUser}))
	print(f'user objects summary  ({myUser}) >>>>', ora.execSysMethod(mySecToken, con, 'getAllUserObjSummary',{'OWNER' : myUser}))
	print(f'invalid user objects  ({myUser}) >>>>', ora.execSysMethod(mySecToken, con, 'getUserObjectsByStatus',{'OWNER' : myUser,'STATUS' : 'INVALID'}))
	print(f'schema size  ({myUser}) >>>>', ora.execSysMethod(mySecToken, con, 'getSchemaSizeMB',{'OWNER' : myUser}))


