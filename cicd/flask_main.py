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
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.common.error import *

"""
Run Flask in production
https://flask.palletsprojects.com/en/1.1.x/tutorial/deploy/
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
		from com.mmc.cicd.factory import Factory
		from com.mmc.cicd.cicd_repo_pg import Repository

		self.util = Utility()
		self.Globals = Globals()
		self.infra = Infrastructure()
		self.sec = Security()

		self.REST_API_CALL_KEYS = ["encKey","method","args","userId"]

		self.LOGGER = logging.getLogger(__name__)

		self.LOGGER.info('instantiating Process request class')

		self.RESPONSE = {"status" : "", "message" : "", "data" : [], "request" : ""}		


		#got_request_exception.connect(self.log_exception, app)

	#def log_exception(self, sender, exception, **extra):
	#	print(sender, exception, extra)

	def get(self):
		return {'about': 'Process Request'}

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
		try:
			#from com.mmc.common.security import Security
			#sec = Security()
			myRequest = self.util.getACopy(request.get_json())

			myValidationResult = self.validateRequest(myRequest)

			if myValidationResult["status"] == self.Globals.unsuccess:
				return jsonify(myValidationResult)

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

			# authenticating
			mySecurityToken = self.sec.authenticate(self.infra.environment["cicd"]["deployUser"][self.util.getEnvKeyVal("ENV")]["domainAdUser"], myRequest["encKey"])
			
			# retrieving trusted proxies
			#print('sec token', mySecurityToken)

			repo = Repository(mySecurityToken)

			myStartTime = repo.util.getStartTimeSecs()

			myTrustedProxies = repo.getTrustedProxies(mySecurityToken)

			myRequest.update({"securityToken" : mySecurityToken})
			#print("my request >>>",myRequest)

			myRequest.pop("encKey")

			try:
				# starting session
				# startSession(self, securityToken, userId, sessionAuth, accessRoute, request, comments)
				mySessionId = repo.startSession(mySecurityToken, myRequest["userId"], {"auth" : "AD authentication"}, myRequest["accessRoute"],myRequest, "new session for rest api")

			except Exception as error:
				self.LOGGER.error("error creating new session >> {error} ".format(error= str(error)), exc_info = True)
				raise error

			try:
				myFactory = Factory(myRequest["securityToken"])

				myResponse = myFactory.processRequest(myRequest)
				
				# completing session			
				myElapsed = repo.util.getElapsedTime(myStartTime)
				repo.completeSession(mySecurityToken, mySessionId, myElapsed, myResponse["status"])

			except Exception as error:
				self.LOGGER.error("error processing request >> {error} ".format(error= str(error)), exc_info = True)
				raise error

			return jsonify(myResponse)

		except Exception as error:
			# we need to commit transaction (pg initiates a transaction even for select. As all changes are controlled by method cicd_repo_pg in, its safe to 
			# commit here
			repo.completeSession(mySecurityToken, mySessionId, '00:00:00', self.Globals.unsuccess)
			self.LOGGER.error('an error occurred during post request >>> {error}'.format(error = str(error)), sys)
			return jsonify(self.util.buildResponse('error', str(error)))

class AuditRequest(Resource):
	"""
	Process Audit requests
	"""

	def __init__(self):
		from com.mmc.audit.aud_globals import Globals
		from com.mmc.audit.factory import Factory

		self.util = Utility()
		self.Globals = Globals()
		self.infra = Infrastructure()
		self.sec = Security()

		self.REST_API_CALL_KEYS = ["encKey","method","args","userId"]

		self.LOGGER = logging.getLogger(__name__)

		self.LOGGER.info('instantiating Process request class')

		self.RESPONSE = {"status" : "", "message" : "", "data" : [], "request" : ""}		

		#got_request_exception.connect(self.log_exception, app)

	#def log_exception(self, sender, exception, **extra):
	#	print(sender, exception, extra)

	def get(self):
		return {'about': 'Audit Process Request'}

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
		try:
			#from com.mmc.common.security import Security
			#sec = Security()
			myRequest = self.util.getACopy(request.get_json())

			myValidationResult = self.validateRequest(myRequest)

			if myValidationResult["status"] == self.Globals.unsuccess:
				return jsonify(myValidationResult)

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

			# authenticating
			mySecurityToken = self.sec.authenticate(self.infra.environment["boot"]["auditScanUer"][self.util.getEnvKeyVal("ENV")], myRequest["encKey"])
			
			""" commenting trusted proxies, will add it later
			# retrieving trusted proxies
			# print('sec token', mySecurityToken)

			repo = Repository(mySecurityToken)

			myStartTime = self.util.getStartTimeSecs()

			myTrustedProxies = repo.getTrustedProxies(mySecurityToken)
			"""
			myRequest.update({"securityToken" : mySecurityToken})
			#print("my request >>>",myRequest)

			# removing enckey
			myRequest.pop("encKey")

			# commeting session management, will add later
			"""
			# starting session
			try:
				# starting session
				# startSession(self, securityToken, userId, sessionAuth, accessRoute, request, comments)
				mySessionId = repo.startSession(mySecurityToken, myRequest["userId"], {"auth" : "AD authentication"}, myRequest["accessRoute"],myRequest, "new session for rest api")

			except Exception as error:
				self.LOGGER.error("error creating new session >> {error} ".format(error= str(error)), exc_info = True)
				raise error
			"""
			try:
				myFactory = Factory(myRequest["securityToken"])

				myResponse = myFactory.processRequest(myRequest)
				
			except Exception as error:
				self.LOGGER.error("error processing request >> {error} ".format(error= str(error)), exc_info = True)
				raise error

			# commeting session management, will add later
			"""
			# completing session			
			myElapsed = repo.util.getElapsedTime(myStartTime)
			repo.completeSession(mySecurityToken, mySessionId, myElapsed, myResponse["status"])
			"""
			return jsonify(myResponse)

		except Exception as error:
			# we need to commit transaction (pg initiates a transaction even for select. As all changes are controlled by method cicd_repo_pg in, its safe to 
			# commit here

			# commeting session management, will add later
			#repo.completeSession(mySecurityToken, mySessionId, '00:00:00', self.Globals.unsuccess)
			self.LOGGER.error('an error occurred during post request >>> {error}'.format(error = str(error)), sys)
			return jsonify(self.util.buildResponse('error', str(error)))

api.add_resource(CICDRequest,'/api/cicd/processRequest', endpoint='cicd')
api.add_resource(AuditRequest,'/api/audit/processRequest', endpoint='audit')

if __name__ == '__main__':
	# we need to read the config file to strat the app on givne port
	app.run(debug=True,host='0.0.0.0', port=8000, threaded=True)




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


#https://pythonhosted.org/Flask-Session/