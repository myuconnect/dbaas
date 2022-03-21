from flask_httpauth import HTTPBasicAuth
from flask import request, Flask, make_response, jsonify, session, flash, redirect, escape, json, got_request_exception
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from datetime import timedelta
from flask_restful import Resource, Api, reqparse
from functools import wraps
from flask.logging import default_handler
import time, secrets

import logging, logging.config, sys

from com.mmc.common.utility import Utility
from com.mmc.common.globals import Globals
from com.mmc.common.security import Security
from com.mmc.common.factory import Factory
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.common.error import *

"""
Run Flask in production
https://flask.palletsprojects.com/en/1.1.x/tutorial/deploy/
"""
"""
gunicorn : https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04
"""

app = Flask(__name__)

app.config["DEBUG"] = True
app.config["TESTING"] = True
secret_key = "testing"

api = Api(app, catch_all_404s=True)
parser = reqparse.RequestParser()

# reinitialize app
#app.login_manager.init_app(app)

auth = HTTPBasicAuth()

#token = secrets.url_safe()
users = {
	"anil.patcha": generate_password_hash("anil.patcha"),
	"anil.singh": generate_password_hash("anil.singh")
}

class CICDRequest(Resource):
	"""
	Process CICD request class mapped to /app/cicd/processRequest
	"""
	def __init__(self):
		from os import environ
		from com.mmc.common.factory import Factory

		self.util = Utility()
		self.Globals = Globals()
		self.sec = Security()

		self.REST_API_CALL_KEYS = ["encKey","method","args","userId"]

		self.RESPONSE = {"status" : "", "message" : "", "data" : [], "request" : ""}		

		# validating flask env variable
		myAllEnvKeys = list(environ.keys())

		myFlaskEnv = ['FLASK_APP','FLASK_HOME','FLASK_CONFIG','FLASK_LOG']

		if not all(env in myAllEnvKeys for env in myFlaskEnv):
			raise ValueError("Flask environment is not set, aborting !!!")

		# flask env is set, loading flask configuration
		myFlaskCfgFile = self.util.buildPath(self.util.getEnvKeyVal("FLASK_CONFIG"),"flask_config.json")

		if not self.util.isFileExists(myFlaskCfgFile):
			raise ValueError(f"missing flask config file {myFlaskCfgFile}, aborting  !!!")

		# loading flask config file
		try:
			self.FLASK_CONFIG = self.util.readJsonFile(myFlaskCfgFile)
			if not self.FLASK_CONFIG:
				raise ValueError("empty flask config file, aborting !!!")

		except Exception as error:
			raise ValueError(f"bootstrap error, unable to read/identifiy config file {myFlaskCfgFile} !!!")

		# checking if Audit env config is found in flask config
		if self.util.getEnvKeyVal("ENV") not in self.FLASK_CONFIG:
			raise ValueError(f"Audit config for {self.util.getEnvKeyVal('ENV')} is missing in flask config, aborting !!!")

		myFlaskEnvConfig = self.FLASK_CONFIG[self.util.getEnvKeyVal("ENV")]

		self.setAppEnv()

		"""
		self.APP_NAME = "CICD"

		if self.APP_NAME not in myFlaskEnvConfig:
			raise ValueError(f"flask config is missing for application {self.APP_NAME} aborting !!!")

		# setting Audit environment variables

		self.util.setEnvKeyVal("APP_NAME", self.APP_NAME)
		self.util.setEnvKeyVal("END_POINT", myFlaskEnvConfig[self.APP_NAME]["endPoint"])
		self.util.setEnvKeyVal("CICD_HOME", myFlaskEnvConfig[self.APP_NAME]["home_loc"])
		self.util.setEnvKeyVal("APP_HOME", myFlaskEnvConfig[self.APP_NAME]["home_loc"])
		self.util.setEnvKeyVal("CICD_CONFIG", myFlaskEnvConfig[self.APP_NAME]["config_loc"])
		self.util.setEnvKeyVal("APP_CONFIG", myFlaskEnvConfig[self.APP_NAME]["config_loc"])
		self.util.setEnvKeyVal("CICD_LOG", myFlaskEnvConfig[self.APP_NAME]["log_loc"])
		self.util.setEnvKeyVal("APP_LOG", myFlaskEnvConfig[self.APP_NAME]["log_loc"])

		print("APP_NAME", self.util.getEnvKeyVal("APP_NAME"))
		print("CICD_HOME", self.util.getEnvKeyVal("CICD_HOME"))
		print("APP_CONFIG", self.util.getEnvKeyVal("APP_CONFIG"))
		print("APP_LOG", self.util.getEnvKeyVal("APP_LOG"))
		"""

		try:
			self.infra = Infrastructure()
		except Exception as error:
			raise ValueError(f"bootstrap error, failed to initialized infrastructure, error >> {error}, aborting !!!")

		self.LOGGER = logging.getLogger(__name__)

		self.LOGGER.info('instantiating Process request class')


		#got_request_exception.connect(self.log_exception, app)

	#def log_exception(self, sender, exception, **extra):
	#	print(sender, exception, extra)

	def setAppEnv(self):
		"""
		Setting environment for AUDIT app
		"""
		try:
			myFlaskEnvConfig = self.FLASK_CONFIG[self.util.getEnvKeyVal("ENV")]

			self.APP_NAME = "CICD"

			if self.APP_NAME not in myFlaskEnvConfig:
				raise ValueError(f"flask config is missing for application {self.APP_NAME} aborting !!!")

			# setting Audit environment variables
			print("flask config file content >>>", myFlaskEnvConfig)
			self.util.setEnvKeyVal("APP_NAME", self.APP_NAME)
			self.util.setEnvKeyVal("END_POINT", myFlaskEnvConfig[self.APP_NAME]["endPoint"])
			self.util.setEnvKeyVal("APP_HOME", myFlaskEnvConfig[self.APP_NAME]["home_loc"])
			self.util.setEnvKeyVal("CICD_HOME", myFlaskEnvConfig[self.APP_NAME]["home_loc"])
			self.util.setEnvKeyVal("APP_CONFIG", myFlaskEnvConfig[self.APP_NAME]["config_loc"])
			self.util.setEnvKeyVal("CICD_CONFIG", myFlaskEnvConfig[self.APP_NAME]["config_loc"])
			self.util.setEnvKeyVal("APP_LOG", myFlaskEnvConfig[self.APP_NAME]["log_loc"])
			self.util.setEnvKeyVal("CICD_LOG", myFlaskEnvConfig[self.APP_NAME]["log_loc"])

		except Exception as error:
			raise error

	def get(self):
		return {'about': 'Welcome to CICD Process Request, GET method is disabled, Pls use POST method !!!'}

	"""
	def _require_token(func):
		# verifies the uuid/token combo of the given account. account type can be: customer, fox, merchant
		@wraps(func)
		def decorator(*args, **kwargs):
			if request.authorization:
				uuid = request.authorization.username
				token = request.authorization.password
				try:
					manager = SessionManager()
					valid = manager.verify(uuid, token)
					if not valid:
						return UnauthorizedResponseJson().make_response()
				except Exception as e:
					traceback.print_exc()
					return ExceptionResponseJson("unable to validate credentials", e).make_response()
			else:
				return UnauthorizedResponseJson().make_response()
			return func(*args, **kwargs)
		return decorator 
	"""
	#@_require_token
	
	def validateRequest(self, request):
		print("request >>>", request)
		requestKeyList = list(request.keys())
		#print(requestKeyList, set(self.REST_API_CALL_KEYS))

		# validating should move to factory class
		if not isinstance(request, dict):
			myResponse = {"status" : "Error", "message" : "request must be json type", "request" : request}
			return jsonify(myResponse)

		if not (set(requestKeyList) == set(self.REST_API_CALL_KEYS)):
			return self.util.buildResponse(self.Globals.unsuccess, "allowed arguments --> (encKey/userId/method/args) !!!")
		else:
			return self.util.buildResponse(self.Globals.success, self.Globals.success)
		"""
		if "encKey" not in request or "args" not in request:
			return {"status" : "error", "message" : "Missing mandatory arguments (encKey/method/args)"}
		else:
			return {"status" : "success", "message" : "success"}

		if "securityToken" in request:
			request.pop("securityToken")
		"""

	def post(self):
		# request.json
		"""
		{
			"encKey" : <encrypted key>,
			"method" : <method_name; str>
			"args" :  <param; dict (key/value pair),
			"user" : "userid"
		}
		"""
		print("starting")
		from com.mmc.cicd.cicd_repo_pg import Repository
		print("ending")

		# setting environment for this post
		print("setting env")
		self.setAppEnv()

		# reloading logging config for this app, as this might have changed if previous call was for cicd
		print("changing log config for this app")
		self.infra._Infrastructure__configAppLogging(self.APP_NAME)

		self.LOGGER = logging.getLogger(__name__)

		myRequest = self.util.getACopy(request.get_json())

		#creating security token upon successful credential authentication
		myRequiredArgs = ["encKey","userId","method","args"]

		if not self.util.isListItemExistsInAList(myRequiredArgs, list(myRequest.keys())):
			return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"authnetication failed !!!"))

		try:
			# authenticating (audit scan user)
			print(list(self.infra.environment.keys()))

			myAuthUser = self.infra.environment["cicd"]["deployUser"][self.util.getEnvKeyVal("ENV")]["domainAdUser"]

			self.LOGGER.info(f'authenticating enc key {myRequest["encKey"]} for user {myAuthUser}' )
			mySecurityToken = self.sec.authenticate(myAuthUser, myRequest["encKey"])
			self.LOGGER.info(f'got security token >> {mySecurityToken}' )

			# retrieving trusted proxies
			#print('sec token', mySecurityToken)
		except Exception as error:
			self.LOGGER.error('an error occurred while while authenticating enc key, error >> {error}'.format(error = str(error)), exc_info = True)
			return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"authnetication failed !!!"))

		# credential is good proceeding with request validation
		try:
			myValidationResult = self.validateRequest(myRequest)

			if myValidationResult["status"] == self.Globals.unsuccess:
				return jsonify(myValidationResult)

		except Exception as error:
			self.LOGGER.error('an error occurred while while validating request, error >> {error}'.format(error = str(error)), exc_info = True)
			return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"an error occurred while while validating request, error >> {error} ) !!!"))

		# validation is good, updating security token to request
		myRequest.update({"securityToken" : mySecurityToken})
		self.
		# updating remote addr and access route to request (this would be needed further enhancing security)
		try:
			#print("request >>>",myRequest, request.host)
			#print('header >>>', request.headers)
			#print('remote >>>', request.remote_addr, ':', request.referrer, ':', request.remote_user, ':', request.routing_exception)

			if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
				myRequest.update({"remoteAddr" : request.environ['REMOTE_ADDR']})
				#self.PYTHON_VER = request.get_json
			else:
				myRequest.update({"remoteAddr" : request.environ['HTTP_X_FORWARDED_FOR']})
				#self.REMOTE_ADDR = request.environ['HTTP_X_FORWARDED_FOR'] # if behind a proxy
			# updating access list

			myRequest.update({"accessRoute" : list(request.access_route)})

		except Exception as error:
			self.LOGGER.error('an error occurred while updating access route/remote addr, error >> {error} !!!'.format(error = str(error)), exc_info = True)
			return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"an error occurred while updating access route/remote addr, error >> {error} !!!"))

		# all checks are passed, proceeding with persisting session metadata
		try:
			self.LOGGER.info(f"security token generated >> {mySecurityToken}")
			repo = Repository(mySecurityToken)

			# persisting session informtion
			myStartTime = repo.util.getStartTimeSecs()
			myTrustedProxies = repo.getTrustedProxies(mySecurityToken)

			myRequest.update({"securityToken" : mySecurityToken})

			myRequest.pop("encKey")

			# starting session
			# startSession(self, securityToken, userId, sessionAuth, accessRoute, request, comments)
			mySessionId = repo.startSession(mySecurityToken, myRequest["userId"], {"auth" : "AD authentication"}, myRequest["accessRoute"],myRequest, "new session for rest api")

		except Exception as error:
			self.LOGGER.error("an error occurred while initiating session, error >> {error} !!!".format(error= str(error)), exc_info = True)
			return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"an error occurred while initiating session, error >> {error} !!!"))

		# processing request
		try:
			print("processing request")
			myFactory = Factory(myRequest["securityToken"])

			myResponse = myFactory.processRequest(myRequest)
				
		except Exception as error:
			self.LOGGER.error("an error occurred while processing request, error >> {error} ".format(error= str(error)), exc_info = True)
			myRespons = self.util.buildResponse(self.Globals.unsuccess, f"an error occurred while processing request, error >> {error} !!!")

		# copleting session, saving session (end) metadata
		try:
			# completing session
			myElapsed = repo.util.getElapsedTime(myStartTime)
			repo.completeSession(mySecurityToken, mySessionId, myElapsed, myResponse["status"])
			return jsonify(myResponse)

		except Exception as error:
			# we need to commit transaction (pg initiates a transaction even for select. As all changes are controlled by method cicd_repo_pg in, its safe to 
			# commit here
			self.LOGGER.error('an error occurred during post request, error >> {error} !!!'.format(error = str(error)), exc_info = True)
			repo.completeSession(mySecurityToken, mySessionId, '00:00:00', self.Globals.unsuccess)
			return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"an error occurred during post request, error >> {error} !!!"))

