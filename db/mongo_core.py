from com.mmc.common.singleton import Singleton
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.globals import Globals
from com.mmc.common.security import Security

from bson import *
from bson import json_util
from bson.codec_options import CodecOptions
from bson.objectid import ObjectId

# bson.SON/collection.OrderDict function would be needed if explicit ordering is needed
from pymongo import MongoClient, uri_parser, ReturnDocument
from pymongo.errors import *

import logging, logging.config, sys, inspect, warnings

# readPreference.SECONDARY
# ./mongo server:27017/db --quiet my_commands.js
# db.command
#	renameCollection, ({rolesInfo :1, showPrivileges : True})
#	command({"usersInfo" : 1})

class MongoCore(object, metaclass=Singleton):
	def __init__(self, securityToken):

		self.securityToken = securityToken

		self.sec = Security()
		#print("validating sec token from mongo", securityToken)
		self.sec.validateSecToken(securityToken)

		self.infra = Infrastructure()
		self.util = Utility()
		self.Globals = Globals()
		
		self.LOGGER = logging.getLogger(__name__)
		self.LOGGER.info("instantiating Mongodb class")

		self.CLASS_NAME = self.__class__.__name__
		self.ENVIRONMENT = self.util.getACopy(self.infra.environment)
		self.OS = self.ENVIRONMENT["hostInfo"]["os"].system
		self.MONGO_HOME = self.ENVIRONMENT["dbConfig"]["mongo"]["home"]

		self.KEY_FILE = self.util.buildPath(self.ENVIRONMENT["app_config_loc"], \
			self.util.getDictKeyValue(self.ENVIRONMENT["boot"], "keyFile"))
		"""
		self.REPOSITORY = self.util.getDictKeyValue(self.ENVIRONMENT["boot"]["repository"],"mongo")
		self.REPOSITORY_DB = self.util.getDictKeyValue(self.REPOSITORY, "db")
		self.REPOSITORY_INV_COLL = self.util.getDictKeyValue(self.REPOSITORY, "inventory")
		"""
		#self.URI_REPLICA_TEMPLATE = self.util.getACopy(self.Globals.template["mongoUriReplTemplate"])
		self.URI_TEMPLATE = self.util.getACopy(self.Globals.template["mongoUriTemplate"])
		self.URI_LDAP_TEMPLATE = self.util.getACopy(self.Globals.template["mongoURiLdapTemplate"])

		#self.KEY_FILE = self.util.buildPath(self.ENVIRONMENT["app_config_loc"], self.ENVIRONMENT["boot"]["main"]["keyFile"])
		#self.AUTH_DB = 'admin'
		#self.AUTH_MECHANISM = 'SCRAM-SHA-1'

		# deploy variable should be in deploy class
		self.SCALE = self.ENVIRONMENT['dbConfig']['mongo']['scale']
		self.MONGO_BACKUP_TOOL = self.util.buildPath(self.ENVIRONMENT["dbConfig"]["mongo"]["home"],'mongodump')

		#pymongo.collection.Collection
		#pymongo.database.Database

		# lambda 
		self.lambdaParseUri = lambda mongoUri : uri_parser.parse_uri(mongoUri)
		self.lambdaGetDbVer = lambda mongoUri : MongoClient(mongoUri).server_info()['version']
		self.lambdaFieldsList2Dict = lambda fieldsList : [{field :1} for field in fieldsList]

	def __repr__(self):
		return "(%s, %s)" % (self.__class__, self.securityToken)

	def __str__(self):
		return "(%s, %s)" % (self.__class__, self.securityToken)

	"""
	@staticmethod
	def __getUserPass(self, userName, userType):

		try:
			pass
		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error
	"""

	def __initMongoDb__(self, securityToken):
		try:
			self.sec.validateSecToken(securityToken)
			self.DB_COMPONENT_CONFIG = self.util.getDictKeyValue(self.ENVIRONMENT["dbConfig"][self.DB_COMPONENT_TYPE],self.DB_COMPONENT)
			self.DB_COMPONENT_HOSTS = self.util.getDictKeyValue(self.DB_COMPONENT_CONFIG, "hosts")
			self.DB_COMPONENT_REPLICA = self.util.getDictKeyValue(self.DB_COMPONENT_CONFIG,"replicaSet")
			self.DB_COMPONENT_ADMIN = self.util.getDictKeyValue(self.DB_COMPONENT_CONFIG["owner"], "userId")
			self.DB_COMPONENT_ADMIN_ENCPASS = self.util.getDictKeyValue(self.DB_COMPONENT_CONFIG["owner"], "encPass")
			self.DB_COMPONENT_AUTHDB = self.util.getDictKeyValue(self.DB_COMPONENT_CONFIG["owner"]["auth"], "authDB")
			self.DB_COMPONENT_AUTH_MODE = self.util.getDictKeyValue(self.DB_COMPONENT_CONFIG["owner"]["auth"],"authMech")
			self.DB_COMPONENT_USER_TYPE = self.util.getDictKeyValue(self.DB_COMPONENT_CONFIG["owner"],"userType")
			self.DB_COMPONENT_DB = self.util.getDictKeyValue(self.DB_COMPONENT_CONFIG,"db")
			self.DB_COMPONENT_INVENTORY_COLL = self.util.getDictKeyValue(self.DB_COMPONENT_CONFIG, "inventory")
			self.DB_COMPONENT_DEPLOY_DETAIL = self.util.getDictKeyValue(self.DB_COMPONENT_CONFIG, "deployDetail")
			self.DB_COMPONENT_DEPLOY_SUMMARY = self.util.getDictKeyValue(self.DB_COMPONENT_CONFIG, "deploySummary")

			self.db = Mongodb(securityToken)

			# build mongo uri for this db component
			self.REPO_URI = self.buildMongoUri(securityToken, \
				hosts = self.DB_COMPONENT_HOSTS, \
				userName = self.DB_COMPONENT_ADMIN, userType = self.DB_COMPONENT_USER_TYPE,\
				authDb = self.DB_COMPONENT_AUTHDB, authMech = self.DB_COMPONENT_AUTH_MODE, replicaSet = self.DB_COMPONENT_REPLICA)

		except Exception as error:
			raise error
				
	def buildMongoUri(self, securityToken, **kwargs):
		"""
		hosts : lsit of hosts with port 
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got argument(s) {args}".format(args = "".join([securityToken, ",", str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)
			
			myArgs = self.util.getACopy(kwargs)
			#myRequiredArgsList = ["hosts","userName","userPass", "userType", "authDb","authMech"]
			myRequiredArgsList = ["hosts","userName","userType", "authDb","authMech"]
			myOptionalArgsList = ["replicaSet","slaveOk"]
			
			self.util.valArguments(myRequiredArgsList, myArgs, myOptionalArgsList)
			"""
			if myArgs["userType"].lower() == "ldap":
				#myMongoUri = self.util.getACopy(self.URI_LDAP_TEMPLATE).format(\
				#	user = self.util.getStringQuote(myArgs['userName']), passwd = self.util.getStringQuote(myArgs['userPass']), hosts = myArgs['hosts'])
				myMongoUri = self.util.getACopy(self.URI_LDAP_TEMPLATE).format(\
					userName = self.util.getStringQuote(myArgs['userName']), userPass = "{userPass}", hosts = myArgs['hosts'])
			"""
			if myArgs["userType"].lower() == "internal":
				#myMongoUri = self.util.getACopy(self.URI_TEMPLATE).format(\
				#	user = self.util.getStringQuote(myArgs['userName']), passwd = self.util.getStringQuote(myArgs['userPass']), hosts = myArgs['hosts'], \
				#	authDb = myArgs['authDb'], authMech = myArgs["authMech"])

				myMongoUri = self.util.getACopy(self.URI_TEMPLATE).format(\
					#user = self.util.getStringQuote(myArgs['userName']), passwd = self.util.getStringQuote(myArgs['userPass']), hosts = myArgs['hosts'], \
					userName = self.util.getStringQuote(myArgs['userName']), userPass = "{userPass}", hosts = myArgs['hosts'], \
					authDb = myArgs['authDb'], authMech = myArgs["authMech"])

			else:
				#myMongoUri = self.util.getACopy(self.URI_LDAP_TEMPLATE).format(\
				#	user = self.util.getStringQuote(myArgs['userName']), passwd = self.util.getStringQuote(myArgs['userPass']), hosts = myArgs['hosts'])
				myMongoUri = self.util.getACopy(self.URI_LDAP_TEMPLATE).format(\
					userName = self.util.getStringQuote(myArgs['userName']), userPass = "{userPass}", hosts = myArgs['hosts'])

			if 'replicaSet' in myArgs:
				myMongoUri = ''.join([myMongoUri, '&replicaSet={repl}'.format(repl= myArgs["replicaSet"])])

			"""
			if 'replicaSet' in myArgs:
				myMongoUri = self.util.getACopy(self.URI_REPLICA_TEMPLATE).format(\
					user = myArgs['userName'], passwd = myArgs['userPass'], hosts = myArgs['hosts'], replSet = myArgs['replicaSet'], authDb = myArgs['authDb'])
			else:
				myMongoUri = self.util.getACopy(self.URI_TEMPLATE).format(\
					user = myArgs['userName'], passwd = myArgs['userPass'], hosts = myArgs['hosts'], authDb = myArgs['authDb'])
			"""

			#if 'replicaSet' in myArgs:
			#	myMongoUri = ''.join([myMongoUri,'&repliaSet={repl}'.format(repl=myArgs['replicaSet'])])

			# build uri for mongodump, we need host:port as an array, replsetname, db user, password, authDb, authMech,

			# commenting below to redact credential
			#self.LOGGER.debug("completed, returning response >>> {response}".format(response = myMongoUri))

			if "slaveOk" in myArgs:
				myMongoUri = ''.join([myMongoUri, '&slaveOk={slaveOk}'.format(slaveOk= myArgs["slaveOk"])])

			return myMongoUri

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred ", exc_info = True)
			raise error
	"""
	def getHostsFromInventory(self, securityToken, **kwargs):

		try:

			myModuleName = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.LOGGER.debug("got argument(s) {args}".format(args = ''.join([securityToken, str(kwargs)]) ))

			myRequiredArgsList = ['conn','env','instType','instName']

			self.util.valArguments(myRequiredArgsList, kwargs)
			#print("getHosts >>>", kwargs)

			#myConnection = self.util.getACopy(kwargs['conn'])
			myConnection = kwargs['conn']			
			myHostCriteria = {'type' : kwargs['instType'], 'name' : kwargs['instName'], 'env' : kwargs['env']}
			myProjection = {'hosts.host' : 1, 'hosts.port' : 1, '_id' : 0}
			myHostsData = self.findDocuments(securityToken, conn = myConnection, db = self.REPOSITORY_DB, collection = self.REPOSITORY_INV_COLL,criteria = myHostCriteria, projection = myProjection )
			#print(myHostsData[0])
			if myHostsData:
				return myHostsData[0]['hosts']

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error
	"""
	def getInvalidMongoUriError(self,securityToken, mongoUri):
		"""
		Returns the error for invalid Mongo URI
		"""
		try:
			client = MongoClient(mongoUri)
			testData = client.server_info()

			return ""
			

		except Exception as error:
			myError = f"error >>> [{error}]"
			return myError
			
	def isValidMongoUri(self, securityToken, mongoUri):
		try:
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got argument(s) {args}".format(args = "redacting uri information due to possibility of user password"))

			self.sec.validateSecToken(securityToken)
			#print(f"mongo uri >> {mongoUri}")
			myMongoUri = self.util.getACopy(mongoUri)

			# injecting sever selection timeout MS
			if self.Globals.srvrSelTimeoutMS not in myMongoUri:
				myMongoUri = ''.join([myMongoUri,'&serverSelectionTimeoutMS=',\
					str(self.ENVIRONMENT['boot']['deploy']['mongo']['serverSelectionTimeoutMS']) ])
				#myMongoUri = ''.join([myMongoUri,'&connectTimeoutMS=200, socketTimeoutMS=200'])

			#print(myMongoUri)
			client = MongoClient(myMongoUri)
			testData = client.server_info()

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(True)))
			return True

		except Exception as error:
			self.LOGGER.error(f"error [{error}] occurred, returning False !!!", exc_info = True)
			#raise error
			return False

	def getUriConn(self, mongoUri):
		try:

			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got argument(s) {args}".format(args = mongoUri))

			#print('uri >>', mongoUri)
			if self.isValidMongoUri(mongoUri):
				myConnection = MongoClient(mongoUri)
				#print('client >>>',client)
				self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(myConnection)))
				return myConnection
			else:
				raise ConnectionFailure

		except ConnectionFailure as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def getConn(self, hosts, userName, userPass, authDB, authMode = "PLAIN", replicaSet = None):
		try:
			
			myModuleName = sys._getframe().f_code.co_name

			self.LOGGER.debug("got argument(s) {args}".format(args = ','.join([\
				'host > ', host, 'user >', userName, 'pass > *****', 'authdb >', authDB, 'authmode >', authMode, 'replset >', str(replicaSet)])))

			#print('uri >>', mongoUri)

			myConnection = MongoClient(hosts = hosts, username = userName, password = userPass, \
				authSource = authDB, authMech = authMode, replicaSet = replicaSet)
			#print('client >>>',client)

			#self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(myConnection)))
			return myConnection

			#self.repDBProperties = self.getConnProperties(self.repDBConn)

		except ConnectionFailure as error:
			self.LOGGER.error(f"an error [{error}] occurred !!", exc_info = True)
			raise error

	def getConnProperties(self, conn):
		try:
			
			myModuleName = sys._getframe().f_code.co_name			

			self.LOGGER.debug("got argument(s) {args}".format(args = str(conn)))
			myConnection = conn

			#print(list(self.conn.nodes))
			myConnProperties = {
				"nodes" : myConnection.nodes,
				"primary" : myConnection.primary,
				"secondaries" : myConnection.secondaries,
				"arbiters" : myConnection.arbiters,
				"is_primary" : myConnection.is_primary,
				"db_names" : myConnection.list_database_names(),
				"read_preference" : myConnection.read_preferences,
				"default_database" : myConnection.get_database().name
			}
			
			self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(myConnProperties)))

			return myConnProperties

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!!", exc_info = True)
			raise error

	def isValidCredential(self, securityToken, **kwargs):
		"""
		Validates the mongo uri and credential

		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri","userName", "userEncPass"]

			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			#myConnection = MongoClient()

			return self.isValidMongoUri(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!!", exc_info = True)
			#return self.util.buildResponse(self.Globals.unsuccess, str(error))
			return False

	def createCollection(self, securityToken, **kwargs):
		#securityToken, uri, userName, userEncPass, db, collection, capped = None):
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ['uri', 'db', "userName", "userEncPass", 'collection']
			myOptionalArgsList = ["capped", "collation"]
			self.util.valArguments(myRequiredArgsList, myKwargs, myOptionalArgsList)

			self.LOGGER.info("building mongo uri for this request")

			myMongoUri = self.util.getACopy(myKwargs["uri"])
			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""
			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			self.LOGGER.info("mongo uri build >>> {uri}".format(uri=myMongoUri))
			myConnection = MongoClient(myMongoUri.format(userPass = myUserPass))

			#print("conn >>", myConnection)
			#print(myKwargs)
			#print(myKwargs["db"])
			db = myConnection[myKwargs["db"]]

			myCappedSize = myCappedMax = 0
			myCappedCollection = False
			
			if "capped" in myKwargs and myKwargs["capped"]:
				if not (isinstance(myKwargs["capped"], dict)):
					raise ValueError("capped argument must be type of dict !!")

				if not ("size" in myKwargs["capped"].keys() or "max" in myKwargs["capped"].keys()):
					raise ValueError("capped argument must contain size/max key value")
			
				myCappedCollection = True
				myCappedSize = myKwargs["capped"].get("size")
				myCappedMax = myKwargs["capped"].get("max")

			if "collation" in myKwargs:
				myCreateCollArgs = {\
					"name" : myKwargs["collection"], 
					"capped" : myCappedCollection, 
					"size" : myCappedSize, 
					"max" : myCappedMax,
					"collation" : myKwargs["collation"]}
			else:
				myCreateCollArgs = {\
					"name" : myKwargs["collection"], 
					"capped" : myCappedCollection, 
					"size" : myCappedSize, 
					"max" : myCappedMax}

			self.LOGGER.info("creating new collection >>> {collDetail} ".format(collDetail = myCreateCollArgs))

			myDBResult = db.create_collection(**myCreateCollArgs)

			myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)
			
			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))

	def createCollectionOld(self, securityToken, **kwargs):
		#securityToken, uri, userName, userEncPass, db, collection, capped = None):
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ['uri', 'db', "userName", "userEncPass", 'collection']
			myOptionalArgsList = ["capped"]
			self.util.valArguments(myRequiredArgsList, myKwargs, myOptionalArgsList)

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection[myKwargs["db"]]

			myCappedSize = myCappedMax = 0
			myCappedCollection = False
			
			if "capped" in myKwargs and myKwargs["capped"]:
				if not (isinstance(myKwargs["capped"], dict)):
					raise ValueError("capped argument must be type of dict !!")

				if not ("size" in myKwargs["capped"].keys() or "max" in myKwargs["capped"].keys()):
					raise ValueError("capped argument must contain size/max key value")
			
				myCappedCollection = True
				myCappedSize = myKwargs["capped"].get("size")
				myCappedMax = myKwargs["capped"].get("max")

			self.LOGGER.info("creating new collection {coll} ".format(coll = myKwargs["collection"]))
			
			myDBResult = db.create_collection(myKwargs["collection"], capped = myCappedCollection, size = myCappedSize, max = myCappedMax)

			myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)
			
			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except AutoReconnect as error:
			self.LOGGER.error(f"AutoReconnect error [{error}] occurred ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def dropCollection(self, securityToken, **kwargs):
		#uri, userName, userEncPass, db, collection):

		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ['uri', 'db', "userName", "userEncPass", 'collection']
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection[myKwargs["db"]][myKwargs["collection"]]

			self.LOGGER.info("dropping collection {coll} ".format(coll = myKwargs["collection"]))

			myDBResult = db.drop_collection(myKwargs["collection"])

			myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except AutoReconnect as error:
			self.LOGGER.error(f"AutoReconnect error [{error}] occurred ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))

	def createIndex(self, securityToken, **kwargs):
		"""
		purpose: create a non TTL index on collection. Pls use createIndex to create TTL index (creatino of an index is allowed on a non existent collection)
				collation does not appy to, better to apply collation at collection level 
					text indexes,
					2d indexes, and
					geoHaystack indexes.

		argument(s) : 
			conn : valid connection handler
			db: database name
			collection: collection name
			indexName : index_name
			indexType : [nonUnique, unique, ttl, partial, caseSensetive, sparse, text, hashed]
			properties : 
				TTL Index:
					{"ttl" : {"expireAfterSeconds" : n}}
				Partial Index:
					{partial : {"partialFilterExpression" : {}}
			keyTupleList: keys in tuple list [('key1', asc/dec/text/hashed)] (asc = 1, desc = -1, text = 'text', hashed = 'hashed')
			background : optional default to True, 
			collation : optional default to empty dict
		usage: 
			createIndex(uri= 'uri', userName = "user", userEncPass = "user encrypted password" 
				db = 'mydb', collection = 'mycoll', 
				indexName = 'index1',
				indexType = "nonUnique/unique/ttl/partial/caseSensetive/sparse/text/hashed"
				keyTupleList = [("key1" = 1), ("key2" = -1)] <OR>
				keyTupleList = [("key1" = "text")]) <OR>
				keyTupleList = [("key1" = "hsahed")], background = <True/False>)
				background = True/False
				collation = {}
		"""
		try:

			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db", "collection", "indexName", "indexType", "keyTupleList", "background"]
			self.util.valArguments(myRequiredArgsList, myKwargs, ["collation","properties"])

			if not (isinstance(myKwargs["db"], str) and isinstance(myKwargs["collection"], str) and isinstance(myKwargs["indexName"], str) \
					and isinstance(myKwargs["indexType"], str)):
				raise InvalidArguments("db/collection/indexName/indexType argument must be string type !!!")

			if not isinstance(myKwargs["keyTupleList"], list):
				raise InvalidArguments("keyTupleList must be type of dict in array, e.g. [('key' : 1/-1/'text')]")

			if not(myKwargs["indexType"] in ["nonUnique", "unique", "ttl", "partial", "caseSensetive", "sparse", "text", "hashed"]):
				raise InvalidArguments("indexType argument must be in {indxList}".format (\
					indxList = "[\"nonUnique\", \"unique\", \"ttl\", \"partial\", \"caseSensetive\", \"sparse\", \"text\", \"hashed\"]" ))

			if myKwargs["indexType"] == "partial" and not ("partial" in myKwargs["properties"] and "partialFilterExpression" in myKwargs["properties"]["partial"]) \
				and not (isinstance(myKwargs["properties"]["partial"]["partialFilterExpression"], dict)):
				raise InvalidArguments("missing partialFilterExpression value for partial index")

			# we would need more validation to ensure we got all the contents validated
			if myKwargs["indexType"] == "ttl" and not ("ttl" in myKwargs["properties"] and "expireAfterSeconds" in myKwargs["properties"]["ttl"]) \
				and not (isinstance(myKwargs["properties"]["ttl"]["expireAfterSeconds"], int)):
				raise InvalidArguments("missing/invalid expireAfterSeconds value for TTL index")

			if not (isinstance(myKwargs["keyTupleList"], list)):
				raise InvalidArguments("keyTupleList argument must be type of tuple in array/list")
			"""
			for key in myKwargs["keyTupleList"]:
				if not(isinstance(key, tuple)):
					raise IvalidArguments("key in keyTupleList must be type of tuple")
			"""

			# building argument as dict need to be passed to create index
			myArguments = {"name" : myKwargs["indexName"], "background" : myKwargs["background"]}
			
			if myKwargs["indexType"] == "unique": 
				myArguments.update({"unique" : True})

			if myKwargs["indexType"] == "ttl": 
				myArguments.update({"expireAfterSeconds" : myKwargs["properties"]["ttl"]["expireAfterSeconds"]})
				myKeys = myKwargs["keyTupleList"][0]
				if isinstance(myKeys, list):
					myKeys = myKeys[0]

			if myKwargs["indexType"] == "partial": 
				myArguments.update({"partialFilterExpression" : myKwargs["properties"]["partial"]["partialFilterExpression"]})

			#spars is applicable for non ttl indexes
			if "sparse" in myKwargs["properties"] and not( myKwargs["indexType"] == "ttl"): 
				myArguments.update({"sparse" : myKwargs["properties"]["sparse"]})

			if not (myKwargs["indexType"] == "ttl"):
				myKeys = []
				for keys in myKwargs["keyTupleList"]:
					if not isinstance(keys, tuple):
						myKeys.append(tuple(keys))
					else:
						myKeys.append(keys)
			
			myArguments.update({"keys" : myKeys})

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection[kwargs['db']][kwargs['collection']]

			self.LOGGER.info("creating index {indx} on {target} with arguments >>> {arg}".format(\
				indx = "".join([myKwargs["indexType"], ':', myKwargs["indexName"], " - ", str(myKwargs["keyTupleList"])]), \
				target = "".join([myKwargs["collection"], ':' , myKwargs["collection"]]), \
				arg = str(myArguments)  ))

			#myDBResult = db.create_index(name = kwargs['indexName'], keys = kwargs['keyTupleList'], unique = unique, background = kwargs['background'])
			#print("create index args >>", str(myArguments))

			myDBResult = db.create_index(**myArguments)

			myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def createIndexOld(self, securityToken, **kwargs):
		"""
		purpose: create a non TTL index on collection. Pls use createIndex to create TTL index (creatino of an index is allowed on a non existent collection)
		argument(s) : 
			conn : valid connection handler
			db: database name
			collection: collection name
			indexName : index_name
			keyTupleList: keys in tuple list [('key1', asc/dec/text/hashed)] (asc = 1, desc = -1, text = 'text', hashed = 'hashed')
			background : index creation in background
		usage: 
			createIndex(conn= 'conn', db = 'mydb', collection = 'mycoll', indexName = 'index1',\
				keyTupleList = [("key1" = 1), ("key2" = -1)] <OR>
				keyTupleList = [("key1" = "text")]) <OR>
				keyTupleList = [("key1" = "hsahed")], background = <True/False>)
		"""
		try:

			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myRequiredArgsList = ['uri', 'userName', "userEncPass", 'db', 'collection', 'indexName', 'unique', 'keyTupleList', 'background']
			self.util.valArguments(myRequiredArgsList, kwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			if not (isinstance(kwargs["db"], str) or isinstance(kwargs["collection"], str) or isinstance(kwargs["indexName"])):
				raise ValueError("db/collection/indexName argument must be string type !!!")

			if not isinstance(kwargs["keyTupleList"], list):
				raise InvalidArguments("keyTupleList must be type of dict in array, e.g. [('key' : 1/-1/'text')]")

			if not(isinstance(unique, bool)):
				raise InvalidArguments("argument unique must be boolean type ")

			self.util.valArguments(myRequiredArgsList, kwargs, [])

			db = myConnection[kwargs['db']][kwargs['collection']]
			myKeyTupleList = []

			self.LOGGER.info("creating index {indx} on {target}".format(\
				indx = "".join([myKwargs["indexType"], ':', myKwargs["collection"]], \
				target = "".join([myKwargs["collection"], " - ", str(myKwargs["keyTupleList"])])  )))

			myDBResult = db.create_index(name = kwargs['indexName'], keys = kwargs['keyTupleList'], unique = unique, background = kwargs['background'])

			myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def createTTLIndexOld(self, securityToken, **kwargs):
		"""
		purpose: create a TTL index on collection. (creatino of an index is allowed on a non existent collection)
		argument(s) : 
			conn : valid connection handler
			db_name: database name (str)
			coll_name: collection name (str)
			index_name : index_name (str)
			key: TTL index key
			expire_after_seconds: (int)
		usage: 
			createTTLIndex(conn= 'conn', db = 'mydb', collection = 'mycoll', indexName = 'index1', key = <key>, expireAfterSeconds = <nSeconds>)
            update existing ttl index	
           	return coll.database.command(
                'collMod', coll.name,
                index={'keyPattern': {index_field: pymongo.ASCENDING},
                       'expireAfterSeconds': ttl})
		self.Globals.INDEX_CREATION_BACKGROUND
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ['uri', 'db', "userName", "userEncPass", 'collection', 'indexName', 'key', 'expireAfterSeconds', 'background']
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			if not (isinstance(myKwargs["key"], str) or isinstance(myKwargs["db"], str) or isinstance(myKwargs["collection"], str) or isinstance(myKwargs["indexName"]) or \
				isinstance(myKwargs["key"], str) ):
				raise ValueError("db/collection/indexName/key argument must be string type !!!")

			if self.isCappedCollection(securityToken, myKwargs["conn"], myKwargs["db"], myKwargs['collection']):
				raise ValueError("TTL index is not allowed on capped collection !!!")

			if not isinstance(myKwargs['expireAfterSeconds'], int):
				raise ValueError("Expire after seconds argument must be a valid integer !!!")


			db = myConnection[myKwargs['db']][myKwargs['collection']]

			# key cant be "_id"
			# can not be compound keys, must be only one key

			self.LOGGER.info("creating index {indx} on {target}".format(\
				indx = "".join([myKwargs["indexType"], ':', myKwargs["collection"]], \
				target = "".join([myKwargs["collection"], " - ", str(myKwargs["keyTupleList"])])  )))

			myDBResult = db.create_index(\
				name = myKwargs['indexName'], keys = myKwargs['key'], expireAfterSeconds = myKwargs['expireAfterSeconds'], background = myKwargs["background"])

			myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)
			
			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def dropAnIndex(self, securityToken, **kwargs):
		"""
		purpose: drops an index for a given namesoace (db.collection)
		argument(s) : 
			uri : valid uri
			db: database name
			collection: collection name
			indexName : index_name
		usage: 
			dropAnIndex(uri= 'uri', db = 'mydb', collection = 'mycoll', indexName = 'index1')
		"""
		try:

			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myRequiredArgsList = ['uri', 'userName', "userEncPass", 'db', 'collection', 'indexName']
			self.util.valArguments(myRequiredArgsList, kwargs, [])
			myKwargs = self.util.getACopy(kwargs)

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			if not (isinstance(myKwargs["db"], str) or isinstance(myKwargs["collection"], str) or isinstance(myKwargs["indexName"])):
				raise ValueError("db/collection/indexName argument must be string type !!!")

			db = myConnection[myKwargs['db']][myKwargs['collection']]

			self.LOGGER.info("dropping index {indx} of collection {target}".format(\
				indx = myKwargs["indexName"], \
				target = "".join([myKwargs["db"], ".", myKwargs["collection"]])  ))

			myDBResult = db.drop_index(myKwargs['indexName'])

			myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def dropAllIndex(self, securityToken, **kwargs):
		"""
		purpose: drops an index for a given namesoace (db.collection). this will non drop _id indexes
		argument(s) : 
			uri : valid uri
			db: database name
			collection: collection name
		usage: 
			dropAllIndex(uri= 'uri', db = 'mydb', collection = 'mycoll')
		"""
		try:

			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myRequiredArgsList = ['uri', 'userName', "userEncPass", 'db', 'collection']
			self.util.valArguments(myRequiredArgsList, kwargs, [])
			myKwargs = self.util.getACopy(kwargs)

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			if not (isinstance(myKwargs["db"], str) or isinstance(myKwargs["collection"], str) or isinstance(myKwargs["indexName"])):
				raise ValueError("db/collection/indexName argument must be string type !!!")

			db = myConnection[myKwargs['db']][myKwargs['collection']]

			self.LOGGER.info("dropping all indexes of collection {target}".format(target = "".join([myKwargs["db"], ".", myKwargs["collection"]])  ))

			myDBResult = db.drop_indexes()

			myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def reIndex(self, securityToken, **kwargs):
		"""
		purpose: drops an index for a given namesoace (db.collection). this will non drop _id indexes
		argument(s) : 
			uri : valid uri
			db: database name
			collection: collection name
		usage: 
			reIndex(uri= 'uri', db = 'mydb', collection = 'mycoll')
		warning:
			1. The db.collection.reIndex() drops all indexes on a collection and recreates them. 
			2. This operation may be expensive for collections that have a large amount of data and/or a large number of indexes.
			3. For replica sets, db.collection.reIndex() will not propagate from the primary to secondaries. db.collection.reIndex() will only affect 
				a single mongod instance.
			4. db.collection.reIndex() always builds indexes in the foreground due to the logic described in Multiple Index Builds.

		"""
		try:

			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myRequiredArgsList = ['uri', 'userName', "userEncPass", 'db', 'collection']
			self.util.valArguments(myRequiredArgsList, kwargs, [])
			myKwargs = self.util.getACopy(kwargs)

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			if not (isinstance(myKwargs["db"], str) or isinstance(myKwargs["collection"], str) or isinstance(myKwargs["indexName"])):
				raise ValueError("db/collection/indexName argument must be string type !!!")

			self.LOGGER.info("dropping all indexes of collection {target}".format(target = "".join([myKwargs["db"], ".", myKwargs["collection"]])  ))

			# must check total documents in collection
			myDBResult = db.reindex()

			myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def renameCollFields(self, securityToken, **kwargs):
		"""
		purpose: rename field of collection
		arguments: 
			securityToken :
			uri:
			userName:
			userEncPass: 
			fieldMapping : array[{oldField: newFiedl}...]

		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ['uri', 'db', "userName", "userEncPass", "db",'collection', 'fieldMapping']
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			if not (isinstance(myKwargs["fieldMappings"], list)):
				raise InvalidArguments("fieldMappings argumnt must be an array")

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection[myKwargs["db"]][myKwargs["collection"]]

			self.LOGGER.info("total {tot} fileds to be renamed".format(tot = str(len(myKwargs["fieldMapping"])) ))

			for mapping in myKwargs["fieldMapping"]:
				self.LOGGER.info("renaming field {field} in collection {coll}".format(field = str(mapping), coll = myKwargs["collection"]))
				db.update_many(filter = myKwargs["criteria"], update = mapping)

			myDBResult = db.update_many(filter = myKwargs["criteria"], update = myKwargs["updateDoc"], array_filters = arrayFilters, \
				upsert = upsert, bypass_document_validation = bypassDocVal)

			if myDBResult.acknowledged:
				myStatus = self.Globals.success
			else:
				myStatus = self.Globals.unsuccess

			myMessage = "matched : {matched}, modified : {modified}, upserted_ids : {ids}".\
					format(matched = myDBResult.matched_count, modified = myDBResult.modified_count, ids = myDBResult.upserted_id)
			
			myResponse = self.util.buildResponse(myStatus, myMessage)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse
			
		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def createRole(self, securityToken, **kwargs):
		"""
		purpose: create role and assign existing roles and privileges to this role, this method would not assign any admin role i.e. role assigned to admin
				database.
		arguments: 
			securityToken :
			uri:
			userName:
			userEncPass:
			db : database in which role to be created 
			privilege : dict{role: [role1, role2], privilege : [], systemRoles : []}]
			  privileges: [
			    { resource: { cluster: true }, actions: [ "addShard" ] },
			    { resource: { db: "config", collection: "" }, actions: [ "find", "update", "insert", "remove" ] },
			    { resource: { db: "users", collection: "usersCollection" }, actions: [ "update", "insert", "remove" ] },
			    { resource: { db: "", collection: "" }, actions: [ "find" ] }
			  ],
			  roles: [
			    { role: "read", db: "admin" }
			  ]
			use admin
		commands: 
		db.runCommand({ createRole: "myClusterwideAdmin",
		  privileges: [
		    { resource: { cluster: true }, actions: [ "addShard" ] },
		    { resource: { db: "config", collection: "" }, actions: [ "find", "update", "insert", "remove" ] },
		    { resource: { db: "users", collection: "usersCollection" }, actions: [ "update", "insert", "remove" ] },
		    { resource: { db: "", collection: "" }, actions: [ "find" ] }
		  ],
		  roles: [
		    { role: "read", db: "admin" }
		  ],
		  writeConcern: { w: "majority" , wtimeout: 5000 }
		})

		read
		readWrite
		dbAdmin
		userAdmin
		clusterAdmin
		readAnyDatabase
		readWriteAnyDatabase
		userAdminAnyDatabase
		dbAdminAnyDatabase

		try:
		    db.command(
		        'createRole', 'noremove',
		        privileges=[{
		            'actions': ['insert', 'update', 'find'],
		            'resource': {'db': 'test', 'collection': 'test'}
		        }],
		        roles=[])
		except DuplicateKeyError:
		    logger.error('Role already exists.')
		    pass
    		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ['uri', 'db', "userName", "userEncPass", "db", 'role', "privilege"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			if not (isinstance(myKwargs["uri"], str) and isinstance(myKwargs["db"], str) and isinstance(myKwargs["userName"], str) and \
				isinstance(myKwargs["userEncPass"], str) and isinstance(myKwargs["uri"], str)):
				raise InvalidArguments("argument uri/userName/userEncPass/db/role must be type of string")

			if not (isinstance(myKwargs["privilege"], dict)):
				raise InvalidArguments("privilege argumnt must be an array")

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection[myKwargs["db"]]

			# building privilege
			myPrivilege = []
			myRoles = []

			for privilege in privileges:
				myPrivilege.append({"actions" : privilege.actions, "resource" : privilege.resource})

			for role in roles:
				myRoles.append(role)

			self.LOGGER.info("creating role >>> {roleInfo}".format(roleInfo = "".join(['role: ',role,' privileges : ', str(myPrivileges), ' roles : ', str(myRoles)]) ))

			myDBResult = db.command("creatingRole", myKwargs["role"], privileges = myPrivileges, role = myRoles)
			
			if myDBResult.acknowledged:
				myStatus = self.Globals.success
			else:
				myStatus = self.Globals.unsuccess

			myMessage = ""

			myResponse = self.util.buildResponse(myStatus, myMessage)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse
			
		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def renameCollection(self, securityToken, **kwargs):
		"""
		purpose: Rename collection
		arguments: 
			securityToken :
			uri:
			userName:
			userEncPass: 
			db:
			oldCollection:
			newCollection:

		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ['uri', 'db', "collection", "userName", "userEncPass", "db", 'newCollection']
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection[myKwargs["db"]][myKwargs["collection"]]

			self.LOGGER.info("renaming collection from {old} to {new}".format(old = myKwargs["collection"], new = myKwargs["newCollection"]))
			
			myDBResult = db.rename(myKwargs["newCollection"])

			if not myDBResult: 
				myResponse = self.util.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)
			else:
				myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def dropCollection(self, securityToken, **kwargs):
		"""
		purpose: Rename collection
		arguments: 
			securityToken :
			uri:
			userName:
			userEncPass: 
			db:
			collection:
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ['uri', 'db', "userName", "userEncPass", "db", 'collection']
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection[myKwargs["db"]]

			self.LOGGER.info("dropping collection {coll}".format(coll = myKwargs["collection"]))
			
			myDBResult = db.drop_collection(myKwargs["collection"])

			if not(myDBResult):
				myResponse = self.util.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)
			else:
				myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def dropDatabase(self, securityToken, **kwargs):
		"""
		purpose: Rename collection
		arguments: 
			securityToken :
			uri:
			userName:
			userEncPass: 
			db:
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ['uri', 'db', "userName", "userEncPass"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))
			
			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			#db = myConnection[myKwargs["db"]]

			self.LOGGER.info("dropping database {db}".format(db = myKwargs["db"]))
			
			myDBResult = myConnection.drop_database(myKwargs["db"])

			# we need to find what would be returned when dropping database
			#if not (myDBResult):
			#	myResponse = self.util.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)
			#else:
			myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error


	# find documents

	def findDocuments(self, securityToken, **kwargs):

		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)

			myRequiredArgsList = ["uri", "userName", "userEncPass", "db","collection", "criteria", "projection"]
			
			self.util.valArguments(myRequiredArgsList, myKwargs, ["projection"])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			if "projection" in myKwargs:
				myProjection = myKwargs['projection']
				if isinstance(myKwargs['projection'], list):
					myProjection = self.lambdaFieldsList2Dict(projection)
			else:
				myProjection = {}

			mySort = None
			myLimit = mySkip = 0


			if 'sort' in myKwargs:
				if not isinstance(myKwargs['sort'], list):
					raise ValueError("Sort argument must be tuple in list !!!")
				mySort = myKwargs['sort']

			if 'limit' in myKwargs:
				myLimit = myKwargs['limit']

			if 'skip' in myKwargs:
				mySkip = myKwargs['skip']

			db = myConnection[myKwargs['db']][myKwargs['collection']]

			if myProjection:
				data = db.find(filter = myKwargs['criteria'], projection = myProjection, skip = mySkip, limit = myLimit, sort = mySort)
			else:
				data = db.find(filter = myKwargs['criteria'], skip = mySkip, limit = myLimit, sort = mySort)

			myData = list(data)
			
			self.LOGGER.info(f"total {len(myData)} documents found for ns --> ({myKwargs['db']}.{myKwargs['collection']}), criteria --> ({myKwargs['criteria']}), projection --> ({myKwargs['projection']}) ")

			return myData

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred while searching for document using criteria ({myKwargs['criteria']}) on ns --> ({myKwargs['db']}.{myKwargs['collection']}) " , exc_info = True)
			#return self.util.buildResponse(self.Globals.unsuccess, str(error))
			raise error

	def findAllDocuments(self, securityToken, **kwargs):

		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)

			myRequiredArgsList = ["uri", "userName", "userEncPass", "db","collection","projection"]
			
			self.util.valArguments(myRequiredArgsList, myKwargs, ["projection"])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			if "projection" in myKwargs:
				myProjection = myKwargs['projection']
			else:
				myProjection = {}

			mySort = None
			myLimit = mySkip = 0

			if isinstance(myKwargs['projection'], list):
				myProjection = self.lambdaFieldsList2Dict(projection)

			if 'sort' in myKwargs:
				if not isinstance(myKwargs['sort'], list):
					raise ValueError("Sort argument must be tuple in list !!!")
				mySort = myKwargs['sort']

			if 'limit' in myKwargs:
				myLimit = myKwargs['limit']

			if 'skip' in myKwargs:
				mySkip = myKwargs['skip']

			db = myConnection[myKwargs['db']][myKwargs['collection']]

			if myProjection:
				data = db.find(filter = {}, projection = myProjection, skip = mySkip, limit = myLimit, sort = mySort)
			else:
				data = db.find(filter = {}, skip = mySkip, limit = myLimit, sort = mySort)

			myData = list(data)

			self.LOGGER.info(f"total {len(myData)} documents found for ns --> ({myKwargs['db']}.{myKwargs['collection']}), criteria --> ({myKwargs['criteria']}) ")

			#self.LOGGER.info("execution result >>> {result}".format(result = str(myData)))

			return myData

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred while searching for document using criteria ({myKwargs['criteria']}) on ns --> ({myKwargs['db']}.{myKwargs['collection']}) " , exc_info = True)
			#return self.util.buildResponse(self.Globals.unsuccess, str(error))
			raise error

	def getDistinct(self, securityToken, **kwargs):

		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db","collection", "criteria", "key"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			mySort = None
			myLimit = mySkip = 0

			db = myConnection[myKwargs['db']][myKwargs['collection']]
			data = db.distinct(filter = myKwargs['criteria'], key = myKwargs["key"])

			myData = list(data)
			self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(myData) ))

			return myData

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred during distinct search on ns {db}, criteria {myKwargs['criteria']} !!! ", exc_info = True)
			#return self.util.buildResponse(self.Globals.unsuccess, str(error))
			raise error
	# CRUD
	def insertOneDoc(self, securityToken, **kwargs):
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db","collection", "doc"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			if not (isinstance(myKwargs["db"], str) and isinstance(myKwargs["collection"], str)):
				raise ValueError("db/collection argument must be type of string")

			if not isinstance(myKwargs["doc"], dict):
				raise ValueError("doc argument must be type of dict (json) !!")

			self.LOGGER.info("inserting document in namespace {ns} >>> {doc}".format(\
				ns = "".join([myKwargs["db"], ".", myKwargs["collection"]]), doc = str(myKwargs["doc"])))

			db = myConnection[myKwargs["db"]][myKwargs["collection"]]
			self.LOGGER.info(f"adding new document (total : {len(myKwargs['doc'])}) in ns >>> {myKwargs['db']}.{myKwargs['collection']}")

			#myDBResult = db.insert_one(myKwargs["doc"], check_keys=False) # check_keys is deprecated
			myDBResult = db.insert_one(myKwargs["doc"])

			if myDBResult.acknowledged:
				myResponse = self.util.buildResponse(self.Globals.success,self.Globals.success, myDBResult.inserted_id)
				self.LOGGER.info("Creating doc operation was successful !!!")
			else:
				myResponse = self.util.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)
				self.LOGGER.info("Creating doc operation was unsuccessful !!!")

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred while creating new doc {myKwargs['doc']} on ns --> ({myKwargs['db']}.{myKwargs['collection']}) ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def insertManyDoc(self, securityToken, **kwargs):
		#conn, db, collection, docs):
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db","collection", "doc"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			if not (isinstance(myKwargs["db"], str) and isinstance(myKwargs["collection"], str)):
				raise ValueError("db/collection argument must be type of string")

			if not isinstance(myKwargs["doc"], list):
				raise ValueError("docs argument must be type of array with dict (json) data ")
				#docs = list(docs)
			
			#self.LOGGER.info('document size is >> {size}'.format(size = self.lambdaGetListSize(docs)))

			db = myConnection[myKwargs["db"]][myKwargs["collection"]]
			self.LOGGER.info(f"adding new documents (total : {len(myKwargs['doc'])}) in ns >>> {myKwargs['db']}.{myKwargs['collection']}")

			#myDBResult = db.insert_many(myKwargs["doc"], check_keys = False) # check_keys is deprecated
			myDBResult = db.insert_many(myKwargs["doc"])

			if myDBResult.acknowledged:
				myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult.inserted_ids)
				self.LOGGER.info("Creating many doc operation was successful !!!")
			else:
				myResponse = self.util.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)
				self.LOGGER.info("Creating many doc operation was unsuccessful !!!")

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse
			
		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred while creating new docs {myKwargs['doc']} on ns --> ({myKwargs['db']}.{myKwargs['collection']}) ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			raise error

	def updateDoc(self, securityToken, **kwargs):
		#conn, db, collection, criteria, updateDoc, upsert=False, bypassDocVal=False):
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db","collection", "criteria", "updateDoc"]
			myOptionalArgsList = ["arrayFilters","upsert","bypassDocVal"]
			self.util.valArguments(myRequiredArgsList, myKwargs, myOptionalArgsList)

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			arrayFilters = []
			bypassDocVal = True
			upsert = False

			if "upsert" in myKwargs: upsert = myKwargs["upsert"]
			if "bypassDocVal" in myKwargs: bypassDocVal = myKwargs["bypassDocVal"]
			if "arrayFilters" in myKwargs: arrayFilters = myKwargs["arrayFilters"]

			if not (isinstance(myKwargs["criteria"], dict) and isinstance(myKwargs["updateDoc"], dict) and isinstance(myKwargs["db"], str) and isinstance(myKwargs["collection"], str)):
				raise ValueError("invalid argument type, valid argumment >>> criteria: dict, updateDoc : dict, db:str, collection:str !!!")
				
			db = myConnection[myKwargs["db"]][myKwargs["collection"]]
			"""
			if myKwargs["collection"] == "deployment.summary":
				print(str(myKwargs["criteria"]), str(myKwargs["updateDoc"]), str(arrayFilters), str(upsert), str(bypassDocVal))
			"""
			self.LOGGER.info(f"updating document(s) (criteria : {myKwargs['criteria']}) in ns >>> {myKwargs['db']}.{myKwargs['collection']}")

			myDBResult = db.update_many(filter = myKwargs["criteria"], update = myKwargs["updateDoc"], array_filters = arrayFilters, \
				upsert = upsert, bypass_document_validation = bypassDocVal)

			if myDBResult.acknowledged:
				myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, \
					{'matched' : myDBResult.matched_count, 'modified' : myDBResult.modified_count, 'upserted_ids' : myDBResult.upserted_id })
				self.LOGGER.info("Update operation was successful ")
			else:
				myResponse = self.util.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess) 
				self.LOGGER.info("Update operation was unsuccessful ")
			
			#myResponse = self.util.buildResponse(myStatus, str(myMessageDict), myDBResult.upserted_id)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse
			
		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred while performing update [{myKwargs}]" , exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def replaceDoc(self, securityToken, **kwargs):
		#conn, db, collection, criteria, replaceDoc, upsert=False, bypassDocVal=False):
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db","collection", "criteria", "replaceDoc"]
			myOptionalArgsList = ["upsert","bypassDocVal"]
			self.util.valArguments(myRequiredArgsList, myKwargs, myOptionalArgsList)

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			arrayFilters = []
			bypassDocVal = True
			upsert = False

			if "upsert" in myKwargs: upsert = myKwargs["upsert"]
			if "bypassDocVal" in myKwargs: bypassDocVal = myKwargs["bypassDocVal"]
			if "arrayFilters" in myKwargs: arrayFilters = myKwargs["arrayFilters"]

			if not (isinstance(myKwargs["criteria"], dict) and isinstance(myKwargs["replaceDoc"], dict) and isinstance(myKwargs["db"], str) and isinstance(myKwargs["collection"], str)):
				raise ValueError("invalid argument type, valid argumment >>> criteria: dict, replaceDoc : dict, db:str, collection:str !!!")
				
			db = myConnection[myKwargs["db"]][myKwargs["collection"]]
			"""
			if myKwargs["collection"] == "deployment.summary":
				print(str(myKwargs["criteria"]), str(myKwargs["replaceDoc"]), str(arrayFilters), str(upsert), str(bypassDocVal))
			"""
			self.LOGGER.info(f"replacing document(s) (criteria : {myKwargs['criteria']}) in ns >>> {myKwargs['db']}.{myKwargs['collection']}")

			myDBResult = db.replace_one(filter = myKwargs["criteria"], replacement = myKwargs["replaceDoc"], upsert = upsert, bypass_document_validation = bypassDocVal)

			if myDBResult.acknowledged:
				myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, \
					{'matched' : myDBResult.matched_count, 'modified' : myDBResult.modified_count, 'upserted_ids' : myDBResult.upserted_id })
				self.LOGGER.info("Replace operation was successful ")
			else:
				myResponse = self.util.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess) 
				self.LOGGER.info("Replace operation was unsuccessful ")
			
			#myResponse = self.util.buildResponse(myStatus, str(myMessageDict), myDBResult.upserted_id)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse
			
		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred while performing update [{myKwargs}]" , exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def deleteDoc(self, securityToken, **kwargs):
		"""
		purpose: delete document for a given criteria
		DEPRECATED - Use delete_one() or delete_many() instead.
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db","collection", "criteria"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection[myKwargs["db"]][myKwargs["collection"]]
			self.LOGGER.info(f"deleting document (criteria : {myKwargs['criteria']}) in ns >>> {myKwargs['db']}.{myKwargs['collection']}")

			myDBResult = db.delete_many(myKwargs["criteria"])

			if myDBResult.acknowledged:
				myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, \
					{'deleted' : myDBResult.deleted_count})
				self.LOGGER.info("Delete operation was successful ")
			else:
				myResponse = self.util.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess) 
				self.LOGGER.info("Delete operation was unsuccessful ")

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def findAndModify(self, securityToken, **kwargs):
		"""
		purpose: find a document, update it and return either original or updated document
		DEPRECATED - Use delete_one() or delete_many() instead.
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db","collection", "criteria", "updateDoc", "returnDoc"]
			myOptionalArgsList = ["projection", "upsert"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			if not( isinstance(myKwargs["uri"], str) and isinstance(myKwargs["userName"], str) and isinstance(myKwargs["userEncPass"], str) and \
				isinstance(myKwargs["db"], str) and isinstance(myKwargs["collection"], str)):
				raise ValueError("arguments uri/userName/userEncPass/db/collection must be type of string !!!")

			if not ( isinstance(myKwargs["criteria"], dict ) and isinstance(myKwargs["updateDoc"], dict) and \
						( "projection" in myKwargs and isinstance(myKwargs["projection"], dict)) 
					):
				raise ValueError("argument criteria,updateDoc and projection must be dict type !!!")

			if "upsert" in myKwargs and not (isinstance(myKwargs["upsert"], bool)):
				raise ValueError("argument upsert must be boolean type !!!")

			projection = None
			upsert = False
			if myKwargs["returnDoc"] not in ["before", "after"]: myKwargs["returnDoc"] = "after"
			if myKwargs["returnDoc"] == "before": myKwargs["returnDoc"] =  ReturnDocument.BEFORE
			if myKwargs["returnDoc"] == "after": myKwargs["returnDoc"] =  ReturnDocument.AFTER

			if "projection" in myKwargs and myKwargs["projection"]: projection = myKwargs["projection"]
			if "upsert" in myKwargs: upsert = myKwargs["upsert"]

			db = myConnection[myKwargs["db"]][myKwargs["collection"]]

			myDBResult = db.find_one_and_update(filter = myKwargs["criteria"], update = myKwargs["updateDoc"], return_document = myKwargs["returnDoc"], \
				projection = projection, upsert = upsert)

			if myDBResult:
				myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)
			else:
				myResponse = self.util.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise

	def runAggregate(self, securityToken, **kwargs):
		"""
		purpose: run aggregate command
		"""
		#conn, db, collection, pipeline, allowDiskUse = True, maxTimeMs = 500):

		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, ",", str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db","collection", "pipeline"]
			myOptionalArgsList = ["allowDisk", "maxTimeMs"]
			self.util.valArguments(myRequiredArgsList, myKwargs, myOptionalArgsList)

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			if not ("allowDiskUse" in myKwargs): allowDiskUse = True
			if not ("maxTimeMs" in myKwargs): maxTimeMs = 0

			db = myConnection[kwargs["db"]][kwargs["collection"]]

			myDBResult = db.aggregate(myKwargs["pipeline"], allowDiskUse = allowDiskUse, maxTimeMS = maxTimeMs)
			myDBResult = list(myDBResult)

			self.LOGGER.debug(f"dbresult from aggregate for arg {myKwargs} >>> {myDBResult}")

			myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, myDBResult)
			#print("aggregate ", myKwargs["pipeline"], myResponse)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			self.LOGGER.info(f"returning total document {len(myDBResult)} for aggregate args >> {myKwargs}")

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred >> pipeline : {myKwargs['pipeline']}, db: {myKwargs['db']}, coll: {myKwargs['collection']} ", exc_info = True)
			#print(str(error))
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			raise error

	def __validateDBHostPort(self, mongoUri):
		"""
		validates database port for a given URI, this need to be called before attempting to execute a command at target
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug(f"got argument(s) [{mongoUri}]")

			for host in mongoUri.split("@")[1].split("/")[0].split(","):
				myHost = host.split(":")[0]
				myPort = host.split(":")[1]
				# checking if port is open
				if not self.util.isPortOpen(myHost, myPort):
					raise ValueError(f"Database host {myHost} port {myPort} is not open, aborting !!!")

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred >> during db port validation : {mongoUri}", exc_info = True)
			raise error

	def runCmd(self, securityToken, **kwargs):
		try:
			"""
			{collstats : <collectionName>}
			{dbstats : 1}
			{"find" : "coll", "filter"}
			https://docs.mongodb.com/v3.6/reference/command/
			"""
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, ",", str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			#myRequiredArgsList = ["uri", "userName", "userEncPass", "db","collection", "pipeline"]
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db", "dbCmd"]
			myOptionalArgsList = []
			#myOptionalArgsList = ["allowDisk", "maxTimeMs"]
			self.util.valArguments(myRequiredArgsList, myKwargs, myOptionalArgsList)

			"""
			db.command("createRole", )
			"""
			myMongoUri = self.util.getACopy(myKwargs["uri"])

			# checking if db port is open from this servers
			self.__validateDBHostPort(myMongoUri)
			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			#self.LOGGER.info(f"testing, uri >>> {myMongoUri.format(userName = myKwargs['userName'], userPass = myUserPass)}")

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			# we need to inject run_command here, its missing
			db = myConnection[myKwargs["db"]]
			if "collection" in myKwargs:
				db = db[myKwargs["collection"]] 
			
			self.LOGGER.info(f"executing: uri >> {myMongoUri} command >> {myKwargs['dbCmd']}")

			myDBResult = db.command(myKwargs["dbCmd"])

			self.LOGGER.info(f"completed, result >> {myDBResult}")

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myDBResult))

			return myDBResult

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error
			#raise error

	# create/drop collection/database

	def valCollectionName(self, collection):
		"""
		purpose: validate collection name
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got argument(s) [{args}]".format(args = collection))

			#if not isinstance(options, (types.DictType, types.NoneType)): 
			#	raise TypeError("options must be an instance of dict") 

			if not collection or ".." in collection: 
				raise Invalidcollection("collection name cannot be empty") 

			if "$" in collection and not (collection in ["$cmd"] or collection.startswith("$cmd")): 
				raise Invalidcollection("collection name must not contain '$'") 

			if collection[0] == "." or collection[-1] == ".": 
				raise Invalidcollection("collecion name must not start or end with '.'") 

			if not isinstance(collection, str): 
				raise TypeError("collection name must be an instance of (str, unicode)") 

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def valdb(self, db):
		"""
		purpose: validate db name
		"""
		try:

			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got argument(s) [{args}]".format(args = collection))

			if not isinstance(db, str): 
				raise TypeError("db name must be an instance of (str, unicode)") 

			if not db or ".." in db: 
				raise InvalidName("db name cannot be empty") 

			if "$" in db and not (db in ["$cmd"] or db.startswith("$cmd")): 
				raise InvalidName("collectiondb names must not contain '$'") 

			if db[0] == "." or db[-1] == ".": 
				raise InvalidName("db names must not start or end with '.'") 
		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error


	def isCappedCollection(self, securityToken, **kwargs):
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db","collection"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myResponse = self.getCollStats(\
				securityToken, uri = myKwargs["uri"], userName = myKwargs["userName"], userEncPass = myKwargs["userEncPass"], \
				db = myKwargs["db"], collection = myKwargs["collection"])['capped']

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def isCollectionExists(self, securityToken, **kwargs):
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db","collection"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			if myKwargs["collection"] in self.getAllcollections(\
				securityToken, uri = myKwargs["uri"], userName = myKwargs["userName"], userEncPass = myKwargs["userEncPass"], \
				db = myKwargs["db"]):
				
				self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(True)))
				return True
			else:
				self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(False)))
				return False
		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def isDbExists(self, securityToken, **kwargs):
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			if myKwargs["db"] in self.getAllDbs(\
				securityToken, uri = myKwargs["uri"], userName = myKwargs["userName"], userEncPass = myKwargs["userEncPass"]):
				self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(True)))
				return True
			else:
				self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(False)))
				return False

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	# db/collection stats

	def getCollStats(self, securityToken, **kwargs):
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db","collection"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))
			
			db = myConnection[myKwargs["db"]]

			myResponse = db.command("collstats", myKwargs["collection"], scale = self.SCALE)
			self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(True)))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def getAllcollections(self, securityToken, **kwargs):
		"""
		return : array
		"""
		try:
			#client = MongoClient(mongoUri)
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection[myKwargs["db"]]

			myResponse = db.list_collection_names()
			self.LOGGER.debug("completed, returning response >>> {response}".format(response = myResponse))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def getAllCollDetails(self, securityToken, **kwargs):
		"""
		purpose: returns all collection and its details for a given db and connection handler
		return : Array; all collections and its details listed below for a given database in Array
				[
					{name : '<coll_name', type : '<coll_type>', options: '', 
						info : {readonly : <boolean>, uuid : '<uuid of colleciton>''}, 
						idIndex: {v : n, key : {_id : n}, name : <idx_name>, ns : '<idx_name_space; db.indxname>' }
					}
				]
		usage : getAllCollDetails('<db>', '<collection_name>')
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection[myKwargs["db"]]
		
			myCollDetailCur = db.list_collections()
			myCollDetailData = list(myCollDetailCur)
			myCollDetailCur.close()

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(myCollDetailData)))

			return myCollDetailData

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def isIndexExists(self, securityToken, **kwargs):
		"""
		purpose: returns if given collection index exists 
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)
			myKwargs = self.util.getACopy(kwargs)

			myRequiredArgsList = ["uri", "userName", "userEncPass", "db", "collection","indexName"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myAllIndexes = self.getIndexes(securityToken, \
				uri = myKwargs["uri"], userName = myKwargs["userName"], userEncPass = myKwargs["userEncPass"], \
				db = myKwargs["db"], collection = myKwargs["collection"], indexName = myKwargs["indexName"])

			self.LOGGER.info("all indexes found for collection >>> {coll}".format(coll = myKwargs["collection"]))

			return myKwargs["indexName"] in myAllIndexes

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def getIndexes(self, securityToken, **kwargs):
		#conn, db, collection):
		"""
		return: index name of a given collection
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db", "collection"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))
			db = myConnection[myKwargs["db"]][myKwargs["collection"]]

			myallIndexes = db.index_information()

			"""
			myAllCollectionDetails = self.getAllCollDetails(securityToken, \
				uri = myKwargs["uri"], userName = myKwargs["userName"], userEncPass = myKwargs["userEncPass"], \
				db = myKwargs["db"], collection = myKwargs["collection"])
			
			myIndexLists = []
			[myIndexLists.append(idx["idIndex"]["name"]) for idx in myAllCollectionDetails if idx["name"] == myKwargs["collection"]]
			"""
			self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(myallIndexes)))

			return myallIndexes

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def getDBStats(self, securityToken, **kwargs):
		"""
		Returns database stats for a given db
		"""

		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection[myKwargs["db"]]

			myResponse = db.command("dbstats", scale = self.SCALE)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(myResponse)))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def getServerStatus(self, securityToken, **kwargs):
		"""
		Returns server status for given connection
		"""

		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection["admin"]

			myResponse = db.command("serverStatus", scale = self.SCALE)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(myResponse)))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def getDBConfig(self, securityToken, **kwargs):
		"""
		Returns server status for given connection
		"""

		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection["admin"]

			myResponse = db.command("getCmdLineOpts", scale = self.SCALE)

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(myResponse)))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def getAllDbs(self, securityToken, **kwargs):
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			myResponse = myConnection.list_database_names()

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(myResponse)))

			return myResponse

		except Exception as e:
			raise e

	def getAllDbDetails(self, securityToken, **kwargs):
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			myDBResult = list(myConnection.list_databases())

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(myDBResult)))

			return myDBResult

		except Exception as error:
			raise error

	def getCollSize(self, securityToken, **kwargs):
		#conn, db, collection):
		"""
		Description : return size of a collection
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db", "collection"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myResponse = self.getCollStats(\
					securityToken, uri = myKwargs["uri"], db = myKwargs["db"], collection = myKwargs["collection"])['storageSize'] + \
				self.getCollStats(\
					securityToken, uri = myKwargs["uri"], db = myKwargs["db"], collection = myKwargs["collection"])['totalIndexSize']

			self.LOGGER.debug("completed, returning response >>> {response}".format(response = str(myResponse)))

			return myResponse

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error
	
	def getTotalDocs(self, securityToken, **kwargs):
		#conn, db, collection, criteria = {}):
		"""
		Description : return total documents of a collection
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db", "collection", "criteria"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection[myKwargs["db"]][myKwargs["collection"]]

			#return self.getCollStats(conn, db, collection)['count']
			totalDocs = db.count_documents(myKwargs["criteria"])

			self.LOGGER.debug("completed, returing total docs [{total}]".format(total = str(totalDocs)))

			return totalDocs

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def getUsedSpace(self, securityToken, **kwargs):
		#conn, db, collection = None):
		"""
		Description : return storage size of a db/collection and its indexes
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db"]
			myOptionalArgsList = ["collection"]
			self.util.valArguments(myRequiredArgsList, myKwargs, myOptionalArgsList)

			if not("collection" in myKwargs):
				# db
				myTotalSize = self.getDBStats(securityToken, uri = myKwargs["uri"], db = myKwargs["db"])["storageSize"] + \
					self.getDBStats(uri = myKwargs["uri"], db = myKwargs["db"])["indexSize"]
			else:
				# collection
				myTotalSize = \
					self.getCollStats(securityToken, uri = myKwargs["uri"], db = myKwargs["db"], collection = myKwargs["collection"])['storageSize'] +\
					self.getCollStats(securityToken, uri = myKwargs["uri"], db = myKwargs["db"], collection = myKwargs["collection"])['totalIndexSize']

			self.LOGGER.debug("completed, returning total size {size} ".format(size = str(myTotalSize)))

			return myTotalSize

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def getDBFSUsedSize(self, securityToken, **kwargs):
		#conn, db):
		"""
		Description : return storage size in file system of a given co
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["uri", "userName", "userEncPass", "db"]
			self.util.valArguments(myRequiredArgsList, myKwargs, [])

			myMongoUri = self.util.getACopy(myKwargs["uri"])

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			myConnection = MongoClient(myMongoUri.format(userName = myKwargs["userName"], userPass = myUserPass))

			db = myConnection[myKwargs["db"]][myKwargs["collection"]]

			myFsUsedSpaceSize = self.getDBStats(securityToken, uri = myKwargs["uri"], db = myKwargs["db"])["fsUsedSize"]

			self.LOGGER.debug("completed, returning total fs ussed space {size} ".format(size = str(myFsUsedSpaceSize)))

			return myFsUsedSpaceSize

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def __buildBackupCmd(self, securityToken, **kwargs):
		try:

			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			#myMongoDBVer = self.lambdaGetDbVer()
			#myDeployUSerPass = self.__getUserPass(kwargs["userName"], "deploy")
			# replacing host name with fqdn
			import socket
			myNewHost = ""
			myHosts = kwargs["hosts"].split(',')

			# building new host string (adding fqdn)
			for hostPort in myHosts:
				host = hostPort.split(':')[0]
				port =  hostPort.split(':')[1]
				newHost = socket.getfqdn(host)
				myNewHost = ",".join([myNewHost, newHost + ':' + str(port)])
			myNewHost = str(myNewHost[1:])

			if self.OS.upper().lower() == "windows":
				myBackupCmdTemplate = self.Globals.mongoUtil["windows"]["backup"]["backup_mongod_base"]
			else:
				myBackupCmdTemplate = self.Globals.mongoUtil["linux"]["backup"]["backup_mongod_base"]

			#myUserPass = '{userPass}' this is not working when passing password before executing os command

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			if kwargs["authdb"] == "external":
				myBaseBackupCmd = myBackupCmdTemplate.format(\
					mongoBackup = "{bin}".format(bin = self.util.buildPath(self.MONGO_HOME, "mongodump")), \
					hosts = myNewHost , \
					userName = kwargs["userName"] , \
					userPass = "".join(["\"", myUserPass, "\""]), \
					authDb = repr("$external"), 
					authMode = "PLAIN", \
					backupDir = kwargs["backupDir"])
			else:
				myBaseBackupCmd = myBackupCmdTemplate.format(\
					mongoBackup = "{bin}".format(bin = self.util.buildPath(self.MONGO_HOME, "mongodump")), \
					hosts = kwargs["hosts"], userName = kwargs["userName"],\
					userPass = myUserPass, \
					authDb = kwargs["authDb"], 
					authMode = kwargs["authMode"], \
					backupDir = kwargs["backupDir"])

			#print('base backup',myBaseBackupCmd)
			if self.OS.upper().lower() == "windows":
				if kwargs["backupType"] == self.Globals.BACKUP_FULL:
					myBackupCmd = ''.join([myBaseBackupCmd, ' /oplog '])

				elif kwargs["backupType"] == self.Globals.BACKUP_DB:
					myBackupCmd = ''.join([myBaseBackupCmd, ' /d "{db}" '.format(db = kwargs['db'])])

				elif kwargs["backupType"] == self.Globals.BACKUP_COLLECTION:
					myBackupCmd = ''.join([myBaseBackupCmd, ' /d "{db}" /c "{collection}"'.format(db = kwargs['db'], collection = kwargs["collection"])])

				elif kwargs["backupType"] == self.Globals.BACKUP_QUERY:
					if not isinstance(kwargs["filter"], dict):
						raise ValueError("filter criteria must be a valid json format !!!")

					import json
					file=self.util.buildPath(kwargs["backupDir"], "query.json")
					self.util.write2JsonFile(file, kwargs["filter"],'w')
					
					#myQuery = json.dumps(kwargs["filter"])
					myQuery = repr(str(kwargs["filter"]))
					#print('query ', myQuery)

					#myBackupCmd = ''.join([myBaseBackupCmd, ' /d "{db}" /c "{collection}" /q \'{query}\' '.\
					#	format(db = kwargs['db'], collection = kwargs["collection"], query = myQuery) ])

					myBackupCmd = ''.join([myBaseBackupCmd, ' /d {db} /c {collection} /q {query} '.\
						format(db = kwargs['db'], collection = kwargs["collection"], query = myQuery) ])

					# using query file instead query option (had issue on windows)

					#myBackupCmd = ''.join([myBaseBackupCmd, ' /d "{db}" /c "{collection}" /queryFile {file} '.\
					#	format(db = kwargs['db'], collection = kwargs["collection"], file = file) ])
					"""
					myBackupCmd = ''.join([myBaseBackupCmd, ' /d "{db}" /c "{collection}" /q {query} '.\
						format(db = kwargs['db'], collection = kwargs["collection"], query = repr(myQuery)) ])
					"""
			else:
				if kwargs["backupType"] == self.Globals.BACKUP_FULL:
					myBackupCmd = ''.join([myBaseBackupCmd, ' --oplog '])

				elif kwargs["backupType"] == self.Globals.BACKUP_DB:
					myBackupCmd = ''.join([myBaseBackupCmd, ' -d "{db}" '.format(db = kwargs['db'])])

				elif kwargs["backupType"] == self.Globals.BACKUP_COLLECTION:
					myBackupCmd = ''.join([myBaseBackupCmd, ' -d "{db}" -c "{collection}"'.format(db = kwargs['db'], collection = kwargs["collection"])])

				elif kwargs["backupType"] == self.Globals.BACKUP_QUERY:
					if not isinstance(kwargs["filter"], dict):
						raise ValueError("filter criteria must be a valid json format !!!")
					"""
					import json
					file=self.util.buildPath(kwargs["backupDir"], "query.json")

					self.util.write2JsonFile(file,kwargs["filter"],'w')

					myBackupCmd = ''.join([myBaseBackupCmd, ' -d "{db}" -c "{collection}" -queryFile {file} '.\
						format(db = kwargs['db'], collection = kwargs["collection"], file = file) ])

					myQuery = json.dumps(kwargs["filter"])
					myBackupCmd = ''.join([myBaseBackupCmd, ' -d "{db}" -c "{collection}" -q {query} '.\
						format(db = kwargs['db'], collection = kwargs["collection"], query = myQuery) ])
					"""
					myQuery = repr(str(kwargs["filter"]))
					#print('query ', myQuery)

					#myBackupCmd = ''.join([myBaseBackupCmd, ' /d "{db}" /c "{collection}" /q \'{query}\' '.\
					#	format(db = kwargs['db'], collection = kwargs["collection"], query = myQuery) ])

					myBackupCmd = ''.join([myBaseBackupCmd, ' -d "{db}" -c "{collection}" -q {query} '.\
						format(db = kwargs['db'], collection = kwargs["collection"], query = myQuery) ])

				# adding logfile and error file to backup cmd
				myBackupCmd = ''.join([myBackupCmd, ' > {logFile} 2> {errorFile} '.format (logFile = kwargs["logFile"], errorFile = kwargs["errorFile"])])

			# before enabling below line, ensure password is redacted
			#print("backup cmd >>>", myBackupCmd)
			#self.LOGGER.debug("bacup cmd built >>> {cmd} ".format(cmd = str(myBackupCmd)))

			return myBackupCmd

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def backupData(self, securityToken, **kwargs):
		try:
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got argument(s) >>> {args} ".format(args = ''.join([securityToken, str(kwargs)])))
			# get size of collection or db
			# get space available in staging area. Do not proceed if sufficient space is not available in staging

			#validation
			self.sec.validateSecToken(securityToken)

			#) received {backup}".format(backup = myBackupCmd))

			myRequiredArgsList = ["hosts","backupDir","logFile","errorFile","userName", "userEncPass", "authDb", "authMode", "backupType"]
			myOptionalArgsList = ["db", "collection", "filter", "replicaSet"]
			myUserArgs = self.util.getACopy(kwargs)
			self.util.valArguments(myRequiredArgsList, kwargs, myOptionalArgsList)

			myKwargs = self.util.getACopy(kwargs)

			# validation
			myBackupCmd = self.__buildBackupCmd(securityToken, **kwargs)
			self.LOGGER.info("backup os cmd >>> {backup}".format(backup = myBackupCmd))
			#results = self.util.execOSCmdRetResult(myBackupCmd)
			#print(myBackupCmd.format(userPass = kwargs["userPass"]))
			#myRetCode = self.util.execOSCmdRetResult(myBackupCmd.format(userPass = kwargs["userPass"]))

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			#print("Pass >>", myUserPass)
			#print("backup cmd >>", myBackupCmd)
			#print("backup cmd >>", myBackupCmd.format(userPass = myUserPass))

			# ensure dir used in mongodump exists
			if not(self.util.isDirExists(myKwargs["backupDir"])): self.util.createDir(myKwargs["backupDir"])
			if not(self.util.isDirExists(self.util.getFileDirName(myKwargs["logFile"]))): self.util.createDir(self.util.getFileDirName(myKwargs["backupDir"]))
			if not(self.util.isDirExists(self.util.getFileDirName(myKwargs["errorFile"]))): self.util.createDir(self.util.getFileDirName(myKwargs["backupDir"]))

			#print("backup is pending !!!")
			myRetCode = self.util.execOSCmdRetCode(myBackupCmd)
			#myRetCode = self.util.execOSCmdRetResult(myBackupCmd.format(userPass = myUserPass))
			#myRetCode = 0			
			#print("return code is >>>", str(myRetCode))
			self.LOGGER.info("backup return code is >>> {retcode}".format(retcode = myRetCode))

			#print('backuo retcode >>>', retCode)

			if myRetCode == 0:
				self.LOGGER.error(f"os return code is 0, backup was sucessful")
				return(self.util.buildResponse(self.Globals.success, self.Globals.success))
			else:
				self.LOGGER.error(f"os return code is {retcode}, backup is not successful, pls review backup error log file for more information".format(retcode = myRetCode))
				myErrorFromLogFile = self.util.readTextFile(kwargs["errorFile"])
				self.LOGGER.error(f"error from backup log file >>> {myErrorFromLogFile}")
				return(self.util.buildResponse(self.Globals.unsuccess, "error during building backup cmd "))

			#print(results)
		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def __buildRestoreCmd(self, securityToken, **kwargs):
		try:

			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			import socket
			myNewHost = ""
			myHosts = kwargs["hosts"].split(',')

			for hostPort in myHosts:
				host = hostPort.split(':')[0]
				port =  hostPort.split(':')[1]
				newHost = socket.getfqdn(host)
				myNewHost = ",".join([myNewHost, newHost + ':' + str(port)])

			myNewHost = str(myNewHost[1:])

			if self.OS.upper().lower() == "windows":
				myRestoreCmdTemplate = self.Globals.mongoUtil["windows"]["restore"]["restore_mongod_base"]
			else:
				myRestoreCmdTemplate = self.Globals.mongoUtil["linux"]["restore"]["restore_mongod_base"]

			#myUserPass = '{userPass}' this is not working when passing password before executing os command

			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""

			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			if kwargs["authdb"] == "external":
				myBaseRestoreCmd = myRestoreCmdTemplate.format(\
					mongoRestore = "{bin}".format(bin = self.util.buildPath(self.MONGO_HOME, "mongorestore")), \
					hosts = myNewHost , \
					userName = kwargs["userName"] , \
					userPass = "".join(["\"", myUserPass, "\""]), \
					authDb = repr("$external"), 
					authMode = "PLAIN"
				)
			else:
				myBaseRestoreCmd = myRestoreCmdTemplate.format(\
					mongoRestore = "{bin}".format(bin = self.util.buildPath(self.MONGO_HOME, "mongorestore")), \
					hosts = kwargs["hosts"], userName = kwargs["userName"],\
					userPass = myUserPass, \
					authDb = kwargs["authDb"], 
					authMode = kwargs["authMode"]
				)

			# adding path to mongorestore
			myBaseRestoreCmd = "".join([myBaseRestoreCmd, " " , kwargs["backupDir"]])

			#print('base backup',myBaseBackupCmd)
			if not(self.OS.upper().lower() == "windows"):
				myRestoreCmd = ''.join([myBaseRestoreCmd, ' 1> {logFile} 2> {errorFile} '.format (logFile = kwargs["logFile"], errorFile = kwargs["errorFile"])])

			self.LOGGER.debug("restore cmd built >>> {cmd} ".format(cmd = str(myRestoreCmd)))

			return myRestoreCmd

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def restoreData(self, securityToken, **kwargs):
		try:
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got argument(s) >>> {args} ".format(args = ''.join([securityToken, str(kwargs)])))
			# get size of collection or db
			# get space available in staging area. Do not proceed if sufficient space is not available in staging

			#validation
			self.sec.validateSecToken(securityToken)

			myRequiredArgsList = ["hosts","backupDir","logFile","errorFile","userName", "userEncPass", "authDb", "authMode", "db"]
			myOptionalArgsList = ["collection","replicaSet"]
			myUserArgs = self.util.getACopy(kwargs)
			self.util.valArguments(myRequiredArgsList, kwargs, myOptionalArgsList)

			myKwargs = self.util.getACopy(kwargs)

			# validation
			myBackupCmd = self.__buildRestoreCmd(securityToken, **kwargs)
			self.LOGGER.info("restore os cmd >>> {backup}".format(backup = myBackupCmd))

			myRetCode = self.util.execOSCmdRetCode(myBackupCmd)
			self.LOGGER.info("restore return code is >>> {retcode}".format(retcode = myRetCode))

			#print('backuo retcode >>>', retCode)

			if myRetCode == 0:
				self.LOGGER.info("os return code is 0, restore was sucessful")
				return(self.util.buildResponse(self.Globals.success, self.Globals.success))
			else:
				self.LOGGER.error(f"os return code is {retcode}, restore is not successful, pls review restore error log file for more information".format(retcode = myRetCode))
				myErrorFromLogFile = self.util.readTextFile(kwargs["errorFile"])
				self.LOGGER.error(f"error from restore log file >>> {myErrorFromLogFile}")
				return(self.util.buildResponse(self.Globals.unsuccess, "error during restoring data {error}".format(error = myErrorFromLogFile)))

			#print(results)
		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def __buildBackupRestoreCmd(self, securityToken, **kwargs):
		try:

			myModuleName = sys._getframe().f_code.co_name			
			self.LOGGER.debug("got argument(s) [{args}]".format(args = ''.join([securityToken, str(kwargs)])))

			#validation
			self.sec.validateSecToken(securityToken)

			myKwargs = self.util.getACopy(kwargs)
			import socket

			# formatting source hosts
			myNewSourceHost = ""
			mySourceHosts = kwargs["Sourcehosts"].split(',')

			for hostPort in mySourceHosts:
				host = hostPort.split(':')[0]
				port =  hostPort.split(':')[1]
				newHost = socket.getfqdn(host)

				myNewSourceHost = ",".join([myNewSourceHost, newHost + ':' + str(port)])

			myNewSourceHost = str(myNewSourceHost[1:])

			# formatting target hosts
			myNewTargetHost = ""
			myTargetHosts = kwargs["Sourcehosts"].split(',')

			for hostPort in myTargetHosts:
				host = hostPort.split(':')[0]
				port =  hostPort.split(':')[1]
				newHost = socket.getfqdn(host)

				myNewTargetHost = ",".join([myNewTargetHost, newHost + ':' + str(port)])

			myNewTargetHost = str(myNewTargetHost[1:])

			if self.OS.upper().lower() == "windows":
				myBackupRestoreCmdTemplate = self.Globals.mongoUtil["windows"]["restore"]["restore_mongod_base"]
			else:
				myBackupRestoreCmdTemplate = self.Globals.mongoUtil["linux"]["restore"]["restore_mongod_base"]

			#myUserPass = '{userPass}' this is not working when passing password before executing os command
			"""
			myUserPass = self.sec._Security__getUserPass(\
				myKwargs["userName"], myKwargs["userEncPass"], self.sec._Security__getKey(myKwargs["userName"], self.KEY_FILE))
			"""
			myUserPass = self.util.getStringQuote(self.sec._Security__decryptText(myKwargs["userEncPass"]))

			if kwargs["authdb"] == "external":
				myBackupRestoreCmd = myBackupRestoreCmdTemplate.format(\
					mongoBackup = "{bin}".format(bin = self.util.buildPath(self.MONGO_HOME, "mongodump")), \
					mongoRestore = "{bin}".format(bin = self.util.buildPath(self.MONGO_HOME, "mongorestore")), \
					sourceHosts = myNewSourceHost , \
					targetHosts = nyNewTargetHost, \
					userName = kwargs["userName"] , \
					userPass = "".join(["\"", myUserPass, "\""]), \
					authDb = repr("$external"), 
					authMode = "PLAIN"
				)
			else:
				myBackupRestoreCmd = myRestoreCmdTemplate.format(\
					mongoBackup = "{bin}".format(bin = self.util.buildPath(self.MONGO_HOME, "mongodump")), \
					mongoRestore = "{bin}".format(bin = self.util.buildPath(self.MONGO_HOME, "mongorestore")), \
					sourceHosts = myNewSourceHost , \
					targetHosts = nyNewTargetHost, \
					userName = kwargs["userName"] , \
					userPass = "".join(["\"", myUserPass, "\""]), \
					authDb = kwargs["authDb"], 
					authMode = kwargs["authMode"]
				)

			#print('base backup',myBaseBackupCmd)
			if not(self.OS.upper().lower() == "windows"):
				myBackupRestoreCmd = ''.join([myBackupRestoreCmd, ' 1> {logFile} 2> {errorFile} '.format (logFile = kwargs["logFile"], errorFile = kwargs["errorFile"])])

			self.LOGGER.debug("backup restore cmd built >>> {cmd} ".format(cmd = str(myBackupRestoreCmd)))

			return myBackupRestoreCmd

		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def backupRestoreData(self, securityToken, **kwargs):
		"""
		purpose: Backup and restore using stdin with archive option
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got argument(s) >>> {args} ".format(args = ''.join([securityToken, str(kwargs)])))
			# get size of collection or db
			# get space available in staging area. Do not proceed if sufficient space is not available in staging

			#validation
			self.sec.validateSecToken(securityToken)

			myRequiredArgsList = ["sourceHosts","targetHost","backupDir","logFile","errorFile","userName", "userEncPass", "authDb", "authMode", "db"]
			myOptionalArgsList = ["collection","replicaSet"]
			myUserArgs = self.util.getACopy(kwargs)
			self.util.valArguments(myRequiredArgsList, kwargs, myOptionalArgsList)

			myKwargs = self.util.getACopy(kwargs)

			# validation
			myBackupCmd = self.__buildBackupRestoreCmd(securityToken, **kwargs)
			self.LOGGER.info("restore os cmd >>> {backup}".format(backup = myBackupCmd))

			myRetCode = self.util.execOSCmdRetCode(myBackupCmd)
			self.LOGGER.info("restore return code is >>> {retcode}".format(retcode = myRetCode))

			#print('backuo retcode >>>', retCode)

			if myRetCode == 0:
				self.LOGGER.info("os return code is 0, backup/restore was sucessful")
				return(self.util.buildResponse(self.Globals.success, self.Globals.success))
			else:
				self.LOGGER.error(f"os return code is {retcode}, backup/restore is not successful, pls review restore error log file for more information".format(retcode = myRetCode))
				myErrorFromLogFile = self.util.readTextFile(kwargs["errorFile"])
				self.LOGGER.error(f"error from restore log file >>> {myErrorFromLogFile}")
				return(self.util.buildResponse(self.Globals.unsuccess, "error during backup/restore data "))

			#print(results)
		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

	def backupTargetDB(self, securityToken, **kwargs):
		try:
			myModuleName = sys._getframe().f_code.co_name
			self.LOGGER.debug("got argument(s) >>> {args} ".format(args = ''.join([securityToken, str(kwargs)])))

			# validation
			self.sec.validateSecToken(securityToken)

			myUserArgs = self.util.getACopy(kwargs)
			myRequiredArgsList = ["hosts", "instType","instName","backupDir","logFile","errorFile","userName", "userPass", "authDb", "authMode", "backupType"]
			myOptionalArgsList = ["db", "collection", "filter"]
			self.util.valArguments(myRequiredArgsList, kwargs, myOptionalArgsList)

			#myAllHostPort = self.getHostsFromInventory(conn = myRepConn, env = kwargs['env'], instType = kwargs['instType'], instName = kwargs['instName'])
			#if not myAllHostPort:
			#	raise ValueError("missing target instance [{inst}] in repository ".format(inst = ':'.join([kwargs["env"], kwargs["instType"], kwargs["instName"]])))
			
			#myFormattedHost = self.util.formatHosts4MongoUri(myAllHostPort)
			if kwargs["instType"] == "replicaSet":
				myHosts = ''.join([kwargs["instName"], "/", myFormattedHost])

			myBackupCmd = self.buildBackupCmd(kwargs, hosts = myFormattedHost)

			self.LOGGER.info("backup os cmd >>> {backup}".format(backup = myBackupCmd))
			#retCode = self.util.execOSCmdRetCode(myBackupCmd.format(userPass = kwargs["userPass"]))
			retCode = self.util.execOSCmdRetResult(myBackupCmd)

			self.LOGGER.info("backup return code is >>>", myRetCode)
			if retCode == 0:
				self.LOGGER.error(f"retcode is 0, backup was sucessful")
				myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success)
			else:
				self.LOGGER.error(f"error occurred during backup, pls review backup error log file for more information")
				myErrorFromLog = self.util.readTextFile(self.util.buildPath(kwargs["backupDir"], ))
				myResponse = self.util.buildResponse(self.Globals.unsuccess, "error during backup cmd {cmd}".format(cmd = myBackupCmd))

			self.LOGGER.debug("completed, returning total fs ussed space {size} ".format(size = str(myResponse)))
			
			return myResponse

			#print(results)
		except Exception as error:
			self.LOGGER.error(f"an error [{error}] occurred !!! ", exc_info = True)
			raise error

