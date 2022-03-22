from flask import Flask, url_for, render_template, redirect, request, flash, jsonify, session, g, abort, make_response, session, send_file, send_from_directory
from flask.sessions import SecureCookieSessionInterface
import pandas as pd
import forms, is_safe_url, requests, os, sys
from datetime import timedelta
import logging

from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bootstrap import Bootstrap
from flask_datepicker import datepicker
from flask_caching import Cache # install Flask-Caching

from bson import json_util

#from werkzeug import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
#from flask_datepicker import datepicker

# Jinja
from jinja2 import Template
from jinja2.filters import FILTERS, environmentfilter

from com.mmc.common.utility import Utility
from com.mmc.audit.www_reports import Reports

#from wip import db, app
#app = Flask(__name__, instance_relative_config=False)
#app.config.from_object('config.Config')

"""
documentation:
https://hackersandslackers.com/flask-login-user-authentication/
"""

util = Utility()
report = Reports()

app = Flask(__name__)

myAppHomeDir = util.getEnvKeyVal("WWW_HOME") 

if not myAppHomeDir:
    raise ValueError("WWW_HOME environment is not set, aborting !!!")

myConfigDir = util.buildPath(myAppHomeDir,"config")
myLogDir = util.buildPath(myConfigDir,"log")
myConfigFile = util.buildPath(myConfigDir,"config.json")
myLoggingConfigFile = util.buildPath(myConfigDir,"logging.json")

if not myConfigDir:
    raise ValueError("WWW config environment is not set, aborting !!!")

if not util.isDirExists(myConfigDir):
    raise ValueError(f"Invalid WWW config dir {myConfigDir}, aborting !!!")

if not util.isFileExists(myConfigFile):
    raise ValueError(f"Invalid WWW config file {myConfigFile}, aborting !!!")

if not util.isFileExists(myLoggingConfigFile):
    raise ValueError(f"Invalid WWW logging config file {myLoggingConfigFile}, aborting !!! ")

myConfigData = util.readJsonFile(myConfigFile)
myLoggingConfigData = util.readJsonFile(myLoggingConfigFile)

if not myConfigData:
    raise ValueError(f"config file {myConfigFile} data is empty, aborting !!!")    

# overwriting log directory in logging 
if myConfigData["logDir"]:
    myLoggingFile = myLoggingConfigData["handlers"]["file_handler"]["filename"]
    myLoggingConfigData["handlers"]["file_handler"].update({"filename" : util.buildPath(myLogDir, util.getFileName(myLoggingFile))})

logging.config.dictConfig(myLoggingConfigData)
LOGGER = logging.getLogger()
LOGGER.info("logger is ready !!!")

myWWWPort = myConfigData["port"]
LOGGER.info(f"config data is used for WWW >>> {myConfigData}")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///P:\\app\\www\\wip\\dbaas\\db\\login.db'
app.config['SECRET_KEY'] = 'qwrwyeqg67re2q3wdhfaiydfasydfasdtif62r1rqwere1332wsQSXAx:jpHCOQW'
app.config['TESTING'] = False

# Flask-Caching related configs

#app.config["CACHE_TYPE"] = "SimpleCache"
#app.config["CACHE_DEFAULT_TIMEOUT"] = 300

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 # to disable cache
csrf = CSRFProtect()
csrf.init_app(app)
#cache = Cache(app)

"""
# Jinja custom filter
@environmentfilter
def numberFormat(environment, value):
    return format(int(value), ',d')

FILTERS["numberFormat"] = numberFormat
"""

""""
IMPORTANT
we need to store all session details in db so load_user can load the session details, work around is logout and logback in

Pending
    1. Python session SAMESITE=None not being set
https://wtforms.readthedocs.io/en/2.3.x/fields/
"""

"""
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)
"""

def page_not_found(e):
  return render_template('404.html'), 404

def page_not_found(e):
  return render_template('500.html'), 500

def server_error(error):
    #app.logger.error(f"Server error: {error}. route: {request.url}")
    return render_template("500.html")

app.register_error_handler(404, page_not_found)
app.register_error_handler(500, server_error)

bootstrap = Bootstrap(app)
loginManager = LoginManager()
loginManager.init_app(app)
datepicker(app)
db=SQLAlchemy(app)

#cache = Cache(app)
loginManager.login_view = 'login'

db.create_all()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    network_id = db.Column(db.String, unique=True)
    domain = db.Column(db.String)
    user_name = db.Column(db.String)
    password_hash = db.Column(db.String(50))
    authenticated = db.Column(db.Boolean, default = False)

    def __init__(self,network_id, domain, user_name, password_hash, authenticated):
        self.network_id = network_id
        self.domain = domain
        self.user_name = user_name
        self.password_hash = password_hash
        self.authenticated = authenticated

    @staticmethod
    def try_login(network_id, password):
        response = self.util.postRestApi("http://usdfw21as383v:8000/api/audit/processRequest", {"apiKey" : "eXokNzl5NEUzOWdXNCkp", "userId" : "DMZPROD01\\svc-dev-deploy-app", "method" : "authenticate", "args": {"networkId" : network_id, "password" : password}})
        print(f"response >>> {response}")
        return response

    def is_authenticated(self):
        return self.authenticated
 
    def is_active(self):
        return True
 
    def is_anonymous(self):
        return False
 
    def get_id(self):
        return self.network_id

@loginManager.user_loader
def load_user(network_id):
    print(f"loading user >>> {network_id}")
    if network_id is not None:
        return User.query.filter_by(network_id = network_id).first()
    else:
        return None

@loginManager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    #flash('You must be logged in to view that page.')
    return redirect(url_for('login'))

@app.before_request
def get_current_user():
    g.user = current_user

@app.route('/badrequest400')
def badRequest():
    abort(400)

"""
def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    return app
"""

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login/", methods=['GET','POST'])
def login():
    """
    Standard `login` form.
    https://flask-login.readthedocs.io/en/latest/
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = forms.LoginForm()
    results = {}
    #print(f"request >>> {request.get_data()}")
    error = None
    """
    if current_user.is_authenticated:
        return redirect(url_for('hosts'))
    """
    if form.validate_on_submit():
        """
        print(f"form.data >> {form.data}")
        print(f"request form >>> , {request.form}")
        print (f"networkId (form.data['networkId']) >>> {form.data['networkId']}")
        print (f"remember (form.data['remember']) >>> {form.data['remember']}")
        print(f"request.form.get id >>> {request.form.get('networkId')}")
        print(f"request.form.get remmeber >>> {request.form.get('remember')}")
        """
        #return redirect(url_for("success"))
        #flash(f"Network id {request.form['networkId']} logged in successfully !!!")
        myUserId = form.data["networkId"]
        myPassword = form.data["password"]        
        myRememberMe = form.data["remember"]
        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

        """
        login_user(myUserId)

        flask.flash('Logged in successfully.', 'success')
        next = flask.request.args.get('next')
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        if not is_safe_url(next):
            return flask.abort(400)

        return flask.redirect(next or flask.url_for('home'))
        """
        # GLB-MMC-MONGODBA-ServerAdmin-S-G --> access to group

        response = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : "authenticate", "args": {"userId" : myUserId, "password" : myPassword}})
        print(f"response >>> {response}")
        if response["status"] == "UnSuccess":
            flash("Invalid credentials !!!","alert alert-danger alert-dismissible fade show")
            # credential is not good, we need to display the message 'credential is not good'
            print(response, error)
            return redirect(url_for('login'))
        else:
            # returing user details from sqlite
            # retrieving logged in user detail 
            #response = util.postRestApi("http://usdfw21as383v:8000/api/audit/processRequest", {"apiKey" : "eXokNzl5NEUzOWdXNCkp", "userId" : "DMZPROD01\\svc-dev-deploy-app", "method" : "authenticate", "args": {"userId" : request.form["networkId"], "password" : request.form["password"]}})
            myDomain = myUserId.split('\\')[0]
            myNetworkId = myUserId.split('\\')[1]
            print("network id >>> {myNetworkId}")
            print("domain >>> {domain}")
            #print("request >>>",jsonify(request.form))
            user = User.query.filter_by(network_id=myNetworkId).first()
            print("user find result >> {user}")
            if not user:
                print("user details not found in db, adding")
                user = User(network_id = myNetworkId, domain = myDomain, user_name = myNetworkId, password_hash = generate_password_hash(myPassword), authenticated = True)
                db.session.add(user)
                db.session.commit()
                db.session.close()
                print(f"user added {myUserId}")
            else:
                print(f"user exists, proceeding")

            # retrieving user ldap details
            session.permanent = True
            myResponse = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : "getLdapUserdetails", "args": {"userSearchAttr" : "networkId", "userSearchAttrVal" : myNetworkId}})
            print(f"user '{myNetworkId}' ldap search results >>> {myResponse}")

            if myResponse["status"] != "Success":
                flash(f"{myResponse['message']}", "danger")
                return render_template(
                    "login_03.html",
                    form=form,
                    template="form-template"
                )

                #raise ValueError(f"An error {myResponse['message']} occurred while retrieving user ldap details !!!")
            
            myUserLdapData = myResponse["data"]["attributes"]
            del myResponse

            myUserDN = myUserLdapData["distinguishedName"]
            myUserName = myUserLdapData["displayName"]
            myUserOpco = myUserLdapData["company"]

            myUserAdGrp = [cn.split(",")[0].split("=")[1] for cn in myUserLdapData["memberOf"]]

            login_user(user, remember = myRememberMe)

            session['userId'] = myNetworkId
            session['domain'] = myDomain
            session["memberOf"] = myUserAdGrp
            session["opco"] = myUserOpco
            session["logonTime"] = util.lambdaGetCurrDateTime()
            session["authenticated"] = True
            session['logged_in'] = True
            session["userName"] = myUserName
            #session.permanent = True
            #app.permanent_session_lifetime = timedelta(minutes=20)

            print(f"Current session >> {session}")

            print(f"user {user} logged in")

            next = request.args.get('next')
            print(f"next >> {request.args.get('next')}, {dir(request.args)}")
            print(f"current_user {current_user}, network id {myNetworkId}")

            if next and not is_safe_url(next):
                return flask.abort(400)
            
            # we need to store ad group this user belongs to and identify the is this user an admin
            """
            session.userMemberOf =""
            session.isAdmin = ""
            session.role = ""
            """
            return redirect(url_for('home'))
    else:
        print(results, form.errors)
        return render_template(
            "login_03.html",
            form=form,
            template="form-template",
            results = results,
            error = error
        )

@app.route("/logout")
#@cache.cached(timeout=50)
@login_required
def logout():
    user = current_user
    print("current user >>>", user)
    print(f"session {session}")
    #["user_id"]
    user.authenticated = False
    #db.session.add(user)
    #db.session.commit()
    session.clear()
    logout_user()
    print(f"session {session}")
    return redirect("login")

@login_required
@app.route("/tenants/", methods=['GET','POST'])
#@cache.cached(timeout=50)
def tenants():
    # retrieving data via rest API
    form = forms.TenantInventoryViewForm()
    # dynamic form selector --> https://www.youtube.com/watch?v=I2dJuNwlIH0

    #myOpco = "MARSH"
    myOpco = myRegion = myDBTechnology = myEnv = myStatus = "ALL"
    myError = None
    print(request)
    if request.method == "POST":
        #if form.validate_on_submit():
        print(f"{request.form}")
        #return jsonify(request.form)
        myOpco = request.form["opco"]
        myRegion = request.form["region"]
        myDBTechnology = request.form["dbTechnology"]
        myEnv = request.form["env"]
        myStatus = form.status.data

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    #myMethod = "getAllHostDetails"
    myMethod = "getTenantsInventory"
    myArguments = {}
    
    #myDBTechnology = "mongo"
    myArguments.update({
        "opco" : myOpco,
        "region" : myRegion,
        "dbTechnology" : myDBTechnology,
        "env" : myEnv,
        "status" : myStatus,
        "output" : ["header","members.summary","databases"]
    })
       
    print(f"query args >>> {myArguments}")
    
    #myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    myTenantsData = myResult["data"]
    # formating data for (cpu. memory, swap)

    if myResult["status"] == "UnSuccess":
        flash(f"An error occurred while retrieving all database details >>> {myResult['message']}","danger")
        return render_template("tenants.html", title = "Database Inventory", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = [], data = [], form = form)

    if not myTenantsData:
        return render_template("tenants.html", title = "Database Inventory", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = [], data = [], form = form)

    # updating data
    for tenant in myTenantsData:
        myTenantDBs = tenant["databases"]["total"]
        myTenantDBSize = 0
        for db in tenant["databases"]["dbs"]:
            myTenantDBSize = myTenantDBSize  + db["sizeOnDisk"]
        myTenantDBSize = "{:,}".format(round(myTenantDBSize/(1024*1024),2))
        #print(tenant["members"])
        myMemberData = [member["tenantId"] for member in tenant["members"]]
        if myMemberData:
            myTenantMembers = len(myMemberData)
        else:
            myTenantMembers = 1

        tenant.update({
            "totMembers" : myTenantMembers,
            "totalDBs" : myTenantDBs,
            "dbSize" : myTenantDBSize,
            "dbTechnology" : tenant["dbTechnology"].upper() 
        })
        tenant.pop("databases")
        #tenant.pop("users")
        #tenant.pop("roles")
        tenant.pop("members")

    # we need to update compliance data for each databases

    headings = ("DB Cluster","Given Cluster","Opco","Region","DB Technology","Status","Env","Docker","Compliance","Version","Members","Total DBs","DB Size(MB)")
    rawHeadings = ["dbCluster","_id","opco","region","dbTechnology","status","env","docker","compliance","version","totMembers","totalDBs","dbSize"]
    tenantData = convertDict2TupleForHtml(rawHeadings, myTenantsData,["env"])

    #print(f"rendering tenant dataa >>> {tenantData}")
    return render_template("tenants.html", title = "Database Inventory", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = headings, data = tenantData, form = form)

@login_required
@app.route("/view_tenant/<tenantName>/", methods = ['GET','POST'])
#@cache.cached(timeout=50)
def view_tenant(tenantName):
    #return jsonify('',render_template('host.html', form = from))
    print(f"route /tenant/{tenantName}")
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    myMethod = "getATenantDetails"
    myArguments = {"tenantName" : tenantName.strip()}
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    #print(myResult)
    if myResult["status"] == "UnSuccess" or (not myResult["data"]):
        #return "<img src=\"{{ url_for('static', filename='no-data.png')}}\" class=\"img-fluid\">"
        flash(myResult['message'])
        return render_template('view_tenant.html', title = "Database Details", user = "".join([session["userName"], " (", session["userId"], ")"]), tenant = myTenantData)

    myTenantData = myResult["data"]
    del myResult
    # formating data for members
    memberHeadings = ["Member Id","Status","Host","Port","Version","BootTime"]
    rawHeadings = ["tenantId","status","hostName","port","version","bootTime"]
    memberData = convertDict2TupleForHtml(rawHeadings, myTenantData["members"],[])

    # formating data for database
    myTenentDBData = []
    for db in myTenantData["databases"]["dbStats"]:
        _db = [db_ for db_ in myTenantData["databases"]["dbs"] if db_["name"] == db["db"]]
        myTenentDBData.append({
            "name" : _db[0]["name"],
            "appId" : _db[0]["appId"],
            "appName" : _db[0]["appName"],
            "appDL" : _db[0]["appDL"],
            "sizeMB" : "{:,}".format(round(_db[0]["sizeMB"],2)),
            "colls" : "{:,}".format(db["collections"]),
            "indexes" : "{:,}".format(db["indexes"])
        })

    dbHeadings = ["Name","AppId","AppName","App DL","Size(MB)","Collections","Indexes"]
    rawHeadings = ["name","appId","appName","appDL","sizeMB","colls","indexes"]
    dbData = convertDict2TupleForHtml(rawHeadings, myTenentDBData,[])

    # formating data for roles
    myTenantRoleData = []
    for role in myTenantData["roles"]:
        myGrantedRoleDB = []
        myGrantedRole = []
        for grantedRole in role["roles"]:
            myGrantedRoleDB.append(grantedRole["db"])
            myGrantedRole.append(grantedRole["role"])

        myGrantee = [user["name"] for user in role["users"]]

        myTenantRoleData.append({
            "role" : role["role"],
            "db" : role["db"],
            "grantedOnDB" : ",".join(myGrantedRoleDB),
            "grnatedRoles" : ",".join(myGrantedRole),
            "grantee" : ",".join(myGrantee)
        })
    roleHeadings = ["Role","DB Owner","Granted Role(s)","Database","Grantee"]
    rawHeadings = ["role","db","grantedRoles","grantedOnDB","grantee"]
    roleData = convertDict2TupleForHtml(rawHeadings, myTenantRoleData,[])

    # formating data for users
    myTenantUserData = []
    for user in myTenantData["users"]:
        myUserRoles = []
        for role in user["roles"]:
            myUserRoles.append(f"{role['role']} on {role['db']}")
        myTenantUserData.append({
            "_id" : user["_id"],
            "user" : user["user"],
            "db" : user["db"],
            "dbRoles" : ",".join(myUserRoles)
        })

    userHeadings = ["User ID","User","Database","Roles"]
    rawHeadings = ["_id","user","db","dbRoles"]
    userData = convertDict2TupleForHtml(rawHeadings, myTenantUserData,[])

    # formating data for rs config
    if myTenantData["instanceType"] == "mongo.rs":
        clusterData = {}
        myRSSettings = {}
        if "rsConfig" in myTenantData:
            myRSSettings.update({
                "clusterName" : myTenantData["rsConfig"]["_id"],
                "version" : myTenantData["rsConfig"]["_id"] if "writeConcernMajorityJournalDefault" in myTenantData["rsConfig"] else "",
                "totalMembers" : len(myTenantData["rsConfig"]["members"]) if "members" in myTenantData["rsConfig"] else "",
                "writeConcernMajorityJournalDefault" : myTenantData["rsConfig"]["writeConcernMajorityJournalDefault"] if "writeConcernMajorityJournalDefault" in myTenantData["rsConfig"] else "",
                "chainingAllowed" : myTenantData["rsConfig"]["settings"]["chainingAllowed"] if "chainingAllowed" in myTenantData["rsConfig"]["settings"] else "",
                "heartbeatIntervalMillis" : myTenantData["rsConfig"]["settings"]["heartbeatIntervalMillis"] if "heartbeatIntervalMillis" in myTenantData["rsConfig"]["settings"] else "",
                "heartbeatTimeoutSecs" : myTenantData["rsConfig"]["settings"]["heartbeatTimeoutSecs"] if "heartbeatTimeoutSecs" in myTenantData["rsConfig"]["settings"] else "",
                "electionTimeoutMillis" : myTenantData["rsConfig"]["settings"]["electionTimeoutMillis"] if "electionTimeoutMillis" in myTenantData["rsConfig"]["settings"] else "",
                "catchUpTimeoutMillis" : myTenantData["rsConfig"]["settings"]["catchUpTimeoutMillis"] if "catchUpTimeoutMillis" in myTenantData["rsConfig"]["settings"] else "",
                "catchUpTakeoverDelayMillis" : myTenantData["rsConfig"]["settings"]["catchUpTakeoverDelayMillis"] if "catchUpTakeoverDelayMillis" in myTenantData["rsConfig"]["settings"] else "",
                "catchUpTakeoverDelayMillis" : myTenantData["rsConfig"]["settings"]["catchUpTakeoverDelayMillis"] if "catchUpTakeoverDelayMillis" in myTenantData["rsConfig"]["settings"] else ""
            })

            #myRSMemberData = myTenantData["rsConfig"]["members"]

            rsMemberHeadings = ["ID","Host","Port","Health","Role","Arbiter","Build Index", "Hidden", "Priority", "Slave Delay","Votes"]
            rawHeadings = ["_id","host","port","health","role","arbiterOnly","buildIndexes","hidden","priority","slaveDelay","votes"]
            for member in myTenantData["rsConfig"]["members"]:
                # we need cluster detail state/health for each member
                myMemberClusetrDetails = [_member for _member in myTenantData["rsDetails"]["members"] if member["_id"] == _member["_id"]]

                if myMemberClusetrDetails:
                    myMemberClusetrDetails = myMemberClusetrDetails[0]

                member.update({
                    "port" : member["host"].split(":")[1],
                    "host" : member["host"].split(":")[0],
                    "health" : "UP" if (myMemberClusetrDetails["health"] if "health" in myMemberClusetrDetails else "N/A") == 1 else "DOWN",
                    "role" : myMemberClusetrDetails["stateStr"] if "stateStr" in myMemberClusetrDetails else "N/A"
                })
            rsMemberData = convertDict2TupleForHtml(rawHeadings, myTenantData["rsConfig"]["members"],[])
            clusterData = {"clusterSettings": myRSSettings, "clusterMemberData" : rsMemberData,"clusterMemberHeading" : rsMemberHeadings}
        else:
            clusterData = {}            
    else:
        clusterData = {}

    myTenantData.pop("members")
    myTenantData.pop("databases")
    myTenantData.pop("roles")
    myTenantData.pop("users")
    myTenantData.pop("rsConfig")
    myTenantData.pop("rsDetails")

    # retrieving history for this tenant, we need last 100 records for history
    myMethod = "getTenantChangeHist"
    myArguments = {"tenantName" : tenantName.strip()}
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    print(f"testing - history result >>> {myResult}")
    if myResult["status"] == "UnSuccess" or (not myResult["data"]):
        raise ValueError(myResult["message"])

    histHeadings = ["TS","Who","Comp","Comments"]
    rawHeadings = ["ts","userId","comp","comments"]
    for hist in myResult["data"]:
        hist.update({"ts" : util.convertDate2Str(util.convStr2DateViaParser(hist["ts"]),"%Y-%m-%d %H:%M:%S") })

    histData = convertDict2TupleForHtml(rawHeadings, myResult["data"],[])

    # retrieving tenant's latest compliance data
    myMethod = "getLatestTenantCompliance"
    myArguments = {"opco" : "ALL","dbTechnology" : "ALL", "compStatus" : "ALL","tenantName" : tenantName.strip()}
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    #print(f"testing - compliance data result >> {myResult}")

    myTenantResult = myResult["data"][0]
    myTenantCompRawData = []
    for comp in myTenantResult["compliances"]:
        # checking if we this comp is extended to multiple host of this database(rs member in Mongo)
        if "members" in comp:
            for member in comp["members"]:
                myTenantCompRawData.append({
                    "runDate" : myTenantResult["compRunDate"],
                    "comp" : comp["comp"],
                    "desc" : " ".join([item.capitalize() for item in comp["comp"].split(".")]),
                    "tenant" : member["tenantId"],
                    "relevance" : "MEMBER",
                    "status" : member["status"],
                    "result" : member["result"],
                })
        else:
            myTenantCompRawData.append({
                "runDate" : myTenantResult["compRunDate"],
                "comp" : comp["comp"],
                "desc" : " ".join([item.capitalize() for item in comp["comp"].split(".")]),
                "tenant" : myTenantResult["tenantName"],
                "relevance" : "DATABASE",
                "status" : comp["status"],
                "result" : comp["result"],
            })
    myCompHeadings = ["DB Id","Relevance", "Compliance","Description","Status","Result"]
    rawHeadings = ["tenant","relevance","comp","desc","status","result"]
    myTenantLatestCompData = convertDict2TupleForHtml(rawHeadings, myTenantCompRawData,[])

    del myTenantResult, myTenantCompRawData

    myTenantData.update({
        "members" : {"headings" : memberHeadings, "data" : memberData},
        "databases" : {"headings" : dbHeadings, "data" : dbData},
        "roles" : {"headings" : roleHeadings, "data" : roleData},
        "users" : {"headings" : userHeadings, "data" : userData},
        "cluster" : clusterData,
        "history" : {"headings" : histHeadings, "data" : histData},
        "compliance" : {"headings" : myCompHeadings, "data" : myTenantLatestCompData}
    })

    #print(f"tenant data {myTenantData}")
    return render_template('view_tenant.html', title = "Database Details", user = "".join([session["userName"], " (", session["userId"], ")"]), tenant = myTenantData)

@login_required
@app.route("/edit_tenant/<tenantName>/", methods = ['GET','POST'])
#@cache.cached(timeout=50)
def edit_tenant(tenantName):

    # Edit tenants in hosts.inventory
    #return jsonify('',render_template('host.html', form = from))
    print(f"route /edit_tenant/{tenantName}")
    form = forms.EditTenantForm()

    myTenantName = tenantName.strip()

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    if request.method == "GET":
        myMethod = "getATenantDetails"
        myArguments = {"tenantName" : myTenantName}
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        form.tenantName.data = myTenantName

        print(myResult)
        if myResult["status"] == "UnSuccess" or (not myResult["data"]):
            #return "<img src=\"{{ url_for('static', filename='no-data.png')}}\" class=\"img-fluid\">"
            flash(myResult["message"])
            return render_template('edit_tenant.html', title = "Database Details", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

        myTenantData = myResult["data"]
        myTenantData.pop("members")
        myTenantData.pop("databases")
        myTenantData.pop("roles")
        myTenantData.pop("users")
        myTenantData.pop("rsConfig")
        myTenantData.pop("rsDetails")

        print(f"tenant data {myTenantData}")
        form.env.data = myTenantData["env"].upper()
        form.haMethod.data = myTenantData["ha"]["method"] if "ha" in myTenantData and "method" in myTenantData["ha"] else ""
        form.backupMethod.data = myTenantData["backup"]["method"] if "backup" in myTenantData and "method" in myTenantData["backup"] else ""
        form.backupServers.data = myTenantData["backup"]["servers"] if "backup" in myTenantData and "servers" in myTenantData["backup"] else ""
        
        if myTenantData["env"].upper() == "PROD":
            form.drMethod.data = myTenantData["dr"]["method"] if "dr" in myTenantData and "method" in myTenantData["dr"] else ""
            form.drServers.data = myTenantData["dr"]["servers"] if "dr" in myTenantData and "servers" in myTenantData["dr"] else ""

        form.licensingNeeded.data = myTenantData["licenseNeeded"] if "licensingNeeded" in myTenantData else ""
        form.usage.data = myTenantData["usage"] if "usage" in myTenantData else "shared"

    else:
        myArguments = {}
        myArguments.update({
            "tenantName" : myTenantName,
            "haMethod" : form.haMethod.data,
            "licensingNeeded" : form.licensingNeeded.data
        })

        if form.env.data.upper() == "PROD":
            myArguments.update({
                "drMethod" : form.drMethod.data,
                "drServers" : form.drServers.data
            })

        myArguments.update({
            "backupMethod": form.backupMethod.data,
            "backupServers" : form.backupServers.data,
            "uri" : form.uri.data,
            "usage" : form.usage.data
        })

        if form.usage.data.upper() == "DEDICATED":
            myArguments.update({"dedicatedFor" : form.dedicatedFor.data}) 

        myArguments.update({"comments" : form.comments.data})

        myMethod = "updateTenant"
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while updating tenant {myTenantName} >>> {myResult['message']}", "danger")
        else:
            flash(f"Tenant {myTenantName} attributes updated successfully !!", "success")

        return redirect(url_for('tenants'))

    return render_template('edit_tenant.html', title = f"Edit Database Details - {myTenantName}", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

@app.route("/no_data_found/", methods = ['GET'])
def no_data_found():
    return render_template('no_data_found.html')

@login_required
@app.route("/view_tenant_member/<tenantMemberId>/", methods = ['GET','POST'])
#@cache.cached(timeout=50)
def view_tenant_member(tenantMemberId):
    #return jsonify('',render_template('tenant_member.html', form = from))
    print(f"route /view_tenant_member/{tenantMemberId}")
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    myMethod = "getATenantMemberDetail"
    myArguments = {"tenantMemberId" : tenantMemberId.strip()}
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    #print(myResult)
    if myResult["status"] == "UnSuccess" or (not myResult["data"]):
        return redirect('no_data_found')

    myTenantMemberData = myResult["data"]

    # formating data for config
    configHeadings = ["Parameter","Value"]
    rawHeadings = ["param","value"]
    myConfFlattenDict = util.flattenDict(myTenantMemberData["config"],parent_key="", sep=".")
    myConfigData = []
    for config in myConfFlattenDict:
        myConfigData.append({"param" : config, "value" : myConfFlattenDict[config]})

    #print("formatted conf data ", myConfigData)

    configData = convertDict2TupleForHtml(rawHeadings, myConfigData,[])
    
    # formating data for build
    buildHeadings = ["Parameter","Value"]
    rawHeadings = ["param","value"]
    myBuildFlattenDict = util.flattenDict(myTenantMemberData["buildInfo"],parent_key="", sep=".")
    myBuildData = []
    for config in myBuildFlattenDict:
        myBuildData.append({"param" : config, "value" : myBuildFlattenDict[config]})

    buildData = convertDict2TupleForHtml(rawHeadings, myBuildData,[])

    # formating data for server
    serverHeadings = ["Parameter","Value"]
    rawHeadings = ["param","value"]
    myServerFlattenDict = util.flattenDict(myTenantMemberData["serverStatus"],parent_key="", sep=".")
    myServerData = []
    for config in myServerFlattenDict:
        myServerData.append({"param" : config, "value" : myServerFlattenDict[config]})

    serverData = convertDict2TupleForHtml(rawHeadings, myServerData,[])

    myTenantMemberData.pop("config")
    myTenantMemberData.pop("buildInfo")
    myTenantMemberData.pop("serverStatus")

    myTenantMemberData.update({
        "dbCluster" : "<need to populate>",
        "configHeadings" : configHeadings,
        "configData" : configData,
        "buildHeadings" : buildHeadings,
        "buildData" : buildData,
        "serverHeadings" : serverHeadings,
        "serverData" : serverData        
    })
    #print(f"tenant Member data {myTenantMemberData}")
    return render_template('view_tenant_member.html', title = "Database Member Details", user = "".join([session["userName"], " (", session["userId"], ")"]), tenantMember = myTenantMemberData)

""" 2 diff button on same form and how to check which button was clicked when Post event happened
def contact():
    if "open" in request.form:
        pass
    elif "close" in request.form:
        pass
    return render_template('contact.html')
