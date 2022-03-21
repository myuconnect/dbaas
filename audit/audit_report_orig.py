from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.security import Security
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.db.mongo_core import MongoCore

from com.mmc.audit.aud_globals import AuditGlobals
from com.mmc.audit.repository import Repository

import logging, logging.config, inspect, warnings, xlsxwriter
from os import system, name, getlogin
from sys import exit, stdout

class AuditReport(object, metaclass=Singleton):
	"""
	Generate report which would be sent to team via email
	"""
	def __init__(self, userId, userEncPass):

		self.infra = Infrastructure()
		self.sec = Security()
		self.util = Utility()
		
		self.ENVIRONMENT = self.util.getACopy(self.infra.environment)
		self.LOGGER = logging.getLogger(__name__)

		self.SECURITY_TOKEN = self.sec.authenticate(userId, userEncPass)

		self.Globals = AuditGlobals(self.SECURITY_TOKEN)

		self.repo = Repository(self.SECURITY_TOKEN)
		#self.mongo = MongoCore(self.SECURITY_TOKEN)
		self.mongo = MongoCore(self.SECURITY_TOKEN)
		# will build mongo uri for repository

		self.ENVIRONMENT = self.util.getACopy(self.infra.environment)

		self.CURRENT_WEEK = self.util.getCurWeekOfYear(self.util.getCurrentDate())
		self.CURR_WEEK_START_DATE, self.CURR_WEEK_END_DATE, = self.util.getWeekStartEndDate(self.util.getCurrentDate())

		self.ENV_TYPE = self.util.getEnvKeyVal("ENV").lower()
		"""
		self.REGION = self.ENVIRONMENT["env"]["REGION"]
		self.OPCO = self.ENVIRONMENT["env"]["OPCO"]
		self.DOMAIN = self.ENVIRONMENT["env"]["DOMAIN"]
		self.DC_LOCATION = self.ENVIRONMENT["env"]["DC_LOCATION"]

		self.HOST_ID = self.util.buildHostId(self.ENVIRONMENT["hostInfo"]["hostFQDN"], self.REGION, self.OPCO).lower()
		self.HOST_NAME_FQDN = self.ENVIRONMENT["hostInfo"]["hostFQDN"]
		self.HOST_NAME = self.ENVIRONMENT["hostInfo"]["hostName"]
		"""
		self.REPO_DB_TYPE = self.ENVIRONMENT["boot"]["repositoryDBType"]

		self.MONGO_AUD_FILTER = self.ENVIRONMENT["dbConfig"][self.Globals.DB_TYPE_MONGO]["auditFilter"]

		# we need to find repository databse config
		if self.ENV_TYPE.lower() not in self.ENVIRONMENT["boot"]["repositoryDB"][self.REPO_DB_TYPE]:
			raise ValueError("Missing environment specific db repository metadata for {env} !!!".format(env = self.ENV_TYPE))

		self.COMPONENT_CONFIG = self.util.getDictKeyValue(self.ENVIRONMENT["boot"]["repositoryDB"][self.REPO_DB_TYPE], self.ENV_TYPE)

		self.COMP_HOSTS = self.util.getDictKeyValue(self.COMPONENT_CONFIG, "hosts")
		self.COMP_REPLICA = self.util.getDictKeyValue(self.COMPONENT_CONFIG,"replicaSet")
		self.COMP_ADMIN = self.util.getDictKeyValue(self.COMPONENT_CONFIG, "userId")
		self.COMP_ADMIN_ENCPASS = self.util.getDictKeyValue(self.COMPONENT_CONFIG, "userEncPass")
		self.COMP_USER_TYPE = self.util.getDictKeyValue(self.COMPONENT_CONFIG,"userType")
		self.COMP_AUTHDB = self.util.getDictKeyValue(self.COMPONENT_CONFIG, "authDB")
		self.COMP_AUTH_MODE = self.util.getDictKeyValue(self.COMPONENT_CONFIG,"authMech")
		self.COMP_DB = self.util.getDictKeyValue(self.COMPONENT_CONFIG,"db")
		#self.COMP_DB = "audit_prod"

		# generate xlsx file attribute
		# xlsx file
		self.XLSX_LOCATION = self.ENVIRONMENT["app_log_loc"]
		self.MONGO_AUD_XLSX_FILE = "mongo_aud_{region}_{date_range}.xlsx"
		self.MONGO_AUD_HEADER = "Mongo Audit Report"

		self.MONGO_ROOT_ACCESS_XLS_FILE = "mongo_root_{date_range}.xlsx"
		self.MONGO_ROOT_PRIV_HEADER = "Mongo Root Admin Report"
		self.ALL_REGION = ["NAM","EMEA","APAC"]


		# collection
		self.CTFY_GRP_COLL = "centrify.groups"
		self.COMPLIANCE_LISTS_COLL = "compliance.lists"
		self.PRODUCT_VERSION_COLL = "product.version"
		self.COMP_EXCEP_COLL = "compliance.exception"
		self.ADMIN_LISTS_COLL = "admin.lists"

		self.HOSTS_COLL = "hosts"
		self.HOST_SCAN_COLL = "host.scans"

		self.TENANTS_COLL = "tenants"
		self.TENANT_SCAN_COLL = "tenant.scans"
		self.TENANT_USER_COLL = "tenant.users"
		self.TENANT_ROLE_COLL = "tenant.roles"
		self.TENANT_CONFG_COLL = "tenant.configs"
		self.TENANT_VERSION = "tenant.versions"
		#self.TENANT_COMP_COLL = "tenant.compliance.prod"
		self.TENANT_COMP_COLL = "tenant.compliances"
		self.TENANT_AUDIT_COLL = "tenant.audits"

		# creating Mongo Uri for this component
		self.MONGO_URI = self.mongo.buildMongoUri(self.SECURITY_TOKEN, \
			hosts = self.COMP_HOSTS, \
			userName = self.COMP_ADMIN, userType = self.COMP_USER_TYPE,\
			authDb = self.COMP_AUTHDB, authMech = self.COMP_AUTH_MODE, replicaSet = self.COMP_REPLICA)

	def getMongoRegionFromMembers(self, members):
		pass

	def getAllTenant4Region(self, region):
		# region : ALL or region name, region column does not exists
		try:
			if region is None or region == "ALL":
				{"members" : {"$exists" : True}}
			else:
				myRegion = "".join(["/",region,"/"])
				{"members.hostId" : myRegion }

			myProjection = {"tenantName" : 1, "_id" : 0}

			myDBResult = self.mongo.findDocuments(\
				self.SECURITY_TOKEN, uri = self.MONGO_URI, userName = self.COMP_ADMIN, userEncPass = self.COMP_ADMIN_ENCPASS,\
				db = self.COMP_DB, collection = self.TENANTS_COLL, \
				criteria = myCriteria, projection = myProjection )
			
			myAllTenants = [tenant["tenantName"] for tenant in myDBResult]

			return myAllTenants

		except Exception as error:
			raise error

	def getAllTenantHost4Region(self, dbTechnology, region):
		# region : ALL or region name, region column does not exists
		try:
			myCriteria = {"dbTechnology" : dbTechnology}
			if not(region is None or region == "ALL"):
				myCriteria.update({"region" : region})

			myProjection = {"_id" : 1}

			myDBResult = self.mongo.findDocuments(\
				self.SECURITY_TOKEN, uri = self.MONGO_URI, userName = self.COMP_ADMIN, userEncPass = self.COMP_ADMIN_ENCPASS,\
				db = self.COMP_DB, collection = self.TENANTS_COLL, \
				criteria = myCriteria, projection = myProjection )
			
			return myDBResult

		except Exception as error:
			raise error

	def getAllTenantHost4MongoRS(self, rsList):
		# region : ALL or region name, region column does not exists
		try:
			myCriteria = {
				"dbTechnology" : self.Globals.DB_TYPE_MONGO,
				"tenantName" : {"$in" : rsList}
			}
			myProjection = {"members.hostId" : 1,"_id":0}

			myDBResult = self.mongo.findDocuments(\
				self.SECURITY_TOKEN, uri = self.MONGO_URI, userName = self.COMP_ADMIN, userEncPass = self.COMP_ADMIN_ENCPASS,\
				db = self.COMP_DB, collection = self.TENANTS_COLL, \
				criteria = myCriteria, projection = myProjection )
			
			myAllHosts = []

			for tenant in myDBResult:
				for host in tenant["members"]:
					myAllHosts.append(host["hostId"])

			return myAllHosts

		except Exception as error:
			raise error

	def getMongoAudRep4Region(self, region, startDate, endDate):
		"""
			param1 : region (ALL)
			param2 : startdate (yyyy-mm-dd hh24:mi:ss) inclusive of start date
			param3 : startdate (yyyy-mm-dd hh24:mi:ss) inclusive of end date
		"""
		try:
			if isinstance(startDate, str):
				myStartDate = self.util.convertStrDate2DateTime(startDate, "%Y-%m-%d")

			if isinstance(endDate, str):
				myEndDate = self.util.convertStrDate2DateTime(endDate, "%Y-%m-%d")

			# get all hosts for 'mongo' database technology
			myAllHostId = self.getAllTenantHost4Region(self.Globals.DB_TYPE_MONGO, region)

			myCriteria = {
				"dbTechnology" : self.Globals.DB_TYPE_MONGO, "hostId" : {"$in" : myAllHostId},
				"ts" :{"gte" : myStartDate, "$lte" : myEndDate}
			}
			
			myProjection = {
				"atype" : 1, "ts" :1, "users" :1, "roles" : 1, "prarm" : 1, "status" : 1, "closedBy" : 1,
				"closedDate" : 1, "comments" : 1
			}

			# we need to get audit for all the hosts identified above
			if myAllHostId:
				myRegionAuditData = self.getMongoAudRep4Hosts(myAllHostId, startDate, endDate)
				return myRegionAuditData

		except Exception as error:
			raise error

	def getMongoAudRep4RS(self, startDate, endDate, replicaSet):
		"""
			param3: startdate (yyyy-mm-dd hh24:mi:ss)
			param4: startdate (yyyy-mm-dd hh24:mi:ss)
		"""
		try:
			myStartDate = self.util.convertStrDate2DateTime(startDate, "%Y-%m-%d")
			myEndDate = self.util.convertStrDate2DateTime(endDate, "%Y-%m-%d")

			if not isinstance(replicaSet, list):
				replicaSet = [replicaSet]

			myAllHosts = self.getAllTenantHost4MongoRS(replicaSet)

			if myAllHosts:
				myAllAuditData = self.getMongoAudRep4Hosts(myAllHosts)
				return myDBResult
			
		except Exception as error:
			raise error

	def getMongoAudRep4Hosts(self, hostIdList, startDate, endDate):
		"""
			param1 : hsotidList (ALL)
			param2 : start date
			param3 : end date
		"""
		try:
			if isinstance(startDate, str):
				myStartDate = self.util.convertStrDate2DateTime(startDate, "%Y-%m-%d")

			if isinstance(endDate, str):
				myEndDate = self.util.convertStrDate2DateTime(endDate, "%Y-%m-%d")

			myCriteria = {
				"dbTechnology" : self.Globals.DB_TYPE_MONGO, 
				"ts" :{"gte" : myStartDate, "$lte" : myEndDate}
			}
			myProjection = {
				"atype" : 1, "ts" :1, "users" :1, "roles" : 1, "prarm" : 1, "status" : 1, "closedBy" : 1,
				"closedDate" : 1, "comments" : 1
			}

			if not(hostIdList[0].upper() == "ALL"):
				myCriteria.update({"hostId" : {"$in" : myAllHostId}})

			# we need to get audit for all the hosts identified above

			myDBResult = self.mongo.findDocuments(\
				self.SECURITY_TOKEN, uri = self.MONGO_URI, userName = self.COMP_ADMIN, userEncPass = self.COMP_ADMIN_ENCPASS,\
				db = self.COMP_DB, collection = self.TENANT_AUDIT_COLL, \
				criteria = myCriteria, projection = myProjection )

			return myDBResult

		except Exception as error:
			raise error


	def getMongoRootAssigned2Users(self):
		"""
		return all role which has root role being assigned to
		"""
		try:
			myPipeline =  [
				{"$unwind" : "$users"},
				{"$unwind" : "$users.roles"},
				{"$match": {"users.roles.role" : "root"}},
				{"$project" : {"tenantName" : 1, "users" : {"user" :1}}}
			]

			myDBResult = self.mongo.runAggregate(self.SECURITY_TOKEN, \
				uri = self.MONGO_URI, userName = self.COMP_ADMIN, userEncPass = self.COMP_ADMIN_ENCPASS,\
				db = self.COMP_DB, collection = self.TENANT_USER_COLL, \
				pipeline = myPipeline)

			myResult = []

			if "data" in myDBResult and myDBResult["data"]:
				# get distinct replica set name from db result
				myDistinctRS = set([tenant["tenantName"] for tenant in myDBResult["data"]])
				myResult = []
				print(myDBResult)
				for rs in myDistinctRS:
					# find all the users from db results for each rs as determined above
					myRSUsers = [ user["users"] for user in myDBResult["data"] if user["tenantName"] == rs]
					myResult.append({"rs" : rs, "users" : myRSUsers})
	
			return myResult
		
		except Exception as error:
			raise error

	def getMongoRootAssigned2Roles(self):
		"""
		return all role which has root role being assigned to
		"""
		try:
			myPipeline =  [
				{"$unwind" : "$roles"},
				{"$unwind" : "$roles.roles"},
				{"$match": {"roles.roles.role" : "root"}},
				{"$project" : {"tenantName" : 1, "roles" : {"role" : 1,"users" : 1}}}]

			myDBResult = self.mongo.runAggregate(self.SECURITY_TOKEN, \
				uri = self.MONGO_URI, userName = self.COMP_ADMIN, userEncPass = self.COMP_ADMIN_ENCPASS,\
				db = self.COMP_DB, collection = self.TENANT_ROLE_COLL, \
				pipeline = myPipeline)

			myResult = []

			if "data" in myDBResult and myDBResult["data"]:
				# get distinct replica set name from db result
				myDistinctRS = set([tenant["tenantName"] for tenant in myDBResult["data"]])
				myResult = []
				for rs in myDistinctRS:
					# find all roles and its users for each rs as determined above
					myRSRoleUsers = [ role for role in myDBResult["data"] if role["tenantName"] == rs]
					myResult.append({"rs" : rs, "roles" : myRSRoleUsers})
	
			return myResult
		
		except Exception as error:
			raise error

	def getMogoPrivsAssigned2DB(self, db):
		"""
		return all role which has root role being assigned to
		"""
		try:
			myPipeline =  [
				{"$unwind" : "$roles"},
				{"$unwind" : "$roles.roles"},
				{"$match": {"roles.roles.db" : db}},
				{"$project" : {"tenantName" : 1, "roles" : {"role" : 1, "roles" : 1, "users" : 1}}}]

			
			myDBResult = self.mongo.runAggregate(self.SECURITY_TOKEN, \
				uri = self.MONGO_URI, userName = self.COMP_ADMIN, userEncPass = self.COMP_ADMIN_ENCPASS,\
				db = self.COMP_DB, collection = self.TENANT_ROLE_COLL, \
				pipeline = myPipeline)

			myResult = []

			if "data" in myDBResult and myDBResult["data"]:
				# get distinct replica set name from db result
				myDistinctRS = set([tenant["tenantName"] for tenant in myDBResult["data"]])
				myResult = []
				for rs in myDistinctRS:
					# find all roles and its users for each rs as determined above
					myGrantedRole = [ role["roles"]["roles"] for role in myDBResult["data"] if role["tenantName"] == rs]
					myGranted2Role = [ role["roles"]["role"] for role in myDBResult["data"] if role["tenantName"] == rs]
					myGranted2RoleUser = [ role["roles"]["users"] for role in myDBResult["data"] if role["tenantName"] == rs]

					myResult.append({"rs" : rs, "db" : db, "grantedRoleOnDB" : myGrantedRole, "granted2Role" : myGranted2Role, "granted2RoleUsers" : myGranted2RoleUser})
	
			return myResult
		
		except Exception as error:
			raise error

	def writeHeader2XlsxFile(self, workBook, workSheet, header, startPos, mergeCellPos):
		try:
			myHeaderFormat = workBook.add_format({'bold' : True, 'font_color' : 'black', 'font_size' : 24, 'align' : 'center', 'border' : True, 'bg_color' : 'gray'})
			if mergeCellPos:
				myCellMergeFormat = workBook.add_format({'align': 'center', 'valign' : 'vcenter', 'border' : 1})
				workSheet.merge_range(mergeCellPos,"", myCellMergeFormat)
			
			workSheet.write_string(startPos, header, myHeaderFormat)
			
			return

		except Exception as error:
			raise error

	def writeColHeader2XlsxFile(self, workBook, workSheet, colHeaderList, row):
		# column position starts with 0. For e.g. (A5 = row 5, col0) (C5 = row 5, col 2)
		try:
			myColLabelFormatStr = workBook.add_format({'font_color' : 'white', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : 'blue'})

			for column in colHeaderList:
				#print("column >>>", column)
				workSheet.set_column( int(column["pos"]), int(column["pos"]), int(column["size"]))
				workSheet.write_string(int(row), int(column["pos"]),column["label"],myColLabelFormatStr)

			return

		except Exception as error:
			raise error

	def writeCellXlsxFile(self, workSheet, row, column, cellText, cellFormat):
		try:
			workSheet.write_string(int(row), int(column),cellText,cellFormat)

		except Exception as error:
			raise error

	def genMongoAudXlsxFile(self, startDateStr, endDateStr):
		"""
		param1: startDateStr (YYYY-MM-DD -> %Y-%m-%d)
		param2: endDateStr (YYYY-MM-DD -> %Y-%m-%d)
		"""
		try:
			# validating date str 
			print("generating mongo audit report for all region")
			self.genMongoAudXlsxFile4Region(self.ALL_REGION, startDateStr, endDateStr)

			# all region processing completed
			print("completed processing all regions Mongo audit weekly report")				

		except Exception as error:
			raise error

	def genMongoAudXlsxFile4Region(self, region, startDateStr, endDateStr):
		"""
		param1: region
		param2: startDateStr (YYYY-MM-DD -> %Y-%m-%d)
		param3: endDateStr (YYYY-MM-DD -> %Y-%m-%d)
		"""
		try:
			# validating date str 
			self.util.convertStrDate2DateTime(startDateStr, '%Y-%m-%d')
			self.util.convertStrDate2DateTime(endDateStr, '%Y-%m-%d')

			#print("split start date >>>", startDateStr.split("-"))
			#print("split end date >>>", endDateStr.split("-"))

			myPrintableDateRange = "".join([\
				startDateStr.split("-")[1],startDateStr.split("-")[2],startDateStr.split("-")[0],"_",\
				endDateStr.split("-")[1],endDateStr.split("-")[2],endDateStr.split("-")[0]
			])

			if not isinstance(region, list):
				myRegion = [region]
			else:
				myRegion = self.util.getACopy(region)

			for region in myRegion:
				print("processing region >>>", region.lower())
				# workbook starts here
				try:

					myAuditFile = self.util.buildPath(\
						self.XLSX_LOCATION,
						self.MONGO_AUD_XLSX_FILE.format(region = region, date_range = myPrintableDateRange))

					workBook = xlsxwriter.Workbook(myAuditFile)
					workBook.formats[0].set_font_size(11)

					# worksheet
					myWorkSheet = workBook.add_worksheet()

					# header
					self.writeHeader2XlsxFile(workBook, myWorkSheet, self.MONGO_AUD_HEADER,'B2', 'B2:K3')
		
					myColFormatStr = workBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True})
					myColFormatTS = workBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True})
					myColFormatDate = workBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'num_format':'yyyy-mm-dd'})

					self.writeCellXlsxFile(myWorkSheet,5, 1, "Region", myColFormatStr)
					self.writeCellXlsxFile(myWorkSheet,5, 2, region, myColFormatStr)
					self.writeCellXlsxFile(myWorkSheet,6, 1, "Start Date", myColFormatStr)
					self.writeCellXlsxFile(myWorkSheet,6, 2, startDateStr, myColFormatDate)
					self.writeCellXlsxFile(myWorkSheet,7, 1, "End Date", myColFormatStr)
					self.writeCellXlsxFile(myWorkSheet,7, 2, endDateStr, myColFormatDate)

					# data column label
					myColLabelList = [
						{"label" : "TimeStamp", "pos" : 1, "size" : 20},
						{"label" : "Action", "pos" : 2, "size" : 20},
						{"label" : "Users", "pos" : 3, "size" : 30},
						{"label" : "Roles", "pos" : 4, "size" : 30},
						{"label" : "Parameter", "pos" : 5, "size" : 20},
						{"label" : "Status", "pos" : 6, "size" : 20},
						{"label" : "Closed By", "pos" : 7, "size" : 20},
						{"label" : "Closed Date", "pos" : 8, "size" : 20},
						{"label" : "Supporting Doc", "pos" : 9, "size" : 20},
						{"label" : "Comments", "pos" : 10, "size" : 20},
					]
					self.writeColHeader2XlsxFile(workBook, myWorkSheet, myColLabelList, 8) # writing col header on row 8

					myMongoAuditData = self.getMongoAudRep4Region(region.lower(), startDateStr, endDateStr)

					myDataStartRow = 9
					
					myCellFormatStr = workBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True})
					myCellFormatTS = workBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'num_format':'yyyy-mm-dd hh:mm:ss.000'})

					if myMongoAuditData:
						for audit in myMongoAuditData:
							self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 1, audit["ts"], myCellFormatTS)
							self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 2, audit["action"], myCellFormatStr)
							self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 3, audit["users"], myCellFormatStr)
							self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 4, audit["roles"], myCellFormatStr)
							self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 5, audit["param"], myCellFormatStr)
							self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 6, audit["status"], myCellFormatStr)
							self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 7, audit["closedBy"], myCellFormatStr)
							self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 8, audit["closedDate"], myCellFormatStr)
							self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 9, "", myCellFormatStr) # place holder for supporting docs
							self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 9, audit["comments"], myCellFormatStr)
							myDataStartRow += 1

					if not myMongoAuditData:
						myEmptyCellStr = "<no records>"
						myEmptyCellFormat = workBook.add_format({'font_color' : 'gray', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True})
						self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 1, myEmptyCellStr, myEmptyCellFormat)
						self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 2, myEmptyCellStr, myEmptyCellFormat)
						self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 3, myEmptyCellStr, myEmptyCellFormat)
						self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 4, myEmptyCellStr, myEmptyCellFormat)
						self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 5, myEmptyCellStr, myEmptyCellFormat)
						self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 6, myEmptyCellStr, myEmptyCellFormat)
						self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 7, myEmptyCellStr, myEmptyCellFormat)
						self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 8, myEmptyCellStr, myEmptyCellFormat)
						self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 9, myEmptyCellStr, myEmptyCellFormat) # place holder for supporting docs
						self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 9, myEmptyCellStr, myEmptyCellFormat)
						print("no audit records found for region {region},  date {date}".format(region = region.lower(), date = "".join([startDateStr, ",", endDateStr])))

					#print(dir(workBook))
					#workBook.close() # no need since we are using context manager

					print("closing workbook, sending email to recipients ...")

					# sending email, attaching this file
					#util.sendEmail(senderEmal, toRecipients, ccRecipients, bccRecipients, subject, body, bodyType, fileAttachment)
					
					myCCRecpients = ""
					myBCCRecipients = ""
					mySubject = "Weekly Mongo Audit Report - {date_range}".format(date_range = "".join([startDateStr , " - ", endDateStr]))
					
					workBook.close()
					self.util.sendEmail(\
						self.Globals.NOTIFICATION_SERVICE_EMAIL, 
						"anil.singh@marsh.com",
						myCCRecpients, myBCCRecipients, mySubject,	
						self.Globals.WEEKLY_AUDIT_EMAIL_BODY, "html", 
						myAuditFile)
					
					print("finished processing audit data for region >>>", region.lower())
				except Exception as error:
					raise error
			# all region processing completed
			print("completed processing all regions Mongo audit weekly report")				
		except Exception as error:
			raise error

	def genMongoRootPrivs4Region(self, region):
		pass

	def genMongoRootRoleReportXlsx(self):
		"""
		replicaset : Str/List
		Add column Valid and validate against dbdocs
		"""
		try:
			myRootRole2RoleAssignment = self.getMongoRootAssigned2Roles()
			myRootRole2UserAssignment = self.getMongoRootAssigned2Users()

			myDateStr = self.util.convertDate2Str(self.util.getCurrentDate(), "%Y-%m-%d-%H-%M-%S")

			myPrintableDateRange = "".join([\
				myDateStr.split("-")[1], myDateStr.split("-")[2], myDateStr.split("-")[0],"_", \
				myDateStr.split("-")[3], myDateStr.split("-")[4], myDateStr.split("-")[5]
			])

			myRootPrivsFile = self.util.buildPath(\
				self.XLSX_LOCATION,
				self.MONGO_ROOT_ACCESS_XLS_FILE.format(date_range = myPrintableDateRange))

			# create workbook
			workBook = xlsxwriter.Workbook(myRootPrivsFile)
			workBook.formats[0].set_font_size(11)

			# worksheet
			myWorkSheet = workBook.add_worksheet("Mongo Root Privilege")

			# header
			self.writeHeader2XlsxFile(workBook, myWorkSheet, self.MONGO_ROOT_PRIV_HEADER,'B2', 'B2:K3')

			# data column label for roles
			myColLabelList = [
				{"label" : "Replica Set", "pos" : 1, "size" : 20},
				{"label" : "Granted To Role", "pos" : 2, "size" : 50},
				{"label" : "Granted To User", "pos" : 3, "size" : 25},
				{"label" : "Role", "pos" : 5, "size" : 50},
				{"label" : "User Id", "pos" : 6, "size" : 15},
				{"label" : "User Name", "pos" : 7, "size" : 25}
			]
			self.writeColHeader2XlsxFile(workBook, myWorkSheet, myColLabelList, 5) # writing col header on row 8
			
			myCellFormatStr = workBook.add_format({'font_color' : 'black', 'font_size' : 8, 'font_name' : 'Callibri', 'border' : True})

			# preparing data
			myRSRootPrivsData = []
			myUniqueRoleRS = set([rs["rs"] for rs in myRootRole2RoleAssignment])
			myUniqueUserRS = set([rs["rs"] for rs in myRootRole2UserAssignment])
			myUniqueRSList = list(myUniqueRoleRS.union(myUniqueUserRS))
			
			for rs in myUniqueRSList:
				# getting all roles which has root privilege for this rs
				myAllRolesDetails = [role["roles"] for role in myRootRole2RoleAssignment if role["rs"] == rs]
				myAllRoles = [role["roles"] for role in myAllRolesDetails[0]]

				# getting all users which has root privilege for this rs
				myAllUserDetails = [user["users"] for user in myRootRole2UserAssignment if user["rs"] == rs]
				myAllUsers = [user for user in myAllUserDetails[0]]

				myRSRootPrivsData.append({"rs" : rs, "roles" : myAllRoles, "users" : myAllUsers})

			myAllRootRoles = []

			# writing data to xlsx file
			myDataStartRow = 6
			for rs in myRSRootPrivsData:
				myReplicaSet = rs["rs"]
				self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 1, rs["rs"], myCellFormatStr)

				# writing role on same line of RS 
				myRoleStartRow = myDataStartRow
				for role in rs["roles"]:
					self.writeCellXlsxFile(myWorkSheet, myRoleStartRow, 2, role["role"], myCellFormatStr)
					# writing an empty str with border for user cell continuation
					self.writeCellXlsxFile(myWorkSheet, myRoleStartRow, 3, "", myCellFormatStr)
					myAllRootRoles.append(role["role"])
					myRoleStartRow += 1

				# writing user on same line of RS 
				myUserStartRow = myDataStartRow
				for user in rs["users"]:
					self.writeCellXlsxFile(myWorkSheet, myUserStartRow, 3, user["user"], myCellFormatStr)
					myUserStartRow += 1

				# setting myDataStartRow to max of user and role start row to ensure we are writing new rs details 
				#after all the role and user details are written for previous replica set
				myDataStartRow = max(myRoleStartRow, myUserStartRow) + 1

			#myDistinctRoles = list(set(myAllRootRoles)) (commenting this is case sensitive dup check, we need case insensitive)
	
			# removing duplicate roles (ignoring case)
			myDistinctRoles = self.util.removeDupFromList(myAllRootRoles)
	
			# writing role user information to xlsx file
			myDataStartRow = 6
			for role in myDistinctRoles:
				# scanning thru all RS, will come out once we find this role details
				for rs in myUniqueRSList:	
					myAllRoleUserDetails = [role["roles"] for role in myRootRole2RoleAssignment if role["rs"] == rs]
					# checking if this role exists in this rs role details
					myRoleDetails = [roleDetails["roles"] for roleDetails in myAllRoleUserDetails[0] if roleDetails["roles"]["role"] == role]
					# if found current role detials will exit
					if myRoleDetails: break


				# got role user details, writing to xls file
				#print("role users >>>", myRoleUserDetails)
				for role in myRoleDetails:
					self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 5, role["role"], myCellFormatStr)
					for user in role["users"]:
						self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 6, user["userId"], myCellFormatStr)
						self.writeCellXlsxFile(myWorkSheet, myDataStartRow, 7, user["userName"], myCellFormatStr)
						myDataStartRow += 1

					# leaving a line gap when writing next role users
					myDataStartRow += 1

			# closing workbook, sending email
			workBook.close()
			myCCRecpients = ""
			myBCCRecipients = ""
			mySubject = "Mongo Root Privilege Report"
			
			workBook.close()
			self.util.sendEmail(\
				self.Globals.NOTIFICATION_SERVICE_EMAIL, 
				"anil.singh@marsh.com",
				myCCRecpients, myBCCRecipients, mySubject,	
				self.Globals.MONTHLY_MONGO_ROOT_PRIVS_BODY, "html", 
				myRootPrivsFile)
			
			print("finished processing Mongo root privilege report")

		except Exception as error:
			raise error


if __name__ == "__main__":
	audRep = AuditReport("us02p01\\u1167965","U2FpQmFiYUNoYXJuYW0wMQ==")
	roles = audRep.getMongoRootAssigned2Roles()


	users = audRep.getMongoRootAssigned2Users()
	dbPrivs = audRep.getMogoPrivsAssigned2DB("mapsDocgenDb")

	print("root assigned to role")
	for role in roles:
		print(role)

	print("root assigned to users")
	for user in users:
		print(user)

	print("privs assigned to db >>> mapsDocgenDb")
	for privs in dbPrivs:
		print(privs)

	audRep.genMongoAudXlsxFile('2019-09-01', '2019-11-07')
	audRep.genMongoRootRoleReportXlsx()