if __name__ == "__main__":
	mongo = Mongodb()
	#print('env >>',mongo.infra.environment)
	myREPOSITORY = mongo.ENVIRONMENT["dbConfig"]["repository"]["mongo"]
	myDEPLOY = mongo.ENVIRONMENT["dbConfig"]["deploy"]["mongo"]
	myKeyFile = mongo.util.buildPath(mongo.ENVIRONMENT["app_config_loc"], mongo.ENVIRONMENT["boot"]["keyFile"])

	deployAdmin = mongo.ENVIRONMENT["dbConfig"]["deploy"]["mongo"]["user"]
	myDeployAdminEncPass = mongo.ENVIRONMENT["dbConfig"]["deploy"]["mongo"]["encPass"]

	repoAdmin = mongo.DEPLOY_USER
	repoAdminEncPass =mongo.ENVIRONMENT["dbConfig"]["repository"]["mongo"]["encPass"]
	#mySecKey = mongo.sec._Security__getKey(repoAdmin, myKeyFile)
	"""
	repAdminPass = mongo.sec._Security__getUserPass(repoAdmin, repoAdminEnsPass, mySecKey)
	"""

	repAdminPass = self.sec._Security__decryptText(repoAdminEncPass)

	deployAdmin = mongo.DEPLOY_USER
	deployAdminPass = mongo.sec._Security__getUserPass(deployAdmin, myDeployAdminEncPass)

	repoUri = mongo.buildMongoUri(hosts="usdf23v0466:27011,usdf23v0467:27011,usdf23v0355:27011", userName=repoAdmin, userPass=repAdminPass, authDb='admin',authMech='Plain',replicaSet='rep_devqa01')
	print('repository uri >>>',repoUri)
	print('repo uri parse >>>',mongo.lambdaParseUri(repoUri))
	repoConn = mongo.getUriConn(repoUri)
	print("repository connection >>>", repoConn)

	#dropping collection
	print("dropping collection")
	result = mongo.dropCollection(repoConn, 'repository','inventory')
	print("result >>>", result)

	print("creating collection")
	result = mongo.createCollection(repoConn, 'repository','inventory')
	print("result >>>", result)

	#inserting bulk data from json file
	print('bulk insert')
	data = mongo.util.readJsonFile("c:\\app\\mongo_deploy\\config\\repository.json")
	result = mongo.insertManyDoc(repoConn, "repository","inventory", data)
	totDocs = mongo.getTotalDocs(repoConn,'repository','inventory')
	print('total docs in repository.inventory >>>', totDocs)
	print("findDocuments")
	data = mongo.findDocuments(\
		conn = repoConn, db = "repository", collection = "inventory", \
		criteria = {"name": "rep_devqa01", "type" : "replicaSet", "env" : "dev"}, \
		projection = {"hosts.host" : 1, "hosts.port" : 1}, \
		limit = 0, skip = 0, sort = [("hosts.host", 1)] )
	print(data)

	print("getHostsFromInventory")
	data = mongo.getHostsFromInventory(conn = repoConn, env= "dev", instType = "replicaSet", instName = "rep_devqa01")
	for x in data:
		print('host >>',x)
	print('hosts >>>',data)
	print('formatted host >>>',mongo.util.formatHosts4MongoUri(data))


	# we need to connect to repository to get target db information which will be used to build target db uri.
	targetUri = mongo.buildTargetDBUri(\
		repConn = repoConn, env= 'dev', instType = 'replicaSet', instName = 'rep_devqa01', \
		userName = deployAdmin, userPass = deployAdminPass, authDb = "admin", authMech = "DEFAULT")

	print('target db uri >>> ', targetUri)
	print('repo uri parse >>>', mongo.lambdaParseUri(targetUri))
	targetConn = mongo.getUriConn(targetUri)

	print ('creating index')
	result = mongo.createIndex(conn = targetConn, db = 'repository', collection = 'inventory', indexName = 'inventoryIndex01', keyTupleList = [("name", 1)], background = True)
	print(result)

	targetPrasedUri = mongo.lambdaParseUri(targetUri)
	myAllHostPort = mongo.getHostsFromInventory(conn = targetConn, env = "dev", instType = "replicaSet", instName = "rep_devqa01")
	myFormattedHost = mongo.util.formatHosts4MongoUri(myAllHostPort)

	#myRequiredArgsList = ["hosts","backupDir","logFile","errorFile","user", "backupType"]
	#myOptionalArgsList = ["db", "collection", "filter"]
	#dict(targetPrasedUri['nodelist'])

	"""
	print("performing full mongod backup")
	#backupResult = mongo.backupDB(hosts = myFormattedHost, backupDir = "c:\\app\\mongo\\backup\\test",\
	#	userName = "mongo_admin", authDb = "admin", authMode = "PLAIN", backupType = mongo.Globals.BACKUP_FULL, errorFile = 'c:\\app\\logs\\error.log', logFile = 'c:\\app\\logs\\backup.log')
	print("performing mongod db backup")
	backupResult = mongo.backupDB(hosts = myFormattedHost, backupDir = "c:\\app\\mongo\\backup\\test",\
		userName = "mongo_admin", authDb = "admin", authMode = "PLAIN", \
		backupType = mongo.Globals.BACKUP_DB, db = "repository",\
		errorFile = 'c:\\app\\logs\\error.log', logFile = 'c:\\app\\logs\\backup.log')
	print("performing mongod collection backup")
	backupResult = mongo.backupDB(hosts = myFormattedHost, backupDir = "c:\\app\\mongo\\backup\\test",\
		userName = "mongo_admin", authDb = "admin", authMode = "PLAIN", \
		backupType = mongo.Globals.BACKUP_COLLECTION, db = "repository", collection = "inventory", errorFile = 'c:\\app\\logs\\error.log', logFile = 'c:\\app\\logs\\backup.log')

	print("performing mongod collection (filter) backup")
	backupResult = mongo.backupDB(hosts = myFormattedHost, backupDir = "c:\\app\\mongo\\backup\\test",\
		userName = "mongo_admin", authDb = "admin", authMode = "PLAIN", \
		backupType = mongo.Globals.BACKUP_QUERY, db = "repository", collection = "inventory", filter = {"name" : "rep_devqa01"} ,\
		errorFile = 'c:\\app\\logs\\error.log', logFile = 'c:\\app\\logs\\backup.log')

	print(backupResult)
	"""

	print("completed ...")
	"""
	>>> result = db.profiles.create_index([('user_id', pymongo.ASCENDING)],unique=True)
	>>> sorted(list(db.profiles.index_information()))
	[u'_id_', u'user_id_1']
	db.create_index()
	"""
	"""
	mongo.parseUri(uri)
	conn = mongo.getUriConn(mongo.repDBUri)
	db = conn[mongo.environment["boot"]["repository"]["mongo"]["db"]]
	print("list dbs >>>", mongo.getAllDbs(conn))
	#print("db stats ['repository'] >>>", mongo.getDBStats(conn, 'repository'))	
	print("list collections ['repository'] >>>", mongo.getAllcollections(conn, 'repository'))
	print("list collection details ['repository'] >>>", mongo.`(conn, 'repository'))
	print("list indexes ['repository.dbInventory'] >>>", mongo.getACollIndexes(conn, 'repository', 'dbInventory'))
	#print("coll stats ['repository.dbInventory'] >>>", mongo.getCollStats(conn, 'repository', 'dbInventory'))
	print("total docs ['repository.dbInventory'] >>>", mongo.getTotalDocs(conn, 'repository', 'dbInventory'))
	print("coll size >>>", mongo.getCollectionSize(conn, 'repository', 'dbInventory'))
	print("db used space ['repository'] size KB >>>", mongo.getUsedSpace(conn, 'repository'))
	print("coll used space ['repository.dbInventory'] size KB >>>", mongo.getUsedSpace(conn, 'repository', 'dbInventory'))
	print("db used space fs ['repository'] size KB >>>", mongo.getDBFSUsedSize(conn, 'repository'))

	uri = "mongodb://mongo_admin:Marsh_oct062018@rep_devqa01/usdf23v0466:27011,usdf23v0467:27011,usdf23v0355:27011/repository?authSource=admin"
	print("backup db ['repository'] >>> ", mongo.backupDB(uri, 'repository'))
	"""
	#print(dir(db))
	#print(mongo.get)
	"""
	import json
	#infra.environment["boot"]["repository"]["dbRepositoryURI"])
	#docs = json.load(open('c:\\app\\mongo_deploy\\config\\init_conf.json'))
	docs = json.load(open('c:\\app\\mongo_deploy\\config\\test_insmany.json'))	
	print(type(docs))
	results = mongo.insertManyDoc(mongo.infra.environment["boot"]["repository"]["dbRepositoryURI"], "repository", "test", docs)
	print(results)
	"""
	"""
	Method for DB client in pymongo
	===================================
	'_BaseObject__codec_options', '_BaseObject__read_concern', '_BaseObject__read_preference', '_BaseObject__write_concern', 
	'_Database__client', '_Database__incoming_copying_manipulators', '_Database__incoming_manipulators', '_Database__name', 
	'_Database__outgoing_copying_manipulators', '_Database__outgoing_manipulators', '__call__', '__class__', '__delattr__',
	'__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattr__', '__getattribute__', '__getitem__',
	'__gt__', '__hash__', '__init__', '__init_subclass__', '__iter__', '__le__', '__lt__', '__module__', '__ne__', '__new__',
	 '__next__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', 
	 '__weakref__', '_apply_incoming_copying_manipulators', '_apply_incoming_manipulators', '_command', '_create_or_update_user', 
	 '_default_role', '_fix_incoming', '_fix_outgoing', '_list_collections', '_read_preference_for', '_write_concern_for',
	 
	 Variables:
	 ==========
	 client, 

	 Functions:
	 ==========
	 'add_son_manipulator', 'add_user', 'authenticate', 
	 'client', 'codec_options', 'collection_names', 'command', 'create_collection', 'current_op', 'dereference', 'drop_collection', 
	 'error', 'eval', 
	 'get_collection', 
	 'incoming_copying_manipulators', 
	 'incoming_manipulators', 
	 'last_status','list_collection_names', 'list_collections', 'logout', 
	 'name', 'next', 
	 'outgoing_copying_manipulators', 'outgoing_manipulators', 
	 'previous_error', 'profiling_info', 'profiling_level', 
	 'read_concern', 
	 'read_preference', 'remove_user', 'reset_error_history', 
	 'set_profiling_level', 'system_js', 
	 'validate_collection', 'watch', 'write_concern']

	"""
	"""
from urllib.parse import quote_plus
uri = "mongodb://{user}:{passwd}@{host}/{default_db}?authSource={authDB}&replicaSet={replSetName}&connect=true".format (\
	user=quote_plus("mongo_admin"),passwd=quote_plus("MarshDb@July2019"), \
	host=quote_plus("usdf23v0466:27011,usdf23v0467:27011,usdf23v0355:27011") ,\
	default_db=quote_plus("admin"),authDB=quote_plus("admin"),replSetName=quote_plus("rep_devqa01") )

	"""

	"""
	searching on date, removing ts
	db.camps.aggregate(
   [
     // Perform the initial match to filter docs by 'status' and 'camp_id'
     {
       $match:
         {
           status: 1,
           camp_id: pCampID
         }
     },
     // Extract the year, month and day portions of the 'enddate' 
     {
       $project:
         {
           year: { $year: "$enddate" },
           month: { $month: "$enddate" },
           day: { $dayOfMonth: "$enddate" },
           status: 1,
           camp_id: 1
         }
     },
     // Filter by date - Replace hard-coded values with values you want
     {
       $match:
         {
           year: { $gte: 2014 },
           month: { $gte: 10 },
           day: { $gte: 10 }
         }
     }
   ]
)
	"""