class AuditRequest(Resource):
	"""
	Process Audit request class mapped to /app/cicd/processRequest
	"""
	def __init__(self):
		from os import environ

		self.util = Utility()
		self.sec = Security()
		self.Globals = Globals()

		self.REST_API_CALL_KEYS = ["apiKey","method","args","userId"]

		self.RESPONSE = {"status" : "", "message" : "", "data" : [], "request" : ""}		

		# validating flask env variable
		myAllEnvKeys = list(environ.keys())

		myFlaskEnv = ['FLASK_APP','FLASK_HOME','FLASK_CONFIG','FLASK_LOG']

		if not all(env in myAllEnvKeys for env in myFlaskEnv):
			raise ValueError("Flask environment is not set, aborting !!!")

		# flask env is set, loading flask configuration
		myFlaskCfgFile = self.util.buildPath(self.util.getEnvKeyVal("FLASK_CONFIG"),"flask_config.json")

		if not self.util.isFileExists(myFlaskCfgFile):
			raise ValueError(f"missing flask config file {myFlaskCfgFile}, aborting  !!!")

		# loading flask config file
		try:
			self.FLASK_CONFIG = self.util.readJsonFile(myFlaskCfgFile)
			if not self.FLASK_CONFIG:
				raise ValueError("empty flask config file, aborting !!!")

		except Exception as error:
			raise ValueError(f"bootstrap error, unable to read/identifiy config file {myFlaskCfgFile} !!!")

		# checking if Audit env config is found in flask config
		if self.util.getEnvKeyVal("ENV") not in self.FLASK_CONFIG:
			raise ValueError(f"Audit config for {self.util.getEnvKeyVal('ENV')} is missing in flask config, aborting !!!")

		# setting application (AUDIT) specific environment
		self.setAppEnv()

		"""
		myFlaskEnvConfig = self.FLASK_CONFIG[self.util.getEnvKeyVal("ENV")]

		self.APP_NAME = "AUDIT"

		if self.APP_NAME not in myFlaskEnvConfig:
			raise ValueError(f"flask config is missing for application {self.APP_NAME} aborting !!!")

		# setting Audit environment variables

		self.util.setEnvKeyVal("APP_NAME", self.APP_NAME)
		self.util.setEnvKeyVal("END_POINT", myFlaskEnvConfig[self.APP_NAME]["endPoint"])
		self.util.setEnvKeyVal("AUDIT_HOME", myFlaskEnvConfig[self.APP_NAME]["home_loc"])
		self.util.setEnvKeyVal("APP_HOME", myFlaskEnvConfig[self.APP_NAME]["home_loc"])
		self.util.setEnvKeyVal("AUDIT_CONFIG", myFlaskEnvConfig[self.APP_NAME]["config_loc"])
		self.util.setEnvKeyVal("APP_CONFIG", myFlaskEnvConfig[self.APP_NAME]["config_loc"])
		self.util.setEnvKeyVal("AUDIT_LOG", myFlaskEnvConfig[self.APP_NAME]["log_loc"])
		self.util.setEnvKeyVal("APP_LOG", myFlaskEnvConfig[self.APP_NAME]["log_loc"])

		print("APP_NAME", self.util.getEnvKeyVal("APP_NAME"))
		print("AUDIT_HOME", self.util.getEnvKeyVal("AUDIT_HOME"))
		print("APP_CONFIG", self.util.getEnvKeyVal("APP_CONFIG"))
		print("APP_LOG", self.util.getEnvKeyVal("APP_LOG"))
		"""
		
		# setting application environment

		self.setAppEnv()

		try:
			self.infra = Infrastructure()
		except Exception as error:
			raise ValueError(f"bootstrap error, failed to initialized infrastructure, error >> {error}, aborting !!!")

		self.LOGGER = logging.getLogger(__name__)

		self.LOGGER.info('instantiating Process request class')

		#got_request_exception.connect(self.log_exception, app)

	#def log_exception(self, sender, exception, **extra):
	#	print(sender, exception, extra)

	def get(self):
		return {'about': 'Welcome to AUDIT Process Request, GET method is disabled, Pls use POST method !!!'}

	"""
	def _require_token(func):
		# verifies the uuid/token combo of the given account. account type can be: customer, fox, merchant
		@wraps(func)
		def decorator(*args, **kwargs):
			if request.authorization:
				uuid = request.authorization.username
				token = request.authorization.password
				try:
					manager = SessionManager()
					valid = manager.verify(uuid, token)
					if not valid:
						return UnauthorizedResponseJson().make_response()
				except Exception as e:
					traceback.print_exc()
					return ExceptionResponseJson("unable to validate credentials", e).make_response()
			else:
				return UnauthorizedResponseJson().make_response()
			return func(*args, **kwargs)
		return decorator 
	"""
	#@_require_token
	
	def validateRequest(self, request):
		requestKeyList = list(request.keys())
		#print(requestKeyList, set(self.REST_API_CALL_KEYS))

		self.LOGGER.debug(f"validating request {request}")
		# validating should move to factory class
		if not isinstance(request, dict):
			myResponse = {"status" : "Error", "message" : "request must be json type", "request" : request}
			return jsonify(myResponse)

		myRequiredArgs = ["userId","method","args"]
		if not self.util.isListItemExistsInAList(myRequiredArgs, requestKeyList):
			self.LOGGER.debug(f"missing mandatory arguments [userId/method/args/apiKey/password] in request >>> {request}")
			return self.util.buildResponse(self.Globals.unsuccess, f"missing mandatory arguments [userId/method/args/apiKey/password] >>>  {request} !!!")

		if not self.util.isAnyElemInListExistsInAList(["password","apiKey"], requestKeyList):
			self.LOGGER.debug(f"missing mandatory arguments apiKey/password in request >>> {request}")
			return self.util.buildResponse(self.Globals.unsuccess, f"missing mandatory arguments in request >>>  {request} !!!")

		return self.util.buildResponse(self.Globals.success, self.Globals.success)

	def setAppEnv(self):
		"""
		Setting environment for AUDIT app
		"""
		try:
			myFlaskEnvConfig = self.FLASK_CONFIG[self.util.getEnvKeyVal("ENV")]

			self.APP_NAME = "AUDIT"

			if self.APP_NAME not in myFlaskEnvConfig:
				raise ValueError(f"flask config is missing for application {self.APP_NAME} aborting !!!")

			# setting Audit environment variables
			self.util.setEnvKeyVal("APP_NAME", self.APP_NAME)
			self.util.setEnvKeyVal("END_POINT", myFlaskEnvConfig[self.APP_NAME]["endPoint"])
			self.util.setEnvKeyVal("APP_HOME", myFlaskEnvConfig[self.APP_NAME]["home_loc"])
			self.util.setEnvKeyVal("AUDIT_HOME", myFlaskEnvConfig[self.APP_NAME]["home_loc"])
			self.util.setEnvKeyVal("AUDIT_CONFIG", myFlaskEnvConfig[self.APP_NAME]["config_loc"])
			self.util.setEnvKeyVal("APP_CONFIG", myFlaskEnvConfig[self.APP_NAME]["config_loc"])
			self.util.setEnvKeyVal("AUDIT_LOG", myFlaskEnvConfig[self.APP_NAME]["log_loc"])
			self.util.setEnvKeyVal("APP_LOG", myFlaskEnvConfig[self.APP_NAME]["log_loc"])

		except Exception as error:
			raise error

	def post(self):
		# request.json
		"""
		{
			"encKey" : <encrypted key>,
			"method" : <method_name; str>
			"args" :  <param; dict (key/value pair),
			"user" : "userid"
		}
		"""
		
		#from com.mmc.audit.mongo_repo import Repository

		#self.APP_NAME = "AUDIT"
		# setting application (AUDIT) specific environment variables
		self.setAppEnv()

		# reloading logging config for this app, as this might have changed if previous call was for cicd
		self.infra._Infrastructure__configAppLogging(self.APP_NAME)

		self.LOGGER = logging.getLogger(__name__)

		myRequest = self.util.getACopy(request.get_json())

		self.LOGGER.info(f"got request >>> {myRequest}")

		myRequiredArgs = ["userId","method","args"]

		# validating request
		try:
			myValidationResult = self.validateRequest(myRequest)

			if myValidationResult["status"] == self.Globals.unsuccess:
				return jsonify(myValidationResult)

		except Exception as error:
			self.LOGGER.error('an error occurred while while validating request, error >> {error}'.format(error = str(error)), exc_info = True)
			return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"an error occurred while while validating request, error >> {error} ) !!!"))

		"""
		if not self.util.isListItemExistsInAList(myRequiredArgs, list(myRequest.keys())):
			return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"missing mandatory arguments [userId/method/args/apiKey/password] !!!"))

		if not self.util.isAnyElemInListExistsInAList(["password","apiKey"], list(myRequest.keys())):
			return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"missing mandatory arguments apiKey/password !!!"))
		"""
		# we might have got userid/password or userod/apiKey, if we have apikey we will ignore password
		if "apiKey" in list(myRequest.keys()):
			myRequiredArgs = ["userId","apiKey","method","args"]

			if not self.util.isListItemExistsInAList(myRequiredArgs, list(myRequest.keys())):
				return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"authnetication failed !!!"))

			self.LOGGER.debug(f"authenticating api key {myRequest['apiKey']} for user {myRequest['userId']}" )
			try:
				mySecurityToken = self.sec.authenticate(myRequest['userId'], myRequest['apiKey'])
				self.LOGGER.debug(f'got security token >> {mySecurityToken}' )
			except Exception as error:
				self.LOGGER.error(f"an error occurred while while authenticating api key, error >> {str(error)}", exc_info = True)
				return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"authnetication failed !!!"))

		else:
			# we got password, will authenticate and generate the sec key
			myRequiredArgs = ["userId","password","method","args"]

			if not self.util.isListItemExistsInAList(myRequiredArgs, list(myRequest.keys())):
				return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"authnetication failed !!!"))

			self.LOGGER.debug(f"authenticating userid, password {myRequest['password']} for user {myRequest['userId']}" )
			try:
				mySecurityToken = self.sec.authenticate(myRequest["userId"], myRequest["password"])
				self.LOGGER.debug(f'got security token >> {mySecurityToken}' )
			except Exception as error:
				self.LOGGER.error(f"an error occurred while while authenticating api key, error >> {str(error)}", exc_info = True)
				return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"authnetication failed !!!"))
		"""
		#creating security token upon successful credential authentication
		try:
			# authenticating (audit scan user)
			#print(list(self.infra.environment.keys()))

			self.LOGGER.debug(f'authenticating enc key {myRequest["encKey"]} for user {self.infra.environment["audit"]["auditScanUser"][self.util.getEnvKeyVal("ENV")]["domainAdUser"]}' )
			mySecurityToken = self.sec.authenticate(self.infra.environment["audit"]["auditScanUser"][self.util.getEnvKeyVal("ENV")]["domainAdUser"], myRequest["encKey"])
			self.LOGGER.debug(f'got security token >> {mySecurityToken}' )

			# retrieving trusted proxies
			#print('sec token', mySecurityToken)
		except Exception as error:
			self.LOGGER.error('an error occurred while while authenticating enc key, error >> {error}'.format(error = str(error)), exc_info = True)
			return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"authnetication failed !!!"))
		"""

		# validation is good, updating security token to request
		myRequest.update({"securityToken" : mySecurityToken})

		# updating remote addr and access route to request (this would be needed further enhancing security)
		try:
			#print("request >>>",myRequest, request.host)
			#print('header >>>', request.headers)
			#print('remote >>>', request.remote_addr, ':', request.referrer, ':', request.remote_user, ':', request.routing_exception)

			if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
				myRequest.update({"remoteAddr" : request.environ['REMOTE_ADDR']})
				#self.PYTHON_VER = request.get_json
			else:
				myRequest.update({"remoteAddr" : request.environ['HTTP_X_FORWARDED_FOR']})
				#self.REMOTE_ADDR = request.environ['HTTP_X_FORWARDED_FOR'] # if behind a proxy
			# updating access list

			myRequest.update({"accessRoute" : list(request.access_route)})

		except Exception as error:
			self.LOGGER.error('an error occurred while updating access route/remote addr, error >> {error} !!!'.format(error = str(error)), exc_info = True)
			return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"an error occurred while updating access route/remote addr, error >> {error} !!!"))

		"""
		commenting session logging, will implement in future
		# all checks are passed, proceeding with persisting session metadata
		try:
			repo = Repository(mySecurityToken)

			# persisting session informtion
			myStartTime = repo.util.getStartTimeSecs()
			myTrustedProxies = repo.getTrustedProxies(mySecurityToken)

			myRequest.update({"securityToken" : mySecurityToken})

			myRequest.pop("encKey")

			# starting session
			# startSession(self, securityToken, userId, sessionAuth, accessRoute, request, comments)
			mySessionId = repo.startSession(mySecurityToken, myRequest["userId"], {"auth" : "AD authentication"}, myRequest["accessRoute"],myRequest, "new session for rest api")

		except Exception as error:
			self.LOGGER.error("an error occurred while initiating session, error >> {error} !!!".format(error= str(error)), exc_info = True)
			return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"an error occurred while initiating session, error >> {error} !!!"))
		"""
		# processing request
		try:
			myResponse = {"unsuccess",f"system error, unable to process factory request {myRequest}, Pls see log server log files for more details !!!"}
			myFactory = Factory(myRequest["securityToken"])
			#print("myrequest >>", myRequest)
			myResponse = myFactory.processRequest(myRequest)
				
		except Exception as error:
			self.LOGGER.error("an error occurred while processing request, error >> {error} ".format(error= str(error)), exc_info = True)
			myRespons = self.util.buildResponse(self.Globals.unsuccess, f"an error occurred while processing request, error >> {error} !!!")

		return jsonify(myResponse)
		"""
		commenting session logging, will implement in future
		# copleting session, saving session (end) metadata
		try:
			# completing session
			myElapsed = repo.util.getElapsedTime(myStartTime)
			repo.completeSession(mySecurityToken, mySessionId, myElapsed, myResponse["status"])
			return jsonify(myResponse)

		except Exception as error:
			# we need to commit transaction (pg initiates a transaction even for select. As all changes are controlled by method cicd_repo_pg in, its safe to 
			# commit here
			self.LOGGER.error('an error occurred during post request, error >> {error} !!!'.format(error = str(error)), sys)
			repo.completeSession(mySecurityToken, mySessionId, '00:00:00', self.Globals.unsuccess)
			return jsonify(self.util.buildResponse(self.Globals.unsuccess, f"an error occurred during post request, error >> {error} !!!"))
		"""