"""

@login_required
@app.route("/new_host/", methods=['GET','POST'])
def new_host():
    # retrieving data via rest API
    form = forms.NewHostForm()
    results = {}
    error = None
    # dynamic form selector --> https://www.youtube.com/watch?v=I2dJuNwlIH0
    print(f"session >>> {session}") 
    #if form.validate_on_submit(): print(form.errors)
    if request.method == "GET":
        return render_template("new_host.html", title = "Register New Host", form=form, user = "".join([session["userName"], " (", session["userId"], ")"]) )
    else:
        myOpco = form.opco.data
        myRegion = form.opco.data
        myDCLocation = form.dcLocation.data
        myDomain = form.tier.data
        myEnv = form.env.data
        myDBTechnology = form.dbTechnology.data
        myScanEnabled = form.scanEnabled.data
        myLicenseNeeded = form.licenseNeeded.data
        myTag = form.tag.data
        myComments = form.comments.data
        myHostName = form.hostName.data
        myCPU = form.cpu.data
        myMemoryGB = form.memoryGB.data
        mySwapGB = form.swapGB.data
        myOS = form.os.data

        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

        myMethod = "addHost2Inventory"
        myDataArgs = {
            "opco" : myOpco,
            "region" : myRegion,
            "dcLocation" : myDCLocation,
            "domain" : myDomain,
            "dbTechnology" : myDBTechnology,
            "env" : myEnv,
            "tag" : myTag,
            "hostName" : myHostName,
            "cpu" : myCPU,
            "memoryGB" : myMemoryGB,
            "swapGB" : mySwapGB,             
            "os" : myOS,             
            "scanEnabled" : myScanEnabled,
            "comments" : myComments,
            "userId" : f"{session['userId']}"
        }
        print(f"data args >>> {myDataArgs}")
        myResult = util.postRestApi(myRestApiURL, \
            {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myDataArgs})
        
        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while registering new host {myHostName}>>> {myResult['message']}","danger")
        else:
            flash(f"Host {myHostName} is registerd successfully !!!","success")

        return redirect(url_for("view_host", title = f"Host Details {myHostName}", host = myHostName))
        #print(f"new_host form.data >> {form.data}")

@login_required
@app.route("/hosts/", methods=['GET','POST'])
#@cache.cached(timeout=50)
def hosts():
    print(f"session details >>> {session}")
    print(f"form request filter >>> {request.form.get('filter')}")
    print(f"form request download >>> {request.form.get('download')}")
    # retrieving data via rest API
    form = forms.HostInventoryViewForm()
    # dynamic form selector --> https://www.youtube.com/watch?v=I2dJuNwlIH0

    myOpco = form.opco.default
    myRegion = form.region.default
    myDBTechnology = form.dbTechnology.default
    myEnv = form.env.default
    myTag = myDCLocation = "ALL"
    myError = None
    print(request)
    if request.method == "POST":
        #if form.validate_on_submit():
        print(f"{request.form}")
        #return jsonify(request.form)
        myOpco = request.form["opco"]
        myRegion = request.form["region"]
        myDBTechnology = request.form["dbTechnology"]
        myEnv = request.form["env"]

        # checking if download button was clicked
        if request.form.get("download"):
            myResult = createHostReport(myOpco, myRegion, myDBTechnology, myEnv)

            if myResult["status"] != "Success":
                flash(f"An error occurred while generating hosts report >>> {myResult['message']} !!!","danger")

            if not myResult["data"]:
                flash("No data available to generate report !!!","warning")

            print(f'testing - result : {myResult}')
            if myResult["data"]:
                return send_from_directory(util.getFileDirName(myResult["data"]), filename=util.getFileName(myResult["data"]), as_attachment=True)

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    #myMethod = "getAllHostDetails"
    myMethod = "getHostInventory"
    myArguments = {}
    
    #myDBTechnology = "mongo"
    myArguments.update({
        "opco" : myOpco,
        "region" : myRegion,
        "dbTechnology" : myDBTechnology,
        "tag" : myTag,
        "env" : myEnv,
        "dcLocation" : myDCLocation
    })
       
    print(f"query args >>> {myArguments}")
    
    #myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    if myResult["status"] == "UnSuccess":
        flash(f"An error occurred while retrieving host details >>> {myResult['message']}","danger")
        return render_template("hosts.html", title = "Hosts Inventory", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = [], data = [], form = form)

    myHostsData = myResult["data"]
    # formating data for (cpu. memory, swap)

    for host in myHostsData:
        host.update({
            "dbTechnology" : ",".join(map(str, set( [tenant["dbTechnology"].upper() for tenant in host["tenants"]] ))),
            #"dbVersion" : ",".join(map(str, set( [tenant["tenantVersion"] for tenant in host["tenants"]] ))),
            "dbVersion" : ",".join(map(str, set( [tenant["version"] for tenant in host["tenants"] if "version" in tenant] ))),
            "dbPort" : ",".join(map(str, set( [tenant["port"] for tenant in host["tenants"]  if "port" in tenant] ))),
            "scanEnabled" : host["scanEnabled"].upper()
        })
        if "osConfig" in host and host["osConfig"]:
            host.update({
                "os" : host["osConfig"]["os"],
                "version" : host["osConfig"]["version"] if "version" in host["osConfig"] else "n/a",
                "cpu" : host["osConfig"]["cpu"]["count"] if "cpu" in host["osConfig"] and "count" in host["osConfig"]["cpu"] else "n/a",
                "memoryGB" : round(host["osConfig"]["memory"]["total"] / (1024*1024*1024)) if "memory" in host["osConfig"] else "n/a",
                "swapMB" : round(host["osConfig"]["swap"]["total"] / (1024*1024)) if "swap" in host["osConfig"] else "n/a",
                "bootTime" : util.convStr2DateViaParser(host["osConfig"]["bootTime"]) if "bootTime" in host["osConfig"] and host["osConfig"]["bootTime"] else ""
            })
        else:
            host.update({
                "cpu" : -1,
                "memoryGB" : -1,
                "swapMB" : -1
            })

    headings = ("Host","Opco", "DataCenter", "Region","Env","Domain","Tag","Status","IPAddress","OS", "Version","CPU","Memory (GB)","Swap (MB)","DB Technology","Boot Time","DB Version","DB Port","Scan Enabled")
    rawHeadings = ["hostName","opco","dcLocation","region","env","domain","tag","status","ipAddress","os","version", "cpu","memoryGB","swapMB","dbTechnology","bootTime","dbVersion","dbPort","scanEnabled"]
    data = convertDict2TupleForHtml(rawHeadings, myHostsData,["env"])
    #print(headings)
    #print(data)
    return render_template("hosts.html", title = "Hosts Inventory", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = headings, data = data, form = form)

@login_required
@app.route("/host/<host>/", methods = ['GET','POST'])
#@cache.cached(timeout=50)
def view_host(host):
    #return jsonify('',render_template('view_host.html', form = from))
    print(f"route /host/{host}")
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    myMethod = "getAHostDetails"
    myArguments = {"hostName" : host.strip()}
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    if myResult["status"] == "UnSuccess":
        raise ValueError(myResult["message"])

    #print(myResult)

    myHostDetails = myResult["data"]
    if not myHostDetails:
        return "#" # returning # to stay on same page and do not route to host since we dont have host information available

    myHostDetails.update({
        "dbTechnology" : ",".join(myHostDetails["dbTechnology"])
        })
    # formating host data
    #print(f"testing - host details >>> {myHostDetails}")
    if "osConfig" in myHostDetails:
        myHostDetails.update({
            "ipAddress" : myHostDetails["osConfig"]["ipAddress"],
            "bootTime" : util.convertDate2Str(util.convStr2DateViaParser(myHostDetails["osConfig"]["bootTime"]),'%B %d, %Y %H:%M:%S') if "bootTime" in myHostDetails["osConfig"] else "n/a",
            "os" : "".join([myHostDetails["osConfig"]["os"], " - ", (myHostDetails["osConfig"]["osDistribution"] if "osDistribution" in myHostDetails["osConfig"] else "")]),
            "osVersion" : myHostDetails["osConfig"]["version"] if "version" in myHostDetails["osConfig"] else "n/a",
            "cpu" : myHostDetails["osConfig"]["cpu"]["count"] if "cpu" in myHostDetails["osConfig"] and "count" in myHostDetails["osConfig"]["cpu"] else "n/a",
            "physMemory" : "".join([str(round(myHostDetails["osConfig"]["memory"]["total"]/(1024*1024*1024))), " GB"]) if "memory" in myHostDetails["osConfig"] and "total" in myHostDetails["osConfig"]["memory"] else "n/a",
            "swapMemory" : "".join([str(round(myHostDetails["osConfig"]["swap"]["total"]/(1024*1024*1024))), " GB"]) if "swap" in myHostDetails["osConfig"] and "total" in myHostDetails["osConfig"]["swap"] else "n/a"
            })
        
        if "fs" in myHostDetails["osConfig"]:
            # building FS data
            fsHeadings = ["FS","Type","Total","Used","Free","Free(%)"]
            rawHeadings = ["mountPoint","fsType","total","used","free","freePerc"]
            myFSRawData = [{
                "mountPoint" : fs["mountPoint"], 
                "fsType" : fs["fsType"], 
                "total" : util.convBytes2HumanReadable(fs["total"]), 
                "used" : util.convBytes2HumanReadable(fs["used"]),
                "free" : util.convBytes2HumanReadable(fs["total"] - fs["used"]),
                "freePerc" : round(((fs["total"] - fs["used"]) / fs["total"]),2) * (100)
                } for fs in myHostDetails["osConfig"]["fs"]
            ]
            fsData = convertDict2TupleForHtml(rawHeadings, myFSRawData,[])
            myHostDetails.update({
                "fsData" : {
                    "fsHeadings" : fsHeadings, 
                    "fsData" : fsData
                }
            })

        if "nicDetails" in myHostDetails["osConfig"]:
            # building nic data
            myNicDetails = []
            nicHeadings = ["Interface","Address","addressType","Broadcast","NetMask","Duplex","MTU","Speed","Up"]
            rawHeadings = ["intf","address","addressType","broadcast","netMask","duplex","mtu","speed","up"]

            for nic in myHostDetails["osConfig"]["nicDetails"]:
                #print("nic >>> ", nic)
                for addr in nic["addresses"]:
                    #print("address >>> ",addr)
                    myNicDetails.append({
                        "intf" : nic["intf"],
                        "address" : addr["address"],
                        "addressType" : addr["addressType"],
                        "broadcast" : addr["broadcast"] if "broadcast" in addr else "-----",
                        "netMask" : addr["netmask"] if "netmask" in addr else "-----",
                        "duplex" : addr["stats"]["duplex"],
                        "mtu" : addr["stats"]["mtu"],
                        "speed" : addr["stats"]["speed"],
                        "up" : addr["stats"]["up"].upper()
                    })
            myNicData = convertDict2TupleForHtml(rawHeadings, myNicDetails,[])

            myHostDetails.update({
                "nicDetails" : {
                    "nicHeadings" : nicHeadings, 
                    "nicData" : myNicData
                }
            })

        myHostDetails.pop("osConfig")

    # building history data
    myHistoryData = []
    histHeadings = ["TS","Who","Component","What"]
    rawHeadings = ["ts","userId","comp","what"]

    # retrieving host history
    myMethod = "getHostChangeHist"
    myArguments = {"hostName" : host.strip()}
    myHistDBResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    if myHistDBResult["status"] == "UnSuccess":
        raise ValueError(myHistDBResult["message"])

    for hist in myHistDBResult["data"]:
        #print("history >>> ", hist)
        myHistoryData.append({
            "ts" : util.convStr2DateViaParser(hist["ts"]) if not isinstance(hist["ts"], str) else hist["ts"],
            "userId" : hist["userId"],
            "comp" : "initial" if not( "comp" in hist and hist["comp"]) else hist["comp"],
            "comments" : hist["comments"],
            "what" : hist["what"] if "what" in hist else hist["comments"]
        })

    myHistData = convertDict2TupleForHtml(rawHeadings, myHistoryData,[])

    myHostDetails.update({
        "history" : {
            "histHeadings" : histHeadings, 
            "histData" : myHistData
        }
    })

    if "tenants" in myHostDetails:
        dbHeadings = ["DBTechnology","Cluster","GivenCluster","Port","Version","Usage","BackupMethod","BackupServer",]
        rawHeadings = ["dbTechnology","dbCluster","givenCluster","port","version","usage","backupMethod","backupServer"]
        myDBData = [
            {"dbTechnology" : db["dbTechnology"].upper(),
            "dbCluster" : db["dbCluster"],
            "givenCluster" : db["givenCluster"],            
            "port" : db["port"],
            "version" : db["version"] if "version" in db else "N/A"
            #"usage": db["usage"].upper(),
            #"backupMethod" : db["backup"]["method"] if "backup" in db and "method" in db["backup"] else "", 
            #"backupServer" : db["backup"]["backupServer"] if "backup" in db and "backupServer" in db["backup"] else "",
            #"haMethod" : db["ha"]["method"] if "ha" in db and "method" in db["ha"] else "n/a", 
            #"drMethod" : db["dr"]["method"] if "dr" in db and "method" in db["dr"] else "n/a", 
            #"uri" : db["uri"]
            } 
                for db in myHostDetails["tenants"]
        ]
        
        # populating HA/DR/Backup/uri method from tenant
        myMethod = "getATenantInfo"
        for db in myDBData:
            # retrieving tenants data
            myArguments = {"tenantName" : db["givenCluster"],"output" : ["header","ha","dr","backup"]}
            myTenantResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

            if myTenantResult["status"] == "UnSuccess":
                raise ValueError(myTenantResult["message"])

            if not myTenantResult["data"]:
                # this tenant data does not exists in tenants coll, nothing to update skipping this tenant
                continue

            db.update({
                "haMethod" : myTenantResult["data"]["ha"]["method"] if "ha" in myTenantResult["data"] and "method" in myTenantResult["data"]["ha"] else "",
                "drMethod" : myTenantResult["data"]["dr"]["method"] if "dr" in myTenantResult["data"] and "method" in myTenantResult["data"]["dr"] else "",
                "backupMethod" : myTenantResult["data"]["backup"]["method"] if "backup" in myTenantResult["data"] and "method" in myTenantResult["data"]["backup"] else "",
                "backupServer" : myTenantResult["data"]["backup"]["server"] if "backup" in myTenantResult["data"] and "server" in myTenantResult["data"]["backup"] else "",
                "usage" : myTenantResult["data"]["usage"].upper() if "usage" in myTenantResult["data"] else "n/a",
                "uri" : myTenantResult["data"]["uri"] if "uri" in myTenantResult["data"] else "n/a"
            })

        #print(f"(for testing only) db data >> {myDBData}, tenant >> {myTenantData}")
        dbData = convertDict2TupleForHtml(rawHeadings, myDBData,[])

        myHostDetails.update({
            "dbData" : {
                "dbHeadings" : dbHeadings, 
                "dbs" : dbData
            }
        })

    #print(f"host details >> {myHostDetails}")
    return render_template('view_host.html', title = "Host Details", user = "".join([session["userName"], " (", session["userId"], ")"]), host = myHostDetails)

@login_required
@app.route("/edit_host/<hostName>/", methods = ['GET','POST'])
#@cache.cached(timeout=50)
def edit_host(hostName):
    #return jsonify('',render_template('view_host.html', form = from))
    print(f"route /edit_host/{hostName}")
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    form = forms.EditHostForm()

    myHostName = hostName.strip() # this is need in post we get additionaal space in hostname

    if request.method == "GET":
        print("request is GET")
        myMethod = "getAHostDetails"
        myArguments = {"hostName" : hostName.strip()}
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        print(myResult)

        form.hostName.data = myHostName

        myHostDetails = myResult["data"]
        if not myHostDetails:
            flash("Missing host details","warning")
            #return "#" # returning # to stay on same page and do not route to host since we dont have host information available
            return render_template('edit_host.html', title = "".join(["Edit Host - ",myHostName]), user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

        myHostDetails.update({
            "dbTechnology" : ",".join(myHostDetails["dbTechnology"])
            })
        
        # formating host data
        if "osConfig" in myHostDetails:
            myHostDetails.update({
                "ipAddress" : myHostDetails["osConfig"]["ipAddress"]
            })

            myHostDetails.pop("osConfig",None)
            myHostDetails.pop("history",None)

        print("host namne attr >> ",dir(form.hostName))
        
        #form.hostName.data = myHostName
        form.opco.default = myHostDetails["opco"]
        form.region.default = myHostDetails["region"]
        form.domain.default = myHostDetails["domain"]
        form.tag.data = myHostDetails["tag"]
        form.status.data = myHostDetails["status"]
        form.scanEnabled.default = myHostDetails["scanEnabled"]
        #form.licensingNeeded.default = myHostDetails["licensingNeeded"]

        print(f"host details >> {myHostDetails}")
    else:
        print("request is POST", request.form, request.args)
        #print(f"request.args.get >>> {request.args.get('employeeId')}")

        # validating arguments
        if not form.comments.data:
            flash("Missing mandatory value for comments !!", "danger")
            return render_template('edit_host.html', title = "".join(["Edit Host - ",myHostName]), user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

        myMethod = "updateHostInventory"
        myArguments = {
            "hostName" : myHostName,
            "opco" : form.opco.data,
            "region" : form.region.data,
            "domain" : form.domain.data,
            "tag" : form.tag.data,
            "scanEnabled" : form.scanEnabled.data,
            "comments" : form.comments.data,
            "userId" : session["userId"]
        }
        print("arguments ", myArguments)
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        if myResult["status"] == "UnSuccess":
            flash(f"Can not save host '{myHostName}' changes, Pls refer to log file for more details >>> {myResult['message']} !!!", "danger" )
        else:
            flash(f"Changes to host '{myHostName}'was successful !!!", "success")

        return redirect(url_for("hosts"))

    return render_template('edit_host.html', title = "".join(["Edit Host - ",myHostName]), user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

@csrf.exempt
@login_required
@app.route("/processAjaxReq", methods = ['POST'])
#@cache.cached(timeout=50)
def processAjaxReq():
    #return request
    #myRequestData = request
    #print(dir(request))
    print(request.data)
    print(request.form)
    print(request.get_json)
    myAjaxRequest = request.json
    print(myAjaxRequest)

    # Rest API variables
    
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    
    print(f"ajax request for endpoint >>> {myAjaxRequest['endPoint']}, args >>> {myAjaxRequest['args']}")
    if myAjaxRequest["endPoint"] == "viewHost":
        myHostName = myAjaxRequest["args"]["hostName"]
        print(f'hostName : {myHostName}')
        #return jsonify(redirect(url_for("viewHost", host = myHostName))) # this will send the content back to ajax
        #return make_response(jsonify(redirect(url_for("viewHost", host = myHostName)))) # this will send the content back to ajax
        return jsonify({'redirect': url_for("view_host", host=myHostName)})
        """
        #return url_for("viewHost", host = myHostName)
        data = url_for("viewHost", host = myHostName)
        make_response(jsonify(data), 200)
        """
    if myAjaxRequest["endPoint"] == "editHost":
        myHostName = myAjaxRequest["args"]["hostName"]
        print(f'hostName : {myHostName}')
        #return jsonify(redirect(url_for("viewHost", host = myHostName))) # this will send the content back to ajax
        #return make_response(jsonify(redirect(url_for("viewHost", host = myHostName)))) # this will send the content back to ajax
        return jsonify({'redirect': url_for("edit_host", hostName=myHostName)})
        """
        #return url_for("viewHost", host = myHostName)
        data = url_for("viewHost", host = myHostName)
        make_response(jsonify(data), 200)
        """
    elif myAjaxRequest["endPoint"] == "decomHost":
        myHostName = myAjaxRequest["args"]["hostName"]
        myDecomDoc = myAjaxRequest["args"]["decomDoc"]
        myDecomDate = myAjaxRequest["args"]["decomDate"]
        myDecomComments = myAjaxRequest["args"]["comments"]
        print(f'host name : {myHostName}, decom doc: {myDecomDoc}, decom date : {myDecomDate}, comments : {myDecomComments}')

        myArguments = {"hostName" : myHostName, "decomDoc" : myDecomDoc, "decomDate" : myDecomDate, "comments" : myDecomComments, "userId" : session["userId"]}
        myMethod = "decomHost"

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while performing decom of host {myHostName}, error >>> {myResult['message']} !!!","danger")
            #raise ValueError(myResult["message"])
        else:
            flash(f"Decom host operation {myHostName} was successful !!","succcess")

        return jsonify({'redirect': url_for("hosts")})

    elif myAjaxRequest["endPoint"] == "viewTenant":
        myTenantName = myAjaxRequest["args"]["tenantName"]
        print(f'tenantName : {myTenantName}')
        return jsonify({'redirect': url_for("view_tenant", tenantName=myTenantName)})

    elif myAjaxRequest["endPoint"] == "editTenant":
        myTenantName = myAjaxRequest["args"]["tenantName"]
        print(f'tenantName : {myTenantName}')
        return jsonify({'redirect': url_for("edit_tenant", tenantName=myTenantName)})

    elif myAjaxRequest["endPoint"] == "decomTenant":
        myTenantName = myAjaxRequest["args"]["tenantName"]
        myDecomDoc = myAjaxRequest["args"]["decomDoc"]
        myDecomDate = myAjaxRequest["args"]["decomDate"]
        myDecomComments = myAjaxRequest["args"]["comments"]
        print(f'tenant name : {myTenantName}, decom doc: {myDecomDoc}, decom date : {myDecomDate}, comments : {myDecomComments}')

        myArguments = {"tenantName" : myTenantName, "decomDoc" : myDecomDoc, "decomDate" : myDecomDate, "comments" : myDecomComments, "userId" : session["userId"]}
        myMethod = "decomTenant"

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while performing decom of tenant {myTenantName}, error >>> {myResult['message']} !!!","danger")
            #raise ValueError(myResult["message"])
        else:
            flash(f"Decom tenant operation {myTenantName} was successful !!","success")

        return jsonify({'redirect': url_for("tenants")})

    elif myAjaxRequest["endPoint"] == "viewTenantMember":
        myTenantMemberId = myAjaxRequest["args"]["tenantMemberId"]
        print(f'tenantMemberId : {myTenantMemberId}')
        return jsonify({'redirect': url_for("view_tenant_member", tenantMemberId=myTenantMemberId)})

    elif myAjaxRequest["endPoint"] == "viewDBAdmin":
        myEmployeeId = myAjaxRequest["args"]["employeeId"]
        print(f'admin employee id : {myEmployeeId}, request : view')
        return jsonify({'redirect': url_for("view_db_admin", employeeId=myEmployeeId)})

    elif myAjaxRequest["endPoint"] == "editDBAdmin":
        myEmployeeId = myAjaxRequest["args"]["employeeId"]
        print(f'admin employee id : {myEmployeeId}, request : edit')
        return jsonify({'redirect': url_for("editDBAdmin", employeeId=myEmployeeId)})

    elif myAjaxRequest["endPoint"] == "offboardDBAdmin":
        myEmployeeId = myAjaxRequest["args"]["employeeId"].strip()
        myOffBoardingDoc = myAjaxRequest["args"]["offBoardingDoc"].strip()
        myOffBoardingDate = myAjaxRequest["args"]["offBoardingDate"].strip()
        print(f'admin employee id : {myEmployeeId}, request : view')
        myMethod = "offBoardDBAdmin"
        myArguments = {"employeeId" : myEmployeeId, "offBoardingDoc" : myOffBoardingDoc, "offBoardDate" : myOffBoardingDate}
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        if myResult["status"] == "UnSuccess":
            raise ValueError(myResult["message"])
        else:
            return jsonify({'redirect': url_for("admin_roster")})
        #

    elif myAjaxRequest["endPoint"] == "offboardDBAdminTech":
        myEmployeeId = myAjaxRequest["args"]["employeeId"].strip()
        myDBTechnology = myAjaxRequest["args"]["dbTechnology"].strip()
        myOffBoardingDoc = myAjaxRequest["args"]["offBoardingDoc"].strip()
        myOffBoardingDate = myAjaxRequest["args"]["offBoardingDate"].strip()
        print(f'admin employee id : {myEmployeeId}, dbTechnology : {myDBTechnology} request : offboard')
        myMethod = "offBoardDBAdminTech"
        myArguments = {"employeeId" : myEmployeeId, "dbTechnology" : myDBTechnology, "offBoardingDoc" : myOffBoardingDoc, "offBoardDate" : myOffBoardingDate}
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        print(myResult)
        if myResult["status"] == "UnSuccess":
            #myResult.update({"statusCode" : 401})
            #return jsonify(myResult), 401
            flash(f"Unable to offboard employee id {myEmployeeId}'s {myDBTechnology.upper()} database login id {myDBLoginIds}, error >>> {myResult['message']}")
        else:
            flash(f"Employee id {myEmployeeId}'s {myDBTechnology.upper()} database login id {myDBLoginIds} offborded successfully !!")
        
        return jsonify({'redirect': url_for("admin_roster")})

    elif myAjaxRequest["endPoint"] == "onboardDBAdminTech":
        myOpco = myAjaxRequest["args"]["opco"].strip()
        myEmployeeId = myAjaxRequest["args"]["employeeId"].strip()
        myDBTechnology = myAjaxRequest["args"]["dbTechnology"].strip()
        myOnBoardingDoc = myAjaxRequest["args"]["onBoardingDoc"].strip()
        myOnBoardingDate = myAjaxRequest["args"]["onBoardingDate"].strip()
        myDBLoginIds = myAjaxRequest["args"]["dbLoginIds"].strip()
        print(f'admin employee id : {myEmployeeId}, dbTechnology : {myDBTechnology} request : onboard new login')
        myMethod = "onBoardDBAdmin"
        myArguments = {
            "employeeId" : myEmployeeId,
            "opco" : myOpco.upper(),
            "dbTechnology" : myDBTechnology, 
            "supportingDoc" : myOnBoardingDoc, 
            "onBoardDate" : myOnBoardingDate, 
            "dbLoginId" : util.splitStrWMultipleDelimiters(myDBLoginIds,[","," ",";",":"]),
            "userId" : session["userId"]
        }
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        #print(myResult)
        if myResult["status"] == "UnSuccess":
            flash(f"Unable to onboard employee id {myEmployeeId}'s {myDBTechnology.upper()} database login id {myDBLoginIds}, error >>> {myResult['message']}","danger")
            #myResult.update({"statusCode" : 401})
            #return jsonify(myResult), 401
        else:
            flash(f"Employee id {myEmployeeId}'s {myDBTechnology.upper()} database login id {myDBLoginIds} onboarded successfully !!","success")
        
        return jsonify({'redirect': url_for("admin_roster")})

    elif myAjaxRequest["endPoint"] == "viewAuditScan":
        myHostName = myAjaxRequest["args"]["hostName"]
        myScanDate = util.convStr2DateViaParser(myAjaxRequest["args"]["scanDate"].strip())
        myScanDate = util.convertDate2Str(myScanDate,"%m-%d-%Y")

        print(f'hostName : {myHostName}, scanDate : {myScanDate}, request : view')
        return jsonify({'redirect': url_for("view_scan_proc_detail", hostName = myHostName.strip(), scanDate = myScanDate.strip())})

    elif myAjaxRequest["endPoint"] == "getDBLists4Tech":
        myDBTechnology = myAjaxRequest["args"]["dbTechnology"]
        #print(f'dbTechnology : {myDBTechnology}')
        myMethod = "getAllTenantsName"
        
        myArguments = {"status" : "Active", "userId" : session["userId"]}

        if "opco" in myAjaxRequest["args"]:
            myArguments.update({"opco" : myAjaxRequest["args"]["opco"].strip()})
        else:
            myArguments.update({"opco" : "ALL"})

        if "region" in myAjaxRequest["args"]:
            myArguments.update({"region" : myAjaxRequest["args"]["region"].strip()})
        else:
            myArguments.update({"region" : "ALL"})

        if "dbTechnology" in myAjaxRequest["args"]:
            myArguments.update({"dbTechnology" : myAjaxRequest["args"]["dbTechnology"].strip()})
        else:
            myArguments.update({"dbTechnology" : "ALL"})
        
        if "env" in myAjaxRequest["args"]:
            myArguments.update({"env" : myAjaxRequest["args"]["env"].strip()})
        else:
            myArguments.update({"env" : "ALL"})

        #print(f"testing - arguments >>> {myArguments}")

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        
        myTenants = []
        if myResult["status"] == "UnSuccess":
            print(f"An error occurred while retrieving database name >>> '{myDBTechnology}' !!!","danger")
        else:
            myTenantsData = myResult["data"]
            if myTenantsData:
                myTenants.append({"id" : "ALL", "name" : "ALL Databases"})
                for tenant in myTenantsData:
                    #myTenants.append("".join([tenant["opco"], ".", tenant["dcLocation"], ".", tenant["dbCluster"] ]))
                    myTenants.append({"id" : tenant["_id"], "name" : tenant["dbCluster"]})
            if not myTenants:
                print(f"There are no databases available for '{myDBTechnology}' !!!","warning")

        #print(f"testing - returning >>> {myTenants}")
        return jsonify(myTenants)

    elif myAjaxRequest["endPoint"] == "getPendingAppDBs":
        myTenant = myAjaxRequest["args"]["tenantName"]
        myMethod = "getPendingAppDBs"
        myArguments = {"tenantName" : myTenant, "userId" : session["userId"]}
        #print(f"testing - pending app dbs args >>> {myArguments}")

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        myAppDBs = []
        if myResult["status"] == "UnSuccess":
            print(f"An error occurred while retrieving database name for '{myTenant}' >>> {myResult['message']} !!!","danger")
        else:
            for db in myResult["data"]:
                myAppDBs.append({"id" : db["dbName"], "name" : db["dbName"]})
            if not myAppDBs:
                print(f"There are no databases available for '{myArguments}' !!!")

        #print(f"testing - pending app dbs >>> {myAppDBs}")
        return jsonify(myAppDBs)

    elif myAjaxRequest["endPoint"] == "getDBConfigKey":
        myDBTechnology = myAjaxRequest["args"]["dbTechnology"]
        print(f'dbTechnology : {myDBTechnology}')
        myMethod = "getDBConfigKey"
        
        myArguments = {"dbTechnology" : myDBTechnology, "userId" : session["userId"]}
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        myConfigKeys = []
        if myResult["status"] == "UnSuccess":
            print(f"An error occurred while retrieving database configuration key for >>> '{myDBTechnology}' !!!","danger")
        else:
            myConfigKeys = myResult["data"]
            if not myConfigKeys:
                print(f"There are no database config key available for '{myDBTechnology}' !!!","warning")

        print(f"returning config keys for {myDBTechnology} >> {myConfigKeys}")
        return jsonify(myConfigKeys)

    elif myAjaxRequest["endPoint"] == "getDBTenantDetails":
        myTenantName = myAjaxRequest["args"]["tenantName"]
        myMethod = "getATenantDetails"
        myArguments = {"tenantName" : myTenantName}
        print(f'args : {myArguments}, method : {myMethod}')
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        print(f"db results >>> {myResult}")
        myTenantDetail = myResult["data"]

        #print(f"db details >>> {myTenantDetail}")

        return jsonify(myTenantDetail)

    elif myAjaxRequest["endPoint"] == "viewCompTask":
        myCompTaskId = myAjaxRequest["args"]["compTaskId"].strip()
        print(f'processing comp task id : {myCompTaskId}, request : view')
        return jsonify({'redirect': url_for("view_comp_task", compTaskId = myCompTaskId)})

    elif myAjaxRequest["endPoint"] == "viewTenantCompliance":
        myTenantName = myAjaxRequest["args"]["tenantName"].strip()
        myCompRunDate = myAjaxRequest["args"]["compRunDate"].strip()
        print(f'processing tenant compliance : {myTenantName}, {myCompRunDate} request : view')
        return jsonify({'redirect': url_for("view_tenant_compliance", tenantName = myTenantName, runDate = myCompRunDate)})

    elif myAjaxRequest["endPoint"] == "editCompTask":
        myCompTaskId = myAjaxRequest["args"]["compTaskId"].strip()
        print(f'processing comp task id : {myCompTaskId}, request : edit')
        return jsonify({'redirect': url_for("editCompTask", compTaskId = myCompTaskId)})

    elif myAjaxRequest["endPoint"] == "viewProductVersion":
        myDBTechnology = myAjaxRequest["args"]["dbTechnology"].strip().lower()
        myBaseVersion = myAjaxRequest["args"]["baseVersion"].strip()
        print(f'processing view product version : {myDBTechnology}/{myBaseVersion}, request : view')
        return jsonify({'redirect': url_for("view_product_version", dbTechnology = myDBTechnology, version = myBaseVersion)})

    elif myAjaxRequest["endPoint"] == "getAllValidBaseVersion":
        myDBTechnology = myAjaxRequest["args"]["dbTechnology"].strip().lower()
        print(f'processing get all product valid base version : {myDBTechnology}, request : view')
        myMethod = "getAllVerDetails"
        myArguments = {"dbTechnology" : myDBTechnology}

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        myVersionData = []

        if myResult["status"] == "UnSuccess":
            print(f"An error occurred while retrieving all base version details for '{myAjaxRequest['args']} >>> {myResult['message']}' !!!")
            return jsonify(myVersionData)

        if myResult["data"]:
            myVersionData = [ver["baseVersion"] for ver in myResult["data"] if not (ver["eosDate"] or ver["eolDate"]) ]
        
        return jsonify(myVersionData)

    elif myAjaxRequest["endPoint"] == "getABaseVerDetails":
        myDBTechnology = myAjaxRequest["args"]["dbTechnology"].strip().lower()
        myVersion = myAjaxRequest["args"]["baseVersion"].strip().lower()
        print(f'processing get a base version detail : {myDBTechnology} {myVersion}, request : view')
        myMethod = "getAVerDetails"
        myArguments = {"dbTechnology" : myDBTechnology, "version" : myVersion}

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        myVersionData = []

        if myResult["status"] == "UnSuccess":
            print(f"An error occurred while retrieving all base version details for '{myAjaxRequest['args']} >>> {myResult['message']}' !!!")
            return jsonify(myVersionData)

        if myResult["data"]:
            if "versions" in myResult["data"]:
                myResult["data"].pop("versions",None)
            return jsonify(myResult["data"])
        else:
            return jsonify({})

    elif myAjaxRequest["endPoint"] == "getCompTasks":
        #myDBTechnology = myAjaxRequest["args"]["dbTechnology"]
        print(f'args received : {myAjaxRequest["args"]}')
        myMethod = "getCompTaskDetail"
        myArguments = {
            "opco" : myAjaxRequest["args"]["opco"], 
            "region" : myAjaxRequest["args"]["region"], 
            "env" : myAjaxRequest["args"]["env"], 
            "dbTechnology" : myAjaxRequest["args"]["dbTechnology"],
            "tenant" : "ALL",
            "compliance" : myAjaxRequest["args"]["compliance"],
            "status" : myAjaxRequest["args"]["status"]
        }
        
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        
        myComplianceTasks = []
        if myResult["status"] == "UnSuccess":
            print(f"An error occurred while retrieving pending compliance tasks  for '{myAjaxRequest['args']} >>> {myResult['message']}' !!!","danger")
        else:
            if myResult["data"]:
                myComplianceTasks = [{
                    "id" : comp["_id"],
                    "value" : "".join([str(util.convStr2DateViaParser(comp["ts"])), "   :   ",  comp["env"].upper(), "   :   ",
                        (comp["tenantId"] if "tenantId" in comp and comp["tenantId"] else comp["tenantName"]), "   :   ", 
                        comp["otherData"], "   :   ", 
                        comp["tag"] ])
                    } for comp in myResult["data"]]

            if not myComplianceTasks:
                print(f"There are no complinace tasks available for '{myAjaxRequest['args']}' !!!","warning")

        return jsonify(myComplianceTasks)

    elif myAjaxRequest["endPoint"] == "getHostInventory4Chart":
        #myDBTechnology = myAjaxRequest["args"]["dbTechnology"]
        print(f'args received : {myAjaxRequest["args"]}')
        myMethod = "getHostInventory"
        myArguments = {
            "opco" : "ALL", 
            "region" : "ALL", 
            "env" : "ALL", 
            "dbTechnology" : "ALL",
            "tenant" : "ALL",
            "status" : "ACTIVE"
        }
        
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        
        myChartLabel = []
        myChartData = []
        if myResult["status"] == "UnSuccess":
            print(f"An error occurred while retrieving pending compliance tasks  for '{myAjaxRequest['args']} >>> {myResult['message']}' !!!","danger")
        else:
            if myResult["data"]:
                myChartLabel = list(set([host["dcLocation"] for host in myResult["data"]]))
                for host in myResult["data"]:
                    pass
                myComplianceTasks = [{
                    "id" : comp["_id"],
                    "value" : "".join([str(util.convStr2DateViaParser(comp["ts"])), "   :   ",  comp["env"].upper(), "   :   ",
                        (comp["tenantId"] if "tenantId" in comp and comp["tenantId"] else comp["tenantName"]), "   :   ", 
                        comp["otherData"], "   :   ", 
                        comp["tag"] ])
                    } for comp in myResult["data"]]

        return jsonify(myComplianceTasks)
    elif myAjaxRequest["endPoint"] == "getSearchCompForSearchIn":
        print(f'args received : {myAjaxRequest["args"]}')

        if myAjaxRequest["args"]["searchIn"].strip().lower() == "live":
            mySearchComp = [
                {"id" : "db.config", "display" : "DB Config"},
                {"id" : "db.users", "display" : "DB Users"},
                {"id" : "db.roles", "display" : "DB Roles"},
                {"id" : "db.database", "display" : "Databases"},
                {"id" : "oplog.size", "display" : "Oplog Size"},
                {"id" : "current.op", "display" : "OPs In-Progress"},
                {"id" : "server.status", "display" : "Server Status"},
                {"id" : "top", "display" : "Top processes"},
                {"id" : "log", "display" : "Mongod logs (latest)"},
                {"id" : "conn.stats", "display" : "Connection Status"},
                #("conn.pool.stats", "display" : "Connection Pool Status"},
                {"id" : "replication.info", "display" : "Replication Info"},
                {"id" : "hosts.info", "display" : "Hosts Info"},
                {"id" : "db.latest.backup", "display" : "DB Latest Backup"}
            ]
        else:
            mySearchComp = [
                {"id" : "db.config", "display" : "DB Config"},
                {"id" : "db.users", "display" : "DB Users"},
                {"id" : "db.roles", "display" : "DB Roles"},
                {"id" : "db.database", "display" : "Databases"},
                {"id" : "oplog.size", "display" : "Oplog Size"} 
            ]
        print(f"returning search comp >>> {mySearchComp}")
        return jsonify(mySearchComp)
    elif myAjaxRequest["endPoint"] == "getOtherInfoAreaData":
        print(f'args received : {myAjaxRequest["args"]}')
        myArea = myAjaxRequest["args"]["area"].strip()
        myResponse = {}

        myMethod = "getOtherInfo"
        myArguments = {"userId" : session["userId"]}
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        print(f"testing - result >> {myResult}")
        if myResult["status"] == "UnSuccess":
            myResponse.update({"status" : "UnSuccess", "error" : myResult['message']})
            print(f"An error occurred while retrieving pending compliance tasks  for '{myAjaxRequest['args']} >>> {myResult['message']}' !!!","danger")
            return jsonify(myResponse)

        if myResult["data"]:
            myResult["data"] = myResult["data"][0]
        else:
            myResponse.update({"status" : "UnSuccess", "error" : "No data found !!!"})
            return jsonify(myResponse)

        myResultRawData = [area for area in myResult["data"]["info"] if area["area"] == myArea]

        if myResultRawData:
            myResultRawData = myResultRawData[0]
        else:
            print(f'area {myArea} detail not found !!!')
            myResponse.update({"status" : "UnSuccess", "error" : f'area {myArea} detail not found !!!'})
            return jsonify(myResponse)

        myResponse = {
            "status" : "Success",
            "incidents" : myResultRawData["incidents"],
            "changeOrders" : myResultRawData["changeOrders"],
            "dls" : myResultRawData["dls"],
            "url" : myResultRawData["url"],
            "escalations" : myResultRawData["escalations"],
            "other" : myResultRawData["other"]
        }
        print(f"testing - response >>> {myResponse}")
        return jsonify(myResponse)
    else:
        return jsonify("#")

@login_required
@app.route("/download/")
def downloadFile(file_):
    print(f'args received : {myAjaxRequest["args"]}')

    #if [arg for arg in myAjaxRequest["args"] if arg not in ["contentType", "contentArgs"]]:
    #    return jsonify("#")    
    
    if myAjaxRequest["args"]["contentType"] == "hosts":
        myResult = createHostReport(myAjaxRequest["args"]["contentArgs"]["opco"], myAjaxRequest["args"]["contentArgs"]["region"], myAjaxRequest["args"]["contentArgs"]["dbTechnology"], myAjaxRequest["args"]["contentArgs"]["env"])

        if myResult["status"] != "Success":
            return jsonify({"error" : f"An error occurred while generating hosts report >>> {myResult['message']} !!!"})

        if not myResult["data"]:
            return jsonify({"error" : f"No data available >>> {myResult['message']} !!!"})

        print(f'testing - result : {myResult}')
        return send_from_directory(util.getFileDirName(myResult["data"]), filename=util.getFileName(myResult["data"]), as_attachment=True)

@login_required
@app.route("/comp_report/", methods=['GET','POST'])
#@cache.cached(timeout=50)
def comp_report():
    print(f"compliance_report; session details >>> {session}")
    form = forms.CompReportForm()
    print(request)
    if request.method == "POST":
        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
        myArguments = {}

        print(f"request >>> {request.form}")
        myReport = request.form["report"]
        print(f"my report request >> {myReport}")
        if myReport.lower() == "audit_report":
            myDBTechnology = request.form["dbTechnology"]
            
            if myDBTechnology.upper() not in  ["MONGO"]:
                flash(f"Audit reporting for {myDBTechnology} is not yet implemented, Pls check back later !!!","warning")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            myOpco = request.form["opco"]
            myDBTechnology = request.form["dbTechnology"]
            myEnv = request.form["env"]
            myStartDate = request.form["startDate"]
            myEndDate = request.form["endDate"]
            myTenantList = ["ALL"]
            print(f"arguments received in form >>> report : {myReport}, opco : {myOpco}, dbTechnology : {myDBTechnology}, startDate : {myStartDate}, endDate : {myEndDate}")
            """
            myMethod = "getAuditData"
            myArguments = {
                "opco" : myOpco.upper(), 
                "env" : myEnv,
                "tenantList" : myTenantList,
                "dbTechnology" : myDBTechnology, 
                "startDate" : myStartDate, 
                "endDate" : myEndDate
            }
            # generating file
            myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
            #print(f"result >>> {myResult}")
            # checking the result of rest api call
            if myResult["status"].upper() == "UNSUCCESS":
                flash(f"{myResult['message']} !!","danger")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)
            
            # we have audit data, we need to create a report
            myArguments = {"auditData" : myResult["data"], "auditArg" : myArguments, "userId" : "svc-dev-deploy-app"}
            myResponse = report.buildMongoAuditReport(**myArguments)
            print(myResponse)
            #return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form=form, response = myResponse)
            #return send_file(myResult["data"], attachment_filename=uitl.getFileName(myResult["data"]))
            """
            myResult = createMongoAuditReport(myOpco, myEnv, myDBTechnology, myTenantList, myStartDate, myEndDate)
            if myResult["status"] != "Success":
                flash(f"An error occurred while generating audit report >>> {myResult['message']} !!!","danger")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            if not myResult["data"]:
                flash(f"No data available !!!","danger")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            return send_from_directory(util.getFileDirName(myResult["data"]), filename=util.getFileName(myResult["data"]), as_attachment=True)

        elif myReport.lower() == "dbver_comp_report":
            myDBTechnology = request.form["dbTechnology"]
            myOpco = request.form["opco"]

            print(f"database ver compliance report for {myDBTechnology}")

            if myDBTechnology.upper() !=  "MONGO":
                flash(f"Database version compliance report for {myDBTechnology} is not yet implemented, Pls check back later !!!","danger")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            myResult = createDBVerCompReport(myOpco, myDBTechnology)
            if myResult["status"] != "Success":
                flash(f"An error occurred while generating {myDBTechnology} database compliance report for '{myOpco.upper()}' Opco >>> {myResult['message']} !!!","danger")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)
            
            print(f"result >> {myResult}")

            if not myResult["data"]:
                flash(f"No data available !!!","danger")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            return send_from_directory(util.getFileDirName(myResult["data"]), filename=util.getFileName(myResult["data"]), as_attachment=True)

        elif myReport.lower() == "db_license_comp_report":
            myDBTechnology = request.form["dbTechnology"]
            myOpco = request.form["opco"]

            print(f"{myDBTechnology.upper()} database license report ")

            if myDBTechnology.upper() !=  "MONGO":
                flash(f"Database version compliance report for {myDBTechnology} is not yet implemented, Pls check back later !!!","danger")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            myResult = createDBLicenseReport(myOpco, myDBTechnology)

            if myResult["status"] != "Success":
                flash(f"An error occurred while generating {myDBTechnology} database licnesing report for '{myOpco.upper()}' Opco >>> {myResult['message']} !!!","danger")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)
            
            print(f"result >> {myResult}")

            if not myResult["data"]:
                flash(f"No data available !!!","danger")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            return send_from_directory(util.getFileDirName(myResult["data"]), filename=util.getFileName(myResult["data"]), as_attachment=True)

        elif myReport.lower() == "dbadmin_comp_report":
            myDBTechnology = request.form["dbTechnology"]
            myOpco = request.form["opco"]

            print(f"database admin report for {myDBTechnology}")

            if myDBTechnology.upper() !=  "MONGO":
                flash(f"Database administrator report for {myDBTechnology} is not yet implemented, Pls check back later !!!","danger")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            myResult = createDBAdminCompReport(myOpco, myDBTechnology)

            if myResult["status"] != "Success":
                flash(f"An error occurred while generating {myDBTechnology} database administrator report for '{myOpco.upper()}' Opco >>> {myResult['message']} !!!","danger")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)
            
            print(f"result >> {myResult}")

            if not myResult["data"]:
                flash(f"No data available !!!","danger")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            #return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, file= myResult["data"])
            #return jsonify(util.getFileName(myResult["data"]))
            print("sending file for download")
            return send_from_directory(util.getFileDirName(myResult["data"]), filename=util.getFileName(myResult["data"]), as_attachment=True)
            #return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

        elif myReport.lower() == "montool_admin_comp_report":
            myDBTechnology = request.form["dbTechnology"]
            myOpco = request.form["opco"]

            print(f"Monitoring tool admin report for {myDBTechnology}")

            if myDBTechnology.upper() !=  "MONGO":
                flash(f"Monitoring tools admin report for {myDBTechnology} is not yet implemented, Pls check back later !!!","danger")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            if myDBTechnology.upper() ==  "MONGO":
                myResult = createMongoOpsMgrAdminReport(myOpco)

                if myResult["status"] != "Success":
                    flash(f"An error occurred while generating {myDBTechnology} Ops Manager admin report for '{myOpco.upper()}' Opco >>> {myResult['message']} !!!","danger")
                    return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)
            
            print(f"result >> {myResult}")

            if not myResult["data"]:
                flash(f"No data available !!!","danger")
                return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            return send_from_directory(util.getFileDirName(myResult["data"]), filename=util.getFileName(myResult["data"]), as_attachment=True)

    return render_template("compliance_report.html", title = "Compliance Reporting", user = "".join([session["userName"], " (", session["userId"], ")"]), form=form)

def createMongoAuditReport(opco, env, dbTechnology, tenantsList, startDate, endDate):
    """
    Create Mongo audit report based on the arguments
    """
    try:
        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
        myMethod = "getAuditData"
        myArguments = {
            "opco" : opco.upper(), 
            "env" : env,
            "tenantList" : tenantsList,
            "dbTechnology" : dbTechnology, 
            "startDate" : startDate, 
            "endDate" : endDate
        }        
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        #print(f"result >>> {myResult}")
        # checking the result of rest api call
        if myResult["status"].upper() == "UNSUCCESS":
            return myResult

        # we have audit data, we need to create a report
        myArguments = {"auditData" : myResult["data"], "auditArg" : myArguments, "userId" : "svc-dev-deploy-app"}
        myResult = report.buildMongoAuditReport(**myArguments)
        #print(myAuditFile)
        return myResult
        #return util.buildResponse("success","success",myAuditFile)

    except Exception as error:
        return util.buildResponse("unSuccess",error)

def createDBVerCompReport(opco, dbTechnology):
    """
    Create database version compliance report
    """
    try:
        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
        myMethod = "getTenantVerComplianceData"
        myArguments = {
            "opco" : opco.upper(), 
            "dbTechnology" : dbTechnology
        }

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        # checking the result of rest api call
        if myResult["status"].upper() == "UNSUCCESS":
            return myResult

        if not myResult["data"]:
            return {"status": "UnSuccess","message" : "No data found !!"}

        # we have version data, we need to create a report
        myArguments = {"tenantVerCompData" : myResult["data"], "tenantVerCompArg" : myArguments, "userId" : "svc-dev-deploy-app"}
        myResult = report.buildTenantVerCompReport(**myArguments)
        #print(myAuditFile)
        return myResult
        #return util.buildResponse("success","success",myAuditFile)

    except Exception as error:
        return util.buildResponse("unSuccess",error)

def createDBAdminCompReport(opco, dbTechnology):
    """
    Create database administrator report
    """
    try:
        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

        if dbTechnology.upper() == "MONGO":
            myMethod = "getAdminUserSummaryList"
        else:
            return self.util.buildResponse("UnSuccess","{dbTechnology.upper()} admin user report is not yet implemented !!!")
    
        myArguments = {
            "opco" : opco.upper(), 
            "dbTechnology" : dbTechnology
        }

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        if myResult["status"].upper() == "UNSUCCESS":
            return myResult

        myDBAdminUserList = myResult["data"]

        # we have db amdin data, we need admin roster data
        myMethod = "getDBAdminRoster"
        myArguments = {
            "opco" : opco.upper(), 
            "dbTechnology" : dbTechnology, 
            "status" : 'Active',
            "consolidated" : "no"
        }

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        if myResult["status"].upper() == "UNSUCCESS":
            return myResult

        myAdminRosterData = myResult["data"]
        # we have all data, we need admin roster data
        myArguments = {"dbAdminData" : myDBAdminUserList, "dbAdminArg" : myArguments, "dbAdminRosterData" : myAdminRosterData, "userId" : "svc-dev-deploy-app"}

        myResult = report.buildDBAdminComReport(**myArguments)

        return myResult
        #return util.buildResponse("success","success",myAuditFile)

    except Exception as error:
        return util.buildResponse("unSuccess",error)

def createMongoOpsMgrAdminReport(opco):
    """
    Create database administrator report
    """
    try:
        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

        myMethod = "getAllOpsMgrUser"
    
        myArguments = {
            "opco" : opco.upper()
        }

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        if myResult["status"].upper() == "UNSUCCESS":
            return myResult

        myOpsMgrAdminUserData = myResult["data"]

        # we have all data, we need admin roster data
        myArguments = {"opsMgrAdminData" : myOpsMgrAdminUserData, "opsMgrAdminArg" : myArguments, "userId" : "svc-dev-deploy-app"}

        myResult = report.buildOpsMgrUserReport(**myArguments)

        return myResult
        #return util.buildResponse("success","success",myAuditFile)

    except Exception as error:
        return util.buildResponse("unSuccess",error)

def createDBLicenseReport(opco, dbTechnology):
    """
    Create database administrator report
    """
    try:
        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

        # retrieving detail data for licensing
        myMethod = "getMongoLicensingData"
        myArguments = {"opco" : opco.upper(), "output" : "detail"}

        #print(f"testing - arguments for detail licensing data --> {myArguments}")

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        #print(f"testing - detail result --> {myResult}")

        if myResult["status"].upper() == "UNSUCCESS":
            return myResult

        myDetailData = myResult["data"]

        # retrieving summary data for licensing
        myArguments = {"opco" : opco.upper(), "output" : "summary"}

        #print(f"testing - arguments for summary licensing data --> {myArguments}")

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        #print(f"testing - summary result --> {myResult}")

        if myResult["status"].upper() == "UNSUCCESS":
            return myResult

        for host_ in myResult["data"]:
            if host_["totalDockerMemLimit"] == 0:
                host_.update({"licensingMemory" : host_["hostMemory"]})
            else:
                host_.update({"licensingMemory" : host_["hostMemory"] if host_["hostMemory"] < host_["totalDockerMemLimit"] else host_["totalDockerMemLimit"]})

        myOpcoStatsRawData = pd.DataFrame(myResult["data"]).groupby(["opco"])["licensingMemory"].apply(sum).to_dict()
        myOpcoStats = []

        #print(f"testing - opco stats raw >>> {myOpcoStatsRawData}, {list(myOpcoStatsRawData.keys())}")

        for opco in list(myOpcoStatsRawData.keys()):
            myOpcoStats.append({"opco" : opco, "totalLicensingMemoryGB" : int(round(myOpcoStatsRawData[opco]/(1024*1024*1024),0))})

        #print(f"testing - opco stats >>> {myOpcoStats}")

        mySummaryData = {
            "totalHosts" : len(list(set(host_["hostName"] for host_ in myResult["data"]))),
            "totalCPUs" : sum(list(host_["hostCPU"] for host_ in myResult["data"])),            
            "totalMemoryGB" : int(round(pd.DataFrame(myResult["data"]).sum().hostMemory/(1024*1024*1024),0)),
            "totalDockerMemAllocGB" : int(round(pd.DataFrame(myResult["data"]).sum().totalDockerMemLimit/(1024*1024*1024),0)),
            "totalDockerMemUsedGB" : int(round(pd.DataFrame(myResult["data"]).sum().totalDockerMemUsed/(1024*1024*1024),0)),
            "totalLicensingMemGB" : int(round(pd.DataFrame(myResult["data"]).sum().licensingMemory/(1024*1024*1024),0)),
            "opcoLicensingStats" : myOpcoStats
        }

        myArguments = {"opco" : opco, "licensingDetailData": myDetailData, "licensingSummaryData" : mySummaryData}

        #print(f"testing - arguments --> {myArguments}")

        myResult = report.genHostReport4MongoLicensing(**myArguments)

        #print(f"testing - report generation result >> {myResult}")

        return myResult

    except Exception as error:
        raise error
        return util.buildResponse("unSuccess",error)

def createHostReport(opco, region, dbTechnology, env):
    """
    Create Hosts report
    """
    try:
        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

        # retrieving detail data for licensing
        myMethod = "getHostInventory"
        myArguments = {"opco" : opco,"region" : region,"dbTechnology" : dbTechnology,"tag" : "ALL", "env" : env,"dcLocation" : "ALL", "userId" : session["userId"]}

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        if myResult["status"].upper() == "UNSUCCESS":
            return myResult

        myHostsData = myResult["data"]

        for host in myHostsData:
            host.update({
                "dbDetails" : ",".join(map(str, set([ "".join([ (tenant["dbTechnology"].upper() if "dbTechnology" in tenant else "N/A"), ":", (tenant["version"] if "version" in tenant else "N/A'"), ":", str( tenant["port"] if "port" in tenant else "N/A"), ":", (tenant["dbCluster"] if "dbCluster" in tenant else "N/A") ]) for tenant in host["tenants"] ])))
            })

            if "osConfig" in host and host["osConfig"]:
                host.update({
                    "os" : host["osConfig"]["os"],
                    "version" : host["osConfig"]["version"] if "version" in host["osConfig"] else "n/a",
                    "cpu" : host["osConfig"]["cpu"]["count"] if "cpu" in host["osConfig"] and "count" in host["osConfig"]["cpu"] else "n/a",
                    "memoryGB" : round(host["osConfig"]["memory"]["total"] / (1024*1024*1024)) if "memory" in host["osConfig"] else "n/a",
                    "swapGB" : round(host["osConfig"]["swap"]["total"] / (1024*1024*1024)) if "swap" in host["osConfig"] else "n/a"
                })
            else:
                host.update({
                    "cpu" : -1,
                    "memoryGB" : -1,
                    "swapGB" : -1
                })

        #print(f"testing - arguments --> {myArguments}")

        myResult = report.buildHostDetailsReport(**{"hostsArgs" : myArguments, "hostsData": myHostsData, "userId" : session["userId"]})

        print(f"testing - report generation result >> {myResult}")

        return myResult

    except Exception as error:
        raise error
        return util.buildResponse("unSuccess",error)

def createTenantReport(opco, region, dbTechnology, env, status):
    """
    Create Hosts report
    """
    try:
        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

        # retrieving detail data for licensing
        myMethod = "getTenantsInventory"
        myArguments = {"opco" : opco.upper(), "region" : region, dbTechnology : dbTechnology, status : "Active", "output" : ["header","members.summary","databases"]}

        #print(f"testing - arguments for detail licensing data --> {myArguments}")

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        #print(f"testing - detail result --> {myResult}")

        if myResult["status"].upper() == "UNSUCCESS":
            return myResult

        myDetailData = myResult["data"]

        # retrieving summary data for licensing
        myArguments = {"opco" : opco.upper(), "output" : "summary"}

        #print(f"testing - arguments for summary licensing data --> {myArguments}")

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        #print(f"testing - summary result --> {myResult}")

        if myResult["status"].upper() == "UNSUCCESS":
            return myResult

        for host_ in myResult["data"]:
            if host_["totalDockerMemLimit"] == 0:
                host_.update({"licensingMemory" : host_["hostMemory"]})
            else:
                host_.update({"licensingMemory" : host_["hostMemory"] if host_["hostMemory"] < host_["totalDockerMemLimit"] else host_["totalDockerMemLimit"]})

        myOpcoStatsRawData = pd.DataFrame(myResult["data"]).groupby(["opco"])["licensingMemory"].apply(sum).to_dict()
        myOpcoStats = []

        #print(f"testing - opco stats raw >>> {myOpcoStatsRawData}, {list(myOpcoStatsRawData.keys())}")

        for opco in list(myOpcoStatsRawData.keys()):
            myOpcoStats.append({"opco" : opco, "totalLicensingMemoryGB" : int(round(myOpcoStatsRawData[opco]/(1024*1024*1024),0))})

        #print(f"testing - opco stats >>> {myOpcoStats}")

        mySummaryData = {
            "totalHosts" : len(list(set(host_["hostName"] for host_ in myResult["data"]))),
            "totalCPUs" : sum(list(host_["hostCPU"] for host_ in myResult["data"])),            
            "totalMemoryGB" : int(round(pd.DataFrame(myResult["data"]).sum().hostMemory/(1024*1024*1024),0)),
            "totalDockerMemAllocGB" : int(round(pd.DataFrame(myResult["data"]).sum().totalDockerMemLimit/(1024*1024*1024),0)),
            "totalDockerMemUsedGB" : int(round(pd.DataFrame(myResult["data"]).sum().totalDockerMemUsed/(1024*1024*1024),0)),
            "totalLicensingMemGB" : int(round(pd.DataFrame(myResult["data"]).sum().licensingMemory/(1024*1024*1024),0)),
            "opcoLicensingStats" : myOpcoStats
        }

        myArguments = {"opco" : opco, "licensingDetailData": myDetailData, "licensingSummaryData" : mySummaryData}

        #print(f"testing - arguments --> {myArguments}")

        myResult = report.genHostReport4MongoLicensing(**myArguments)

        #print(f"testing - report generation result >> {myResult}")

        return myResult

    except Exception as error:
        raise error
        return util.buildResponse("unSuccess",error)

def createAdminRosterReport(opco, dbTechnology):
    """
    Create Hosts report
    """
    try:
        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

        # retrieving detail data for licensing
        myMethod = "getMongoLicensingData"
        myArguments = {"opco" : opco.upper(), "output" : "detail"}

        #print(f"testing - arguments for detail licensing data --> {myArguments}")

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        #print(f"testing - detail result --> {myResult}")

        if myResult["status"].upper() == "UNSUCCESS":
            return myResult

        myDetailData = myResult["data"]

        # retrieving summary data for licensing
        myArguments = {"opco" : opco.upper(), "output" : "summary"}

        #print(f"testing - arguments for summary licensing data --> {myArguments}")

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        #print(f"testing - summary result --> {myResult}")

        if myResult["status"].upper() == "UNSUCCESS":
            return myResult

        for host_ in myResult["data"]:
            if host_["totalDockerMemLimit"] == 0:
                host_.update({"licensingMemory" : host_["hostMemory"]})
            else:
                host_.update({"licensingMemory" : host_["hostMemory"] if host_["hostMemory"] < host_["totalDockerMemLimit"] else host_["totalDockerMemLimit"]})

        myOpcoStatsRawData = pd.DataFrame(myResult["data"]).groupby(["opco"])["licensingMemory"].apply(sum).to_dict()
        myOpcoStats = []

        #print(f"testing - opco stats raw >>> {myOpcoStatsRawData}, {list(myOpcoStatsRawData.keys())}")

        for opco in list(myOpcoStatsRawData.keys()):
            myOpcoStats.append({"opco" : opco, "totalLicensingMemoryGB" : int(round(myOpcoStatsRawData[opco]/(1024*1024*1024),0))})

        #print(f"testing - opco stats >>> {myOpcoStats}")

        mySummaryData = {
            "totalHosts" : len(list(set(host_["hostName"] for host_ in myResult["data"]))),
            "totalCPUs" : sum(list(host_["hostCPU"] for host_ in myResult["data"])),            
            "totalMemoryGB" : int(round(pd.DataFrame(myResult["data"]).sum().hostMemory/(1024*1024*1024),0)),
            "totalDockerMemAllocGB" : int(round(pd.DataFrame(myResult["data"]).sum().totalDockerMemLimit/(1024*1024*1024),0)),
            "totalDockerMemUsedGB" : int(round(pd.DataFrame(myResult["data"]).sum().totalDockerMemUsed/(1024*1024*1024),0)),
            "totalLicensingMemGB" : int(round(pd.DataFrame(myResult["data"]).sum().licensingMemory/(1024*1024*1024),0)),
            "opcoLicensingStats" : myOpcoStats
        }

        myArguments = {"opco" : opco, "licensingDetailData": myDetailData, "licensingSummaryData" : mySummaryData}

        #print(f"testing - arguments --> {myArguments}")

        myResult = report.genHostReport4MongoLicensing(**myArguments)

        #print(f"testing - report generation result >> {myResult}")

        return myResult

    except Exception as error:
        raise error
        return util.buildResponse("unSuccess",error)

def createAAppRosterReport(opco, dbTechnology):
    """
    Create Hosts report
    """
    try:
        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

        # retrieving detail data for licensing
        myMethod = "getMongoLicensingData"
        myArguments = {"opco" : opco.upper(), "output" : "detail"}

        #print(f"testing - arguments for detail licensing data --> {myArguments}")

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        #print(f"testing - detail result --> {myResult}")

        if myResult["status"].upper() == "UNSUCCESS":
            return myResult

        myDetailData = myResult["data"]

        # retrieving summary data for licensing
        myArguments = {"opco" : opco.upper(), "output" : "summary"}

        #print(f"testing - arguments for summary licensing data --> {myArguments}")

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        #print(f"testing - summary result --> {myResult}")

        if myResult["status"].upper() == "UNSUCCESS":
            return myResult

        for host_ in myResult["data"]:
            if host_["totalDockerMemLimit"] == 0:
                host_.update({"licensingMemory" : host_["hostMemory"]})
            else:
                host_.update({"licensingMemory" : host_["hostMemory"] if host_["hostMemory"] < host_["totalDockerMemLimit"] else host_["totalDockerMemLimit"]})

        myOpcoStatsRawData = pd.DataFrame(myResult["data"]).groupby(["opco"])["licensingMemory"].apply(sum).to_dict()
        myOpcoStats = []

        #print(f"testing - opco stats raw >>> {myOpcoStatsRawData}, {list(myOpcoStatsRawData.keys())}")

        for opco in list(myOpcoStatsRawData.keys()):
            myOpcoStats.append({"opco" : opco, "totalLicensingMemoryGB" : int(round(myOpcoStatsRawData[opco]/(1024*1024*1024),0))})

        #print(f"testing - opco stats >>> {myOpcoStats}")

        mySummaryData = {
            "totalHosts" : len(list(set(host_["hostName"] for host_ in myResult["data"]))),
            "totalCPUs" : sum(list(host_["hostCPU"] for host_ in myResult["data"])),            
            "totalMemoryGB" : int(round(pd.DataFrame(myResult["data"]).sum().hostMemory/(1024*1024*1024),0)),
            "totalDockerMemAllocGB" : int(round(pd.DataFrame(myResult["data"]).sum().totalDockerMemLimit/(1024*1024*1024),0)),
            "totalDockerMemUsedGB" : int(round(pd.DataFrame(myResult["data"]).sum().totalDockerMemUsed/(1024*1024*1024),0)),
            "totalLicensingMemGB" : int(round(pd.DataFrame(myResult["data"]).sum().licensingMemory/(1024*1024*1024),0)),
            "opcoLicensingStats" : myOpcoStats
        }

        myArguments = {"opco" : opco, "licensingDetailData": myDetailData, "licensingSummaryData" : mySummaryData}

        #print(f"testing - arguments --> {myArguments}")

        myResult = report.genHostReport4MongoLicensing(**myArguments)

        #print(f"testing - report generation result >> {myResult}")

        return myResult

    except Exception as error:
        raise error
        return util.buildResponse("unSuccess",error)

@login_required
@app.route("/scan_status/", methods=['GET','POST'])
#@cache.cached(timeout=50)
def scan_status():
    print(f"scan_status; session details >>> {session}")
    """ we need to work on this pending
    if not( session.get("userId") and session.get("userName")):
        print("scan_status; redirecting to login, missing details in session")
        session.clear()
        return redirect("login")
    """
    # retrieving data via rest API
    form = forms.ScanStatusViewForm()
    # dynamic form selector --> https://www.youtube.com/watch?v=I2dJuNwlIH0

    #myOpco = "MARSH"
    #myStartDate = util.getCurrentDate()
    #myEndDate = util.getCurrentDate()

    print(request)
    if request.method == "POST":
        print(f"request >>> {request.form}")
        myOpco = request.form["opco"]
        myStartDate = request.form["startDate"]
        myEndDate = request.form["endDate"]
        print(f"start date : {myStartDate}")
        print(f"end date : {myEndDate}")
    else:
        myStartDate = form.startDate.data
        myEndDate = form.endDate.data
        myOpco = "ALL"

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    myMethod = "getAuditScanStatus"
    myArguments = {}
    
    myDBTechnology = "mongo"
    print(f"form start date :{form.startDate.data}, {type(form.startDate.data)}")
    print(f"form end date :{form.endDate.data}, {type(form.endDate.data)}")

    myArguments.update({
        "opco" : myOpco,
        #"dbTechnology" : myDBTechnology,
        "startDate" : util.convertDate2Str(myStartDate,'%m-%d-%Y') if not isinstance(myStartDate, str) else myStartDate,
        "endDate" : util.convertDate2Str(myEndDate,'%m-%d-%Y') if not isinstance(myEndDate, str) else myEndDate
    })
       
    headings = ("Opco", "DataCenter", "Region","Env","Host","Scan Date","Status","Results")
    rawHeadings = ["opco","dcLocation","region","env","hostName","scanDate","status","results"]

    print(f"query args >>> {myArguments}")
    
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    # checking the result of rest api call
    if myResult["status"].upper() == "UNSUCCESS":
        flash(f"{myResult['message']} !!","danger")
        return render_template("scan_status.html", title = "Audit Scan Status", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = headings, form = form, data=[])

    myScanStatusData = myResult["data"]
    for scan in myScanStatusData:
        #print(f"scan data >>> {scan}")
        if "results" in scan and not scan["results"]:
            scan.update({"results" : scan["status"]})

    #print(f"all scan data >> {myScanStatusData}")

    data = convertDict2TupleForHtml(rawHeadings, myScanStatusData, ["env"])
    print(f"current session >>> {session}")
    return render_template("scan_status.html", title = "Audit Scan Status", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = headings, form = form, data=data)

@login_required
@app.route("/audit_data/", methods=['GET','POST'])
#@cache.cached(timeout=50)
def audit_data():
    print(f"audit_data; session details >>> {session}")
    """ we need to work on this pending
    if not( session.get("userId") and session.get("userName")):
        print("scan_status; redirecting to login, missing details in session")
        session.clear()
        return redirect("login")
    """
    # retrieving data via rest API
    form = forms.AuditDataViewForm()
    # dynamic form selector --> https://www.youtube.com/watch?v=I2dJuNwlIH0

    #myOpco = "MARSH"
    #myStartDate = util.getCurrentDate()
    #myEndDate = util.getCurrentDate()

    print(f"audit data request >>> {request}")
    if request.method == "POST":
        print(f"request >>> {request.form}")
        print(f"opco >> {request.form['opco']}")
        print(f"env >> {request.form['env']}")
        print(f"dbtech >> {request.form['dbTechnology']}")
        print(f"start >> {request.form['startDate']}")
        print(f"end >> {request.form['endDate']}")
        myOpco = request.form['opco']
        print(f"opco >> {request.form['opco']}")
        myDBTechnology = request.form['dbTechnology']
        myEnv = request.form['env']
        myStartDate = request.form['startDate']
        myEndDate = request.form['endDate']
        print(f"arguments form POST >>> {myOpco}, {myDBTechnology}, {myStartDate}, {myEndDate}")
    
        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
        myMethod = "getAuditData"
        myArguments = {}
    else:
        myOpco = form.opco.data
        myDBTechnology = form.dbTechnology.data
        myEnv = form.env.data
        myStartDate = form.startDate.data
        myEndDate = form.endDate.data
        print(f"arguments form GET >>> {myOpco}, {myDBTechnology}, {myStartDate}, {myEndDate}")
    
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    myMethod = "getAuditData"
    myArguments = {}
    """
            myAtypeExcludeList = ["authCheck","authenticate"]
            myResult = self.repo.getAuditEvent(\
                #myKwArgs["securityToken"], myKwArgs["opco"], myKwArgs["region"], myKwArgs["tenantList"], \
                myKwArgs["securityToken"], 
                myKwArgs["opco"].upper(), myKwArgs["env"].lower(), \
                myKwArgs["dbTechnology"].lower(), myKwArgs["region"],  \
                myKwArgs["tenantList"], myKwArgs["startDate"], myKwArgs["endDate"])
    """
    
    print(f"form start date :{form.startDate.data}, {type(form.startDate.data)}")
    print(f"form end date :{form.endDate.data}, {type(form.endDate.data)}")

    myArguments.update({
        "opco" : myOpco,
        "dbTechnology" : myDBTechnology,
        "env" : myEnv,
        "tenantList" : ["ALL"],
        "startDate" : util.convertDate2Str(myStartDate,'%m-%d-%Y') if not isinstance(myStartDate, str) else myStartDate,
        "endDate" : util.convertDate2Str(myEndDate,'%m-%d-%Y') if not isinstance(myEndDate, str) else myEndDate
    })        

    print(f"query args >>> {myArguments}")
    
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    # checking the result of rest api call
    if myResult["status"].upper() == "UNSUCCESS":
        flash(f"{myResult['message']} ","danger")
        return render_template("view_audit.html", title = "Audit Data", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, auditData = [])

    if not myResult["data"]:
        flash(f"No data found for {myOpco}/{myEnv}/{myDBTechnology}/{myStartDate}/{myEndDate} !!, Pls refine your filter criteria","warning")
        return render_template("view_audit.html", title = "Audit Data", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

    myAuditData = myResult["data"]

    headings = ("Opco", "DB Technology", "TS", "HostName", "Database", "Event","Local","Remote","User","Role", "Parameter","Supporting Doc")
    rawHeadings = ["opco","dbTechnology","ts","hostName","tenantName","atype","localData","remoteData","userData","rolesData","paramData","supportingDoc"]
    
    for aud_ in myAuditData:
        aud_.update({
            "localData" : ','.join('{}:{}'.format(*data) for data in aud_["local"].items())  if "local" in aud_ else "n/a",
            "paramData" : ','.join('{}:{}'.format(*data) for data in aud_["param"].items())  if "param" in aud_ else "n/a",
            "remoteData" : ','.join('{}:{}'.format(*data) for data in aud_["remote"].items())  if "remote" in aud_ else "n/a",
            "usersData" : "<pending array>",
            "rolesData" : "<penidng array>",
            "dbTechnology" : aud_["dbTechnology"].upper(),
            "ts" : util.convertDate2Str(util.convStr2DateViaParser(aud_["ts"]),"%Y-%m-%d %H:%M:%S:%f") if isinstance(aud_["ts"], str) else util.convertDate2Str(aud_["ts"],"%Y-%m-%d %H:%M:%S:%f")
        })
        #aud_.update({"ts" : util.})

    data = convertDict2TupleForHtml(rawHeadings, myAuditData, ["ENV"])
    myAuditData = {
        "data" : data,
        "headings" : headings
    }
    print(f"current session >>> {session}")
    return render_template("view_audit.html", title = "Audit Data", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, auditData = myAuditData)

@login_required
@app.route("/view_scan_proc_detail/<hostName>/<scanDate>/", methods=['GET','POST'])
def view_scan_proc_detail(hostName, scanDate):
    print(f"view_scan_proc_detail; session details >>> {session}")
    """ we need to work on this pending
    if not( session.get("userId") and session.get("userName")):
        print("scan_status; redirecting to login, missing details in session")
        session.clear()
        return redirect("login")
    """
    # retrieving data via rest API
    form = forms.scanStatusDetailForm()
    scanData = {"hostName" : hostName, "scanDate" : scanDate}
    scanSummaryData = {}

    # dynamic form selector --> https://www.youtube.com/watch?v=I2dJuNwlIH0
    print(f"scan date >>> {scanDate}")
    myScanEndDate = util.addDaysToDate(util.convStr2DateViaParser(scanDate),1)
    # we need to build scan start date because start date from form is being passed as 'Mon, 22 Mar 2021 00:00:00 GMT'
    myScanStartDate = util.addDaysToDate(myScanEndDate,-1) 

    print(request)

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    myMethod = "getAuditScanDetail"
    myArguments = {}

    myArguments.update({
        "hostName" : hostName.strip(),
        "scanStartDate" : util.convertDate2Str(myScanStartDate,'%m-%d-%Y') if not isinstance(myScanStartDate, str) else myScanStartDate,
        "scanEndDate" : util.convertDate2Str(myScanEndDate,'%m-%d-%Y') if not isinstance(myScanEndDate, str) else myScanEndDate
    })
       
    headings = ("Opco", "DataCenter", "Region","Env","Host","Scan Date","Status","Results")
    rawHeadings = ["opco","dcLocation","region","env","hostName","scanDate","status","results"]

    print(f"query args >>> {myArguments}")
    
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    # checking the result of rest api call
    if myResult["status"].upper() == "UNSUCCESS":
        flash(f"{myResult['message']}","danger")
        return render_template("view_scan_proc_detail.html", \
            title = "Audit Scan Detail", \
            user = "".join([session["userName"], " (", session["userId"], ")"]), \
            form = form, scan = [], scanDetailData = {}, summaryData = scanSummaryData)

    data = myResult["data"]
    if not data:
        return render_template("view_scan_proc_detail.html", \
            title = "Audit Scan Detail", \
            user = "".join([session["userName"], " (", session["userId"], ")"]), \
            form = form, scan = [], scanDetailData = {}, summaryData = scanSummaryData)

    summaryHeadings = ("DB Technology","Total Database", "Docker", "Non Docker","Status", "Started","Completed","Elapsed(Sec)", "Status Code")
    summaryRawHeadings = ["dbTechnology","totalDBs","docker","nonDokcer","status","startTS","completedTS","elapsed","statusCode"]

    dbHeadings = ("DB Technology", "DB ID", "Port", "Audit Files","Scan Status", "Transmit Status", "Audit Transmit Status","Comments")
    dbRawHeadings = ["dbTechnology","tenantId","port","totalAuditFiles","scanStatus","scanTransmitStatus","auditTransmitStatus","comments"]

    dbAudHeadings = ("DB Id", "Audit File", "Transmit Status", "Message")
    dbAudRawHeadings = ["tenantId","file","transmitStatus","message"]

    myAllScanFiles=[]
    for scan in data:
        print(f"scan details >>> {scan['details']}")
        for detail in scan["details"]:
            myAllScanFiles.append((util.getFileName(detail["hostScanFile"]),util.getFileName(detail["hostScanFile"])))
    
    print(f"all scan files built >> {myAllScanFiles}")
    form.hostScanFile.choices = myAllScanFiles
    print(f"form data choices>> {form.hostScanFile.choices}")

    if request.method == "POST":
        # post method, we have got file name selected by user
        myHostScanFile = form.hostScanFile.data
    else:
        for file in myAllScanFiles:
            myHostScanFile = file[0]
            break # we need 1st file
    
    print(f"host scan file >> {myHostScanFile}")

    # formating data
    mySummaryRawData = []
    myDBRawData = []
    myAuditRawData = []
    for scan in data:
        for detail in scan["details"]:
            if util.getFileName(detail["hostScanFile"]) != util.getFileName(myHostScanFile):
                continue
            for tenant in detail["tenants"]:
                myComments = ""
                if "comments" in tenant:
                    if "error" in tenant["comments"]:
                        myComments = tenant["comments"][tenant["comments"].find("error"):]
                    else:
                        myComments = tenant["comments"]
                myDBRawData.append({
                    "dbTechnology" : tenant["dbTechnology"], 
                    "tenantId" : tenant["tenantId"], 
                    "port" : tenant["port"], 
                    "totalAuditFiles" : tenant["totalAuditFiles"] if "totalAuditFiles" in tenant else 0,
                    "scanStatus" : tenant["scanStatus"],
                    "scanTransmitStatus" : tenant["scanTransmitStatus"] if "scanTransmitStatus" in tenant else "N/A",
                    "auditTransmitStatus" : tenant["audTransmitStatus"] if "audTransmitStatus" in tenant else "N/A",
                    "comments" : myComments,
                })
                if "auditFiles" in tenant:
                    for file in tenant["auditFiles"]:
                        myAuditRawData.append({
                            "tenantId" : tenant["tenantId"],
                            "file" : file["file"],
                            "transmitStatus" : file["transmitStatus"],
                            "message" : file["message"]
                        })
    # building main data
    #print(f"dbRawData >> {myDBRawData}")
    myDistDBTech = list(set([db["dbTechnology"] for db in myDBRawData]))
    #print(f"distinct db tech >> {myDistDBTech}")
    myTotalDBs = 0
    for dbtech in myDistDBTech:
        myTotalDBs = len([db["tenantId"] for db in myDBRawData if db["dbTechnology"] == dbtech])
        # building db tech specific summary
        for scan in data:
            for detail in scan["details"]:
                if util.getFileName(detail["hostScanFile"]) != util.getFileName(myHostScanFile):
                    continue
                print(f"dbtech >> {dbtech}, tenants summary >> {detail['tenantsSummary']}")
                myDBTechDocker = detail["tenantsSummary"][dbtech]["docker"]
                myDBTechNonDocker = detail["tenantsSummary"][dbtech]["nonDocker"]
                myDBTechStatus = "".join(["Success : ", str(detail["tenantsSummary"][dbtech]["Success"]), " UnSuccess : ", str(detail["tenantsSummary"][dbtech]["UnSuccess"])])
                myStartTS = detail["startTS"]
                myCompletedTS = detail["completedTS"]
                myElapsedTime = detail["response"]["elapsed"]
                myStatusCode = detail["response"]["statusCode"]

        mySummaryRawData.append({
            "opco" : data[0]["opco"],
            "region" : data[0]["region"],
            "dcLocation" : data[0]["dcLocation"],
            "env" : data[0]["env"],
            "dbTechnology" : dbtech,
            "totalDBs" : myTotalDBs, 
            "docker" : myDBTechDocker, 
            "nonDocker" : myDBTechNonDocker, 
            "status" : myDBTechStatus, 
            "startTS" : myStartTS,
            "completedTS" : myCompletedTS,
            "elapsed" : myElapsedTime,
            "statusCode" : myStatusCode
        })

    scanSummaryData = {
        "opco" : data[0]["opco"],
        "region" : data[0]["region"],
        "dcLocation" : data[0]["dcLocation"],
        "env" : data[0]["env"],
        "status" : data[0]["status"],
        "scanTS" : data[0]["scanTS"],        
        "startTS" : data[0]["startTS"],
        "completedTS" : data[0]["completedTS"],
        "totalDBs" : myTotalDBs
    }

    #print(f"raw summary data >> {mySummaryRawData}")
    mySummaryData = convertDict2TupleForHtml(summaryRawHeadings, mySummaryRawData, ["dbTechnology"])
    #print(f"final summary data >> {mySummaryData}")
    myDBData = convertDict2TupleForHtml(dbRawHeadings, myDBRawData, ["dbTechnology"])
    #print(f"db heading >> {dbHeadings}, db data >> {myDBData}")
    myAuditData = convertDict2TupleForHtml(dbAudRawHeadings, myAuditRawData, ["dbTechnology"])
    #print(f"aud data >> {myAuditData}")

    scanDetailData = {
        "summaryData" : mySummaryData, "summaryHeadings" : summaryHeadings,
        "dbData" : myDBData, "dbHeadings" : dbHeadings,
        "auditData" : myAuditData, "auditHeadings" : dbAudHeadings        
    }
    print(f"current session >>> {session}")
    print(f"scan detail >>> {scanDetailData}")
    return render_template("view_scan_proc_detail.html", \
        title = "Audit Scan Detail", \
        user = "".join([session["userName"], " (", session["userId"], ")"]), \
        form = form, scan = scanData, scanDetailData = scanDetailData, scanSummary = scanSummaryData)

@login_required
@app.route("/admin_roster/", methods=['GET','POST'])
#@cache.cached(timeout=50)
def admin_roster():
    """
    Admin roster view form
    """
    form = forms.AdminRosterViewForm()

    print(request)
    if request.method == "POST":
        print(f"{request.form}")
        myOpco = request.form["opco"]
        myDBTechnology = request.form["dbTechnology"]
        myStatus = request.form["status"]
    else:
        myOpco = "MARSH"
        myDBTechnology = "ALL"
        myStatus = "ALL"

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    myMethod = "getDBAdminRoster"
    myArguments = {}
    
    myArguments.update({
        "opco" : myOpco,
        "dbTechnology" : myDBTechnology,
        "status" : myStatus,
        "consolidated" : "no",
    })
       
    print(f"query args >>> {myArguments}")
    
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    if myResult["status"] == "UnSuccess":
        flash(f"An error occurred while retrieving admin roster data >>> {myResult['message']} !!!","danger")
        return render_template("admin_roster.html", title = "DB Admin Roster", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = [], data = [], form = form)

    #print(f"db result >> {myResult}")

    myDBAdminRosterData = myResult["data"]
    #print(f'raw admin data >>> {myDBAdminRosterData}')
    # formating data
    for admin in myDBAdminRosterData:
        # excluding mongo_admin account from roster
        admin.update({
            "opco" : admin["technology"]["opco"],
            "dbTechnology" : admin["technology"]["dbTechnology"].upper(),
            "dbLoginId" : ", ".join(admin["technology"]["dbLoginId"]),
            "onBoardDate" : admin["technology"]["onBoardDate"],
            "onBoardingDoc" : admin["technology"]["onBoardingDoc"],
            "offBoardingDate" : admin["technology"]["offBoardingDoc"] if "offBoardingDoc" in admin["technology"] else None,
            "offBoardingDoc" : admin["technology"]["offBoardingDoc"] if "offBoardingDoc" in admin["technology"] else None
        })

    myDBAdminRosterData = [admin for admin in myDBAdminRosterData if not admin["_id"].startswith("9")]
    headings = ("EmployeeID", "Name", "Location","Email","Opco","DBTechnology","LoginId","Status","Onboarded Date","onBoardingDoc","Offboarded Date","Offboarded Doc")
    rawHeadings = ["_id","name","location","email","opco","dbTechnology","dbLoginId","status","onBoardDate","onBoardingDoc","offBoardDate","offBoardingDoc"]
    data = convertDict2TupleForHtml(rawHeadings, myDBAdminRosterData)
    
    return render_template("admin_roster.html", title = "DB Admin Roster", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = headings, data = data, form = form)

@login_required
@app.route("/comp_tasks/", methods=['GET','POST'])
#@cache.cached(timeout=50)
def comp_tasks():
    """
    Compliance task view form
    """
    form = forms.CompTasksForm()
    myOpco = "MARSH"
    myError = None

    print(f"request >>> {request}")

    if request.method == 'GET':
        #form.tenant.choices == [("ALL","All Tenants")]:
        # we need to fill choices for tenants
        myOpco = form.opco.default
        myDBTechnology = form.dbTechnology.default
        myCompTask = form.compTask.default
        myTenant = form.tenant.default
        
        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
        myMethod = "getTenantsInventory"
        myArguments = {"opco" : myOpco, "region" : "ALL", "env" : "ALL", "dbTechnology" : "ALL"}
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        myTenantsData = myResult["data"]
        myTenants = []
        if myTenantsData:
            form.tenant.choices = [("ALL","All Databases")]
            for tenant in myTenantsData:
                form.tenant.choices.append((tenant["_id"], tenant["_id"]))
           
            #form.tenant.default = 1
            # retrieving the 1st tenant name's details
            #form.tenant.choices[0][0]

    if request.method == 'POST':
        print(f"{request.form}")
        myOpco = request.form["opco"]
        myDBTechnology = request.form["dbTechnology"]
        myCompTask = request.form["compTask"]
        if "tenant" in request.form: 
            myTenant =  request.form["tenant"]
        else:
            myTenant = "ALL"
    else:
        myTenant = form.opco.default

    # retrieving comp task history
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    myMethod = "getCompTaskDetail"

    myArguments = {
        "opco" : myOpco,
        "region" : "ALL",
        "env" : "ALL",
        "dbTechnology" : myDBTechnology,
        "compliance" : "ALL" if not myCompTask else myCompTask,
        "tenant" : myTenant,
        "status" : "ALL",
    }
       
    print(f"raw comp data; query args >>> {myArguments}")
    
    headings = ("TS","Opco","Comp Task ID","Frequency","Comp Task","Data","Result","Reference Doc","When","Status","Age","Opco", "Region","DB Technology", "Database","Env","Hosts","Tag")
    rawHeadings = ["ts","opco","_id","frequency","task","relevantData","result","supportingDoc","when","status","age","opco","region","dbTechnology","tenantName","env","hostsList","tag"]

    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    if myResult["status"] != "Success":
        flash(f"An error occurred while retrieving data >>> {myResult['message']} !!!","alert alert-danger alert-dismissible fade show")
        return render_template("comp_tasks.html", title = "Compliance Task history", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = headings, data = [], form = form)

    myCompTasksData = myResult["data"]
    print(f'raw comp data >>> {myCompTasksData}')

    # formating data
    for task in myCompTasksData:
        if "hosts" in task:
            myHostsList = ",".join([host["host"] for host in task["hosts"] ])
        elif "hostName" in task: 
            myHostsList = task["hostName"]
        else:
            myHostsList = "N/A"

        if "otherData" in task:
            if isinstance(task["otherData"], list):
                myRelevantData = ",".join(task["otherData"])
            else:
                myRelevantData = str(task["otherData"])
        else:
            myRelevantData = "N/A"

        #print("ts conv :", util.convStr2DateViaParser(task["ts"]), type(util.convStr2DateViaParser(task["ts"])))

        taskage = 0
        taskAge = util.diffBetweenDatesInDays(util.convStr2DateViaParser(task["ts"]).replace(tzinfo=None), util.getCurrentDate().replace(tzinfo=None))

        task.update({ 
            "hostsList" : myHostsList,
            #"task" : " ".join(task["task"].split(".")).capitalize(),
            "frequency" : task["frequency"].capitalize(),
            "age" : taskAge,
            "relevantData" : myRelevantData,
            "ts" : util.convertDate2Str(util.convStr2DateViaParser(task["ts"]),"%Y-%m-%d") if isinstance(task["ts"], str) else util.convertDate2Str(task["ts"],"%Y-%m-%d")
        })

    data = convertDict2TupleForHtml(rawHeadings, myCompTasksData,["env","dbTechnology"])
    
    return render_template("comp_tasks.html", title = "Compliance Task history", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = headings, data = data, form = form)

@login_required
@app.route("/product_version/", methods=['GET','POST'])
#@cache.cached(timeout=50)
def product_version():
    """
    Product version
    """
    form = forms.ProductVersionForm()

    print(f"compliance request >>> {request}")
  
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    myMethod = "getAllVerDetails"

    headings = ["DB Technology","Base Version","Released Date","Current Version","Released Date","EOS","EOL"]

    if request.method == "GET":
        myDBTechnology = form.dbTechnology.default
    else:
        myDBTechnology = form.dbTechnology.data

    myArguments = {"dbTechnology" : myDBTechnology}
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    if myResult["status"] == "UnSuccess":
        flash(f"An error occurred while retrieving database product version details >>> {myResult['message']} !!!","danger")
        return render_template("product_version.html", title = "Database Version Details", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = headings, data = [], form = form)


    rawHeadings = ["dbTechnology","baseVersion","baseVerReleasedDate","currentVersion","currVerReleasedDate","eosDate","eolDate"]
    data = convertDict2TupleForHtml(rawHeadings, myResult["data"],["dbTechnology"])
    return render_template("product_version.html", title = "Database Version Details", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = headings, data = data, form = form)

@login_required
@app.route("/view_product_version/<dbTechnology>/<version>", methods=['GET','POST'])
#@cache.cached(timeout=50)
def view_product_version(dbTechnology, version):
    """
    Product version
    """
    print(f"compliance request >>> {request}")
  
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    myMethod = "getAVerDetails"

    myArguments = {"dbTechnology" : dbTechnology.strip(), "version" : version.strip()}
    myVerResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    if request.method == "POST":
        return redirect(url_for('product_version'))

    if myVerResult["status"] == "UnSuccess":
        flash(f"An error occurred while retrieving database product version details >>> {myVerResult['message']} !!!","danger")
        return render_template("view_product_version.html", title = f"{dbTechnology.upper()} Database Version {version} Details ", user = "".join([session["userName"], " (", session["userId"], ")"]), data = [])

    versionHeadings = ["TS","Version","Released Date","Who","Comments"]
    if not myVerResult["data"]:
        flash(f"No {dbTechnology.upper()} database product version {version} details found !!!","danger")
        return render_template("view_product_version.html", title = f"{dbTechnology.upper()} Database Version {version} Details ", user = "".join([session["userName"], " (", session["userId"], ")"]), data = [])

    for ver in myVerResult["data"]["versions"]:
        ver.update({"ts" : util.convertDate2Str(util.convStr2DateViaParser(ver["ts"]),"%Y-%m-%d %H:%M:%S")})

    rawHeadings = ["ts","version","releasedDate","who","comments"]
    versionData = convertDict2TupleForHtml(rawHeadings, myVerResult["data"]["versions"],["dbTechnology"])
    
    return render_template("view_product_version.html", title = f"{dbTechnology.upper()} Database Version {version} Details ", user = "".join([session["userName"], " (", session["userId"], ")"]), data = {"header" : myVerResult["data"], "versionHeadings" : versionHeadings, "versionData" : versionData})

@login_required
@app.route("/new_product_version/", methods=['GET','POST'])
def new_product_version():
    """
    Product version
    """
    form = forms.NewProduvVersionForm()

    print(f"compliance request >>> {request}")
  
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    # retrieving all version details for this db technology
    myMethod = "getAllVerDetails"
    myArguments = {"dbTechnology" : form.dbTechnology.default.strip().lower()}

    myVerResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    if myVerResult["status"] == "Success" and "data" in myVerResult and myVerResult["data"]:
        print(f"new_product_version- got version data >> {myVerResult}")
        # we have data, will populate in form object
        form.baseVersion.choices = [(ver["baseVersion"], ver["baseVersion"]) for ver in myVerResult["data"]]
        form.baseVersion.choices.append(("new", "New Base Version"))
        form.baseVersion.default = form.baseVersion.choices[0][0]
        myBaseVersionData = [ver for ver in myVerResult["data"] if ver["baseVersion"] == form.baseVersion.default]
        if myBaseVersionData:
            print(f"new_product_version- got base version data >> {myBaseVersionData}")
            form.baseVerReleasedDate.data = myBaseVersionData[0]["baseVerReleasedDate"]
            form.currVersion.data = myBaseVersionData[0]["currentVersion"]
            form.currVerReleasedDate.data = myBaseVersionData[0]["currVerReleasedDate"]
            form.eolDate.data = myBaseVersionData[0]["eolDate"]
            form.eosDate.data = myBaseVersionData[0]["eosDate"]

    print(f"new_product_version- form data >> {form}")
    if request.method == "POST":
        myDBTechnology = form.dbTechnology.data
        myBaseVersion = form.baseVersion.data
        myCurrVersion = form.currVersion.data        
        myCurrVerReleasedDate = util.convStr2DateViaParser(form.currVersion.data)
        myNewVersion = form.newVersion.data
        myNewVerReleasedDate = util.convStr2DateViaParser(form.newVerReleasedDate.data)

        #if myBaseVersion == "new":

        if myNewVersion:
            # adding new version was requested
            myMethod = "addNewDBVersion"
            myArguments = {"dbTechnology" : myDBTechnology, "version" : myNewVersion, "releasedDate" : util.convertDate2Str(myNewVerReleasedDate, "%Y-%m-%d"), "userId" : session["userId"]}
            myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
            if myResult["status"] == "UnSuccess":
                flash(f"An error occurred while adding a new {myDBTechnology} database version {myNewVersion} >>> {myResult['message']} !!!","danger")

        # checking if eos/eol update was requested
        if form.eosEolCheck.data == True:
            # eos eol update was requested
            if not (form.eosDate.data or form.eolDate.data):
                flash("Missing mandatory field value EOS Date/EOL Date !!!")
                return render_template("new_product_version.html", title = "New Database Version", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            myMethod = "updDBVersionEOL"
            myArguments = {"dbTechnology" : myDBTechnology, "version" : myBaseVersion, "eolDate" : util.convertDate2Str(form.eolDate.data, "%Y-%m-%d"), "eosDate" : util.convertDate2Str(form.eosDate.data, "%Y-%m-%d"), "userId" : session["userId"]}

            myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

            if myResult["status"] == "UnSuccess":
                flash(f"An error occurred while saving EOL/EOS for {myDBTechnology} database version {myBaseVersion} >>> {myResult['message']} !!!","danger")
            else:
                flash(f"EOL/EOS update for {myDBTechnology} database version {myBaseVersion} was successfull !!","success")
        else:
            flash(f"New {myDBTechnology} database version {myNewVersion} addedd successfull !!","success")

        return redirect (url_for("product_version"))

        #else:

        """
        print(f'new ver released date type {type(myNewVerReleasedDate)}')
        print(f"new_product_version.post >> currVersion : '{myCurrVersion}'")
        print(f"new_product_version.post >> currVerReleasedDate : '{myCurrVerReleasedDate}'")
        print(f"new_product_version.post >> CurrVerReleasedDate (remove time): '{util.removeTimeFromDate(myCurrVerReleasedDate)}'")
        print(f"new_product_version.post >> newVersion : '{myNewVersion}'")
        print(f"new_product_version.post >> newVerReleasedDate : '{myNewVerReleasedDate}'")
        print(f"new_product_version.post >> newVerReleasedDate (remove time): '{util.removeTimeFromDate(myNewVerReleasedDate)}'")

        print(f"new_product_version.post >> eosEolCheck : '{form.eosEolCheck.data}'")
        print(f"new_product_version.post >> eosDate : '{form.eosDate.data}'")
        print(f"new_product_version.post >> eolDate : '{form.eolDate.data}'")
        if myNewVersion == myCurrVersion:
            flash(f"New version {myNewVersion} can not be same as current version {myCurrVersion} !!!")

        if ".".join(myNewVersion.split(".")[:2]) != myBaseVersion:
            flash(f"New version {myNewVersion} must belong to base version {form.currVersion.data} !!!")

        if form.newVersion.data.split(".")[-1] <= form.currVersion.data.split(".")[-1]:
            flash(f"New version {form.newVersion.data} can not be same or lower than current version {form.currVersion.data} !!!")

        if util.removeTimeFromDate(myNewVerReleasedDate) <= util.removeTimeFromDate(myCurrVerReleasedDate):
            flash(f"New version released date {myNewVerReleasedDate} can not be earlier than current version released date {myCurrVerReleasedDate} !!!")

        if form.eosEolCheck.data == True:
            # validating eol eos date
            if util.removeTimeFromDate(util.convStr2DateViaParser(form.eolDate.data)) <= util.removeTimeFromDate(util.convStr2DateViaParser(form.currVerReleasedDate.data)):
                flash(f"EOL date {form.eolDate.data} can not be earlier than current version released date {form.currVerReleasedDate.data} !!!")

            if util.removeTimeFromDate(util.convStr2DateViaParser(form.eolDate.data)) <= removeTimeFromDate(util.convStr2DateViaParser(form.currVerReleasedDate.data)):
                flash(f"EOS date {form.eolDate.data} can not be earlier than current version released date {form.currVerReleasedDate.data} !!!")
        # retrieving form data                
        myDBTechnology = form.dbTechnology.data
        newVersion = form.newVersion.data
        newVerReleasedDate = form.newVerReleasedDate.data

        myArguments = {"dbTechnology" : myDBTechnology}
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while retrieving database product version details >>> {myResult['message']} !!!","danger")

        return redirect(url_for("product_version"))
        """

    return render_template("new_product_version.html", title = "New Database Version", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

@login_required
@app.route("/new_db_admin/", methods=['GET','POST'])
def new_db_admin():
    """
    Product version
    """
    form = forms.NewDBAdminForm()

    print(f"new db admin request >>> {request}")
  
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    
    if request.method == "POST" : 
        #print(f"testing - post request (new_db_admin) >>> {request.form}")
        if request.form['action'].lower() == "search":
            # request is post and action is search
            # 1. check if this user exists in ldap

            myMethod = "getLdapUserdetails"
            myArguments = {"userSearchAttr" : "employeeId","userSearchAttrVal" : form.employeeId.data.strip(),"returnValue" : "networkId,name,location,email,contact#,createdOn,dn,cn,memberOf,memberOfDn"}

            myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
            if myResult["status"] == "UnSuccess":
                flash(f"An error occurred while retrieving user details from AD >>> {myResult['message']} !!!","danger")
                return render_template("new_db_admin.html", title = "Onboard New DB Admin", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            if not myResult["data"]:
                flash(f"Invalid employeed id {form.employeeId.data} !!!","danger")
                return render_template("new_db_admin.html", title = "Onboard New DB Admin", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            myLdapUserDetails = myResult["data"]

            # 2. check if this user is already not onboarded
            myMethod = "getDBAdminDetails"
            myArguments = {"employeeId" : form.employeeId.data.strip()}

            myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
            if myResult["status"] == "UnSuccess":
                flash(f"An error occurred while validating existence of admin {form.employeeId.data} in roster >>> {myResult['message']} !!!","danger")
                return render_template("new_db_admin.html", title = "Onboard New DB Admin", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
            if myResult["data"]:
                flash(f"Employee id {form.employeeId.data} is already onboarded !!!","danger")
                return render_template("new_db_admin.html", title = "Onboard New DB Admin", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            # validation passed returning search data 
            form.name.data = myLdapUserDetails["name"]
            form.networkId.data = myLdapUserDetails["networkId"]            
            form.location.data = myLdapUserDetails["location"]
            form.contact.data = myLdapUserDetails["contact#"]
            form.memberOf.data = myLdapUserDetails["memberOf"]
            form.dn.data = myLdapUserDetails["dn"]
            form.validEmployee.data = "yes"

            return render_template("new_db_admin.html", title = "Onboard New DB Admin", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)
        elif request.form['action'].lower() == "save":
            myEmployeeId = form.employeeId.data
            myOnboardingDoc = form.onboardingDoc.data
            myOnboardingDate = form.onboardingDate.data
            myMongoLoginIds = form.mongoDbLoginIds.data
            myOpco = form.opco.data
            
            myMethod = "onBoardDBAdmin"
            myArguments = {"opco" : myOpco, "employeeId" : myEmployeeId, "supportingDoc" : myOnBoardingDoc, "onBoardDate" : myOnboardingDate, "dbLoginId" : myMongoLoginIds, "dbTechnology" : "mongo"}
 
            myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
 
            if myResult["status"] == "UnSuccess":
                flash(f"An error occured while onboarding new admin id {myEmployeeId} !!!","danger")
                return render_template("new_db_admin.html", title = "Onboard New DB Admin", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

            if myResult["status"] == "Success":
                flash(f"Employee {myEmployeeId} is onboarded successfully !!!","success")
                return redirect("url_for('admin_roster'")
        """
        getLdapUserdetails("securityToken","userSearchAttr","userSearchAttrVal","returnValue",userId")
        getLdapUserdetails("employeeId", myKwArgs["employeeId"],"networkId,name,location,email,contact#,createdOn,dn,cn,memberOf,memberOfDn")
        getDBAdminDetails("securityToken","employeeId","userId")        
        """

    return render_template("new_db_admin.html", title = "Onboard New DB Admin", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

@login_required
@app.route("/compliances/", methods=['GET','POST'])
#@cache.cached(timeout=50)
def compliances():
    """
    Compliance
    """
    form = forms.ComplianceViewForm()

    print(f"compliance request >>> {request}")
  
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    myMethod = "getLatestTenantCompliance"

    if request.method == "GET":
        myOpco = form.opco.default
        myDBTechnology = form.dbTechnology.default
        myCompStatus = form.compStatus.default
    elif request.method == 'POST':
        print(f"{request.form}")
        myOpco = form.opco.data
        myDBTechnology = form.dbTechnology.data
        myCompStatus = form.compStatus.data

    myArguments = {"opco" : myOpco, "tenantName" : "ALL", "dbTechnology" : myDBTechnology, "compStatus" : myCompStatus}

    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    if myResult["status"] == "UnSuccess":
        flash(f"An error occurred while retrieving latest tenant compliances >>> {myResult['message']} !!!","danger")
        return render_template("compliances.html", title = "Database Compliances", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = [], data = [], form = form)

    if not myResult["data"]:
        return render_template("compliances.html", title = "Database Compliances", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = [], data = [], form = form)

    print(f"compliance result >> {myResult}")
    #myTenantsCompData = myResult["data"]
    if myResult["data"]:
        myAllTenantsRaw = list(set([tenant["tenantName"] for tenant in myResult["data"]]))
        for tenant in myAllTenantsRaw:
            form.tenant.choices.append((tenant, tenant))

    for tenant in myResult["data"]:
        for comp in tenant["compliances"]:
            tenant.update({comp["comp"] : comp["status"]})
        tenant.update({
            "displayInompTasks" : ("".join([str(len(tenant["complianceTasks"])), " - ", " | ".join(tenant["complianceTasks"])])) if len(tenant["complianceTasks"]) > 0 else "0",
            "displayNonCompTasks" : ("".join([str(len(tenant["nonComplianceTasks"])), " - ", " | ".join(tenant["nonComplianceTasks"])]) if len(tenant["nonComplianceTasks"]) > 0 else "0") if len(tenant["nonComplianceTasks"]) > 0 else "0",
            "displayAtRiskCompTasks" : ("".join([str(len(tenant["atRiskComplianceTasks"])), " - ", " | ".join(tenant["atRiskComplianceTasks"])]) if len(tenant["atRiskComplianceTasks"]) > 0 else "0") if len(tenant["atRiskComplianceTasks"]) > 0 else "0",
            "runDate" : util.convertDate2Str(util.convStr2DateViaParser(tenant["compRunDate"]),"%Y-%m-%d"),
            "score" : int(round((len(tenant["complianceTasks"]) / (len(tenant["complianceTasks"]) + len(tenant["nonComplianceTasks"]) + len(tenant["atRiskComplianceTasks"]))) * 100, 0))
        })

    headings = ["Opco","Env","Run Date","Database","DB Technology","Comp Score %","Audit Enable","Audit Filter","DB Version","DB Users","User Pass Change","Restore Test","Compliant","At-Risk","Non-Compliancs"]
    rawHeadings  = ["opco","env","runDate","tenantName","dbTechnology","complianceScore","aud.enabled","aud.filter","db.version","db.local.users","annual.dbuser.pass.change","annual.restore.test","displayInompTasks","displayAtRiskCompTasks","displayNonCompTasks"]
    data = convertDict2TupleForHtml(rawHeadings, myResult["data"],["env","dbTechnology"])
    print(f"comp data for html table >>> {data}")
    return render_template("compliances.html", title = "Database Compliances", user = "".join([session["userName"], " (", session["userId"], ")"]), headings = headings, data = data, form = form)

@login_required
@app.route("/view_tenant_compliance/<tenantName>/<runDate>/", methods=['GET','POST'])
#@cache.cached(timeout=50)
def view_tenant_compliance(tenantName, runDate):
    form = forms.ComplianceViewForm()
    print(f"view_tenant_compliance; >>> {session}")
    """ we need to work on this pending
    if not( session.get("userId") and session.get("userName")):
        print("scan_status; redirecting to login, missing details in session")
        session.clear()
        return redirect("login")
    """
    # retrieving data via rest API
    print(f'view_tenant_compliance request >>> {request}')

    if request.method == "POST":
        return redirect(url_for('compliances'))

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    myMethod = "getATenantCompliance"

    myArguments = {"tenantName" : tenantName, "runDate" : runDate}

    print(f"view_tenant_compliance query args >>> {myArguments}")
    
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    if request.method == "POST":
        return redirect("url_for('compliances'")

    #print(f"result >>> {myResult}")
    # checking the result of rest api call
    if myResult["status"].upper() == "UNSUCCESS":
        flash(f"{myResult['message']}","danger")
        return render_template("view_tenant_compliance.html", \
            title = f"Database Compliance Detail - {tenantName.split('.')[4]}", \
            user = "".join([session["userName"], " (", session["userId"], ")"]), \
            comp = {}, form = form)

    #compData = myResult["data"]
    if not myResult["data"]:
        flash(f"Data is missing !!","warning")
        return render_template("view_tenant_compliance.html", \
            title = f"Database Compliance Detail - {tenantName.split('.')[4]}", \
            user = "".join([session["userName"], " (", session["userId"], ")"]), \
            comp = {}, form = form)
    """
    myCompHeading = {
        "tenantName" : myResult["data"]["tenantName"],
        "opco" : myResult["data"]["opco"],
        "dbTechnology" : myResult["data"]["dbTechnology"],
        "env" : myResult["data"]["env"],
        "inCompCount" : myResult["data"]["totalComplianceCount"],
        "atRiskCompCount" : myResult["data"]["totalAtRiskCount"],
        ""
    }
    """
    myTenantCompliances = []

    # building tenant compliances
    for comp in myResult["data"]["compliances"]:
        # checking if we this comp is extended to multiple host of this database(rs member in Mongo)
        if "members" in comp:
            for member in comp["members"]:
                myTenantCompliances.append({
                    "comp" : comp["comp"],
                    "desc" : " ".join([item.capitalize() for item in comp["comp"].split(".")]),
                    "tenant" : member["tenantId"],
                    "relevance" : "MEMBER",
                    "status" : member["status"],
                    "result" : member["result"],
                })
        else:
            myTenantCompliances.append({
                "comp" : comp["comp"],
                "desc" : " ".join([item.capitalize() for item in comp["comp"].split(".")]),
                "tenant" : myResult["data"]["tenantName"],
                "relevance" : "DATABASE",
                "status" : comp["status"],
                "result" : comp["result"],
            })
    myCompDetailHeadings = ["DB Id","Relevance", "Compliance","Description","Status","Result"]
    rawHeadings = ["tenant","relevance","comp","desc","status","result"]
    myTenantCompDetailData = convertDict2TupleForHtml(rawHeadings, myTenantCompliances,[])
    myResult["data"].pop("compliances", None)

    print(f"current session >>> {session}")

    return render_template("view_tenant_compliance.html", \
        title = f"Database Compliance Detail - {tenantName.split('.')[4]}", \
        user = "".join([session["userName"], " (", session["userId"], ")"]), \
        comp = {"header" : myResult["data"], "compTasksData" : myTenantCompDetailData, "compTasksHeading" : myCompDetailHeadings}, form = form)

@login_required
@app.route("/view_comp_task/<compTaskId>/", methods=['GET','POST'])
#@cache.cached(timeout=50)
def view_comp_task(compTaskId):
    print(f"view_comp_task; compTaskId details >>> {session}")
    """ we need to work on this pending
    if not( session.get("userId") and session.get("userName")):
        print("scan_status; redirecting to login, missing details in session")
        session.clear()
        return redirect("login")
    """
    # retrieving data via rest API
    print(request)

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    myMethod = "getACompTaskDetail"
    myArguments = {}

    myArguments.update({"compTaskId" : compTaskId})
       
    historyHeadings = ("TS", "Who", "Comments")
    historyRawHeadings = ["ts","who","comments"]

    print(f"query args >>> {myArguments}")
    
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    #print(f"result >>> {myResult}")
    # checking the result of rest api call
    if myResult["status"].upper() == "UNSUCCESS":
        flash(f"{myResult['message']}","danger")
        return render_template("view_comp_task.html", \
            title = f"Compliance Task Detail - {compTaskId}", \
            user = "".join([session["userName"], " (", session["userId"], ")"]), \
            comp = {})

    compData = myResult["data"]
    if not compData:
        flash(f"No data available !!","warning")
        return render_template("view_comp_task.html", \
            title = f"Compliance Task Detail - {compTaskId}", \
            user = "".join([session["userName"], " (", session["userId"], ")"]), \
            comp = {})

    myHistData = convertDict2TupleForHtml(historyRawHeadings, compData["history"], ["who"])

    compData.update({
        "historyHeadings" : historyHeadings, 
        "historyData" : myHistData,
        "task" : " ".join(compData["task"].split(".")).capitalize()
    })

    print(f"current session >>> {session}")

    return render_template("view_comp_task.html", \
        title = f"Compliance Task Detail - {compTaskId}", \
        user = "".join([session["userName"], " (", session["userId"], ")"]), \
        comp = compData)

@login_required
@app.route("/bulk_update_comp_tasks/", methods=['GET','POST'])
def bulk_update_comp_tasks():
    form = forms.BulkUpdateCompTaskForm()
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    
    if request.method == "GET":
        # pulling all pending comp tasks
        myMethod = "getCompTaskDetail"
        myArguments = {
            "opco" : "ALL",
            "region" : "ALL",
            "env" : "ALL",
            "dbTechnology" : "ALL",
            "compliance" : "ALL",
            "tenant" : "ALL",
            "status" : "Pending"
        }

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        if myResult["status"] == "UnSuccess":
            flash(f"An error {myResult['message']} occurred while retrieving pending compliances !!!", "danger")
            return render_template("bulk_update_comp_tasks.html", \
                title = f"Bulk Updfate Compliance Tasks", \
                user = "".join([session["userName"], " (", session["userId"], ")"]), \
                comp = {}, form = form)

        if myResult["data"]:
            myOpco = []
            myRegion = []
            myEnv = []
            myDBTechnology = []
            myCompliance = []
            myTasks = []
            for comp in myResult["data"]:
                myOpco.append(comp["opco"])
                myRegion.append(comp["region"])
                myEnv.append(comp["env"])
                myDBTechnology.append(comp["dbTechnology"])
                myCompliance.append(comp["task"])
                myTasks.append({"id" : comp["_id"], "ts" : util.convStr2DateViaParser(comp["ts"]), "opco" : comp["opco"], "env" : comp["env"], "tenant" : comp["tenantId"] if "tenantId" in comp else comp["tenantName"], "otherData" : comp["otherData"], "tag" : comp["tag"]})

            myOpco = list(set(myOpco))
            myRegion = list(set(myRegion))
            myEnv = list(set(myEnv))
            myDBTechnology = list(set(myDBTechnology))
            myCompliance = list(set(myCompliance))

            # populating select field
            [form.opco.choices.append((opco, opco)) for opco in myOpco]
            [form.region.choices.append((region, region)) for region in myRegion]
            [form.env.choices.append((env, env.upper())) for env in myEnv]
            [form.dbTechnology.choices.append((dbTechnology, dbTechnology.upper())) for dbTechnology in myDBTechnology]
            [form.compliance.choices.append((comp, comp)) for comp in myCompliance]

            # filling comp task based on above default value
            form.compTasks.choices = [(
                comp["id"], 
                "".join([
                    str(comp["ts"]), "   :   ", comp["env"].upper(), "   :   ", comp["opco"].upper(), " : ", comp["tenant"], "   :   ", comp["otherData"], "   :   ", comp["tag"]
                ])
            ) for comp in myTasks]

        return render_template("bulk_update_comp_tasks.html", \
            title = f"Bulk Updfate Compliance Tasks", \
            user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)
    else:
        print(f"post >>> {request.args}")
        """
        myCompTaskIds = request.form.getlist("compTasks")
        mySupportingDoc = request.form.get('supportingDoc')
        myWhen = request.form.get("when")
        myTag = request.form.get('tag')
        myComments = request.form.get('comments')
        """
        print("tasks",request.form.getlist("compTasks"))
        print("doc",request.form.get("supportingDoc"))
        print("when",request.form.get("when"))
        print("tag",request.form.get("tag"))
        print("comments",request.form.get("comments"))

        myMethod = "updCompTasks"
        myArguments = {
            "compTaskIds" : request.form.getlist("compTasks"),
            "supportingDoc" : request.form.get("supportingDoc"),
            "when" : request.form.get("when"),
            "tag" : request.form.get("tag"),
            "comments" : request.form.get("comments"),
            "userId" : session["userId"]
        }

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while updating comp task data >>> {myResult['message']}","danger")

            # building pending task lists
            myMethod = "getCompTaskDetail"
            myArguments = {
                "opco" : "ALL",
                "region" : "ALL",
                "env" : "ALL",
                "dbTechnology" : "ALL",
                "compliance" : "ALL",
                "tenant" : "ALL",
                "status" : "Pending"
            }
            myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
            if myResult["status"] == "UnSuccess":
                flash(f"An error {myResult['message']} occurred while retrieving pending compliances !!!", "danger")
                return render_template("bulk_update_comp_tasks.html", \
                    title = f"Bulk Update Compliance Tasks", \
                    user = "".join([session["userName"], " (", session["userId"], ")"]), \
                    comp = {}, form = form)

            if myResult["data"]:
                myOpco = []
                myRegion = []
                myEnv = []
                myDBTechnology = []
                myCompliance = []
                myTasks = []

                for comp in myResult["data"]:
                    myOpco.append(comp["opco"])
                    myRegion.append(comp["region"])
                    myEnv.append(comp["env"])
                    myDBTechnology.append(comp["dbTechnology"])
                    myCompliance.append(comp["task"])
                    myTasks.append({"id" : comp["_id"], "ts" : util.convStr2DateViaParser(comp["ts"]), "env" : comp["env"], "tenant" : comp["tenantId"] if "tenantId" in comp else comp["tenantName"], "otherData" : comp["otherData"], "tag" : comp["tag"]})

                myOpco = list(set(myOpco))
                myRegion = list(set(myRegion))
                myEnv = list(set(myEnv))
                myDBTechnology = list(set(myDBTechnology))
                myCompliance = list(set(myCompliance))

                # populating select field
                [form.opco.choices.append((opco, opco)) for opco in myOpco]
                [form.region.choices.append((region, region)) for region in myRegion]
                [form.env.choices.append((env, env.upper())) for env in myEnv]
                [form.dbTechnology.choices.append((dbTechnology, dbTechnology.upper())) for dbTechnology in myDBTechnology]
                [form.compliance.choices.append((comp, comp)) for comp in myCompliance]
            
                form.compTasks.choices = [(comp["id"], "".join([str(comp["ts"]), "   :   ", comp["env"].upper(), "   :   ", comp["tenant"], "   :   ", comp["otherData"], "   :   ", comp["tag"] ])) for comp in myTasks]

            return render_template("bulk_update_comp_tasks.html", \
                title = f"Bulk Update Compliance Tasks", \
                user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)
        else:
            flash(f"Comp task data updated successfully !!","success")
            return redirect(url_for('comp_tasks'))

@login_required
@app.route("/editCompTask/<compTaskId>/", methods=['GET','POST'])
#@cache.cached(timeout=50)
def editCompTask(compTaskId):
    form = forms.EditCompTask()
    print(f"editCompTask; compTaskId details >>> {session}")
    """ we need to work on this pending
    if not( session.get("userId") and session.get("userName")):
        print("scan_status; redirecting to login, missing details in session")
        session.clear()
        return redirect("login")
    """
    # retrieving data via rest API
    print(request)

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    myMethod = "getACompTaskDetail"
    myArguments = {}

    if request.method == "GET":
        myArguments.update({"compTaskId" : compTaskId})
           
        historyHeadings = ("TS", "Who", "Comments")
        historyRawHeadings = ["ts","who","comments"]

        print(f"query args >>> {myArguments}")
        
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        #print(f"result >>> {myResult}")
        # checking the result of rest api call
        if myResult["status"].upper() == "UNSUCCESS":
            flash(f"An error occurred validating comp task id {compTaskId} >>> {myResult['message']}","danger")
            return render_template("edit_comp_task.html", \
                title = f"Compliance Task Detail - {compTaskId}", \
                user = "".join([session["userName"], " (", session["userId"], ")"]), \
                comp = {}, form = form)

        compData = myResult["data"]
        if not compData:
            flash(f"No data available !!","warning")
            return render_template("edit_comp_task.html", \
                title = f"Compliance Task Detail - {compTaskId}", \
                user = "".join([session["userName"], " (", session["userId"], ")"]), \
                comp = {}, form = form)

        myHistData = convertDict2TupleForHtml(historyRawHeadings, compData["history"], ["who"])

        compData.update({
            "historyHeadings" : historyHeadings, 
            "historyData" : myHistData,
            "task" : " ".join(compData["task"].split(".")).capitalize()
        })
        """
        print(form.supportingDoc,dir(form.supportingDoc))
        print(form.when,dir(form.when))
        print(form.comments,dir(form.comments))
        """
        if compData["supportingDoc"]:
            form.supportingDoc.data = compData["supportingDoc"]
        if compData["when"]:
            form.when.data = util.convStr2DateViaParser(compData["when"])
        if compData["tag"]:    
            form.tag.data = compData["tag"]

        """
        print(form.supportingDoc,dir(form.supportingDoc))
        print(form.when,dir(form.when))
        print(form.comments,dir(form.comments))
        print(f"current session >>> {session}")
        """
        return render_template("edit_comp_task.html", \
            title = f"Compliance Task Detail - {compTaskId}", \
            user = "".join([session["userName"], " (", session["userId"], ")"]), \
            comp = compData, form=form)
    else:
        # this is post, user is requesting to update the changes
        print(f"request : {request.args}")
        myMethod = "updCompTasks"
        myArguments = {
            "userId" : session["userId"],
            "compTaskIds" : [compTaskId],
            "supportingDoc" : form.supportingDoc.data,
            "when" : form.when.data if isinstance(form.when.data, str) else util.convertDate2Str(form.when.data,"%m-%d-%Y"),
            "tag" : form.tag.data,
            "comments" : form.comments.data
        }
        print(f"apiKey : {mySrvcAcctAPIKey}, userId : {mySrvcAccount}, method : {myMethod}, args: {myArguments}")
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while updating comp task data >>> {myResult['message']}","danger")
            form.process()
            return render_template("edit_comp_task.html", \
                title = f"Compliance Task Detail - {compTaskId}", \
                user = "".join([session["userName"], " (", session["userId"], ")"]), \
                comp = compData, form=form)
        else:
            flash(f"Comp task data updated successfully !!","success")
            return redirect(url_for('comp_tasks'))

@login_required
@app.route("/new_comp_tasks/", methods=['GET','POST'])
def new_comp_tasks():
    """
    Admin roster view form
    """
    form = forms.NewCompTaskForm()
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    print(f"request >>> {request}")
    if request.method == "POST":
        print(f"post request >>> {request.form}")
        myTaskType = request.form.get("compTask")
        if myTaskType == "annual.compliance.task":
            myOpco = request.form.get("opco")
            myEnv = request.form.get("env")
            myDBTechnology = request.form.get("dbTechnology")
            myCompTask = request.form.get("annualCompTask")
            myTenants = request.form.getlist("tenant")
            mySupportingDoc = request.form.get("supportingDoc")
            myWhen = request.form.get("when")
            myResult = request.form.get("result")
            myOtherData = request.form.get("otherData")
            myTag = request.form.get("tag")
            myComments = request.form.get("comments")

            print(f"comp task type: {myTaskType}, comp task : {myCompTask}, opco : {myOpco}, env : {myEnv}, db technology : {myDBTechnology}, tenants : {myTenants}, when : {myWhen}, other data: {myOtherData}, tag :{myTag}")
            print(f"result: {myResult}, comments : {myComments}, supportingDoc : {mySupportingDoc}")

            myMethod = "addCompTaskDetail"
            if myCompTask == "annual.dbuser.pass.change":
                myResult = "Success"

            myArguments = {
                "task" : myCompTask, 
                "tenantNames" : myTenants, 
                "supportingDoc" : mySupportingDoc, 
                "when" : myWhen, 
                "result" : myResult, 
                "otherData" : myOtherData,
                "tag" : myTag, 
                "comments" : myComments,
                "userId" : session["userId"]
            }

            myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

            print(f"result >> {myResult}")
            if myResult["status"] == "UnSuccess":
                flash(f"An error occurred while saving compliance data >>> {myResult['message']} !!!","danger")
            else:
                flash(f"Compliance task created successfull !! >>> {myResult['message']} !!!","success")

            """
            myMethod = "getAllTenantsName"
            myArguments = {"opco" : myOpco, "region" : "ALL", "env" : myEnv, "dbTechnology" : myDBTechnology, "status" : "Active"}
            myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
            myAllTenants = []
            myTenantsNameRawData = myResult["data"]

            for tenant in myTenantsNameRawData:
                form.tenant.choices.append((tenant["_id"], tenant["_id"]))

            if myTenantsNameRawData:
                # assigning back value which we got duirng post because we are processing form data
                form.tenant.default = [myTenantsNameRawData[0]["_id"]]
                form.env.default = myEnv
                form.dbTechnologydefault = myDBTechnology
                form.supportingDocdefault = mySupportingDoc
                form.annualCompTaskdefault = myCompTask
                form.whendefault = util.convStr2DateViaParser(myWhen)
                form.resultdefault = myResult
                form.dbUsers.default = myOtherData
                form.comments.default = myComments 

                # processing default selected
                form.process()
            
            """
            myMethod = "getAllTenantsName"
            myArguments = {"opco" : myOpco, "region" : "ALL", "env" : myEnv, "dbTechnology" : myDBTechnology, "status" : "Active"}
            myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
            myAllTenants = []
            myTenantsNameRawData = myResult["data"]

            for tenant in myTenantsNameRawData:
                form.tenant.choices.append((tenant["_id"], tenant["_id"]))
            if myTenantsNameRawData:
                form.tenant.default = [myTenantsNameRawData[0]["_id"]]
                # processing default selected
                form.process()

            return render_template("new_comp_tasks.html", title = "New Compliance Task", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

    else:
        myOpco = form.opco.default
        myEnv = form.env.default
        myDBTechnology = form.dbTechnology.default
        form.supportingDoc.default = ""
        form.otherData.default = ""
        # retrieving database name for a given db technologies
        myMethod = "getAllTenantsName"
        myArguments = {"opco" : myOpco, "region" : "ALL", "env" : myEnv, "dbTechnology" : myDBTechnology, "status" : "Active"}
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        myAllTenants = []
        myTenantsNameRawData = myResult["data"]

        for tenant in myTenantsNameRawData:
            form.tenant.choices.append((tenant["_id"], tenant["_id"]))
        if myTenantsNameRawData:
            form.tenant.default = [myTenantsNameRawData[0]["_id"]]
            # processing default selected
            form.process()
        #print(form.tenant.default,form.tenant, dir(form.tenant))
    return render_template("new_comp_tasks.html", title = "New Compliance Task", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

@login_required
@app.route("/admin_tasks/", methods=['GET','POST'])
#@cache.cached(timeout=50)
def admin_tasks():
    """
    New 
    """
    form = forms.dbAdminTaskForm()
    result = []
    print(f"request >>> {request}")
    if request.method == "POST":
        myDBTechnology = request.form.dbTechnology.data
    else:
        myDBTechnology = form.dbTechnology.default
        # retrieving database name for a given db technologies
        myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
        mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
        mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
        myMethod = "getAllTenantsName"
        myArguments = {"opco" : "ALL", "region" : "ALL", "env" : "ALL", "dbTechnology" : myDBTechnology, "status" : "Active"}
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        myAllTenants = []
        myTenantsNameRawData = myResult["data"]

        for tenant in myTenantsNameRawData:
            form.tenant.choices.append((tenant["_id"], tenant["_id"]))

    return render_template("dbadmin_task.html", title = "Administration Tasks", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, result = result)

@login_required
@app.route("/new_db_request/", methods=['GET','POST'])
def new_db_request():
    """
    Create new database change request
    """
    form = forms.NewDBRequestForm()
    print(f'tenant name form >>> {form.tenantName}')
    print(f'dbTechnology form >>> {form.dbTechnology}')
    print(f'dbTechnology default >>> {form.dbTechnology.default}')
    print(request)

    myDBTechnology = form.dbTechnology.default
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    myMethod = "getTenantsInventory"
    myArguments = {"opco" : "ALL", "region" : "ALL", "env" : "ALL", "dbTechnology" : myDBTechnology}
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    myTenantsData = myResult["data"]
    myTenants = []
    if myTenantsData:
        for tenant in myTenantsData:
            if tenant["status"] == "Active":
                #myTenants.append("".join([tenant["opco"], ".", tenant["dcLocation"], ".", tenant["dbCluster"] ]))
                myTenants.append(tenant["_id"])

        # populaing tenant name select field
        form.tenantName.choices = [(tenant, tenant.upper()) for tenant in myTenants]
        form.tenantName.default = 1
        # retrieving the 1st tenant name's details 
        myDefaultTenantName = form.tenantName.choices[0][0]
        myMethod = "getATenantInfo"
        myArguments = {"tenantName" : myDefaultTenantName}
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        myTenantDetail = myResult["data"]
        #print(f"db details >>> {myTenantDetail}")
        form.env = myTenantDetail["env"]
        form.dbCluster = myTenantDetail["dbCluster"]
        form.version = myTenantDetail["version"]
    if request.method == "POST":
        print("in post request.form >> {request.form}")
        # create a new database change call here

    return render_template("new_dbrequest_for_audit.html", title = "New DB Change Request", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form)

@login_required
@app.route("/view_db_admin/<employeeId>", methods=['GET','POST'])
#@cache.cached(timeout=50)
def view_db_admin(employeeId):
    form = forms.ViewDBAdminForm()
    myOpco = "MARSH"
    myError = None
    #print(f"jsonify request >>> {jsonify(request)}")
    print(f"request >> {request}")

    myEmployeeId = employeeId.strip()

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    if request.method == "POST":
        return redirect(url_for("admin_roster"))

    myMethod = "getDBAdminDetails"
    myArguments ={"employeeId" : myEmployeeId}
       
    print(f"query args >>> {myArguments}")
    
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    
    if myResult["status"] == "UnSuccess":
        flash(f"An error occurred while retrieving admin data >>> {myResult['message']}")
        return render_template("view_db_admin.html", title = "View DB Admin", user = "".join([session["userName"], " (", session["userId"], ")"]), admin = {}, form=form)

    myDBAdminData = myResult["data"]

    #print(f"db admin data >>> {myDBAdminData}")
    #myDBAdminData.update({"contact" : myDBAdminData["contact"]})

    # dbtechnologies data
    dbTechHeadings = ["DB Technology","Opco","Login Id","Status","Onboarding Date","Onboarding Doc","OffBoarding Date","Offboarding Doc"]
    rawHeadings = ["dbTechnology","opco","loginIds", "status","onBoardingDate","onBoardingDoc","offBoardingDate","offBoardingDoc"]
    myTechnologyData = []

    for dbTech in myDBAdminData["technology"]:
        myTechnologyData.append({
            "opco" : dbTech["opco"],
            "dbTechnology" : dbTech["dbTechnology"].upper(),
            "status" : dbTech["status"],
            "loginIds" : ",".join(dbTech["dbLoginId"]),
            "onBoardingDate" : dbTech["onBoardDate"],
            "onBoardingDoc" : dbTech["onBoardingDoc"],
            "offBoardingDate" : dbTech["offBoardDate"] if "offBoardDate" in dbTech else "N/A",
            "offBoardingDoc" : dbTech["offBoardingDoc"] if "offBoardingDoc" in dbTech else "N/A",
        })

    dbTechData = convertDict2TupleForHtml(rawHeadings, myTechnologyData,[])

    # history data
    histHeadings = ["TS","Who","What"]
    rawHeadings = ["ts","userId","comments"]
    histData = convertDict2TupleForHtml(rawHeadings, myDBAdminData["history"],[])

    myDBAdminData.update({
        "dbTechHeadings" : dbTechHeadings,
        "dbTechData" : dbTechData,
        "histHeadings" : histHeadings,
        "histData" : histData
        })

    myDBAdminData.pop("technology")
    myDBAdminData.pop("history")

    return render_template("view_db_admin.html", title = "View DB Admin", user = "".join([session["userName"], " (", session["userId"], ")"]), admin = myDBAdminData, form=form)

@login_required
@app.route("/edit_db_admin/<employeeId>", methods=['GET','POST'])
#@cache.cached(timeout=50)
def editDBAdmin(employeeId):
    form = forms.EditDBAdminForm()
    myOpco = "MARSH"
    myError = None
    #print(f"jsonify request >>> {jsonify(request)}")
    print(f"request >> {request}, {dir(request)}")
    print(f"get_json >>> {request.get_json()}")
    print(f"get_data >>> {request.get_data()}")
    print(f"request.values >>> {request.values}")
    print(f"request.args >>> {request.args}")
    print(f"request.args.get >>> {request.args.get('employeeId')}")

    myEmployeeId = employeeId.strip()

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    if request.method == "POST":
        print(f"request >>> : {request.form}")
        if request.form.get("saveChanges") == "saveChanges":
            # we need to save the changes
            myMethod = "modifyDBAdmin"
            myArguments = {"employeeId" : myEmployeeId, "contact" : request.form.get("contact")}
            print("post arguments >>> ", myArguments)
            myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
            if myResult["status"] == "UnSuccess":
                flash(f"An error occurred while saving DB admin changes >>> {myResult['message']} !!!")    

    myMethod = "getDBAdminDetails"
    myArguments ={"employeeId" : myEmployeeId}
       
    print(f"query args >>> {myArguments}")
    
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    
    if myResult["status"] == "UnSuccess":
        flash(f"An error occurred while retrieving admin data >>> {myResult['message']}")
        return render_template("edit_db_admin.html", title = "Modify DB Admin", user = "".join([session["userName"], " (", session["userId"], ")"]), admin = {}, form=form)

    myDBAdminData = myResult["data"]

    #print(f"db admin data >>> {myDBAdminData}")
    #myDBAdminData.update({"contact" : myDBAdminData["contact"]})

    # dbtechnologies data
    dbTechHeadings = ["DB Technology","Opco","Login Id","Status","Onboarding Date","Onboarding Doc","OffBoarding Date","Offboarding Doc"]
    rawHeadings = ["dbTechnology","opco","loginIds", "status","onBoardingDate","onBoardingDoc","offBoardingDate","offBoardingDoc"]
    myTechnologyData = []

    for dbTech in myDBAdminData["technology"]:
        myTechnologyData.append({
            "opco" : dbTech["opco"],
            "dbTechnology" : dbTech["dbTechnology"].upper(),
            "status" : dbTech["status"],
            "loginIds" : ",".join(dbTech["dbLoginId"]),
            "onBoardingDate" : dbTech["onBoardDate"],
            "onBoardingDoc" : dbTech["onBoardingDoc"],
            "offBoardingDate" : dbTech["offBoardDate"] if "offBoardDate" in dbTech else "N/A",
            "offBoardingDoc" : dbTech["offBoardingDoc"] if "offBoardingDoc" in dbTech else "N/A",
        })

    dbTechData = convertDict2TupleForHtml(rawHeadings, myTechnologyData,[])

    # history data
    histHeadings = ["TS","Who","What"]
    rawHeadings = ["ts","userId","comments"]
    histData = convertDict2TupleForHtml(rawHeadings, myDBAdminData["history"],[])

    myDBAdminData.update({
        "dbTechHeadings" : dbTechHeadings,
        "dbTechData" : dbTechData,
        "histHeadings" : histHeadings,
        "histData" : histData
        })

    myDBAdminData.pop("technology")
    myDBAdminData.pop("history")

    return render_template("edit_db_admin.html", title = "Modify DB Admin", user = "".join([session["userName"], " (", session["userId"], ")"]), admin = myDBAdminData, form=form)

def convertDict2TupleForHtml(heading, _dictDataInList, convUpperCaseKeyList = [], convLowerCaseKeyList = []):
    """
    Convert dict object to tuple data for Jinja template html rendering
    Arguments:
        heading 
        dictDataObjectsInList
    """
    myDataArray = []
    for data in _dictDataInList:
        myData = []
        for head in heading:
            if head in data:
                if head in convUpperCaseKeyList:
                    myData.append(data[head].upper())
                elif head in convLowerCaseKeyList:
                    myData.append(data[head].lower())
                else:
                    myData.append(data[head])

            else:
                myData.append(None)
        if myData:
            myDataArray.append(tuple(myData))
    
    return tuple(myDataArray)

@login_required
@app.route("/contact/", methods=['GET','POST'])
#@cache.cached(timeout=50)
def contact():
    """Standard `contact` form."""
    # this route will be submitted again once user submits the form
    form = forms.ContactForm()
    results = {}
    if request.method == 'POST':
        print("in post")
        result = request.form
        #if form.validate_on_submit():
        #  return redirect(url_for("success"))

        print(f"results >> {result}")
        return result
    else:
        print("in get")
        return render_template(
            "contact.html",
            form=form,
            template="form-template",
            results = results
        )

@login_required
@app.route("/test/")
def test():
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    """
    myMethod = "getTenantCompliance"
    myArguments = {"tenantName" : "dev.MARSH.APAC.mongo.LIS4_QA"}
    """
    """
    >>> import pandas
    >>> df = pandas.dataframe(data)
    >>> grouped = df.groupby("opco")["totalServers"]
    >>> grouped.apply(sum)
    opco
    MGTI     3
    Marsh    8
    Name: totalServers, dtype: int64
    >>> grouped.apply(list).to_dict()
    {'MGTI': [3], 'Marsh': [6, 2]}
    >>> grouped.apply(sum).to_dict()
    {'MGTI': 3, 'Marsh': 8}

    """
    """    
    myMethod = "getDashboardData"
    myArguments = {"opco" : "ALL"}
    print(f"method >>> {myMethod} ")
    print(f"args >>> {myArguments} ")
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    print(myResult)
    
    import pandas as pd
    myHostDataFrame = pd.DataFrame(myResult["data"]["hostSummaryData"])

    myHostDataByOpco = myHostDataFrame.groupby("opco")["totalServers"].apply(sum).to_dict();
    myHostDataByTech = myHostDataFrame.groupby("dbTechnology")["totalServers"].apply(sum).to_dict();
    myHostDataByEnv = myHostDataFrame.groupby("env")["totalServers"].apply(sum).to_dict();
    myHostDataByOS = myHostDataFrame.groupby(["os","osVersion"])["totalServers"].apply(sum).to_dict();
    myHostDataByLoc = myHostDataFrame.groupby("dcLocation")["totalServers"].apply(sum).to_dict();

    # converting pandas output to list
    myHostDataByOS = [{"os" : key[0], "osVersion": key[1], "totalServers" : myHostDataByOS[key]} for key in myHostDataByOS.keys()]
    myHostDataByOpco = [{key: myHostDataByOpco[key]} for key in myHostDataByOpco.keys()]
    myHostDataByTech = [{key: myHostDataByTech[key]} for key in myHostDataByTech.keys()]
    myHostDataByEnv = [{key: myHostDataByEnv[key]} for key in myHostDataByEnv.keys()]
    myHostDataByLoc = [{key: myHostDataByLoc[key]} for key in myHostDataByLoc.keys()]

    myHostAggregateData = {"opco" : myHostDataByOpco, "dbTechnology" : myHostDataByTech, "env" : myHostDataByEnv, "dcLocation" : myHostDataByLoc, "os" : myHostDataByOS, "storage" : myResult["data"]["myHostStorageStats"]}
    print(f"host aggregate data >>> {myHostAggregateData}")
    """
    """
    myMethod = "getDBEstateData"
    myArguments = {}
    """
    """
    myMethod = "getMongoLiceningData"
    myArguments = {"opco" : "ALL"}
    """
    """
    myMethod = "getScanAuth"
    myArguments = {"hostName" : "usdf21v0126","dbTechnology" : "mongo"}

    print(f"method >>> {myMethod} ")
    print(f"args >>> {myArguments} ")
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    
    """
    """
    myMethod = "searchDBComp"
    #myArguments = {'tenants': ['dev.MARSH.NAM.mongo.rep_devqa01'], 'searchComp': 'db.users', 'searchCompValue' : 'ALL', 'searchIn': 'live'}
    myArguments = {'tenants': ['dev.MARSH.NAM.mongo.rep_devqa01'], 'searchComp': 'server.status', 'searchCompValue' : 'ALL', 'searchIn': 'live'}
    """

    myMethod = "getLdapEntityDetails"
    myArguments = {'entityType': 'user', 'searchAttr': 'networkId', 'entity' : 'U1167965','domain': 'DMZ', 'userId' : session["userId"]}
    #myArguments = {'entityType': 'group', 'searchAttr': 'None', 'entity' : 'CTFY-UG_GLB_MMC_atodbs-S-L','domain': 'CORP', 'userId' : session["userId"]}

    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
    if myResult["status"] == "UnSuccess" or (not myResult["data"]):
        return render_template("test.html", title = f"Test - '{myMethod}'", user = "".join([session["userName"], " (", session["userId"], ")"]), data = myResult)

    if isinstance(myResult["data"], str):
        #print(f"raw results >>> {myResult['data']}")
        myResult["data"] = json_util.loads(myResult["data"])

    myResult["data"].update({"method" : myMethod, "arguments" : myArguments})

    return render_template("test.html", title = f"Test - '{myMethod}'", user = "".join([session["userName"], " (", session["userId"], ")"]), data = util.encodeDictData({"raw" : myResult}))

@login_required
@app.route("/under_construction/", methods=["GET","POST"])
#@cache.cached(timeout=50)
def under_construction():

    return render_template("under_construction.html", user = "".join([session["userName"], " (", session["userId"], ")"]) )

@app.route("/signup/")
def signup():
    """Standard `contact` form."""
    form = SignupForm()

    if form.validate_on_submit():
        return redirect(url_for("success"))
    return render_template(
        "sugnup.html",
        form=form,
        template="form-template"
    )

@login_required
@app.route("/licensing/", methods=["GET","POST"])
#@cache.cached(timeout=50)
def licensing():
    form = forms.licensingForm()
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    myMethod = "getMongoLicensingData"

    if request.method == "POST":
        myOpco = form.opco.data
    else:
        myOpco = form.opco.default

    myArguments = {"opco" : myOpco, "output" : "summary", "userId" : session["userId"]}

    print(f"query args >>> {myArguments}")

    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    ##print(f"testing result >>> {myResult['data']}")

    licnesingHeadings = ["OPCO","Host Name","DB Instances","Memory (GB)","Total CPUs","Docker Memory (GB)","Licensing Memory (GB)"]
    summaryHeadings = ["OPCO","Total Memory(GB)"]
    
    if myResult["status"] == "UnSuccess":
        flash(f"An error occurred while retrieving licensing detail data >>> {myResult['message']}")
        return render_template("licensing.html", title = "MMC Mongo Licensing Details", user = "".join([session["userName"], " (", session["userId"], ")"]), data={}, form = form)

    if not myResult["data"]:
        #flash(f"There are no data to display !!", "warning")
        return render_template("licensing.html", title = "MMC Mongo Licensing Details", user = "".join([session["userName"], " (", session["userId"], ")"]), data = {"data" : [], "headings" : licnesingHeadings, "summaryHeadings" : summaryHeadings, "summaryData": {}}, form = form)

    licnesingHeadings = ["OPCO","Host Name","DB Instances","Memory (GB)","Total CPUs","Docker Memory (GB)","Licensing Memory (GB)"]
    rawHeadings = ["opco","hostName","tenantInstanceCount","hostMemoryGB","hostCPU","totalDockerMemLimitGB","licensingMemoryGB"]

    for data_ in myResult["data"]:
        data_.update({
            "hostMemoryGB" : round(data_["hostMemory"]/(1024*1024*1024),0),
            "totalDockerMemLimitGB" : round(data_["totalDockerMemLimit"]/(1024*1024*1024),0)            
        })
        if data_["totalDockerMemLimit"] == 0:
            data_.update({"licensingMemoryGB" : data_["hostMemoryGB"]})
        else:
            data_.update({"licensingMemoryGB" : data_["hostMemory"] if data_["hostMemory"] < data_["totalDockerMemLimit"] else data_["totalDockerMemLimitGB"]})

    # we need to perform group by on all docker instances
    myLicensingData = convertDict2TupleForHtml(rawHeadings, myResult["data"], [])

    mySummaryRawData = pd.DataFrame(myResult["data"]).groupby("opco")["licensingMemoryGB"].apply(sum).to_dict()
    myAllOpcos = list(mySummaryRawData.keys())
    mySummaryData = []

    ##print(f"testing - summary raw data (after applying group by) >>> {mySummaryRawData}")

    for opco in myAllOpcos:
        mySummaryData.append({"opco" : opco, "totalMemoryGB" : mySummaryRawData[opco]})

    mySummaryData.append({"opco" : "Total", "totalMemoryGB" : pd.DataFrame(myResult["data"]).sum().licensingMemoryGB})
    #print(f"testing - summary data >>> {mySummaryData}")

    rawHeadings = ["opco","totalMemoryGB"]
    mySummaryData = convertDict2TupleForHtml(rawHeadings, mySummaryData, [])

    return render_template("licensing.html", title = "MMC Mongo Licensing Details", user = "".join([session["userName"], " (", session["userId"], ")"]), data = {"data" : myLicensingData, "headings" : licnesingHeadings, "summaryHeadings" : summaryHeadings, "summaryData": mySummaryData}, form = form)

@login_required
@app.route("/home/", methods=["GET","POST"])
#@cache.cached(timeout=50)
def home():
    form = forms.homeForm()

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"
    myMethod = "getDashboardData"

    if request.method == "POST":
        myOpco = form.opco.data
    else:
        myOpco = form.opco.default

    myArguments = {"opco" : myOpco, "userId" : session["userId"]}

    print(f"query args >>> {myArguments}")

    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    if myResult["status"] == "UnSuccess":
        flash(f"An error occurred while retrieving dashboard data >>> {myResult['message']}")
        return render_template("home.html", title = "MMC DbaaS Home", user = "".join([session["userName"], " (", session["userId"], ")"]), data=[], form = form)

    #print(f"testing - result 'hostSummaryData' >>> {myResult['data']['hostSummaryData']}")

    #print(f"dashboard raw results [tenants comp] >>> {myResult['data']['tenantCompData']}")
    #print(f"dashboard raw results [tenants summary] >>> {myResult['data']['tenantSummaryData']}")
    #print(f"dashboard raw results [tenants version] >>> {myResult['data']['tenantVerSummaryData']}")
    #print(f"dashboard raw results [tenants prod ver] >>> {myResult['data']['productVersion']}")

    myHostDataFrame = pd.DataFrame(myResult["data"]["hostSummaryData"])

    #myHostDataByOpco = myHostDataFrame.groupby("opco")["totalServers"].apply(sum).to_dict();
    #myHostDataByTech = myHostDataFrame.groupby("dbTechnology")["totalServers"].apply(sum).to_dict();
    #myHostDataByEnv = myHostDataFrame.groupby("env")["totalServers"].apply(sum).to_dict();
    #myHostDataByOS = myHostDataFrame.groupby(["os","osVersion"])["totalServers"].apply(sum).to_dict();
    #myHostDataByLoc = myHostDataFrame.groupby("dcLocation")["totalServers"].apply(sum).to_dict();

    # converting pandas output to list
    #myHostDataByOS = [{"os" : key[0], "osVersion": key[1], "totalServers" : myHostDataByOS[key]} for key in myHostDataByOS.keys()]
    #myHostDataByOpco = [{key: myHostDataByOpco[key]} for key in myHostDataByOpco.keys()]
    #myHostDataByTech = [{key: myHostDataByTech[key]} for key in myHostDataByTech.keys()]
    #myHostDataByEnv = [{key: myHostDataByEnv[key]} for key in myHostDataByEnv.keys()]
    #myHostDataByLoc = [{key: myHostDataByLoc[key]} for key in myHostDataByLoc.keys()]

    if myOpco.upper() == "ALL":
        hostSummaryHeadings = ["Opco","DC Location", "DB Technology","Env","OS","Total"]
        rawHeadings = ["opco","dcLocation","dbTechnology","env","os", "totalServers"]
    else:
        hostSummaryHeadings = ["DC Location", "DB Technology","Env","OS","Total"]
        rawHeadings = ["dcLocation","dbTechnology","env","os", "totalServers"]

    myTotalHosts = sum([host["totalServers"] for host in myResult["data"]["hostSummaryData"]])
    hostSummaryData = convertDict2TupleForHtml(rawHeadings, myResult["data"]["hostSummaryData"], ["env","dbTechnology"])

    print(f"testing - host summary label/data >> {hostSummaryHeadings}, {hostSummaryData}")

    myHostLocData = {
        "label" : [key for key in myHostDataFrame.groupby("dcLocation")["totalServers"].apply(sum).keys()],
        "data" :  [data for data in myHostDataFrame.groupby("dcLocation")["totalServers"].apply(sum).values]
    }

    myHostDBTechData = {
        "label" : [key for key in myHostDataFrame.groupby("dbTechnology")["totalServers"].apply(sum).keys()],
        "data" :  [data for data in myHostDataFrame.groupby("dbTechnology")["totalServers"].apply(sum).values]
    }

    myHostEnvData = {
        "label" : [key for key in myHostDataFrame.groupby("env")["totalServers"].apply(sum).keys()],
        "data" :  [data for data in myHostDataFrame.groupby("env")["totalServers"].apply(sum).values]
    }

    myHostOSData = {
        "label" : [key for key in myHostDataFrame.groupby(["os","osVersion"])["totalServers"].apply(sum).keys()],
        "data" :  [data for data in myHostDataFrame.groupby(["os","osVersion"])["totalServers"].apply(sum).values]
    }

    #print(f"host storage data >>> {myResult['data']['hostStorageData']}")
    if myResult["data"]["hostStorageData"]:
        myHostStorageData = {
            "label" : list(pd.DataFrame(myResult["data"]["hostStorageData"]).period.values),
            "data" :  list(pd.DataFrame(myResult["data"]["hostStorageData"]).usedSizeGB.values),
        }
    else:
        myHostStorageData = {"label" : [], "data" : []}

    # Tenants version data
    myUniqueDBTech = list(set([dbtech["dbTechnology"] for dbtech in myResult["data"]["tenantVerSummaryData"]]))

    myTenantVerData4Graph = []
    myAllDBTechLabels = []
    myBGColor =  ['rgb(255, 99, 132)', 'rgb(255, 159, 64)', 'rgb(255, 205, 86)', 'rgb(75, 192, 192)', 'rgb(54, 162, 235)', ]
    for dbTech in myUniqueDBTech: 
        myDBTech = [{"version" : data_["version"], "totalDBClusters" : data_["totalDBClusters"]} for data_ in myResult["data"]["tenantVerSummaryData"] if data_["dbTechnology"] == dbTech]
        myDBTechLabels = list(pd.DataFrame(myDBTech).version.values)
        myAllDBTechLabels.extend(list(pd.DataFrame(myDBTech).version.values))
        myDBTechData = [int(server) for server in list(pd.DataFrame(myDBTech).totalDBClusters.values)]
        myTenantVerData4Graph.append({"data" : myDBTechData, "datalabels" : myDBTechLabels, "backgroundColor": myBGColor, "hoverOffset": 4})

    myTenantVerHeadings = ["Db Technology","Version","EOS Date","Total DB Instances"]
    rawHeadings = ["dbTechnology","version","eosDate","totalDBClusters"]
    for data_ in myResult["data"]["tenantVerSummaryData"]:
        #print(f"tenant ver data >>> {data_}")
        #print(f"prod version >>> {myResult['data']['productVersion']}")
        myEOSDate = [prodVersion["eosDate"] for prodVersion in myResult["data"]["productVersion"] if ".".join(data_["version"].split(".")[:2]) == prodVersion["baseVersion"] and prodVersion["eosDate"]]

        if myEOSDate:
            data_.update({"eosDate" : util.convertDate2Str(util.convStr2DateViaParser(myEOSDate[0]),"%Y-%m-%d")} )
        else:
            data_.update({"eosDate" : ""})
    """
    # building summary version data (need some aggregation)
    myVersionDataByHosts = pd.DataFrame(myResult["data"]["tenantVerSummaryData"]).groupby(["dbTechnology","version"]).count().to_dict()
    myVersionDataByDBInst = pd.DataFrame(myResult["data"]["tenantVerSummaryData"]).groupby(["dbTechnology","version"])["totalDBClusters"].apply(sum).to_dict()

    myVersionData = []

    for key in list(myVersionDataByDBInst.keys()):
        myVersionData.append({
            "dbTechnology" : key[0],
            "version" : key[1],
            "totalDBClusters" : myVersionDataByDBInst[key],
            "totalHosts" : myVersionDataByHosts["hostName"][key]
        })
    myTenantVerData = convertDict2TupleForHtml(rawHeadings, myVersionData, ["dbTechnology"])

    """
    myResult["data"]["tenantVerSummaryData"] = util.sortDictInListByKey(myResult["data"]["tenantVerSummaryData"],"version")
    myTenantVerData = convertDict2TupleForHtml(rawHeadings, myResult["data"]["tenantVerSummaryData"], ["dbTechnology"])

    # licnesing data
    myMongoLicensingRawData = myResult["data"]["mongoLicesingData"]
    if myMongoLicensingRawData:
        # updating licenisng memory
        for data_ in myMongoLicensingRawData:
            if data_["totalDockerMemLimit"] == 0:
                data_.update({"licensingMemoryGB" : data_["hostMemoryGB"]})
            else:
                data_.update({"licensingMemoryGB" : data_["hostMemory"] if data_["hostMemory"] < data_["totalDockerMemLimit"] else data_["totalDockerMemLimitGB"]})
        
        myMongoLicensingData = {
            "label" : [key for key in pd.DataFrame(myMongoLicensingRawData).groupby(["opco"])["licensingMemoryGB"].apply(sum).keys()],
            "data" :  [data for data in pd.DataFrame(myMongoLicensingRawData).groupby(["opco"])["licensingMemoryGB"].apply(sum).values]
        }

        myTotalMongoMemUsedGB = pd.DataFrame(myMongoLicensingRawData).sum().licensingMemoryGB
    else:
        myMongoLicensingData = ""
        myTotalMongoMemUsedGB = 0
    # building context for method to be used in html jinja template
    context = {
        'daysDiff' : util.diffBetweenDatesInDays,
        'today' : util.getCurrentDate
    }

    #preparing data to be sent
    myData = {
        "totalHosts" : myTotalHosts,
        "hostsSummaryHeadings" : hostSummaryHeadings, 
        "hostSummaryData" : hostSummaryData,
        #"hostsVerSummaryHeadings" : hostVerSummHeadings,
        #"hostVerSummaryData" : hostVerSummaryData,
        "hostLocGraphData" : myHostLocData,
        "hostVerGraphData" : myHostOSData,
        "hostDBTechGraphData" : myHostDBTechData,
        "hostStroageGrpahData" : myHostStorageData,
        #"tenantsSummaryHeadings" : tenantSummaryHeadings, 
        #"tenantsSummaryData" : tenantsSummaryData,
        #"tenantCompData" : tenantCompData,
        "tenantVerDataSet" : myTenantVerData4Graph,
        "tenantVerDataLabels" : myAllDBTechLabels,
        "tenantVerHeadings" : myTenantVerHeadings,
        "tenantVerData" : myTenantVerData,
        "mongoLicensingData" : myMongoLicensingData,
        "totalMongoLicUtilGB" : myTotalMongoMemUsedGB,
        "notifications" : "Notifications goes here"
    }

    print(f"dashboard raw data >>> {myData}" )
    return render_template("home.html", title = "Home", user = "".join([session["userName"], " (", session["userId"], ")"]), data=myData, form = form, **context)

@app.route("/search_db_comp/", methods=["GET","POST"])
@login_required
#@cache.cached(timeout=50)
def search_db_comp():
    print(f"Sesson details >>> {session}")
    #print(f"sesson details >>> {session}")
    form = forms.searchDBComp()

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    # building context for method to be used in html jinja template
    context = {
        'daysDiff' : util.diffBetweenDatesInDays,
        'today' : util.getCurrentDate
    }

    #print(dir(form.tenants))
    #return render_template("search_db_comp.html", title = "Search DB Components", user = "".join([session["userName"], " (", session["userId"], ")"]), result = mySearchResult, form = form, **context)

    myData = []
    myHeadings = []
    mySearchResult = {"data" : myData, "headings" : myHeadings}

    if request.method == "GET":
        myOpco = form.opco.default
        myDBTechnology = form.dbTechnology.default
        myEnv = form.env.default
        mySearchIn = form.searchIn.default
        if mySearchIn.lower() == "live":
            form.searchComp.choices = [
                ("db.config", "DB Config"),
                ("db.users", "DB Users"),
                ("db.roles", "DB Roles"),
                ("db.database", "Databases"),
                ("oplog.size", "Oplog Size"),
                ("current.op", "OPs In-Progress"),
                ("top", "Top processes"),
                ("log", "Mongod logs (latest)"),
                ("server.status", "Server Status"),
                ("conn.stats", "Connection Status"),
                #("conn.pool.stats", "Connection Pool Status"),
                ("replication.info", "Replication Info"),
                ("hosts.info", "Hosts Info"),
                ("validate", "Validate collection"),
                ("db.latest.backup", "DB Latest Backup")
            ]
        else:
            form.searchComp.choices = [
                ("db.config","DB Config"),
                ("db.users","DB Users"),
                ("db.roles","DB Roles"),
                ("db.database","Databases"),
                ("oplog.size","Oplog Size")
            ]

        form.searchComp.default = form.searchComp.choices[0][0]
        mySearchComp = form.searchComp.default
        # checking if default search comp is "db.config", if yes will populate default config keys for dbtechnology
        if mySearchComp == "db.config":
            myMethod = "getDBConfigKey"        
            myArguments = {"dbTechnology" : myDBTechnology, "userId" : session["userId"]}
            myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

            if myResult["status"] == "UnSuccess":
                flash(f"An error occurred while retrieving config keys for {myArguments} >>> {myResult['message']}","danger")
                return render_template("search_db_comp.html", title = "Search DB Components", user = "".join([session["userName"], " (", session["userId"], ")"]), results = {}, form = form, **context)
            else:
                myConfigKeys = myResult["data"]
                if not myConfigKeys:
                    print(f"There are no database config key available for '{myDBTechnology}' !!!","warning")

                form.dbConfigKey.choices = [(key, key)for key in myConfigKeys]

        myMethod = "getAllTenantsName"
        myArguments = {"region" : "ALL", "status" : "Active", "userId" : session["userId"]}
        myArguments.update({"opco" : myOpco, "dbTechnology" : myDBTechnology, "env" : myEnv})
        
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while retrieving database name for {myArguments} >>> {myResult['message']}","danger")
            return render_template("search_db_comp.html", title = "Search DB Components", user = "".join([session["userName"], " (", session["userId"], ")"]), results = {}, form = form, **context)

        form.tenants.choices = [(tenant["_id"], tenant["_id"]) for tenant in myResult["data"]]

        if form.dbConfigKey.choices:
            form.dbConfigKey.default = form.dbConfigKey.choices[0][0]
        if form.tenants.choices:
            form.tenants.default = form.tenants.choices[0][0] 
        
        form.process()
        #print(f"testing - form data (tenats choices) in get >>> {form.tenants.choices}")
        return render_template("search_db_comp.html", title = "Search DB Components", user = "".join([session["userName"], " (", session["userId"], ")"]), results = {}, form = form, **context)
    else:
        print("request is POST", request.form, request.args)
        #print(f"testing - form data (tenants.choices) in post >>> {form.tenants.choices}")
        myOpco = form.opco.data
        myDBTechnology = form.dbTechnology.data
        myEnv = form.env.data
        mySearchComp = form.searchComp.data
        mySearchIn = form.searchIn.data

        myMethod = "getAllTenantsName"
        myArguments = {"region" : "ALL", "status" : "Active", "userId" : session["userId"]}
        myArguments.update({"opco" : myOpco, "dbTechnology" : myDBTechnology, "env" : myEnv})
        
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while retrieving database name for {myArguments} >>> {myResult['message']}","danger")
            return render_template("search_db_comp.html", title = "Search DB Components", user = "".join([session["userName"], " (", session["userId"], ")"]), results = {}, form = form, **context)

        form.tenants.choices = [(tenant["_id"], tenant["_id"]) for tenant in myResult["data"]]

        if mySearchIn.lower() == "live":
            form.searchComp.choices = [
                ("db.config", "DB Config"),
                ("db.users", "DB Users"),
                ("db.roles", "DB Roles"),
                ("db.database", "Databases"),
                ("oplog.size", "Oplog Size"),
                ("current.op", "OPs In-Progress"),
                ("top", "Top processes"),
                ("log", "Mongod logs (latest)"),
                ("server.status", "Server Status"),
                ("conn.stats", "Connection Status"),
                #("conn.pool.stats", "Connection Pool Status"),
                ("replication.info", "Replication Info"),
                ("hosts.info", "Hosts Info"),
                ("validate", "Validate collection"),
                ("db.latest.backup", "DB Latest Backup")
            ]
        else:
            form.searchComp.choices = [
                ("db.config","DB Config"),
                ("db.users","DB Users"),
                ("db.roles","DB Roles"),
                ("db.database","Databases"),
                ("oplog.size","Oplog Size")
            ]

        #print(form.tenants.data)
        myTenants = form.tenants.data
        mySearchComp = form.searchComp.data        
        myDBConfigKey = form.dbConfigKey.data if mySearchComp == "db.config" else ""
        mySearchCompValue = form.searchCompValue.data

        # validation
        if not myTenants:
            flash(f"You must select ataleast 1 database instance to perform search !!!","danger")
            return render_template("search_db_comp.html", title = "Search DB Components", user = "".join([session["userName"], " (", session["userId"], ")"]), results = {}, form = form, **context)

        if mySearchIn.lower() == "live":
            if len(myTenants) > 1:
                flash(f"Multiple database selection is restricted for live search !!!","danger")
                return render_template("search_db_comp.html", title = "Search DB Components", user = "".join([session["userName"], " (", session["userId"], ")"]), results = {}, form = form, **context)

        if not mySearchCompValue:
            mySearchCompValue = "ALL"

        myMethod = "searchDBComp"
        myArguments = {"tenants" : myTenants, "searchComp" : mySearchComp, "searchCompValue" : mySearchCompValue, "searchIn" : form.searchIn.data}

        if myDBConfigKey:
            myArguments.update({"configKey" : myDBConfigKey})

        print(f'arguments >> {myArguments}')
        try:
            myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})
        except Exception as error:
            flash(f"an error occurred while making rest api call {error}", "danger")
            return render_template("search_db_comp.html", title = "Search DB Components", user = "".join([session["userName"], " (", session["userId"], ")"]), results = {}, form = form, **context)

        #print(f'api result >> {myResult}')
        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while performing search using arguments {myArguments} >>> {myResult['message']}","danger")
            return render_template("search_db_comp.html", title = "Search DB Components", user = "".join([session["userName"], " (", session["userId"], ")"]), results = {}, form = form, **context)

        if isinstance(myResult["data"], str):
            # we got dict stored in string, need to convert back to dict
            myResult["data"] = json_util.loads(myResult["data"])

        #print(f" data >> {json_util.dumps(myResult['data'])}")
        if mySearchComp == "db.config":
            if mySearchIn.lower() == "repo":
                if myDBConfigKey == "db.version":
                    myHeadings = ["Database Name","Host", "Port", "DB Version"]
                    rawHeadings = ["tenantName","hostName","port","version"]
                elif myDBConfigKey == "all.configs":
                    # we have gotten all config, need to remove scan id and scan date if present (wip)
                    for data_ in myResult["data"]:
                        data_["config"].pop("scanId",None)
                        data_["config"].pop("scanDate",None)
                        # renaming config to a different key, we need config to store all param key
                        #data_["_config"] = data_.pop("config")
                        #print(f"keys >>> {data_['config'].keys()} config >>> {data_['config']}")
                        myConfigKeys = list(data_["config"].keys())
                        for key in myConfigKeys:
                            #print(f'key "{key}", config data >>> {data_["config"]}')
                            #if not isinstance(data_["config"][key], str):
                            if key == "config":
                                data_.update({"configFile" : str(data_["config"][key])})
                            else:
                                data_.update({key : str(data_["config"][key])})
                            #else:
                            #    data_.update({key : data_["config"][key]})
                        # removing config for this tenant
                        data_.pop("config", None)

                    myHeadings = ["Database Name","Host", "Port", "Docker","Version","Config File", "Audit", "Net","Process","Replication","Security","Set Parameter","Storage","SystemLog"]
                    rawHeadings = ["tenantName","hostName","port","docker","version","configFile","auditLog","net","processManagement","replication","security","setParameter","storage","systemLog"]
                else:
                    myHeadings = ["Database Name","Host", "Port", "Docker","Version", "Config", "Value"]
                    rawHeadings = ["tenantName","hostName","port","docker","version","config","value"]

                myData = convertDict2TupleForHtml(rawHeadings, myResult["data"], [])
            else:
                # building data if its live search
                if myDBConfigKey == "db.version":
                    myVersionData = []
                    for tenant in myResult["data"]:
                        for member in tenant["memberResults"]:
                            myVersionData.append({
                                "tenantName" : tenant["tenantName"],
                                "hostName" : member["hostName"],
                                "port" : member["port"],
                                "docker" : member["docker"],
                                "maxBsonSize" : member["results"]["maxBsonObjectSize"],
                                "version" : member["results"]["version"],
                                "arch" : member["results"]["buildEnvironment"]["target_arch"],
                                "os" : member["results"]["buildEnvironment"]["target_os"]
                            })
                    myHeadings = ["Database Name","Host", "Port", "Docker", "Version","Max Bson Size","Architecture","Target OS"]
                    rawHeadings = ["tenantName","hostName","port", "docker","version","maxBsonSize","arch","os"]
                    myData = convertDict2TupleForHtml(rawHeadings, myVersionData, [])
                else:
                    myConfigData = []
                    for tenant in myResult["data"]:
                        for member in tenant["memberResults"]:
                            # processing arg passed to mongod
                            for idx, arg in enumerate(member["results"]["argv"]):
                                myConfigData.append({
                                    "tenantName" : tenant["tenantName"],
                                    "hostName" : member["hostName"],
                                    "port" : member["port"],
                                    "docker" : member["docker"],
                                    "version" : member["version"],
                                    "configType" : f"arguments - {str(idx)}",
                                    "config" : "",
                                    "value" : arg
                                })
                            # processing parsed config
                            for key in member["results"]["parsed"].keys():
                                if myDBConfigKey != "all.configs" and myDBConfigKey != key:
                                    continue
                                myConfigData.append({
                                    "tenantName" : tenant["tenantName"],
                                    "hostName" : member["hostName"],
                                    "port" : member["port"],
                                    "docker" : member["docker"],
                                    "version" : member["version"],
                                    "configType" : "parsed",
                                    "config" : key,
                                    "value" : str(member["results"]["parsed"][key])
                                })
                    myHeadings = ["Database Name","Host", "Port", "Docker", "Version", "Config Type","Config", "Value"]
                    rawHeadings = ["tenantName","hostName","port","docker","version","configType","config","value"]
                    myData = convertDict2TupleForHtml(rawHeadings, myConfigData, [])

            mySearchResult = {"headings" : myHeadings, "data" : myData}

        elif mySearchComp == "db.users":
            myHeadings = ["Database Name","User", "Database", "Granted Roles"]
            rawHeadings = ["tenantName","user","db","roles"]
            if mySearchIn.lower() == "repo":
                myData = convertDict2TupleForHtml(rawHeadings, myResult["data"], [])
            else:
                myUsers = []
                for tenant in myResult["data"]:
                    for user in tenant["results"]["users"]:
                        myUsers.append({
                            "tenantName" : tenant["tenantName"],
                            "user" : user["user"],
                            "db" : user["db"],
                            "roles" : str(user["roles"])
                        })
                myData = convertDict2TupleForHtml(rawHeadings, myUsers, [])

            mySearchResult = {"headings" : myHeadings, "data" : myData}

        elif mySearchComp == "db.roles":
            myHeadings = ["Database Name","Role", "Database", "Granted Roles"]
            rawHeadings = ["tenantName","role","db","roles"]

            if mySearchIn.lower() == "repo":
                myData = convertDict2TupleForHtml(rawHeadings, myResult["data"], [])
            else:
                myRoles = []
                for tenant in myResult["data"]:
                    for role in tenant["results"]["roles"]:
                        myRoles.append({
                            "tenantName" : tenant["tenantName"],
                            "role" : role["role"],
                            "db" : role["db"],
                            "roles" : str(role["roles"])
                        })
                myData = convertDict2TupleForHtml(rawHeadings, myRoles, [])

            mySearchResult = {"headings" : myHeadings, "data" : myData}

        elif mySearchComp == "db.database":

            if mySearchIn.lower() == "repo":
                myHeadings = ["Database Name","DB","APP Id","Size MB","Collections","Indexes","Views","Documents"]
                rawHeadings = ["tenantName","db","appId","sizeMB","collections","indexes","views","objects"]
                for _db in myResult["data"]:
                    if "appId" not in _db or (not _db["appId"] and _db["db"].lower() in ["admin","local","config"]):
                        _db.update({"appId" : "system"})

                myData = convertDict2TupleForHtml(rawHeadings, myResult["data"], [])
            else:
                myHeadings = ["Database Name","DB","Size MB","Collections","Indexes","Views","Documents"]
                rawHeadings = ["tenantName","db","sizeMB","collections","indexes","views","objects"]
                myDatabases = []
                for tenant in myResult["data"]:
                    for db in tenant["dbs"]:
                        myDatabases.append({
                            "tenantName" : tenant["tenantName"],
                            "db" : db["db"],
                            "sizeMB" : round(db["sizeMB"],2),
                            "collections" : db["collections"],
                            "views" : db["views"],
                            "indexes" : db["indexes"],
                            "objects" : db["objects"]
                        })
                myData = convertDict2TupleForHtml(rawHeadings, myDatabases, [])

            mySearchResult = {"headings" : myHeadings, "data" : myData}

        elif mySearchComp == "oplog.size":
            if mySearchIn.lower() == "repo":
                myHeadings = ["Database Name","Host","Port","Dokcer","Version","Oplog Size(MB)"]
                rawHeadings = ["tenantName","hostName","port","docker","version","opLogSizeMB"]
                myData = convertDict2TupleForHtml(rawHeadings, myResult["data"], [])
            else:
                myOpLogSizeData = []
                for tenant in myResult["data"]:
                    for member in tenant["memberResults"]:
                        myOpLogSizeData.append({
                            "tenantName" : tenant["tenantName"],
                            "hostName" : member["hostName"],
                            "port" : member["port"],
                            "doker" : member["docker"],
                            "version" : member["version"],
                            "opLogSizeMB" : member["results"]["maxSize"]/(1024*1024)
                        })
                myHeadings = ["Database Name","Host", "Port", "Dokcer","Version","Oplog Size (MB)"]
                rawHeadings = ["tenantName","hostName","port","docker","version","opLogSizeMB"]
                myData = convertDict2TupleForHtml(rawHeadings, myOpLogSizeData, [])

            mySearchResult = {"headings" : myHeadings, "data" : myData}

        elif mySearchComp == "replication.info":
            if mySearchIn.lower() == "repo":
                myHeadings = ["Database Name","RS", "Member", "Health","Role","Synching From","Election Date","UpTime (Min)","Last Oplog", "Last Heartbeat"]
                rawHeadings = ["tenantName","rs","member","health","role","synchingFrom","electionDate","upTime","lastOplogTime","lastHeartbeat"]
                myData = convertDict2TupleForHtml(rawHeadings, myResult["data"], [])
            else:
                myRepInfoData = []
                for tenant in myResult["data"]:
                    for member in tenant["results"]["members"]:
                        myRepInfoData.append({
                            "tenantName" : tenant["tenantName"],
                            "rs" : tenant["results"]["set"],
                            "member" : member["name"],
                            "health" : "UP" if member["health"] == 1 else "DOWN",
                            "role" : member["stateStr"],
                            "synchingFrom" : member["syncSourceHost"],
                            "electionDate" : member["electionDate"] if "electionDate" in member else "N/A",
                            "upTime" : '{:,}'.format(round(member["uptime"] /60,0)) if "uptime" in member else "N/A",
                            "lastOplogTime" : member["optimeDate"] if "optimeDate" in member else "N/A",
                            "lastHeartbeat" : member["lastHeartbeat"] if "lastHeartbeat" in member else "N/A"
                        })

                myHeadings = ["Database Name","RS", "Member", "Health","Role","Synching From","Election Date","UpTime (Min)","Last Oplog", "Last Heartbeat"]
                rawHeadings = ["tenantName","rs","member","health","role","synchingFrom","electionDate","upTime","lastOplogTime","lastHeartbeat"]

                myData = convertDict2TupleForHtml(rawHeadings, myRepInfoData, [])

            mySearchResult = {"headings" : myHeadings, "data" : myData}

        elif mySearchComp == "hosts.info":
            if mySearchIn.lower() == "repo":
                myHeadings = ["Database Name","Host", "DB Version","Docker","OS","Mem Size (MB)","CPUs","Page Size", "Pages", "Open Files (max)"]
                rawHeadings = ["tenantName","hostName","version","docker","os","memSizeMB","cpus","pageSize","numPages","maxOpenFiles"]
                myData = convertDict2TupleForHtml(rawHeadings, myResult["data"], [])
            else:
                myHostMemberData = []
                myHostStorageData = []
                for tenant in myResult["data"]:
                    for member in tenant["memberResults"]:
                        myHostMemberData.append({
                            "tenantName" : tenant["tenantName"],
                            "hostName" : member["hostName"],
                            "version" : member["version"],
                            "docker" : member["docker"],
                            "os" : " ".join(member["results"]["os"]["name"].split(" Linux Server release ")),
                            "memSizeMB" : '{:,}'.format(member["results"]["system"]["memSizeMB"]),
                            #"cpuArch" : member["results"]["system"]["cpuArch"],
                            "cpus" : member["results"]["system"]["numCores"],
                            "pageSize" : '{:,}'.format(member["results"]["extra"]["pageSize"]),
                            "numPages" : '{:,}'.format(member["results"]["extra"]["numPages"]),
                            "maxOpenFiles" : '{:,}'.format(member["results"]["extra"]["maxOpenFiles"])
                        })

                myHeadings = ["Database Name","Host", "DB Version","Docker","OS","Mem Size (MB)","CPUs","Page Size", "Pages", "Open Files (max)"]
                rawHeadings = ["tenantName","hostName","version","docker","os","memSizeMB","cpus","pageSize","numPages","maxOpenFiles"]

                myData = convertDict2TupleForHtml(rawHeadings, myHostMemberData, [])

            mySearchResult = {"headings" : myHeadings, "data" : myData}
        elif mySearchComp == "top":
            # this is from live feed
            myHeadings = ["Database Name","Name Space","Total Time(ms)","Total Count","Read Lock(ms)","Read Lock(count)","Write Lock(ms)", "Write Lock(count)", "Queries(ms)", "Queries(count)", "Insert(ms)", "Insert(count)","Update(ms)","Update(count)","Remove(ms)","Remove(count)","Commands(ms)", "Commands(total)"]
            rawHeadings = ["tenantName","ns","nsTotalMS","nsTotalCnt","nsReadLockMS","nsReadLockCnt","nsWriteLockMS","nsWriteLockCnt","nsQueriesMS","nsQueriesCnt","nsInsertMS","nsInsertCnt","nsCommandMS","nsCommandCnt","nsRemoveMS","nsRemoveCnt", "nsReadLockMS","nsReadLockCnt"]
            myTopData = []
            for data in myResult["data"]:
                for key in data["results"]["totals"].keys():
                    if key.lower() == "note":
                        continue
                    myTopData.append({
                        "tenantName" : data["tenantName"], 
                        "ns" : key, 
                        "nsTotalMS" : data["results"]["totals"][key]["total"]["time"]/(1000),
                        "nsTotalCnt" : data["results"]["totals"][key]["total"]["count"],
                        "nsReadLockMS" : data["results"]["totals"][key]["readLock"]["time"]/(1000),
                        "nsReadLockCnt" : data["results"]["totals"][key]["readLock"]["count"],
                        "nsWriteLockMS" : data["results"]["totals"][key]["writeLock"]["time"]/(1000),
                        "nsWriteLockCnt" : data["results"]["totals"][key]["writeLock"]["count"],
                        "nsQueriesMS" : data["results"]["totals"][key]["queries"]["time"]/(1000),
                        "nsQueriesCnt" : data["results"]["totals"][key]["queries"]["count"],
                        "nsInsertMS" : data["results"]["totals"][key]["insert"]["time"]/(1000),
                        "nsInsertCnt" : data["results"]["totals"][key]["insert"]["count"],
                        "nsUpdateMS" : data["results"]["totals"][key]["update"]["time"]/(1000),
                        "nsUpdateCnt" : data["results"]["totals"][key]["update"]["count"],
                        "nsRemoveMS" : data["results"]["totals"][key]["remove"]["time"]/(1000),
                        "nsRemoveCnt" : data["results"]["totals"][key]["remove"]["count"],
                        "nsCommandsMS" : data["results"]["totals"][key]["commands"]["time"]/(1000),
                        "nsCommandsCnt" : data["results"]["totals"][key]["commands"]["count"]
                    })
            myData = convertDict2TupleForHtml(rawHeadings, myTopData, [])
            mySearchResult = {"headings" : myHeadings, "data" : myData}

        elif mySearchComp == "current.op":
            # this is from live feed
            myHeadings = ["DB Instance", "OP Time","Connection Id","Status","Desc","Client","Client OS/Driver/Version","Effective Users","Op","Command","Plan Summary","Name Space","Duration (Seconds)","Cursor","Host"]
            rawHeadings = ["tenantName","currentOpTime","connectionId","desc","status","client","clientDetails","effectiveUsers","op","command","planSummary","nameSpace","duration","cursorDetails","host"]
            myCurrentOpData = []
            for data in myResult["data"]:
                for inprog in data["results"]["inprog"]:
                    print(f"processing {inprog}")
                    if "command" in inprog:
                        inprog["command"].pop("$clusterTime", None)
                        inprog["command"].pop("signature", None)
                    myCurrentOpData.append({
                        "tenantName" : data["tenantName"],                        
                        "currentOpTime" : util.convertDate2Str(util.convStr2DateViaParser(inprog["currentOpTime"]), "%Y-%m-%d-%H:%M:%S.%f"),
                        "connectionId" : inprog["connectionId"] if "connectionId" in inprog else "n/a",
                        "status" : "Active" if inprog["active"] == True else "In-Active",
                        "desc" : inprog["desc"],
                        "client" : inprog["client"] if "client" in inprog else "n/a",
                        "clientDetails" : "".join([ str(inprog["clientMetadata"]["os"]), " / ", str(inprog["clientMetadata"]["driver"])]) if "clientMetadata" in inprog else "n/a",
                        "effectiveUsers" : ",".join([str(user) for user in inprog["effectiveUsers"]]) if "effectiveUsers" in inprog else "n/a",
                        "op" : inprog["op"] if "op" in inprog else "n/a",
                        "command" : str(inprog["command"]) if "command" in inprog else "n/a",
                        "planSummary" : inprog["planSummary"] if "planSummary" in inprog else "n/a",
                        "nameSpace" : inprog["ns"] if "ns" in inprog else "n/a",
                        "duration" : inprog["microsecs_running"]/1000000 if "microsecs_running" in inprog else 0,
                        "cursorDetails" : f"docs retrurned : {inprog['cursor']['ndocsReturned']}, await data : {str(inprog['cursor']['awaitData'])}" if "cursor" in inprog and "ndocsReturned" in inprog["cursor"] else "n/a",
                        "host" : inprog["host"] if "host" in inprog else "n/a"
                    })
            myData = convertDict2TupleForHtml(rawHeadings, myCurrentOpData, [])
            mySearchResult = {"headings" : myHeadings, "data" : myData}

        elif mySearchComp == "server.status":
            # this is from live feed
            """
            hostname = repl.me, 
            primary node = repl.primary
            replicaSet = repl.setName
            """
            myMemoryHeadings = ["DB Instance", "Host Name","Is Master","Metrics"]
            myWiredTigerCacheHeadings = ["DB Instance", "Host Name","Is Master","Metrics","Value"]
            myWiredTigerCapacityHeadings = ["DB Instance", "Host Name","Is Master","Metrics","Value"]
            myWiredTigerConnectionsHeadings = ["DB Instance", "Host Name","Is Master","Metrics","Value"]
            myWiredTigerPerfHeadings = ["DB Instance", "Host Name","Is Master","Metrics","Value"]
            myWiredTigerLockHeadings = ["DB Instance", "Host Name","Is Master","Metrics","Value"]
            myWiredTigerCursorHeadings = ["DB Instance", "Host Name","Is Master","Metrics","Value"]
            myWiredTigerSessionHeadings = ["DB Instance", "Host Name","Is Master","Metrics","Value"]
            myWiredTigerTransHeadings = ["DB Instance", "Host Name","Is Master","Metrics","Value"]

            myMemoryData = []
            myCacheData = []
            myCapacityData = []
            myConnectionsData = []
            myPerfData = []
            myLockData = []
            myCursorData = []
            mySessionData = []
            myTransactionData = []

            for tenant in myResult["data"]:
                # tcmalloc
                for metrics in tenant["results"]["tcmalloc"]["tcmalloc"]["formattedString"].split("\n"):
                    if metrics.startswith("----"):
                        continue
                    ##print(f"testing - me --> {tenant['results']['repl']}, {tenant['results']['repl']['me']} ")
                    myMemoryData.append({
                        "tenantName" : tenant["tenantName"],
                        "hostName" : tenant["results"]["repl"]["me"],
                        "isMaster" : tenant["results"]["repl"]["ismaster"],
                        "metrics" : metrics
                    })
                # wirde tiger cache
                myKeys = tenant["results"]["wiredTiger"]["cache"].keys()
                for key in myKeys:
                    myCacheData.append({
                        "tenantName" : tenant["tenantName"],
                        "hostName" : tenant["results"]["repl"]["me"],
                        "isMaster" : tenant["results"]["repl"]["ismaster"],
                        "metrics" : key,
                        "value" : tenant["results"]["wiredTiger"]["cache"][key]
                    })
                # wirde tiger capacity
                myKeys = tenant["results"]["wiredTiger"]["capacity"].keys()
                for key in myKeys:
                    myCapacityData.append({
                        "tenantName" : tenant["tenantName"],
                        "hostName" : tenant["results"]["repl"]["me"],
                        "isMaster" : tenant["results"]["repl"]["ismaster"],
                        "metrics" : key,
                        "value" : tenant["results"]["wiredTiger"]["capacity"][key]
                    })
                # wirde tiger connections
                myKeys = tenant["results"]["wiredTiger"]["connection"].keys()
                for key in myKeys:
                    myConnectionsData.append({
                        "tenantName" : tenant["tenantName"],
                        "hostName" : tenant["results"]["repl"]["me"],
                        "isMaster" : tenant["results"]["repl"]["ismaster"],
                        "metrics" : key,
                        "value" : tenant["results"]["wiredTiger"]["connection"][key]
                    })
                # wirde tiger perf
                myKeys = tenant["results"]["wiredTiger"]["perf"].keys()
                for key in myKeys:
                    myPerfData.append({
                        "tenantName" : tenant["tenantName"],
                        "hostName" : tenant["results"]["repl"]["me"],
                        "isMaster" : tenant["results"]["repl"]["ismaster"],
                        "metrics" : key,
                        "value" : tenant["results"]["wiredTiger"]["perf"][key]
                    })
                # wirde tiger lock
                myKeys = tenant["results"]["wiredTiger"]["lock"].keys()
                for key in myKeys:
                    myLockData.append({
                        "tenantName" : tenant["tenantName"],
                        "hostName" : tenant["results"]["repl"]["me"],
                        "isMaster" : tenant["results"]["repl"]["ismaster"],
                        "metrics" : key,
                        "value" : tenant["results"]["wiredTiger"]["lock"][key]
                    })
                # wirde tiger cursor
                myKeys = tenant["results"]["wiredTiger"]["cursor"].keys()
                for key in myKeys:
                    myCursorData.append({
                        "tenantName" : tenant["tenantName"],
                        "hostName" : tenant["results"]["repl"]["me"],
                        "isMaster" : tenant["results"]["repl"]["ismaster"],
                        "metrics" : key,
                        "value" : tenant["results"]["wiredTiger"]["cursor"][key]
                    })
                # wirde tiger session
                myKeys = tenant["results"]["wiredTiger"]["session"].keys()
                for key in myKeys:
                    mySessionData.append({
                        "tenantName" : tenant["tenantName"],
                        "hostName" : tenant["results"]["repl"]["me"],
                        "isMaster" : tenant["results"]["repl"]["ismaster"],
                        "metrics" : key,
                        "value" : tenant["results"]["wiredTiger"]["session"][key]
                    })
                # wirde tiger transactions
                myKeys = tenant["results"]["wiredTiger"]["transaction"].keys()
                for key in myKeys:
                    myTransactionData.append({
                        "tenantName" : tenant["tenantName"],
                        "hostName" : tenant["results"]["repl"]["me"],
                        "isMaster" : tenant["results"]["repl"]["ismaster"],
                        "metrics" : key,
                        "value" : tenant["results"]["wiredTiger"]["transaction"][key]
                    })

            myMemoryRawHeadings = ["tenantName", "hostName","isMaster","metrics"]
            myWiredTigerCacheRawHeadings = ["tenantName", "hostName","isMaster","metrics","value"]
            myWiredTigerCapacityRawHeadings = ["tenantName", "hostName","isMaster","metrics","value"]
            myWiredTigerConnectionsRawHeadings = ["tenantName", "hostName","isMaster","metrics","value"]
            myWiredTigerPerfRawHeadings = ["tenantName", "hostName","isMaster","metrics","value"]
            myWiredTigerLockRawHeadings = ["tenantName", "hostName","isMaster","metrics","value"]
            myWiredTigerCursorRawHeadings = ["tenantName", "hostName","isMaster","metrics","value"]
            myWiredTigerSessionRawHeadings = ["tenantName", "hostName","isMaster","metrics","value"]
            myWiredTigerTransRawHeadings = ["tenantName", "hostName","isMaster","metrics","value"]
 
            #print(f"testing - cache --> {myCacheData}, capacity{myCapacityData}")
            mySearchResult = {
                "headings" : {
                    "memory" : myMemoryHeadings,
                    "cache" : myWiredTigerCacheHeadings,
                    "capacity" : myWiredTigerCapacityHeadings,
                    "connections" : myWiredTigerConnectionsHeadings,
                    "perf" : myWiredTigerPerfHeadings,
                    "lock" : myWiredTigerLockHeadings,
                    "cursor" : myWiredTigerCursorHeadings,
                    "session" : myWiredTigerSessionHeadings,
                    "transaction" : myWiredTigerTransHeadings
                },
                "data" : {
                    "memory" : convertDict2TupleForHtml(myMemoryRawHeadings, myMemoryData, []),
                    "cache" : convertDict2TupleForHtml(myWiredTigerCacheRawHeadings, myCacheData, []),
                    "capacity" : convertDict2TupleForHtml(myWiredTigerCapacityRawHeadings, myCapacityData, []),
                    "connections" : convertDict2TupleForHtml(myWiredTigerConnectionsRawHeadings, myConnectionsData, []),
                    "perf" : convertDict2TupleForHtml(myWiredTigerPerfRawHeadings, myPerfData, []),
                    "lock" : convertDict2TupleForHtml(myWiredTigerLockRawHeadings, myLockData, []),
                    "cursor" : convertDict2TupleForHtml(myWiredTigerCursorRawHeadings, myCursorData, []),
                    "session" : convertDict2TupleForHtml(myWiredTigerSessionRawHeadings, mySessionData, []),
                    "transaction" : convertDict2TupleForHtml(myWiredTigerTransRawHeadings, myTransactionData, [])    
                }
            }

        elif mySearchComp == "conn.stats":
            # this is from live feed
            myHeadings = ["DB Instance", "Host Name","Port","Docker","Version","Current","Available","Active","Total Created"]
            rawHeadings = ["tenantName","hostName","port","docker","version","current","available","active","totalCreated"]
            myConnStatusData = []
            for tenant in myResult["data"]:
                for member in tenant["memberResults"]:
                    myConnStatusData.append({
                        "tenantName" : tenant["tenantName"],
                        "hostName" : member["hostName"],
                        "port" : member["port"],
                        "docker" : member["docker"],
                        "version" : member["version"],
                        "current" : '{:,}'.format(member["results"]["current"]),
                        "available" : '{:,}'.format(member["results"]["available"]),
                        "active" : '{:,}'.format(member["results"]["active"]),
                        "totalCreated" : '{:,}'.format(member["results"]["totalCreated"])                        
                        })
            myData = convertDict2TupleForHtml(rawHeadings, myConnStatusData, [])
            mySearchResult = {"headings" : myHeadings, "data" : myData}

        elif mySearchComp == "log":
            # this is from live feed
            myHeadings = ["DB Instance", "Mongod logs"]
            rawHeadings = ["tenantName","log"]
            myLogData = []
            for data in myResult["data"]:
                for log in data["results"]["log"]:
                    myLogData.append({
                        "tenantName" : data["tenantName"],
                        "log" : log
                    })                          
            myData = convertDict2TupleForHtml(rawHeadings, myLogData, [])
            mySearchResult = {"headings" : myHeadings, "data" : myData}

        print(f"search result >>> {mySearchResult}")      
        return render_template("search_db_comp.html", title = "Search DB Components", user = "".join([session["userName"], " (", session["userId"], ")"]), results = mySearchResult, form = form, **context)

@login_required
@app.route("/new_app_env/", methods=["GET","POST"])
def new_app_env():
    form = forms.newAppDBForm()

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    # building context for method to be used in html jinja template
    context = {
        'daysDiff' : util.diffBetweenDatesInDays,
        'today' : util.getCurrentDate
    }

    #print(dir(form.tenants))
    #return render_template("search_db_comp.html", title = "Search DB Components", user = "".join([session["userName"], " (", session["userId"], ")"]), result = mySearchResult, form = form, **context)

    if request.method == "GET":
        # we need to populate tenants list and databases for 1st selected tenants
        myMethod = "getAllTenantsName"
        myArguments = {"opco" : form.opco.default, "region" : "ALL", "env" : form.env.default, "dbTechnology" : form.dbTechnology.default, "status" : "Active"}
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while retrieving db details >>> {myResult['message']} !!!","danger")
            return render_template("new_app_env.html", title = "New Application Env Onboarding", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, **context)

        form.tenant.choices = [(tenant["_id"], tenant["_id"]) for tenant in myResult["data"]]
        if form.tenant.choices:
            form.tenant.default = form.tenant.choices[0]
        # retrieving default tenants databases pending app dbs

        myMethod = "getPendingAppDBs"
        myArguments = {"tenantName" : form.tenant.default[0], "userId" : session["userId"]}
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while retrieving db details >>> {myResult['message']} !!!","danger")
            return render_template("new_app_env.html", title = "New Application Env Onboarding", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, **context)

        form.dbName.choices = [(db["dbName"], db["dbName"]) for db in myResult["data"]]
        if form.dbName.choices:
            form.dbName.default = form.dbName.choices[0]

    else:
        myMethod = "onboardNewAppEnv"
        myArguments = {
            "opco": form.opco.data, 
            "env" : form.env.data, 
            "dbTechnology" : form.dbTechnology.data,
            "tenantName" : form.tenant.data,
            "dbName" : form.dbName.data,
            "appName" : form.appName.data,
            "lob" : form.lob.data,
            "appOwnerDL" : form.appOwnerDL.data,
            "busOwnerDL" : form.busOwnerDL.data,
            "serviceAccount" : form.serviceAccount.data,
            "notificationDL" : form.notificationDL.data,
            "storageRequirement" : {
                "storageBaseSizeMB" : form.storageBaseSizeMB.data,
                "storageAnnualGrowthPerc" : form.storageAnnualGrowthPerc.data
            },
            "userId" : session["userId"]
        }

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        #print(f"testing - onboarding result >>> {myResult}")

        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while onboarding new application with arguments >>> {myArguments} !!!","danger")

        return redirect(url_for("app_inventory"))

    return render_template("new_app_env.html", title = "New Application Env Onboarding", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, **context)

@login_required
@app.route("/app_inventory/", methods=["GET","POST"])
def app_inventory():
    form = forms.newAppDBForm()

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    # building context for method to be used in html jinja template
    context = {
        'daysDiff' : util.diffBetweenDatesInDays,
        'today' : util.getCurrentDate
    }

    #print(dir(form.tenants))
    #return render_template("search_db_comp.html", title = "Search DB Components", user = "".join([session["userName"], " (", session["userId"], ")"]), result = mySearchResult, form = form, **context)
    
    myMethod = "getAllAppDetails"
    
    if request.method == "GET":
        myArguments = {"opco" : form.opco.default, "dbTechnology" : form.dbTechnology.default, "userId" : session["userId"]}
    else:
        myArguments = {"opco" : form.opco.data, "dbTechnology" : form.dbTechnology.data, "userId" : session["userId"]}

    myData = []
    myHeadings = ["ID","App Name", "Env", "DB Name", "DB Size","Service Acct","DB Roles", "Collections", "Indexes", "Total Documents", "LOB", "App Owner DL", "Bus Onwer DL","Notification DL"]
    rawHeadings = ["_id", "name","env", "dbName", "sizeMB","serviceAccount","roles","collections","indexes","documents","lob","appOwnerDL","busOwnerDL","notificationDL"]

    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    for _data in myResult["data"]:
        keys = list(_data["envs"].keys())
        for key in keys:
            if isinstance(_data["envs"][key], dict) or isinstance(_data["envs"][key], list):
                _data.update({key : str(_data["envs"][key]) })
            else:
                if key in ['collections','indexes','documents']:
                    #_data.update({key : '{:,}'.format(_data["envs"][key]) })
                    _data.update({key : format(_data["envs"][key], ',d') })
                else:
                    _data.update({key : _data["envs"][key] })

        # removing envs key, we already got all item to root key
        _data.pop("envs", None)
        _data.pop("history", None)

    myData = convertDict2TupleForHtml(rawHeadings, myResult["data"], ["env"])

    #print(f"testing - app inventory result >>> {myResult}")

    if myResult["status"] == "UnSuccess":
        flash(f"An error occurred while retrieving application inventory >>> {myArguments}, {myResult['message']} !!!","danger")

    return render_template("app_inventory.html", title = "Application Inventory", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, data = myData, headings = myHeadings,  **context)

@login_required
@app.route("/ldap_query/", methods=["GET","POST"])
def ldap_query():
    form = forms.adToolForm()

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    # building context for method to be used in html jinja template
    context = {
        'daysDiff' : util.diffBetweenDatesInDays,
        'today' : util.getCurrentDate
    }

    #print(dir(form.tenants))
    #return render_template("search_db_comp.html", title = "Search DB Components", user = "".join([session["userName"], " (", session["userId"], ")"]), result = mySearchResult, form = form, **context)
    
    myData = []
    myHeadings = ["ID","App Name", "Env", "DB Name", "DB Size","Service Acct","DB Roles", "Collections", "Indexes", "Total Documents", "LOB", "App Owner DL", "Bus Onwer DL","Notification DL"]
    rawHeadings = ["_id", "name","env", "dbName", "sizeMB","serviceAccount","roles","collections","indexes","documents","lob","appOwnerDL","busOwnerDL","notificationDL"]

    myGroupResults = ""
    myUserResults = ""
    if request.method == "POST":
        myMethod = "getLdapEntityDetails"

        #myArguments = {'entityType': 'user', 'searchAttr': 'networkId', 'entity' : 'U1167965','domain': 'CORP', 'userId' : session["userId"]}
        if form.entityType.data == "group":
            myArguments = {'entityType': form.entityType.data, 'searchAttr': 'None', 'entity' : form.entity.data, 'domain': form.domain.data, 'userId' : session["userId"]}
        else:
            myArguments = {"entityType" : form.entityType.data, "searchAttr" : form.searchAttr.data, "entity" : form.entity.data, "domain": form.domain.data, "userId" : session["userId"]}

        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        #print(f"testing - ldap results for args >>> {myArguments}, results >>> {myResult}")

        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while retrieving LDAP enity details >>> {myArguments}, {myResult['message']} !!!","danger")
            return render_template("ldap_query.html", title = "LDAP Query", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, groupResults = myGroupResults, userResults = myUserResults, **context)

        if not myResult["data"]:
            flash(f"No data found for {myArguments} !!!","warning")
            return render_template("ldap_query.html", title = "LDAP Query", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, groupResults = myGroupResults, userResults = myUserResults, **context)

        #print(f"testing - we have result, processing for entity type >>> {form.entityType.data}")
        if form.entityType.data == "group":
            myMemberDetailsHeadings = ["Name", "Network Id","CN","DN","Email","Contact","Location","Member Of Group"]
            myRawHeadings = ["name","networkId","cn","dn","email","contact","location","memberOf"]
            myMemberData = []
            for _data in myResult["data"]["member_details"]:
                myMemberData.append({
                    "name" : _data["name"],
                    "networkId" : _data["networkId"],
                    "cn" : _data["cn"],
                    "dn" : _data["dn"],
                    "email" : _data["email"],
                    "contact" : _data["contact#"],
                    "location" : _data["location"],
                    "memberOf" : ",".join(_data["memberOf"])
                })
            myData = convertDict2TupleForHtml(myRawHeadings, myMemberData, [])
            myGroupGeneralData = {
                "name" : myResult["data"]["name"],
                "cn" : myResult["data"]["cn"],
                "dn" : myResult["data"]["dn"],               
                "description" : myResult["data"]["description"],
                "createdTS" : myResult["data"]["createdTS"],
                "updatedTS" : myResult["data"]["updatedTS"],
                "sAMAccountName" : myResult["data"]["sAMAccountName"],
                "objectCategory" : myResult["data"]["objectCategory"]
            }
            myGroupResults = {"general" : myGroupGeneralData, "memberDetailsHeadings" : myMemberDetailsHeadings, "memberData" : myData}
            #print(f"testing - groupResults : {myGroupResults}")
        else:
            if "attributes" in myResult["data"]:
                myUserResults = myResult["data"]["attributes"]
                myUserResults.update({"dn" : myResult["data"] if "dn" in myResult["data"] else "n/a"})
    return render_template("ldap_query.html", title = "LDAP Query", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, groupResults = myGroupResults, userResults = myUserResults, **context)

@login_required
@app.route("/check_db_port/", methods=["GET","POST"])
def check_db_port():
    form = forms.dbPortOpemForm()
    # implement concurrency and parallelism
    # https://www.toptal.com/python/beginners-guide-to-concurrency-and-parallelism-in-python
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    myMethod = "getTenantsInventory"

    # building context for method to be used in html jinja template
    context = {
        'daysDiff' : util.diffBetweenDatesInDays,
        'today' : util.getCurrentDate
    }
    
    myData = []
    myHeadings = ["Opco","TenantName", "Tenant Id", "DB Technology", "HostName", "IP Address","SSH Port", "DB Port", "Status"]
    rawHeadings = ["opco","tenantName", "tenantId", "dbTechnology", "hostName", "ipAddress", "sshPort", "dbPort", "status"]

    if request.method == "POST":

        myArguments = {'opco': "ALL", 'region': "ALL", 'dbTechnology' : form.dbTechnology.data, 'env': 'ALL', 'status' : 'Active', 'userId' : session["userId"], 'output' : ['members.summary']}

        # retrieving all tenants
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        #print(f"testing - results >>> {myResult}")

        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while retrieving all tenenat db details >>> {myArguments}, {myResult['message']} !!!","danger")
            return render_template("check_db_port.html", title = "Check DB Port Open", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, results = myData, **context)

        if not myResult["data"]:
            flash(f"No data found for {myArguments} !!!","warning")
            return render_template("check_db_port.html", title = "Check DB Port Open", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, results = myData, **context)

        myAllTenantsData = []
        for tenant in myResult["data"]:
            for member in tenant["members"]:
                # db port
                myAllTenantsData.append({
                    "opco" : tenant["opco"],
                    "tenantName" : tenant["_id"],
                    "tenantId" : member["tenantId"],
                    "dbTechnology" : tenant["dbTechnology"],
                    "hostName" : member["hostName"],
                    "ipAddress" : util.getHostIPAddress(member["hostName"]),
                    "sshPort" : "Pending",
                    "dbPort" : member["port"],
                    "status" : "Pending"
                })
        """
        import threading
        myTotalThread = len(myAllTenantsData)//10
        if len(myAllTenantsData)//10:
            myTotalThread += 1
        for thread in myTotalThread:
            threading.tThread(target = )
        """
        # checking for SSH Port
        for host in myAllTenantsData:
            if util.isPortOpen(host["hostName"], 22):
                host.update({"sshPort" : "Open"})
            else:
                host.update({"sshPort" : "Blocked"})

        # checking for DB Port
        i = 0
        for host in myAllTenantsData:
            if util.isPortOpen(host["hostName"], int(host["dbPort"])):
                if form.status.data.lower() == "all":
                    host.update({"status" : "Open"})
                else:
                    host.update({"status" : "open.donot.show"})

                print(f"{util.lambdaGetCurrDateTime()} - {host['hostName']}, port {host['dbPort']} is open ")
            else:
                host.update({"status" : "Blocked"})
                print(f"{util.lambdaGetCurrDateTime()} - {host['hostName']}, port {host['dbPort']} is blocked ")
            
            """
            # testing starts
            i += 1
            if i >10:
                break
            # testing ends
            """
        myAllTenantsData = [host for host in myAllTenantsData if host["status"] != "open.donot.show"]
        myData = convertDict2TupleForHtml(rawHeadings, myAllTenantsData, [])

    myResults = {"data" : myData, "headings" : myHeadings}

    return render_template("check_db_port.html", title = "Check DB Port Open", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, results = myResults, **context)

@app.route("/feedback/", methods=["GET","POST"])
@login_required
def feedback():
    form = forms.feedbackForm()
    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    myMethod = "saveUserFeedback"

    # building context for method to be used in html jinja template
    context = {
        'daysDiff' : util.diffBetweenDatesInDays,
        'today' : util.getCurrentDate
    }
    
    myData = []

    if request.method == "POST":

        myArguments = {'category': form.categories.data, 'response' : form.response.data, 'userId' : session["userId"]}

        # retrieving all tenants
        myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

        #print(f"testing - results >>> {myResult}")

        if myResult["status"] == "UnSuccess":
            flash(f"An error occurred while saving user feedback >>> {myArguments}, {myResult['message']} !!!","danger")
            return render_template("feedback.html", title = "Feedback", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, **context)

        flash(f"Feedback saved successfully !!!","success")
        return redirect(url_for('home'))

    return render_template("feedback.html", title = "Feedback", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form,  **context)

@app.route("/other_info/", methods=["GET","POST"])
@login_required
def other_info():
    form = forms.otherInfo()

    myRestApiURL = "http://usdfw21as383v:8000/api/audit/processRequest"
    mySrvcAcctAPIKey = "eXokNzl5NEUzOWdXNCkp"
    mySrvcAccount = "DMZPROD01\\svc-dev-deploy-app"

    myMethod = "getOtherInfo"

    # building context for method to be used in html jinja template
    context = {
        'daysDiff' : util.diffBetweenDatesInDays,
        'today' : util.getCurrentDate
    }
    
    myData = []

    if request.method == "POST":
        return redirect(url_for('home'))

    myArguments = {'userId' : session["userId"]}

    # retrieving all tenants
    myResult = util.postRestApi(myRestApiURL, {"apiKey" : mySrvcAcctAPIKey, "userId" : mySrvcAccount, "method" : myMethod, "args": myArguments})

    print(f"testing - results >>> {myResult}")

    if myResult["status"] == "UnSuccess":
        flash(f"An error occurred while retrieving other information >>> {myResult['message']} !!!","danger")
        return render_template("other_info.html", title = "Other Information", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, **context)
        
    if myResult["data"] and isinstance(myResult["data"], list):
        myResult["data"] = myResult["data"][0]

    myData = []
    """
    for area in myResult["data"]["info"]:
        myData.append({
            "area": area["area"],
            "incidents": ",".join(area["incident"]),
            "changeOrders": ",".join(area["changeOrders"]),
            "dls": ",".join(area["dls"]),
            "escalations": ",".join(area["escalations"]),
            "url": ",".join(area["url"]),
            "other": ",".join(area["other"])
      })
    """

    form.area.choices = [(area["area"],area["area"]) for area in myResult["data"]["info"]]
    if form.area.choices:
        form.area.default = form.area.choices[0][0]

    myAreaRawData = [area for area in myResult["data"]["info"] if area["area"] == form.area.default]

    if myAreaRawData:
        myAreaRawData = myAreaRawData[0]

    if myAreaRawData:
        form.incidents.data = myAreaRawData["incidents"]
        form.changeOrders.data = myAreaRawData["changeOrders"]
        form.dls.data = myAreaRawData["dls"]
        form.url.data = myAreaRawData["url"]
        form.escalations.data = myAreaRawData["escalations"]
        form.other.data = myAreaRawData["other"]

    for howto in myResult["data"]["howTo"]:
        form.howToSubject.choices.append(
            (howto["topic"] , howto["doc"])

        )
        form.howToSubject.default = form.howToSubject.choices[0][0]

    return render_template("other_info.html", title = "Other Information", user = "".join([session["userName"], " (", session["userId"], ")"]), form = form, **context)

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0', port=myWWWPort, threaded=True)

    #https://developers.google.com/chart/interactive/docs/quick_start
    """
    session management auto logout
    session.permanent = True
    app.permanent_session_lifetime = timedelta(seconds=3)
    session.modified = True
    """