"""
Specify Multiple Conditions for Array of Documents
When specifying conditions on more than one field nested in an array of documents, you can specify the query such that either a single document meets these condition or any combination of documents (including a single document) in the array meets the conditions.

A Single Nested Document Meets Multiple Query Conditions on Nested Fields
Use $elemMatch operator to specify multiple criteria on an array of embedded documents such that at least one embedded document satisfies all the specified criteria.

# update field value from another field
db.tenant.configs.updateMany(
	{},[{ 
		$set: { 
			config: {
				"auditLog" : "$auditLog", 
				"net" : "$net", 
				"processManagement" : "$processManagement", 
				"replication" : "$replication", 
				"security" : "$security", 
				"setParameter" : "$setParameter",
				"storage" : "$storage", 
				"systemLog" : "$systemLog" 
			} 
		}
	}],
);
# remove field
db.tenant.configs.updateMany(
	{},
	{ 
		$unset: { 
			"auditLog" : "", 
			"net" : "", 
			"processManagement" : "", 
			"replication" : "", 
			"security" : "", 
			"setParameter" : "",
			"storage" : "", 
			"systemLog" : "" 
		}
	},
);
# add month/year to statistics where statsType is storge and this field is not present
db.statistics.updateMany(
	{"statsType" : "storage", "month" : {"$exists" : false}, "year" : {"$exists" : false}},
	[
		{$addFields: { 
			"month" : {"$month" : "$scanDate"}, 
			"year" : {"$year" : "$scanDate"} 
			} 
		}
	]
);

# update 


# remove top or last (based on sort) n doc stored in an array
db.tenant.configs.updateMany({}, {
	"$push" : {
		"history" : {
			"$each" : [], 
			"$sort" : {"ts" : 1},
			"$slice" : 2
		}
	}
});

# for each function (updating hostId from scanid)
db.getCollection('host.change.history').find({"scanId" : "12102020_002003.nam.marsh.usdf24v0213.mrshmc.com"}).forEach(function (doc) {
	doc.hostId = doc.scanId.split(".").slice(-3).join(".");
	print (doc.hostId);
	db.host.change.history.save(doc);
})


#  Group by count and having clause (group by hostname , count total host which has count more than one)
db.hosts.aggregate([
	{"$group" : {"_id" : "$hostName", "total" : {$sum: 1}}},
	{"$match" : {"total": {"$gt" : 1 }}}
])

# remove duplicate (based on hosname)
db.hosts.aggregate([
  { $group: { 
    _id: { 'hostName': "$hostName"}, // can be grouped on multiple properties 
    dups: { "$addToSet": "$_id" }, 
    count: { "$sum": 1 } 
  }}, 
  { $match: { 
    count: { "$gt": 1 }    // Duplicates considered as count greater than one
  }}
],
{allowDiskUse: true}       // For faster processing if set is larger
)               // You can display result until this and check duplicates 
.forEach(function(doc) {
    doc.dups.shift();      // First element skipped for deleting
    db.hosts.deleteMany({_id : {$in: doc.dups }});  // Delete remaining duplicates
})

# create duplicate collection with data from other collection
db.hosts.find().forEach(function(d){ db.getSiblingDB('audit_prod')['hosts_backup'].bulkwrite(d); });
db.hosts.find().forEach(function(d){ db.getSiblingDB('audit_prod')['hosts_backup'].insertMany(d); });

"""