#api.add_resource(CICDRequest,'/api/cicd/processRequest', endpoint='cicd_request')
api.add_resource(AuditRequest,'/api/audit/processRequest', endpoint='audit_request')

if __name__ == '__main__':
	# we need to read the config file to strat the app on givne port
	app.run(debug=True,host='0.0.0.0', port=8000, threaded=True, processes=10)




"""
	#ssh_ca_server.views
	#~~~~~~~~~~~~~~~~~~~~
	#Implement Flask views
from functools import wraps
import logging
from flask import request
import os

from . import app
from .config import Config
from .databag import DataBag
from .ldapclient import LdapClient
from .sshca import CA


def requires_auth(function):
	# Bind against LDAP to ` users credentials

	@wraps(function)
	def decorated(*args, **kwargs):

		logger = logging.getLogger("ca_server")
		auth = request.authorization
		ldap = LdapClient()

		if not auth or not ldap.check_auth(auth.username, auth.password):
			output = DataBag()
			output.set_error("Access denied")
			if hasattr(auth, "username"):
				logger.info("requires_auth: access denied {}".format(auth.username))
			else:
				logger.info("requires_auth: access denied")
			return output.get_json()

		return function(auth.username)
	return decorated

@app.route("/")
def app_root():
	# Base URL request to support client version check & health check

	output = DataBag()
	return output.get_json()

@app.route("/list/cas")
def list_cas():
	#Return full list of available CAs

	output = DataBag()
	output.set_payload(Config.cas)
	return output.get_json()

@app.route("/list/roles")
def list_roles():
	#Return complete list of roles for given user

	requested_username = request.args.get("user")
	output = DataBag()
	ldap = LdapClient()

	if ldap.ldap_connection:
		roles_list = ldap.get_roles()

		authorized_roles = []
		for role in roles_list:
			ldap_group = role['ldap_group']

			if ldap.is_member(requested_username, ldap_group):
				authorized_roles.append(role)

		output.set_payload(authorized_roles)
	else:
		output.set_error("Server issue, please contact your administrator")

	return output.get_json()

@app.route("/get/<ca_name>")
def get_key(ca_name):
	# Return CA public key 

	output = DataBag()

	try:
		requested_ca = CA(ca_name)

	except ValueError:
		output.set_error("Requested CA does not exist")

	else:
		output.set_payload(requested_ca.public_key)

	return output.get_json()


@app.route("/sign", methods=["GET", "POST"])
@requires_auth
def sign_cert_request(username):
	#Sign my public key!!! 

	logger = logging.getLogger("ca_server")
	requested_ca = request.args.get("ca")
	ldap = LdapClient()

	output = DataBag()

	allowed_principals = ldap.get_authorized_principals(username, requested_ca)

	if request.method == "POST" and len(allowed_principals) > 0:
		uploaded_file = request.files["file"]
		filename = os.path.join(Config.upload_folder, uploaded_file.filename)
		uploaded_file.save(filename)

		# Initialize requested CA and sign public key
		try:
			signing_ca = CA(requested_ca)
			cert_file = signing_ca.sign_cert(username, allowed_principals, filename)

		except ValueError:
			output.set_error("Requested CA does not exist")
			logger.info("sign_cert_request: {} requested invalid CA {}".format(username, requested_ca))

		else:
			signed_cert = open(cert_file).read()
			os.remove(cert_file)
			os.remove(filename)

			output.set_payload(signed_cert)
			logger.info("sign_cert_request: {} successful signing request for ({}) -> {}".format(
						username, requested_ca, allowed_principals))

	else:
		output.set_error("Invalid or failed request, please check that you are using a valid CA")
		logger.info("sign_cert_request: {} invalid request".format(username))

	return output.get_json()
"""

