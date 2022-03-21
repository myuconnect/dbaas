from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.security import Security
#from com.mmc.common.infrastructure import Infrastructure
#from com.mmc.common.globals import Globals
from com.mmc.cicd.cicd_globals import CICDGlobals

import logging, logging.config, sys

import os, json

class Parser(object, metaclass=Singleton):
	"""
	We need to ensure if a task is depndent on an existence of object??? may be during execution need to be explored 
	"""
	def __init__(self, securityToken):
		try:

			self.SECURITY_TOKEN = securityToken
			#self.DB_TECHNOLOGY = dbTechnology

			self.sec = Security()
			self.util = Utility()
			#self.infra = Infrastructure()
			#self.Globals = Globals()
			self.Globals = CICDGlobals()

			#self.ENVIRONMENT = self.util.getACopy(self.infra.environment)
			self.LOGGER = logging.getLogger(__name__)

			self.sec.validateSecToken(securityToken)
			self.DEPLOY_README_KEYS = [""]
			#if dbTechnology == self.Globals.TECHNOLOGY_ORACLE:
			#	self.__initOraVar(securityToken)

		except Exception as  error:
			raise ValueError("an error occurred executing SqlParser constructor ")

	def __initOraVar(self, securityToken):
		"""
		Description: Initialize all instance variable required for parsing Oracle files (sql)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.LOGGER.info("initializing instance var needed to parse Oracle (sql) files")

			self.CURR_SCHEMA = ""
			self.LOGGER = logging.getLogger(__name__)

			self.SQL_TYPE_QUERY = "query"
			self.SQL_TYPE_DML = "dml"
			self.SQL_TYPE_DCL = "dcl"
			self.SQL_TYPE_DDL = "ddl"
			self.SQL_TYPE_TXN = "txn"
			self.SQL_TYPE_BLK = "block"
			self.SQL_TYPE_EXEC = "exec"

			self.SQL_TYPE_LIST = [
				self.SQL_TYPE_QUERY, 
				self.SQL_TYPE_DML, 
				self.SQL_TYPE_DCL, 
				self.SQL_TYPE_DDL,
				self.SQL_TYPE_TXN,
				self.SQL_TYPE_BLK,
				self.SQL_TYPE_EXEC
			]

			self.SQL_OP_SELECT = "select"
			self.SQL_OP_WITH = "with"
			self.SQL_OP_INSERT = "insert"
			self.SQL_OP_UPDATE = "update"
			self.SQL_OP_DELETE = "delete"
			self.SQL_OP_MERGE = "merge"
			self.SQL_OP_COMMIT = "commit"
			self.SQL_OP_ROLLBACK = "rollback"
			self.SQL_OP_SAVEPOINT = "savepoint"
			self.SQL_OP_GRANT = "grant"
			self.SQL_OP_REVOKE = "revoke"
			self.SQL_OP_EXECUTE = "exec"
			self.SQL_OP_CREATE = "create"
			self.SQL_OP_ALTER = "alter"
			self.SQL_OP_DROP = "drop"
			self.SQL_OP_RENAME = "rename"
			self.SQL_OP_TRUNCATE = "truncate"
			self.SQL_OP_DECLARE = "declare"
			self.SQL_OP_BEGIN = "begin"
			self.OP_ORA_BACKUP = "backup"
			self.OP_ORA_BACKUP_EXP = "exp"
			self.OP_ORA_BACKUP_EXPDP = "expdp"
			self.OP_ORA_BACKUP_IMP = "imp"
			self.OP_ORA_BACKUP_IMPDP = "impdp"
			self.OP_ORA_SQLLDR = "sqlldr"

			# objects
			self.OBJ_TYP_ORA_TABLE = "table"
			self.OBJ_TYP_ORA_VIEW = "view"
			self.OBJ_TYP_ORA_PROC = "procedure"
			self.OBJ_TYP_ORA_FUNC = "function"
			self.OBJ_TYP_ORA_TRIG = "trigger"
			self.OBJ_TYP_ORA_PKG_SPEC = "package spec"
			self.OBJ_TYP_ORA_PKG_BODY = "package body"

			self.STORED_OBJ_OP_CREATE_PROC = "create procedure"
			self.STORED_OBJ_OP_CREATE_PKG = "create package"
			self.STORED_OBJ_OP_CREATE_PKG_BODY = "create package body"
			self.STORED_OBJ_OP_CREATE_FUNC = "create function"
			self.STORED_OBJ_OP_CREATE_TRIG = "create trigger"

			# rollback operation
			self.ROLLBACK_OP_DELETE = "delete {table_name} where {whereClause}"
			self.ROLLBACK_OP_DML_QUERY_BACKUP = "{expPath} {userId}/{password}@{targetDB} directory={dirObj} dumpFile={dumpFile} logFie={logFile} query='{objName}:\" {whereClause} \"' flachback_time=systimestamp parallel={degree}"
			self.ROLLBACK_OP_OBJ_BACKUP = "{expPath} {userId}/{password}@{targetDB} directory={dirObj} dumpFile={dumpFile} logFie={logFile} query='{objName}:\" {whereClause} \"' "

			"""
			An ocp tool stands for "Oracle Copy" and written exactly for the purpose of copying dump files back and forth from/to a database server. It is available here: https://github.com/maxsatula/ocp/releases/download/v0.1/ocp-0.1.tar.gz That is a source distribution, so once downloaded and unpacked, run ./configure && make
			"""
			# operation list
			self.SQL_TYPE_QUERY_LIST = [self.SQL_OP_SELECT, self.SQL_OP_WITH]
			self.SQL_TYPE_DML_LIST = [self.SQL_OP_INSERT, self.SQL_OP_UPDATE, self.SQL_OP_DELETE, self.SQL_OP_MERGE]
			self.SQL_TYPE_DCL_LIST = [self.SQL_OP_GRANT, self.SQL_OP_REVOKE]
			self.SQL_TYPE_DDL_LIST = [self.SQL_OP_CREATE, self.SQL_OP_ALTER, self.SQL_OP_DROP, self.SQL_OP_TRUNCATE, self.SQL_OP_RENAME]
			self.SQL_TYPE_TXN_LIST = [self.SQL_OP_COMMIT, self.SQL_OP_ROLLBACK, self.SQL_OP_SAVEPOINT]
			self.SQL_TYPE_BLK_LIST = [self.SQL_OP_DECLARE, self.SQL_OP_BEGIN]
			self.SQL_TYPE_EXEC_LIST = [self.SQL_OP_EXECUTE]

			# start operation list
			self.STORED_OBJ_START_OP_LIST = [
				self.STORED_OBJ_OP_CREATE_PROC, 
				self.STORED_OBJ_OP_CREATE_FUNC, 
				self.STORED_OBJ_OP_CREATE_PKG, 
				self.STORED_OBJ_OP_CREATE_PKG_BODY, 
				self.STORED_OBJ_OP_CREATE_TRIG
			]
			self.DML_START_OP_LIST = [self.SQL_OP_INSERT, self.SQL_OP_UPDATE, self.SQL_OP_DELETE, self.SQL_OP_MERGE]
			self.DDL_START_OP_LIST = [self.SQL_OP_CREATE, self.SQL_OP_ALTER, self.SQL_OP_DROP, self.SQL_OP_TRUNCATE, self.SQL_OP_RENAME]
			self.TXN_START_OP_LIST = [self.SQL_OP_COMMIT, self.SQL_OP_ROLLBACK, self.SQL_OP_SAVEPOINT]
			self.DCL_START_OP_LIST = [self.SQL_OP_GRANT, self.SQL_OP_REVOKE]

			self.SQL_TYPE_MAP = [
				{"operation" : self.SQL_TYPE_QUERY_LIST, "sqlType" : self.SQL_TYPE_QUERY},
				{"operation" : self.SQL_TYPE_DML_LIST, "sqlType" : self.SQL_TYPE_DML},
				{"operation" : self.SQL_TYPE_DCL_LIST, "sqlType" : self.SQL_TYPE_DCL},
				{"operation" : self.SQL_TYPE_DDL_LIST, "sqlType" : self.SQL_TYPE_DDL},
				{"operation" : self.SQL_TYPE_BLK_LIST, "sqlType" : self.SQL_TYPE_BLK},
				{"operation" : self.SQL_TYPE_EXEC_LIST, "sqlType" : self.SQL_TYPE_EXEC},
				{"operation" : self.SQL_TYPE_TXN_LIST, "sqlType" : self.SQL_TYPE_TXN}
			]

			self.SKIP_KWLIST_IN_SQLFILE = ["set","accept","spool","prompt"]
			self.SYS_OBJ_START_KW_LIST = ["dbms_","outln_","sdo_","utl_"]
			self.SINGLE_LINE_COMMENT_KW_LIST = ["--","rem","#","/*"]
			self.MULTI_LINE_COMMENT_START = ["/*"]
			self.MULTI_LINE_COMMENT_END = ["*/"]
			self.ORA_SYS_TABLE_PREFIX_LIST = ['v$','gv$','dba_','all_','user_','dual']

			# rollback
			"""
			self.ROLLBACK_MAP = [
				{
					"op" : self.SQL_OP_QUERY, 
					"rollback" : ""
				},
				{
					"op" : self.SQL_OP_INSERT, 
					"rollback" : { 
						"op" : self.SQL_OP_DELETE,
						"supportData" : "where"
					}
				},
				{
					"op" : self.SQL_OP_UPDATE, 
					"rollback" : { 
						self.SQL_OP_UPDATE}
				},
				{
					"op" : self.SQL_OP_DELETE, 
					"rollback" : {self.SQL_OP_INSERT}
				},
				{
					"op" : self.SQL_OP_CREATE, 
					"rollback" : {self.SQL_OP_DELETE}
				},
				{
					"op" : self.SQL_OP_ALTER, 
					"rollback" : {self.SQL_OP_DELETE}
				},
				{
					
					"op" : self.SQL_OP_DROP, 
					"rollback" : {self.SQL_OP_DELETE}
				},
				{
					"op" : self.SQL_OP_DROP, 
					"rollback" : {self.SQL_OP_DELETE}
				},
				{
					"op" : self.SQL_OP_RENAME, 
					"rollback" : {self.SQL_OP_DELETE}
				},
				{
					"op" : self.SQL_OP_GRANT, 
					"rollback" : {}},
				{
					"op" : self.SQL_OP_REVOKE, 
					"rollback" : {""}},
				{
					"op" : self.SQL_OP_EXECUTE, 
					"rollback" : {}
				},
				{
					"op" : self.SQL_OP_COMMIT, 
					"rollback" : {}
				},
				{
					"op" : self.SQL_OP_ROLLBACK, 
					"rollback" : {}
				},
				{
					"op" : self.SQL_OP_SAVEPOINT, 
					"rollback" : {}
				},
			]
			"""
			self.LOGGER.info("initializing completed successfully")

		except Exception as error:
			self.LOGGER.error("an error occurred initializing instance var", exc_info = True)
			raise error

	def parseDeployFiles(self, securityToken, deployId, appDetails, deployCtrlId, dbTechnology, deployFileLocation):
		"""
		Description: Parse all files for a given deploy id and deploy control id and create parse_out.json
		Arguments:
			securityToken : security token
			deployId: deployment id
			deployCtrlId: deployment control if
			dbTechnology : deployment database technology
			deployFileLocation : deployment file location
		Returns: (parsed json file has relevant deployment file name and dbtechnology, no need to return it as object)
			{
				"parseJson" : "parsed json file",
				"deployFilePath" : deployment file path,
				"total tasks" : n,
				"deployFiles" : [
					{
						"file" : "fileName",
						"seq" : "seq"
						"status" : myParsedStatus,
						"message" : myParsedMsg,
						"totalTasks" : len(myParsedObjects),
						"success" : len(mySuccessTasks),
						"unSuccess" : len(myFailedTasks),
					}
				]
				""
			}

		Usage : parseDeployFiles(<secToken>, <deployId>, <deployCtrlId>, <dbTechnology>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', deployId, ',', str(appDetails), ',', str(deployCtrlId), ',', dbTechnology, ',', deployFileLocation])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not appDetails:
				raise ValueError("app details argument is empty !!!")

			# variables
			myStartTimestamp = self.util.lambdaGetCurrDateTime()
			myStartSeq = myTotalSuccessTasks = myTotalUnSuccessTasks = 0
			myAllParsedTasks = []
			myParsedFileSummary = []
			myAppDBSchema = appDetails["db_schemas"]

			myAllFilesParseStatus = self.Globals.success
			#myDeployPath = self.util.buildPath(self.Globals.DEPLOY_DOWNLOAD_LOC, str(deployId))
			myDeployPath = deployFileLocation
			myDeployRedameFile = self.util.buildPath(myDeployPath,  self.util.getFileName(self.Globals.DEPLOY_README_FILE))

			myDeployParseFile = self.util.buildPath(myDeployPath,self.util.getFileName(\
				self.Globals.DEPLOY_PARSE_OUT_FILE.format(\
						suffix = "".join([str(deployCtrlId), ".", \
							str(self.util.getCurDateTimeForDir()) ]) )
				)
			)

			# looking for deploy readme file
			if not self.util.isFileExists(myDeployRedameFile):
				raise ValueError(f"deployment readme file {myDeployRedameFile} is missing !!!")

			# loading deploy readme file
			myDeployReadmeObj = self.util.readJsonFile(myDeployRedameFile)
			
			# validating deployReadmeFile 
			myReadmeKeys = ["app","dbTechnology","preDeploy","deploy","postDeploy"]
			if not self.util.isListItemExistsInAList(myReadmeKeys, list(myDeployReadmeObj.keys())):
				raise ValueError(f"Mising mandatory key(s) {myReadmeKeys} in readme json file {myDeployReadmeObj} !!!")

			myDeployKeys = ["seq","op","file","ignoreError"]
			for deploy in myDeployReadmeObj["deploy"]:
				if not self.util.isListItemExistsInAList(myDeployKeys, list(deploy.keys())):
					raise ValueError(f"Mising mandatory deploy key(s) {myDeployKeys} in readme json file {myDeployReadmeObj} deploy object {deploy} !!!")

			# we dont want to initialize all instance var for all technology to avoide more memory consumption, thus initializing instance var for given technology
			if myDeployReadmeObj["dbTechnology"].lower() == self.Globals.TECHNOLOGY_ORACLE.lower():
				self.__initOraVar(securityToken)
				# adding sys as a valid app schema 
				myAppDBSchema.append("sys")
			else:
				raise ValueError(f"Invalid db technology, got technology {dbTechnology} in deploy readme file {myDeployReadmeFile} for which there are no constructor available !!!")

			# retrieving system tasks if defined in bootstrap
			if dbTechnology.lower() in self.Globals.CICD_INFRA_DEPLOY_VAR and "preDeploy" in self.Globals.CICD_INFRA_DEPLOY_VAR[dbTechnology.lower()]:
				myPreDeployData = self.util.getACopy(self.Globals.CICD_INFRA_DEPLOY_VAR[dbTechnology.lower()]["preDeploy"])
				myPreDeploySortedTasks = self.util.sortDictInListByKey(myPreDeployData["tasks"],"seq")
				myPostDeployData = self.util.getACopy(self.Globals.CICD_INFRA_DEPLOY_VAR[dbTechnology.lower()]["postDeploy"])
				myPostDeploySortedTasks = self.util.sortDictInListByKey(myPostDeployData["tasks"],"seq")
			else:
				myPreDeployData = []
				myPreDeploySortedTasks = []
				myPostDeployData = []
				myPostDeploySortedTasks = []

			# technoogy specific predeploy task
			if dbTechnology.lower() == self.Globals.TECHNOLOGY_ORACLE.lower():
				#building sys tasks if defined in bootstrap
				for sysTask in myPreDeploySortedTasks:
					myStartSeq += 1
					#mySysObject = self.getObjDetail(securityToken, sysTask["sql"])
					#(<sqlType>, <objectType>, <sqlOperation>, <objectName>,<objectOwner>)
					if sysTask["type"].lower() == "sql":
						myTaskObject = self.getObjDetail(securityToken, sysTask["statement"])
					elif sysTask["type"].lower() == "proc":
						myTaskObject = ["exec", sysTask["op"].split(".")[0], sysTask["op"], sysTask["statement"].split(".")[1].split("(")[0], sysTask["statement"].split(".")[0]]
					else:
						myTaskObject = ('','','','','')

					myAllParsedTasks.append({
						"seq": myStartSeq,
						"taskType" : self.Globals.TASK_TYPE_SYS,
						"op": myTaskObject[2],
						"deployFile": self.Globals.DEPLOY_README_FILE,
						"opType": myTaskObject[0],
						"opStatement": sysTask["statement"],
						"objOwner": myTaskObject[4],
						"objName": myTaskObject[3],
						"objType": myTaskObject[1],
						"ignoreError" : "N",
						"status": self.Globals.success,
						"message": self.Globals.success
					})

			myTotalSuccessTasks = len(myAllParsedTasks)

			# associating system tasks (if found) to "deploy readme json file", so all predeploy task would belong to this file			
			myParsedFileSummary.append({
				"file" : self.Globals.DEPLOY_README_FILE,
				"seq" : 0,
				"startTime" : self.util.lambdaGetCurrDateTime(),
				"endTime" : self.util.lambdaGetCurrDateTime(),
				"status" : self.Globals.success,
				"ignoreError" : "N",
				"message" : self.Globals.success,
				"totalTasks" : len(myAllParsedTasks),
				"successTasks" : len(myAllParsedTasks),
				"unSuccessTasks" : 0
			})

			#sorting deployment files by seq
			myDeployFilesList = self.util.sortDictInListByKey(self.util.getACopy(myDeployReadmeObj["deploy"]), "seq")

			# parsing user deployment files
			for file in myDeployFilesList:
				# parsing files
				
				# finding raw contents of this deploy file (moving this code to repo, due to huge amount of data being passed as argument)
				# myDeployFileRawContents = self.util.readTextFile(self.util.buildPath(deployFilesPath, self.util.getFileName(file["file"])))
				myParsedStartTime = self.util.lambdaGetCurrDateTime()

				print("parsing file >>>", file)

				if "".join([myDeployReadmeObj["dbTechnology"], ".", file["op"]]) == "oracle.run":
					# this is Oracle sql file
					myDeployFile = self.util.buildPath(myDeployPath, self.util.getFileName(file["file"]))
					myParsedTasks = self.parseOraSqlFile(securityToken, myDeployFile, myStartSeq)

					# tech specific validation (Oracle)
					# 1 checking if schema used in this file is a vlaid schema (must belongs to app)
					for task in myParsedTasks:
						# updating skip on error flag to all the tasks processed for this file
						if file["ignoreError"] == True:
							task.update({"ignoreError" : "Y"})
						else:
							task.update({"ignoreError" : "N"})

						# validating schema in deployment with application to which this schema belongs to
						if task["objOwner"] not in myAppDBSchema:
							if task["status"] == self.Globals.success:
								task.update(
									{"status" : self.Globals.unsuccess,
									"message" : f"schema {task['objOwner']} used in this task does not belong to app {myAppDBSchema}"})
							else:
								# task status is already unsuccess, adding this message to exisiting task message
								task.update(
									{"message" : "".join([task["message"], "\n, ", f"schema {task['objOwner']} used in this task does not belong to app {appDetails['app_name']}"])})

							# validating statment in deployment with allowed deployment statement for this technology
						if task["opType"].lower() == "ddl" and "".join([task["op"], ".", task["objType"]]) not in self.Globals.ALLOWED_USER_DEPLOY_STMT[dbTechnology.lower()]:
							if task["status"] == self.Globals.success:
								task.update(
									{"status" : self.Globals.unsuccess,
									"message" : f"".join([task["op"], ".", task["objType"], " is not allowed !!"])})
							else:
								task.update(
									{"message" : "".join([task["message"], "\n, ", "".join([task["op"], ".", task["objType"], " is not allowed !!"])])})


				elif "".join([myDeployReadmeObj["dbTechnology"], ".", file["op"]]) == "oracle.load":
					# this is Oracel load/control file
					myParsedResults = self.parseOraCtrlFile(securityToken, deployFilesPath, self.util.getFileName(file["file"]), file["stmt"], deployFilesPath, myStartSeq)

				# commenting below code, instead of buiding 1 obj will build object for each file along with seq of execution of file 
				# and file name
				#myParsedObjectsList.extend(myParsedTasks)

				myParsedStatusList =  self.util.getUniqueKeyValFromDictInList(myParsedTasks, "status")
				myParsedStatusMsgList =  self.util.getUniqueKeyValFromDictInList(myParsedTasks, "message")

				#print("status >>>",myParsedStatusList)

				if len(myParsedStatusList) > 1 and self.Globals.unsuccess in myParsedStatusList:
					myParsedStatus = self.Globals.unsuccess
				elif len(myParsedStatusList) == 1:
					myParsedStatus = myParsedStatusList[0]

				# parsed message
				if myParsedStatus == self.Globals.success:
					myParsedMsg = self.Globals.success
				else:
					# remove success value and concatenate str of list
					self.util.removeListItem(myParsedStatusMsgList, self.Globals.success)
					myParsedMsg = ','.join(myParsedStatusMsgList)

				if myAllFilesParseStatus == self.Globals.success and myParsedStatus == self.Globals.unsuccess:
					myAllFilesParseStatus = myParsedStatus

				mySuccessTasks = [task for task in myParsedTasks if task["status"] == self.Globals.success]
				myUnSuccessTasks = [task for task in myParsedTasks if task["status"] == self.Globals.unsuccess]

				myPrasedSummary = {
					"file" : self.util.getFileName(file["file"]),
					"seq" : file["seq"],
					"startTime" : myParsedStartTime,
					"endTime" : self.util.lambdaGetCurrDateTime(),
					"status" : myParsedStatus,
					"message" : myParsedMsg,
					"totalTasks" : len(myParsedTasks),
					"successTasks" : len(mySuccessTasks),
					"unSuccessTasks" : len(myUnSuccessTasks)
				}
				if file["ignoreError"] == True:
					myPrasedSummary.update({"ignoreError" : "Y"})
				else:
					myPrasedSummary.update({"ignoreError" : "N"})

				myParsedFileSummary.append(myPrasedSummary)

				myAllParsedTasks.extend(myParsedTasks)

				myTotalSuccessTasks = myTotalSuccessTasks + len(mySuccessTasks)
				myTotalUnSuccessTasks = myTotalUnSuccessTasks + len(myUnSuccessTasks)

				myStartSeq += len(myParsedTasks)

				#self.LOGGER.debug("parsed objects built >>> {parsed}".format(parsed = str(myParsedTasks)))

			# technoogy specific postdeploy task
			myPostDeployTasks = []

			if dbTechnology.lower() == self.Globals.TECHNOLOGY_ORACLE.lower():
				#building sys tasks if defined in bootstrap
				for sysTask in myPostDeploySortedTasks:
					myStartSeq += 1

					if sysTask["type"].lower() == "sql":
						myTaskObject = self.getObjDetail(securityToken, sysTask["statement"])
					elif sysTask["type"].lower() == "proc":
						myTaskObject = ["exec", sysTask["op"].split(".")[0], sysTask["op"], sysTask["statement"].split(".")[1].split("(")[0], sysTask["statement"].split(".")[0]]
					else:
						myTaskObject = ('','','','','')

					myPostDeployTasks.append({
						"seq": myStartSeq,
						"taskType" : self.Globals.TASK_TYPE_SYS,
						"op": myTaskObject[2],
						"deployFile": self.Globals.DEPLOY_README_FILE,
						"opType": myTaskObject[0],
						"opStatement": sysTask["statement"],
						"objOwner": myTaskObject[4],
						"objName": myTaskObject[3],
						"objType": myTaskObject[1],
						"ignoreError" : "N",
						"status": self.Globals.success,
						"message": self.Globals.success
					})
				# we need to recompile all invalid objects for all the schema of this app in this environment

				# updating post deploy summary of deploy readme json file in parsedFileSummary section
				for file in myParsedFileSummary:
					if file["file"] == self.Globals.DEPLOY_README_FILE:
						file.update({
							"endTime" : self.util.lambdaGetCurrDateTime(), 
							"totalTasks" : file["totalTasks"] + len(myPostDeployTasks), 
							"successTasks" : file["successTasks"] + len(myPostDeployTasks)})

			myTotalSuccessTasks = myTotalSuccessTasks + len(myPostDeployTasks)
			myAllParsedTasks.extend(myPostDeployTasks)
			# writing all parsed object to file, will return the file name

			self.util.write2JsonFile(myDeployParseFile, {
				"ts" : myStartTimestamp, 
				"dbTechnology" : dbTechnology,
				"path" : myDeployPath,
				#"parseFile" : self.util.getFileName(myDeployParseFile),
				"parseFile" : myDeployParseFile,
				"parseSummary" : {
					"tasks" : {
						"total" : myTotalSuccessTasks + myTotalUnSuccessTasks,
						"success" : myTotalSuccessTasks,
						"unSuccess" : myTotalUnSuccessTasks,
						"status" : myAllFilesParseStatus,
					},
					"deployFiles" : myParsedFileSummary
				},
				"tasks" : myAllParsedTasks
			})

			# commenting below line, we would not return any object rather write the parsed output to file and
			# that file must be read to get the parsed contents

			return myDeployParseFile

		except Exception as error:
			self.LOGGER.error("an error occurred initializing instance var", exc_info = True)
			raise error
		finally:
			#self.util.releaseMemory()
			pass

	def parseOraCtrlFile(self, securityToken, deployFilesPath, controlFile, loaderStmt, startSeq = None):
		"""
		Description: Parse sql file, returns all sql in file as an object in arrary
		Returns: array object {
			"seq" : <sql execution seq#>,
			"type" : <sql type query/dml/ddl/dcl/txn>,
			"object" : "object name",
			"objectType" : <object type>,
			"op" : <operation sqlldr>,
			"opStatement" : sql statement
		}
		Usage : parseSqlFile(<secToken>,<sqlFileWPath>, <start exec seq#>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', fileName, ',', fileType, ',', str(startExecSeq)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myControlFile = self.util.buildPath(deployFilesPath, self.util.getFileName(controlFile))

			# will read and replace the content of control file
			myControlFileContents = self.util.readTextFile(myControlFile)

			if not self.util.isFileExists(controlFile):
				raise ValueError("control file {file} is missing !!!".format(file = controlFile))

			myCtrlFileSplit = controlFile.split()
			myLoaderStmtSplit = loaderStmt.split()

			myInFilePos = [idx for idx, val in enumerate(myCtrlFileSplit) if val.lower() == 'infile']
			myBadFilePos = [idx for idx, val in enumerate(myCtrlFileSplit) if val.lower() == 'badfile']
			myDscFilePos = [idx for idx, val in enumerate(myCtrlFileSplit) if val.lower() == 'discardfile']
			myTablePos =  [idx for idx, val in enumerate(myCtrlFileSplit) if val.lower() == 'table']

			myLogFile = myDataFile = myBadFile = myDiscFile = myTableName = myTableOwner = ""

			# finding datafile name from control file
			if myInFilePos:
				myDataFile = myCtrlFileSplit[myInfilePos+1]

				if re.search("^[\'\"].*[\'\"]$",myDataFile):
					myDataFile = myDataFile[1:-1]

				myNewDataFile = self.util.buildPath(deployFilesPath, self.util.getFileName(myDataFile))

			if not self.isFileExists(myDataFile):
				raise ValueError("missing data file {file} as referred in control file {ctrlFile}".format(file = myDataFile))

			# finding badfile name
			if myBadFilePos:
				myBadFile = myCtrlFileSplit[myBadFilePos+1]

				if re.search("^[\'\"].*[\'\"]$",myBadFile):
					myBadFile = myBadFile[1:-1]

				myNewBadFile = self.util.buildPath(deployFilesPath, self.util.getFileName(myBadFile))

			# finding discard file name
			if myDscFilePos:
				myDscfile = myCtrlFileSplit[myDscFilePos+1]

				if re.search("^[\'\"].*[\'\"]$",myDscfile):
					myDscfile = myDscfile[1:-1]

				myNewDscfile = self.util.buildPath(deployFilesPath, self.util.getFileName(myDscfile))

			if myTablePos:
				myTableNameRaw = myCtrlFileSplit[myTablePos+1]
				if re.search("^[\'\"].*[\'\"]$",myTableNameRaw):
					myTableNameRaw = myTableNameRaw[1:-1]
			
			# need to add deploy file path if we found file (data/bad/discard) referred in control file
			if myDataFile: myControlFileContents.replace(myDataFile, myNewDataFile)
			if myBadFile: myControlFileContents.replace(myBadFile, myNewBadFile)
			if myDscFile: myControlFileContents.replace(myDscFile, myNewDscFile)


			# getting all file location in loader statement (control, data, log, bad, discard)
			myCtrlFilePos = [idx for idx, val in myLoaderStmtSplit if value.lower() == "control"]
			myLogFilePos = [idx for idx, val in myLoaderStmtSplit if value.lower() == "data"]
			myBadFilePos = [idx for idx, val in myLoaderStmtSplit if value.lower() == "bad"]
			myDiscFilePos = [idx for idx, val in myLoaderStmtSplit if value.lower() == "discard"]

			#adding deployfile path if we found control/data/log/bad/discard file used in sqlldr statement

			if myCtrlFilePos:
				myCtrlFile = myLoaderStmtSplit[myCtrlFilePos + 1]
				loaderStmt.replace(myCtrlFile, self.util.buildPath(deployFilesPath, self.util.getFileName(myCtrlFile)))

			if myLogFilePos:
				myLogFile = myLoaderStmtSplit[myLogFilePos + 1]
				loaderStmt.replace(myLogFile, self.util.buildPath(deployFilesPath, self.util.getFileName(myLogFile)))
			else:
				myLogFile = self.util.replFileNameExtn(controlFile,".log")
				loaderStmt = "".join([loaderStmt, " log = ", self.util.buildPath(deployFilesPath, self.util.getFileName(myLogFile))])

			if myBadFilePos:
				myBadFile = myLoaderStmtSplit[myBadFilePos + 1]
				loaderStmt.replace(myBadFile, self.util.buildPath(deployFilesPath, self.util.getFileName(myBadFile)))

			if myDiscFilePos:
				myDscFile = myLoaderStmtSplit[myDiscFilePos + 1]
				loaderStmt.replace(myDscFile, self.util.buildPath(deployFilesPath, self.util.getFileName(myDscFile)))

			# during execution we need to replace the sqlldr file with fully qualified path and credential

			# changing path to all the files metioned in loader statement

			if not(myDataFile and controlFile):
				raise ValueError("missing control/data file >> {files} !!! ".format(files = "".join([controlFile, ",", myDataFile])))

			myParsedObject = {
				"seq" : startExecSeq + 1,
				"op" : self.OP_ORA_SQLLDR,
				"opType" : self.Globals.ORACLE_DATA_LOAD,
				"opStatement" : "".join([self.ORA_SQLLDR_FILE, " control = ", controlFile, " log= ", myLogFile]),
				"objType" : self.OBJ_TYP_ORA_TABLE,
			}

			if not len(myTableNameRaw.split(".")) > 1:
				myParsedObject.update({
					"objOwner" : myTableNameRaw.split(".")[0],
					"objName" : myTableNameRaw.split(".")[1],
					"status" : self.Globals.success,
					"message" : self.Globals.success
				})
			else:
				myParsedObject.update({
					"objOwner" : "",
					"objName" : myTableNameRaw.split(".")[0],
					"status" : self.Globals.unsuccess,
					"message" : "missing schema name in sqlloader control file >> {file}".format(file = controlFile)
				})

			# renaming original control file to .orig.yyyymmddhhmiss
			self.util.renameFile(myControlFile, myControlFile + '.orig.'+ str(self.getCurDateTimeForDir()) )

			# writing new contents to control file
			self.util.write2File(myControlFile, myControlFileContents)

			return myParsedObject

		except Exception as  error:
			raise ValueError("an error occurred executing Oracle control file >> {file} ".format(controlFile))

	def __parseOraSqlFile__donotuse(self, securityToken, sqlFile, parseFile, startExecSeq = None):
		"""
		Description: Parse sql file, returns all sql in file as an object in arrary
		Returns: array object {
			"seq" : <sql execution seq#>,
			"type" : <sql type query/dml/ddl/dcl/txn>,
			"object" : "object name",
			"objectType" : <object type>,
			"op" : <operation select/insert/update/delete/create/alter/drop/truncate>,
			"sql" : sql statement
		}
			{
	
			}
		Usage : parseSqlFile(<secToken>,<sqlFilePath>, <sqlFile>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sqlFile, ',', parseFile, ',', str(startExecSeq)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			#mySqlFile = self.util.buildPath(filePath, sqlFile)

			if not self.util.isFileExists(sqlFile):
				raise ValueError("invalid sql file >>> {file}".format(file = sqlFile))


			#mySqlFileLines = self.util.readTextFileLines(mySqlFile)
			#mySqlObjLists = self.parseContents(securityToken, mySqlFileLines, startExecSeq)
			mySqlObjLists = self.parseContents(securityToken, mySqlFile, startExecSeq)

			self.LOGGER.info("returing >>> {result}".format(result = str(mySqlObjLists) ))

			return mySqlObjLists

		except Exception as error:
			self.LOGGER.error("an error occurred while parsing sql file {file}".format(file = sqlFile), exc_info = True)
			raise error

	def __removeComments_donotuse(self, fileContents):
		"""
		remove comments from sql file contents
		"""
		myRemoveKeyWordList = ["--","/*","*/","set","accept","spool","rem","prompt"]
		# we need to identify prompt and pass the input ???
		myNewFileContents = []
		myBlockCnt = 0
		myIgnoreComment = False
		multiLineComment = False
		for line in fileContents:
			#print('parsing line >>> ', line)
			# checking if line starts with create procedure/function/package body
			#myStoredObjStartKwList = ["create or replace procedure","create or replace function","create or replace package","create or replace trigger","create table","create view","create type","create materialized view"]
			myStoredObjStartKwList = ["create or replace"]
			# this is create object line, we would ignore removing comments till we find end for this create
			if self.util.isTextStartsWithKW(line, myStoredObjStartKwList):
				print("found kw for creating stored obj")
				myIgnoreComment = True
			elif self.util.isTextStartsWithKW(line, ["begin"]):
				print("found kw 'begin'")
				myIgnoreComment = True
				myBlockCnt = myBlockCnt + 1;
			elif self.util.isTextStartsWithKW(line.replace(" ", "").lower(), ["end;"]):
				print("found kw 'end'")
				myBlockCnt = myBlockCnt - 1;
				if myBlockCnt == 0:
					myIgnoreComment = False

			# checking for multi line comment where it starts with /* and does not end with */ (this is multi line comment)
			if not myIgnoreComment:
				if self.util.isTextStartsWithKW(line, ["/*"]) and not(self.util.isTextEndsWithKW(line, ["*/"])):
					print("found multi line comment (start) outside of ignore comment")
					multiLineComment = True
				if multiLineComment and line.endswith("*/"):
					print("found multi line comment (end) outside of ignore comment")
					multiLineComment = False
			if myIgnoreComment:
				# we are ignoring comment which is part of object
				if line: myNewFileContents.append(line)
			elif not (myIgnoreComment) and not multiLineComment and not self.util.isTextStartsWithKW(line, myRemoveKeyWordList):
				# this is not comment, adding to new content
				if line: myNewFileContents.append(line)
			"""
			elif not (myIgnoreComment) and not isTextStarstWithKW(line, myRemoveKeyWordList) :
				# ignoreCommnet is False and we did not find this line starts with comment kw
				myNewFileContents.append(line)
			"""
			#
			print("ignore comment >>", myIgnoreComment, "block cnt >>> ", myBlockCnt, "line >>>", line, "new Content >>>" ,myNewFileContents)
		return myNewFileContents

	def getSqlOpType(self, securityToken, sqlHeader):
		"""
		Description: Returns sql type of contents passed (content must have initial sql statement which can be identified as sql)
		Returns: String (query/dml/dcl/ddl/txn/block/execute)
		Usage : getSqlType(<securityToken>, <sqlHeader>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sqlHeader])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mySqlOp = sqlHeader.lower().replace("\r"," ").replace("\n"," ").split(" ")[0].replace(";","").strip()

			mySqlType = [ map["sqlType"] for map in self.SQL_TYPE_MAP if mySqlOp.lower().strip() in map["operation"]]

			self.LOGGER.info("returning > {result}".format(result = mySqlType))

			if mySqlType: return mySqlType[0]

		except Exception as error:
			self.LOGGER.error("an error occurred while retrieving sql type for sql header > {sqlHeader}".format(sqlHeader = sqlHeader), exc_info = True)
			raise error

	def getObjOwnerName(self, securityToken, objName):
		"""
		Description: Returns object name and owner from a given object, if owner can not be determined, instance variable
		  CURR_SCHEMA is returned if this is part of current sql as alter session set current_schema
		Returns: Tuple (owner, object name)
		Usage : getObjOwnerName(<securityToken>, <object>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', objName])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myObjectSplitList = objName.strip().split(".")

			if len(myObjectSplitList) > 1:
				myObject = (myObjectSplitList[0],myObjectSplitList[1])
			else:
				if self.util.isTextStartsWithKW(myObjectSplitList[0], self.ORA_SYS_TABLE_PREFIX_LIST):
					myObject = ('sys',myObjectSplitList[-1:][0])
				else:
					myObject = (self.CURR_SCHEMA,myObjectSplitList[-1:][0])

			self.LOGGER.info("returning > {result}".format(result = myObject))

			return myObject

		except Exception as error:
			self.LOGGER.error("an error occurred while retrieving obj owner/name from > {obj}".format(obj = objName), exc_info = True)
			raise error
		finally:
			#self.util.releaseMemory()
			pass

	def getQueryObjDetail(self, securityToken, sqlHeader):
		"""
		Description: returns object detail of given query sql (partial sql, atleast content which identifies sql type)
		Returns: Tuple 
			(<sqlType>, <objectType>, <sqlOperation>, <objectName>,<objectOwner>)
		Usage : getQueryObjDetail(<securityToken>, <sqlHeader>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sqlHeader])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myObjectDetail = ('','','','','')

			mySqlSplitList = [elem for elem in sqlHeader.replace("\r"," ").replace("\n"," ").lower().strip().split(" ") if elem.strip() != ""]

			"""
			myFromPos = [idx for idx, val in enumerate(mySqlSplitList) if val.lower() == "from"]
			myWherePos = [idx for idx, val in enumerate(mySqlSplitList) if val.lower() == "where"]

			if myFromPos:
				myTableList = mySqlSplitList[myFromPos[0] + 1].split(",")
			else:
				myTableList = []

			myObjectDetail = (self.SQL_TYPE_QUERY, "table", mySqlSplitList[0], myTableList, "")
			"""

			# accomodating subquery to retrieve all tables and its owners
			mySelectSplitList = [elem for elem in sqlHeader.replace("\r"," ").replace("\n"," ").lower().strip().split("select") if elem.strip() != ""]
			myAllTables = []

			#print(sqlHeader)
			if sqlHeader.replace("\r"," ").replace("\n"," ").lower().strip().find("from") > 0:
				for select in mySelectSplitList:
					# spliting from to pick 2st element (1st element is always column being selected) and,
					# then spliting on where to pick 1st element to get all the table name
					myTablesList = []
					#print("select >>>", select)
					if select.find("from") > 0 and sqlHeader.find("where") > 0:
						myTablesSplit = [table.strip() for table in select.split("from")[1].split("where")[0].split(",") if table.strip() != ""]
						#['et2_owner.policy_service_team t', 'et2_owner.user_contact ucn']
						#print("select split (from and where present) >", myTablesSplit)
						
						myTablesList = [table.strip().split()[0] for table in myTablesSplit if table] 
						#print("table list >", myTablesList)

					elif select.find("from") > 0 and sqlHeader.find("group by") > 0:
						myTablesSplit = [table.strip() for table in select.split("from")[1].split("group by")[0].split(",") if table.strip() != ""]
						#['et2_owner.policy_service_team t', 'et2_owner.user_contact ucn']
						#print("select split (from and group by present) >", myTablesSplit)
						
						myTablesList = [table.strip().split()[0] for table in myTablesSplit if table] 
						#print("table list >", myTablesList)

					elif select.find("from") > 0:
						myTablesSplit = [table.strip() for table in select.split("from")[1].split(",") if table.strip() != ""]
						#['et2_owner.policy_service_team t', 'et2_owner.user_contact ucn']
						#print("select split (from only) >", myTablesSplit)
						
						myTablesList = [table.strip().split()[0].replace(";","") for table in myTablesSplit if table] 
						#print("table list >", myTablesList)

					# adding table lists
					if myTablesList: myAllTables.extend(myTablesList)

			myObjectDetail = (self.SQL_TYPE_QUERY, "table", mySqlSplitList[0], myAllTables, "")

			return myObjectDetail

		except Exception as error:
			self.LOGGER.error("an error occurred while retrieving QUERY object detail > {sqlHeader}".format(sqlHeader = sqlHeader), exc_info = True)

		finally:
			#self.util.releaseMemory()
			self.LOGGER.info("returning > {result}".format(result = str(myObjectDetail) ))
			return myObjectDetail

	def getDMLObjDetail(self, securityToken, sqlHeader):
		"""
		Description: returns object detail of given dml sql (partial sql, atleast content which identifies sql type)
		Returns: Tuple 
			(<sqlType>, <objectType>, <sqlOperation>, <objectName>,<objectOwner>)
		Usage : getDMLObjDetail(<securityToken>, <sqlHeader>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sqlHeader])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mySqlSplitList = [elem.strip() for elem in sqlHeader.replace("\r"," ").replace("\n"," ").lower().strip().split() if elem.strip() and elem not in ['from','into']]

			myObjectDetail = ('','','','','')
			#print("sql spit list in dml",mySqlSplitList)

			# we need 3 element in sql to move forward <op> (we have removed 'into' and 'from' kw in sql statement )
			# if not will return empty objeect detail 
			if len(mySqlSplitList) < 3:
				return myObjectDetail

			mySqlObjOwner, mySqlObjName = self.getObjOwnerName(securityToken, mySqlSplitList[1])

			myObjectDetail = (self.SQL_TYPE_DML, "table", mySqlSplitList[0], mySqlObjName, mySqlObjOwner)

			self.LOGGER.info("returning > {result}".format(result = str(myObjectDetail) ))

			return myObjectDetail

		except Exception as error:
			self.LOGGER.error("an error occurred while retrieving DML object detail > {sqlHeader}".format(sqlHeader = sqlHeader), exc_info = True)

		finally:
			#self.util.releaseMemory()
			self.LOGGER.info("returning > {result}".format(result = str(myObjectDetail) ))
			return myObjectDetail

	def getDDLObjDetail(self, securityToken, sqlHeader):
		"""
		Description: returns object detail of given ddl sql (partial sql, atleast content which identifies sql type)
		Returns: Tuple 
			(<sqlType>, <objectType>, <sqlOperation>, <objectName>,<objectOwner>)
		Usage : getDDLObjDetail(<securityToken>, <sqlHeader>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sqlHeader])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mySqlHeader = sqlHeader.replace("\r"," ").replace("\n"," ").replace("(", " ").strip().lower()

			mySqlHeaderSplit = [elem.strip() for elem in mySqlHeader.split(" ") if elem.strip() != ""]

			myObjectDetail = ('','','','','')

			mySqlHeader = " ".join(mySqlHeaderSplit)
			#print('mysql', mySqlHeader)
			if self.util.isTextStartsWithKW(mySqlHeader, ["alter session set current_schema"]):
				self.LOGGER.debug("alter session set current_schema sql")

				mySetSchema = mySqlHeader.strip().split("=")[1].strip().replace(";","")

				# overriding CURR_SCHEMA to this sql current schema
				self.CURR_SCHEMA = mySetSchema
				
				myObjectDetail = (self.SQL_TYPE_DDL,"session.schema","alter session", mySetSchema, mySetSchema)

			elif self.util.isTextStartsWithKW(mySqlHeader, ["alter session set"]):
				self.LOGGER.debug("alter session set sql")
				#print("alter session set sql")
				mySetSessionNS = mySqlHeader.strip().lower().split("set")[1].strip().split("=")[0].strip()
				#print('session ns >', mySetSessionNS)
				myObjectDetail = (self.SQL_TYPE_DDL,"".join(["session",".",mySetSessionNS]),"alter session","",self.CURR_SCHEMA)

			elif self.util.isTextStartsWithKW(mySqlHeader, ["alter session enable"]):
				self.LOGGER.debug("alter session enable sql")

				myObjectDetail = (self.SQL_TYPE_DDL,"session.enable","alter session enable","",self.CURR_SCHEMA)

			elif self.util.isTextStartsWithKW(mySqlHeader, ["alter session"]):
				self.LOGGER.debug("alter session sql")

				myObjectDetail = (self.SQL_TYPE_DDL,"session","alter.session","",self.CURR_SCHEMA)

			elif self.util.isTextStartsWithKW(mySqlHeader, ["alter system"]):
				self.LOGGER.debug("alter system sql")

				myObjectDetail = (self.SQL_TYPE_DDL,"system","alter system","",self.CURR_SCHEMA)

			elif self.util.isTextStartsWithKW(mySqlHeader, ["create or replace package body"]):
				self.LOGGER.debug("creating package body sql")

				mySqlObj = mySqlHeader.lower().strip().split("package body")[1].strip().split(" ")[0].strip()
				#print("sql obj in create package body",mySqlObj)
				
				mySqlObjOwner, mySqlObjName = self.getObjOwnerName(securityToken, mySqlObj)

				myObjectDetail = (self.SQL_TYPE_DDL, "package.body", "create", mySqlObjName, mySqlObjOwner)

			elif self.util.isTextStartsWithKW(mySqlHeader, ["create or replace package"]):
				self.LOGGER.debug("creating package spec sql")

				mySqlObj = mySqlHeader.lower().strip().split("package")[1].strip().split(" ")[0].strip()

				mySqlObjOwner, mySqlObjName = self.getObjOwnerName(securityToken, mySqlObj)

				myObjectDetail = (self.SQL_TYPE_DDL, "package.spec", "create", mySqlObjName, mySqlObjOwner)

			elif self.util.isTextStartsWithKW(mySqlHeader, ["create or replace"]):
				self.LOGGER.debug("this is create or replace proc/func/trig/view etc.")

				mySqlSplit = [elem for elem in mySqlHeader.lower().replace(" or replace ", " ").split() if elem.strip()]
				mySqlOp = mySqlSplit[0]
				myObjType = mySqlSplit[1]
				mySqlObj = mySqlSplit[2]

				mySqlObjOwner, mySqlObjName = self.getObjOwnerName(securityToken, mySqlObj)

				myObjectDetail = (self.SQL_TYPE_DDL, myObjType, "create", mySqlObjName, mySqlObjOwner)

			else:
				self.LOGGER.debug("this is ddl sql")

				mySqlSplit = [elem for elem in mySqlHeader.lower().split(" ") if elem.strip()]

				mySqlOP = mySqlSplit[0]
				mySqlObjType = mySqlSplit[1]
				mySqlObj = mySqlSplit[2]

				mySqlObjOwner, mySqlObjName = self.getObjOwnerName(securityToken, mySqlObj)

				myObjectDetail = (self.SQL_TYPE_DDL, mySqlObjType, mySqlOP, mySqlObjName, mySqlObjOwner)

		except Exception as error:
			self.LOGGER.error("an error occurred while retrieving DDL object detail > {sqlHeader}".format(sqlHeader = sqlHeader), exc_info = True)

		finally:
			#self.util.releaseMemory()
			self.LOGGER.info("returning > {result}".format(result = str(myObjectDetail) ))
			return myObjectDetail

	def getDCLObjDetail(self, securityToken, sqlHeader):
		"""
		Description: returns object detail of given dcl sql (partial sql, atleast content which identifies sql type)
		Returns: Tuple 
			(<sqlType>, <objectType>, <sqlOperation>, <objectName>,<objectOwner>)
		Usage : getDCLObjDetail(<securityToken>, <sqlHeader>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sqlHeader])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			"""
				"grant select,insert,update on table to grantee1" 
					split on "to" pick [1] to get grnatee1
				"grant role to grantee"
				"grant sysprivs to grantee"
				"revoke sele on tab1 from test1"
				"revoke role1 from grantee"
			"""
			# removing extra space in grant/revoke statement
			mySqlSplitList = [elem.strip() for elem in sqlHeader.replace("\r"," ").replace("\n"," ").lower().strip().split() if elem.strip()]

			myObjectDetail = ('','','','','')

			mySql = " ".join(mySqlSplitList)

			mySqlObj = ""

			if mySqlSplitList[0].lower() == "grant":

				myGrantee = mySql.split(" to ")[1].replace(";","").strip()

				if not [elem for elem in mySql.split("grant")[1].split(" ") if elem.strip() == "on"]:
					myPriveType = "role"
					myObjectType = "role"
					myPrivilege = mySql.split("grant ")[1].split(" ")[0]
					mySqlObj = mySql.split(" to ")[0].strip().split("grant")[1].strip()

				else:
					myPriveType = "privilege"
					myObjectType = "privilege"
					myPrivList = mySql.split(" on ")[0].split("grant")[1].strip().split(",")
					mySqlObj = mySql.split(" on ")[1].split("to")[0]

			elif mySqlSplitList[0].lower() == "revoke":

				myRevokee = mySql.split(" from ")[1].replace(";","").strip()

				if not [elem for elem in mySql.split("revoke")[1].split(" ") if elem.strip() == "on"]:
					myPriveType = "role"
					myObjectType = "role"
					myPrivilege = mySql.split("revoke ")[1].split(" ")[0]
					mySqlObj = mySql.split(" from ")[0].strip().split("revoke")[1].strip()

				else:
					myPriveType = "privilege"
					myObjectType = "privilege"
					myPrivList = mySql.split(" from ")[1].split(" on ")[0].split(",")
					mySqlObj = mySql.split(" from ")[1].split("to")[0]

			mySqlObjOwner, mySqlObjName = self.getObjOwnerName(securityToken, mySqlObj)

			myObjectDetail = (self.SQL_TYPE_DCL, myObjectType, mySqlSplitList[0], mySqlObjName, mySqlObjOwner)

		except Exception as error:
			self.LOGGER.error("an error occurred while retrieving DML object detail > {sqlHeader}".format(sqlHeader = sqlHeader), exc_info = True)

		finally:
			self.LOGGER.info("returning > {result}".format(result = str(myObjectDetail) ))
			return myObjectDetail

	def getTXNObjDetail(self, securityToken, sqlHeader):
		"""
		Description: returns object detail of given txn sql (partial sql, atleast content which identifies sql type)
		Returns: Tuple 
			(<sqlType>, <objectType>, <sqlOperation>, <objectName>,<objectOwner>)
		Usage : getTXNObjDetail(<securityToken>, <sqlHeader>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sqlHeader])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mySqlSplitList = [elem.strip() for elem in sqlHeader.replace("\r"," ").replace("\n"," ").lower().strip().split(" ") if elem.strip()]

			myObjectDetail = ('','','','','')

			myObjectDetail = (self.SQL_TYPE_TXN, "", mySqlSplitList[0], "", "")

		except Exception as error:
			self.LOGGER.error("an error occurred while retrieving DML object detail > {sqlHeader}".format(sqlHeader = sqlHeader), exc_info = True)

		finally:
			self.LOGGER.info("returning > {result}".format(result = str(myObjectDetail) ))
			return myObjectDetail

	def getEXCObjDetail(self, securityToken, sqlHeader):
		"""
		Description: returns object detail of given exec statement
		Returns: Tuple 
			(<sqlType>, <objectType>, <sqlOperation>, <objectName>,<objectOwner>)
		Usage : getEXECObjDetail(<securityToken>, <sqlHeader>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sqlHeader])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mySqlSplitList = [elem.strip() for elem in sqlHeader.replace("\r"," ").replace("\n"," ").lower().strip().split() if elem.strip()]

			myObjectDetail = ('','','','','')

			mySqlObjOwner, mySqlObjName = self.getObjOwnerName(securityToken, mySqlSplitList[1])

			if self.util.isTextStartsWithKW(mySqlObjName, self.SYS_OBJ_START_KW_LIST):
				mySqlObjOwner = "sys"

			myObjectDetail = (self.SQL_TYPE_EXEC, "procedure", mySqlSplitList[0], mySqlObjName, mySqlObjOwner)

		except Exception as error:
			self.LOGGER.error("an error occurred while retrieving EXEC object detail > {sqlHeader}".format(sqlHeader = sqlHeader), exc_info = True)

		finally:
			self.LOGGER.info("returning > {result}".format(result = str(myObjectDetail) ))
			return myObjectDetail

	def getBLKObjDetail(self, securityToken, sqlHeader):
		"""
		Description: returns object detail of given exec statement
		Returns: Tuple 
			(<sqlType>, <objectType>, <sqlOperation>, <objectName>,<objectOwner>)
		Usage : getBLKObjDetail(<securityToken>, <sqlHeader>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sqlHeader])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mySqlSplitList = [elem.strip() for elem in sqlHeader.replace("\r"," ").replace("\n"," ").lower().strip().split(" ") if elem.strip()]

			myObjectDetail = ('','','','','')

			myObjectDetail = (self.SQL_TYPE_BLK, "", mySqlSplitList[0], "", "")

		except Exception as error:
			self.LOGGER.error("an error occurred while retrieving BLK object detail > {sqlHeader}".format(sqlHeader = sqlHeader), exc_info = True)

		finally:
			self.LOGGER.info("returning > {result}".format(result = str(myObjectDetail) ))
			return myObjectDetail

	def getObjDetail(self, securityToken, sqlHeader):
		"""
		Description: returns object detail of given sql (partial sql, atleast content which identifies sql type)
		Returns: Tuple 
			(<sqlType>, <objectType>, <sqlOperation>, <objectName>,<objectOwner>)
		Usage : getObjDetail(<securityToken>, <sqlHeader>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sqlHeader])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mySqlType = self.getSqlOpType(securityToken, sqlHeader)

			if not mySqlType:
				raise ValueError("unable to retrieve sql type from >>> {sql}".format(sql = sqlHeader))

			myObjectDetail = ()

			# removing additional space from sql
			mySqlHeader = " ".join([elem for elem in sqlHeader.replace("\n","").replace("\r","").split() if elem.strip()])

			self.LOGGER.info('sqlHeader after removing additional space >> {sqlHeader}'.format(sqlHeader = sqlHeader))

			if mySqlType == self.SQL_TYPE_QUERY: 
				myQueryObjectDetail = self.getQueryObjDetail(securityToken, sqlHeader)

				# parsing owner and table, we might have multiple table in select statement
				myOwnerList = []
				myTableList = []

				#print("owner, table", type(myOwnerList), type(myTableList), myOwnerList, myTableList)

				for table in myQueryObjectDetail[3]:
					myTableOwner, myTableName = self.getObjOwnerName(securityToken, table)
					myOwnerList.append(myTableOwner)
					myTableList.append(table)

				# creating new tuple
				myObjectDetail = (myQueryObjectDetail[0], myQueryObjectDetail[1], myQueryObjectDetail[2], myTableList, myOwnerList)

			if mySqlType == self.SQL_TYPE_DML: myObjectDetail = self.getDMLObjDetail(securityToken, sqlHeader)
			if mySqlType == self.SQL_TYPE_DDL: myObjectDetail = self.getDDLObjDetail(securityToken, sqlHeader)
			if mySqlType == self.SQL_TYPE_DCL: myObjectDetail = self.getDCLObjDetail(securityToken, sqlHeader)
			if mySqlType == self.SQL_TYPE_TXN: myObjectDetail = self.getTXNObjDetail(securityToken, sqlHeader)
			if mySqlType == self.SQL_TYPE_BLK: myObjectDetail = self.getBLKObjDetail(securityToken, sqlHeader)
			if mySqlType == self.SQL_TYPE_EXEC: myObjectDetail = self.getEXCObjDetail(securityToken, sqlHeader)

			self.LOGGER.info("returning > {result}".format(result = str(myObjectDetail) ))

			return myObjectDetail

		except Exception as error:
			self.LOGGER.error("an error occurred while retrieving object detail > {sqlHeader}".format(sqlHeader = sqlHeader), exc_info = True)
			raise error

	def isMultiLineCommStart(self, securityToken, sqlLine):
		"""
		Description: returns if given sql line starts with multi line
		Returns: Boolean
		Usage : isMultiLineCommStart(<securityToken>, <sqlLine>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sqlLine])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if self.util.isTextStartsWithKW(sqlLine, self.MULTI_LINE_COMMENT_START):
				return True
			else:
				return False

		except Exception as error:
			self.LOGGER.error("an error occurred while determining if line is start of multi line comment > {line}".format(line = sqlLine))
			raise error

	def isMultiLineCommEnd(self, securityToken, sqlLine):
		"""
		Description: returns if given sql line ends with multi line
		Returns: Boolean
		Usage : isMultiLineCommStart(<securityToken>, <sqlLine>)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sqlLine])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if self.util.isTextEndsWithKW(sqlLine, self.MULTI_LINE_COMMENT_END):
				return True
			else:
				return False

		except Exception as error:
			self.LOGGER.error("an error occurred while determining if line is end of multi line comment > {line}".format(line = sqlLine))
			raise error

	def validateSqlHeader(self, securityToken, sqlHeader):
		"""
		Description: Validates sql header, returns validation status and message
		Returns: Tuple (status, validation message)
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sqlHeader])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mySqlType, mySqlObjType, mySqlOperation, mySqlObjName, mySqlObjOwner = self.getObjDetail(securityToken, sqlHeader)
			
			self.LOGGER.info("obj detail found in sql header (type.op.objType.objOwner.objName) >> {objDetails}".\
				format(objDetails = "".join([mySqlType,".",mySqlOperation,".",mySqlObjType,".", str(mySqlObjOwner),".", str(mySqlObjName)])))

			if mySqlType not in self.SQL_TYPE_LIST:

				self.LOGGER.info("sql type '{sqlType}' not found in valid list of sql type > {valid}".format(sqlType = mySqlType, valid = str(self.SQL_TYPE_LIST)))

				return (False,"invalid sqltype {sqlType} !!!".format(sqlType = mySqlType))

			elif mySqlType == self.SQL_TYPE_QUERY:

				if not (mySqlOperation and mySqlObjName):

					self.LOGGER.info("missing sql operation/object name from sql > {sql} ".format(sql = sqlHeader))

					return (False, "missing all required components for sql type {type}".format(type = mySqlType))

			elif mySqlType in [self.SQL_TYPE_TXN, self.SQL_TYPE_BLK]:
				
				if not (mySqlOperation):
				
					self.LOGGER.info("missing sql operation from sql > {sql} ".format(sql = sqlHeader))

					return (False, "Mandatory component (op) is missing from sql type {sqlType}, got >>> {got}".\
						format(sqlType = mySqlType, got = "".join([mySqlOperation])))

			# returning True as we have not encountered this sq type???
			self.LOGGER.info("no check performed for sql type {sqlType} from > {sql} , returning True ".format(sqlType = mySqlType, sql = sqlHeader))		
			return (True, "success")

		except Exception as error:
			self.LOGGER.error("an error occurred while checking if sql header is complete, sql header  > {sqlHeader}".format(sqlHeader = sqlHeader))
			raise error
		finally:
			#self.util.releaseMemory()
			pass

	def getSqlHeader(self, securityToken, sql):
		"""
		Description: This will return sql header, if available in sql string
		Returns: String 
			create or replace ... 
			create table
			alter objcet_type obj_name
			insert ...
			delete ...
			update ...
			merge ...
			select ...
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sql])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if type(sql) in(list, tuple):
				mySql = " ".join([elem for elem in " ".join(sql).split(" ") if elem.strip()])

			elif type(sql) == str:
				mySql = " ".join([elem for elem in sql.split(" ") if elem.strip()])

			if self.util.isTextStartsWithKW(mySql.replace(" or replace "," "), self.STORED_OBJ_START_OP_LIST):
				# ddl, returning (op, objtype, objName)
				mySqlSplit = [elem for elem in mySql.replace(" or replace "," ").split(" ") if elem.strip()]

				if len(mySqlSplit) < 3:
					return ('','','')
				self.LOGGER.debug("ddl, returning (op,obj type, obj name) (create, procedure, procedure name")

				#print("sql header split > ",mySqlSplit, "returning > ", " ".join([mySqlSplit[0], mySqlSplit[1]]), mySqlSplit[2])

				return (" ".join([mySqlSplit[0], mySqlSplit[1]]), mySqlSplit[2] )

			elif self.util.isTextStartsWithKW(\
				mySql.replace(" into ", " ").replace(" from ", " "),self.DML_START_OP_LIST):
				# dml, returning (op,table,tablename) (insert, table, table name)

				mySqlSplit = mySql.replace(" into ", " ").replace(" from ", " ").split(" ")

				# we need atleast 2 element in a dml sql to return sql header (op, table)
				if len(mySqlSplit) < 2:
					return ('','')

				self.LOGGER.info("returning (dml header info) >> {result}".format(result = "".join([mySqlSplit[0], ',', mySqlSplit[1]])))

				#return (mySqlSplit[0], mySqlSplit[1], mySqlSplit[2])
				return (mySqlSplit[0], mySqlSplit[1])

			elif self.util.isTextStartsWithKW(mySql, self.SQL_TYPE_QUERY_LIST):
				# select statement, returning (op,objtype, obj) (select, table, table_name)

				mySqlSplit = mySql.split()

				self.LOGGER.info("returning (select header info) >> {result}".format(result = "".join([mySqlSplit[0], ',', self.SQL_TYPE_QUERY, ',', '' ])))

				myFromPos = [idx for idx, val in enumerate(mySqlSplit) if val.lower() == "from"]

				if myFromPos:
					myTables = mySqlSplit[myFromPos[0] + 1].split(",")
					return (mySqlSplit[0], self.SQL_TYPE_QUERY, myTables)
				else:
					return (mySqlSplit[0], self.SQL_TYPE_QUERY, '')

			elif self.util.isTextStartsWithKW(mySql, self.DDL_START_OP_LIST):
				# ddl, returning (op,objtype, obj) (create, table, tablename)

				mySqlSplit = mySql.split(" ")

				if len(mySqlSplit) < 3:
					return ('','','')

				self.LOGGER.info("returning (dml header info) >> {result}".format(result = "".join([mySqlSplit[0], ',', mySqlSplit[1], ',', mySqlSplit[2]])))

				return (mySqlSplit[0], mySqlSplit[1], mySqlSplit[2] )

			elif self.util.isTextStartsWithKW(mySql, self.TXN_START_OP_LIST):
				# txn, returning (op,objtype, obj) (savepoint, 'txn' , <savepoint name>)

				mySqlSplit = mySql.split(" ")

				if len(mySqlSplit) > 1:
					# accomodating savepoiont name if used
					self.LOGGER.info("returning (txn header info) >> {result}".format(result = "".join([mySqlSplit[0], ',', self.SQL_TYPE_TXN, ',', mySqlSplit[1]])))
	
					return (mySqlSplit[0], self.SQL_TYPE_TXN, mySqlSplit[1] )
				else:
					self.LOGGER.info("returning (txn header info) >> {result}".format(result = "".join([mySqlSplit[0], ',', self.SQL_TYPE_TXN, ',', '' ])))

					return (mySqlSplit[0], self.SQL_TYPE_TXN, "" )

			elif self.util.isTextStartsWithKW(mySql, self.DCL_START_OP_LIST):
				# txn, returning (op,objtype, obj) (grant/revoke, 'dcl' , '')

				mySqlSplit = mySql.split(" ")

				self.LOGGER.info("returning (dcl header info) >> {result}".format(result = "".join([mySqlSplit[0], ',', self.SQL_TYPE_DCL, ',', '' ])))

				return (mySqlSplit[0], self.SQL_TYPE_DCL, "" )

			elif self.util.isTextStartsWithKW(mySql, ["declare"]):
				# returning (op,objtype, obj) (create, table, tablename)

				mySqlSplit = mySql.split(" ")

				if len(mySqlSplit) > 1:
					# accomodating savepoiont name if used

					self.LOGGER.info("returning (block header info) >> {result}".format(result = "".join([mySqlSplit[0], ',', self.SQL_TYPE_BLK, ',', mySqlSplit[1] ])))

					return (mySqlSplit[0], "blk", mySqlSplit[1] )
				else:
					self.LOGGER.info("returning (block header info) >> {result}".format(result = "".join([mySqlSplit[0], ',', self.SQL_TYPE_BLK, ',', '' ])))

					return (mySqlSplit[0], self.SQL_TYPE_BLK, "" )
			else:
				raise ValueError("unable to retrieve sql header for (invalid op) >>> {sql}".format(sql = sql))

		except Exception as error:
			self.LOGGER.error("an error occurred while retrieving sql header detail from > {sqlHeader}".format(sqlHeader = sql), exc_info = True)
			return ("","","")
		finally:
			#self.util.releaseMemory()
			pass

	def parseOraSqlFile(self, securityToken, sqlFile, startExecSeq = None):
		"""
		Description: Parse sql file contents and resturns each operation as an object in array
		Arguments: 
			SecurityToken, 
			contents (readlines from a sql file), 
			startExecSeq: Execution order start seq, if None sql execution order will start from 0
		Retursn: sql object (dict) in Array
			{
				"seq" : mySqlOrder,
				"op" : mySqlOp,
				"opType" : mySqlType, 
				"opStatement" : myFinalSql,
				"objOwner" : mySqlObjOwner, 
				"objName" : mySqlObjName, 
				"objType" : mySqlObjType,
				"status" : myValStatus,
				"message" : myValMessage
			}
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', sqlFile, ',', str(startExecSeq)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not self.util.isFileExists(sqlFile):
				raise ValueError("invalid sql file >>> {file}".format(file = sqlFile))

			# variabes
			isInParsingSql = False # sql parsing started (default False)
			isInParsingStoredObj = False # stored object (pkg/func/trig/proc) parsing started (default False)
			isCommentLine = multiLineCommEnd = multiLineCommStart = foundEndOfSql = myObjCompleted = myPendingSql = mySubObjInProg = False
			waitingForSqlStart = True
			myBeginCount = myEndCount = myTotalTasks = mySuccessTasks = myFailedTasks = 0
			myValStatus = myValMessage = "" # for sql parsing validation result
			mySql = []
			mySqlLists = []
			mySqlHeader = []
			mySqlTypeInfo = ()
			myStartTime = self.util.lambdaGetCurrDateTime()

			if startExecSeq: 
				mySqlOrder = startExecSeq
			else:
				mySqlOrder = 0
			
			# processing contents of sql, expecting generator is used while reading text file 
			for line in self.util.readTxtFileLineGen(sqlFile):

				#print("os details >>> ", self.util.getOsDetails())
				line = line.replace("\n"," ")
				self.LOGGER.debug("processing line > {line}, waitingForSqlStart (var) > {sqlStart}".format(line = line, sqlStart = waitingForSqlStart))

				if not (isInParsingSql or isInParsingStoredObj):
					if not line.strip():
						# skipping emptry line if out of sql and object
						#print("found empty line (not part of sql), skipping",line)
						self.LOGGER.debug("found empty line, not part of a sql, skipping")

						continue
					elif self.util.isTextStartsWithKW(line, self.SKIP_KWLIST_IN_SQLFILE):
						self.LOGGER.debug("found ignore keyword from list > {kwList}".format(kwList = self.SKIP_KWLIST_IN_SQLFILE))
						#print("found ignore kw (not part of sql), skipping",line)
						continue

				# parsing comments started
				if not multiLineCommStart:
					multiLineCommStart = self.isMultiLineCommStart(securityToken, line)

				multiLineCommEnd = self.isMultiLineCommEnd(securityToken, line)

				if multiLineCommStart:
					# resetting multiLineCommStart/End to its default value (False), if we got start and end of multi line comment
					# this would occur when multi line comment is used in a single line
					if multiLineCommEnd: 
						multiLineCommStart = multiLineCommEnd = False
					isCommentLine = True

				elif self.util.isTextStartsWithKW(line, self.SINGLE_LINE_COMMENT_KW_LIST):
					# single line comment
					if not isCommentLine: isCommentLine = True

				if isCommentLine:
					#print('comment processing, waitingForSqlStart/mySqlTypeInfo', waitingForSqlStart, mySqlTypeInfo)

					if (not waitingForSqlStart) and mySqlTypeInfo and  mySqlTypeInfo[0] in self.STORED_OBJ_START_OP_LIST:
						# sql parsing started, we are in creating stored object and found comment line, preserve this comment
						# but would skip parsing this comment line
						mySql.append(line.replace("\n"," "))
						#print("preserving comment part of stored object, skip parsing comment line >", line)
						self.LOGGER.debug("preserving comment part of stored object, skip parsing comment line >> {line}".format(line = line))

					elif (not waitingForSqlStart) and mySqlTypeInfo and mySqlTypeInfo[0] not in self.STORED_OBJ_START_OP_LIST:
						# sql parsing started, we are not in creating stored object and found comment line
						# would ignore and skip parsing this comment line
						# print("comment is not part of stored object, ignoring/skip parsing thie line >", line)
						self.LOGGER.debug("comment is not part of stored object, ignoring/skip parsing thie line >> {line}".format(line = line))

					elif waitingForSqlStart:
						#print("waiting for sql parsing to be started, ignore/skip comment line")
						self.LOGGER.debug("waiting for sql parsing to be started, ignore/skip this comment line")

					# skip parsing comment line
					isCommentLine = False
					continue

				# parsing comment ends

				if waitingForSqlStart:
					# ignore line with "/", if previous parsing was unsuccessful

					#if not myValStatus and line.strip() == "/":
					if line.strip() == "/":
						# found end of line marker "/" and sql is not started, skipping
						#print("found eol '/' doesnt belong to sql, skip peocessing this line")
						self.LOGGER.debug("found eol '/' doesnt belong to sql, skip peocessing this line")
						continue

					# adding line to sql header
					mySqlHeader.append(line)

					# validating sql header
					self.LOGGER.debug("validating sql header >> {header}".format(header = " ".join(mySqlHeader)))

					myValStatus, myValMessage = self.validateSqlHeader(securityToken, " ".join(mySqlHeader))
					
					#print("validation status for sql >>>", mySqlHeader, myValStatus, myValMessage)

					self.LOGGER.debug("sql header validation result >> {result}".format(result = "".join([str(myValStatus), ',', myValMessage])))

					if not myValStatus:
						# if validation is unsuccesful, will keep adding lines to sql header without processing, unless we got successful
					
						self.LOGGER.debug("sql header validation is unsuccessful !!")

						mySqlTypeInfo = self.getSqlHeader(securityToken, "".join(mySqlHeader))
					
						#print("sql type info for <{sqlheader}> >".format(sqlheader = mySqlHeader), mySqlTypeInfo)
						self.LOGGER.debug("sql type info from sql header {header} >> result > {result}".format(header = "".join(mySqlHeader), result = mySqlTypeInfo))
						
						#print("sql type info from sql header {header} >> result > {result}".format(header = "".join(mySqlHeader), result = mySqlTypeInfo))
						if mySqlTypeInfo[0] in ["create procedure","create package","create function","create trigger"]:
							myEolMarkerList = ["/"]
						else:
							myEolMarkerList = [";","/"]

						#print("eol marker >>>", myEolMarkerList)
						self.LOGGER.debug("end of sql statement marker [{marker}] will be used for this sql ".format(marker = str(myEolMarkerList)))
	
						if not self.util.isTextEndsWithKW(line, myEolMarkerList):
							# skipping processing, we did not encounter end of sql marker (;,/)
							self.LOGGER.debug("end of statement marker not found, adding this line to sql header, skip processing this line")
							mySql.append(line.replace("\n"," "))
							#print("eol not found for sql, skip parsing this line", mySql)
							continue
						else:
							# we found end of line marker but sql header is missing mandatory comp
							# will get object details, needed to store this as failed parsing
							#mySqlType, mySqlObjType, mySqlOp, mySqlObjName, mySqlObjOwner = self.getObjDetail(securityToken, " ".join(mySqlHeader))
							#print("eol found for sql, proceeding with parsing ", mySql, mySqlType)
							self.LOGGER.debug("end of statement marker found, will proceed with parsing")
							#pass
					else:
						#print("sql header is ready, proceeding withe line >", line, "mysql header >", mySqlHeader)
						self.LOGGER.debug("sql header validation is successful, proceeding")

						mySqlTypeInfo = self.getSqlHeader(securityToken, "".join(mySqlHeader))
						#print("sql type info for <{sqlheader}> >".format(sqlheader = mySqlHeader), mySqlTypeInfo)

						self.LOGGER.debug("sql header object >> {result}".format(result = str(mySqlTypeInfo)))

						self.LOGGER.debug("resetting default value for inParsingSql (True), waitingForSqlStart (False)")
	
						isInParsingSql = True
						waitingForSqlStart = False
										
				#print("parsing obj detail from sql header >", "".join(mySqlHeader))
				#print("mySqlHeader > ", mySqlHeader)
				self.LOGGER.debug("parsing obj detail from sql header > {header}".format(header = str(mySqlHeader)))

				mySqlType, mySqlObjType, mySqlOp, mySqlObjName, mySqlObjOwner = self.getObjDetail(securityToken, " ".join(mySqlHeader))
				#self.LOGGER.info("sql object details found >>> {sqlObj}".format(sqlObj = "".join([mySqlType,".",mySqlObjType,".",mySqlOp,".",mySqlObjName,".",mySqlObjOwner])))
				#print("sql object details found >>> {sqlObj}".format(sqlObj = "".join([mySqlType,".",mySqlObjType,".",mySqlOp,".",mySqlObjName,".",mySqlObjOwner])))
				self.LOGGER.debug("sql object details found >>> {sqlObj}".format(sqlObj = "".join([mySqlType,".",mySqlObjType,".",mySqlOp,".", str(mySqlObjName),".", str(mySqlObjOwner)])))

				if not(mySqlType and mySqlOp):
					raise ValueError("sql header parsing error, unable to determine sql type/operation from [{sqlHeader}] , aborting !!! >>>".format(sqlHeader = str(mySqlHeader)))

				#print("sql type {type} found from >".format(type = mySqlType)," ".join(mySqlHeader))

				if not myValStatus:
					# sql header parsing validation failed, will log this sql as failed parsing
					#mySql.append(line.replace(";","").replace("/","").replace("\n",""))
					#print("parsing unsuccessful",mySql)
					self.LOGGER.debug("Validation is unsuccessful, wraping this sql >> {sql}".format(sql = "\n".join(mySql)))

					myFinalSql = "\n".join(mySql)
					mySqlOrder += 1
					myTotalTasks += 1
					myFailedTasks += 1

					mySqlObject = {
						"seq" : mySqlOrder,
						"taskType" : self.Globals.TASK_TYPE_USER,
						"op" : mySqlOp,
						"deployFile" : self.util.getFileName(sqlFile),
						#"sqlType" : mySqlType, 
						"opType" : mySqlType, 
						"opStatement" : myFinalSql,
						"objOwner" : mySqlObjOwner, 
						"objName" : mySqlObjName, 
						"objType" : mySqlObjType,
						"status" : self.Globals.unsuccess,
						"message" : myValMessage
					}

					self.LOGGER.debug("sql object built (validation unsuccessful) >> {sql}".format(sql = str(mySqlObject)))

					mySqlLists.append(mySqlObject)
					#self.util.write2JsonFile(parseFile, mySqlObject)

					# resetting all variable since this sql parsing is completed	
					mySqlType = mySqlObjType = mySqlOp = mySqlObjName = mySqlObjOwner = ""
					if isInParsingStoredObj: isInParsingStoredObj = False
					if isInParsingSql: isInParsingSql = False

					isInParsingSql = foundEndOfSql = myObjCompleted = myPendingSql = False
					waitingForSqlStart = True # this sql ended will wait for new sql parsing to be started
					mySql = []
					mySqlHeader = []
					#self.util.releaseMemory()
					continue

				if mySqlType in [self.SQL_TYPE_QUERY, self.SQL_TYPE_TXN, self.SQL_TYPE_DML, self.SQL_TYPE_DCL]:
					if self.util.isTextEndsWithKW(line, [";","/"]):
						foundEndOfSql = True

				elif mySqlType == self.SQL_TYPE_DDL:
					if "".join([mySqlObjType,".",mySqlOp]) == "package.spec.create":
						if not isInParsingStoredObj:
							#print("found stored obj create (pkg.spec)")
							isInParsingStoredObj = True

						#print("checking end of package spec marker in line ",line)
						# remove owner name from object when looking for eol marker
						myEolMarkerList = ["end;", "".join(["end ", mySqlObjName.split(".")[-1:][0],";"]), "".join(["end ", mySqlObjName,";"]) ]
						if self.util.isTextStartsWithKW(line,myEolMarkerList):
							#print("found stored obj create (pkg.spec) end marker")
							myObjCompleted = True
						
						#print("obj completed > ", myObjCompleted, ', line >', line)
						
						if myObjCompleted and line.strip() == "/":
							#print("pkg spec completed >", myObjCompleted, "line >", line)
							# obj is completed, found end of object marker "/"
							foundEndOfSql = True

					# checking for package body
					elif "".join([mySqlObjType,".",mySqlOp]) == "package.body.create":
						# this is package body we need to check each begin which may end with its object
						if not isInParsingStoredObj:
							#print("found stored obj create (pkg.body)")
							isInParsingStoredObj = True

						if self.util.isTextStartsWithKW(line, ["procedure","function"]):
							# retrieving obj name in package body so we can correctly fix end of object which may end with 
							# 'end' or 'end <objectName>'
							myCurrObjInPkg = [obj for obj in line.strip().split(" ") if obj][1]
							mySubObjInProg = True
						
						if mySubObjInProg:
							# we are in sub object of package, will check for each begin and end
							if self.util.isTextStartsWithKW(line,["begin"]):
								myBeginCount += 1;
							elif  self.util.isTextStartsWithKW(line,["end;", "".join(["end ", myCurrObjInPkg,";"]) ]):
								# found end for begin or end with object name (end <objname>;)
								myBeginCount -= 1;

								# checking if we got begin count to 0, we need this condition under this block
								if myBeginCount == 0:
									mySubObjInProg = False
						
						#print("checking end of package body marker in line ",line)
						# checking if we found end for package body (end or end <package name>)
						myEolMarkerList = ["end;", "".join(["end ", mySqlObjName.split(".")[-1:][0],";"]), "".join(["end ", mySqlObjName,";"]) ]
						if self.util.isTextStartsWithKW(line,myEolMarkerList):
							myObjCompleted = True
							#print("found package body create end marker")

						#print("pkg body completed >", myObjCompleted, "line >", line)
						if myObjCompleted and line.strip() == "/":
							# obj is completed, found end of object marker "/"
							foundEndOfSql = True

					elif "".join([mySqlObjType,".",mySqlOp]) in ["procedure.create","function.create","trigger.create"]:
						#print("found stored obj create (procedure,function,package,trigger)")
						# we need a way to find the end of ddl
						# this is create procedure/function/trigger							
						if self.util.isTextStartsWithKW(line,["begin"]):
							myBeginCount += 1;

						elif self.util.isTextStartsWithKW(line,["end;", "".join(["end ", mySqlObjName,";"]) ]):
							# found end for begin or end with object name (end <objname>;)
							myBeginCount -= 1;

							if myBeginCount == 0:
								myObjCompleted = True
								#print("found stored obj (proc/func/trigger) create end marker")
						if myObjCompleted and line.strip() == "/":
							#print('eol found for pro/func/trig')
							foundEndOfSql = True

						#print("begin cnt > ", myBeginCount, "line >", line)
					else:
						"""
						print("".join([mySqlObjType,".",mySqlOp]))
						print("this is not proc/func/pkg/trig sql, we dont need to check for begin/end, we need ;")
						print("checking for end of sql, parsing > ", line)
						"""
						if self.util.isTextEndsWithKW(line, [";","/"]):
							#print("found ddl end marker")
							foundEndOfSql = True

				if foundEndOfSql:
					# adding last line of sql by removing end of sql character ';','/'
					if line.replace(";"," ").replace("/"," ").replace("\n"," ").strip():
						self.LOGGER.debug("adding line (to current sql) >> {line}".format(line = str(line)))
						#print("adding sql >>>", mySql)
						mySql.append(line)

					myFinalSql = "\n".join(mySql)
					#print("final sql >>", myFinalSql)
					mySqlOrder += 1
					myTotalTasks += 1

					# we are here because our validation was successful, checking for object owner
					# we might have multiple table therefor need to valiate if all table has its owner
					if mySqlType == self.SQL_TYPE_QUERY:
						myValStatus = self.Globals.success
						for owner in mySqlObjOwner:
							if not owner:
								myValMessage = "missing object owner"
								myValStatus = self.Globals.unsuccess
								break
						mySqlObjOwner = ','.join(map(str, mySqlObjOwner))
						mySqlObjName = ','.join(map(str, mySqlObjName))
					else:
						# checking if we got owner, which is excluded from sql header validation
						if myValStatus  and not mySqlObjOwner and \
							mySqlType in [ self.SQL_TYPE_DDL, self.SQL_TYPE_DML ]:
							myValStatus = self.Globals.unsuccess
							myValMessage = "missing object owner"
						else:
							myValStatus = self.Globals.success

					if myValStatus == self.Globals.success:
						mySuccessTasks += 1
					else:
						myFailedTasks += 1

					# removing last character ";" if found in final sql excluding sql for create procedure/package/function/trigger and block sql

					if mySqlType == self.SQL_TYPE_DDL:
						if mySqlOp == "create" and mySqlObjType in ["package.spec","package.body","procedure","function","trigger"]:
							# task is creating stored objects would not remove ';'
							pass
						else:
							# task is ddl and not creating stored objects removing ';'
							if myFinalSql.rstrip().endswith(";"):
								myFinalSql = myFinalSql.rstrip()[: -1].rstrip()
							#mySql.append(line.replace("/",""))
					elif mySqlType == self.SQL_TYPE_BLK:
						myFinalSql = myFinalSql.rstrip()
					else:
						if myFinalSql.rstrip().endswith(";"):
							myFinalSql = myFinalSql.rstrip()[: -1].rstrip()
						else:
							myFinalSql = myFinalSql.rstrip()

					mySqlObject = {
						"seq" : mySqlOrder,
						"taskType" : self.Globals.TASK_TYPE_USER,
						"op" : mySqlOp,
						"deployFile" : self.util.getFileName(sqlFile),
						#"sqlType" : mySqlType, 
						"opType" : mySqlType, 
						"opStatement" : myFinalSql,
						"objOwner" : mySqlObjOwner, 
						"objName" : mySqlObjName, 
						"objType" : mySqlObjType,
						"status" : myValStatus,
						"message" : myValMessage
					}

					self.LOGGER.info(f"sql object details >>> str({mySqlObject}) ")

					mySqlLists.append(mySqlObject)
					
					# resetting all variable since this sql parsing is completed	
					if isInParsingStoredObj: isInParsingStoredObj = False
					if isInParsingSql: isInParsingSql = False

					isInParsingSql = foundEndOfSql = myObjCompleted = myPendingSql = False
					waitingForSqlStart = True # this sql ended will wait for new sql parsing to be started
					mySqlType = mySqlObjType = mySqlOp = mySqlObjName = mySqlObjOwner = mySqlTypeInfo = ""
					mySql = []
					mySqlHeader = []
					#self.util.releaseMemory()
				else:
					# adding line to mysql, no end of sql found
					self.LOGGER.debug('adding this line to mysql list')
					mySql.append(line.replace("\n"," "))

				# setting pending sql to true if we found a value in mysql
				if mySql: myPendingSql = True

			# cheking if we missed any mismatch of begin/end in objects (package/proc/func/trigger)
			if myPendingSql:
				#print("sql not added ....", mySql)
				#print("begin cnt > ", myBeginCount, "end marker >", foundEndOfSql, )
				raise ValueError("invalid sql file, sql is still pending to be added to final sql list !!!")
			else:
				return mySqlLists
				"""
				self.util.write2JsonFile(parseFile, mySqlLists)
				return {
					"totalTasks" : myTotalTasks,
					"parseStatus" : "success" if myFailedTasks == 0 else "unSuccess",
					"successParse" : mySuccessTasks,
					"unSuccessParse" : myFailedTasks 
				}
				"""
		except Exception as error:
			self.LOGGER.error("an error [{error}] occurred while parsing sql contents ".format(error = str(error)), exc_info = True)
			raise error
		finally:
			self.util.releaseMemory()

if __name__ == "__main__":
	sec = Security()
	mySecToken = sec.authenticate('DMZPROD01\\svc-dev-deploy-app','eXokNzl5NEUzOWdXNCkp')

	parser = Parser(mySecToken)
	"""
	#file = "p:\\app\\com\\mmc\\cicd\\config\\PSTG_TABLE_TRUNCATE.sql"
	#file = "p:\\app\\com\\mmc\\cicd\\config\\test_ora_pkg_Spec.sql"
	#file = "p:\\app\\com\\mmc\\cicd\\config\\px_cu_mi_move_subscription_pg.sql"
	#file = "p:\\app\\com\\mmc\\cicd\\config\\test_role_parser.sql"
	file = "p:\\app\\com\\mmc\\cicd\\config\\METADATA_DELETE.sql"
	#file = "p:\\app\\com\\mmc\\cicd\\config\\test_sql_file_parser.sql"
	print("Parsing sql file >>", file)
	myNewSqlList = parser.parseFile(mySecToken,file, 'oracle.sql')
	#myNewSqlJson = json.dump(myNewSqlList)
	print("sql parsing completed, printing sql object details .... ")
	#print("new sql list >>> \n", myNewSqlList, "\n")
	for sql in myNewSqlList:
		print("sql order : ", sql["seq"])
		print("op type : ", sql["sqlType"])
		print("op : ", sql["op"])
		print("op statement : ", sql["opStatement"])
		print("owner : ", sql["objOwner"])
		print("object : ", sql["objName"])
		print("objectType : ", sql["objType"])
		print("status : ", sql["status"])
		print("message : ", sql["message"])
	#print("new sql >>> \n", myNewSql, "\n completed ...")
	"""
	#myNewSqlList = parser.parseDeployFiles(mySecToken, "p:\\app\\cicd\\deploy","oracle")

	#securityToken, deployId, deployCtrlId, dbTechnology

	myResult = parser.parseDeployFiles(mySecToken, "deploy_test","001", "oracle")
	print("sql parsing completed, following file is generate by parser .... \n", myResult)
	#parser.util.write2JsonFile('p:\\app\\cicd\\deploy\\parse_output.json', myNewSqlList, 'w+')
	
	#parser._Parser__initOraVar(mySecToken)
	#parser.getObjDetail(mySecToken, "ALTER SESSION SET NLS_DATE_FORMAT = 'MM/DD/YYYY HH:MI:SSPM")
	"""
	print("new sql list >>> \n", myNewSqlList, "\n")
	for sql in myNewSqlList:
		print("sql order : ", sql["seq"])
		print("op : ", sql["op"])
		print("op type : ", sql["opType"])
		print("op statement : ", sql["opStatement"])
		print("owner : ", sql["objOwner"])
		print("object : ", sql["objName"])
		print("objectType : ", sql["objType"])
		print("status : ", sql["status"])
		print("message : ", sql["message"])
	#print("new sql >>> \n", myNewSql, "\n completed ...")
	"""