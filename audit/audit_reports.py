from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.security import Security
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.audit.mongo_repo import Repository

from com.mmc.audit.aud_globals import AuditGlobals

from xlsxwriter import Workbook, workbook

import logging, logging.config, sys

class Reports(object, metaclass=Singleton):
	"""
	generate and send Mongo Audit reports
	Colors:
		https://en.wikipedia.org/wiki/Web_colors
		Color name	RGB color code
		==========================		
		black		#000000
		blue		#0000FF
		brown		#800000
		cyan		#00FFFF
		gray		#808080
		green		#008000
		lime		#00FF00
		magenta		#FF00FF
		navy		#000080
		orange		#FF6600
		pink		#FF00FF
		purple		#800080
		red			#FF0000
		silver		#C0C0C0
		white		#FFFFFF
		yellow		#FFFF00

	"""
	def __init__(self, securityToken):
		self.util = Utility()
		self.infra = Infrastructure()
		self.sec = Security()
		self.util = Utility()
		self.repo = Repository(securityToken)
		self.Globals = AuditGlobals(securityToken)

		self.ENVIRONMENT = self.util.getACopy(self.infra.environment)

		if "app_log_loc" not in self.ENVIRONMENT:
			raise ValueError("bootstrap error, environment variable not set (app_locg_loc), aborting !!!")

		self.LOGGER = logging.getLogger(__name__)
		self.REPORT_LOC = self.util.buildPath(self.infra.environment["app_home_loc"], "reports")

		if not self.util.isDirExists(self.REPORT_LOC):
			self.util.createDir(self.REPORT_LOC)

		# defining heading format
		self.SUB_HEAD_FORMAT_OBJ = {'bold' : True, 'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : True}
		self.SUB_HEAD_VAL_FORMAT_OBJ = {'bold' : True, 'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : True}

		self.COL_HEAD_FORMAT_STR_OBJ = {'font_color' : 'white', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#000000'}
		self.COL_HEAD_FORMAT_DATE_OBJ = {'font_color' : 'white', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#000000'}
		self.COL_HEAD_FORMAT_TS_OBJ = {'font_color' : 'white', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#000000'}

		self.DATA_FORMAT_STR_OBJ = {'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False }
		self.DATA_FORMAT_STR_ERR_OBJ = {'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False, 'text_wrap': True }
		self.DATA_FORMAT_NUM_OBJ = {'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'num_format' : '###,####,###,##0', 'bold' : False }
		self.DATA_FORMAT_TS_OBJ = {'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'num_format':'yyyy-mm-dd hh:mm:ss.000', 'bold' : False }
		self.DATA_FORMAT_DATE_OBJ = {'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True , 'num_format':'mm/dd/yyyy', 'bold' : False}
		self.DATA_FORMAT_NON_COMP = {'font_color' : 'white', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : True, "bg_color" :  "#FF0000"}
		self.DATA_FORMAT_AT_RISK = {'font_color' : 'white', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : True, "bg_color" :  "#FF6600"}
		self.DATA_FORMAT_COMP = {'font_color' : 'white', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : True, "bg_color" :  "#008000"}

		self.AUDIT_EMAIL_BODY = """
Attn Team, 

Pls find attached Mongo audit report for date range {startDate} {endDate} for your review, do perform following steps. 

1. Update CA/CO# if available for all audit events\n
2. Send an email to regional lead along with this file\n
3. Once approved, upload this file to following sharepoint location\n
	https://sharepoint.mrshmc.com/sites/ts1/dbaportal/Audit%20Controls/Forms/AllItems.aspx?RootFolder=%2Fsites%2Fts1%2Fdbaportal%2FAudit%20Controls%2FWeekly%20Audit%20Action%20Review%20Documentation%2FNAM%2F2021%2FMongoDB&FolderCTID=0x012000CFA6120379B919408E36D0BB55929AE2&View=%7B7A5ABB5E%2DA680%2D43B8%2DB41C%2D4414FE209361%7D
	
			"""
		self.OPSMGR_ADMIN_REPORT_BODY = """
Attn Team, 

Pls find attached Mongo OpsMgr admin user report for opco {opco} for your review, do perform following steps for compliance. 

1. Pls review, validate and obtain Global Lead approval

2. Once approved, upload this file to following sharepoint location along will approval email

	https://sharepoint.mrshmc.com/sites/ts1/dbaportal/Audit%20Controls/Forms/AllItems.aspx?RootFolder=%2Fsites%2Fts1%2Fdbaportal%2FAudit%20Controls%2FMonthly%20Audit%20Review%20Documentation%2FNAM%2FDBA%20Account%20Reviews%2F2020%2FMongo&FolderCTID=0x012000CFA6120379B919408E36D0BB55929AE2&View=%7B7A5ABB5E%2DA680%2D43B8%2DB41C%2D4414FE209361%7D
	
			"""

		self.ADMIN_REPORT_BODY = """
Attn Team, 

Pls find attached {dbTechnology} admin user detailed report for opco {opco} for your review. 

		"""
		self.HOST_DETAIL_REPORT_EMAIL_BODY = """
Attn Team, 

Pls find attached {opco} {dbTechnology} database host detail report for your review. 

		"""
	def initXlsxFile(self, **kwargs):
		"""
		Initialize xlsx file (Add headeer, sheet and return the workbook object)

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string )
			:param arg2: file (string )
			:param arg3: sheet (string )
			:param arg4: border (string )
			:return: response (json --> {}} 
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				initXlsxFile('FnaGnyjuS-_bMQ6duQISpLwUf5ks0KwLw3zraoWdtGE', <file>, <sheet>, <border)

		.. note::
			
		.. warning:: 

		.. seealso:: 

		"""
		try:
			# logging arguments
			myModuleName = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(myKwArgs)])))

			# validating securityToken
			self.sec.validateSecToken(myKwArgs["securityToken"])

			myArgValidationList = [
				{"arg" : "file", "type" : str, "value" : myKwArgs["file"]}, 
				{"arg" : "header", "type" : str, "value" : myKwArgs["header"]},
				{"arg" : "headerCellRange", "type" : str, "value" : myKwArgs["headerCellRange"]},
				{"arg" : "sheet", "type" : str, "value" : myKwArgs["sheet"]},
				{"arg" : "border", "type" : dict, "value" : myKwArgs["border"]}			
			]

			self.util.valArguments2(myArgValidationList, ["sheet","border"])

			#print("file name >>>", myKwArgs["file"])

			if self.util.isFileExists(myKwArgs["file"]):
				raise ValueError(f"file {myKwArgs['file']} already exists !!!")

			# creating work book amd writing header to file
			#myWorkBook = Workbook(file, {'constant_memory': True, 'default_date_format': 'mm/dd/yyyy'})
			myWorkBook = Workbook(myKwArgs["file"], {'default_date_format': 'mm/dd/yyyy'})

			# creating sheet
			myWorkSheet = myWorkBook.add_worksheet(myKwArgs["sheet"])

			myWorkBook.formats[0].set_font_size(11)
			"""
			self.format_red_color = myWorkBook.add_format({'color' : 'red'})
			self.format_blue_color = myWorkBook.add_format({'color' : 'blue'})
			self.format_green_color = myWorkBook.add_format({'color' : 'green'})
			self.format_bold_color = myWorkBook.add_format({'bold' : True})
			"""
			# format
			format_header = myWorkBook.add_format({'bold' : True, 'font_color' : 'dark blue', 'font_size' : 28, 'align' : 'center', 'border' : True})
			date_format = myWorkBook.add_format({'bold' : True, 'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True})
			#header_format = myWorkBook.add_format({'bold' : True, 'font_color' : 'dark blue', 'font_size' : 24, 'align' : 'center', 'border' : True})

			header_cell_merge_format = myWorkBook.add_format({'align': 'center', 'valign' : 'vcenter', 'border' : 1})
			cell_merge_format = myWorkBook.add_format({'align': 'left', 'valign' : 'left', 'border' : 1})
		
			# merging cell for header
			myWorkSheet.merge_range('A1:B1', "", cell_merge_format)
			myWorkSheet.merge_range(myKwArgs["headerCellRange"], "", header_cell_merge_format)

			# writing header
			#myWorkSheet.write_string('A2', 'Mongo Audit Report - {date_range}'.format(date_range = "09/01/2019 to 09/06/2019"), header_format)
			myWorkSheet.write_string('A1', f"Date : {self.util.lambdaGetCurrReadableTime()}", date_format)
			myWorkSheet.write_string('A2', myKwArgs["header"], format_header)


			#mySubHeaderFormat = myWorkBook.add_format({'bold' : True, 'font_color' : 'dark blue', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : True})			
			mySubHeaderFormat = myWorkBook.add_format(self.SUB_HEAD_FORMAT_OBJ)
			mySubHeaderValueFormat = myWorkBook.add_format(self.SUB_HEAD_VAL_FORMAT_OBJ)

			#myWorkSheet.write_string("B4","Region :",mySubHeaderFormat)
			#myWorkSheet.write_string("B5", "Start Date :",mySubHeaderFormat)
			#myWorkSheet.write_string("B6", "End Date :",mySubHeaderFormat)

			#column_heading_format_str = myWorkBook.add_format(self.COL_HEAD_FORMAT_STR_OBJ)
			#column_heading_format_date = myWorkBook.add_format(self.COL_HEAD_FORMAT_DATE_OBJ)
			#column_heading_format_ts = myWorkBook.add_format(self.COL_HEAD_FORMAT_TS_OBJ)

			# creating border, if instructed
			if myKwArgs["border"]:
				myBorderSetting = myKwArgs["border"]
				if "topThickness" in myBorderSetting:
					myTopThickness = myBorderSetting["topThickness"]  
				else:
					myTopThickness = 1
				if "BotomThickness" in myBorderSetting:
					myBottomThickness = myBorderSetting["BotomThickness"]
				else:
					myBottomThickness = 1
				if "LeftThickness" in myBorderSetting:
					myLeftThickness = myBorderSetting["LeftThickness"]
				else:
					myLeftThickness = 1
				if "RightThickness" in myBorderSetting:
					myRightThickness = myBorderSetting["RightThickness"]
				else:
					myRightThickness = 1

				#thickness =1
				myWorkSheet.conditional_format(myBorderSetting["range"], \
					{'type': 'formula', 'criteria': 'True',\
						'format': myWorkBook.add_format({'top': myTopThickness, 'bottom':myBottomThickness,
						'left': myLeftThickness,'right':myRightThickness})})
			return myWorkBook, myWorkSheet

		except Exception as error:
			self.LOGGER.error(str(error), exc_info = True)
			raise error

	def genMongoAuditReport(self, **kwargs):
		"""
		Parameter:
			opco
			region
			tenantNameList
			startDate
			endDate
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			myKwArgs = self.util.getACopy(kwargs)

			myReportId = "mongo.weekly.aud.report"
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(myKwArgs)])))

			# validating securityToken
			self.sec.validateSecToken(myKwArgs["securityToken"])

			# checking for required arguments
			myRequiredArgList = ["securityToken","opco","env","dbTechnology","tenantList","startDate","endDate","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]}, 
				{"arg" : "env", "type" : str, "value" : myKwArgs["env"]}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				#{"arg" : "region", "type" : str, "value" : myKwArgs["region"]},
				{"arg" : "tenantList", "type" : list, "value" : myKwArgs["tenantList"]},
				{"arg" : "startDate", "type" : str, "value" : myKwArgs["startDate"]},
				{"arg" : "endDate", "type" : str, "value" : myKwArgs["endDate"]},
				#{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, ["recepient"])
			
			# validating startdate/endDate
			try:
				myStartDate = self.util.convStr2DateViaParser(myKwArgs["startDate"])
			except Exception as error:
				raise ValueError(f"Invalid start date {myKwArgs['startDate']}, error >>> {error}")

			try:
				myEndDate = self.util.convStr2DateViaParser(myKwArgs["endDate"])
			except Exception as error:
				raise ValueError(f"Invalid end date {myKwArgs['endDare']}")

			# retrieving sys config data
			mySysConfigData = self.repo.getSysConfig(myKwArgs["securityToken"], myKwArgs["opco"])

			if not mySysConfigData:
				raise ValueError(f"Sys config data for Opco --> {myKwArgs['opco']} is missing !!!")

			# retrieving this reports metadata from repository
			myReportMeta = [report for report in mySysConfigData["reports"] if report["reportId"] == myReportId]
			
			if not myReportMeta:
				raise ValueError(f"Report '{myReportId}' metadata is missing in repository !!")

			if myReportMeta:
				myReportMeta = myReportMeta[0]

			print(f"Report metadata >>> {myReportMeta}")

			myHeader = myReportMeta["reportHeader"]
			myHeaderCellRange = myReportMeta["cellRange"]
			myReportSheet = myReportMeta["sheetName"]

			myReportFileNamePrefix = myReportMeta["fileNamePrefix"]
			myReportFileRetDays = myReportMeta["retentionDays"]

			#myRecepient = myReportMeta["recepient"]
			
			#myNotificationDL = mySysConfigData["globalSettings"]["notificationDL"]

			# retrieving the data from repository
			#def getAuditEvent(self, securityToken, opco, env, dbTechnology, region, tenantList, startDate, endDate)
			myAtypeExcludeList = ["authCheck","authenticate"]
			myDBResult = self.repo.getAuditEvent(\
				#myKwArgs["securityToken"], myKwArgs["opco"], myKwArgs["region"], myKwArgs["tenantList"], \
				myKwArgs["securityToken"], \
				myKwArgs["opco"].upper(),  \
				myKwArgs["env"].lower(), \
				myKwArgs["dbTechnology"].lower(), \
				#myKwArgs["region"],  \
				myKwArgs["tenantList"], \
				myKwArgs["startDate"], myKwArgs["endDate"])

			# will send empty file if no audit records found, thus commenting below 2 lines
			#if not myDBResult:
			#	return self.util.buildResponse(self.Globals.success, f"no audit data found for {myKwArgs}")

			myFileName = self.util.buildPath(self.REPORT_LOC, \
				"".join([myReportFileNamePrefix, myKwArgs["opco"], "_", str(self.util.getCurDateTimeForDir()), ".xlsx"]))
			
			myWorkBook, myWorkSheet = self.initXlsxFile(\
				securityToken = myKwArgs["securityToken"], file = myFileName, \
				header = myHeader, headerCellRange = myHeaderCellRange, sheet = myReportSheet, border = {})

			# we will add following sub header to this file
			#mySubHeaderFormat = myWorkBook.add_format({'bold' : True, 'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : True})
			#mySubHeaderValueFormat = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : False})
			mySubHeaderFormat = myWorkBook.add_format(self.SUB_HEAD_FORMAT_OBJ)
			mySubHeaderValueFormat = myWorkBook.add_format(self.SUB_HEAD_VAL_FORMAT_OBJ)

			# adjusting column width
			""" commenting as this is done below adjusting column width
			myWorkSheet.set_column("A:B", 5, 15)
			myWorkSheet.set_column("A:B", 6, 15)
			myWorkSheet.set_column("A:B", 7, 15)
			myWorkSheet.set_column("A:B", 8, 15)
			myWorkSheet.set_column("A:B", 9, 15)
			"""
			# writing opco, region, start and end date
			myWorkSheet.write_string("A4","Opco",mySubHeaderFormat)
			#myWorkSheet.write_string("A5","Region",mySubHeaderFormat)
			myWorkSheet.write_string("A6","Tenant(s)",mySubHeaderFormat)
			myWorkSheet.write_string("A7", "Start Date",mySubHeaderFormat)
			myWorkSheet.write_string("A8", "End Date",mySubHeaderFormat)
			myWorkSheet.write_string("A9", "Total Audit Records#",mySubHeaderFormat)

			myTotAudRecords = len(myDBResult) if myDBResult else 0
			myWorkSheet.write_string("B4", myKwArgs["opco"],mySubHeaderValueFormat)
			#myWorkSheet.write_string("B5", "ALL",mySubHeaderValueFormat)
			myWorkSheet.write_string("B6", ",".join(myKwArgs["tenantList"]),mySubHeaderValueFormat)
			myWorkSheet.write_string("B7", myKwArgs["startDate"],mySubHeaderValueFormat)
			myWorkSheet.write_string("B8", myKwArgs["endDate"],mySubHeaderValueFormat)
			myWorkSheet.write_number("B9", myTotAudRecords,mySubHeaderValueFormat)

			# writing column header
			#column_heading_format_str = myWorkBook.add_format({'font_color' : 'white', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : 'light blue'})
			#column_heading_format_date = myWorkBook.add_format({'font_color' : 'white', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : 'light blue'})
			#column_heading_format_ts = myWorkBook.add_format({'font_color' : 'white', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : 'light blue'})

			#column_heading_format_str = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})
			column_heading_format_str = myWorkBook.add_format(self.COL_HEAD_FORMAT_STR_OBJ)
			column_heading_format_date = myWorkBook.add_format(self.COL_HEAD_FORMAT_DATE_OBJ)
			column_heading_format_ts = myWorkBook.add_format(self.COL_HEAD_FORMAT_TS_OBJ)

			myWorkSheet.set_column(0,5, 30) # sets column 0 to 1 (A:B) to 30
			#myWorkSheet.set_column(2,3, 30) # sets column 0 to 1 (C:D) to 30
			#myWorkSheet.set_column(4,7, 30) # sets column 0 to 1 (E:H) to 30

			myWorkSheet.write_string('A10',"Tenant",column_heading_format_str)
			myWorkSheet.write_string('B10',"TimeStamp",column_heading_format_str)
			myWorkSheet.write_string('C10',"Action",column_heading_format_str)
			myWorkSheet.write_string('D10',"Users",column_heading_format_str)
			myWorkSheet.write_string('E10',"Roles",column_heading_format_str)
			myWorkSheet.write_string('F10',"Parameter",column_heading_format_str)
			myWorkSheet.write_string('G10',"Supporting Doc (CO#)",column_heading_format_str)
			#myWorkSheet.write_string('G10',"Closed By",column_heading_format_str)
			#myWorkSheet.write_string('H10',"Closed Date",column_heading_format_date)

			# creating data format for audit data
			#https://en.wikipedia.org/wiki/Web_colors
			data_format_str = myWorkBook.add_format(self.DATA_FORMAT_STR_OBJ)
			data_format_num = myWorkBook.add_format(self.DATA_FORMAT_NUM_OBJ)
			data_format_ts = myWorkBook.add_format(self.DATA_FORMAT_TS_OBJ)
			data_format_date = myWorkBook.add_format(self.DATA_FORMAT_DATE_OBJ)

			# writing audit data to file
			myDataRow = 10 # this is row 11
			for audit in myDBResult:
				# building user data
				myDataList = []
				for user in audit["users"]:
					[myDataList.append(''.join([key, ':', user[key]])) for key in user]

				myUserData = ','.join(myDataList)
				#if audit["atype"] in ["createDatabase","dropDatabase","renameDatabase"]
				# ts, action, hostname, users, role, param
				if "tenantName" in audit:
					myWorkSheet.write_string(myDataRow,0,audit["tenantName"], data_format_str)
				else:
					myWorkSheet.write_string(myDataRow,0,audit["tenantId"], data_format_str)

				myWorkSheet.write_datetime(myDataRow,1,audit["ts"], data_format_ts)
				myWorkSheet.write_string(myDataRow,2, audit["atype"], data_format_str)
				if audit["users"]:
					myWorkSheet.write_string(myDataRow,3, self.util.convertDict2Str(audit["users"]), data_format_str)
				else:
					myWorkSheet.write_string(myDataRow,3, "", data_format_str)					
				if audit["roles"]:
					myWorkSheet.write_string(myDataRow,4, self.util.convertDict2Str(audit["roles"]), data_format_str)
				else:
					myWorkSheet.write_string(myDataRow,4, "", data_format_str)
				if audit["param"]:
					myWorkSheet.write_string(myDataRow,5, self.util.convertDict2Str(audit["param"]), data_format_str)
				else:
					myWorkSheet.write_string(myDataRow,5, "", data_format_str)
				myWorkSheet.write_string(myDataRow,6,"",data_format_str) # wrinting empty string for CO so we can get the border on cell
				#myWorkSheet.write_string(myDataRow,7, "",data_format_str)
				#myWorkSheet.write_string(myDataRow,7,audit["closedDate"],data_format_date)

				myDataRow += 1
			# close the workbook
			myWorkBook.close()

			if "recepient" in myKwArgs and myKwArgs["recepient"]:
				self.LOGGER.info(f"file {myFileName} is created, rcepient value is passed, sending email to {myRecepient}")
				myRecepient = myKwArgs["recepient"]
				mySubject = myReportMeta["subject"].format(opco = myKwArgs['opco'].upper())
				myEmailBody = myReportMeta["emailBody"].format(startDate = myKwArgs["startDate"], endDate = myKwArgs["endDate"]).replace("\\n","\n")
				myFromMailBox = (myReportMeta["from"], myReportMeta["fromEmail"])

				self.util.sendEmail(\
					myFromMailBox, \
					myRecepient, None, None, \
					mySubject, \
					myEmailBody, \
					'plain', myFileName)

				self.LOGGER.debug("email is sent, performing cleanup")

				myFilesDeleted = self.util.deleteFilesOlderThanDays(self.REPORT_LOC, ".xlsx", myReportFileRetDays)

				self.LOGGER.info(f"files older than {myReportFileRetDays} deleted >>> {myFilesDeleted}")

				return self.util.buildResponse(self.Globals.success, f'file {self.util.getFileName(myFileName)} is sent via email to {myRecepient}')
			else:
				return self.util.buildResponse(self.Globals.success, self.Globals.success, myFileName)

		except Exception as error:
			raise error

	def genOpsMgrUserReport(self, **kwargs):
		"""
		Parameter:
			opco
			region
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			myKwArgs = self.util.getACopy(kwargs)

			myReportId = "mongo.quarterly.opsMgr.admin.report" 

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(myKwArgs)])))

			# validating securityToken
			self.sec.validateSecToken(myKwArgs["securityToken"])

			# checking for required arguments
			myRequiredArgList = ["securityToken","opco","recepient","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},				
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}
			]

			self.util.valArguments2(myArgValidationList, [])
			
			# retrieving sys config data
			#mySysConfigData = self.repo.getSysConfig(myKwArgs["securityToken"], myKwArgs["opco"], myKwArgs["region"], self.Globals.DB_TYPE_MONGO)
			mySysConfigData = self.repo.getSysConfig(myKwArgs["securityToken"], myKwArgs["opco"])

			if not mySysConfigData:
				raise ValueError(f"Sys config data for Opco --> {myKwArgs['opco']} is missing !!!")

			myReportMeta = [report for report in mySysConfigData["reports"] if report["reportId"] == myReportId]
			
			if not myReportMeta:
				raise ValueError(f"Report '{myReportId}' metadata is missing in repository !!")

			if myReportMeta:
				myReportMeta = myReportMeta[0]

			print(f"Report metadata >>> {myReportMeta}")

			myDay, myDyName, myMonth, myMonthName, myYear = self.util.getEachElemOfDate(self.util.getCurrentDate())
			myMonthYear = "".join([myMonthName, " ", str(myYear)])

			myHeader = myReportMeta["reportHeader"]
			myHeaderCellRange = myReportMeta["cellRange"]
			myReportSheet = myReportMeta["sheetName"]

			myReportFileNamePrefix = myReportMeta["fileNamePrefix"]
			myReportFileRetDays = myReportMeta["retentionDays"]

			myRecepient = myKwArgs["recepient"]
			mySubject = myReportMeta["subject"].format(monthYear = myMonthYear, opco = myKwArgs['opco'].upper())
			myEmailBody = myReportMeta["emailBody"].format(opco = myKwArgs['opco'].upper(), monthYear = myMonthYear).replace("\\n","\n")
			myFromMailBox = (myReportMeta["from"], myReportMeta["fromEmail"])

			#myNotificationDL = mySysConfigData["globalSettings"]["notificationDL"]

			myOpsMgrUrlList = [category["opsMgrDetails"] for category in mySysConfigData["categories"] if category["category"] == "opsMgrReport" ]

			if myOpsMgrUrlList:
				myOpsMgrUrlList = myOpsMgrUrlList[0]

			if not myOpsMgrUrlList:
				return ValueError(f"Can not retrieve OpsMgrDetails from system config for opco {myKwArgs['opco']} !!")

			
			# retrieving OpsMgr user details for all OpsMgrUrl
			myDBResult = self.repo.getOpsMgrAdminUserList(securityToken = myKwArgs["securityToken"], opco = myKwArgs["opco"])

			if myDBResult["status"] == self.Globals.unsuccess:
				return myDBResult

			myOpsMgrData = myDBResult["data"]

			if not myOpsMgrData:
				return self.util.buildResponse(self.Globals.success, f"No OpsMgr admin user found for {myKwArgs}")

			myFileName = self.util.buildPath(self.REPORT_LOC, \
				"".join(["mongo_opsmgr_admin_report_", myKwArgs["opco"], "_", myMonthName, "_", str(myYear), "_", str(self.util.getCurDateTimeForDir()), ".xlsx"]))
			
			myWorkBook, myWorkSheet = self.initXlsxFile(\
				securityToken = myKwArgs["securityToken"], file = myFileName, \
				header = myHeader, headerCellRange = myHeaderCellRange, sheet = myReportSheet, border = {})

			# we will add following sub header to this file
			#mySubHeaderFormat = myWorkBook.add_format({'bold' : True, 'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : True})
			#mySubHeaderValueFormat = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : False})
			mySubHeaderFormat = myWorkBook.add_format(self.SUB_HEAD_FORMAT_OBJ)
			mySubHeaderValueFormat = myWorkBook.add_format(self.SUB_HEAD_VAL_FORMAT_OBJ)

			# writing opco, region, start and end date
			myWorkSheet.write_string("A4","Opco",mySubHeaderFormat)
			#myWorkSheet.write_string("A5","Region",mySubHeaderFormat)

			myWorkSheet.write_string("B4", myKwArgs["opco"],mySubHeaderValueFormat)
			#myWorkSheet.write_string("B5", myKwArgs["region"],mySubHeaderValueFormat)

			#column_heading_format_str = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})
			#column_heading_format_date = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})
			#column_heading_format_ts = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})
			column_heading_format_str = myWorkBook.add_format(self.COL_HEAD_FORMAT_STR_OBJ)
			column_heading_format_date = myWorkBook.add_format(self.COL_HEAD_FORMAT_DATE_OBJ)
			column_heading_format_ts = myWorkBook.add_format(self.COL_HEAD_FORMAT_TS_OBJ)

			myWorkSheet.set_column(0,5, 30) # sets column 0 to 1 (A:B) to 30

			myWorkSheet.write_string('A6',"URL",column_heading_format_str)
			myWorkSheet.write_string('B6',"Organization",column_heading_format_str)			
			myWorkSheet.write_string('C6',"ID",column_heading_format_str)
			myWorkSheet.write_string('D6',"Email",column_heading_format_str)
			myWorkSheet.write_string('E6',"Name",column_heading_format_str)

			# creating data format for audit data
			#https://en.wikipedia.org/wiki/Web_colors

			#data_format_str = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False })
			#data_format_ts = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'num_format':'yyyy-mm-dd hh:mm:ss.000', 'bold' : False })
			#data_format_date = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True , 'num_format':'mm/dd/yyyy', 'bold' : False})
			#data_format_str_err = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False, 'text_wrap': True })
			data_format_str = myWorkBook.add_format(self.DATA_FORMAT_STR_OBJ)
			data_format_num = myWorkBook.add_format(self.DATA_FORMAT_NUM_OBJ)
			data_format_ts = myWorkBook.add_format(self.DATA_FORMAT_TS_OBJ)
			data_format_date = myWorkBook.add_format(self.DATA_FORMAT_DATE_OBJ)
			data_format_str_err = myWorkBook.add_format(self.DATA_FORMAT_STR_ERR_OBJ)

			# writing Ops mgr user admin data to file
			myDataRow = 6 # this is row 7
			for url in myOpsMgrData:
				myWorkSheet.write_url(myDataRow,0, url["opsMgrUrl"],data_format_str)

				# checking if we were successfull retrieving admin user list from this url 
				if url["status"] == self.Globals.unsuccess:
					# this url 
					cell_merge_format = myWorkBook.add_format({'align': 'center', 'valign' : 'vcenter', 'border' : 1})
					# merging cell for header
					myWorkSheet.write_string(myDataRow,1,url["org"],data_format_str)
					myWorkSheet.merge_range(f'C{myDataRow}:E{myDataRow}', "", cell_merge_format)
					myWorkSheet.write_string(myDataRow,2, url["message"], data_format_str_err)
					# skipping this url processing as there was an error processing this url
					myDataRow += 1
					continue

				for user in url["users"]:
					myWorkSheet.write_string(myDataRow,1,url["org"],data_format_str)
					myWorkSheet.write_string(myDataRow,2,user["userName"],data_format_str)
					myWorkSheet.write_string(myDataRow,3,user["email"],data_format_str)
					myWorkSheet.write_string(myDataRow,4,user["name"],data_format_str)
	
					myDataRow += 1

			# close the workbook
			myWorkBook.close()

			self.LOGGER.info(f"file {myFileName} is created, sending email to {myRecepient}")

			self.util.sendEmail(\
				myFromMailBox, \
				myRecepient, None, None, \
				mySubject, \
				myEmailBody, \
				'plain', myFileName)

			self.LOGGER.debug("email is sent, performing cleanup")

			myFilesDeleted = self.util.deleteFilesOlderThanDays(self.REPORT_LOC, ".xlsx", myReportFileRetDays)

			self.LOGGER.info(f"files older than {myReportFileRetDays} deleted >>> {myFilesDeleted}")

			return self.util.buildResponse(self.Globals.success, f'file {self.util.getFileName(myFileName)} is sent via email to {myRecepient}')

		except Exception as error:
			self.LOGGER.error(str(error), exc_info = True)
			raise error

	def genAdminUserSummaryReport(self, **kwargs):
		"""
		parameter
			opco, region, dbTechnology
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			myKwArgs = self.util.getACopy(kwargs)

			myReportId = f"{myKwArgs['dbTechnology'].lower()}.monthly.superUser.report" 

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(myKwArgs)])))

			# validating securityToken
			self.sec.validateSecToken(myKwArgs["securityToken"])

			# checking for required arguments
			myRequiredArgList = ["securityToken","opco","recepient","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]}, 
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]},				
			]

			self.util.valArguments2(myArgValidationList, [])

			# retrieving sys config data
			mySysConfigData = self.repo.getSysConfig(myKwArgs["securityToken"], myKwArgs["opco"])

			if not mySysConfigData:
				raise ValueError(f"Sys config data for Opco --> {myKwArgs['opco']} is missing !!!")

			myReportMeta = [report for report in mySysConfigData["reports"] if report["reportId"] == myReportId]
			
			if not myReportMeta:
				raise ValueError(f"Report '{myReportId}' metadata is missing in repository !!")

			if myReportMeta:
				myReportMeta = myReportMeta[0]

			print(f"Report metadata >>> {myReportMeta}")
			
			myDay, myDyName, myMonth, myMonthName, myYear = self.util.getEachElemOfDate(self.util.lambdaGetCurrReadableTime())
			myMonthYear = "".join([myMonthName, " ", str(myYear)])

			myHeader = myReportMeta["reportHeader"].format(dbTechnology = myKwArgs["dbTechnology"].upper())
			myHeaderCellRange = myReportMeta["cellRange"]
			myReportSheet = myReportMeta["sheetName"]

			myReportFileNamePrefix = myReportMeta["fileNamePrefix"]
			myReportFileRetDays = myReportMeta["retentionDays"]

			myRecepient = myKwArgs["recepient"]
			mySubject = myReportMeta["subject"].format(opco = myKwArgs['opco'].upper(), dbTechnology = myKwArgs["dbTechnology"].upper(), monthYear = myMonthYear)
			myEmailBody = myReportMeta["emailBody"].format(opco = myKwArgs['opco'].upper(), monthYear = myMonthYear).replace("\\n","\n")
			myFromMailBox = (myReportMeta["from"], myReportMeta["fromEmail"])

			if myKwArgs["dbTechnology"] == self.Globals.DB_TYPE_MONGO:
				# request is for Mongo, retrieving Mongo Super user list

				myDBResult = self.repo.getMongoRootUserSummaryList(securityToken = myKwArgs["securityToken"], opco = myKwArgs["opco"])

				if myDBResult["status"] == self.Globals.unsuccess:
					return myDBResult

				mySuperUserList = myDBResult["data"]

				if not mySuperUserList:
					return self.util.buildResponse(self.Globals.success, f"No Super user found for OPCO: {myKwArgs['opco']}, DB Technology: {myKwArgs['dbTechnolgoy']} !!!")

				# building file name for this report, since we have got data
				myFileName = self.util.buildPath(self.REPORT_LOC, \
					"".join([myReportFileNamePrefix, myKwArgs["opco"], "_", str(myYear), "_", myMonthName, "_", str(self.util.getCurDateTimeForDir()), ".xlsx"]))
			else:
				return self.util.buildResponse(self.Globals.success, f"Super user report is not implemented for {myKwArgs['dbTechnolgoy']} !!!")

			# we are here because we have super user data which need to be processed
			# initializing file
			myWorkBook, myWorkSheet = self.initXlsxFile(\
				securityToken = myKwArgs["securityToken"], file = myFileName, \
				header = myHeader, headerCellRange = myHeaderCellRange, sheet = myReportSheet, border = {})

			# we will add following sub header to this file
			#mySubHeaderFormat = myWorkBook.add_format({'bold' : True, 'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : True})
			#mySubHeaderValueFormat = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : False})
			mySubHeaderFormat = myWorkBook.add_format(self.SUB_HEAD_FORMAT_OBJ)
			mySubHeaderValueFormat = myWorkBook.add_format(self.SUB_HEAD_VAL_FORMAT_OBJ)

			# writing opco, region, start and end date
			myWorkSheet.write_string("A4","Opco",mySubHeaderFormat)
			#myWorkSheet.write_string("A5","Region",mySubHeaderFormat)

			myWorkSheet.write_string("B4", myKwArgs["opco"],mySubHeaderValueFormat)
			#myWorkSheet.write_string("B5", myKwArgs["region"],mySubHeaderValueFormat)

			#column_heading_format_str = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})
			#column_heading_format_date = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})
			#column_heading_format_ts = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})

			column_heading_format_str = myWorkBook.add_format(self.COL_HEAD_FORMAT_STR_OBJ)
			column_heading_format_date = myWorkBook.add_format(self.COL_HEAD_FORMAT_DATE_OBJ)
			column_heading_format_ts = myWorkBook.add_format(self.COL_HEAD_FORMAT_TS_OBJ)

			myWorkSheet.set_column(0,6, 30) # sets column 0 to 1 (A:B) to 30

			myWorkSheet.write_string('A6',"User ID",column_heading_format_str)
			myWorkSheet.write_string('B6',"User Name",column_heading_format_str)
			myWorkSheet.write_string('C6',"Location",column_heading_format_str)
			myWorkSheet.write_string('D6',"Email",column_heading_format_str)
			myWorkSheet.write_string('E6',"DB/AD Group",column_heading_format_str)
			myWorkSheet.write_string('F6',"Status",column_heading_format_str)

			# creating data format for audit data
			#https://en.wikipedia.org/wiki/Web_colors
			#data_format_str = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False })
			#data_format_ts = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'num_format':'yyyy-mm-dd hh:mm:ss.000', 'bold' : False })
			#data_format_date = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True , 'num_format':'mm/dd/yyyy', 'bold' : False})
			#data_format_str_err = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False, 'text_wrap': True })
			data_format_str = myWorkBook.add_format(self.DATA_FORMAT_STR_OBJ)
			data_format_num = myWorkBook.add_format(self.DATA_FORMAT_NUM_OBJ)
			data_format_ts = myWorkBook.add_format(self.DATA_FORMAT_TS_OBJ)
			data_format_date = myWorkBook.add_format(self.DATA_FORMAT_DATE_OBJ)
			data_format_str_err = myWorkBook.add_format(self.DATA_FORMAT_STR_ERR_OBJ)

			myDBAdminRosterArg = {
				"securityToken" : myKwArgs["securityToken"], 
				"opco" : myKwArgs["opco"], 
				"dbTechnology" : myKwArgs["dbTechnology"], 
				"status" : self.Globals.active,
				"consolidated" : "no", 
				"userId" : myKwArgs["userId"]
			}

			myDBResult = self.repo.getDBAdminRoster(**myDBAdminRosterArg)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"an error occurred while retrieving admin roster >>> {myDBResult['message']}")
			
			myDBAdminRoster = myDBResult["data"]

			#converting all dbloginid to uppercase
			for admin in myDBAdminRoster:
				# this result set is from unwind, so technology object is being changed from array to dict object
				for adminId in admin["technology"]["dbLoginId"]:
					adminId = adminId.upper()

			# writing admin details to file
			myDataRow = 6 # this is row 7
			for user in mySuperUserList:
				myWorkSheet.write_string(myDataRow,0,user["userId"],data_format_str)
				myWorkSheet.write_string(myDataRow,1,user["userName"],data_format_str)
				#userId" : user["networkId"], "userName" : user["name"], "location" : user["location"], "email" : user["email"]}) for user in myADGrpUsers["member_details"]]
				if "location" in user:
					myWorkSheet.write_string(myDataRow,2,user["location"],data_format_str)
				else:
					myWorkSheet.write_string(myDataRow,2," ",data_format_str)

				if "email" in user:
					myWorkSheet.write_string(myDataRow,3,user["email"],data_format_str)
				else:
					myWorkSheet.write_string(myDataRow,3," ",data_format_str)

				if "placement" in user:
					myWorkSheet.write_string(myDataRow,4,user["placement"],data_format_str)
				else:
					myWorkSheet.write_string(myDataRow,4," ",data_format_str)

				isAdminInRoster = [admin["_id"] for admin in myDBAdminRoster if user["userId"].upper() in [id_.upper() for id_ in admin["technology"]["dbLoginId"]] ]

				if isAdminInRoster:
					myWorkSheet.write_string(myDataRow,5,"Valid",data_format_str)
				else:
					myWorkSheet.write_string(myDataRow,5,"InValid (not in roster)",data_format_str)

				myDataRow += 1

			# creating another sheet for roster
			myRosterHeader = f"{myKwArgs['dbTechnology'].upper()} DB Admin Roster - {myKwArgs['opco'].upper()}"
			myRosterWorkSheet = myWorkBook.add_worksheet("Roster")
			myRosterWorkSheet.set_column(0,7, 30)

			format_header = myWorkBook.add_format({'bold' : True, 'font_color' : 'dark blue', 'font_size' : 28, 'align' : 'center', 'border' : True})
			date_format = myWorkBook.add_format({'bold' : True, 'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True})
			header_cell_merge_format = myWorkBook.add_format({'align': 'center', 'valign' : 'vcenter', 'border' : 1})
			cell_merge_format = myWorkBook.add_format({'align': 'left', 'valign' : 'left', 'border' : 1})
		
			# merging cell for header
			myRosterWorkSheet.merge_range('A1:B1', "", cell_merge_format)
			myRosterWorkSheet.merge_range("A2:D3", "", header_cell_merge_format)

			# writing header
			myRosterWorkSheet.write_string('A1', f"Date : {self.util.lambdaGetCurrReadableTime()}", date_format)
			myRosterWorkSheet.write_string('A2', myRosterHeader, format_header)

			myRosterWorkSheet.write_string('A5',"Employee Id",column_heading_format_str)
			myRosterWorkSheet.write_string('B5',"Name",column_heading_format_str)
			myRosterWorkSheet.write_string('C5',"Location",column_heading_format_str)
			myRosterWorkSheet.write_string('D5',"Email",column_heading_format_str)
			myRosterWorkSheet.write_string('E5',"Contact#",column_heading_format_str)
			myRosterWorkSheet.write_string('F5',"Technology",column_heading_format_str)
			myRosterWorkSheet.write_string('G5',"DB Login Id",column_heading_format_str)
			myRosterWorkSheet.write_string('H5',"Onboarding Date",column_heading_format_str)

			myDataRow = 6
			for admin in myDBAdminRoster:
				myRosterWorkSheet.write_string(myDataRow,0,str(admin["_id"]),data_format_str)
				myRosterWorkSheet.write_string(myDataRow,1,admin["name"],data_format_str)
				if "location" in admin:
					myRosterWorkSheet.write_string(myDataRow,2,admin["location"],data_format_str)

				if "email" in admin:
					myRosterWorkSheet.write_string(myDataRow,3,admin["email"],data_format_str)

				if "contact#" in admin:
					myRosterWorkSheet.write_string(myDataRow,4,admin["contact#"],data_format_str)

				if "technology" in admin and "dbTechnology" in admin["technology"]:
					myRosterWorkSheet.write_string(myDataRow,5,admin["technology"]["dbTechnology"].upper(),data_format_str)
				else:
					myRosterWorkSheet.write_string(" ",data_format_str)

				if "technology" in admin and "dbLoginId" in admin["technology"]:
					myDBLoginIds = ",".join(admin["technology"]["dbLoginId"])
					myRosterWorkSheet.write_string(myDataRow,6,myDBLoginIds,data_format_str)
				else:
					myRosterWorkSheet.write_string(myDataRow,6," ",data_format_str)

				if "technology" in admin and "onBoardDate" in admin["technology"]:
					myRosterWorkSheet.write_string(myDataRow,7,str(admin["technology"]["onBoardDate"]),data_format_str)
				else:
					myRosterWorkSheet.write_string(myDataRow,7, " ",data_format_str)
				myDataRow += 1

			# close the workbook
			myWorkBook.close()

			self.LOGGER.info(f"file {myFileName} is created, sending email to {myRecepient}")

			self.util.sendEmail(\
				myFromMailBox, \
				myRecepient, None, None, \
				mySubject, \
				myEmailBody, \
				'plain', myFileName)

			self.LOGGER.debug("email is sent, performing cleanup")

			myFilesDeleted = self.util.deleteFilesOlderThanDays(self.REPORT_LOC, ".xlsx", myReportFileRetDays)

			self.LOGGER.info(f"files older than {myReportFileRetDays} deleted >>> {myFilesDeleted}")

			return self.util.buildResponse(self.Globals.success, f'file {self.util.getFileName(myFileName)} is sent via email to {myRecepient}')

		except Exception as error:
			self.LOGGER.error(str(error), exc_info = True)
			raise error

	def genTenantAdminUserReport(self, **kwargs):
		"""
		parameter
			opco, region, dbTechnology
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			myKwArgs = self.util.getACopy(kwargs)

			myReportId = f"adhoc.{myKwArgs['dbTechnology'].lower()}.superUser.report" 

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(myKwArgs)])))

			# validating securityToken
			self.sec.validateSecToken(myKwArgs["securityToken"])

			# checking for required arguments
			myRequiredArgList = ["securityToken","opco","dbTechnology","tenants","recepient","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]}, 
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "tenants", "type" : list, "value" : myKwArgs["tenants"]},
				{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, [])

			# retrieving sys config data
			#mySysConfigData = self.repo.getSysConfig(myKwArgs["securityToken"], myKwArgs["opco"], myKwArgs["region"], self.Globals.DB_TYPE_MONGO)
			mySysConfigData = self.repo.getSysConfig(myKwArgs["securityToken"], myKwArgs["opco"])

			if not mySysConfigData:
				raise ValueError(f"Sys config data for Opco --> {myKwArgs['opco']} is missing !!!")

			myReportMeta = [report for report in mySysConfigData["reports"] if report["reportId"] == myReportId]
			
			if not myReportMeta:
				raise ValueError(f"Report '{myReportId}' metadata is missing in repository !!")

			if myReportMeta:
				myReportMeta = myReportMeta[0]

			print(f"Report metadata >>> {myReportMeta}")
			
			myDay, myDyName, myMonth, myMonthName, myYear = self.util.getEachElemOfDate(self.util.lambdaGetCurrReadableTime())
			myMonthYear = "".join([myMonthName, " ", str(myYear)])

			myHeader = myReportMeta["reportHeader"].format(opco = myKwArgs["opco"].upper(), dbTechnology = myKwArgs["dbTechnology"].upper())
			myHeaderCellRange = myReportMeta["cellRange"]
			myReportSheet = myReportMeta["sheetName"]

			myReportFileNamePrefix = myReportMeta["fileNamePrefix"]
			myReportFileRetDays = myReportMeta["retentionDays"]

			myRecepient = myKwArgs["recepient"]
			mySubject = myReportMeta["subject"].format(opco = myKwArgs['opco'].upper(), dbTechnology = myKwArgs["dbTechnology"].upper(), monthYear = myMonthYear)
			myEmailBody = myReportMeta["emailBody"].format(opco = myKwArgs['opco'].upper(), dbTechnology = myKwArgs["dbTechnology"].upper(), monthYear = myMonthYear).replace("\\n","\n")
			myFromMailBox = (myReportMeta["from"], myReportMeta["fromEmail"])

			if myKwArgs["dbTechnology"] == self.Globals.DB_TYPE_MONGO:
				# request is for Mongo, retrieving Mongo Super user list (detailed report)

				myDBResult = self.repo.getMongoRootUserList(securityToken = myKwArgs["securityToken"], opco = myKwArgs["opco"], tenants = myKwArgs["tenants"])
				#myDBResult = self.repo.getMongoRootUserList(securityToken = myKwArgs["securityToken"], opco = myKwArgs["opco"], region = myKwArgs["region"], tenants = myKwArgs["tenants"])

				if myDBResult["status"] == self.Globals.unsuccess:
					return myDBResult

				mySuperUserList = myDBResult["data"]

				if not mySuperUserList:
					return self.util.buildResponse(self.Globals.success, f"No Super user found for OPCO: {myKwArgs['opco']}, REGION: {myKwArgs['region']}, DB Technology: {myKwArgs['dbTechnolgoy']} !!!")

				# building file name for this report, since we have got data
				myFileName = self.util.buildPath(self.REPORT_LOC, \
					"".join([myReportFileNamePrefix, myKwArgs["opco"], "_", str(self.util.getCurDateTimeForDir()), ".xlsx"]))

			else:
				return self.util.buildResponse(self.Globals.success, f"Super user detailed report is not implemented for {myKwArgs['dbTechnolgoy']} !!!")

			# initializing file
			myWorkBook, myWorkSheet = self.initXlsxFile(\
				securityToken = myKwArgs["securityToken"], file = myFileName, \
				header = myHeader, headerCellRange = myHeaderCellRange, sheet = myReportSheet, border = {})

			# we will add following sub header to this file
			#mySubHeaderFormat = myWorkBook.add_format({'bold' : True, 'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : True})
			#mySubHeaderValueFormat = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : False})
			mySubHeaderFormat = myWorkBook.add_format(self.SUB_HEAD_FORMAT_OBJ)
			mySubHeaderValueFormat = myWorkBook.add_format(self.SUB_HEAD_VAL_FORMAT_OBJ)

			# writing opco, region, start and end date
			myWorkSheet.write_string("A4","Opco",mySubHeaderFormat)
			#myWorkSheet.write_string("A5","Region",mySubHeaderFormat)

			myWorkSheet.write_string("B4", myKwArgs["opco"],mySubHeaderValueFormat)
			#myWorkSheet.write_string("B5", myKwArgs["region"],mySubHeaderValueFormat)

			#column_heading_format_str = myWorkBook.add_format({'font_color' : 'white', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})
			#column_heading_format_date = myWorkBook.add_format({'font_color' : 'white', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})
			#column_heading_format_ts = myWorkBook.add_format({'font_color' : 'white', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})

			column_heading_format_str = myWorkBook.add_format(self.COL_HEAD_FORMAT_STR_OBJ)
			column_heading_format_date = myWorkBook.add_format(self.COL_HEAD_FORMAT_DATE_OBJ)
			column_heading_format_ts = myWorkBook.add_format(self.COL_HEAD_FORMAT_TS_OBJ)

			myWorkSheet.set_column(0,7, 30) # sets column 0 to 1 (A:B) to 30

			myWorkSheet.write_string('A6',"Tenant",column_heading_format_str)
			myWorkSheet.write_string('B6',"User ID",column_heading_format_str)
			myWorkSheet.write_string('C6',"User Name",column_heading_format_str)
			myWorkSheet.write_string('D6',"Location",column_heading_format_str)
			myWorkSheet.write_string('E6',"Email Id",column_heading_format_str)
			myWorkSheet.write_string('F6',"DB/AD Group",column_heading_format_str)			
			myWorkSheet.write_string('G6',"Status",column_heading_format_str)


			# creating data format for audit data
			#https://en.wikipedia.org/wiki/Web_colors
			#data_format_str = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False })
			#data_format_num = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'num_format':'###,###,##0', 'bold' : False })
			#data_format_ts = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'num_format':'yyyy-mm-dd hh:mm:ss.000', 'bold' : False })
			#data_format_date = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True , 'num_format':'mm/dd/yyyy', 'bold' : False})
			#data_format_str_err = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False, 'text_wrap': True })

			data_format_str = myWorkBook.add_format(self.DATA_FORMAT_STR_OBJ)
			data_format_num = myWorkBook.add_format(self.DATA_FORMAT_NUM_OBJ)
			data_format_ts = myWorkBook.add_format(self.DATA_FORMAT_TS_OBJ)
			data_format_date = myWorkBook.add_format(self.DATA_FORMAT_DATE_OBJ)
			data_format_str_err = myWorkBook.add_format(self.DATA_FORMAT_STR_ERR_OBJ)

			myDBAdminRosterArg = {
				"securityToken" : myKwArgs["securityToken"], 
				"opco" : myKwArgs["opco"], 
				"dbTechnology" : myKwArgs["dbTechnology"], 
				"status" : self.Globals.active,
				"consolidated" : "no", 
				"userId" : myKwArgs["userId"]
			}

			myDBResult = self.repo.getDBAdminRoster(**myDBAdminRosterArg)
			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"an error occurred while retrieving admin roster >>> {myDBResult['message']}")
			
			myDBAdminRoster = myDBResult["data"]

			# writing Ops mgr user admin data to file
			myDataRow = 6 # this is row 7
			for tenant in mySuperUserList:
				myWorkSheet.write_string(myDataRow,0,tenant["tenant"],data_format_str)
				for user in tenant["users"]:
					myWorkSheet.write_string(myDataRow,1,user["userId"],data_format_str)
					myWorkSheet.write_string(myDataRow,2,user["userName"],data_format_str)

					if "location" in user:
						myWorkSheet.write_string(myDataRow,3, user["location"],data_format_str)
					else:
						myWorkSheet.write_string(myDataRow,3, " ",data_format_str)

					if "email" in user:
						myWorkSheet.write_string(myDataRow,4,user["email"],data_format_str)
					else:
						myWorkSheet.write_string(myDataRow,4," ",data_format_str)

					if "placement" in user:
						myWorkSheet.write_string(myDataRow,5,user["placement"],data_format_str)
					else:
						myWorkSheet.write_string(myDataRow,5," ",data_format_str)

					# checking if this user is in roster
					isAdminInRoster = [admin["_id"] for admin in myDBAdminRoster if user["userId"].upper() in admin["technology"]["dbLoginId"] ]
					if isAdminInRoster:
						myWorkSheet.write_string(myDataRow,5,"Valid",data_format_str)
					else:
						myWorkSheet.write_string(myDataRow,5,"InValid (not in roster)",data_format_str)

					myDataRow += 1

			# creating another sheet for roster
			myRosterHeader = f"{myKwArgs['dbTechnology'].upper()} DB Admin Roster - {myKwArgs['opco'].upper()}"
			myRosterWorkSheet = myWorkBook.add_worksheet("Roster")
			myRosterWorkSheet.set_column(0,7, 30)

			format_header = myWorkBook.add_format({'bold' : True, 'font_color' : 'dark blue', 'font_size' : 28, 'align' : 'center', 'border' : True})
			date_format = myWorkBook.add_format({'bold' : True, 'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True})
			header_cell_merge_format = myWorkBook.add_format({'align': 'center', 'valign' : 'vcenter', 'border' : 1})
			cell_merge_format = myWorkBook.add_format({'align': 'left', 'valign' : 'left', 'border' : 1})
		
			# merging cell for header
			myRosterWorkSheet.merge_range('A1:B1', "", cell_merge_format)
			myRosterWorkSheet.merge_range("A2:D3", "", header_cell_merge_format)

			# writing header
			myRosterWorkSheet.write_string('A1', f"Date : {self.util.lambdaGetCurrReadableTime()}", date_format)
			myRosterWorkSheet.write_string('A2', myRosterHeader, format_header)

			myRosterWorkSheet.write_string('A5',"Employee Id",column_heading_format_str)
			myRosterWorkSheet.write_string('B5',"Name",column_heading_format_str)
			myRosterWorkSheet.write_string('C5',"Location",column_heading_format_str)
			myRosterWorkSheet.write_string('D5',"Email",column_heading_format_str)
			myRosterWorkSheet.write_string('E5',"Contact#",column_heading_format_str)
			myRosterWorkSheet.write_string('F5',"Technology",column_heading_format_str)
			myRosterWorkSheet.write_string('G5',"DB Login Id",column_heading_format_str)
			myRosterWorkSheet.write_string('H5',"Onboarding Date",column_heading_format_str)

			myDataRow = 6
			for admin in myDBAdminRoster:
				myRosterWorkSheet.write_string(myDataRow,0,str(admin["_id"]),data_format_str)
				myRosterWorkSheet.write_string(myDataRow,1,admin["name"],data_format_str)
				if "location" in admin:
					myRosterWorkSheet.write_string(myDataRow,2,admin["location"],data_format_str)

				if "email" in admin:
					myRosterWorkSheet.write_string(myDataRow,3,admin["email"],data_format_str)

				if "contact#" in admin:
					myRosterWorkSheet.write_string(myDataRow,4,admin["contact#"],data_format_str)

				if "technology" in admin and "dbTechnology" in admin["technology"]:
					myRosterWorkSheet.write_string(myDataRow,5,admin["technology"]["dbTechnology"].upper(),data_format_str)
				else:
					myRosterWorkSheet.write_string(" ",data_format_str)

				if "technology" in admin and "dbLoginId" in admin["technology"]:
					myDBLoginIds = ",".join(admin["technology"]["dbLoginId"])
					myRosterWorkSheet.write_string(myDataRow,6,myDBLoginIds,data_format_str)
				else:
					myRosterWorkSheet.write_string(myDataRow,6," ",data_format_str)

				if "technology" in admin and "onBoardDate" in admin["technology"]:
					myRosterWorkSheet.write_string(myDataRow,7,str(admin["technology"]["onBoardDate"]),data_format_str)
				else:
					myRosterWorkSheet.write_string(myDataRow,7, " ",data_format_str)
				myDataRow += 1

			# close the workbook
			myWorkBook.close()
			self.LOGGER.info(f"file {myFileName} is created, sending email to {myRecepient}")

			self.util.sendEmail(\
				myFromMailBox, \
				myRecepient, None, None, \
				mySubject, \
				myEmailBody, \
				'plain', myFileName)

			self.LOGGER.debug("email is sent, performing cleanup")

			myFilesDeleted = self.util.deleteFilesOlderThanDays(self.REPORT_LOC, ".xlsx", myReportFileRetDays)

			self.LOGGER.info(f"files older than {myReportFileRetDays} deleted >>> {myFilesDeleted}")

			return self.util.buildResponse(self.Globals.success, f'file {self.util.getFileName(myFileName)} is sent via email to {myRecepient}')

		except Exception as error:
			self.LOGGER.error(str(error), exc_info = True)
			raise error

	def genMongoPassCompReport(self, **kwargs):
		"""
		parameter
			opco, region, dbTechnology
		"""
		pass

	def genAllHostDetailsReport(self, **kwargs):
		"""
		parameter
			opco, dbTechnology
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			myKwArgs = self.util.getACopy(kwargs)

			myReportId = f"{myKwArgs['dbTechnology'].lower()}.monthly.hostDetails.report" 

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(myKwArgs)])))

			# validating securityToken
			self.sec.validateSecToken(myKwArgs["securityToken"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]},							
			]

			self.util.valArguments2(myArgValidationList, ["opco","inclEnvList"])

			# retrieving sys config data
			#mySysConfigData = self.repo.getSysConfig(myKwArgs["securityToken"], myKwArgs["opco"], myKwArgs["region"], self.Globals.DB_TYPE_MONGO)
			mySysConfigData = self.repo.getSysConfig(myKwArgs["securityToken"], myKwArgs["opco"])

			if not mySysConfigData:
				raise ValueError(f"Sys config data for Opco --> {myKwArgs['opco']} is missing !!!")

			myReportMeta = [report for report in mySysConfigData["reports"] if report["reportId"] == myReportId]
			
			if not myReportMeta:
				raise ValueError(f"Report '{myReportId}' metadata is missing in repository !!")

			if myReportMeta:
				myReportMeta = myReportMeta[0]

			print(f"Report metadata >>> {myReportMeta}")
			
			myDay, myDyName, myMonth, myMonthName, myYear = self.util.getEachElemOfDate(self.util.lambdaGetCurrReadableTime())
			myMonthYear = "".join([myMonthName, " ", str(myYear)])

			myHeader = myReportMeta["reportHeader"].format(dbTechnology = myKwArgs["dbTechnology"].upper())
			myHeaderCellRange = myReportMeta["cellRange"]
			myReportSheet = myReportMeta["sheetName"]

			myReportFileNamePrefix = myReportMeta["fileNamePrefix"]
			myReportFileRetDays = myReportMeta["retentionDays"]

			myRecepient = myKwArgs["recepient"]
			mySubject = myReportMeta["subject"].format(monthYear = myMonthYear)
			myEmailBody = myReportMeta["emailBody"].format(monthYear = myMonthYear).replace("\\n","\n")
			myFromMailBox = (myReportMeta["from"], myReportMeta["fromEmail"])

			# retrieve all host for this opco and tenants
			myArguments = {
				"securityToken" : myKwArgs["securityToken"],
				"dbTechnology" : myKwArgs["dbTechnology"]
			}

			if "opco" in myKwArgs and myKwArgs["opco"]:
				myArguments.update({"opco" : myKwArgs["opco"]})

			if "inclEnvList" in myKwArgs and myKwArgs["inclEnvList"]:
				myArguments.update({"inclEnvList" : myKwArgs["inclEnvList"]})

			myDBResult = self.repo.getAllHostDetails(**myArguments)

			if myDBResult["status"] == self.Globals.unsuccess:
				return myDBResult

			myAllOpcoMongoDBHosts = myDBResult["data"]

			if not myAllOpcoDBHosts:
				return self.util.buildResponse(self.Globals.success, f"No host details found for OPCO: {myKwArgs['opco']}, DB Technology: {myKwArgs['dbTechnolgoy']} !!!")

			# building file name for this report, since we have got data
			myFileName = self.util.buildPath(self.REPORT_LOC, \
				"".join([myReportFileNamePrefix, myKwArgs["opco"], str(self.util.getCurDateTimeForDir()), ".xlsx"]))

			# ceating excel file object
			myWorkBook, myWorkSheet = self.initXlsxFile(\
				securityToken = myKwArgs["securityToken"], file = myFileName, \
				header = myHeader, headerCellRange = myHeaderCellRange, sheet = myReportSheet, border = {})

			# we will add following sub header to this file
			#mySubHeaderFormat = myWorkBook.add_format({'bold' : True, 'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : True})
			#mySubHeaderValueFormat = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : False})
			mySubHeaderFormat = myWorkBook.add_format(self.SUB_HEAD_FORMAT_OBJ)
			mySubHeaderValueFormat = myWorkBook.add_format(self.SUB_HEAD_VAL_FORMAT_OBJ)

			# writing opco, region, start and end date
			#myWorkSheet.write_string("A4","Opco",mySubHeaderFormat)
			#myWorkSheet.write_string("A5","Region",mySubHeaderFormat)

			#myWorkSheet.write_string("B4", myKwArgs["opco"],mySubHeaderValueFormat)
			column_heading_format_str = myWorkBook.add_format(self.COL_HEAD_FORMAT_STR_OBJ)
			column_heading_format_date = myWorkBook.add_format(self.COL_HEAD_FORMAT_DATE_OBJ)
			column_heading_format_ts = myWorkBook.add_format(self.COL_HEAD_FORMAT_TS_OBJ)

			# adjusting column size for Tenant Name/ID/Application Details
			myWorkSheet.set_column(0,3, 15) # sets column size 0 to 1 (A:C) to 15
			myWorkSheet.set_column(4,4, 10) # sets column size 0 to 1 (A:C) to 15			
			myWorkSheet.set_column(5,7, 30) # sets column size M to N to 30
			myWorkSheet.set_column(13,14, 30) # sets column size M to N to 30
			#myWorkSheet.set_column(14,14, 20) # sets column size O to 20 
			myWorkSheet.set_column(20,20, 15) # sets column size M to N to 30
			# setting R/S/T to size 30 char
			myWorkSheet.set_column(17,19, 25) # sets column size R/S/T to 30			
			#myWorkSheet.set_column()

			myWorkSheet.write_string('A6',"OPCO",column_heading_format_str)
			myWorkSheet.write_string('B6',"Region",column_heading_format_str)
			myWorkSheet.write_string('C6',"Domain",column_heading_format_str)
			myWorkSheet.write_string('D6',"DC Location",column_heading_format_str)
			myWorkSheet.write_string('E6',"Env",column_heading_format_str)			
			myWorkSheet.write_string('F6',"Host Name",column_heading_format_str)
			myWorkSheet.write_string('G6',"IPV4 Address",column_heading_format_str)
			myWorkSheet.write_string('H6',"IPV6 Address",column_heading_format_str)
			myWorkSheet.write_string('I6',"OS Type",column_heading_format_str)
			myWorkSheet.write_string('J6',"OS Version",column_heading_format_str)
			myWorkSheet.write_string('K6',"Memory (MB)",column_heading_format_str)
			myWorkSheet.write_string('L6',"Swap Memory (MB)",column_heading_format_str)
			myWorkSheet.write_string('M6',"CPU Count",column_heading_format_str)
			myWorkSheet.write_string('N6',"Tenant Name",column_heading_format_str)
			myWorkSheet.write_string('O6',"Tenant ID",column_heading_format_str)
			myWorkSheet.write_string('P6',"Tenant Version",column_heading_format_str)
			#myWorkSheet.write_string('Q6',"Env",column_heading_format_str)
			myWorkSheet.write_string('Q6',"Docker",column_heading_format_str)
			myWorkSheet.write_string('R6',"Docker Memory (MB)",column_heading_format_str)
			myWorkSheet.write_string('S6',"Docker Memory Used (MB)",column_heading_format_str)
			myWorkSheet.write_string('T6',"Docker CPU ",column_heading_format_str)
			myWorkSheet.write_string('U6',"Total DBs",column_heading_format_str)
			#myWorkSheet.write_string('W6',"App Details",column_heading_format_str)


			# creating data format for audit data
			#data_format_str = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False })
			#data_format_num = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'num_format' : '###,####,###,##0', 'bold' : False })
			#data_format_ts = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'num_format':'yyyy-mm-dd hh:mm:ss.000', 'bold' : False })
			#data_format_date = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True , 'num_format':'mm/dd/yyyy', 'bold' : False})
			#data_format_str_err = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False, 'text_wrap': True })

			data_format_str = myWorkBook.add_format(self.DATA_FORMAT_STR_OBJ)
			data_format_num = myWorkBook.add_format(self.DATA_FORMAT_NUM_OBJ)
			data_format_ts = myWorkBook.add_format(self.DATA_FORMAT_TS_OBJ)
			data_format_date = myWorkBook.add_format(self.DATA_FORMAT_DATE_OBJ)
			data_format_str_err = myWorkBook.add_format(self.DATA_FORMAT_STR_ERR_OBJ)
			data_format_num = myWorkBook.add_format(self.DATA_FORMAT_NUM_OBJ)

			# writing Ops mgr user admin data to file
			myDataRow = 6 # this is row 7
			
			myAllHostMemory = myAllHostSwapMemory = myAllHostCPUS = myTotalDockAllocMem = myTotalDockUsedMem = 0
			for host in myAllOpcoDBHosts:
				myAllHostMemory = myAllHostMemory + host["memory"]["total"]
				myAllHostSwapMemory = myAllHostSwapMemory + host["swap"]["total"]
				myAllHostCPUS = myAllHostCPUS + host["cpu"]["count"]
				# looping thru all tenants for this hosts
				for tenant in host["tenants"]:
					myWorkSheet.write_string(myDataRow, 0, host["opco"], data_format_str)
					myWorkSheet.write_string(myDataRow, 1, host["region"], data_format_str)
					myWorkSheet.write_string(myDataRow, 2, host["domain"], data_format_str)
					myWorkSheet.write_string(myDataRow, 3, host["dcLocation"], data_format_str)
					myWorkSheet.write_string(myDataRow, 4, tenant["env"].upper(), data_format_str)					
					myWorkSheet.write_string(myDataRow, 5, host["hostName"], data_format_str)
					myWorkSheet.write_string(myDataRow, 6, host["ipAddress"], data_format_str)
					myWorkSheet.write_string(myDataRow, 7, host["ipv6Address"], data_format_str)
					myWorkSheet.write_string(myDataRow, 8, host["os"], data_format_str)
					myWorkSheet.write_string(myDataRow, 9, host["version"], data_format_str)
					myWorkSheet.write_number(myDataRow, 10, host["memory"]["total"]/(1024*1024), data_format_num)
					myWorkSheet.write_number(myDataRow, 11, host["swap"]["total"]/(1024*1024), data_format_num)
					myWorkSheet.write_number(myDataRow, 12, host["cpu"]["count"], data_format_num)
					myWorkSheet.write_string(myDataRow, 13, tenant["tenantName"], data_format_str)
					myWorkSheet.write_string(myDataRow, 14, tenant["tenantId"], data_format_str)
					myWorkSheet.write_string(myDataRow, 15, tenant["tenantVersion"], data_format_str)
					#myWorkSheet.write_string(myDataRow, 15, tenant["env"], data_format_str)
					myWorkSheet.write_string(myDataRow, 16,  str(tenant["docker"]), data_format_str)
					# docker attributes
					if tenant["docker"] == True:
						# writing docker attributes
						myWorkSheet.write_number(myDataRow, 17, tenant["CTRPhysMemLimitMB"], data_format_num)
						myWorkSheet.write_number(myDataRow, 18, tenant["CTRPhysMemUsedMB"], data_format_num)
						myWorkSheet.write_number(myDataRow, 19, tenant["CTRcpuCount"], data_format_num)

						myTotalDockAllocMem = myTotalDockAllocMem + tenant["CTRPhysMemLimitMB"]
						myTotalDockUsedMem = myTotalDockUsedMem + tenant["CTRPhysMemUsedMB"]
					else:
						myWorkSheet.write_number(myDataRow, 17, 0, data_format_num)
						myWorkSheet.write_number(myDataRow, 18, 0, data_format_num)
						myWorkSheet.write_number(myDataRow, 19, 0, data_format_num)

					"""

					# retrieving database details for this tenant
					myTenantDBs = self.repo.getTenantDBDetails(myKwArgs["securityToken"], tenant["tenantName"])

					if myTenantDBs:
						myTenantAppDBs = [db for db in myTenantDBs["dbs"] if db["appId"].lower() != "system"]
					else:
						myTenantAppDBs = []

					myWorkSheet.write_number(myDataRow,20, len(myTenantAppDBs), data_format_num)
					
					myAllTenantAppDBs = ["".join([ db["name"], " --> ", db["appName"] ]) for db in myTenantAppDBs]

					myWorkSheet.write_string(myDataRow,21, str(myAllTenantAppDBs), data_format_str)
					"""
					myDataRow += 1

			# close the workbook
			# writing summary
			sumarry_heading_format = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : 'white'})

			#myWorkSheet.write_string(myDataRow + 1, 4,  "Summary", column_heading_format_str)
			#myWorkSheet.write_string(myDataRow + 1, 5, "         ", column_heading_format_str)
			myWorkSheet.write_string(myDataRow + 2, 4 , "Total Hosts ", sumarry_heading_format)
			myWorkSheet.write_number(myDataRow + 2, 5, len(myAllOpcoDBHosts), data_format_num)
			myWorkSheet.write_string(myDataRow + 3, 4 , "Total Memory (GB) ", sumarry_heading_format)
			myWorkSheet.write_number(myDataRow + 3, 5, myAllHostMemory/(1024*1024*1024), data_format_num)
			myWorkSheet.write_string(myDataRow + 4, 4, "Total Swap (GB) ", sumarry_heading_format)
			myWorkSheet.write_number(myDataRow + 4, 5, myAllHostSwapMemory/(1024*1024*1024), data_format_num)
			myWorkSheet.write_string(myDataRow + 5, 4, "Total CPUs", sumarry_heading_format)
			myWorkSheet.write_number(myDataRow + 5, 5, myAllHostCPUS, data_format_num)
			myWorkSheet.write_string(myDataRow + 6, 4, "Total Docker Memory Allocated (GB)", sumarry_heading_format)
			myWorkSheet.write_number(myDataRow + 6, 5, myTotalDockAllocMem, data_format_num)
			myWorkSheet.write_string(myDataRow + 7, 4, "Total Docker Memory Used (GB)", sumarry_heading_format)
			myWorkSheet.write_number(myDataRow + 7, 5, myTotalDockUsedMem, data_format_num)


			myWorkBook.close()
			self.LOGGER.info(f"file {myFileName} is created, sending email to {myRecepient}")

			self.util.sendEmail(\
				myFromMailBox, \
				myRecepient, None, None, \
				mySubject, \
				myEmailBody, \
				'plain', myFileName)

			self.LOGGER.debug("email is sent, performing cleanup")

			myFilesDeleted = self.util.deleteFilesOlderThanDays(self.REPORT_LOC, ".xlsx", myReportFileRetDays)

			self.LOGGER.info(f"files older than {myReportFileRetDays} deleted >>> {myFilesDeleted}")

			return self.util.buildResponse(self.Globals.success, f'file {self.util.getFileName(myFileName)} is sent via email to {myRecepient}')

		except Exception as error:
			self.LOGGER.error(str(error), exc_info = True)
			raise error

	def genHostReport4MongoLicensing(self, **kwargs):
		"""
		Generate Host details report for licensing
		arguments
			opco, recepient
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			myKwArgs = self.util.getACopy(kwargs)

			myReportId = "mongo.monthly.hostDetails.licensing.report" 

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(myKwArgs)])))

			# validating securityToken
			self.sec.validateSecToken(myKwArgs["securityToken"])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				#{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]},
			]

			self.util.valArguments2(myArgValidationList, ["recepient"])

			# retrieving sys config data
			#mySysConfigData = self.repo.getSysConfig(myKwArgs["securityToken"], myKwArgs["opco"], myKwArgs["region"], self.Globals.DB_TYPE_MONGO)
			mySysConfigData = self.repo.getSysConfig(myKwArgs["securityToken"], myKwArgs["opco"])

			if not mySysConfigData:
				raise ValueError(f"Sys config data for Opco --> {myKwArgs['opco']} is missing !!!")

			myReportMeta = [report for report in mySysConfigData["reports"] if report["reportId"] == myReportId]
			
			if not myReportMeta:
				raise ValueError(f"Report '{myReportId}' metadata is missing in repository !!")

			if myReportMeta:
				myReportMeta = myReportMeta[0]

			print(f"Report metadata >>> {myReportMeta}")
			
			myDay, myDyName, myMonth, myMonthName, myYear = self.util.getEachElemOfDate(self.util.lambdaGetCurrReadableTime())
			myMonthYear = "".join([myMonthName, " ", str(myYear)])

			myHeader = myReportMeta["reportHeader"]
			myHeaderCellRange = myReportMeta["cellRange"]
			myReportSheet = myReportMeta["sheetName"]

			myReportFileNamePrefix = myReportMeta["fileNamePrefix"]
			myReportFileRetDays = myReportMeta["retentionDays"]

			myRecepient = myKwArgs["recepient"]
			mySubject = myReportMeta["subject"].format(monthYear = myMonthYear)
			myEmailBody = myReportMeta["emailBody"].format(monthYear = myMonthYear).replace("\\n","\n")
			myFromMailBox = (myReportMeta["from"], myReportMeta["fromEmail"])

			"""
			# retrieve all host for this opco db technology
			myArguments = {
				"securityToken" : myKwArgs["securityToken"],
				"opco" : myKwArgs["opco"],
				"dbTechnology" : self.Globals.DB_TYPE_MONGO
			}
			myDBResult = self.repo.getAllHostDetails(**myArguments)
			"""

			myDBResult = self.getMongoLicensingData(myKwArgs["securityToken"], myKwArgs["opco"], "detail")

			if myDBResult["status"] == self.Globals.unsuccess:
				return myDBResult

			myAllOpcoMongoDBHosts = myDBResult["data"]

			if not myAllOpcoMongoDBHosts:
				return self.util.buildResponse(self.Globals.success, f"No host details found for OPCO: {myKwArgs['opco']} !!!")

			# retrieving summary data
			myDBResult = self.getMongoLicensingData(myKwArgs["securityToken"], myKwArgs["opco"])

			if myDBResult["status"] == self.Globals.unsuccess:
				return myDBResult

			myLicensingSummaryData = myDBResult["data"]

			# adding licensingMemoryGB to raw data
			for host in myLicensingSummaryData:
				if host["dockerMemLimit"] == 0:
					host.update({"licensingMemoryGB" : host["hostMemoryGB"]})
				else:
					host.update({"licensingMemoryGB" : host["hostMemory"] if host["hostMemory"] < host["totalDockerMemLimit"] else host["dockerMemLimitGB"]})

			"""
			myHostInventoryArgs = {
				"securityToken" : myKwArgs["securityToken"],
				"opco" : myKwArgs["opco"],
				"region" : "all",
				"dcLocation" : "all",
				"dbTechnology" : self.Globals.DB_TYPE_MONGO,
				"env" : "prod",
				"tag" : "all",
				"userId" : myKwArgs["userId"]
			}
			
			myDBResult = self.repo.getHostInventory(**myHostInventoryArgs)

			if myDBResult["status"] == self.Globals.unsuccess:
				return myDBResult

			myAllOpcoMongoDBHostsInventory = myDBResult["data"]
			myValidHosts4Licensing = [host["hostName"] for host in myAllOpcoMongoDBHostsInventory if host["licenseNeeded"] == "yes"]
			"""
			# building file name for this report, since we have got data
			myFileName = self.util.buildPath(self.REPORT_LOC, \
				"".join([myReportFileNamePrefix, myKwArgs["opco"], "_", str(self.util.getCurDateTimeForDir()), ".xlsx"]))

			# ceating excel file object
			myWorkBook, myWorkSheet = self.initXlsxFile(\
				securityToken = myKwArgs["securityToken"], file = myFileName, \
				header = myHeader, headerCellRange = myHeaderCellRange, sheet = myReportSheet, border = {})

			# we will add following sub header to this file
			#mySubHeaderFormat = myWorkBook.add_format({'bold' : True, 'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : True})
			#mySubHeaderValueFormat = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : False})
			mySubHeaderFormat = myWorkBook.add_format(self.SUB_HEAD_FORMAT_OBJ)
			mySubHeaderValueFormat = myWorkBook.add_format(self.SUB_HEAD_VAL_FORMAT_OBJ)

			# writing opco, region, start and end date
			#myWorkSheet.write_string("A4","Opco",mySubHeaderFormat)
			#myWorkSheet.write_string("A5","Region",mySubHeaderFormat)

			#myWorkSheet.write_string("B4", myKwArgs["opco"],mySubHeaderValueFormat)
			column_heading_format_str = myWorkBook.add_format(self.COL_HEAD_FORMAT_STR_OBJ)
			column_heading_format_date = myWorkBook.add_format(self.COL_HEAD_FORMAT_DATE_OBJ)
			column_heading_format_ts = myWorkBook.add_format(self.COL_HEAD_FORMAT_TS_OBJ)

			# adjusting column size for Tenant Name/ID/Application Details
			myWorkSheet.set_column(0,3, 15) # sets column size 0 to 1 (A:C) to 15
			myWorkSheet.set_column(4,4, 10) # sets column size 0 to 1 (A:C) to 15			
			myWorkSheet.set_column(5,7, 30) # sets column size M to N to 30
			myWorkSheet.set_column(13,14, 30) # sets column size M to N to 30
			#myWorkSheet.set_column(14,14, 20) # sets column size O to 20 
			myWorkSheet.set_column(20,20, 15) # sets column size M to N to 30
			# setting R/S/T to size 30 char
			myWorkSheet.set_column(17,19, 25) # sets column size R/S/T to 30			
			#myWorkSheet.set_column()

			myWorkSheet.write_string('A6',"OPCO",column_heading_format_str)
			#myWorkSheet.write_string('B6',"Region",column_heading_format_str)
			#myWorkSheet.write_string('C6',"Domain",column_heading_format_str)
			#myWorkSheet.write_string('D6',"DC Location",column_heading_format_str)
			#myWorkSheet.write_string('E6',"Env",column_heading_format_str)			
			myWorkSheet.write_string('B6',"Host Name",column_heading_format_str)
			myWorkSheet.write_string('C6',"Database ID",column_heading_format_str)
			myWorkSheet.write_string('D6',"DB/Cluster Name",column_heading_format_str)			
			myWorkSheet.write_string('E6',"DB Instance ID",column_heading_format_str)
			myWorkSheet.write_string('F6',"Port",column_heading_format_str)
			myWorkSheet.write_string('G6',"Memory (MB)",column_heading_format_str)
			#myWorkSheet.write_string('L6',"Swap Memory (MB)",column_heading_format_str)
			myWorkSheet.write_string('H6',"CPU Count",column_heading_format_str)
			#myWorkSheet.write_string('Q6',"Env",column_heading_format_str)
			myWorkSheet.write_string('I6',"Docker",column_heading_format_str)
			myWorkSheet.write_string('J6',"Docker Memory (MB)",column_heading_format_str)
			myWorkSheet.write_string('K6',"Docker Memory Used (MB)",column_heading_format_str)
			myWorkSheet.write_string('L6',"Docker CPU ",column_heading_format_str)
			#myWorkSheet.write_string('U6',"Total DBs",column_heading_format_str)
			#myWorkSheet.write_string('W6',"App Details",column_heading_format_str)


			# creating data format for audit data
			#data_format_str = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False })
			#data_format_num = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'num_format' : '###,####,###,##0', 'bold' : False })
			#data_format_ts = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'num_format':'yyyy-mm-dd hh:mm:ss.000', 'bold' : False })
			#data_format_date = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True , 'num_format':'mm/dd/yyyy', 'bold' : False})
			#data_format_str_err = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False, 'text_wrap': True })

			data_format_str = myWorkBook.add_format(self.DATA_FORMAT_STR_OBJ)
			data_format_num = myWorkBook.add_format(self.DATA_FORMAT_NUM_OBJ)
			data_format_ts = myWorkBook.add_format(self.DATA_FORMAT_TS_OBJ)
			data_format_date = myWorkBook.add_format(self.DATA_FORMAT_DATE_OBJ)
			data_format_str_err = myWorkBook.add_format(self.DATA_FORMAT_STR_ERR_OBJ)
			data_format_num = myWorkBook.add_format(self.DATA_FORMAT_NUM_OBJ)

			# writing Ops mgr user admin data to file
			myDataRow = 6 # this is row 7
			
			for host in myAllOpcoMongoDBHosts:
				myWorkSheet.write_string(myDataRow, 0, host["opco"], data_format_str)
				myWorkSheet.write_string(myDataRow, 1, host["hostName"], data_format_str)
				myWorkSheet.write_string(myDataRow, 2, host["tenantName"], data_format_str)
				myWorkSheet.write_string(myDataRow, 2, host["dbCluster"], data_format_str)
				myWorkSheet.write_string(myDataRow, 2, host["tenantId"], data_format_str)
				myWorkSheet.write_string(myDataRow, 2, host["port"], data_format_str)
				myWorkSheet.write_string(myDataRow, 2, host["hostMemoryGB"], data_format_str)
				myWorkSheet.write_string(myDataRow, 2, host["docker"], data_format_str)
				myWorkSheet.write_string(myDataRow, 2, host["dokcerMemLimitGB"], data_format_str)
				myWorkSheet.write_string(myDataRow, 2, host["dokcerMemUsedGB"], data_format_str)
				myWorkSheet.write_string(myDataRow, 7, host["ipv6Address"], data_format_str)
				myWorkSheet.write_string(myDataRow, 8, host["dockerCPUCount"], data_format_str)

				"""

				# retrieving database details for this tenant
				myTenantDBs = self.repo.getTenantDBDetails(myKwArgs["securityToken"], tenant["tenantName"])

				if myTenantDBs:
					myTenantAppDBs = [db for db in myTenantDBs["dbs"] if db["appId"].lower() != "system"]
				else:
					myTenantAppDBs = []

				myWorkSheet.write_number(myDataRow,20, len(myTenantAppDBs), data_format_num)
				
				myAllTenantAppDBs = ["".join([ db["name"], " --> ", db["appName"] ]) for db in myTenantAppDBs]

				myWorkSheet.write_string(myDataRow,21, str(myAllTenantAppDBs), data_format_str)
				"""
				myDataRow += 1

			# close the workbook
			# writing summary
			sumarry_heading_format = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : 'white'})

			#myWorkSheet.write_string(myDataRow + 1, 4,  "Summary", column_heading_format_str)
			#myWorkSheet.write_string(myDataRow + 1, 5, "         ", column_heading_format_str)
			cell_merge_format = myWorkBook.add_format({'align': 'left', 'valign' : 'left', 'border' : 1})


			myDataRow = myDataRow + 2
			myWorkSheet.merge_range(f'D{myDataRow+1}:E{myDataRow+1}', "", cell_merge_format)
			myWorkSheet.write_string(myDataRow, 3 , "Total hosts ", sumarry_heading_format)
			myWorkSheet.write_number(myDataRow, 5, len(list(set([host["hostName"] for host in myLicensingSummaryData]))), data_format_num)

			myDataRow += 1
			myWorkSheet.merge_range(f'D{myDataRow+1}:E{myDataRow+1}', "", cell_merge_format)
			myWorkSheet.write_string(myDataRow, 3 , "Total memory (GB) ", sumarry_heading_format)
			myWorkSheet.write_number(myDataRow, 5, sum(list(set([host["hostMemoryGB"] for host in myLicensingSummaryData]))), data_format_num)
			
			myDataRow += 1
			myWorkSheet.merge_range(f'D{myDataRow+1}:E{myDataRow+1}', "", cell_merge_format)
			myWorkSheet.write_string(myDataRow, 3, "Total CPUs", sumarry_heading_format)
			myWorkSheet.write_number(myDataRow, 5, sum(list(set([host["hostCPU"] for host in myLicensingSummaryData]))), data_format_num)

			myDataRow += 1
			myWorkSheet.merge_range(f'D{myDataRow+1}:E{myDataRow+1}', "", cell_merge_format)
			myWorkSheet.write_string(myDataRow, 3, "Total docker memory allocated (GB)", sumarry_heading_format)
			myWorkSheet.write_number(myDataRow, 5, sum(list(set([host["totalDockerMemLimit"] for host in myLicensingSummaryData]))), data_format_num)

			myDataRow += 1
			myWorkSheet.merge_range(f'D{myDataRow+1}:E{myDataRow+1}', "", cell_merge_format)
			myWorkSheet.write_string(myDataRow, 3, "Total docker memory used (GB)", sumarry_heading_format)
			myWorkSheet.write_number(myDataRow, 5, sum(list(set([host["totalDockerMemUsed"] for host in myLicensingSummaryData]))), data_format_num)

			myDataRow += 1
			myWorkSheet.merge_range(f'D{myDataRow+1}:E{myDataRow+1}', "", cell_merge_format)
			myWorkSheet.write_string(myDataRow, 3, "Total memory required for lincesing (GB)", sumarry_heading_format)
			myWorkSheet.write_number(myDataRow, 5, sum(list(set([host["licensingMemoryGB"] for host in myLicensingSummaryData]))), data_format_num)

			myWorkBook.close()
			
			if "recepient" in myKwArgs:
				self.LOGGER.info(f"file {myFileName} is created, sending email to {myRecepient}")

				self.util.sendEmail(\
					myFromMailBox, \
					myRecepient, None, None, \
					mySubject, \
					myEmailBody, \
					'plain', myFileName)

				self.LOGGER.debug("email is sent, performing cleanup")

			myFilesDeleted = self.util.deleteFilesOlderThanDays(self.REPORT_LOC, ".xlsx", myReportFileRetDays)

			self.LOGGER.info(f"files older than {myReportFileRetDays} deleted >>> {myFilesDeleted}")

			return self.util.buildResponse(self.Globals.success, f'file {self.util.getFileName(myFileName)} is sent via email to {myRecepient}')

		except Exception as error:
			self.LOGGER.error(str(error), exc_info = True)
			raise error

	def genAdminRosterReport(self, **kwargs):
		"""
		parameter
			opco, region, dbTechnology
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			myKwArgs = self.util.getACopy(kwargs)

			myReportId = "adhoc.dbadmin.roster.report" 

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(myKwArgs)])))

			# validating securityToken
			self.sec.validateSecToken(myKwArgs["securityToken"])

			# checking for required arguments
			myRequiredArgList = ["securityToken","opco","status","dbTechnology","recepient","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "status", "type" : str, "value" : myKwArgs["status"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, [])

			# retrieving sys config data
			mySysConfigData = self.repo.getSysConfig(myKwArgs["securityToken"], myKwArgs["opco"])

			if not mySysConfigData:
				raise ValueError(f"Sys config data for Opco --> {myKwArgs['opco']} is missing !!!")

			myReportMeta = [report for report in mySysConfigData["reports"] if report["reportId"] == myReportId]
			
			if not myReportMeta:
				raise ValueError(f"Report '{myReportId}' metadata is missing in repository !!")

			if myReportMeta:
				myReportMeta = myReportMeta[0]

			print(f"Report metadata >>> {myReportMeta}")
			
			#myDay, myDyName, myMonth, myMonthName, myYear = self.util.getEachElemOfDate(self.util.lambdaGetCurrReadableTime())
			#myMonthYear = "".join([myMonthName, " ", str(myYear)])

			myHeader = myReportMeta["reportHeader"].format(dbTechnology = myKwArgs["dbTechnology"].upper(), opco = myKwArgs["opco"].upper())
			myHeaderCellRange = myReportMeta["cellRange"]
			myReportSheet = myReportMeta["sheetName"]

			myReportFileNamePrefix = myReportMeta["fileNamePrefix"]
			myReportFileRetDays = myReportMeta["retentionDays"]

			myRecepient = myKwArgs["recepient"]
			mySubject = myReportMeta["subject"].format(opco = myKwArgs['opco'].upper(), dbTechnology = myKwArgs["dbTechnology"].upper())
			myEmailBody = myReportMeta["emailBody"].format(opco = myKwArgs['opco'].upper(), dbTechnology = myKwArgs['dbTechnology']).replace("\\n","\n")
			myFromMailBox = (myReportMeta["from"], myReportMeta["fromEmail"])

			myKwArgs.update({"consolidated" : "no"})
			myKwArgs.pop("recepient")

			myDBResult = self.repo.getDBAdminRoster(**myKwArgs)

			if myDBResult["status"] == self.Globals.unsuccess:
				return myDBResult

			myDBAdminRoster = myDBResult["data"]

			if not myDBAdminRoster:
				return self.util.buildResponse(self.Globals.success, f"No DB Admin roster found OPCO: {myKwArgs['opco']}, DB Technology: {myKwArgs['dbTechnology']} and status : {myKwArgs['status']} !!!")

			# building file name for this report, since we have got data
			myFileName = self.util.buildPath(self.REPORT_LOC, \
				"".join([myReportFileNamePrefix, myKwArgs["opco"], "_", str(self.util.getCurDateTimeForDir()), ".xlsx"]))

			# we are here because we have roster data which need to be processed
			# initializing file
			myWorkBook, myWorkSheet = self.initXlsxFile(\
				securityToken = myKwArgs["securityToken"], file = myFileName, \
				header = myHeader, headerCellRange = myHeaderCellRange, sheet = myReportSheet, border = {})

			# we will add following sub header to this file
			#mySubHeaderFormat = myWorkBook.add_format({'bold' : True, 'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : True})
			#mySubHeaderValueFormat = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : False})
			mySubHeaderFormat = myWorkBook.add_format(self.SUB_HEAD_FORMAT_OBJ)
			mySubHeaderValueFormat = myWorkBook.add_format(self.SUB_HEAD_VAL_FORMAT_OBJ)

			# writing opco, region, start and end date
			myWorkSheet.write_string("A4","Opco",mySubHeaderFormat)
			myWorkSheet.write_string("A5","DB Technology ",mySubHeaderFormat)

			myWorkSheet.write_string("B4", myKwArgs["opco"],mySubHeaderValueFormat)
			myWorkSheet.write_string("B5", myKwArgs["dbTechnology"].upper(),mySubHeaderValueFormat)

			#column_heading_format_str = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})
			#column_heading_format_date = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})
			#column_heading_format_ts = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})

			column_heading_format_str = myWorkBook.add_format(self.COL_HEAD_FORMAT_STR_OBJ)
			column_heading_format_date = myWorkBook.add_format(self.COL_HEAD_FORMAT_DATE_OBJ)
			column_heading_format_ts = myWorkBook.add_format(self.COL_HEAD_FORMAT_TS_OBJ)

			myWorkSheet.set_column(0,8, 30) # sets column 0 to 1 (A:B) to 30

			myWorkSheet.write_string('A7',"Employee Id",column_heading_format_str)
			myWorkSheet.write_string('B7',"Name",column_heading_format_str)
			myWorkSheet.write_string('C7',"Location",column_heading_format_str)
			myWorkSheet.write_string('D7',"Email",column_heading_format_str)
			myWorkSheet.write_string('E7',"Contact#",column_heading_format_str)
			myWorkSheet.write_string('F7',"Technology",column_heading_format_str)
			myWorkSheet.write_string('G7',"DB Login Id",column_heading_format_str)
			myWorkSheet.write_string('H7',"Onboarding Date",column_heading_format_str)

			# creating data format for audit data
			#https://en.wikipedia.org/wiki/Web_colors
			#data_format_str = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False })
			#data_format_ts = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'num_format':'yyyy-mm-dd hh:mm:ss.000', 'bold' : False })
			#data_format_date = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True , 'num_format':'mm/dd/yyyy', 'bold' : False})
			#data_format_str_err = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False, 'text_wrap': True })
			data_format_str = myWorkBook.add_format(self.DATA_FORMAT_STR_OBJ)
			data_format_num = myWorkBook.add_format(self.DATA_FORMAT_NUM_OBJ)
			data_format_ts = myWorkBook.add_format(self.DATA_FORMAT_TS_OBJ)
			data_format_date = myWorkBook.add_format(self.DATA_FORMAT_DATE_OBJ)
			data_format_str_err = myWorkBook.add_format(self.DATA_FORMAT_STR_ERR_OBJ)

			# writing roster data
			myDataRow = 7 # this is row 8
			for admin in myDBAdminRoster:
				myWorkSheet.write_string(myDataRow,0,str(admin["_id"]),data_format_str)
				myWorkSheet.write_string(myDataRow,1,admin["name"],data_format_str)
				if "location" in admin:
					myWorkSheet.write_string(myDataRow,2,admin["location"],data_format_str)

				if "email" in admin:
					myWorkSheet.write_string(myDataRow,3,admin["email"],data_format_str)

				if "contact#" in admin:
					myWorkSheet.write_string(myDataRow,4,admin["contact#"],data_format_str)

				if "technology" in admin and "dbTechnology" in admin["technology"]:
					myWorkSheet.write_string(myDataRow,5,admin["technology"]["dbTechnology"].upper(),data_format_str)

				if "technology" in admin and "dbLoginId" in admin["technology"]:
					myDBLoginIds = ",".join(admin["technology"]["dbLoginId"])
					myWorkSheet.write_string(myDataRow,6,myDBLoginIds,data_format_str)

				if "technology" in admin and "onBoardDate" in admin["technology"]:
					myWorkSheet.write_string(myDataRow,7,str(admin["technology"]["onBoardDate"]),data_format_str)

				myDataRow += 1

			# close the workbook
			myWorkBook.close()

			self.LOGGER.info(f"file {myFileName} is created, sending email to {myRecepient}")

			self.util.sendEmail(\
				myFromMailBox, \
				myRecepient, None, None, \
				mySubject, \
				myEmailBody, \
				'plain', myFileName)

			self.LOGGER.debug("email is sent, performing cleanup")

			myFilesDeleted = self.util.deleteFilesOlderThanDays(self.REPORT_LOC, ".xlsx", myReportFileRetDays)

			self.LOGGER.info(f"files older than {myReportFileRetDays} deleted >>> {myFilesDeleted}")

			return self.util.buildResponse(self.Globals.success, f'file {self.util.getFileName(myFileName)} is sent via email to {myRecepient}')

		except Exception as error:
			self.LOGGER.error(str(error), exc_info = True)
			raise error

	def genAuditScanStatusReport(self, **kwargs):
		"""
		parameter
			opco, region, dbTechnology
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			myKwArgs = self.util.getACopy(kwargs)

			myReportId = "daily.auditScan.status.report" 

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(myKwArgs)])))

			# validating securityToken
			self.sec.validateSecToken(myKwArgs["securityToken"])

			# checking for required arguments
			myRequiredArgList = ["securityToken","opco","startDate","endDate","recepient","userId"]
			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "startDate", "type" : str, "value" : myKwArgs["startDate"]},
				{"arg" : "endDate", "type" : str, "value" : myKwArgs["endDate"]},
				{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},				
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, [])

			if not self.util.isValidDate(myKwArgs["startDate"]):
				raise ValueError(f"Invalid start date {myKwArgs['startDate']} !!!")

			if not self.util.isValidDate(myKwArgs["endDate"]):
				raise ValueError(f"Invalid end date {myKwArgs['endDate']} !!!")

			# retrieving sys config data
			mySysConfigData = self.repo.getSysConfig(myKwArgs["securityToken"], myKwArgs["opco"])

			if not mySysConfigData:
				raise ValueError(f"Sys config data for Opco --> {myKwArgs['opco']} is missing !!!")

			myReportMeta = [report for report in mySysConfigData["reports"] if report["reportId"] == myReportId]
			
			if not myReportMeta:
				raise ValueError(f"Report '{myReportId}' metadata is missing in repository !!")

			if myReportMeta:
				myReportMeta = myReportMeta[0]

			print(f"Report metadata >>> {myReportMeta}")
			
			#myDay, myDyName, myMonth, myMonthName, myYear = self.util.getEachElemOfDate(self.util.lambdaGetCurrReadableTime())
			#myMonthYear = "".join([myMonthName, " ", str(myYear)])

			myHeader = myReportMeta["reportHeader"].format(opco = myKwArgs["opco"].upper())
			myHeaderCellRange = myReportMeta["cellRange"]
			myReportSheet = myReportMeta["sheetName"]

			myReportFileNamePrefix = myReportMeta["fileNamePrefix"]
			myReportFileRetDays = myReportMeta["retentionDays"]

			myRecepient = myKwArgs["recepient"]
			mySubject = myReportMeta["subject"].format(opco = myKwArgs["opco"].upper())
			myEmailBody = myReportMeta["emailBody"].format(opco = myKwArgs["opco"].upper()).replace("\\n","\n")
			myFromMailBox = (myReportMeta["from"], myReportMeta["fromEmail"])

			myKwArgs.pop("recepient")

			#getAuditScanStatus(self, securityToken, opco, region, env, dbTechnology, dbTechnology, startDate, endDate)
			
			myDBResult = self.repo.getAuditScanStatus(**myKwArgs)

			if myDBResult["status"] == self.Globals.unsuccess:
				return myDBResult

			myAuditScanStatusData = myDBResult["data"]

			#if not myAuditScanStatusData:
			#	return self.util.buildResponse(self.Globals.success, f"No audit scan found for OPCO: {myKwArgs['opco']} !!!")

			# building file name for this report, since we have got data
			myFileName = self.util.buildPath(self.REPORT_LOC, \
				"".join([myReportFileNamePrefix, myKwArgs["opco"], "_", str(self.util.getCurDateTimeForDir()), ".xlsx"]))

			# we are here because we have roster data which need to be processed
			# initializing file
			myWorkBook, myWorkSheet = self.initXlsxFile(\
				securityToken = myKwArgs["securityToken"], file = myFileName, \
				header = myHeader, headerCellRange = myHeaderCellRange, sheet = myReportSheet, border = {})

			# we will add following sub header to this file
			#mySubHeaderFormat = myWorkBook.add_format({'bold' : True, 'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : True})
			#mySubHeaderValueFormat = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : False})
			mySubHeaderFormat = myWorkBook.add_format(self.SUB_HEAD_FORMAT_OBJ)
			mySubHeaderValueFormat = myWorkBook.add_format(self.SUB_HEAD_VAL_FORMAT_OBJ)

			# writing opco, region, start and end date
			myWorkSheet.write_string("A4","Opco",mySubHeaderFormat)
			myWorkSheet.write_string("A5","Start Date",mySubHeaderFormat)
			myWorkSheet.write_string("A6","End Date",mySubHeaderFormat)

			myWorkSheet.write_string("B4", myKwArgs["opco"],mySubHeaderValueFormat)
			#myWorkSheet.write_string("B7", myKwArgs["dbTechnology"].upper(),mySubHeaderValueFormat)

			myWorkSheet.write_string("B5", myKwArgs["startDate"], mySubHeaderValueFormat)
			myWorkSheet.write_string("B6", myKwArgs["endDate"], mySubHeaderValueFormat)

			#column_heading_format_str = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})
			#column_heading_format_date = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})
			#column_heading_format_ts = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 11, 'font_name' : 'Callibri', 'border' : True, 'bold' : True, 'bg_color' : '#1E90FF'})

			column_heading_format_str = myWorkBook.add_format(self.COL_HEAD_FORMAT_STR_OBJ)
			column_heading_format_date = myWorkBook.add_format(self.COL_HEAD_FORMAT_DATE_OBJ)
			column_heading_format_ts = myWorkBook.add_format(self.COL_HEAD_FORMAT_TS_OBJ)

			myWorkSheet.set_column(0,13, 30) # sets column 0 to 13 (A:L) to 30
			myWorkSheet.set_column(14,14, 60) # sets column M to 60

			myWorkSheet.write_string('A8',"Host",column_heading_format_str)
			myWorkSheet.write_string('B8',"Status",column_heading_format_str)
			myWorkSheet.write_string('C8',"Timestamp",column_heading_format_str)
			myWorkSheet.write_string('C8',"Scan Timestamp",column_heading_format_str)
			myWorkSheet.write_string('D8',"Status",column_heading_format_str)			
			myWorkSheet.write_string('E8',"Scan File",column_heading_format_str)
			myWorkSheet.write_string('F8',"Status",column_heading_format_str)
			myWorkSheet.write_string('G8',"DB Technology",column_heading_format_str)
			myWorkSheet.write_string('H8',"Tenant Id",column_heading_format_str)
			myWorkSheet.write_string('I8',"Status (Scan)",column_heading_format_str)
			myWorkSheet.write_string('J8',"Status (Scan Transmit)",column_heading_format_str)
			myWorkSheet.write_string('K8',"Audit Files",column_heading_format_str)			
			myWorkSheet.write_string('L8',"Status (Aud Tansmit)",column_heading_format_str)
			myWorkSheet.write_string('M8',"Comments",column_heading_format_str) 
			# we need to provide the error as comment which might have occurred for scan/aud transmit

			# creating data format for audit data
			#https://en.wikipedia.org/wiki/Web_colors
			#data_format_str = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False })
			#data_format_ts = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'num_format':'yyyy-mm-dd hh:mm:ss.000', 'bold' : False })
			#data_format_date = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True , 'num_format':'mm/dd/yyyy', 'bold' : False})
			#data_format_str_err = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False, 'text_wrap': True })

			data_format_str = myWorkBook.add_format(self.DATA_FORMAT_STR_OBJ)
			data_format_num = myWorkBook.add_format(self.DATA_FORMAT_NUM_OBJ)
			data_format_ts = myWorkBook.add_format(self.DATA_FORMAT_TS_OBJ)
			data_format_date = myWorkBook.add_format(self.DATA_FORMAT_DATE_OBJ)
			data_format_str_err = myWorkBook.add_format(self.DATA_FORMAT_STR_ERR_OBJ)

			# writing data
			myHostInventoryArgs = {
				"securityToken" : myKwArgs["securityToken"],
				"opco" : myKwArgs["opco"],
				"region" : "all",
				"dcLocation" : "all",
				"dbTechnology" : "all",
				"env" : "all",
				"tag" : "all",
				"userId" : myKwArgs["userId"]
			}

			myDBResult = self.repo.getHostInventory(**myHostInventoryArgs)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"An error {myDBResult['message']} occurred while retrieving hosts inventory !!!")
			else:
				myHostsInvetory = myDBResult["data"]

			myDataRow = 9 # this is row 10

			for host in myHostsInvetory:
				myWorkSheet.write_string(myDataRow, 0, host["hostName"], data_format_str)
				if ("scanEnabled" in host and host["scanEnabled"].lower() == "no") or ("scanEnabled" not in host):
					myWorkSheet.write_string(myDataRow, 1, "Scan not enabled", data_format_str)
					myDataRow += 1
					continue

				myHostScanData = [scanData for scanData in myAuditScanStatusData if scanData["hostName"].strip().lower() == host["hostName"].strip().lower()]

				if not myHostScanData:
					#myWorkSheet.write_string(myDataRow, 0, host["hostName"], data_format_str)
					myWorkSheet.write_string(myDataRow, 1, "Missing", data_format_str)
					myDataRow += 1
					continue

				myHostScanData = myHostScanData[0]

				if not isinstance(myHostScanData, list):
					myHostScanData = [myHostScanData]

				for hostScan in myHostScanData:
					for scanFile in hostScan["details"]:
						for tenant in scanFile["tenants"]:
							myWorkSheet.write_string(myDataRow, 0, host["hostName"], data_format_str)
							myWorkSheet.write_string(myDataRow, 1, "Active", data_format_str)
							myWorkSheet.write_string(myDataRow, 2, str(hostScan["ts"]),data_format_str)
							myWorkSheet.write_string(myDataRow, 3, str(hostScan["scanTS"]),data_format_str)
							#myWorkSheet.write_string(myDataRow, 2, hostScan["hostName"], data_format_str)
							myWorkSheet.write_string(myDataRow, 4, hostScan["status"], data_format_str)
							myWorkSheet.write_string(myDataRow, 5, scanFile["hostScanFile"], data_format_str)
							myWorkSheet.write_string(myDataRow, 6, scanFile["status"], data_format_str)
							myWorkSheet.write_string(myDataRow, 7, tenant["dbTechnology"], data_format_str)
							myWorkSheet.write_string(myDataRow, 8, tenant["tenantId"], data_format_str)
							myWorkSheet.write_string(myDataRow, 9, tenant["scanStatus"], data_format_str)
							myWorkSheet.write_string(myDataRow, 10, tenant["scanTransmitStatus"], data_format_str)
							if "totalAuditFiles" in tenant:
								myWorkSheet.write_string(myDataRow, 11, str(tenant["totalAuditFiles"]), data_format_str)
							else:
								myWorkSheet.write_string(myDataRow, 11, "", data_format_str)

							myWorkSheet.write_string(myDataRow, 12, tenant["audTransmitStatus"], data_format_str)
							myComments = ""
							
							if hostScan["status"] == self.Globals.unsuccess:
								# overall status is an error, we need to print error in comments
								if tenant["scanTransmitStatus"] == self.Globals.unsuccess:
									myComments = f"Scan Transmit Response: {scanFile['message']}"
								else:
									# scan transmit was successful, navigating the errors, checking audit file transit error
									for aud_ in tenant["auditFiles"]:
										if aud_["transmitStatus"] == self.Globals.unsuccess:
											myComments = "".join([ myComments, "\n", f"audFile : {aud_['file']} \n error: {aud_['message']} " ])

							myWorkSheet.write_string(myDataRow, 12, myComments, data_format_str)
							myDataRow += 1

			# close the workbook
			myWorkBook.close()

			self.LOGGER.info(f"file {myFileName} is created, sending email to {myRecepient}")

			self.util.sendEmail(\
				myFromMailBox, \
				myRecepient, None, None, \
				mySubject, \
				myEmailBody, \
				'plain', myFileName)

			self.LOGGER.debug("email is sent, performing cleanup")

			myFilesDeleted = self.util.deleteFilesOlderThanDays(self.REPORT_LOC, ".xlsx", myReportFileRetDays)

			self.LOGGER.info(f"files older than {myReportFileRetDays} deleted >>> {myFilesDeleted}")

			return self.util.buildResponse(self.Globals.success, f'file {self.util.getFileName(myFileName)} is sent via email to {myRecepient}')

		except Exception as error:
			self.LOGGER.error(str(error), exc_info = True)
			raise error

	def genTenantVerCompReport(self, **kwargs):
		"""
		parameter
			opco, dbTechnology
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			myKwArgs = self.util.getACopy(kwargs)

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(myKwArgs)])))

			# validating securityToken
			self.sec.validateSecToken(myKwArgs["securityToken"])

			# checking for required arguments
			myRequiredArgList = ["securityToken","opco","dbTechnology","recepient","userId"]

			self.util.valArguments(myRequiredArgList, myKwArgs, [])

			myArgValidationList = [
				{"arg" : "securityToken", "type" : str, "value" : myKwArgs["securityToken"]},
				{"arg" : "opco", "type" : str, "value" : myKwArgs["opco"]},
				{"arg" : "dbTechnology", "type" : str, "value" : myKwArgs["dbTechnology"]},
				{"arg" : "recepient", "type" : str, "value" : myKwArgs["recepient"]},				
				{"arg" : "userId", "type" : str, "value" : myKwArgs["userId"]}				
			]

			self.util.valArguments2(myArgValidationList, [])

			myReportId = f"monthly.{myKwArgs['dbTechnology']}.version.compliance.report" 

			# retrieving sys config data
			mySysConfigData = self.repo.getSysConfig(myKwArgs["securityToken"], myKwArgs["opco"])

			if not mySysConfigData:
				raise ValueError(f"Sys config data for Opco --> {myKwArgs['opco']} is missing !!!")

			myReportMeta = [report for report in mySysConfigData["reports"] if report["reportId"] == myReportId]
			
			if not myReportMeta:
				raise ValueError(f"Report '{myReportId}' metadata is missing in repository !!")

			if myReportMeta:
				myReportMeta = myReportMeta[0]

			print(f"Report metadata >>> {myReportMeta}")
			
			myDay, myDyName, myMonth, myMonthName, myYear = self.util.getEachElemOfDate(self.util.lambdaGetCurrReadableTime())
			myMonthYear = "".join([myMonthName, " ", str(myYear)])

			myHeader = myReportMeta["reportHeader"]
			myHeaderCellRange = myReportMeta["cellRange"]
			myReportSheet = myReportMeta["sheetName"]

			myReportFileNamePrefix = myReportMeta["fileNamePrefix"]
			myReportFileRetDays = myReportMeta["retentionDays"]

			myRecepient = myKwArgs["recepient"]
			mySubject = myReportMeta["subject"].format(opco = myKwArgs["opco"].upper(), monthYear = myMonthYear)
			myEmailBody = myReportMeta["emailBody"].format(opco = myKwArgs["opco"].upper()).replace("\\n","\n")
			myFromMailBox = (myReportMeta["from"], myReportMeta["fromEmail"])

			myKwArgs.pop("recepient")

			#getAuditScanStatus(self, securityToken, opco, region, env, dbTechnology, dbTechnology, startDate, endDate)
			
			myDBResult = self.repo.getTenantVersionDetail(\
				myKwArgs["securityToken"], myKwArgs["opco"], myKwArgs["dbTechnology"])

			if myDBResult["status"] == self.Globals.unsuccess:
				return myDBResult

			myTenantVerCompData = myDBResult["data"]

			if not myTenantVerCompData:
				return self.util.buildResponse(self.Globals.success, f"There are no {myKwArgs['dbTechnology'].upper()} database found for OPCO: {myKwArgs['opco']} !!!")

			# building file name for this report, since we have got data
			myFileName = self.util.buildPath(self.REPORT_LOC, \
				"".join([myReportFileNamePrefix, myKwArgs["opco"], "_", str(self.util.getCurDateTimeForDir()), ".xlsx"]))

			# we are here because we have roster data which need to be processed
			# initializing file
			myWorkBook, myWorkSheet = self.initXlsxFile(\
				securityToken = myKwArgs["securityToken"], file = myFileName, \
				header = myHeader, headerCellRange = myHeaderCellRange, sheet = myReportSheet, border = {})

			# we will add following sub header to this file
			#mySubHeaderFormat = myWorkBook.add_format({'bold' : True, 'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : True})
			#mySubHeaderValueFormat = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 10, 'align' : 'left', 'border' : True, "bold" : False})
			mySubHeaderFormat = myWorkBook.add_format(self.SUB_HEAD_FORMAT_OBJ)
			mySubHeaderValueFormat = myWorkBook.add_format(self.SUB_HEAD_VAL_FORMAT_OBJ)

			# writing opco, region, start and end date
			myWorkSheet.write_string("A4","Opco",mySubHeaderFormat)
			myWorkSheet.write_string("B4", myKwArgs["opco"],mySubHeaderValueFormat)

			column_heading_format_str = myWorkBook.add_format(self.COL_HEAD_FORMAT_STR_OBJ)
			column_heading_format_date = myWorkBook.add_format(self.COL_HEAD_FORMAT_DATE_OBJ)
			column_heading_format_ts = myWorkBook.add_format(self.COL_HEAD_FORMAT_TS_OBJ)

			myWorkSheet.set_column(0,1, 15) # sets columns (A:B) to size 15
			myWorkSheet.set_column(2,3, 30) # sets columns (C:D) to size 30
			myWorkSheet.set_column(4,7, 20) # sets columns (E:G) to size 20
			#myWorkSheet.set_column(4,6, 20) # sets columns (E:F) to size 20

			myWorkSheet.write_string('A6',"Region",column_heading_format_str)
			myWorkSheet.write_string('B6',"Env",column_heading_format_str)
			myWorkSheet.write_string('C6',"Host",column_heading_format_str)
			myWorkSheet.write_string('D6',"Tenant DB",column_heading_format_str)
			myWorkSheet.write_string('E6',"DB Version",column_heading_format_str)
			myWorkSheet.write_string('F6',"Released Version",column_heading_format_str)
			myWorkSheet.write_string('G6',"Released Date",column_heading_format_str)
			myWorkSheet.write_string('H6',"Status",column_heading_format_str)			
			# we need to provide the error as comment which might have occurred for scan/aud transmit

			# creating data format for audit data
			#https://en.wikipedia.org/wiki/Web_colors
			#data_format_str = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False })
			#data_format_ts = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'num_format':'yyyy-mm-dd hh:mm:ss.000', 'bold' : False })
			#data_format_date = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True , 'num_format':'mm/dd/yyyy', 'bold' : False})
			#data_format_str_err = myWorkBook.add_format({'font_color' : 'black', 'font_size' : 9, 'font_name' : 'Arial', 'border' : True, 'bold' : False, 'text_wrap': True })

			data_format_str = myWorkBook.add_format(self.DATA_FORMAT_STR_OBJ)
			data_format_num = myWorkBook.add_format(self.DATA_FORMAT_NUM_OBJ)
			data_format_ts = myWorkBook.add_format(self.DATA_FORMAT_TS_OBJ)
			data_format_date = myWorkBook.add_format(self.DATA_FORMAT_DATE_OBJ)
			data_format_str_err = myWorkBook.add_format(self.DATA_FORMAT_STR_ERR_OBJ)
			data_format_str_non_comp = myWorkBook.add_format(self.DATA_FORMAT_NON_COMP)
			data_format_str_at_risk = myWorkBook.add_format(self.DATA_FORMAT_AT_RISK)
			data_format_str_comp = myWorkBook.add_format(self.DATA_FORMAT_COMP)

			#red_font_color_format = workbook.add_format({'font_color': 'red'})

			myDataRow = 6 # this is row 7
			for tenant in myTenantVerCompData:
				myWorkSheet.write_string(myDataRow, 0, tenant["region"], data_format_str)
				myWorkSheet.write_string(myDataRow, 1, tenant["env"].upper(), data_format_str)
				myWorkSheet.write_string(myDataRow, 2, tenant["host"],data_format_str)
				myWorkSheet.write_string(myDataRow, 3, tenant["tenant"],data_format_str)
				myWorkSheet.write_string(myDataRow, 4, tenant["version"],data_format_str)
				myWorkSheet.write_string(myDataRow, 5, tenant["verReleased"],data_format_str)
				myWorkSheet.write_string(myDataRow, 6, self.util.convertDate2Str(tenant["verReleasedDT"],"%m/%d/%Y"),data_format_date)

				if tenant["status"].lower() == "compliant":
					myWorkSheet.write_string(myDataRow, 7, tenant["status"], data_format_str_comp)
				elif tenant["status"].lower() == "at-risk":
					myWorkSheet.write_string(myDataRow, 7, tenant["status"], data_format_str_at_risk)
				elif tenant["status"].lower() == "non-compliant":
					myWorkSheet.write_string(myDataRow, 7, tenant["status"], data_format_str_non_comp)
				else:
					myWorkSheet.write_string(myDataRow, 7, tenant["status"], data_format_str)

				myDataRow += 1

			# close the workbook
			myWorkBook.close()

			self.LOGGER.info(f"file {myFileName} is created, sending email to {myRecepient}")

			self.util.sendEmail(\
				myFromMailBox, \
				myRecepient, None, None, \
				mySubject, \
				myEmailBody, \
				'plain', myFileName)

			self.LOGGER.debug("email is sent, performing cleanup")

			myFilesDeleted = self.util.deleteFilesOlderThanDays(self.REPORT_LOC, ".xlsx", myReportFileRetDays)

			self.LOGGER.info(f"files older than {myReportFileRetDays} deleted >>> {myFilesDeleted}")

			return self.util.buildResponse(self.Globals.success, f'file {self.util.getFileName(myFileName)} is sent via email to {myRecepient}')

		except Exception as error:
			self.LOGGER.error(str(error), exc_info = True)
			raise error

	def sendComplianceReport(self, securityToken):
		"""
		Sends report for compliance

		- **parameters**, **return** and **raises**::

			:param arg1: securityToken (string )
			:return: response (json)
			)
			:raises: ValueError

		- section **Example** using the double commas syntax::

			:Example:
				
				sendComplianceReport('securityToken'}

		.. note::
			
		.. warning:: 

		.. seealso:: 

		"""
		try:
			myModuleName = sys._getframe().f_code.co_name

			myKwArgs = self.util.getACopy(kwargs)

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([str(myKwArgs)])))
			"""
			>>> from com.mmc.common.utility import Utility
			>>> util = Utility()
			>>> a = util.getDateFromSched({"freq" : "weekly","day" : "monday"})
			>>> a
			datetime.datetime(2020, 12, 21, 0, 0)
			>>> util.addTimeToDate
			util.addTimeToDate(      util.addTimeToDateTime(
			>>> util.addTimeToDateTime(a,6,23,59,59,59)
			datetime.datetime(2020, 12, 27, 23, 59, 59, 59)
			>>> exit()

			"""
		except Exception as error:
			self.LOGGER.error(str(error), exc_info = True)
			raise error

if __name__ == "__main__":
	import sys, xlsx
	xlsx = Xlsx()
	print("arguments >>>", sys.argv)
	myFile = sys.argv[1]
	myHeader = sys.argv[2]
	if xlsx.util.isFileExists(myFile):
		xlsx.util.deleteFile(myFile)
	myWorkBook = xlsx.initFile(file = myFile, header = myHeader, sheet = "OpsMgr User Report", border = {})

	myWorkBook.close()
