from com.<>.common.globals import Globals
from com.<>.common.singleton import Singleton

from urllib.parse import quote_plus
from git import Repo
from shutil import rmtree, copy, copy2, move
from copy import deepcopy
from pathlib import Path
from contextlib import closing
from dateutil.relativedelta import relativedelta, FR, SA, SU, MO, TU, WE
from contextlib import contextmanager
from functools import wraps, partial
#from ldap3 import Server, Connection, AUTO_BIND_NO_TLS
#from memory_profiler import memory_usage

import json, os, sys, platform, psutil, datetime, time, subprocess, socket, re, uuid, getpass, yaml, glob

class JsonFormatter(object, metaclass=Singleton):
	def format(self, record):
		obj = {attr: getattr(record, attr)
			for attr in ATTR_TO_JSON}
		return json.dumps(obj, indent=5)

class Utility(object, metaclass=Singleton):
	def __init__(self):
		#self.Globals = Globals()

		#lambda functions

		self.lambdaGetCurrDateTime = lambda : datetime.datetime.now()
		self.lambdaGetCurrReadableTime = lambda : time.ctime()

		self.lamdbdaGetCurDir = lambda : os.getcwd()

		self.lamdbaGetAllEnvVar = lambda : os.environ

		self.lambdaGetCurrPID = lambda : os.getpid()
		self.lambdaGetMyParentPID = lambda : psutil.Process(os.getpid()).ppid()
		self.lambdaGetAllPID = lambda : list(psutil.process_iter(['pid']))

		self.lambdaAdd = lambda value, inc : value  
		# print ordinal # 1st, 2nd, 3rd, 4th .....
		self.lambdaOrdinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])

		self.lambdaGetCurTSStr = lambda : time.ctime()
		self.lambdaGetCurrTSTZ = lambda tz = self.TZ : datetime.datetime.now(tz if tz else self.TZ)
		self.lambdaGetCurrTSTZStr = lambda tz  = self.TZ : datetime.datetime.now(tz if tz else self.TZ).isoformat()
		self.lambdaGetCurUTCTSStr = lambda : datetime.datetime.utcnow().isoformat()
		self.lambdaCurrMethod = lambda n=0: sys._getframe(n + 1).f_code.co_name

		requests.packages.urllib3.disable_warnings("InsecureRequestWarning")
		urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
		
		self.outputStdout = "stdout"
		self.outputStdoutNFile = "both"
		self.outputFile = "file"

		self.Globals = Globals()

		# smtp server
		if self.getEnvKeyVal("SMTP_SERVER"):
			self.SMTP_SERVER = self.getEnvKeyVal("SMTP_SERVER")
		else:
			self.SMTP_SERVER = "nasa1smtp.mmc.com"

		# AD GRoups
		if self.getEnvKeyVal("LDAP_SERVER"):
			self.LDAP_SERVER = self.getEnvKeyVal("LDAP_SERVER").split(":")[0]
			self.LDAP_SERVER_PORT = int(self.getEnvKeyVal("LDAP_SERVER").split(":")[1])
		else:
			self.LDAP_SERVER = ""
			self.LDAP_SERVER_PORT = ""

		self.LDAP_SERVER_CONFIG = {
			"CORP" : {
				"user" : "CORP\\svc-dev-deploy-app",
				"userPass" : "rSa3mc7%#sfasMBQZ"
			},
			"DMZPROD01" : {
				"user" : "DMZPROD01\\svc-uat-deploy-app",
				"userPass" : "rSa3mc7%#sfasMBQZ"			
			}
		}

		self.ADGRP_OU_LIST = ["OU=Applications,OU=Groups","OU=User Role Groups,OU=Centrify,OU=Enterprise Systems","OU=Enterprise Systems"]
		self.ADGRP_OU = "OU=User Role Groups,OU=Centrify,OU=Enterprise Systems"

		self.ADUSER_OU_LIST = ["OU=MMC_Users","OU=Administrative"]
		self.ADUSER_OU = "OU=MMC_Users"

		"""
		for server_ in self.LDAP_SERVERS_LIST:
			if self.isPortOpen(server_["server"], server_["port"]):
				# checking if we have successful connection
				try:
					server = Server(server_["server"], port = server_["port"], use_ssl=False, get_info='ALL')
					print("establishing connectio to {server}")
					conn = Connection(server, auto_bind=AUTO_BIND_NO_TLS, user = server_["user"], password = server_["userPass"])
					conn.bind()
					self.LDAP_SERVER = server_["server"]
					self.LDAP_SERVER_PORT = server_["port"]
					self.BASE_DC = server_["DC"]
					#self.AD_DOMAIN = server_["domain"]
					self.LDAP_USER = server_["user"]
					self.LDAP_USER_PASS = server_["userPass"]
					break
				except Exception as error:
					print(f"an error {error} occurred while establish connection to {server}")
		if self.isPortOpen(self.LDAP_SERVER, self.LDAP_SERVER_PORT):
			self.BASE_DC =  ",".join(["".join(["DC=",dc]) for dc in self.LDAP_SERVER.split(".")[2:]])
			self.LDAP_USER = self.LDAP_SERVER_CONFIG[self.LDAP_SERVER.split(".")[2].upper()]["user"]
			self.LDAP_USER_PASS = self.LDAP_SERVER_CONFIG[self.LDAP_SERVER.split(".")[2].upper()]["userPass"]
		else:
			self.LDAP_SERVER = self.LDAP_SERVER_PORT = self.LDAP_SERVER = self.BASE_DC = self.LDAP_SERVER = ""
		"""

	# file functions
	def __repr__(self):
		return "(%s)" % (self.__class__)

	def __str__(self):
		return "(%s)" % (self.__class__)


	def isTextStartsWithKW(self, _text, kwList):
		"""
		Description: Checks if given text starts with any keywork in passed key word list
		Returns: Boolean
		Usage : isTextStartsWithKW(<secToken>,<sqlFileWPath>)
		"""
		#print('checking if text starts with any kw in lists, text  >',_text, ', kwlist> ', kwList)
		for keyWord in kwList:
			#print('checking text starts with kw, text >',_text, ", kw >", keyWord)
			if _text.lower().lstrip().replace(" ","").startswith(keyWord.lower().replace(" ","")):
				#print('found, text starts with, text > ',_text, ', kw >',keyWord)
				return True
		#print('text does not start with given kwlist, text > ',_text, ', kwlist >',kwList)
		return False

	def isTextEndsWithKW(self, _text, kwList):
		"""
		Description: Checks if given text ends with any keywork in passed key word list
		Returns: Boolean
		Usage : isTextEndsWithKW(<secToken>,<sqlFileWPath>)
		"""
		# print('checking if text ends with any kw in lists, text  >',_text, ', kwlist> ', kwList)

		for keyWord in kwList:
			#print('checking text ends with kw, text >',_text, ", kw >", keyWord)
			if _text.lower().rstrip().replace(" ","").endswith(keyWord.lower().replace(" ","")):
				#print('found, text ends with kw, text > ',_text, ', kw >',keyWord)
				return True
		#print('text does not end with given kwlist, text > ',_text, ', kwlist >',kwList)
		return False

	## Resource usage stats
	def getResourceUsage(self):
		if not os.platform.system().lower == "windows":
			import resource
			return {
				"peakMemUsage" : resource.getrusage(reosurce.RUSAGE_SELF).ru_maxrss,
				"userCpuTime" : resource.getrusage(reosurce.RUSAGE_SELF).ru_utime,
				"userCpuTime" : resource.getrusage(reosurce.RUSAGE_SELF).ru_stime
			}
		else:
			return {
				"peakMemUsage" : "not available in windows",
				"userCpuTime" : "not available in windows",
				"userCpuTime" : "not available in windows"
			}

	def getCurrTimeInFormat(self, format):
		# format : %m%d%y%H%M%S
		return datetime.datetime.now().strftime(format)

	# file (text/json)

	def getFileExtn(self, fileName):
		
		# will return the extension of a given file

		fileSplit = os.path.splitext(fileName)
		if isinstance(fileSplit, tuple):
			#return fileSplit[-1].replace(".","")
			return fileSplit[-1]

	def getFilesByExtn(self, path, extnList):
		"""
		returns all files for a given list extension and path (using generator, if we have dir with lots of inode or file helps to improve mem usage)
		"""
		myFiles = []

		if path and self.isDirExists(path):

			for file in os.scandir(path):
				if file.is_file() and self.getFileExtn(file.name) in  extnList:
					myFiles.append(file.name)

		return myFiles

	def getFilesByPattern(self, path, pattern):
		"""
		returns all files for a given path and pattern
		"""

		if not pattern:
			pattern = "*"

		if path and self.isDirExists(path):
			myAllFiles = glob.glob(self.buildPath(path,pattern))
			if not myAllFiles:
				return []
			else:
				return myAllFiles
		else:
			return []

	def encodeDictData(self, dictData, indent = 3, sort_keys = True):
		'''
		return json encoding of dictionary/list data with default indent of 3, sorted_keys = True
		'''
		return json.dumps(dictData, indent = indent, sort_keys = sort_keys, default=self.convertDT2IsoFormat)

	def convertDT2IsoFormat(self, dateTimeObj):
		"""
		converts date time object stored in a string to a date time object. Used in json dumps to convert dt str to dt object
		"""
		if isinstance(dateTimeObj, (datetime.datetime, datetime.date)):
			return  dateTimeObj.isoformat()

	def isValidDate(self, date_):
		"""
		checks if passed argument is a valid date
		"""
		try:
			if isinstance(date_, int):
				return False
			myDate = self.convStr2DateViaParser(date_)
			return True
		except Exception as error:
			return False

	def convStr2DateViaParser(self, date_):
		"""
		Convert string to date format using dateutil.parser
		"""
		try:
			if isinstance(date_, str):
				from dateutil import parser
				from dateutil.tz import tzutc
				return parser.parse(date_)
			elif (isinstance(date_, datetime.datetime) or isinstance(date_, datetime.date)):
				return date_
			else:
				print(type(date_))
				raise ValueError(f"Invalid date {date_} !!!")

		except Exception as error:
			raise

	def convertIsoDateStr2Date(self, isoDateTimeStr):
		"""
		converts ISO date time string to a date time object (useful in converting back datetime iso string stored in json to datetime object)
		"""
		#return  datetime.datetime.fromisoformat(isoDateTimeStr) # fromisoformat is only allowed in python 3.7+

		# checking if we got fraction of second in this date string
		if len(isoDateTimeStr.split(".")) > 1:
			# we got fraction using fraction format
			return  datetime.datetime.strptime(isoDateTimeStr,"%Y-%m-%dT%H:%M:%S.%f")
		else:
			return  datetime.datetime.strptime(isoDateTimeStr,"%Y-%m-%dT%H:%M:%S")

	def convertJsonDictToString(self, jsonData):
		
		return json.dumps(jsonData)

	def readJsonFile(self, jsonFile):
		try:
			if self.isFileExists(jsonFile):
				with open(jsonFile) as file:
					jsonData = json.load(file)
				return jsonData

		except Exception as error:
			raise ValueError("an error occurred reading json file {file} >>> {error}".format(file = jsonFile, error = str(error)))

	def readJsonFileGen(self, jsonFile):
		"""
		Returns generator of reading json object, we must use ijson to accomplish this
		https://pypi.org/project/ijson/
		self.getFileSizeBytes(fileName)
		"""
		try:
			if self.isFileExists(jsonFile):
				with open(jsonFile) as file:
					jsonData = json.load(file)

				return jsonData
		except Exception as error:
			raise ValueError("an error occurred reading json file {file} >>> {error}".format(file = jsonFile, error = str(error)))

	def readConfigTextFile(self, confFile):
		"""
		Reads text config file (where value is stored as key = value), removes all the comments from in line and begining of line as well.
		Returns as dict
		"""
		try:
			if not self.isFileExists(confFile):
				return tuple()

			myRawConfData = self.readTextFile(confFile)
			myConfigData = {}
			for line in myRawConfData.splitlines():
				myConigKey = myConigKeyVal = ""
				# checking for comment line and line which might be empty
				if not (line.strip().startswith("#")) and line.strip() :
					#print(f"found valid line >> {line}")
					# removing any comments # which may be inline
					#line = line[:] if find("#") == -1 else line[line.find("#")]
					myLineSplit = line.split("=")
					if len(myLineSplit) > 1:
						myConigKey = myLineSplit[0].strip()
						# spliting on space, will pick 1st value
						myConfigKeyVal = myLineSplit[1].strip()
						if myConfigKeyVal.startswith("'"):
							# value starts with "'", we need to find 2nd occurrence of
							myStartPos = myConfigKeyVal.find("'")
							myEndPos =  myConfigKeyVal.find("'", myStartPos+1)
							myConfigKeyVal = myConfigKeyVal[myStartPos:myEndPos+1].replace("'","")
						elif myConfigKeyVal.startswith('"'):
							myStartPos = myConfigKeyVal.find('"')
							myEndPos =  myConfigKeyVal.find('"', myStartPos+1)
							myConfigKeyVal = myConfigKeyVal[myStartPos:myEndPos+1].replace('"',"")
						else:
							# value doesn't start with either ' or ", will retrieve the value ignoring any comments
							myEndPos = myConfigKeyVal.strip().find("#")
							if myEndPos > 0:
								myConfigKeyVal = myConfigKeyVal.strip()[0:myEndPos-1]
							else:
								myConfigKeyVal = myConfigKeyVal.strip()

						myConfigKeyVal = myConfigKeyVal.replace("\t","").strip()
						myConfigData.update({myConigKey : myConfigKeyVal})
			return myConfigData	
		except Exception as error:
			raise error

	def readPGhbaConfigFile(self, confFile):
		"""
		Reads text config file (where value is stored as key = value), removes all the comments from in line and begining of line as well.
		Returns as dict
		"""
		try:
			if not self.isFileExists(confFile):
				#return tuple()
				return {}

			myRawConfData = self.readTextFile(confFile)

			myConfigData = []
			lineNum = 0
			for line in myRawConfData.splitlines():
				myConigKey = myConigKeyVal = ""
				# checking for comment line and line which might be empty
				if not (line.strip().startswith("#")) and line.strip() :
					# if we find "ldap" word in hba conf file then we need to make 2 part of string
					# 	1st is for ldap --> string[string.find("ldap"):]
					# 	2nd is for remaining ---> [elem for elem in string[:string.find("ldap")].split(" ") if elem.strip()]
					#  [for elem in ]
					if line.find("ldap") > 0:
						connHBAAddr = line[line.find("ldap"):]
						connHBAMethod = ""
						connHBAConfig = [elem for elem in line[:line.find("ldap")].split(" ") if elem.strip() ]
					else:
						connHBAConfig = [elem for elem in line.split(" ") if elem.strip() ]
						connHBAAddr = connHBAConfig[3] if len(connHBAConfig) >= 4 else ""
						connHBAMethod = connHBAConfig[4] if len(connHBAConfig) == 5 else ""

					connHBAType = connHBAConfig[0] if len(connHBAConfig) >= 4 else ""
					connHBADatabase = connHBAConfig[1] if len(connHBAConfig) >= 4 else ""
					connHBAUser = connHBAConfig[2] if len(connHBAConfig) >= 4 else ""
					lineNum += 1
					myConfigData.append({
						"step" : lineNum, 
						"type" : connHBAType, 
						"database" : connHBADatabase, 
						"user" : connHBAUser, 
						"address" : connHBAAddr,
						"method" : connHBAMethod
					})
			return myConfigData

		except Exception as error:
			raise error

	def readTextFile(self, textFile):
		try:
			if self.isFileExists(textFile):
				with open(textFile) as file:
					textData = file.read()

				return textData
		except Exception as error:
			raise ValueError("an error occurred reading text file {file} >>> {error}".format(file = textFile, error = str(error)))

	def readTxtFileGen(self, textFile, newLine = "\r\n"):
		"""
		Returns generator, you must iter through results. This is text file, using encoding utf8
		"""
		try:
			if self.isFileExists(textFile):
				with open(textFile, mode = "r", newline = newLine, encoding = "utf8") as file:
					while True:
						textData = file.read()
						if not textData:
							break
						yield textData

		except (IOError, OSError):
			raise ValueError("error opening text file {file} >>> {error}".format(file = textFile, error = str(error)))
		except Exception as error:
			raise ValueError("an error occurred reading text file (as a line) {file} >>> {error}".format(file = textFile, error = str(error)))

	def readTextFileLines(self, textFile):
		"""
		Returns all file lines contents
		"""
		try:
			if self.isFileExists(textFile):
				with open(textFile) as file:
					textData = file.readlines()

				return textData
		except Exception as error:
			raise ValueError("an error occurred reading text file (as a line) {file} >>> {error}".format(file = textFile, error = str(error)))

	def readTxtFileLineGen(self, textFile):
		"""
		Returns generator, you must iter through results. This is text file, using encoding utf8
		"""
		try:
			if self.isFileExists(textFile):
				with open(textFile, mode = "r", encoding = "utf8") as file:
					while True:
						textData = file.readline()
						if not textData:
							break
						yield textData

		except (IOError, OSError):
			raise ValueError("error opening text file {file} >>> {error}".format(file = textFile, error = str(error)))
		except Exception as error:
			raise ValueError("an error occurred reading text file (as a line) {file} >>> {error}".format(file = textFile, error = str(error)))

	def write2File(self, fileWPath, message, mode = 'a'):
		fileDirName = Path(self.getFileDirName(fileWPath))
		self.createDir(fileDirName)

		with open(fileWPath,mode) as file:
			file.write(message)

	def convertDict2Str(self, data_):
		"""
		convert dict to string
		"""
		return json.dumps(data_, indent = 4, default=self.convertDT2IsoFormat)

	def write2JsonFile(self, fileWPath, data_, mode = 'a'):
		#myIndentData = self.encodeDictData(data_)
		fileDirName = self.getFileDirName(fileWPath)
		self.createDir(fileDirName)		

		with open(fileWPath,mode) as file:
			# using convertDT2IsoFormat to convert datetime to isoformat in str
			json.dump(data_, file, indent = 4, default=self.convertDT2IsoFormat)

	def sendOutput(self, **kwargs):
		'''
		purpose: send output to stdout, file or both
		returns: None
		arguments: **kwargs
			output: output type stdout/file/both
			message: message to be redirectected to output type
			file: filename to which message to be written to, this option is only valid if output is either file or both
		'''
		try:
			if ("output" not in kwargs.keys() or "message" not in kwargs.keys()) or \
					 (kwargs["output"] in [self.outputStdoutNFile, self.outputFile] and \
					 	"file" not in kwargs.keys()):
				raise ValueError("missing arguments, usage: sendOutput(output = <stdout/file/both>, message = <your_message>, file = <file_name if output = both/file")
			
			if kwargs["output"] in [self.outputStdout, self.outputStdoutNFile]:
				print(kwargs["message"])
			
			if kwargs["output"] in [self.outputFile, self.outputStdoutNFile]:
				message = "".join([str(self.getCurTimeWODate()), "  - ", kwargs["message"]])			
				#print("writing to file", kwargs["file"])
				self.write2File(kwargs["file"], "".join([message,"\n"]) )

			return
		except Exception as error:
			print("error sending output >>> ", str(error))
			if "message" in kwargs:
				print(kwargs["message"])
			return

	def getAllFilesInAFolder(self, sourcePath):
		"""
		returns all files from a given folder
		"""
		if self.isDirExists(sourcePath):
			files = [file.name for file in os.scandir(sourcePath) if file.is_file() == True]
			return files

	def getTotalFilesInAFolder(self, sourcePath):
		"""
		Returns total # of files in a given directory
		"""
		if self.isDirExists(sourcePath):
			files = [file.name for file in os.scandir(sourcePath) if file.is_file() == True]
			return len(files)

	def getTotalDirInAFolder(self, sourcePath):
		"""
		Returns total # of files in a given directory
		"""
		if self.isDirExists(sourcePath):
			dirs = [file.name for file in os.scandir(sourcePath) if file.is_dir() == True]
			return len(dirs)

	def archiveFolder(self, sourcePath, destPath):
		"""
		archive source folder contents to destination folder
		"""
		#print("args >>>", sourcePath, destPath)
		try:
			if not sourcePath: return

			#for file in os.scandir(sourcePath):
			#	self.createDir(destPath)
			#	break

			if not self.isDirExists(destPath):
				self.createDir(destPath)

			for file in os.scandir(sourcePath):
				if file.is_file():
					self.moveFilesFromSrc2destn(self.buildPath(sourcePath, file.name), destPath)

		except Exception as error:
			raise error

	def copyFilesTo(self, sourcePath, destPath, filter_ = None):
		"""
		Copy files from source to destination (filter optional)
		"""
		self.createDir(destPath)
		for file in self.getAllFilesWPathFromPath(sourcePath, filter_):
			#print("file", file)
			# will copy files only
			if self.isFileExists(file):
				copy2(file, self.buildPath(destPath, self.getFileName(file)))

	def copyFilesFromSrc2destn(self, file, destPath):
		"""
		Copy files from source to destination
		"""
		self.createDir(destPath)
		copy2(file, self.buildPath(destPath, self.getFileName(file)))

	def moveFilesFromSrc2destn(self, file, destPath):
		"""
		Move files from source to destination
		"""
		if not self.isDirExists(destPath):
			self.createDir(destPath)

		#print("move files >", file, destPath)
		move(file, self.buildPath(destPath, self.getFileName(file)))

	def replFileNameExtn(self, fileName, newExtn):
		"""
		Return file name extn passed in argument with new extn. This does not change extn of a physical file
		"""
		return "".join([os.path.splitext(file)[0], nexExtn])
		
	def moveFiles2Target(self, source, target, fileExtn):
		"""
		Move files (given extension) from source to target
		"""
		if not destPath: 
			self.createDir(target)

		files = glob.iglob(self.buildPath(source,fileExtn))
		filesMoved = []
		for file in files:
			if self.isfile(file):
				# redirecting output to a var
				filesMoved.append(move(file, target))
		# returning files moved
		return filesMoved

	def getFileDirName(self, filePath):
		return os.path.dirname(filePath)

	def getFileName(self, filePath):
		return os.path.basename(filePath)

	def isDirExists(self, path):
		return os.path.isdir(path)

	def isFileExists(self, fileName):
		return os.path.isfile(fileName)

	def isDirEmpty(self, path):
		if not self.isDirExists(path): return False

		dirContents = os.listdir(path)
		if len(dirContents) == 0:
			return True
		else:
			return False

	def getAllFiles(self, path, extn = "*"):
		"""
		Returns all files from a given path and filter using extn
			e.g. : glob.glob('/tmp/*.log'), glob.glob('/tmp/*.sql'), glob.glob('/tmp/*')
		"""
		if "*" not in extn:
			extn = "".join(["*",extn])

		return [file for file in glob.glob(self.buildPath(path,extn))]

	def getAllDir(self, path):
		"""
		Returns all files from a given path and filter using extn
			e.g. : glob.glob('/tmp/*.log'), glob.glob('/tmp/*.sql'), glob.glob('/tmp/*')
		"""
		return [dir for dir in os.lisdir(path) if self.isDirExists(dir)]

	def getAllDirFilesRecur(self, path):
		"""
		Returns all directory and files recursively for a given path
			tuple (dirpath, dirnames (list), filenames (list))
		"""
		return os.walk(path)

	def getFileModDateTime(self, fileName):
		return datetime.datetime.fromtimestamp(os.stat(fileName).st_mtime)

	def getFileOwnerGidUid(self, fileName):
		myFileGroupId = os.stat(fileName).st_gid
		myFileUserId = os.stat(fileName).st_uid
		return myFileGroupId, myFileUserId

	def getGroupDetails4Gid(self, gid):
		return grp.getgrgid(gid)

	def getGroupDetails4GrpName(self, grpName):
		return grp.getgrnam(grpName)

	def getUserDetails4Uid(self, uid):
		return pwd.getpwuid(uid)

	def getUserDetails4UserNae(self, userName):
		return grp.getpwnam(userName)

	def getFileStats(self, fileName):
		"""
		Returns file metadata stats (creation/modification/access time & size in bytes)
		"""
		fileStat = os.stat(fileName)
		return {
			"file" : fileName,
			"create_time" : datetime.datetime.fromtimestamp(fileStat.st_ctime),
			"modify_time" : datetime.datetime.fromtimestamp(fileStat.st_mtime),
			"access_time" : datetime.datetime.fromtimestamp(fileStat.st_atime),
			"size_bytes" : fileStat.st_size
		}

	def changeFileOnwerShipById(self, fileName, gid, uid):
		os.chown(fileName, uid, gid)

	def getFileSizeBytes(self, fileName):
		"""
		Returns file size in bytes
		"""
		return self.getFileStats(fileName)["size_bytes"]

	def isFileChanged(self, origFileStat, fileName):
		"""
		Returns if current file has been changed, need older file metadata stats
		"""
		myCurrFileStats = self.getFileStats(fileName)

		return False if origFileStat["modify_time"] == myCurrFileStats["modify_time"] else True

		return False if origFileStat["size_bytes"] == myCurrFileStats["size_bytes"] else True

	def isFileModifiedToday(self, file):
		"""
		checks if file was last modified today, returns True, else False
		"""
		modDtTime = self.removeTimeFromDate(self.getFileModDateTime(file))
		curDtTime = self.getCurrentDate()

		return (modDtTime == curDtTime)

	def getAllFilesWPathFromPath(self, path_, filter_ = []):
		# returns all files (exclude dir) from a dir with path built in, applying filter if provided to include those files only
		# filter must be specified in array. For e.g. ["sql","json","bson"]
		from stat import S_ISREG

		myAllFiles = os.listdir(path_)
		myAllFilesFinal = []
		#myAllFiles = []

		"""
		# lets remove dir from all files
		for idx, file in enumerate(myAllFiles):
			mode = os.stat(v).st_mode
			if S_ISREG(mode):
				myAllFiles.append()
				print("file")
			if S_ISDIR(mode):
			print("dir")

			if os.stat(file).st_mode == S_ISDIR
		"""

		for file in myAllFiles:
			myFile = self.buildPath(path_, file)

			if not S_ISREG(os.stat(myFile).st_mode): # if mode is not 33152 (file), skip
				continue

			if filter_ :
				#print("file", myFile)
				myFileExtn = self.getFileExtn(myFile)

				#print("extn", myFileExtn, filter_)
				if not(myFileExtn in filter_):
					continue

				myAllFilesFinal.append(myFile)
				#print("final >", myAllFilesFinal)
			else:
				myAllFilesFinal.append(myFile) 

		#print("final files >>>", myAllFilesFinal)
		return myAllFilesFinal

	def splitFileAndExtn(self, fileName):
		"""
		Returns tuple with 2 value (filename wo extn and its extn) ('<file_name>','<extn>')
		"""
		return os.path.splitext(fileName)

	def buildPath(self, *pathArg):
		return os.path.join(*pathArg)

	def getCurrentDir(self):
		return os.getcwd()

	def createDir(self, path):
		myPath = Path(path)
		myPath.mkdir(parents=True, exist_ok=True)		

	def deleteDir(self, path):
		if self.isDirExists(path): rmtree(path)		

	def renameFile(self, fileName, newFileName):
		#print(fileName)
		if self.isFileExists(fileName):
			#print("removing ",fileName)
			os.rename(fileName, newFileName)

	def deleteFile(self, fileName):
		#print(fileName)
		if self.isFileExists(fileName):
			#print("removing ",fileName)
			os.remove(fileName)

	def convToInteger(self, int_):
		"""
		Convert passed argument to integer
		"""
		try:
			return int(int_)
		except Exception as error:
			raise error

	def deleteFilesOlderThanDays(self, path, fileExtn, retentionDays):
		"""
		Delete files older than retention days 
		"""
		filesDeleted = []
		myCurrentDateTime = self.lambdaGetCurrDateTime()
		if not self.isDirExists(path):
			return filesDeleted

		myRetentionDays = self.convToInteger(retentionDays)

		for file in self.getAllFiles(path, fileExtn):
			#print("checking file")
			if self.diffBetweenDatesInDays(self.getFileModDateTime(file), myCurrentDateTime) > myRetentionDays:
				print(f"deleting file {file}, last modified time is > {myRetentionDays}")
				self.deleteFile(file)
				filesDeleted.append(file)
	
		return filesDeleted

	def buildDeployLogFile(self, path, deployDoc, env):
		'''
		purpose: build logfile for deployDoc
		returns: file name as string(change order, env, and current timestamp i.e. /<path>/co#_<env>_<datetime>)
		'''
		return self.buildPath(path, ''.join(['deploy_', str(deployDoc), '_', env, str(self.getCurDateTimeForDir()), '.log']))

	# environment function

	def getAllEnv(self):
		return os.environ

	def getEnvKeyVal(self, key):
		#print("key in getEnvKeyVal", key)
		return os.getenv(key)

	def setEnvKeyVal(self, key, value):
		os.environ[key] = value
		return

	#def getPrevEnv(self, env):
	#	return self.Globals.envMapping[env]

	# process functions
	def getCurrentPID(self):
		return os.getpid()

	def getAllPID(self):
		return psutil.pids()

	def getParentPID(self):
		return psutil.Process(os.getpid()).ppid()

	def isPidAlive(self, processId):
		return psutil.pid_exists(int(processId))

	def getCurrentProcDetail(self):
		# return tuples (pid, name, started)
		return psutil.Process(os.getpid())

	"""
	def execOSCmdRetCode(self, osCmd):
		#print(osCmd)
		retval = subprocess.call(osCmd, shell=True, stdout=subprocess.PIPE, stderr=open(os.devnull, 'w'))
		return retval
	"""
	def execOSCmdRetCode(self, osCmd):
		#print(osCmd)
		"""
		data = subprocess.run(["/bin/adquery", "group", "-s", "#Hyperion BI Custom Group2"],stdout=subprocess.PIPE, universal_newlines=True)
		data.stdout
			'christopher-smith@CORP.MMCO.INT\nDeborah-Tetlow@CORP.MMCO.INT\nJoe-Unger@CORP.MMCO.INT\nlisa-reid@CORP.MMCO.INT\nJREINH00@CORP.MMCO.INT\nMary-Lem@CORP.MMCO.INT\ngpratt02@CORP.MMCO.INT\ngwebb01@CORP.MMCO.INT\npharve07@CORP.MMCO.INT\nScott-Myszka@CORP.MMCO.INT\nnfrenc02@CORP.MMCO.INT\n'
		data.returncode
		"""
		retval = subprocess.call(osCmd, shell=True, stdout=subprocess.PIPE, stderr=open(os.devnull, 'w'))
		return retval

	'''
	def execOSCmd(self, osCmd):
		retval = subprocess.call(osCmd, shell=True, stdout=subprocess.PIPE)
		return retval

	def execOSCmdRetCode(self, osCmd):
		retval = subprocess.call(osCmd, shell=True, stdout=subprocess.PIPE)
		return retval
	'''
	def execOSCmdRetResult(self, osCmd):
		#print('os >>>', osCmd)
		processHandle = subprocess.Popen(osCmd, shell=True, stdout=subprocess.PIPE)
		result = processHandle.communicate()
		# result is tuple, 1st value is data and 2nd value is error
		return result

	def fetchDataFromOsCmdResult(self, osCmdResult):
		"""
		will return array, osCmdResult must be type of tuple
		"""
		myDataResult = osCmdResult[:1]
		myError = osCmdResult[1:]
		if isinstance(myDataResult, tuple):
			myRawData = myDataResult[0]

			if isinstance(myRawData, bytes):
				myStrData = myRawData.decode('utf-8')
			else:
				myStrData = myRawData

			'''
			if myStrData.endswith("\n"):
				myData = myStrData[:-1].split("\n") 
			else:
				myData = myStrData.split("\n")
			'''

			return myStrData.splitlines()
			
	def getLinuxPidPath(self, pid):
		"""
		Linux only:
		return the path of pid form where its being executed, this is needed when a process does not have full path
		For e.g. 
			1. if "mongod" process is spawn directly from mongod bin location, ps -ef would not return path of mongod  
		"""
		try:
			myPidPathRetreiveCmd = "/bin/readlink -f /proc/{pid}/exe"
			myPidExecFile = self.fetchDataFromOsCmdResult(self.execOSCmdRetResult(myPidPathRetreiveCmd.format(pid = pid)))
			# we have got an array, if we have value we would need 1st element
			if myPidExecFile:
				myPidExecFile = myPidExecFile[0]
			myPidPath = self.getFileDirName(myPidExecFile)
			return myPidPath
		except Exception as error:
			raise error

	# os details functions
	def getOsDetails(self):
		try:
			loginUser = os.getlogin()
		except Exception as error:
			loginUser = getpass.getuser() 
			# this would happen when process is spawen by systemd or threading, following is excerpt from Christian Heimes (christian.heimes)
			"""
			msg383161 - (view)	Author: Christian Heimes (christian.heimes) * (Python committer)	Date: 2020-12-16 12:32
			errno 6 is ENXIO. According to https://www.man7.org/linux/man-pages/man3/getlogin.3.html the error code means "The calling process has no controlling terminal.".

			os.getlogin() returns the name of the user logged in on the controlling terminal of the process. Typically processes in user session (tty, X session) have a controlling terminal. Processes spawned by a service manager like init, systemd, or upstart usually do not have a controlling terminal. You have to get the user information by other means. Our documentation for os.getlogin() recommends getpass.getuser().
			"""

		return {
			'node' : platform.node(),
			'os' : platform.system(),
			'cpu_count' : os.cpu_count(),
			'phys_memory' : psutil.virtual_memory(), # this is tuple
			'swap_memory' : psutil.swap_memory(), # this is tuple
			'processor' : platform.machine(),
			'login_id' : loginUser
		}

	def getNetworkAddress(self):
		return psutil.net_if_addrs()

	def getNetworkStats(self):
		return psutil.net_if_stats()

	def getCpuUtilization(self):
		return psutil.cpu_percent()

	def getDiskUtilization(self, disk):
		diskUsageRawTuple = psutil.disk_usage(disk)
		diskUsage = {
			"toal" : diskUsageRawTuple.toal, 
			"used" : diskUsageRawTuple.used,
			"free" : diskUsageRawTuple.free,
			"percent" : diskUsageRawTuple.percent}
		return

	# variable dict/list functions
	def sortDictInListByKey(self, dataList, keyInDict, reverse=False):
		'''
		purpose: sort dict stored in list by a given key
		arguments: 
			dataList : List - dict stored in array
			keyInDict: String - Key in dict which will be used for sorting
			reverse : Boolean - Reverse sorting Order (default False) 
		e.g.
			sortDictInListByKey(<dict stored in list>, "key", False)
		'''
		return sorted(dataList, key = lambda key: key[keyInDict], reverse = reverse)


	def cmp(self, x, y):
		"""
		Replacement for built-in function cmp that was removed in Python 3

		Compare the two objects x and y and return an integer according to
		the outcome. The return value is negative if x < y, zero if x == y
		and strictly positive if x > y.

		https://portingguide.readthedocs.io/en/latest/comparisons.html#the-cmp-function
		"""

		return (x > y) - (x < y)

	def sortDictInListByMultiKey(self, items, columns):
		"""
		sort on multiple keys in dict of list
		"""
		from operator import itemgetter as i
		from functools import cmp_to_key

		comparers = [
			((i(col[1:].strip()), -1) if col.startswith('-') else (i(col.strip()), 1))
			for col in columns
		]

		def comparer(left, right):
			comparer_iter = (
				self.cmp(fn(left), fn(right)) * mult for fn, mult in comparers
			)
			return next((result for result in comparer_iter if result), 0)
		return sorted(items, key=cmp_to_key(comparer))

	def removeDuplicateFromList(self, listArg):
		"""
		remove duplicate value from list/array
		"""
		myListarg = self.getACopy(listArg)
		return list(set(myListarg))

	def removeDuplicateFromListOfDic(self, listOfDict):
		"""
		remove duplicate value from list/array
		"""
		return [val for idx, val in enumerate(listOfDict) if val not in listOfDict[idx + 1:]]

	def getUniqueKeyValFromDictInList(self, listArg, key):
		"""
		Returns distinct value of a key stored in List.
		Arguments: 
			listArg : Dict stored in List
			Key : Key from dict which would need distinct/unique value 
		For e.g.
			getUniqueKeyValFromDictInList([{"status" : "Success"},{"status" : "Success"},{"status" : "Success"},{"status" : "UnSuccess"}])
			will return List ['UnSuccess', 'Success']
		"""
		return list(set([elem[key] for elem in listArg]))

	def convertTupleInListToDictinList(self, tupleListArg):
		myData = []
		for tuple in tupleListArg:
			myData.append(dict([(tuple)]))
		return myData

	def removeListItem(self, listArg, value):
		"""
		remove a value from list, will not throw error if value is not present
		Arguments: 
			listArg : List/Array
			value: value need to be removed
		For e.g.: remove 'sales' from item array
			removeListItem(['sales','finance'], 'sales')
		"""
		try:
			listArg.remove(value)
		except:
			pass

	def getDictRecursiveItems(self, dict_):
		"""
		Returns tuple for a given nested dictionary
		For mongod conig, it will return ..
			('auditLog', {'destination': 'file', 'filter': '{ atype: { $in: [ "authenticate","createDatabase","dropDatabase","createUser","dropCollection", "dropUser","dropAllUsersFromDatabase","updateUser","grantRolesToUser","createRole","updateRole","dropRole","dropAllRolesFromDatabase","grantRolesToRole","revokeRolesFromRole","grantPrivilegesToRole","shutdown" ] } }', 'format': 'BSON', 'path': '/var/mongo/logs/LIS/audit/auditLog_QA1.bson'})
			('destination', 'file')

		"""
		for key, value in dict_.items():
			if type(value) is dict:
				yield (key, value)
				yield from recursive_items(value)
			else:
				yield (key, value)

	def flattenDict(self,dict_,parent_key="",sep="."):
		"""
		Flattens nested dictioary to a given seperator
		For e.g.
			{"a":{"b":{"c":2}}} output ==> {"a.b.c" : 2}
		"""
		from collections import MutableMapping
		items = [] 
		for k, v in dict_.items():
			new_key = parent_key + sep + k if parent_key else k 

			if isinstance(v, MutableMapping): 
				items.extend(self.flattenDict(v, new_key, sep = sep).items()) 
			else: 
				items.append((new_key, v)) 
		return dict(items)

	def convertToString(self, value_):
		"""
		Converts to string 
		"""
		if isinstance(value_, bytes):
			return value_.decode("utf-8")
		else:
			return str(value_)

	def removeNonNumFromStr(self, string_):
		"""
		Removes all non numeric character from passed string, this is helpful when a string need to be converted to int and all non num character
		to be ignored
		"""
		import re
		return re.sub(r"[^0-9]+","",string_)
		
	def removeNumFromString(self, string_):
		"""
		Remoces all numeric character from string
		"""
		import re
		return re.sub(r"[0-9]+","",string_)

	def splitStrWMultipleDelimiters(self, string_, delimiterList):
		"""
		Split string with multiple delimiters passed
		"""
		return [elem.strip() for elem in re.split("|".join(delimiterList), string_) if elem]

	def convertToInt(self, value_):
		"""
		Converts to integer
		"""
		try:
			myValue = int(value_)
			return myValue
		except Exception as error:
			return value_

	def getPartialStrInList(self, partialString, listArg):
		# returns index of a given partial string found in list
		return [listArg.index(i) for i in listArg if partialString.lower() in i.lower()]

	def getKeyFromDict(self, dictData):
		return list(dictData.keys())

	def getDictKeyValue(self, dictData, key):
		try:
			return dictData[key]
		except Exception as error:
			return None

	def delKeysFromDict(self, dictData, key):
		"""
		*** Should not use this, rather use removeKeysFromDict
		deletes a key from dict
		"""
		result = dictData.pop(key, None)
		return result

	def removeKeysFromDict(self, dictArg, keyList):
		"""
		remove keys from dict using dict comprehension
		"""
		return {key: dictArg[key] for key in dictArg if key not in keyList }

	def delElemFromList(self, listData, elemValue):
		try:
			listData.remove(elemValue)
		except Exception as error:
			# suppressing error, this could happend if givn elem is not in list
			return 

	def isListItemExistsInAList(self, sourceList, targetList):
		"""
		checks if all source item present in target list
		"""
		return all(elem in targetList for elem in sourceList)

	def isAnyElemInListExistsInAList(self, sourceList, targetList):
		"""
		checks if all source item present in target list
		"""
		return any(elem in targetList for elem in sourceList)

	def valArguments2(self, dictArgInList, optionalArgList):
		"""
		Validates argument, checks for argument data type and its value (if mandatory (not provided in optinoal arg list))
		e.g.

			valArguments2([
				{'arg' : 'opco', 'type', str, 'value' : 'marsh'},
				{'arg' : 'serverCnt', 'type' : int, 'value' : '123},
				['location'])

			will raise error because argument 'serverCnt' is not a valid integer

		"""
		## checking for arg values
		try:
			myEmptyArgList = [arg['arg'] for arg in dictArgInList if not arg['value'] and arg['arg'] not in optionalArgList and arg]

			if myEmptyArgList:
				raise ValueError("expecting a not null value, got Null for arguments >>> {arg}".format(arg = str(myEmptyArgList)))

			# checking for argument data type
			# this code is used when dictArgInList is passed as [{'argValue' : dataType}] 
			#myInvalidDataType = [ {list(elem.keys())[0] : ''.join(['expecting ', list(elem.values())[0]]) } for elem in dictInListArg if not isinstance( list(elem.keys())[0], list(elem.values())[0] ) ]

			myInvalidDataType = [ ''.join(['expecting arg [', elem['arg'], '] ', str(elem['type']), ', got ', str(type(elem['value'])), ' value > ', repr(elem['value']) ]) for elem in dictArgInList if not isinstance( elem['value'], elem['type'] ) ]

			if myInvalidDataType:
				raise ValueError("Invalid argument data type >>> {arg}".format(arg = list(myInvalidDataType)))

		except Exception as error:
			raise error

	def isDictKeyValueExistsInList(self, argList, key, value):
		for elem in argList:
			if key in elem and elem[key] == value:
				return True
		return False

	#response

	def buildResponse(self, status, message = None, data = None):

		myResponse = self.getACopy(self.Globals.template['response'])
		myResponse['status'] = status
		if message: myResponse['message'] = message

		if data:
			myResponse['data'] = data
		else:
			myResponse['data'] = ""

		return myResponse

	def getNonEmptyKeyFromDict(self, argDict):
		return dict([ (key,value) for key, value in argDict.items() if (value) ])

	def valArguments(self, requiredArgLists, userArgsDict, ignoreArgLists = []):
		'''
		argLists : required argument in array
		userArgDict : passed arguments which need to be validated as dict
		ignoreArgList: Optional argument which need to be skipped for validation
		'''
		if not (isinstance(requiredArgLists, list) or isinstance(userArgsDict, dict) or (not ignoreArgLists and isinstance(ignoreArgLists, list)) ):
			raise ValueError("Invalid arguments !!!")
			sys.exit(-1)

		# gathering keys from userArgDict and removing ignoreArgLists from argLists and newlist built from userArgDict
		#myNewUserArgLists = list(self.getNonEmptyKeyFromDict(userArgsDict).keys())
		myUserArgLists = list(set(list(userArgsDict.keys())) - set(ignoreArgLists))
		myRequiredArgLsts = list(set(requiredArgLists) - set(ignoreArgLists))
		#print('user args >>> ',myNewUserArgLists)
		
		#print('final >>>', myFinalUSerArgLists, argLists)

		#myMissingArgLists = list(set(argLists) - set(myNewUserArgLists))
		myMissingArgLists = list(set(myRequiredArgLsts) - set(myUserArgLists))

		if myMissingArgLists:
			raise ValueError("Missing arguments {missing}".format(missing = str(myMissingArgLists)))

	# time
	def sleep(self, seconds):
		time.sleep(seconds)
		return

	def getStartTimeSecs(self): 
		return time.time()
	
	def getElapsedTimeSecs(self, startTime):
		'''
		startTime : this argument can be time.time object or datetime.datetime class
		'''
		#print("startTime type >>>" , str(type(startTime)))
		if isinstance(startTime, datetime.datetime):
			totalElapsed = (datetime.datetime.now() - startTime)
			return totalElapsed.total_seconds()
		else:
			return time.time() - startTime
	
	def getElapsedTime(self, startTime):
		'''
		startTime : this argument can be time.time object or datetime.datetime class
		'''
		if isinstance(startTime, datetime.datetime):
			totalElapsed = (datetime.datetime.now() - startTime)
			myElapsedSec = totalElapsed.total_seconds()
		else:
			myElapsedSec = time.time() - startTime

		return time.strftime("%H:%M:%S", time.gmtime(myElapsedSec))

	def formatElapsedTime(self, elapsed):
		#return '{:02d}:{:02d}:{:02d}'.format(elapsed // 3600, (elapsed % 3600 // 60), elapsed % 60)
		return time.strftime("%H:%M:%S", time.gmtime(elapsed))

	def isDate(self, var_):
		if isinstance(var_, datetime.datetime):
			return True
		elif isinstance(var_, datetime.date):
			return True
		else:
			return False

	def isInt(self, var_):
		return isinstance(var_, int)

	def isStr(self, var_):
		return isinstance(var_, str)

	def isBool(self, var_):
		return isinstance(var_, bool)

	def replCharFromDictKeys(self, dict_, char_, tochar_):
		newDict = {}
		for key, value in dict_.items():
			if isinstance(value, dict):
				value = self.replCharFromDictKeys(value, char_, tochar_)
			newDict[key.replace(char_, tochar_)] = value
		return newDict

	def replCharInDictValues(self, dict_, char_, tochar_):
		for key, value in dict_.items():
			if isinstance(value, dict) and value:
				value = replCharInDictValues(value, char_, tochar_)
			#print(key,value, type(key), type(value))
			if isinstance(value, str):
				dict_[key] = value.replace(char_, tochar_)
			#print("new dict >>>" ,dict_)
		return dict_

	def escapeValueInDict(self, dict_, char_):
		newDict = {}
		for key, value in dict_.items():
			if isinstance(value, dict):
				value = self.escapeStringInDict(value, char_)
			if isinstance(value, str):
				value = self.escapeStringChar(value)
			newDict[key] = value
		return newDict

	def escapeStringChar(self, string_):
		if isinstance(string_, str):
			return "".join(["\\", "\"", str_, "\\"])

	def formatElapsedSecs(self, elapsedSeconds):
		return time.strftime("%H:%M:%S", time.gmtime(elapsedSeconds))

	def getCurDateTimeForDir(self):
		return ''.join([str(datetime.datetime.now().month).zfill(2), str(datetime.datetime.now().day).zfill(2), str(datetime.datetime.now().year),'_',str(datetime.datetime.now().hour).zfill(2),str(datetime.datetime.now().minute).zfill(2), str(datetime.datetime.now().second).zfill(2) ])
	
	def convertStrDate2DateTime(self, dateStr, dateStrFormat):
		return datetime.datetime.strptime(dateStr, dateStrFormat)	

	def convertEpocToDateTime(self, epochTime):
		return datetime.datetime.fromtimestamp(epochTime)

	def convertDate2Str(self, dateArg, strFormat):
		return dateArg.strftime(strFormat)

	def isNowBetweenDates(self, startDateTime, endDateTime):

		currentDateTime = datetime.datetime.now()
		return startDateTime <= currentDateTime <= endDateTime

	def getCurDateTimeFormat(self, timeFormat):
		return datetime.datetime.now().strftime(timeFormat)

	def getCurTimeWODate(self):
		return self.getCurDateTimeFormat("%H:%M:%S")

	#def getDictSize(self, objDict):
	#	return sys.getsozeof(cPickle.dumps(objDict))
	
	#def getListSize(self, objlist): 
	#	return sys.getsozeof(cPickle.dumps(objList))
	
	def getACopy(self, objVar):
		#return deepcopy(objVar)
		import copy
		return copy.copy(objVar)

	def getStringQuote (self, userString): 
		return quote_plus(userString)

	def getDiskFreeSpace(self, disk):
		pass

	# user name, password

	#Mongo utility
	def formatHosts4MongoUri(self, hostPortList, instType = "standAlone", instName = None):
		'''
		Args: host, port information in dict passed as an array
				i.e. [{host:<>,port:<>},{....}]
		Return: returns all host and port concatenated by ':' seperated by ','. This is useful in building uri
		'''
		try:

			myModuleName = sys._getframe().f_code.co_name

			#self.LOGGER.info("got argument(s) {args}".format(args = hostPortList))

			if not isinstance(hostPortList, list):
				raise InvalidArguments("expecting arguments hostPortList as array, got {got}".format(got = type(hostPortList)))

			myHosts = ''
			for hostPort in hostPortList:
				if not isinstance(hostPort, dict):
					raise InvalidArguments("expecting arguments hostPortList as array, got {got}".format(got = type(hostPortList)))
				myHosts = ','.join([myHosts,hostPort['host'] + ':' +  str(hostPort['port'])])

			myHost = myHosts[1:]

			#if instType == "replicaSet":
			#	myHost = "".join([instName, "/", myHost])
			#elif instType == "shard":
			#	pass

			return myHost

		except Exception as error:
			#self.LOGGER.error("error [{error}] occurred ", exc_info = True)
			raise error

	def postRestApi(self, url, jsonData_):
		"""
		Call REST API using post, would return text/json
		conevrt curl to Python syntax
		https://curl.trillworks.com/
		"""
		try:
			"""
			response.apparent_encoding      response.encoding               response.iter_lines(            response.raw
			response.close(                 response.headers                response.json(                  response.reason
			response.connection             response.history                response.links                  response.request
			response.content                response.is_permanent_redirect  response.next                   response.status_code
			response.cookies                response.is_redirect            response.ok                     response.text
			response.elapsed                response.iter_content(          response.raise_for_status(      response.url
			"""

			#if not isinstance(data_, json):
			#	raise ValueError("")

			from requests import post, utils
			myHeaders = utils.default_headers()
			myHeaders = {'Content-Type': 'application/json', 'User-Agent': 'Python Rest API'}
			#import eventlet
			#eventlet.monkey_patch()
			#try:
			#	with eventlet.Timeout(30):
			myResponse = post(url, headers=myHeaders, json=jsonData_)
			#except Exception as error:
			#	raise error

			#print(f"response from post for {jsonData_}>>>", myResponse)

			if myResponse.ok: # status is 200
				#myResponseData = json.loads(myResponse.contents)
				myResponseData = myResponse.json()
				#print("response after josn conversion >>>", myResponseData)
				myResponseData.update({
					"elapsed" : "".join([str(myResponse.elapsed.total_seconds()), "seconds "]),
					"statusCode" : myResponse.status_code,
					"data" : str(myResponseData["data"]) if not myResponseData["data"] else myResponseData["data"]
				})
				#print("response after updating statistics >>>", myResponseData)
				return myResponseData
			else:
				myResponse.raise_for_status()

		except Exception as error:
			print("error", str(error))
			raise error

	def getRestApiWAuth(self, url, userName, userPass_,  params_ = {}, authType = None):
		"""
		Call REST API using get with auth, would return json
		Params:
			url: url 
			userName : username for auth
			userPass_ : password or apikey (for digest only)
			authType : digest/basic
		"""
		try:

			from requests import get
			from requests.auth import HTTPBasicAuth, HTTPDigestAuth

			if authType and authType == "digest":
				myAuth = HTTPDigestAuth(userName, userPass_)
			else:
				myAuth = HTTPBasicAuth(userName, userPass_)

			myHeaders = {
				'Accept': 'application/json',
				'Content-Type': 'application/json'
			}
			
			myResponse = get(url, headers=myHeaders, auth = myAuth, params = params_)

			myResponseURL = myResponse.url
			#print(f"response from post for {jsonData}>>>", myResponse)

			if myResponse.ok: # status is 200
				#myResponseData = json.loads(myResponse.contents)
				myResponseData = myResponse.json()
				#print("response after josn conversion >>>", myResponseData)
				myResponseData.update({
					"url" : myResponseURL,
					"elapsed" : "".join([str(myResponse.elapsed.total_seconds()), "seconds "]),
					"statusCode" : myResponse.status_code #,
					#"data" : str(myResponseData) if not myResponseData else myResponseData
				})
				#print("response after updating statistics >>>", myResponseData)
				return myResponseData
			else:
				myResponse.raise_for_status()

		except Exception as error:
			print("error", str(error))
			raise error

	# upload/download to Nexus (better to use native lib which would need port to be open)
	def downloadFileFromUrl(self, url_, fileName_, userid_, userPass_):
		from requests import get
		try:
			# will pass the filename without path (getFileName will remove path)
			myUrl = "".join([url_,self.getFileName(fileName_)]) 
			response = get(myUrl, auth = (userid_,userPass_))
			#raising error for status code 4XXX or 5XXX
			response.raise_for_status()
			return response
		except Exception as error:
			if "response" in locals():
				for elem in response.headers:
					print(elem)
			raise error

	def uploadFileToUrl(self, url_, fileName_, userId_, userPass_):
		from requests import put
		try:
			'''
			import requests
			files = {'file': open('yourfile.rpm', 'rb')}
			response = requests.post('http://nexusURL/repository/yumRepo/yourfile.rpm', files=files, auth=('username', 'password'))
			>>> auth = ('admin','admin123')
			>>> url="
			http://nam.marshnexus.mrshmc.com/repository/Onprem_Prod_RAW_Hosted_Repo/"
			http://nam.marshnexus.mrshmc.com/repository/Onprem_Prod_RAW_Hosted_Repo/23123213_deploy.json
			http://nam.marshnexus.mrshmc.com/repository/Onprem_Prod_RAW_Hosted_Repo/23123213_deploy.json
			>>> path="/opt/ansible/deploy/staging/JIRA3453EF32S/dev/23123213/23123213_deploy.json"
			>>> content=open(path,'rb').read()
			>>> content
			b'{"jiraKey": "F234W24S45111", "changeOrder": "PROD-CO-10000001", "description": "test deployment",...'
			>>> import requests
			>>> resp = requests.put(url+"23123213_deploy.json",data=content, auth=auth)
			>>> resp
			<Response [201]>

			'''
			#myFile = {'file' : open(fileName_,'rb')}
			myUrl = self.buildPath(url_, self.getFileName(fileName_))

			myContents = open(fileName_,'rb').read()

			response = put(myUrl, data = myContents, auth = (userId_,userPass_))
			#raising error for status code 4XXX or 5XXX
			response.raise_for_status()
			return response
		except Exception as error:
			if "response" in locals():
				for elem in response.headers:
				  print(elem)
			raise error

	def downloadAllJiraAttachments(self, baseUrl, jiraIssueKey, targetLoc, userId_, userPass_, filter_ = []):
		"""
			filter_ argumemtn must be passed as an array
		"""
		try:
			# 
			jira = JIRA(auth=(userId_,userPass_), options={'server': baseUrl})
			jira_issue = jira.issue(jiraIssueKey, expand="attachment")

			for attachment in  jira_issue.fields.attachment  :    
				image = attachment.get()  
				jiraFileName = attachment.filename

				# will create target location if it doesnt exists
				if not(self.isDirExists(targetLoc)):
					self.createDir(targetLoc)

				# aplying filter (download files with extention as passed in filter_ array) if passed as an argument
				if filter_ :
					myJiraFileExtn = self.getFileExtn(jiraFileName)
					if not(myJiraFileExtn in filter_):
						continue

				#with open(jiraFileName, 'wb') as f:
				#	f.write(image)

				# adding target location path to file name
				myDownloadFileWPath = self.buildPath(targetLoc, jiraFileName)

				with open(myDownloadFileWPath, 'wb') as f:
					#if there is a space in the filename (attachment.get() crashes in this case)
					if " " in myDownloadFileWPath:
						for chunk in attachment.iter_content(chunk_size=512):
							if chunk: # filter out keep-alive new chunk
								f.write(chunk)
					else:
						#Getting the file from the jira server and writing it to the current directory
						image = attachment.get()
						f.write(image)
		except Exception as error:
			raise error

	def downloadJiraAttachment(self, baseUrl, jiraIssueKey, targetLoc, userId_, userPass_, fileName):
		#https://community.atlassian.com/t5/Jira-questions/Downloading-attachments-via-jira-module-in-python/qaq-p/449195
		"""
			filter_ argumemtn must be passed as an array
		"""
		try:
			# 
			jira = JIRA(auth=(userId_,userPass_), options={'server': baseUrl})
			jira_issue = jira.issue(jiraIssueKey, expand="attachment")

			for attachment in  jira_issue.fields.attachment  :    
				image = attachment.get()  
				jiraFileName = attachment.filename

				# will download file passed in argument only, ignore rest of them
				if not(fileName == jiraFileName):
					continue

				# adding target location path to file name
				myDownLoadFileWPath = self.buildPath(targetLoc, jiraFileName)

				with open(myDownLoadFileWPath, 'wb') as f:
					#if there is a space in the filename (attachment.get() crashes in this case)
					if " " in myDownLoadFileWPath:
						for chunk in attachment.iter_content(chunk_size=512):
							if chunk: # filter out keep-alive new chunk
								f.write(chunk)
					else:
						#Getting the file from the jira server and writing it to the current directory
						image = attachment.get()
						f.write(image)
		except Exception as error:
			raise error

	def addAttachment2JiraIssue(self, jiraBaseUrl, jiraKey, userId_, userPass_, fileName):
		try:
			from jira.client import JIRA
			from jira.client import JIRA

			jira = JIRA(basic_auth=(userId_, userPass_), options={'server': jiraBaseUrl})
			issue = jira.issue(jiraKey)
			file = open(fileName, 'rb')
			attachment_object = jira.add_attachment(issue,file)

		except Exception as error:
			raise

	# socket
	def isPortOpen(self, host, port):
		with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
			sock.settimeout(1)
			try:
				result = sock.connect_ex((host.strip(), int(port)))
				if result == 0:
					#print(f"{host}, {port}, Open")
					return True
				else:
					#print(f"{host}, {port}, Not Open")
					return False
			except Exception as error:
				# got an error, will remove domain name if that seems to be an issue
				# removing domain name from host
				if host.split('.')[-1].isalpha():
					myHost = re.sub("\..*", "",host)
					if sock.connect_ex((myHost, int(port))) == 0:
						return True
					else:
						return False
				else:
					# we encountered an error
					return False

	# os/system
	def getMemoryUsedByMe(self):
		pid = os.getpid()
		py = psutil.Process(pid)
		memoryUse = py.memory_info()[0]/2.**30  # memory use in GB...I think
		return {'memory used:', memoryUse}

	def convBytes2HumanReadable(self, bytes):
		"""
		Convert bytes to human readable format
		"""
		from psutil._common import bytes2human
		return bytes2human(bytes)

	def getNicDetails(self):
		"""
		Rturns Nic address, stats and ip counters 
		"""
		from psutil._common import bytes2human
		stats = psutil.net_if_stats()
		ioCounters = psutil.net_io_counters(pernic=True)
		af_map = {
			socket.AF_INET: 'IPv4',
			socket.AF_INET6: 'IPv6',
			psutil.AF_LINK: 'MAC',
		}

		duplex_map = {
			psutil.NIC_DUPLEX_FULL: "full",
			psutil.NIC_DUPLEX_HALF: "half",
			psutil.NIC_DUPLEX_UNKNOWN: "?",
		}
		myAllNicDetails = []
		for nic, addrs in psutil.net_if_addrs().items():
			if nic in stats:
				st = stats[nic]
				mygetNicDetails = {"speed" : st.speed, "duplex" : duplex_map[st.duplex], "mtu" : st.mtu, "up" : "yes" if st.isup else "no"}
			else:
				mygetNicDetails = {}
			if nic in ioCounters:
				io = ioCounters[nic]        
				myNicIOCntrs = {
					"incoming" : {
						"bytesRaw" : io.bytes_recv, 
						"bytes" : bytes2human(io.bytes_recv), 
						"packets" : io.packets_recv, 
						"errs" : io.errin, 
						"drops" : io.dropin
					}
				}
				myNicIOCntrs.update( 
					{
						"outgoing" : {
						"bytesRaw" : io.bytes_sent, 
						"bytes" : bytes2human(io.bytes_sent), 
						"packets" : io.packets_sent, 
						"errs" : io.errout, 
						"drops" : io.dropout
					}
				})

			myAllNicAddress = []
			for addr in addrs:
				myNicAddress = {"addressType" : af_map.get(addr.family, addr.family), "address" : addr.address}
				if addr.broadcast:
					myNicAddress.update({"broadcast" : addr.broadcast})
				if addr.netmask:
					myNicAddress.update({"netmask" : addr.netmask})
				if addr.ptp:
					myNicAddress.update({"p2p" : addr.ptp})
				myAllNicAddress.append(myNicAddress)
				myAllNicDetails.append({nic : {"address" : myAllNicAddress, "stats" : mygetNicDetails, "ioCounters" : myNicIOCntrs, "address" : myNicAddress}})
			
		# reformatting to move all addresstype together for a given nic
		# retrieving all interface
		myAllInterfaces = list(set([list(nic.keys())[0] for nic in myAllNicDetails]))
		myAllInterfaces.sort(reverse=True) # moving "loopback -- lo to the top of the list"
		myFormattedNicDetails = []
		for intf in myAllInterfaces:
			myintfDetails = [nicIntf for nicIntf in myAllNicDetails if list(nicIntf.keys())[0] == intf]
			# found all address for a given interface
			myAllIntfAddresses = []
			for address in myintfDetails:
				myNicAddDetails = self.getACopy(address[intf]["address"])
				myNicAddDetails.update({"stats" : address[intf]["stats"]})
				myNicAddDetails.update({"ioCounters" : address[intf]["ioCounters"]})
				myAllIntfAddresses.append(myNicAddDetails)
			# adding this interface's all address and its stats/iocounters
			myFormattedNicDetails.append({"intf" : intf, "addresses" : myAllIntfAddresses})

		return myFormattedNicDetails
		#return myAllNicDetails
		#print("nic stats json", str(myAllNicDetails))

	def getCurrentUser(self):
		"""
		returns current user
		"""
		try:
			return {"current" : getpass.getuser(), "login" : os.getlogin()}
		except Exception as error:
			return {"current" : getpass.getuser(), "login" : getpass.getuser()}

	def getHostInfo(self):
		"""
		Returns the host details for host
		"""
		# disk usage information
		import distro
		partitions = psutil.disk_partitions()
		storageDetails = []
		for part in partitions:
			usage = psutil.disk_usage(part.mountpoint)
			storageDetails.append({
				"mountPoint" : part.mountpoint,
				"fsType" : part.fstype,
				"total" : usage.total,
				"used" : usage.used,
				"free" : usage.free
				})

		#loginUser = getpass.getuser()
		try:
			loginUser = os.getlogin()
		except Exception as error:
			loginUser = getpass.getuser()

		currentUser = getpass.getuser()

		if platform.system().upper() == "LINUX":
			import grp
			currUsrGrpDetail = grp.getgrgid(os.getgid())
			currUsrGrpName = currUsrGrpDetail.gr_name
		else:
			currUsrGrpName = "N/A"

		myOsPlatformUName = platform.uname()

		myOS = {
			"system" : myOsPlatformUName.system,
			"node" : myOsPlatformUName.node,
			"version" : myOsPlatformUName.version,
			"release" : myOsPlatformUName.release,
			"machine" : myOsPlatformUName.machine,
			"processor" : myOsPlatformUName.processor,
			"distribution" : ""
		}
		
		if myOsPlatformUName.system.lower() == "linux":
			myOS.update({
				#"distribution" : platform.linux_distribution()[0],
				#"version" : "".join([platform.linux_distribution()[1], ",", platform.linux_distribution()[2]]),
				#"release" : myOsPlatformUName.release,
				"distribution" : distro.linux_distribution()[0],
				"version" : "".join([distro.linux_distribution()[1], ",", distro.linux_distribution()[2]]),
				"release" : myOsPlatformUName.release,
			})


		hostInfo = {
			"hostName" : socket.gethostname(),
			"hostFQDN" : self.getHostFqDn(),
			"ipAddress" : self.getIpAddr(),
			"ipv6Address" : self.getIPV6(),
			"cpuCount" : psutil.cpu_count(logical=True), # need # physical core * thread
			"cpuPercent" : psutil.cpu_percent(),
			"cpuTimes" : psutil.cpu_times(),  #scputimes(user=29956.54, nice=224.69, system=14441.85, idle=1434416.23, iowait=857.91, irq=0.0, softirq=316.35, steal=0.0, guest=0.0, guest_nice=0.0)
			#"avgLoad" : psutil.getloadavg(), # average system load over the last 1, 5 and 15 minutes as a tuple
			"avgLoad" : [load / psutil.cpu_count() * 100 for load in psutil.getloadavg()], # return load average taking into consideration of all cpu available
			"memory" : psutil.virtual_memory(), # svmem(total=16657461248, available=15409311744, percent=7.5, used=867164160, free=237600768, active=702038016, inactive=15002210304, buffers=19894272, cached=15532802048, shared=34611200, slab=442126336)
			"swap" : psutil.swap_memory(), # sswap(total=2147479552, used=0, free=2147479552, percent=0.0, sin=0, sout=0)
			"osType" : platform.system(),
			"os" : platform.uname(), #uname_result(system='Linux', node='usdfw21as383v', release='3.10.0-957.10.1.el7.x86_64', version='#1 SMP Thu Feb 7 07:12:53 UTC 2019', machine='x86_64', processor='x86_64'
			"osInfo" : myOS,
			"bootTime" : self.convertEpocToDateTime(psutil.boot_time()),
			#"netConnections" : psutil.net_connections(),
			"nicDetails" : self.getNicDetails(),
			"nicAddress" : psutil.net_if_addrs(),
			"netConnections" : psutil.net_connections(),
			"storageDetails" : storageDetails,
			"storageStats" : psutil.disk_io_counters(), # sdiskio(read_count=157732, write_count=8275084, read_bytes=3592052736, write_bytes=240303613952, read_time=765554, write_time=55836044, read_merged_count=1616, write_merged_count=253846, busy_time=4300865)
			"connectedUsers" : psutil.users(), # users connected in system
			"users" : {"connectedUsers": psutil.users(), "loginUser" : loginUser, "currentUser" : currentUser, "currentUserGrp" : currUsrGrpName}
		}


		if hasattr(psutil, "sensors_fans"):
			hostInfo.update({"sensorFans" : psutil.sensors_fans()}) # returns temperature
		else:
			hostInfo.update({"sensorFans" : ""})

		if hasattr(psutil, "sensors_temperatures"):
			hostInfo.update({"sensorTemps" : psutil.sensors_temperatures()}) # return fans speed
		else:
			hostInfo.update({"sensorTemps" : ""})

		if hasattr(psutil, "sensors_battery"):
			hostInfo.update({"sensorBattery" : psutil.sensors_fans()}) # return battery detail
		else:
			hostInfo.update({"sensorBattery" : ""})

		return hostInfo

	# pid method
	def getPidInfo(self, pid):
		"""
		Returns prcess information
		"""
		try:
			if psutil.pid_exists(pid):
				myProcess = psutil.Process(pid)
				"""
				myProcInfo = {
					"pid" : myProcess.pid(),
					"ppid" : myProcess.ppid(),
					"started" : datetime.datetime.fromtimestamp(myProcess.create_time()).strftime("%Y-%m-%d %H:%M:%S"),
					"name" : myProcess.name(),
					"username" : myProcess.username(),
					"cmdline" : myProcess.cmdline(),
					"cpu_times" : sum(myProcess.cpu_times()),
					"memory_info" : "".join([str(myProcess.memory_info().rss / (1024*1024))," MB"]),
					"open_files" : myProcess.open_files(),
					"open_file_count" : len(myProcess.open_files()) if myProcess.open_files() else 0 
				}
				"""
				myProcDictRaw = myProcess.as_dict()
				myProcessInfoDict = {
					"pid" : myProcDictRaw["pid"],
					"ppid" : myProcDictRaw["ppid"],
					"name" : myProcDictRaw["name"],
					"status" : myProcDictRaw["status"],
					"username" : myProcDictRaw["username"],
					"cmdline" : myProcDictRaw["cmdline"],
					"cwd" : myProcDictRaw["cwd"],
					"cpu_times" : sum(myProcDictRaw["cpu_times"]),
					"cpu_percent" : myProcDictRaw["cpu_percent"],
					"memory_info" : "".join([str(myProcDictRaw["memory_info"].rss / (1024*1024))," MB"]),
					"connections" : myProcDictRaw["connections"],
					"open_files" : [file.path for file in myProcDictRaw["open_files"]] if myProcDictRaw["open_files"] else [],
					"open_file_count" : len(myProcDictRaw["open_files"]) if myProcDictRaw["open_files"] else 0,
					"environment" : myProcDictRaw["environ"]
				}
				return myProcessInfoDict

		except Exception as error:	
			raise error

	def getParentPid(self, pid):
		"""
		Returns Pid's parent pid information 
		"""
		try:
			return psutil.Process(pid)
		except Exception as e:
			return None

	def getPidEnvironment(self, pid = None):
		"""
		Returns pid's environment variable which was used to fork this pid
		"""
		return psutil.Process(pid).environ()

	def findProcStatusByCount(self):
		"""
		returns distinct process status and its count
		"""
		from collections import Counter

		allProcStatus = [p.info['status'] for p in psutil.process_iter(['status'])]

		return dict(zip(Counter(allProcStatus).keys(), Counter(allProcStatus).values()))

	def findAllProcessByStatus(self, status):
		"""
		returns all process by a given status
		"""
		processLists = []
		for proc in psutil.process_iter(["name","username","exe","cmdline","status","create_time","pid","ppid","cpu_times","open_files","memory_info"]):
			if status == proc.info['status']:
				processLists.append({
					"pid" : proc.info["pid"],
					"ppid" : proc.info["ppid"],
					"name" : proc.info["name"],
					"status" : proc.info["status"],
					"started" : datetime.datetime.fromtimestamp(proc.info["create_time"]).strftime("%Y-%m-%d %H:%M:%S"),
					"username" : proc.info["username"],
					"cmdline" : proc.info["cmdline"],
					"exe" : proc.info["exe"],
					"cpu_times" : sum(proc.info["cpu_times"]),
					"memory_info" : "".join([str(proc.info["memory_info"].rss / (1024*1024))," MB"]),
					"open_files" : proc.info["open_files"],
					"open_file_count" : len(proc.info["open_files"]) if proc.info["open_files"] else 0 
					})
		return processLists

	def findProcessByName(self, name):
		"""
		returns all process for given name
		"""
		processLists = []
		for proc in psutil.process_iter(["name","username","exe","cmdline","status","create_time","pid","ppid","cpu_times","open_files","memory_info"]):
			if name == proc.info['name'] or proc.info['exe'] and \
				os.path.basename(proc.info['exe']).lower() == name or proc.info['cmdline'] and \
				proc.info['cmdline'][0] == name:
				processLists.append({
					"pid" : proc.info["pid"],
					"ppid" : proc.info["ppid"],
					"name" : proc.info["name"],
					"status" : proc.info["status"],
					"started" : datetime.datetime.fromtimestamp(proc.info["create_time"]).strftime("%Y-%m-%d %H:%M:%S"),
					"username" : proc.info["username"],
					"cmdline" : proc.info["cmdline"],
					"exe" : proc.info["exe"],
					"cpu_times" : sum(proc.info["cpu_times"]),
					"memory_info" : "".join([str(proc.info["memory_info"].rss / (1024*1024))," MB"]),
					"open_files" : proc.info["open_files"],
					"open_file_count" : len(proc.info["open_files"]) if proc.info["open_files"] else 0 
					})
		return processLists

	def findProcessByUser(self, user):
		"""
		returns all process for a given user
		"""
		processLists = []
		for proc in psutil.process_iter(["name","username","exe","cmdline","status","create_time","pid","ppid","cpu_times","open_files","memory_info"]):
			if proc.info['username'].lower().startswith(user.lower()):
				processLists.append({
					"pid" : proc.info["pid"],
					"ppid" : proc.info["ppid"],
					"name" : proc.info["name"],
					"status" : proc.info["status"],
					"started" : datetime.datetime.fromtimestamp(proc.info["create_time"]).strftime("%Y-%m-%d %H:%M:%S"),
					"username" : proc.info["username"],
					"cmdline" : proc.info["cmdline"],
					"exe" : proc.info["exe"],
					"cpu_times" : sum(proc.info["cpu_times"]),
					"memory_info" : "".join([str(proc.info["memory_info"].rss / (1024*1024))," MB"]),
					"open_files" : proc.info["open_files"],
					"open_file_count" : len(proc.info["open_files"]) if proc.info["open_files"] else 0 
					})
		return processLists

	def findAllActiveProcesse(self):
		"""
		returns all active process running
		"""
		processLists = []
		for proc in psutil.process_iter(["name","username","exe","cmdline","status","create_time","pid","ppid","cpu_times","open_files","memory_info"]):
			if proc.info['status'] == psutil.STATUS_RUNNING:
				processLists.append({
					"pid" : proc.info["pid"],
					"ppid" : proc.info["ppid"],
					"name" : proc.info["name"],
					"status" : proc.info["status"],
					"started" : datetime.datetime.fromtimestamp(proc.info["create_time"]).strftime("%Y-%m-%d %H:%M:%S"),
					"username" : proc.info["username"],
					"cmdline" : proc.info["cmdline"],
					"exe" : proc.info["exe"],
					"cpu_times" : sum(proc.info["cpu_times"]),
					"memory_info" : "".join([str(proc.info["memory_info"].rss / (1024*1024))," MB"]),
					"open_files" : proc.info["open_files"],
					"open_file_count" : len(proc.info["open_files"]) if proc.info["open_files"] else 0 
					})
		return processLists

	def findAllProcsUsingLogFiles(self):
		"""
		returns all processes which is using log files
		"""
		processLists = []
		for proc in psutil.process_iter(["name","username","exe","cmdline","status","create_time","pid","ppid","cpu_times","open_files","memory_info"]):
			for file in proc.info['open_files'] or []:
				if file.path.endswith('.log'):
					processLists.append({
						"pid" : proc.info["pid"],
						"ppid" : proc.info["ppid"],
						"name" : proc.info["name"],
						"status" : proc.info["status"],
						"started" : datetime.datetime.fromtimestamp(proc.info["create_time"]).strftime("%Y-%m-%d %H:%M:%S"),
						"username" : proc.info["username"],
						"cmdline" : proc.info["cmdline"],
						"exe" : proc.info["exe"],
						"cpu_times" : sum(proc.info["cpu_times"]),
						"memory_info" : "".join([str(proc.info["memory_info"].rss / (1024*1024))," MB"]),
						"log_file" : file.path 
						})
		return processLists

	def findTopCpuProcess(self, nProcess = 10):
		"""
		returns top n process consuming cpu
		"""
		#pp([(proc.pid, proc.info['name'], sum(proc.info['cpu_times'])) for proc in sorted(psutil.process_iter(['name', 'cpu_times']), key=lambda p: sum(proc.info['cpu_times'][:2]))][-3:])
		myProcessList = []
		for proc in sorted(psutil.process_iter(["name","username","exe","cmdline","status","create_time","pid","ppid","cpu_times","open_files","memory_info"]), \
			key=lambda p: sum(proc.info['cpu_times'][:2]))[-nProcess:]:
			processLists.append({
				"pid" : proc.info["pid"],
				"ppid" : proc.info["ppid"],
				"name" : proc.info["name"],
				"status" : proc.info["status"],
				"started" : datetime.datetime.fromtimestamp(proc.info["create_time"]).strftime("%Y-%m-%d %H:%M:%S"),
				"username" : proc.info["username"],
				"cmdline" : proc.info["cmdline"],
				"exe" : proc.info["exe"],
				"cpu_times" : sum(proc.info["cpu_times"]),
				"memory_info" : "".join([str(proc.info["memory_info"].rss / (1024*1024))," MB"]),
				"open_files" : proc.info["open_files"],
				"open_file_count" : len(proc.info["open_files"]) if proc.info["open_files"] else 0 
				})
		return processLists

	def findTopMemoryProcess(self, memoryThreshold):
		"""
		returns all processes consuming more memory as passed
		arguments: memoryThreshold (in MB)
		"""
		#pp([(proc.pid, proc.info['name'], sum(proc.info['cpu_times'])) for proc in sorted(psutil.process_iter(['name', 'cpu_times']), key=lambda p: sum(proc.info['cpu_times'][:2]))][-3:])
		myProcessList = []
		for proc in psutil.process_iter(["name","username","exe","cmdline","status","create_time","pid","ppid","cpu_times","open_files","memory_info"]):
			if proc.info['memory_info'].rss > (memoryThreshold * 1024 * 1024):
				processLists.append({
					"pid" : proc.info["pid"],
					"ppid" : proc.info["ppid"],
					"name" : proc.info["name"],
					"status" : proc.info["status"],
					"started" : datetime.datetime.fromtimestamp(proc.info["create_time"]).strftime("%Y-%m-%d %H:%M:%S"),
					"username" : proc.info["username"],
					"cmdline" : proc.info["cmdline"],
					"exe" : proc.info["exe"],
					"cpu_times" : sum(proc.info["cpu_times"]),
					"memory_info" : "".join([str(proc.info["memory_info"].rss / (1024*1024))," MB"]),
					"open_files" : proc.info["open_files"],
					"open_file_count" : len(proc.info["open_files"]) if proc.info["open_files"] else 0 
					})
		return processLists

	def getPidCreateTime(self, pid = None):
		"""
		Returns time (string) when thid pid was created (if pid parmeter is None, current pid value is used). Returns datetime (converting epoch time)
		"""
		return datetime.datetime.fromtimestamp(psutil.Process(pid).create_time()).strftime("%Y-%m-%d %H:%M:%S")

	def getLinuxUSerLastLogon(self, userName):
		"""
		Linux only; return last log on details for a given user (WIP)
		"""
		myLastLogOnCmd = f"/bin/last {userName} | sed -re 's,\\s+, ,g' | cut -d ' ' -f 3-"
		myLastLoginRecords = self.execOSCmdRetResult(myLastLogOnCmd)

	def getAllOsUserDetsils(self):
		"""
		return all OS userss as a generator, use list to get all the users list
		"""
		myOSType = self.getOSType()

		if  myOSType == "linux":
			import pwd
			for user in pwd.getpwall():
				yield {
					"user" : user.pw_name, "name" : user.pw_gecos, "uid" : user.pw_uid, "gid" : user.pw_gid, "homeDir" : user.pw_dir, "shell" : user.pw_shell
					}
		elif myOSType == "windows":
			pass

	def isLinuxOsUserExists(self, userName):
		try:
			import pwd
			myUserDetail = pwd.getpwnam(userName)
			return True
		except KeyError:
			return False

	def getLinuxOsUserDetails(self, userName):
		try:
			import pwd
			myUserDetail = pwd.getpwnam(userName)
			return myUserDetail
		except KeyError as error:
			raise error

	def getUXPassLastChange(self, userName):
		try:
			myLastPassChgDtRaw = self.execOSCmdRetResult(self.Globals.OS_CMD["LAST_PASSWORD_CHANGE_DATE"].format(user = userName))

			if myLastPassChgDtRaw:
				if isinstance(myLastPassChgDtRaw, tuple) or isinstance(myLastPassChgDtRaw, list):
					# we got tuple/list, picking 1st item
					myLastPassChgDtRaw = myLastPassChgDtRaw[0]

					if isinstance(myLastPassChgDtRaw, bytes):
						myLastPassChgDtStr = myLastPassChgDtRaw.decode('utf-8')
					if myLastPassChgDtStr:
						myLastPassChgDtStr = myLastPassChgDtStr.lstrip().replace('\n','').replace('\t','')
						myLastPassChgDate = self.convertStrDate2DateTime(myLastPassChgDtStr, "%b %d, %Y")
					else:
						myLastPassChgDate = ""
				else:
					myLastPassChgDate = ""

				return myLastPassChgDate

		except Exception as error:
			raise error

	# deploy
	def buildDeployVar(self, jiraKey, deployDocId, env, location):
		'''
		build deployment var which can be used by deploy.py/mongo_deploy.py and other module which need 
		'''
		baseLoc = self.buildPath(location, str(jiraKey))
		stagingLoc = self.buildPath(baseLoc, self.buildPath(env, str(deployDocId)) )
		
		bbCloneDir = self.buildPath(stagingLoc, "bb_clone_")
		jiraDownloadDir = self.buildPath(stagingLoc, "jira_download_")
		jiraUploadDir = self.buildPath(stagingLoc, "jira_upload")

		backupDir = self.buildPath(stagingLoc, ''.join(['backup_',self.getCurDateTimeForDir()]) )
		rollbackDir = self.buildPath(stagingLoc, ''.join(['rollback_',self.getCurDateTimeForDir()]) )

		backupLogFile = self.buildPath(backupDir, ''.join([str(deployDocId),'_backup.log']) )
		backupErrorFile = self.buildPath(backupDir, ''.join([str(deployDocId),'_backup.error']) )
		backupReadmeFile = self.buildPath(backupDir, ''.join([str(deployDocId),'_backup.readme']) )
		pidFile = 	self.buildPath(stagingLoc, ''.join(['deploy',str(deployDocId),".pid"]))
		successFile = self.buildPath(stagingLoc, self.Globals.success)
		unSuccessFile = self.buildPath(stagingLoc, self.Globals.unsuccess)


		return {
			"baseLoc" : baseLoc,
			"stagingLoc" : stagingLoc,
			"bbCloneLoc" : bbCloneDir,
			"jiraDownload" : jiraDownloadDir,
			"jiraUpload" : jiraUploadDir,
			"backupDir" : backupDir,
			"rollbackDir" : rollbackDir,
			"backupLogFile" : backupLogFile,
			"backupErrorFile" : backupErrorFile,
			"backupReadmeFile" : backupReadmeFile,
			"pidFile" : pidFile,
			"successFile" : successFile,
			"unSuccessFile" : unSuccessFile
		}

	def buildBBCloneLoc(self, jiraKey, deployDocId, env, location):
		'''
		build deployment var which can be used by deploy.py/mongo_deploy.py and other module which need 
		'''
		baseLoc = self.buildPath(stagingLoc, str("jiraKey"))
		stagingLoc = self.buildPath(baseLoc, self.buildPath(env, str(deployDocId)) )
		bbCloneLoc = self.buildPath(stagingLoc, "bb_clone") 

		return bbCloneLoc


	def buildBackupLocObj(self, deployDocId, taskId, baseBackupLoc):
		'''
		build the backup loc and file information, this is needed when calling backup routine
		'''
		myBackupLoc = self.buildPath(baseBackupLoc, "".join(["task_", str(taskId)]))
		myBackupObj = {
			"location" : myBackupLoc,
			"logFile" : self.buildPath(myBackupLoc, ''.join([ str(deployDocId), "_task_", str(taskId),'_backup.log'])),
			"errorFile" : self.buildPath(myBackupLoc, ''.join([ str(deployDocId), "_task_", str(taskId),'_backup.error'])),
			"readmeFile" : self.buildPath(myBackupLoc, ''.join([ str(deployDocId), "_task_", str(taskId),'_backup.readme']))
		}
		return myBackupObj

	def buildRestoreLocObj(self, deployDocId, taskId, backupLoc, logFileLoc):
		'''
		build the restore loc and file information, this is needed when calling restore routine
		'''
		myRestoreObj = {
			"location" : backupLoc,
			"logFile" : self.buildPath(logFileLoc, ''.join([ str(deployDocId), "_task_", str(taskId),'_restore.log'])),
			"errorFile" : self.buildPath(logFileLoc, ''.join([ str(deployDocId), "_task_", str(taskId),'_restore.error']))
		}
		return myRestoreObj

	def convObjectId2Json(self, objectIds):
		from bson import ObjectId, json_util
		if isinstance(objectIds, list):
			myObjectIds = []
			[myObjectIds.insert(json.loads(json_util.dump(id))) for id in objectIds]
			return myObjectIds
		elif isinstance(objectIds, ObjectId):
			return json.loads(json_util.dump(objectIds))

	def convStrToDict(self, strValue):
		# convert json stotred in string to dict
		return json.loads(strValue)

	def convStrToJson(self, strValue):
		# convert json stotred in string to dict
		return json.loads(strValue)

	def removeDupFromList(self, listArg):
		usedElements = set()
		return [elem for elem in listArg if not self.isInElement(elem, usedElements) ]

	def isInElement(self, value, usedElem):
		low = value.lower()
		if low in usedElem:
			return True
		usedElem.add(low)
		return False

	def writeMongoIds2Json(self, fileNameWPath, data):
		from bson import ObjectId
		myData = []
		if isinstance(data, list):
			for value in data:
				if isinstance(value, ObjectId.ObjectId):
					# convert to string
					pass
		with open(fileOpenMode,"w") as file:
			pass

	def buildRollbackFile(self, fileName, taskId, op):
		return fileName.format(taskId = taskId, sourceOp = op)

	def getCompDbType(self, component):
		# return component database type from Globals (each component has its associated db type used e.g. repository:mongo)
		dbType = [comp[component] for comp in self.Globals.componentDB if component in comp]
		if dbType: return dbType[0]

	def isValidComponent(self, component):
		# checks if this a valid component
		comp = [comp for comp in self.Globals.componentDB if component in comp]
		if comp: 
			return True
		else:
			return False

	def buildBeginDeployStatus(self, operation):
		'''
		purpose: return begin deployment status based on operation
		arguments:
			securityToken : securityToken
			operation: deployment operation
		return: begin deployment status
		'''
		try:
			if operation in [self.Globals.opDeploy, self.Globals.opRemoveTask]:
				return self.Globals.deployInprogress
			elif operation == self.Globals.opRollback:
				return self.Globals.rollbackInprogress
			else:
				return self.inprogress 

		except Exception as error:
			raise error

	def splitString(self, string_):
		return re.findall(r'[^,;\s]+',string_)

	def getHostName(self):
		return socket.gethostname()

	def getOSType(self):
		"""
		return os type
		"""
		return platform.uname()[0].lower()

	def isValidHost(self, hostName):
		try:
			myResult = socket.gethostbyname(socket.getfqdn(hostName))
			#print(f"returning true, found host >>> {myResult}")
			if myResult:
				return True
			else:
				return False
		except Exception as error:
			#print("returning false")
			return False

	def getHostFqDn(self):
		return socket.getfqdn(socket.gethostname())

	def getHostFqdn4Server(self, server):
		return socket.getfqdn(server)

	def getHostIPAddress(self, server):
		try:
			return socket.gethostbyname(socket.getfqdn(server))
		except Exception as error:
			return ""

	def getHostNameByAddr(self, ipAddress):
		try:
			if len(ipAddress.split(".")) == 3:
				# we have valid ip, looking for name
				return socket.gethostbyaddr(ipAddress)
			else:
				raise ValueError("Invalid IP Address !!!")
		except Exception as error:
			return ""

	def getIpAddr(self):
		return [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
	
	def getIPV6(self):
		# search for all addresses, but take only the v6 ones
		host = self.getHostName()
		port = 0
		alladdr = socket.getaddrinfo(host,port)
		ip6 = filter(
			lambda x: x[0] == socket.AF_INET6, # means its ip6
			alladdr
			)
		# if you want just the sockaddr
		# return map(lambda x:x[4],ip6)
		if list(ip6):
			return list(ip6)[0][4][0]
		else:
			return ""

	def isIpv6(self):
		return socket.has_ipv6

	def genUniqueId(self):
		#return uuid.uuid5(uuid.NAMESPACE_DNS, self.getHostFqDn())
		return uuid.uuid4()

	def genStrUniqueId(self):
		return str(self.genUniqueId())

	def buildBBUrl(self, bbUrl):
		return bbUrl.replace("https://","https://{user}:{userPass}@")

	def cloneGit(self, bbUrl, userName, userPass, cloneToDir):
		myBBUrl = self.buildBBUrl(bbUrl)
		myBBUrlWithCred = myBBUrl.format(user = userName, userPass = userPass)
		myClonedRepo = Repo.clone_from(myBBUrlWithCred, cloneToDir)
		return myClonedRepo

	def exitSuccess(self):
		sys.exit(0)

	def exitFailure(self):
		sys.exit(1)

	def isBsonObjectId(self, element):
		import bson
		return isinstance(element, bson.objectid.ObjectId)

	def convBsonObjectId2Oid(self, data):
		from bson.json_util import dumps
		if self.isBsonObjectId(data):
			return dumps(data)

	def convOid2BsonObjectId(self, data):
		from bson.json_util import dumps
		if isinstance(data, dict) or isinstance(data, list):
			return dumps(data)

	def getCurrentDate(self):
		# return current date only (removes time factor)
		return self.removeTimeFromDate(self.lambdaGetCurrDateTime())

	def getDayName4Date(self, dateArg):
		# return day name for a given date
		import calendar
		return calendar.day_name[dateArg.weekday()]

	def addDaysToDate(self, datetime_):
		"""
		add days to a given dateTime object
		"""
		if self.isDate(datetime_):
			return datetime_ + datetime.timedelta(days = 1)

	def removeTimeFromDate(self, datetime_):
		"""
		remove time factor from dateTime object
		"""
		if self.isDate(datetime_):
			if isinstance(datetime_, datetime.datetime):
				return datetime_.replace(hour=0, minute=0, second=0, microsecond=0)
			elif isinstance(datetime_, datetime.date):
				# adding hour/minute/seconds/milliseconds and then replacing
				return self.convStr2DateViaParser(datetime_.strftime("%Y-%m-%d %H:%M:%S.%f")).replace(hour=0, minute=0, second=0)
		else:
			return datetime_


	def addTimeToDateTime(self, datetime_, days_ = 0, hours_ = 0, minutes_ = 0, seconds_ = 0, microSeconds_ = 0, millSeconds_ = 0 ):
		"""
		returns by adding days/hours/minutes/seconds/microseconds/milliseconds to a dateTime
		"""
		return datetime_ + datetime.timedelta(days = days_, hours = hours_, minutes = minutes_, seconds = seconds_, microseconds = microSeconds_, milliseconds = millSeconds_)


	def isValidStrDateFormat(self, dateStr, dateStrFormat):
		"""
		checks if given date in string matches with the format passed as an argument
		For e.g. "2020-01-01" matches with the format "%Y-%m-%d"
		"""
		try:
			myDate = self.convertStrDate2DateTime(dateStr, dateStrFormat)
			return True
		except Exception as error:
			return False

	def isDateBetween2Dates(self, dateTime_, startDateTime_, endDateTime_):
		"""
		checks if a given dateTime is between startDateTime_ and endDateTime_
		"""
		# should convert if any string found
		if not isinstance(dateTime_, datetime.datetime):
			myDateTime = datetime.strptime(dateTime_, '%Y-%m-%d')
		else:
			myDateTime = dateTime_

		if not isinstance(startDateTime_, datetime.datetime):
			myStartDateTime = datetime.strptime(startDateTime_, '%Y-%m-%d')
		else:
			myStartDateTime = dateTime_

		if not isinstance(endDateTime_, datetime.datetime):
			myEndDateTime = datetime.strptime(endDateTime_, '%Y-%m-%d')
		else:
			myEndDateTime = dateTime_

		return myStartDateTime <= myDateTime <= myEndDateTime

	def diffBetweenDatesInDays(self, startDateArg, endDateArg):
		"""
		Returns difference between 2 dates as days
		"""
		#print(startDateArg, endDateArg)
		return round((self.convStr2DateViaParser(endDateArg) - self.convStr2DateViaParser(startDateArg)).days)

	def getNthDayMonth(self, dateTime_, day, occurrence):
		"""
		returns nth day of Month as datetime. 
		For e.g. return 3rd Sunday of Month getNthDayOfMonth(datetime.datetime.now(), "Sunday", 3)
		"""
		from datetime import date
		#print (dt + relativedelta(day=1, weekday=SA(occurrence)))
		if day.lower() == "monday":
			return dateTime_ + relativedelta(day=1, weekday=MO(occurrence))
		if day.lower() == "tuesday":
			return dateTime_ + relativedelta(day=1, weekday=TU(occurrence))
		if day.lower() == "wednesday":
			return dateTime_ + relativedelta(day=1, weekday=WE(occurrence))
		if day.lower() == "thursday":
			return dateTime_ + relativedelta(day=1, weekday=TH(occurrence))
		if day.lower() == "friday":
			return dateTime_ + relativedelta(day=1, weekday=FR(occurrence))
		if day.lower() == "saturday":
			return dateTime_ + relativedelta(day=1, weekday=SA(occurrence))
		if day.lower() == "sunday":
			return dateTime_ + relativedelta(day=1, weekday=SU(occurrence))

		#get_third_fri_of_mth(date(2019, 1, 30))
		#get_third_fri_of_mth(date(2019, 6, 4))
		# add time date + datetime.timedelta(hours=, minutes=, seconds=)

	def getDateFromSched(self, schedule):
		"""
		will return the start and for a given schedule. schedule must be in following format
		daily 	:	daily schedule
			{"freq" : "daily"}
		weekly 	:	every monday
			{"freq" : "weekly", "day" : "monday"}
		monthly	:	every Monday of 1st week of each month 
			{"freq" : "monthly", "week" : 1, "day" : monday"}
		quarterly	:	every Monday of 1st week of 2nd month of a Quarter
			{"freq" : "quarterly", "month" : 1, week" : 1, "day" : monday"}
		"""
		myFrequency = schedule["freq"]
		myStartDate = ""

		# validation
		if myFrequency.lower() == "weekly":
			if not("day" in schedule):
				raise ValueError("day key is required")
		if myFrequency.lower() == "monthly":
			if not("week" in schedule and "day" in schedule):
				raise ValueError("week/day key is required")
		if myFrequency.lower() == "quarterly":
			if not("month" in schedule and "week" in schedule and "day" in schedule):
				raise ValueError("month/week/day key is required")		
		if myFrequency.lower() == "yearly":
			if not("month" in schedule and "week" in schedule and "day" in schedule):
				raise ValueError("month/week/day key is required")

		myDays=["sunday","monday","tuesday","wednesday","thursday","friday","saturday"]

		if "day" in schedule and schedule["day"]:
			if not schedule["day"].lower() in myDays:
				raise ValueError("Invalid days, days must be in {days}".format(days = myDays))

			myDayInt = myDays.index(schedule["day"].lower()) - 1

		if myFrequency.lower() == "daily":
			myStartDate = self.removeTimeFromDate(datetime.datetime.today())
			'''
			# Date for Monday of this week
			return datetime.datetime.now() + datetime.timedelta(days=-datetime.datetime.now().weekday())
			# Date for Friday of this week
			return datetime.datetime.now()+datetime.timedelta(days= 4 - datetime.datetime.now().weekday())
			'''
		if myFrequency.lower() == "weekly":

			myStartDate = self.removeTimeFromDate(datetime.datetime.today() + datetime.timedelta(days = (myDayInt- datetime.datetime.now().weekday())))
			startWeekDate = myStartDate + datetime.timedelta(days = ( - datetime.datetime.today().weekday()))
			endWeekDate = myStartDate + datetime.timedelta(days = (4 - datetime.datetime.today().weekday()))

			# Date for Monday of this week
			'''
			if myDayInt = 1: # monday
				return datetime.datetime.now() + datetime.timedelta(days=-datetime.datetime.now().weekday())
			els:
				# Date for Friday of this week
				return datetime.datetime.now() + datetime.timedelta(days= 4 - datetime.datetime.now().weekday())
			'''
		if myFrequency.lower() == "monthly":
			# we need week and day
			myWeek = schedule["week"]
			myDay = schedule["day"]
			myYear = datetime.datetime.today().year
			myMonth = datetime.datetime.today().month

			myStartDate = self.removeTimeFromDate(self.getDayOfWeekOfMonth(myDay, int(myYear), int(myMonth), int(myWeek)))

		if myFrequency.lower() == "quarterly":
			# we need week and day
			myWeek = schedule["week"]
			myDay = schedule["day"]
			myQtrMonth = int(datetime.datetime.today().month)
			myNMonth = schedule["month"]
			myYear = datetime.datetime.today().year

			myMonth = self.getNMonthOfQtr(myQtrMonth, myNMonth)
			myYear = datetime.datetime.today().year

			myStartDate = self.removeTimeFromDate(self.getDayOfWeekOfMonth(myDay, int(myYear), int(myMonth), int(myWeek)))

		if myFrequency.lower() == "yearly":
			# we need week and day
			myWeek = schedule["week"]
			myDay = schedule["day"]
			myMonth = schedule["month"]
			myYear = datetime.datetime.today().year

			#myMonth = self.getNMonthOfQtr(myQtrMonth, myNMonth)
			myYear = datetime.datetime.today().year

			myStartDate = self.removeTimeFromDate(self.getDayOfWeekOfMonth(myDay, int(myYear), int(myMonth), int(myWeek)))

		return myStartDate

	def getEachElemOfDate(self, date_):
		"""
		returns each element of date as tuple (date, day, month#, month name, year)
		"""
		if self.isValidDate(date_):
			myDate = self.convStr2DateViaParser(date_)
			import calendar
			myDay = myDate.day
			myWeekDay = myDate.weekday()
			myDayName = calendar.day_name[myWeekDay]
			myMonth = myDate.month
			myMonthName = calendar.month_name[myMonth]
			myYear = myDate.year
			return (myDay, myDayName, myMonth, myMonthName, myYear)

	def buildDateTimeForMaintWindow(self, maintWindow):
		"""
		return start and end datetime in tuble for a given (below format) maintenance window.
		"maintenanceWindow" : {"week" : 3, "day" : "Saturday", "hours" : "22", "minutes" : 0, "seconds" : 0, "duration" : {"hours" : 6, "minutes" : 0, "seconds" : 0}},
		"""
		myCurrentDateTime = datetime.datetime.today()
		MyStartDateTime = self.getNthDayMonth()

	def buildDateTime4Sched(self, schedule):
		"""
		returns date time based on schedule 
			#schedule : {'freq' : 'daily', 'hour' : 10, 'minutes' : 20, 'seconds' : 10},
			schedule : {'freq' : 'weekly', day' : 'Monday'},
			schedule : {'freq' : 'monthly', 'week':  1, 'day' : 2},
			schedule : {'freq' : 'quarterly', 'month' : 1, 'week':  1, 'day' : 'Monday'},
			schedule : {'freq' : 'yearly', 'month':  1, 'week' : 2, 'day' : 'Monday'},
		"""
		if schedule["freq"].lower() == "weekly":
			pass
		if schedule["freq"].lower() == "monthly":
			pass
		if schedule["freq"].lower() == "quarterly":
			pass
		if schedule["freq"].lower() == "yearly":
			pass

		myCurrentDateTime = datetime.datetime.now()
		MyStartDateTime = self.getNthDayMonth()

	def getNMonthOfQtr(self, currQtrMonth, nMonth):
		"""
		return nth month of qtr
		getNMonthOfQtr
		"""
		return int(currQtrMonth) - (int(currQtrMonth) - int(nMonth)) %3

	def getDayOfWeekOfMonth(self, dayOfWeek, year, month, week) -> datetime.date:
		import calendar
		#def get_nth_DOW_for_YY_MM(dow, yy, mm, nth) -> datetime.date:
		#dow - Python Cal - 6 Sun 0 Mon ...  5 Sat
		#week is 1 based... -1. is ok for last.
		if dayOfWeek.lower() == "sunday":
			myDayOfWeek = calendar.SUNDAY
		elif  dayOfWeek.lower() == "monday":
			myDayOfWeek = calendar.MONDAY
		elif  dayOfWeek.lower() == "tuesday":
			myDayOfWeek = calendar.TUESDAY
		elif  dayOfWeek.lower() == "wednesday":
			myDayOfWeek = calendar.WEDNESDAY
		elif  dayOfWeek.lower() == "thursday":
			myDayOfWeek = calendar.THURSDAY
		elif  dayOfWeek.lower() == "friday":
			myDayOfWeek = calendar.FRIDAY
		elif  dayOfWeek.lower() == "saturday":
			myDayOfWeek = calendar.SATURDAY

		i = -1 if week == -1 or week == 5 else week -1
		valid_days = []
		for d in calendar.Calendar(myDayOfWeek).monthdatescalendar(year, month):
			if d[0].month == month:
				valid_days.append(d[0])

		# will return datetime.datetime class rather datetime.date (mongo bson would thow an error if inserting datetime.date class)
		return datetime.datetime(valid_days[i].year, valid_days[i].month, valid_days[i].day)

	def getCurWeekOfYear(self, dateArg):
		"""
		returns week number of year for a given date 
		"""
		#return datetime.datetime.strftime(dateArg, "%U") # this will consider Sunday as the 1st day of week
		return int(datetime.datetime.strftime(dateArg, "%W"))  # this will consider Monday as the 1st day of week

	def getMonthCalendar(self, yearArg, monthArg):
		"""
		returns list of date for a given month and year.
			For e.g.: calendar.monthcalendar(2019,6) --> get calendar for June 2019
				[[0, 0, 0, 0, 0, 1, 2], [3, 4, 5, 6, 7, 8, 9], [10, 11, 12, 13, 14, 15, 16], [17, 18, 19, 20, 21, 22, 23], [24, 25, 26, 27, 28, 29, 30]]		
			list starts with Monday and ends with Sunday, 2nd array; day 3 is Monday, day 9 is on Sunday
		"""
		return calendar.monthcalendar(yearArg, monthArg)

	def getCurrQtrStartEndDate(self):
		"""
		will return start and date of current qtr
		"""
		current_date = datetime.datetime.now()
		current_quarter = round((current_date.month - 1) / 3 + 1)
		startQtrDate = datetime.datetime(current_date.year, 3 * current_quarter - 2, 1)
		endQtrDate = datetime.datetime(current_date.year, 3 * current_quarter + 1, 1) + datetime.timedelta(days=-1)

		return (self.removeTimeFromDate(startQtrDate), self.removeTimeFromDate(endQtrDate))

	def getQtrEndDate(self, dateArg):
		"""
		will return end date of a qtr for a given date
		"""
		myQuarter = round((dateArg.month - 1) / 3 + 1)
		startQtrDate = datetime.datetime(dateArg.year, 3 * myQuarter - 2, 1)
		endQtrDate = datetime.datetime(dateArg.year, 3 * myQuarter + 1, 1) + datetime.timedelta(days=-1)

		return self.removeTimeFromDate(endQtrDate)

	def getWeekStartEndDate(self, dateArg):
		"""
		will return start and end date of week for a given date
		"""
		#today = datetime.datetime.now()

		startWeekDate = dateArg + datetime.timedelta(days = ( - datetime.datetime.today().weekday()))
		#endWeekDate = dateArg + datetime.timedelta(days = (4 - datetime.datetime.today().weekday()))
		endWeekDate = dateArg + datetime.timedelta(days = 6)
		# need to replace time factor with 0

		return (self.removeTimeFromDate(startWeekDate), self.removeTimeFromDate(endWeekDate))

	def getMonthEndDate(self, dateArg):
		"""
		will return start and end date of month for a given date
		"""
		#today = datetime.datetime.now()

		#from dateutil.relativedelta import relativedelta
		#1stDayOfMonth = datetime(dateArg.year, dateArg.month, 1) + relativedelta(months=1, days=-1)
		lastDayOfMonth = datetime.datetime(dateArg.year, dateArg.month, 1) + relativedelta(month=1, days=-1)
		return self.removeTimeFromDate(lastDayOfMonth)

	def getYearEndDate(self, dateArg):
		"""
		will return start and end date of month for a given date
		"""
		#today = datetime.datetime.now()

		#from dateutil.relativedelta import relativedelta
		#1stDayOfMonth = datetime(dateArg.year, dateArg.month, 1) + relativedelta(months=1, days=-1)
		return datetime.date(dateArg.year, 12, 31)

	def addDaysToDate(self, dateArg, daysArg):
		"""
		add days to a date argument
		"""

		return dateArg + relativedelta(days = daysArg)

	def addMonthsToDate(self, dateArg, monthsArg):
		"""
		add months to a date argument
		"""

		return dateArg + relativedelta(months = monthsArg)

	def addYearsToDate(self, dateArg, yearsArg):
		"""
		add years to a date argument
		"""

		return dateArg + relativedelta(years = yearsArg)

	def addTimeToDate(self, dateArg, hoursArg, minutesArg, secondsArg):
		"""
		add months to a date argument
		"""

		return dateArg + relativedelta(hours = hoursArg, minutes = minutesArg, seconds = secondsArg )

	def convSecs2Hour(self, seconds):
		"""
		convert seconds to hours
		"""
		mm, ss = divmod(secs, 60)
		hh, mm = divmod(mm, 60)
		return "%d:%02d:%02d" % (hh, mm, ss)

	def getUsersGroup(self, userName):
		"""
		returns users group name (do not use !!!)
		"""
		if platform.system().upper() == "LINUX":
			import grp,pwd

			gids = [g.gr_gid for g in grp.getgrall() if userName in g.gr_mem]
			gid = pwd.getpwnam(userName).pw_gid
			gids.append(grp.getgrgid(gid).gr_gid)
			return [grp.getgrgid(gid).gr_name for gid in gids]

	def getGidName(self, gid):
		"""
		Return gid name
		"""
		import grp
		myGrpInfo = grp.getgrgid(gid)
		if myGrpInfo:
			return myGrpInfo.gr_name
		else:
			return ""

	def buildHostId(self, host, region, opco):
		# returns hostid for a given host, region, opco
		return "".join([region, ".", opco, ".", host])

	def buildTenantId(self, host, dbTech, tenant):
		# returns tenantID for a given host and tenant, if tenant name can not be determined, port# should be used as tenant
		if not isinstance(tenant, str):
			return "".join([host, ".", dbTech, ".", repr(tenant)])
		else:
			return "".join([host, ".", dbTech, ".", tenant])

	# YAML
	def readYamlFile(self, fileName):
		'''	
		Load/Read yaml file, return as dict
		'''
		if self.isFileExists(fileName):
			with open(fileName) as f:
				myYamlData = yaml.safe_load(f)

			return myYamlData

	def writeYamlFile(self, fileName, data):
		'''	
		Write yaml file
		'''
		if not self.isFileExists(fileName):
			with open(fileName, 'w', encoding='utf8') as f:
				yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

	"""
	def getStartDateFromSched(self, schedule):
		myFrequency = schedule["freq"]
		if myFrequency.lower() == "daily":
			pass 
		if myFrequency.lower() == "weekly":
			if not("week" in schedule and "day" in schedule):
				raise ValueError("week/day key is required")
		if myFrequency.lower() == "quarterly":
			if not("month" in scheudle and week" in schedule and "day" in schedule):
				raise ValueError("month/weekday key is required")
		
		if myFrequency.lower() == "daily":
			# Date for Monday of this week
			return datetime.datetime.now() + datetime.timedelta(days=-datetime.datetime.now().weekday())
			# Date for Friday of this week
			return datetime.datetime.now()+datetime.timedelta(days= 4 - datetime.datetime.now().weekday())

		if myFrequency.lower() == "monthly":
			# we need week and day
			myWeek = schedule["week"]
			myDay = schedule["day"]
			myYear = datetime.datetime.now().year
			myMonth = datetime.datetime.now().month
			myStartDate = self.getDayOfWeekOfMonth(myDay,myYear,myMonth,myWeek)

		if myFrequency.lower() == "quarterly":
			# we need week and day
			myWeek = schedule["week"]
			myDay = schedule["day"]
			myQtrMonth = schedule["month"]

			myMonth = self.getNMonthOfQtr(currentMonth, nMonth):
			myYear = datetime.datetime.now().year
			myStartDate = self.getDayOfWeekOfMonth(myDay,myYear,myMonth,myWeek)

	today = datetime.datetimne.now()
	# date attribute
		>>> today.month
		6
		>>> today.weekday()
		1
		>>> today.year
		2019
		>>> today.day
		4
		>>> today.hour
		20
		>>> today.min
		datetime.datetime(1, 1, 1, 0, 0)
		>>> today.minute
		7
	# add or substract to date object
		>>> DT.datetime.now() - datetime.timedelta(days=1)
		datetime.datetime(2019, 6, 3, 21, 19, 31, 505220)
		>>> DT.datetime.now() - datetime.timedelta(hours=1)
		datetime.datetime(2019, 6, 4, 20, 19, 43, 469930)
		>>> DT.datetime.now() - datetime.timedelta(minutes=1)
		datetime.datetime(2019, 6, 4, 21, 18, 53, 158748)


	# print last Monday
	1.
		from datetime import date
		from dateutil.relativedelta import relativedelta, MO

		today = date.now()
		last_monday = today + relativedelta(weekday=MO(-1))
		print last_monday
	2. # will give you current week's Monday and Friday
		>>> datetime.datetime.now()+datetime.timedelta(days=-datetime.datetime.now().weekday())
		datetime.date(2019, 6, 3)
		>>> datetime.datetime.now().weekday()
		1
		>>> datetime.datetime.now()+datetime.timedelta(days= 5 - datetime.datetime.now().weekday())
		datetime.date(2019, 6, 8)
		>>> datetime.datetime.now()+datetime.timedelta(days= 4 - datetime.datetime.now().weekday())
		datetime.date(2019, 6, 7)
		>>>
	3. (will give u next monday date or today if today is Monday)
		>>> d = datetime.datetime.now().weekday()
		>>> datetime.datetime.now() + datetime.timedelta(days=(7-d)%7)
		datetime.datetime(2019, 6, 10, 21, 27, 3, 563038)

	# Add months to date
	from datetime import datetime
	from dateutil.relativedelta import relativedelta

	date_after_month = datetime.now()+ relativedelta(months=1)
	print 'Today: ',datetime.now().strftime('%d/%m/%Y')
	print 'After Month:', date_after_month.strftime('%d/%m/%Y')	
	"""
	def sendEmail(self, senderEmail, toRecipients, ccRecipients, bccRecipients, subject, body, bodyType, fileAttachment = None):
		"""
		Param:
			senderEmail: Tuple (name, email) For e.g. ('Notification Service', 'donotreply@marsh.com')
			toEmail: Recipients email "comma seerated"
		"""
		try:
			import email, smtplib
			from email import encoders
			from email.mime.base import MIMEBase
			from email.mime.multipart import MIMEMultipart
			from email.mime.text import MIMEText

			#print("Sender email    : ", senderEmail)
			#print("Recipient [TO]  : ", toRecipients)
			#print("Recipient [CC]  : ", ccRecipients)
			#print("Recipient [BCC] : ", bccRecipients)
			#print("Subject         : ", subject)

			mySenderEmail = email.utils.formataddr((senderEmail))
			myReceiverEmail = toRecipients
			myCCEmail = ccRecipients
			myBccEmail = bccRecipients

			message = MIMEMultipart()

			# processing attachment if passed
			if fileAttachment:
				# Open attached file in binary mode
				with open(fileAttachment, "rb") as attachment:
					# Add file as application/octet-stream
					# Email client can usually download this automatically as attachment
					part = MIMEBase("application", "octet-stream")
					part.set_payload(attachment.read())

				# Encode file in ASCII characters to send by email    
				encoders.encode_base64(part)

				# Add header as key/value pair to attachment part
				part.add_header(
					"Content-Disposition",
					f"attachment; filename= {self.getFileName(fileAttachment)}",
				)

				# adding attachment
				message.attach(part)

			# Add attachment to message and convert message to string
			message["Subject"] = subject
			message["From"] = mySenderEmail
			message["To"] = myReceiverEmail
			message["Cc"] = myCCEmail
			message["Bcc"] = myBccEmail  # Recommended for mass emails

			if bodyType == "html":
				message.attach(MIMEText(body, "html"))
			else:
				message.attach(MIMEText(body, "plain"))

			# sending email
			try:
				server = smtplib.SMTP(self.SMTP_SERVER)
				server.set_debuglevel(False) # show communication with the server
				server.sendmail(mySenderEmail, myReceiverEmail, message.as_string())
			finally:
				if "server" in locals():
					server.quit()

		except Exception as e:
			raise e

	@contextmanager
	def suppressStdout(self):
		"""
		supress stdout with contextmanager
		e.g.

		with self.supressStdOut():
			print('test') # all stdout is directed to /dev/null under this context

		print('pls show this') # this will be sent to stdput as we are out of above context
		"""
		with open(os.devnull, "w") as devnull:
			old_stdout = sys.stdout
			sys.stdout = devnull
			try:  
				yield
			finally:
				sys.stdout = old_stdout
	
	def measureMemUsage(func):
		"""A decorator to profile the usage of time and memory by a function"""
		import inspect
		measure_memory = partial(memory_usage, proc=-1, interval=0.2, timeout=1)
		@wraps(func)
		def wrapper(*args, **kwargs):        
			print("Before function <{}>, memory usage: {:.2f} MiB"
				.format(func.__name__, measure_memory()[0]))
			memUsageBeforeExec = measure_memory()[0]
			start = time.time()
			result = func(*args, **kwargs)
			end = time.time()
			print("After function <{}> done, memory usage: {:.2f} MiB"
				.format(func.__name__, measure_memory()[0]))

			memUsageAfterExec = measure_memory()[0]

			print("Function <{}> took {:.2f} s".format(func.__name__, end - start))

			meUsed = end - start

			return result
		return wrapper

	def releaseMemory(self):
		return
		#print("releasing memory")
		#import gc
		#gc.collect()
		#gc.garbage[:]

	def unzipFile(self, zipFile, extractPath):
		"""
		import zip file to an extract location
		"""
		if not self.isFileExists(zipFile):
			raise ValueError(f"zip file {zipFile} does not exists !!!")

		self.createDir(extractPath)

		if not self.isDirExists(extractPath):
			raise ValueError("target extract dir {extractPath} does not exists !!!")

		import zipfile
		zip_ref = zipfile.ZipFile(zipFile, 'r')
		zip_ref.extractall(extractPath)
		zip_ref.close()

	def deepDiff(self, source, target, excludeKeys=[]):
		"""
		Compares json dictionatries and returns the keys and value which is different
		for e.g.
		source = [{"security" : {"ip" : "127.0.0.1", "port" : 1500}}]
		target = [{"security" : {"ip" : "127.0.0.1", "port" : 15001, "test" : "Nothing"}}]
		deepDiff(source, target)
		
		Returns --> [{'security': {'test': (None <source value>, 'Nothing' <targetValue>), 'port': (1500 <source value>, 15001 <target vaue)}}]		

		"""
		
		if source == target:
			return None

		if type(source) != type(target) or type(source) not in [list, dict]:
			return (source, target)
		
		if type(source) == dict:
			diff = {}
			for key in source.keys() ^ target.keys():
				if key in excludeKeys:
					continue

				if key in source:
					diff[key] = (deepcopy(source[key]), None)
				else:
					diff[key] = (None, deepcopy(target[key]))

			for key in source.keys() & target.keys():
				if key in excludeKeys:
					continue
				next_d = self.deepDiff(source[key], target[key])
				if next_d is None:
					continue
				diff[key] = next_d
			
			return diff if len(diff) else None

		# must be list:
		diff = [None] * max(len(source), len(target))
		
		flipped = False
		
		if len(source) > len(target):
			flipped = True
			source, target = target, source
			for i, sourceVal in enumerate(source):
				diff[i] = self.deepDiff(target[i], sourceVal) if flipped else self.deepDiff(sourceVal, target[i])
		
			for i in range(len(source), len(target)):
				diff[i] = (target[i], None) if flipped else (None, target[i])

		return diff

	def isAppInstalledInLinuxOS(self, app):
		"""
		checks if a given application is installed
		"""
		try:
			cmd = "which {appName} 2>/dev/null".format(appName = app)
			if self.execOSCmdRetCode(cmd) == 0:
				return True
			else:
				return False

		except Exception as error:
			raise error

	def listAllLinuxProcess(self):
		"""
		Returns all process from a linux box with attribute
		"""
		# valid keys for process_iter
		# ['status', 'cpu_num', 'num_ctx_switches', 'pid', 'memory_full_info', 'connections', 'cmdline', 'create_time', 'ionice', 'num_fds', 'memory_maps', 'cpu_percent', 'terminal', 'ppid', 'cwd', 'nice', 'username', 'cpu_times', 'io_counters', 'memory_info', 'threads', 'open_files', 'name', 'num_threads', 'exe', 'uids', 'gids', 'cpu_affinity', 'memory_percent', 'environ']

		return list(psutil.process_iter(['pid','create_time','uids','gids','username','environ','cmdline','cpu_percent','memory_info','open_files']))

	def getAllContainers(self):
		"""
		returns all container details on host
		"""
		if not self.isAppInstalledInLinuxOS("docker"):
			return 

		import docker
	
		try:
			myOSDetails = self.getOsDetails()
			client = docker.from_env()
			allContainers = []
			for container in client.containers.list():
				try:
					osProcess = container.top()
					containerDetail={
						"id" : container.id,
						#"pidFromTop" : container.top()['Processes'],
						"pid" : container.attrs['State']['Pid'],
						"started" : container.attrs['State']['StartedAt'],
						#"created" : container.attrs['Id'],
						"binds" : container.attrs['HostConfig']['Binds'],
						"mounts" : container.attrs['Mounts'],
						"Path" : container.attrs['Path'],
						"processes" : container.top() if container.attrs['Path'].endswith("/docker-entrypoint.sh") else "",
						"Args" : container.attrs['Args'],
						"Status" : container.attrs['State']['Status'],
						"physMemoryLimitMB" : myOSDetails["phys_memory"].total/(1024*1024) if container.attrs['HostConfig']['Memory'] == 0 else container.attrs['HostConfig']['Memory'],
						"swapMemoryLimitMB" : myOSDetails["swap_memory"].total/(1024*1024) if container.attrs['HostConfig']['MemorySwap'] == 0 else container.attrs['HostConfig']['MemorySwap'],
						"physMemoryUsedMB" : container.attrs['HostConfig']['ShmSize']/(1024*1024),
						"cpuCount" : myOSDetails["cpu_count"] if container.attrs['HostConfig']['CpuCount'] == 0 else container.attrs['HostConfig']['CpuCount'],
					}
					if container.attrs['Path'] == "mongod":
						#this is mongo container, we need to find mongod.conf
						#print(container.attrs['Args'])
						containerDetail.update({"type" : "mongo"})
						#containerDetail.update({"pid" : container.attrs['State']["Pid"]})
						myMongoConf = container.attrs['Args'][1]
						# now we need to find relevant file which is bind to this config file
						#print(container.attrs['Mounts'])
						for bind_ in container.attrs['Mounts']:
							#print('bind',bind_)
							if bind_['Destination'] == myMongoConf:
								containerDetail.update({"confFile" : bind_["Source"]})
								#myMongodConfWPath = bind["source"]
								break
					elif container.attrs['Path'].endswith("/docker-entrypoint.sh")  and container.attrs["Arg"][0].lower() == "postgres":
						# this is postgres container
						containerDetail.update({"type" : "postgres"})
						#containerDetail.update({"confFile" : "".join([container.attrs['HostConfig']['Binds'][0].split(':')[1], "/postgresql.conf"]) })
						myPgConfFile = ""
						for env_ in container.attrs['Config']['Env']:
							if env_.split('=')[0].upper() == "PGDATA":
								myPGDataLoc = env_.split('=')[1]
								myPgConfFile = self.buildPath(myPGDataLoc, "postgresql.conf")
								break
						if not myPgConfFile:
							myPgConfFile = self.buildPath(container.attrs['HostConfig']['Binds'][0].split(':')[1], "postgresql.conf")

						containerDetail.update({"confFile" : myPgConfFile})
					else:
						containerDetail.update({"type" : "unknown","confFile" : "n/a"})

					#print("container >>> ")
					#print(json.dumps(containerDetail, indent=5))
					if containerDetail["type"] != "unknown":
						allContainers.append(containerDetail)

				except Exception as error:
					print(f"an error occurred parsing container detail for {container.id} >>> {error} !!!")
					# supressing error
			return allContainers
		except Exception as error:
			#raise error
			return f"error >>> {error}"

	def getContainers(self, dbTechnology):
		"""
		returns all container details on host
		"""
		if not self.isAppInstalledInLinuxOS("docker"):
			return 

		myContainersList = []
		myAllContainers = self.getAllContainers() 
		if not isinstance(myAllContainers, list):
			return myContainersList

		for container in self.getAllContainers():
			if 'type' in container and container['type'].lower() == dbTechnology.lower():
				myContainersList.append(container)

		return myContainersList

	def getOSUsersProcess(self, osUser, cmdLineKw = "all"):
		# Returns all process for a given osUser 
		# valid keys for process_iter
		# ['status', 'cpu_num', 'num_ctx_switches', 'pid', 'memory_full_info', 'connections', 'cmdline', 'create_time', 'ionice', 'num_fds', 'memory_maps', 'cpu_percent', 'terminal', 'ppid', 'cwd', 'nice', 'username', 'cpu_times', 'io_counters', 'memory_info', 'threads', 'open_files', 'name', 'num_threads', 'exe', 'uids', 'gids', 'cpu_affinity', 'memory_percent', 'environ']

		allProcesLists = []

		if self.getOSType().lower() == "linux":
			if not self.isLinuxOsUserExists(osUser):
				return []
			# user is valid/exists
			# retrieving all the processed owned by this process

			allUserProcesses = [proc.info for proc in psutil.process_iter(['pid','create_time','uids','gids','username','environ','cmdline','cpu_percent','memory_info','open_files']) if proc.username() == osUser]
			for proc in allUserProcesses:
				myProcess = {}
				if cmdLineKw.lower() != "all" :
					# checking if we have command line for this process
					if proc["cmdline"]:
						for line in proc["cmdline"]:
							if cmdLineKw in line:
								myProcess = {
									"pid" : proc["pid"],
									"gids" : proc["gids"],
									"uids" : proc["uids"],
									"user" : proc["username"],
									"createTime" : self.convertEpocToDateTime(proc["create_time"]) if not isinstance(proc["create_time"], datetime.datetime) else proc["create_time"],
									"cpuPercent" : proc["cpu_percent"],
									"memoryInfo" : proc["memory_info"],
									"openFiles" : proc["open_files"],
									"cmdLine" : proc["cmdline"]
								}
								break
						if myProcess:
							allProcesLists.append(myProcess)
					# need to filter the cmdlineKW
				else:
					myProcess = {
						"pid" : proc["pid"],
						"gids" : proc["gids"],
						"uids" : proc["uids"],
						"user" : proc["username"],
						"createTime" : self.convertEpocToDateTime(proc["create_time"]) if not isinstance(proc["create_time"], datetime.datetime) else proc["create_time"],
						"cpuPercent" : proc["cpu_percent"],
						"memoryInfo" : proc["memory_info"],
						"openFiles" : proc["open_files"],
						"cmdLine" : proc["cmdline"]
					}
					allProcesLists.append(myProcess)
		else:
			allUserProcesses = [proc.info for proc in psutil.process_iter(['pid','create_time','username','environ','cmdline','cpu_percent','memory_info']) if proc.username() == osUser]
			for proc in allUserProcesses:
				myProcess = {}
				if cmdLineKw.lower() != "all" :
					# checking if we have command line for this process
					if proc["cmdline"]:
						for line in proc["cmdline"]:
							if cmdLineKw in line:
								myProcess = {
									"pid" : proc["pid"],
									"user" : proc["username"],
									"createTime" : self.convertEpocToDateTime(proc["create_time"]) if not isinstance(proc["create_time"], datetime.datetime) else proc["create_time"],
									"cpuPercent" : proc["cpu_percent"],
									"memoryInfo" : proc["memory_info"],
									"cmdLine" : proc["cmdline"]
								}
								break
						if myProcess:
							allProcesLists.append(myProcess)
					# need to filter the cmdlineKW
				else:
					myProcess = {
						"pid" : proc["pid"],
						"user" : proc["username"],
						"createTime" : self.convertEpocToDateTime(proc["create_time"]) if not isinstance(proc["create_time"], datetime.datetime) else proc["create_time"],
						"cpuPercent" : proc["cpu_percent"],
						"memoryInfo" : proc["memory_info"],
						"cmdLine" : proc["cmdline"]
					}
					allProcesLists.append(myProcess)
		return allProcesLists

	def getAliveDBProcesses(self):
		"""
		Returns all alive database process detail 
		usage: getAliveDBProcesses()
		arguments: none
		
		# following lines are not part of help, its comment of previous code

		import getpass, psutil

		proc = psutil.process_iter()
		for x in proc:
			mycmdline = x.cmdline()
			isMongoProcess = ["mongo" for line in mycmdline if "mongod" in line]
			if isMongoProcess:
				isParent = True if x.ppid() == 1 else False
				if isParent:
					print(f'Mongo pid: {x.pid}')
					print(f'	username: {x.username()}')
					print(f'	cmdline: {x.cmdline()}')
					print(f'	started @ : {x.create_time()}')
					print(f'	total connections : {x.connections() if x.username() == getpass.getuser() else -1}')
					print(f'	status: {x.status()}')
					print(f'	exe: {x.exe()}')
					print(f'	memory_info: {x.memory_info()}')
					print(f'	memory%: {x.memory_percent()}')
					print(f'	Is Running: {x.is_running()}')
					print(f'	env: {x.environ() if x.username() == getpass.getuser() else "n/a"}')
		"""
		allDBProcLists = []
		myAllMongodDockerPids = []

		# checking for database in docker
		if self.isAppInstalledInLinuxOS("docker"):
			# docker file presents, scanning all Mongo docker container
			allMongodContainers = self.getContainers(self.Globals.DB_TYPE_MONGO.lower())
			#self.LOGGER.debug(f"containers discovered >>> {allMongodContainers}")

			if isinstance(allMongodContainers, list):
				for container in allMongodContainers:
					myPidInfo = self.getPidInfo(container["pid"])
					allDBProcLists.append({
						"dbType" : self.Globals.DB_TYPE_MONGO,
						"pid" : container["pid"],
						"configFile" : container["confFile"],
						"started" : container["started"],
						"createTime" : container["started"],
						"docker" : True,
						"owner" : myPidInfo["username"] if myPidInfo and "username" in myPidInfo else "n/a",
						"binds" : container["binds"],
						"mounts" : container["mounts"],
						"cmdLine" : " ".join([container["Path"], container["Args"][0], container["confFile"]]),
						"dockerConfig" : {
							"physMemLimitMB" : container["physMemoryLimitMB"],
							"physMemUsedMB" : container["physMemoryUsedMB"],
							"swapMemLimitMB" : container["swapMemoryLimitMB"],
							"cpuCount" : container["cpuCount"]
						}
					})
				
			myAllMongodDockerPids = [mongodDockerProd['pid'] for mongodDockerProd in allDBProcLists]

		# loading all non docker mongod config files
		for proc in psutil.process_iter():
			# we are interested in parent pid
			isParentPid = True if proc.ppid() == 1 else False
			if isParentPid == False:
				# not parent pid, skipping this process
				continue

			#checking if this pid is counted as docker as db process in mongod will appear at host
			if  proc.pid in myAllMongodDockerPids:
				# ignoring this pid if it is docker mongod pid and is being recorded as docker mongod
				#self.LOGGER.debug(f"Pid {mongodProc['pid']} is in container, skipping")
				continue

			# we have parent pid
			myProcDBType = ""
			myCmdLine = proc.cmdline()
			# checking for mongo
			#if "mongod" in myCmdLine[0] and myCmdLine[0].endswith("mongod") and myCmdLine[1].replace(" ", "") == "-f" :
			if myCmdLine[0].endswith("mongod") and myCmdLine[1].replace(" ", "") == "-f" :
				myProcDBType = self.Globals.DB_TYPE_MONGO
				myConfigFile = myCmdLine[2]
			#elif "postgres" in myCmdLine[0] and myCmdLine[1].replace(" ", "") == "-D":
			elif myCmdLine[0].endswith("postgres") and myCmdLine[1].replace(" ", "") == "-D":
				myConfigFile = self.buildPath(myCmdLine[2],"postgresql.conf")
				myProcDBType = self.Globals.DB_TYPE_POSTGRES
			else:
				# this is neither Mongo/Postgres parent process, skipping processing this proc
				continue
			# adding non docker db processes
			allDBProcLists.append({
				"dbType" : myProcDBType,
				"pid" : proc.pid,
				"docker" : False,
				"cmdLine" : myCmdLine,
				"configFile" : myConfigFile,
				"createTime" : self.convertEpocToDateTime(proc.create_time()),
				"owner" : proc.username(),
				"status" : proc.status(),
				"cpuPercent" : proc.cpu_percent(),
				"memoryInfo" : proc.memory_info(),
				"memoryPercent" : proc.memory_percent()
			})	

		# updating other attributes
		for proc_ in allDBProcLists:
			myPort = myBindIP = "" 
			myConfigData = {}

			if proc_["dbType"] == self.Globals.DB_TYPE_MONGO:
				#myConfigFile = proc_["cmdLine"][2]
				#try:
				myConfigData = self.readYamlFile(proc_["configFile"])
				if myConfigData:
					if "net" in myConfigData and "port" in myConfigData["net"]:
						myPort =  myConfigData["net"]["port"]
					if "net" in myConfigData and "bindIp" in myConfigData["net"]:
						myBindIP = myConfigData["net"]["bindIp"].split(",")
				# if this is docker, we want to update mongod log and audit log location
				if proc_["docker"] == True:
					# mongod log file
					#print("mounts: ",proc_["mounts"])
					myDestMongodLogLoc = self.getFileDirName(myConfigData['systemLog']['path'])
					myDestAuditLogLoc = self.getFileDirName(myConfigData['auditLog']['path'])
					myMongodLogFile = self.getFileName(myConfigData['systemLog']['path'])
					myAuditBsonFile = self.getFileName(myConfigData['auditLog']['path'])
					myDestDBPath = myConfigData['storage']['dbPath'] if "storage" in myConfigData and "dbPath" in myConfigData['storage'] else "/data/db"
					myLogPath = myAuditLogPath = myDataLoc = ""
					#print("dest log loc:",myDestMongodLogLoc)
					#print("dest audit log loc:",myDestAuditLogLoc)
					#print("dest db loc:",myDestDBPath)
					for bind in proc_["mounts"]:
						if bind["Type"] == "bind":
							if bind["Destination"].strip() == myDestMongodLogLoc.strip():
								myLogPath = self.buildPath(bind["Source"], myMongodLogFile)
							elif bind["Destination"].strip() == myDestAuditLogLoc.strip():
								myAuditLogPath = self.buildPath(bind["Source"], myAuditBsonFile)
							elif bind["Destination"].strip() == myDestDBPath.strip():
								myDataLoc = bind["Source"]
					# checking if we have resolved all the keys
					#print('log loc:', myLogPath)
					#print('audit log loc: ', myAuditLogPath)
					#print('db loc: ', myDataLoc)

					if (not myLogPath) or (not myAuditLogPath) or (not myDataLoc):
						raise ValueError("couldnt resolve mongod log/audit/db data location !!!")
					# updating this information to config file
					myConfigData["systemLog"].update({"path" : myLogPath})
					myConfigData["auditLog"].update({"path" : myAuditLogPath})
					myConfigData["storage"].update({"dbPath" : myDataLoc})

					# removing mounts and binds
					#proc_.pop("mounts",None) if "mounts" in proc_ else ""
					proc_.pop("bind",None) if "bind" in proc_ else ""
					proc_.update({"status" : self.Globals.success})
				"""
				except Exception as error:
					proc_.update({
						"status" : self.Globals.unsuccess, 
						"message" : f"an error occurred while updating other attributes to this process >>> {error}",
						"bindIp" : myBindIP,
						"port" : myPort
					})
					continue
				"""
			elif proc_["dbType"] == self.Globals.DB_TYPE_POSTGRES:
				#myConfigFile = self.buildPath(proc_["cmdLine"][2],"postgresql.conf")
				myConfigData = self.readConfigTextFile(proc_["configFile"])
				if myConfigData:
					if "port" in myConfigData:
						myPort = myConfigData["port"]
					if "listen_addresses" in myConfigData:
						myBindIP =  myConfigData["listen_addresses"].split(",")

				#checking for pgpass file
				myPGhbaConfigFile = self.buildPath(self.getFileDirName(proc_["configFile"]),"pg_hba.conf")
				if self.isFileExists(myPGhbaConfigFile):
					myPGhbaConfigData = self.readPGhbaConfigFile(myPGhbaConfigFile)
				else:
					myPGhbaConfigData = []

			# updating bindIp,port,configData if found
			proc_.update({
				"bindIp" : myBindIP,
				"port" : myPort,
				#"configFile" : myConfigFile,
				"configData" : myConfigData,
				"hbaConfigFile" : myPGhbaConfigFile, 
				"hbaConfData" : myPGhbaConfigData
			})

		return allDBProcLists
	
	def listProcDetail4KW(self, cmdLineKW):
		# valid keys for process_iter
		# ['status', 'cpu_num', 'num_ctx_switches', 'pid', 'memory_full_info', 'connections', 'cmdline', 'create_time', 'ionice', 'num_fds', 'memory_maps', 'cpu_percent', 'terminal', 'ppid', 'cwd', 'nice', 'username', 'cpu_times', 'io_counters', 'memory_info', 'threads', 'open_files', 'name', 'num_threads', 'exe', 'uids', 'gids', 'cpu_affinity', 'memory_percent', 'environ']

		myKWProc = []
		if psutil.LINUX:
			allProcess = list(psutil.process_iter(['pid','create_time','uids','gids','username','environ','cmdline','cpu_percent','memory_info','open_files']))
			for proc in allProcess:
				if proc.info["cmdline"]:
					myProcess = {}
					for line in proc.info["cmdline"]:
						if cmdLineKW in line:
							myProcess = {
								"pid" : proc.info["pid"],
								"gids" : proc.info["gids"],
								"uids" : proc.info["uids"],
								"user" : proc.info["username"],
								"createTime" : self.convertEpocToDateTime(proc.info["create_time"]) if not isinstance(proc.info["create_time"], datetime.datetime) else proc.info["create_time"],
								"cpuPercent" : proc.info["cpu_percent"],
								"memoryInfo" : proc.info["memory_info"],
								"openFiles" : proc.info["open_files"]
							}
							break
					if myProcess:
						myProcess.update({"cmdLine" : proc.info["cmdline"]})
						myKWProc.append(myProcess)
		else:
			allProcess = list(psutil.process_iter(['pid','create_time','username','environ','cmdline','cpu_percent','memory_info']))
			for proc in allProcess:
				if proc.info["cmdline"]:
					myProcess = {}
					for line in proc.info["cmdline"]:
						if cmdLineKW in line:
							myProcess = {
								"pid" : proc.info["pid"],
								"user" : proc.info["username"],
								"createTime" : self.convertEpocToDateTime(proc.info["create_time"]) if not isinstance(proc.info["create_time"], datetime.datetime) else proc.info["create_time"],
								"cpuPercent" : proc.info["cpu_percent"],
								"memoryInfo" : proc.info["memory_info"]							
							}
					if myProcess:
						myProcess.update({"cmdLine" : proc.info["cmdline"]})
						myKWProc.append(myProcess)

		return myKWProc

	def getProcessDetail(self, pids):
		"""
		Return process detail for a given pid
		"""
		allProcessDetails = []
		if not isinstance(pids, list):
			pidLists = [pids]
		else:
			pidLists = pids

		for pid in pidLists:
			process = psutil.Process(pid)
			procDetail = process.as_dict()
			procDetail.update({
				'create_time_dt' : self.convertEpocToDateTime(procDetail['create_time']),
				'create_time_epoch' : procDetail['create_time']
			})
			procDetail.pop('create_time')
			allProcessDetails.append(procDetail)

		return allProcessDetails

	# LDAP (Ad/CTFY groups) methods
	def getADGrpUserDetail(self, grpName):
		"""
		return userid, username for a given ad group [{"userId" : "", "userName" : ""}]
		"""
		myQryResult = \
		self.fetchDataFromOsCmdResult(\
			self.execOSCmdRetResult(self.Globals.OS_CMD["GET_CTFY_MEMBER"].format(ctfy_grp = grpName)))

		myRoleUsers = []
		for user in myQryResult:
			myUserId = user.split("@")[0]
			myUserName = self.fetchDataFromOsCmdResult(\
				self.execOSCmdRetResult(self.Globals.OS_CMD["GET_MEMBER_NAME"].format(userid = myUserId)))
			if myUserName:
				myRoleUsers.append({"userId" : myUserId, "userName" : myUserName[0], "scanDate" : self.getCurrentDate(), "comments" : ""})

		return myRoleUsers

	def getUserAdGrp(self, networkId):
		"""
		returns list of adgroup user is part of ( we need to replace this with module ldap3)
		"""
		myAllGrp = self.fetchDataFromOsCmdResult(self.execOSCmdRetResult(self.Globals.OS_CMD["GET_USER_GRP_NAME"].format(userid = networkId)))
		if myAllGrp:
			return [grp.split("/")[-1:][0] for grp in myAllGrp]

	def getADGrpUserName(self, networkId):
		"""
		returns AD group user name for a given network id
		"""
		myUserName = self.fetchDataFromOsCmdResult(self.execOSCmdRetResult(self.Globals.OS_CMD["GET_MEMBER_NAME"].format(userid = networkId)))

		if myUserName:
			return myUserName[0]

	def getAdGroupMemberIds(self,adGroupList):
		"""
		returns all member id for a given ad group
		"""
		if not isinstance(adGroupList, list):
			adGroupList = [adGroupList]

		myAdGroupIdList = []
		for grp in adGroupList:
			try:
				myCtfyQryResult = \
					self.fetchDataFromOsCmdResult(\
						self.execOSCmdRetResult(self.Globals.OS_CMD["GET_CTFY_MEMBER"].format(ctfy_grp = grp)))
				#Building member ids in a list
				myAdGroupMemberIdList = [user.split("@")[0] for user in myCtfyQryResult]
				[myAdGroupIdList.append(adminId) for adminId in myAdGroupMemberIdList]

			except Exception as error:
				pass

		# removing duplicate from list
		return list(set(myAdGroupIdList))

	def isAdGroup(self, adGrpName):
		"""
		checks if given id is ad or ctfy group
		"""
		try:
			#if self.getAdGroupMemberIds([adGrpName]):
			#with self.suppressStdout():
			retval = self.execOSCmdRetCode(self.Globals.OS_CMD["GET_CTFY_MEMBER"].format(ctfy_grp = adGrpName))
			
			#print('retval',retval)
			if retval == 0: ## executed successfully
				return True
			else:
				return False
		except Exception as error:
			raise error

	#
	def getADGrpFromMongoRole(self, mongoRole):
		"""
		returns ad group name from mongo role, if role is linked to AD group
		""" 
		# retrieving role name
		myRoleSplitList = mongoRole.split(",")
		# find string index contains "CN="
		myPos = self.getPartialStrInList("CN", myRoleSplitList)

		if myPos:
			myCnRoleSplitList = myRoleSplitList[myPos[0]].split("=")
			#myPos = self.getPartialStrInList("MAR", myRoleSplitList)
			myRole = myCnRoleSplitList[1] # 2nd value

			return myRole
		else:
			print("found role linked to AD group, couldn't find 'CN' kw in role >>> {role}".format(role = mongoRole))
			return

	def isValidLdapGroup(self, groupName):
		"""
		checks if this is valid ldap group
		"""
		if self.getLdapGroupDetails(groupName):
			return True
		else:
			return False

	def getLdapGroupDetails(self, groupName, ldap):
		"""
		return AD group details (via ldap3 module)
		arguments: groupName
		"""
		try:
			if not groupName:
				return {}

			from ldap3 import Server, Connection, AUTO_BIND_NO_TLS, SUBTREE, BASE, ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, ObjectDef, AttrDef, Reader, Entry, Attribute, OperationalAttribute, ObjectDef, AttrDef, Reader, Entry, Attribute, OperationalAttribute

			"""
			if ldap == "default":
				if not self.LDAP_SERVER:
					raise ValueError(f"No ldap server is available !!!")
				myLdapServer = self.LDAP_SERVER
				myLdapServerPort = int(self.LDAP_SERVER_PORT)
				myLdapUser = self.LDAP_USER
				myLdapPass == self.LDAP_USER_PASS
			else:
			"""
			from com.mmc.common.security import Security
			sec = Security()

			myLdapServer = ldap["server"].split(":")[0]
			myLdapServerPort = int(ldap["server"].split(":")[1])
			myLdapUser = sec._Security__decryptText(ldap["id"])
			myLdapPass = sec._Security__decryptText(ldap["enc"])
			#myBaseDC =  ",".join(["".join(["DC=",dc]) for dc in myLdapServer.split(".")[-2:]])
			#myBaseDC = "DC=corp,DC=mmco,DC=int"

			#self.LOGGER.info(f"ldap info to be used >>> {myLdapServer}, {myLdapServerPort}, {myBaseDC}")
			del sec

			if not self.isPortOpen(myLdapServer, myLdapServerPort):
				raise ValueError(f"Ldap server {myLdapServer} port {myLdapServerPort} is not open ")

			server = Server(myLdapServer, port = myLdapServerPort, use_ssl=False, get_info='ALL')			

			with Connection(server, auto_bind=AUTO_BIND_NO_TLS, user = myLdapUser, password = myLdapPass, auto_referrals=False) as conn:
				for ou in self.ADGRP_OU_LIST:
					myBaseDn = "".join([ou,",", ldap["baseDC"]])
					mySearchFilter=f'(&(objectClass=GROUP)(cn={groupName}))'
					attr=[ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES]
					scope=SUBTREE
					limit=0
					#print(f"dn >> {myBaseDn} filter >> {mySearchFilter} attr >> {attr}")
					#print(f"searching {groupName} with arg >>> search base >> {myBaseDn}, search filter >> {mySearchFilter}")
					if conn.search(search_base = myBaseDn, search_filter = mySearchFilter, search_scope = scope, attributes = attr, size_limit = limit):
						#print(f"search filter {mySearchFilter} in base dn >>> {myBaseDn}, result : found")
						#print("found")
						break

				myGrpDetails = json.loads(conn.response_to_json())
				#print(f"grp details found >>> {myGrpDetails}")

				if myGrpDetails and "entries" in myGrpDetails and myGrpDetails["entries"] and "attributes" in myGrpDetails["entries"][0] and myGrpDetails["entries"][0]["attributes"]:
					return {"attributes" : myGrpDetails["entries"][0]["attributes"], "dn" : myGrpDetails["entries"][0]["dn"]}
				else:
					return {}

				# returning an array with 2 key value attributes (list) and dn (string)
				"""
				[
					{
					"attributes": {
						"cn": "GLB-MER-MongoDBAs-ServerAdmin-S-G",
						"dSCorePropagationData": [
							"2019-02-19 21:51:56+00:00",
							"2019-01-17 16:16:05+00:00",
							"1601-01-01 00:04:17+00:00"
						],
						"description": [
							"CO1267455 - DBA"
						],
						"distinguishedName": "CN=GLB-MER-MongoDBAs-ServerAdmin-S-G,OU=Mercer,OU=MongoDB,OU=Enterprise Systems,DC=corp,DC=mmco,DC=int",
						"groupType": -2147483646,
						"instanceType": 4,
						"member": [
							"CN=U1073575_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int",
							"CN=U847320_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int",
							"CN=U842533_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int",
							"CN=U824873_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int",
							"CN=U650981_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int",
							"CN=U1097312_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int",
							"CN=U782302_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int",
							"CN=U1052712_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int",
							"CN=U851090_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int",
							"CN=U1007198_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int",
							"CN=U1081283_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int",
							"CN=U651739_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int",
							"CN=U1068388_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int"
						],
						"name": "GLB-MER-MongoDBAs-ServerAdmin-S-G",
						"objectCategory": "CN=Group,CN=Schema,CN=Configuration,DC=mmco,DC=int",
						"objectClass": [
							"top",
							"group"
						],
						"objectGUID": "{58c64bbe-183d-4600-b61d-1d9aadcfcb58}",
						"objectSid": "S-1-5-21-1877973003-1762826398-3036156396-341002",
						"sAMAccountName": "GLB-MER-MongoDBAs-ServerAdmin-S-G",
						"sAMAccountType": 268435456,
						"uSNChanged": 260368783,
						"uSNCreated": 138993194,
						"whenChanged": "2020-12-14 09:55:38+00:00",
						"whenCreated": "2018-10-10 12:00:19+00:00"
					},
					"dn": "CN=GLB-MER-MongoDBAs-ServerAdmin-S-G,OU=Mercer,OU=MongoDB,OU=Enterprise Systems,DC=corp,DC=mmco,DC=int"
					}
				]
				"""
		except Exception as error:
			raise error

	def getLdapUserDetails(self, userSearchAttr, attrValue, ldap, returnValue = "default"):
		"""
		return AD group details
		Arguments:
			userSearchAttr:
				userDN : exact DN with OU, w/o DC (better to use networkid/userid/email)
				networkId : network id (for e.g. U11111) 
				employeeId: peoplesoft id (For e.g. 11111)
				emailId: email id of an user
			attrValue: value of search attribute (for e.g. if userSearchAttr = "networkId" then attrValue will be networkId value to be searched)
			returnValue: key pair values need to be returned, default is 'default' i.e. all attributes
		"""
		try:
			validUsrSearchAttr = ["userDN","networkId","employeeId","emailId"]
			validReturnValue = ["default","networkId","name","location","email","contact#","createdOn","dn","cn","memberOf","memberOfDn"]
			myReturnValueArgList = returnValue.split(",")

			if not userSearchAttr in validUsrSearchAttr:
				raise ValueError(f"User search attribute arg must be from this list {validUsrSearchAttr}, got {userSearchAttr} !!!")

			invalidRetVal = [ret for ret in myReturnValueArgList if ret.lower() not in [ret_.lower() for ret_ in validReturnValue]]

			if invalidRetVal:
				raise ValueError(f"Invalid return value {invalidRetVal}, valid values (any/all) >>> {validReturnValue} !!!")

			from ldap3 import Server, Connection, AUTO_BIND_NO_TLS, SUBTREE, BASE, ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, ObjectDef, AttrDef, Reader, Entry, Attribute, OperationalAttribute, ObjectDef, AttrDef, Reader, Entry, Attribute, OperationalAttribute

			from com.mmc.common.security import Security
			sec = Security()
			myLdapServer = ldap["server"].split(":")[0]
			myLdapServerPort = int(ldap["server"].split(":")[1])
			myLdapUser = sec._Security__decryptText(ldap["id"])
			myLdapPass = sec._Security__decryptText(ldap["enc"])
			#myBaseDC =  ",".join(["".join(["DC=",dc]) for dc in myLdapServer.split(".")[-2:]])

			del sec

			if not self.isPortOpen(myLdapServer, myLdapServerPort):
				raise ValueError(f"Ldap server {myLdapServer} port {myLdapServerPort} is not open ")

			server = Server(myLdapServer, port = myLdapServerPort, use_ssl=False, get_info='ALL')			

			#server = Server(self.LDAP_SERVER, port = self.LDAP_SERVER_PORT, use_ssl=False, get_info='ALL')
			
			with Connection(server, auto_bind=AUTO_BIND_NO_TLS, user = myLdapUser, password = myLdapPass, auto_referrals=False) as conn:
				attr=[ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES]
				scope=SUBTREE
				limit=0

				if userSearchAttr == "userDN":
					mySearchDn = "".join([attrValue,",", ldap["baseDC"]])
					mySearchFilter=f'(objectClass=PERSON)'

					#print(f"search_base : {mySearchDn}, search_filter : {mySearchFilter}")

					if conn.search(search_base = mySearchDn, search_filter = mySearchFilter, search_scope = scope, attributes = attr, size_limit = limit):
						myUserDetails = json.loads(conn.response_to_json())
						return {"attributes" : myUserDetails["entries"][0]["attributes"], "dn" : myUserDetails["entries"][0]["dn"]}
					else:
						return {}

				#mySearchDn = "".join([self.ADUSER_OU, ",", self.BASE_DC])
				if userSearchAttr == "networkId":
					mySearchFilter=f'(&(objectClass=PERSON)(objectClass=user)(sAMAccountName={attrValue}))'

				elif userSearchAttr == "employeeId":
					mySearchFilter=f'(&(objectClass=PERSON)(objectClass=user)(employeeNumber={attrValue}))'

				elif userSearchAttr == "emailId":
					mySearchFilter=f'(&(objectClass=PERSON)(objectClass=user)(mail={attrValue}))'

				myUserDetails = {}

				for adUserOU in self.ADUSER_OU_LIST:
					mySearchDn = "".join([adUserOU, ",", ldap["baseDC"] ])
					#print(f"searchAttr: {userSearchAttr}, value : {attrValue}, search_base : {mySearchDn}, search_filter : {mySearchFilter}")
					# we need try/catch for any possible error which might occur during search
					try:
						if conn.search(search_base = mySearchDn, search_filter = mySearchFilter, search_scope = scope, attributes = attr, size_limit = limit):
							myUserDetails = json.loads(conn.response_to_json())
							break
					except Exception as error:
						pass
				
				"""
				# results returnes
				{
					"attributes": {
						"accountExpires": "9999-12-31 23:59:59.999999",
						"cn": "U1101345_app",
						"codePage": 0,
						"countryCode": 0,
						"dSCorePropagationData": [
							"1601-01-01 00:00:00+00:00"
						],
						"description": [
							"CO1719494 - Operating Company: Mercer. Role: Server Application Support. Region: APAC. AMSI -DBA"
						],
						"displayName": "Pandey, Rakesh",
						"distinguishedName": "CN=U1101345_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int",
						"givenName": "Rakesh",
						"instanceType": 4,
						"lastLogonTimestamp": "2020-12-19 00:30:22.410751+00:00",
						"lockoutTime": "1601-01-01 00:00:00+00:00",
						"memberOf": [
							"CN=GLB-MER-MongoDBAs-ServerAdmin-S-G,OU=Mercer,OU=MongoDB,OU=Enterprise Systems,DC=corp,DC=mmco,DC=int"
						],
						"name": "U1101345_app",
						"objectCategory": "CN=Person,CN=Schema,CN=Configuration,DC=mmco,DC=int",
						"objectClass": [
							"top",
							"person",
							"organizationalPerson",
							"user"
						],
						"objectGUID": "{2f3f0b13-b36f-47bd-becc-f9c80f72dbb4}",
						"objectSid": "S-1-5-21-1877973003-1762826398-3036156396-407035",
						"primaryGroupID": 513,
						"pwdLastSet": "1601-01-01 00:00:00+00:00",
						"sAMAccountName": "U1101345_app",
						"sAMAccountType": 805306368,
						"sn": "Pandey",
						"uSNChanged": 261233722,
						"uSNCreated": 261198521,
						"userAccountControl": 512,
						"userPrincipalName": "U1101345_app@corp.mmco.int",
						"whenChanged": "2020-12-19 00:41:07+00:00",
						"whenCreated": "2020-12-18 19:07:15+00:00",
						"zzAccountType": 3,
						"zzEmail": "rakesh.pandey@mmc.com",
						"zzEmployeeID": "1101345"
					},
					"dn": "CN=U1101345_app,OU=Application Support,OU=Users - Support,OU=Administrative,DC=corp,DC=mmco,DC=int"
				}
				"""
				myResponse = {}
				if myUserDetails:

					if "default" in myReturnValueArgList:
						#print(f'user details >>> {myUserDetails}')
						#if myUserDetails and myUserDetails["entries"]:
						if myUserDetails and "entries" in myUserDetails and myUserDetails["entries"] and "attributes" in myUserDetails["entries"][0]:
							myResponse = {"attributes" : myUserDetails["entries"][0]["attributes"], "dn" : myUserDetails["entries"][0]["dn"]}
						return myResponse
					
					#print(f"userDetails >>> {myUserDetails}")

					if myUserDetails and "entries" in myUserDetails and myUserDetails["entries"] and "attributes" in myUserDetails["entries"][0]:
						myRawData = myUserDetails["entries"][0]["attributes"]
						myParentData = {}
					else:
						return myResponse

					# checking if we have zzEmployeeID to fetch parent data, if id ends with _app, it might have zzemployeeID reference to its parent data	
					if "zzEmployeeID" in myRawData:
						myAdUserData = self.getLdapUserDetails("employeeId", myRawData["zzEmployeeID"], ldap)
						if myAdUserData and "attributes" in myAdUserData:
							myParentData = myAdUserData["attributes"]

					for val in myReturnValueArgList:
						#"networkId","name","location","email","contact#","dn","cn","memberOf","memberOfDn"
						if val.lower() == "networkid":
							myResponse.update({"networkId" : myRawData["sAMAccountName"] if "sAMAccountName" in myRawData else ""})
						if val.lower() == "name":
							myResponse.update({"name" : myRawData["displayName"]})
						if val.lower() == "location":
							if "physicalDeliveryOfficeName" in myRawData:
								myResponse.update({"location" : myRawData["physicalDeliveryOfficeName"] })
							else:
								myResponse.update({"location" : "" })

							if not myResponse["location"]:
								# location not found trying from parent data
								if "physicalDeliveryOfficeName" in  myParentData:
									myResponse.update({"location" : myParentData["physicalDeliveryOfficeName"] })

						if val.lower() == "email":
							#myResponse.update({"email" : myRawData["userPrincipalName"] if "userPrincipalName" in myRawData else ""})
							if "mail" in myRawData:
								myResponse.update({"email" : myRawData["mail"]})
							elif "zzEmail" in myRawData:
								myResponse.update({"email" : myRawData["zzEmail"]})
							else:
								myResponse.update({"email" : ""})

							# retrieving data from parent data if this attribute is not found
							if ("email" in myResponse and not myResponse["email"]) or ("email" not in myResponse):
								if "mail" in myParentData:
									myResponse.update({"email" : myParentData["mail"]})
								else:
									myResponse.update({"email" : ""})

						if val.lower() == "contact#":
							if "mobile" in myRawData:
								myResponse.update({"contact#" : myRawData["mobile"]})
							elif "telephoneNumber" in myRawData:
								myResponse.update({"contact#" : myRawData["telephoneNumber"]})
							else:
								myResponse.update({"contact#" : ""})

							# retrieving data from parent data if this attribute is not found
							if not myResponse["contact#"]:
								if "mobile" in myParentData:
									myResponse.update({"contact#" : myParentData["mobile"]})
								elif "telephoneNumber" in myParentData:
									myResponse.update({"contact#" : myParentData["telephoneNumber"]})

						if val.lower() == "cn":
							myResponse.update({"cn" : myRawData["cn"] if "cn" in myRawData else ""})
						if val.lower() == "dn":
							myResponse.update({"dn" : myRawData["distinguishedName"] if "distinguishedName" in myRawData else ""})							
						if val.lower() == "memberof":
							myResponse.update({"memberOf" : [memberOf.split(",")[0].replace("CN=","") for memberOf in myRawData["memberOf"]] if "memberOf" in myRawData else ""})							
						if val.lower() == "memberofdn":
							myResponse.update({"memberOfDn" : myRawData["memberOf"] if "memberOf" in myRawData else ""})
						if val.lower() == "createdon":
							myResponse.update({"createdOn" : self.convStr2DateViaParser(myRawData["whenCreated"]) if "whenCreated" in myRawData else ""})
				else:
					myResponse = {}
				return myResponse

		except Exception as error:
			raise error

	def getLdapGroupCompInfo(self, groupName, ldap, comp = 'default'):
		"""
		return AD group component informarion
		arguments:
			groupName: ad group name
			comp : valid values --> ['all','group_dn','group_cn','group_name','group_misc','member_dn','member_cn','member_details','member_of']
		"""
		try:
			validComp = ['default','group_dn','group_cn','group_name','group_misc','member_dn','member_cn','member_details','member_of']
			myCompArgList = comp.split(",")

			invalidComp = [comp for comp in myCompArgList if comp.lower() not in [valComp.lower() for valComp in validComp]]

			if invalidComp:
				raise ValueError(f"Invalid comp {invalidComp}, valid values (any/all) >>> {validComp} !!!")
			"""
			if comp not in validComp:
				raise ValueError(f'Invaid component {comp}, valid comp value ${validComp} !!!')
			"""
			myGroupCompInfo = {}
			myGrpDetails = self.getLdapGroupDetails(groupName, ldap)
			if not myGrpDetails:
				return myGroupCompInfo

			if comp.lower() == 'default': 
				return myGrpDetails

			# user has passed the custom comp (not all)

			for comp_ in myCompArgList:
				if comp_.lower() == 'group_dn':
					myGroupCompInfo.update({"dn" : myGrpDetails["attributes"]["distinguishedName"]})

				if comp_.lower() == 'group_cn':
					myGroupCompInfo.update({"cn" : myGrpDetails["attributes"]["cn"]})

				if comp_.lower() == 'group_name':
					myGroupCompInfo.update({"name" : myGrpDetails["attributes"]["name"]})

				if comp_.lower() == 'member_dn':
					if "member" in myGrpDetails["attributes"] :
						myGroupCompInfo.update({"member_dn" : myGrpDetails["attributes"]["member"]})
					else:
						myGroupCompInfo.update({"member_dn" : []})

				if comp_.lower() == 'member_cn':
					if "member" in myGrpDetails["attributes"] :
						myGroupCompInfo.update({"member_cn" : [member.split(",")[0].upper().replace("CN=","") for member in myGrpDetails["attributes"]["member"]]})
					else:
						myGroupCompInfo.update({"member_cn" : []})

				if comp_.lower() == 'member_details':
					if "member" in myGrpDetails["attributes"]:
						
						myAllMemberDN = [userDN for userDN in myGrpDetails["attributes"]["member"]]
						myAllMemberDetails = []
						# we will process using network id and if not found for any dn, will switch to employeeid for remaining dn
						
						for dn in myAllMemberDN:
							cn = [elem.replace("CN=","").replace("\\","") for elem in dn.split(",") if not(elem.startswith("OU") or elem.startswith("DC"))]
							cn = ",".join(cn)

							myMemberDetails = self.getLdapUserDetails('networkId',cn, ldap, "networkId,name,location,email,contact#,dn,cn,memberOf,memberOfDn")
							# checking if we got the details
							if not myMemberDetails:
								# did not find member details, switching to employee id
								myMemberDetails = self.getLdapUserDetails('employeeId',cn,ldap, "networkId,name,location,email,contact#,dn,cn,memberOf,memberOfDn")
								if not myMemberDetails:
									# exhausted finding member details, constructing one
									myMemberDetails = {
										"networkId" : cn, "name" : cn.replace("\\",""), 
										"location" : "", "email" : "", "contact#" : "" ,
										"dn" :dn ,"cn" : cn,"memberOf" : [], "memberOfDn" : ""
									}
							myAllMemberDetails.append(myMemberDetails)		

						myGroupCompInfo.update({
							"member_details" : myAllMemberDetails
						}) 
					else:
						myGroupCompInfo.update({"member_details" : []})

				if comp_.lower() == 'member_of':
					if "member_of" in myGrpDetails["attributes"]: 
						myGroupCompInfo.update({"member_of" : myGrpDetails["attributes"]["member_of"]})
					else:
						myGroupCompInfo.update({"member_of" :[]})

			return myGroupCompInfo

		except Exception as error:
			raise error

	def getDBFootPrintViaOsCMD(self):
		"""
		Returns all databases details alive on current host
		"""
		try:
			myDBFootPrint = []
			if self.getOSType().lower() == "linux":
				# checking for mongo
				for proc in self.fetchDataFromOsCmdResult(self.execOSCmdRetResult('pgrep -la -f "mongod -f')):
					myDBFootPrint.append({
						"dbTechnology" : "mongo",
						"pid" : proc.split(" ")[0],
						"path" : proc.split(" ")[1],
						"configFile" : proc.split(" ")[3]
						})
				# checking for Postgres
				for proc in self.fetchDataFromOsCmdResult(self.execOSCmdRetResult('pgrep -la -f "postgres -D')):
					myDBFootPrint.append({
						"dbTechnology" : "mongo",
						"pid" : proc.split(" ")[0],
						"path" : proc.split(" ")[1],
						"configFile" : self.buildPath(proc.split(" ")[3],"postgressql.conf"),
						"hbaFile" : self.buildPath(proc.split(" ")[3],"pg_hba.conf"),
						})
			elif self.getOSType().lower() == "windows":
				pass
				#tasklist /fi "Imagename eq mongod.exe*"
			# checking for Mongo
			# checking for Postgres

		except Exception as error:
			raise error

	def getOsUsersAliveDBInfo(self, osUser, dbTech):
		"""
		Returns all alive databases proc details for a given osuser and db technology
		"""
		try:
			myDBTechnologies = [
				{"dbTechnology" : "mongo", "daemon" : "mongod"},
				{"dbTechnology" : "postgres", "daemon" : "postgres"}
			]
			myAliveDBDetails = []

			myDaemon = [db["daemon"] for db in myDBTechnologies if dbTech.lower() == db["dbTechnology"]]
			
			if not myDaemon:
				# we couldnt find relevant db daemon, returning empty list
				return myAliveDBDetails

			myDaemon = myDaemon[0]
			dbProcesses = self.getOSUsersProcess(osUser, myDaemon)
			#print(dbProcesses)
			for proc in dbProcesses:
				#print("proc >>> ", proc)
				# mongo and postgres processes must have 3 element in cmdline, skip if we didnt find 3 in cmdline
				if len(proc["cmdLine"]) != 3:
					continue

				myConfigFile = myPort = myBindIP = ""
				# get process detail
				if dbTech.lower() == "mongo":
					# checking if we have mongod and -f swith on this process, if not ignore this process
					if not("mongod" in proc["cmdLine"][0] and proc["cmdLine"][1].replace(" ", "") == "-f"):
						continue

					myConfigFile = proc["cmdLine"][2]
					# mongo config file is in yaml
					myConfigData = self.readYamlFile(myConfigFile)
					myPort = myBindIP = "" 
					if myConfigData:
						if "net" in myConfigData and "port" in myConfigData["net"]:
							myPort =  myConfigData["net"]["port"]
						if "net" in myConfigData and "bindIp" in myConfigData["net"]:
							myBindIP = myConfigData["net"]["bindIp"].split(",")
						
				elif dbTech.lower() == "postgres":
					# checking if we have mongod and -f swith on this process, if not ignore this process
					if not("mongod" in proc["cmdLine"][0] and proc["cmdLine"][1].replace(" ", "") == "-D"):
						continue

					myConfigFile = self.buildPath(proc["cmdLine"][2],"postgressql.conf")
					# postgres conf file is in ini format loading
					myConfigData = self.readConfigTextFile(myConfigFile)
					myPort = myBindIP = "" 
					if myConfigData:
						if "port" in myConfigData:
							myPort = myConfigData["port"]
						if "listen_addresses" in myConfigData:
							myBindIP =  myConfigData["listen_addresses"].split(",")
					# need hba.conf file as well
					myHbaConfigFile = self.buildPath(proc["cmdLine"][2],"pg_hba.conf")

				myProcDetail = self.getProcessDetail(proc["pid"])

				if myProcDetail:
					myProcDetail = myProcDetail[0]

				myAliveDBDetails.append({
					"dbTechnology" : dbTech.lower(),
					"pid" : proc["pid"],
					"user" : proc["user"],
					"configFile" :  myConfigFile,
					"binPath" : myProcDetail["exe"],
					"port" : int(myPort)
				})

			return myAliveDBDetails

		except Exception as error:
			raise error

	def getMyAliveDBInfo(self, dbTech):
		"""
		Returns all databases process for current user
		"""
		myCurrentUser = self.getCurrentUser()
		if myCurrentUser:
			myCurrentUser = myCurrentUser["current"]
			return self.getOsUsersAliveDBInfo(myCurrentUser, dbTech.lower())

	def convVersion2Tuple(self, version):
		"""
		Converts semantic version "n.n.n" to tuple, this is used for comparing a semantic verison
		For e.g. convVersion2Tuple("4.2.7") > convVersion2Tuple(4.2.0)
		"""
		return tuple(map(int, (version.split("."))))

	def genRandomNumber(self, minNum, maxNum, returnSamples):
		import random
		return random.sample(range(minNum, maxNum), returnSamples)

	def genRandomNumber(self, minNum, maxNum):
		import random
		return random.randint(minimum, maximum)

if __name__ == "__main__":
	util = Utility()
	#print(util.valArguments(['a','b','c'], {'a':1,'c':3,'d' : 4}, ['d']))

	'''
	curl --request POST \
	--url "https://dev.jira.mrshmc.com/rest/api/2/issue/MADOPMD-2/attachments" \
	--header "X-Atlassian-Token: nocheck" \
	-F "file=@./info.log" \
	-u u1167965
	'''
	
	'''
	# copying files
	util.copyFilesTo("/opt/ansible/deploy/logs/", "/opt/ansible/deploy/logs/temp/", [".log"])
	'''

	# exec os command which returns result
	
	'''
	result = util.execOSCmdRetResult("ps -eaf | grep -i 'mongod -f' | grep -v grep | awk '{print $10}'")
	print(str(result))
	data = util.fetchDataFromOsCmdResult(result)
	print(data)
	'''
	
	#getDayOfWeekOfMonth(self, dayOfWeek, year, month, week)

	"""
		daily 	:	daily schedule
			{"freq" : "daily"}
		weekly 	:	every monday
			{"freq" : "weekly", "day" : "monday"}
		monthly	:	every Monday of 1st week of each month 
			{"freq" : "monthly", "week" : 1, "day" : monday"}
		quarterly	:	every Monday of 1st week of 2nd month of a Quarter
			{"freq" : "quarterly", "month" : 1, week" : 1, "day" : monday"}
	"""
	
	""" commenting to test docker
	print("daily >>>", util.getDateFromSched({"freq" : "daily"}))
	print("weekly monday >>>", util.getDateFromSched({"freq" : "weekly", "day" : "monday"}))
	print("weekly wednesday >>>", util.getDateFromSched({"freq" : "weekly", "day" : "wednesday"}))
	print("weekly friday >>>", util.getDateFromSched({"freq" : "weekly", "day" : "friday"}))
	print("monthly >>>", util.getDateFromSched({"freq" : "monthly", "week" : 1, "day" : "monday"}))
	print("quarterly >>>", util.getDateFromSched({"freq" : "quarterly", "month" : 1, "week" : 1, "day" : "monday"}))
	print("quarterly >>>", util.getDateFromSched({"freq" : "yearly", "month" : 1, "week" : 1, "day" : "monday"}))
	try:
		myArg = [{"arg" : "opco", "type" : str, "value" : "region"}, {"arg" : "count", "type" : int, "value" : "1234"}]
		print('validating arg', myArg)
		util.valArguments2(myArg, [])
		print('arg validated successfully')
	except Exception as error:
		print('error occurred while validating args >>>',str(error))
	print('u1167965 is ad grp', util.isAdGroup('u1167965'))
	print('CTFY-UG_APAC_Marsh_dba-S-L is ad grp', util.isAdGroup('CTFY-UG_APAC_Marsh_dba-S-L'))
	print('retrieving grp name of user u1167965')
	print('ad grp >>', util.getUserAdGrp('u1167965'))
	print('ux grp >>', util.getUsersGroup('u1167965'))
	myFolder = "/opt/ansible/app/cicd/deploy/deploy_test"
	print(f'files in folder  {myFolder} >>', util.getAllFilesInAFolder(myFolder))
	"""
	"""
	def list_to_dict(l):
	    return dict(zip(map(str, range(len(l))), l))

	def dd(old, new, ctx=""):
	    changes = []
	    print ("Changes in " + ctx)
	    for k in new:
	        if k not in old:
	            #print(k, " removed from" , old)
	            changes.append({"what" : new[k], "type" : "missing"})
	    for k in old:
	        if k not in new:
	            print()
	            print (k ," added in ", old)
	            changes.append({"what" : {"old" : old[k], "new" : ""}, "type" : "added"})
	            continue
	        if old[k] != new[k]:
	            if type(old[k]) not in (dict, list):
	                print (k, " changed in old to ", str(old[k]))
	                changes.append({"what" : {"old" : old[k], "new" : new[k]}, "type" : "changed"})
	            else:
	                if type(new[k]) != type(old[k]):
	                    print (k, " changed to ", str(old[k]))
	                    changes.append({"what" : {"old" : old[k], "new" : new[k]}, "type" : "changed"})
	                    continue
	                else:
	                    if type(old[k]) == dict:
	                        dd(new[k], old[k], k)
	                        continue
	                    elif type(old[k]) == list:
	                        dd(list_to_dict(new[k]), list_to_dict(old[k]), k)
	    print("Done with changes in " + ctx)
	    print(changes)
	    return

	d1 = {"name":"Joe", "Pets":[{"name":"spot", "species":"dog"}]}
	d2 = {"name":"Joe", "Pets":[{"name":"spot", "species":"cat"}]}
	dd(d1, d2, "base")

	def diff(orig, new):
	    changes = []
	    for item in new:
	        if item not in orig:
	            changes.append({"what" : {item: orig[key]}, "changes" : "new keys" })
	            continue
	        if new[item] != orig[item]:
	            changes.append({"what" : {item: {"orig" : orig[item], "new" : new[item]}, "changes" : "new key value" })
	            continue

	        if type(item

	    for k in old:
	        if k not in new:
	            print()
	            print (k ," added in ", old)
	            changes.append({"what" : old[k], "type" : "added"})
	            continue
	        if old[k] != new[k]:
	            if type(old[k]) not in (dict, list):
	                print (k, " changed in old to ", str(old[k]))
	                changes.append({"what" : old[k], "type" : "added"})
	            else:
	                if type(new[k]) != type(old[k]):
	                    print (k, " changed to ", str(old[k]))
	                    continue
	                else:
	                    if type(old[k]) == dict:
	                        dd(new[k], old[k], k)
	                        continue
	                    elif type(old[k]) == list:
	                        dd(list_to_dict(new[k]), list_to_dict(old[k]), k)
	    print("Done with changes in " + ctx)
	    print(changes)
	    return
	"""

	"""
	# testing docker
	#getMongoDockerContainerCmd = "/bin/docker ps --format {{.Names}} {{.Command}} | grep -i \"mongod -f\" | awk '{print $1}'"
	getMongoDockerContainerCmd = "/bin/docker ps --format {{.Names}} {{.Command}} | grep -i \"mongod -f\" "
	getDockerConfigCmd = "/bin/docker inspect {container}"

	myResult = util.execOSCmdRetResult(getMongoDockerContainerCmd)
	myDockerContainerResult = myResult[0]

	for result in myDockerContainerResult.splitlines():
		print("container result", result)
		
		container = result.decode("utf-8").split(" ")[0]
		mongoConfFile = result.decode("utf-8").split(" ")[1]
		
		dockerConfig = util.execOSCmdRetResult(getDockerConfigCmd.formt(container=container))
		dockerConfigDict = util.convStrToDict(dockerConfig)

		myMonngoConfInDockerConfig = dockerConfigDict[0]["Args"][1]

		myMongoConfResult = [bind.split(":")[0] for bind in dockerConfigDict[0]["HostConfig"]["Binds"] if myMonngoConfInDockerConfig in bind]
		myMongoConfFile = myMongoConfResult[0] 
		print("container - ", container, ", mongo conf file >>> ", myMongoConfFile)

	"""
	"""
	# print network address stats
	from __future__ import print_function
	import socket

	import psutil
	from psutil._common import bytes2human


	af_map = {
	    socket.AF_INET: 'IPv4',
	    socket.AF_INET6: 'IPv6',
	    psutil.AF_LINK: 'MAC',
	}

	duplex_map = {
	    psutil.NIC_DUPLEX_FULL: "full",
	    psutil.NIC_DUPLEX_HALF: "half",
	    psutil.NIC_DUPLEX_UNKNOWN: "?",
	}


	def main():
	    stats = psutil.net_if_stats()
	    io_counters = psutil.net_io_counters(pernic=True)
	    for nic, addrs in psutil.net_if_addrs().items():
	        print("%s:" % (nic))
	        if nic in stats:
	            st = stats[nic]
	            print("    stats          : ", end='')
	            print("speed=%sMB, duplex=%s, mtu=%s, up=%s" % (
	                st.speed, duplex_map[st.duplex], st.mtu,
	                "yes" if st.isup else "no"))
	        if nic in io_counters:
	            io = io_counters[nic]
	            print("    incoming       : ", end='')
	            print("bytes=%s, pkts=%s, errs=%s, drops=%s" % (
	                bytes2human(io.bytes_recv), io.packets_recv, io.errin,
	                io.dropin))
	            print("    outgoing       : ", end='')
	            print("bytes=%s, pkts=%s, errs=%s, drops=%s" % (
	                bytes2human(io.bytes_sent), io.packets_sent, io.errout,
	                io.dropout))
	        for addr in addrs:
	            print("    %-4s" % af_map.get(addr.family, addr.family), end="")
	            print(" address   : %s" % addr.address)
	            if addr.broadcast:
	                print("         broadcast : %s" % addr.broadcast)
	            if addr.netmask:
	                print("         netmask   : %s" % addr.netmask)
	            if addr.ptp:
	                print("      p2p       : %s" % addr.ptp)
	        print("")


	if __name__ == '__main__':
	    main()
    """
	# testing process method
	util = Utility()
	"""
	#chcking pid
	myPid = util.lambdaGetCurrPID()
	print(util.getPidInfo(myPid))
	print(util.findProcStatusByCount())
	print(util.findAllProcessByStatus('running'))
	print(util.findAllActiveProcesse())
	"""

	"""
	#checking rest api call
	if not util.isPortOpen("usdfw21as383v",8000):
		print("appears to be no process is listening on 8000 !!!")
	else:	
		myScanDoc = util.readJsonFile("/opt/ansible/app/audit/log/host_scan_usdfw21as383v.mrshmc.com_08282020_123300.json")
		myScanDoc = {
			"encKey": "eXokNzl5NEUzOWdXNCkp",
			"userId": "u1167965",
			"method": "transmitScan",
			"args": {
				"scanDoc": myScanDoc
			}
		}

		result = util.postRestApi("http://usdfw21as383v:8000/api/audit/processRequest", myScanDoc)
		print("result >>>", result)
	"""

	# checking process
	"""
	procDetail = util.listProcDetail4KW("mongod")
	for proc in procDetail:
		print(util.encodeDictData(proc)) 
	"""

	# rest api with auth
	#getRestApiWAuth(self, url, userName, userPass_,  params_ = {}, authType = None)
	"""
	myUrl = 'http://usdf24v0098.mrshmc.com:8080/api/public/v1.0/groups'
	myUrl = 'http://usdf24v0098.mrshmc.com:8080/api/public/v1.0/users/5f7dd08f25e78f32b44d5df0'
	myUrl = 'http://usdf24v0098.mrshmc.com:8080/api/public/v1.0/groups/5c6ead631df5673131f55845'
	myUrl = 'http://usdf24v0098.mrshmc.com:8080/api/public/v1.0/groups/5c6ead631df5673131f55845/users'
	myUrl = 'http://usdf24v0098.mrshmc.com:8080/api/atlas/v1.0/users/5c1cf5083a6da88952845963'
	myUser = "anil.singh@marsh.com"
	myUserApiKey = '044588d9-0f46-4e76-9cdf-81bf8ad9f02f'
	myParams = {"pretty" : True}
	myAuthType = "digest"
	myResults = util.getRestApiWAuth(myUrl,myUser, myUserApiKey,myParams,myAuthType)
	print("keys >>> ", (myResults.keys()))
	for key in (myResults.keys()):
		print(key, myResults[key])

from ldap3 import Server, Connection, SUBTREE, AUTO_BIND_NO_TLS,ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, authentication
total_entries = 0
myLdapUser="CORP\\svc-dev-deploy-app"
myLdapPass="rSa3mc7%#sfasMBQZ"
myBaseDC="dc=corp,dc=mmco,dc=int"
myUserId="U1167965"
myEmployeeNumber="1167965"
myEmail="anil.singh1@mmc.com"
server = Server("usdfw1.ldap.corp.mmco.int",port=389,use_ssl=False, get_info='ALL')
with Connection(server, auto_bind=AUTO_BIND_NO_TLS, user = myLdapUser, password = myLdapPass, auto_referrals=False, authentication="NTLM") as conn:
	attr=[ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES]
	scope=SUBTREE
	myAllFilters=[
		f'(&(OU=MMC_Users)(objectClass=inetOrgPerson)(objectClass=user)(sAMAccountName={myUserId}))',
		f'(&(OU=MMC_Users)(objectClass=inetOrgPerson)(objectClass=user)(employeeNumber={myEmployeeNumber}))',
		f'(&(OU=MMC_Users)(objectClass=inetOrgPerson)(objectClass=user)(mail={myEmail}))',
		f'(&(OU=MMC_Users)(objectClass=inetOrgPerson)(sAMAccountName={myUserId}))',
		f'(&(OU=MMC_Users)(objectClass=inetOrgPerson)(employeeNumber={myEmployeeNumber}))',
		f'(&(OU=MMC_Users)(objectClass=inetOrgPerson)(mail={myEmail}))']
	for filter in myAllFilters:
		#print(f"user search filter >>> {filter}")	
		#for adUserOU in ["OU=MMC_Users","OU=Administrative"]:
		#print(f"searching in >> ou : {adUserOU}")
		#mySearchDn = "".join([adUserOU, ",", myBaseDC ])
		# we need try/catch for any possible error which might occur during search
		try:
			#if conn.search(search_base = mySearchDn, search_filter = mySearchFilter, search_scope = scope, attributes = attr):
			if conn.search(search_base = myBaseDC, search_filter = filter, search_scope = scope, attributes = ALL_ATTRIBUTES):
				print(f"user search filter >> {filter} found !!")
				print(conn.response_to_json())
				#break
			else:
				print(f"user search filter >> {filter} not found !!")
		except Exception as error:
			pass
			

from ldap3 import Server, Connection, SUBTREE, AUTO_BIND_NO_TLS,ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, authentication
total_entries = 0
myLdapUser="svc-dev-deploy-app"
myLdapPass="rSa3mc7%#sfasMBQZ"
myBaseDC="dc=corp,dc=mmco,dc=int"
myUserId="U1167965"
myEmployeeNumber="1167965"
myEmail="anil.singh1@mmc.com"
server = Server("usdfw1.ldap.corp.mmco.int",port=389,use_ssl=False, get_info='ALL')
conn = Connection(server, user = myLdapUser, password = myLdapPass)
conn.bind()
entry_generator = conn.extend.standard.paged_search(search_base = 'dc=corp,dc=mmco,dc=int',
     search_filter = '(&(OU=MMC_Users)(objectClass=inetOrgPerson)(objectClass=user)(employeeNumber=1167965))',
     search_scope = SUBTREE,
     attributes = '*',
     paged_size = 5,
     generator=True
)
for entry in entry_generator:
	total_entries += 1
	print(entry, entry.keys(), dir(entry))
	#print(entry['dn'], entry['attributes'])
	"""

	# ad groups
	# adGroupCompInfo --> 'all','group_dn','group_cn','group_name','group_misc','member_dn','member_cn','member_details','member_of'
	# memberAttr --> "userDN","networkId","employeeId","emailId"
	"""
	corpLdap = {'server': 'usdfw1.ldap.corp.mmco.int:389', 'id': 'Q09SUFxzdmMtZGV2LWRlcGxveS1hcHA=', 'enc': 'clNhM21jNyUjc2Zhc01CUVo=',"baseDC": "dc=corp,dc=mmco,dc=int"}
	dmzLdap = {'server': 'usfkl11dc109v.mrshmc.com:389', 'id': 'RE1aUFJPRDAxXHN2Yy11YXQtZGVwbG95LWFwcA==', 'enc': 'clNhM21jNyUjc2Zhc01CUVo=',"baseDC": "dc=dmzprod01,dc=mrshmc,dc=com"}
	print("grp details (GLB-MER-MongoDBAs-ServerAdmin-S-G) >>>",util.encodeDictData(util.getLdapGroupDetails("GLB-MER-MongoDBAs-ServerAdmin-S-G", corpLdap)))
	print("grp details (GLB-MER-MongoDBAs-ServerAdmin-S-G) >>>",util.encodeDictData(util.getLdapGroupDetails("GLB-MER-MongoDBAs-ServerAdmin-S-G", dmzLdap)))
	print("user detail by email id (anil.singh1@mmc.com) >>>",util.encodeDictData(util.getLdapUserDetails('emailId',"anil.singh1@mmc.com", corpLdap)))
	print("user detail by employee id (1167965) >>>",util.encodeDictData(util.getLdapUserDetails('employeeId',"1167965", dmzLdap)))
	print("user detail by _app network id (u1167965_app) >>>",util.encodeDictData(util.getLdapUserDetails('networkId',"u1167965_app", dmzLdap)))
	"""

	"""
	print("grp comp details (GLB-MER-MongoDBAs-ServerAdmin-S-G) all >>>",util.encodeDictData(util.getLdapGroupCompInfo("GLB-MER-MongoDBAs-ServerAdmin-S-G",'all')))
	print("grp comp details (GLB-MER-MongoDBAs-ServerAdmin-S-G) group_dn >>>",util.encodeDictData(util.getLdapGroupCompInfo("GLB-MER-MongoDBAs-ServerAdmin-S-G",'group_dn')))
	print("grp comp details (GLB-MER-MongoDBAs-ServerAdmin-S-G) group_cn >>>",util.encodeDictData(util.getLdapGroupCompInfo("GLB-MER-MongoDBAs-ServerAdmin-S-G",'group_cn')))
	print("grp comp details (GLB-MER-MongoDBAs-ServerAdmin-S-G) group_name >>>",util.encodeDictData(util.getLdapGroupCompInfo("GLB-MER-MongoDBAs-ServerAdmin-S-G",'group_name')))
	print("grp comp details (GLB-MER-MongoDBAs-ServerAdmin-S-G) group_misc >>>",util.encodeDictData(util.getLdapGroupCompInfo("GLB-MER-MongoDBAs-ServerAdmin-S-G",'group_misc')))
	print("grp comp details (GLB-MER-MongoDBAs-ServerAdmin-S-G) member_cn >>>",util.encodeDictData(util.getLdapGroupCompInfo("GLB-MER-MongoDBAs-ServerAdmin-S-G",'member_cn')))
	print("grp comp details (GLB-MER-MongoDBAs-ServerAdmin-S-G) member_details >>>",util.encodeDictData(util.getLdapGroupCompInfo("GLB-MER-MongoDBAs-ServerAdmin-S-G",'member_details')))
	print("grp comp details (GLB-MER-MongoDBAs-ServerAdmin-S-G) member_of >>>",util.encodeDictData(util.getLdapGroupCompInfo("GLB-MER-MongoDBAs-ServerAdmin-S-G",'member_of')))
	print("user detail by networkId (1214088) >>>",util.encodeDictData(util.getLdapUserDetails('networkId',"1214088")))
	print("user detail by emplyeeId (1214088) >>>",util.encodeDictData(util.getLdapUserDetails('employeeId',"1214088")))
	print("user detail by email id (anil.singh1@mmc.com) >>>",util.encodeDictData(util.getLdapUserDetails('emailId',"anil.singh1@mmc.com")))
	print("grp comp details (CTFY-UG_GLB_Marsh_dba-S-L) member_of >>>",util.encodeDictData(util.getLdapGroupCompInfo("CTFY-UG_GLB_Marsh_dba-S-L","default")))
	print("grp comp details (CTFY-UG_GLB_Marsh_dba-S-L) member_of >>>",util.encodeDictData(util.getLdapGroupCompInfo("CTFY-UG_GLB_Marsh_dba-S-L","group_cn,group_dn,member_cn,member_details")))
	"""
	#print("group details >>>", grpDetails)
	"""
	# testing diffBetweenDatesInDays (deleting files older than days)
	print("testing diffBetweenDatesInDays")
	myPath = "/opt/ansible/app/audit/reports/temp2del"
	myExtn = ".xlsx"
	myRetentionDays = 10000000000
	print(f"deleting files ({myExtn}) older than {myRetentionDays} from {myPath} ...")
	util.deleteFilesOlderThanDays(myPath, myExtn, myRetentionDays)
	"""
	"""
	userName = "mongo"
	dbTech = "mongo"
	currentUser = util.getCurrentUser()
	print(f"current user detail >> {currentUser['current']}")
	print(f"listing '{dbTech.lower()}' db details for user '{userName.lower()}' ...")
	print(util.getOsUsersAliveDBInfo(userName.lower(), dbTech.lower()))
	print(f"retrieving {currentUser['current']} user's alive mongo database details >>> \n {util.getMyAliveDBInfo(dbTech.lower())}")
	print(f"retrieving all alive db parent processes >>> {util.getAliveDBProcesses()}")
	#print(util.readConfigTextFile("test.conf"))
	#print(util.getOSUsersProcess("mongo", "mongod"))
	"""

	#testing postgres pid details
	userName = "postgres"
	dbTech = "postgres"
	currentUser = util.getCurrentUser()
	print(f"current user detail >> {currentUser['current']}")
	print(f"listing '{dbTech.lower()}' db details for user '{userName.lower()}' ...")
	print(util.getOsUsersAliveDBInfo(userName.lower(), dbTech.lower()))
	print(f"retrieving {currentUser['current']} user's alive postgres database details >>> \n {util.getMyAliveDBInfo(dbTech.lower())}")
	print(f"retrieving all alive db parent processes >>> {util.getAliveDBProcesses()}")