"""
gunicorn config
https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04
https://stackoverflow.com/questions/23928213/how-to-get-gunicorn-to-use-python-3-instead-of-python-2-502-bad-gateway
https://www.digitalocean.com/community/questions/gunicorn-service-can-t-read-environment-variables
gunicorn --pythonpath=/opt/ansible/app/source/ wsgi_restapi:app -b 0.0.0.0:8000 --env APP_NAME=FLASK --env FLASK_APP=flask --env BASE_DIR=/opt/ansible/ --env FLASK_HOME=/opt/ansible/app/common --env FLASK_CONFIG=/opt/ansible/app/common/config --env FLASK_LOG=/opt/ansible/app/common/log --env ENV=prod --env APP_CONFIG=/opt/ansible/app/common/config^C
gunicorn --pythonpath=/opt/ansible/app/source/ wsgi_restapi:app -b 0.0.0.0:8000 --env APP_NAME=FLASK --env FLASK_APP=flask --env BASE_DIR=/opt/ansible/ --env FLASK_HOME=/opt/ansible/app/common --env FLASK_CONFIG=/opt/ansible/app/common/config --env FLASK_LOG=/opt/ansible/app/common/log --env ENV=prod --env APP_CONFIG=/opt/ansible/app/common/config --env REGION=NAM --env OPCO=MARSH --env DOMAIN=corp --env DC_LOCATION=dallas --daemon

gunicorn --config /opt/ansible/app/restapi/config/config.py --pythonpath=/opt/ansible/app restapi.wsgi_restapi:app --env APP_NAME=FLASK --env FLASK_APP=flask --env BASE_DIR=/opt/ansible/ --env FLASK_HOME=/opt/ansible/app/common --env FLASK_CONFIG=/opt/ansible/app/common/config --env FLASK_LOG=/opt/ansible/app/common/log --env ENV=prod --env APP_CONFIG=/opt/ansible/app/common/config --env REGION=NAM --env OPCO=MARSH --env DOMAIN=corp --env DC_LOCATION=dallas --env env=prod

https://docs.gunicorn.org/en/stable/settings.html

https://readthedocs.org/projects/gunicorn-docs/downloads/pdf/latest/
gunicorn --daemon

"""
#https://pythonhosted.org/Flask-Session/