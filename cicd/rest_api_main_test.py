from flask_httpauth import HTTPBasicAuth
from flask import request, Flask, make_response, jsonify, session, flash, redirect, escape, json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from datetime import timedelta

import time, secrets

app = Flask(__name__)

app.config["DEBUG"] = True
app.config["TESTING"] = True
secret_key = "testing"

# reinitialize app
#app.login_manager.init_app(app)

auth = HTTPBasicAuth()

#token = secrets.url_safe()
users = {
    "anil.patcha": generate_password_hash("anil.patcha"),
    "anil.singh": generate_password_hash("anil.singh")
}

#myEnvironment = request.environ.get('HTTP_X_REAL_IP', request.remote_addr) 

"""
@app.route('/', methods=['GET'])
def home():
	return "<h1>Distant Reading Archive</h1><p>This site is a prototype API for distant reading of science fiction novels.</p>"
"""
@app.before_request
def make_session_permanent():
	session.permanet=True
	app.permanent_session_lifetime = timedelta(minutes=5)

@app.route('/', methods=['GET'])
def home():
	return '''<h1>Distant Reading Archive</h1>
<p>A prototype API for distant reading of science fiction novels.</p>'''

# A route to return all of the available entries in our catalog.


@app.route('/api/v1/cicd/processRequest', methods=['POST'])
@auth.login_required
def processRequest():
	myRequest = request.get_json()
	print("request type", type(myRequest))
	if not isinstance(myRequest, dict):
		return jsonify({"status" : "Error", "message" : "request must be json type"})

	if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
		remoteAddr = request.environ['REMOTE_ADDR']
	else:
		remoteAddr = request.environ['HTTP_X_FORWARDED_FOR'] # if behind a proxy
    
	response = {
		"status" : "Success", 
		"message" : "Success", 
		'ts' : str(time.ctime()), 
		"data" : {'ip': request.remote_addr, 'client_ip' : remoteAddr},
		"request" : myRequest

	}
	return jsonify(response)

	#return jsonify({'request' : myRequest, 'from_ip': request.remote_addr, 'client_ip' : remoteAddr, 'message' : 'Success', 'when' : str(time.ctime()) })

@app.route('/api/v1/cicd/testingParam/<int:num>', methods=['GET','POST'])
def testingParam(num):
	pass

@app.route('/api/v1/cicd/test', methods=['GET'])
@auth.login_required
def api_all():

	if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
		remoteAddr = request.environ['REMOTE_ADDR']
	else:
		remoteAddr = request.environ['HTTP_X_FORWARDED_FOR'] # if behind a proxy
	response = {
		"status" : "Success", 
		"message" : "Success", 
		'ts' : str(time.ctime()), 
		"data" : {'ip': request.remote_addr, 'client_ip' : remoteAddr}
	}
	return jsonify(response)

	#request.environ['REMOTE_ADDR']

@app.errorhandler(404)
def page_not_found(e):
	return "<h1>404</h1><p>The resource could not be found.</p>", 404

@auth.verify_password
def verify_password(username, password):
    if username in users:
        return check_password_hash(users.get(username), password)
    return False

@auth.get_password
def get_password(username):
	if username == 'miguel':
		return 'python'
	return None

if __name__ == '__main__':
	app.run(debug=True,host='0.0.0.0', port=8000)


"""
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

auth = HTTPBasicAuth()

@auth.get_password
def get_password(username):
    if username == 'miguel':
        return 'python'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

@auth.login_required
def get_tasks():
    return jsonify({'tasks': tasks})

from flask import Flask, request
from flask_restful import Resource, Api

app = Flask(__name)
api = Api(app)

class HelloWorld(resource):
	def get(self):
		return {'about': 'Hello World'}

	def post(self):
		request = request.get_json()
		return ({"request" : request})

class Multi(Resource):
	def get(self, num):
		return {'result' : num * 10}

api.add_resource(HelloWorld,'/')
api.add_resource(Multi,'/multi/<int:num>')

if __name__ == '__main__':
	app.run(debug=True)
"""