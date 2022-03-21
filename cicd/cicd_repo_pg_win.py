from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.security import Security
from com.mmc.common.infrastructure_win import Infrastructure
from com.mmc.common.globals import Globals
from com.mmc.common.jira_util import JiraUtility

from com.mmc.db.postgres_core import PGCore
from com.mmc.db.oracle_core import OracleCore
from com.mmc.db.mongo_core import MongoCore
from com.mmc.db.dbaas import Dbaas

from com.mmc.cicd.deploy_files_parser import Parser

import logging, logging.config, sys, json

class Repository(object, metaclass=Singleton):

	def __init__(self, securityToken):
		# need pg_background_worker extension of autonomou transaction
		# software url: https://github.com/vibhorkum/pg_background
		# example: https://blog.dalibo.com/2016/08/19/Autonoumous_transactions_support_in_PostgreSQL.html
		self.util = Utility()
		self.sec = Security()
		self.infra = Infrastructure()
		self.Globals = Globals()

		self.sec.validateSecToken(securityToken)

		self.parser = Parser(securityToken)

		self.LOGGER = logging.getLogger(__name__)

		self.ENVIRONMENT = self.util.getACopy(self.infra.environment)
		self.ADMIN_GROUP = self.util.getACopy(self.ENVIRONMENT["boot"]["adminSrvcGroup"])
		self.MAX_PENDING_APP_PER_USER = self.ENVIRONMENT["cicd"]["onBoarding"]["maxOnboardingAppPerUser"]

		#print(self.ENVIRONMENT)
		self.ENV = self.util.getEnvKeyVal("ENV")

		# we would need to determine env type either its prod or non-prod, we have got dev/prod. changing it to pro/non-prod
		if self.ENV == "prod":
			myPGEnv = self.ENV
		else:
			myPGEnv = "non-prod"

		# we need repostory info to instantiate PG class
		self.PG_REPO = {
			"user" : self.ENVIRONMENT["boot"]["repository"][myPGEnv]["user"],
			"userEncPass" : self.ENVIRONMENT["boot"]["repository"][myPGEnv]["userEncPass"],
			"host" : self.ENVIRONMENT["boot"]["repository"][myPGEnv]["host"],
			"port" : self.ENVIRONMENT["boot"]["repository"][myPGEnv]["port"],
			"database" : self.ENVIRONMENT["boot"]["repository"][myPGEnv]["db"]
		}
		#self.pg = PGCore(securityToken, self.PG_REPO["user"], self.PG_REPO["encPass"],self.PG_REPO["host"], self.PG_REPO["port"], self.PG_REPO["db"])

		self.pg = PGCore(securityToken)
		self.PG_CONN = self.pg.newConnection(securityToken, self.PG_REPO)

		self.dbaas = Dbaas(securityToken)

		self.__initPGRepoSql(securityToken)

	def __initPGRepoSql(self, securityToken):
		# initialized all repository sql
		try:
			#select
			self.isAppExistsSql = "SELECT COUNT(app_id) as total FROM app.app WHERE app_id = %(appId)s" 
			self.isAppExistsByNameSql = "SELECT COUNT(app_id) as total FROM app.app WHERE name = %(appName)s" 
			self.isAppEnvExistsSql = "SELECT COUNT(env.app_id) as total FROM app.app_env env, app.app app WHERE app.app_id = %(appId)s AND env.app_id = app.app_id AND env.env = %(appEnv)s" 
			self.isAppEnvExistsByNameSql = "SELECT COUNT(env.app_id) as total FROM app.app_env env, app.app app WHERE app.name = %(appName)s AND env.app_id = app.app_id AND env.env = %(appEnv)s" 
			self.isAppEnvContactExistsSql = "SELECT COUNT(app_id) as total FROM app.app_env_contact WHERE app_id = %(appId)s AND env = %(env)s AND contact_type = %(contactType)s AND contact_id = %(contactId)s "

			# checks if approver exists in valid approver table
			self.isValidApproverSql = "SELECT COUNT(network_id) as total FROM app.valid_approver WHERE network_id = lower(%(userId)s) AND status = '{activeStatus}'".format(activeStatus = self.Globals.STATUS_ACTIVE)

			# checks if this app is ready for approval
			self.isAppReadyForDeploySql = "SELECT COUNT(app.app_id) as total FROM app.app app WHERE app.app_id = %(appId)s AND app.status = '{activeStatus}'".format(activeStatus = self.Globals.STATUS_ACTIVE)

			# checks if given db instance and schema is already in use
			#self.isDbInstSchemaInUseSql = "SELECT COUNT(app_id) as total FROM app.app_env env, app.app app WHERE env.db_instance = ALL(%(dbInstance)s) and db_schemas @> %(dbSchema)s and app.app_id = env.app_id and app.technology = lower(%(dbTechnology)s) "
			self.isDbInstSchemaInUseSql = "SELECT COUNT(DISTINCT env.app_id) as total FROM app.app_env env, app.app app WHERE env.db_instance = %(dbInstance)s AND db_schemas @>  %(dbSchema)s::VARCHAR[] and app.app_id = env.app_id and app.technology = lower(%(dbTechnology)s) "

			# returns all available db schema for a given db instance which is not being used by anyother app (not used in on boarding)
			self.getDBSchemaInUseSql = """
				SELECT env.db_schemas as db_schemas 
					FROM app.app_env env, app.app app 
					WHERE app.opco = %(opco)s AND
						app.region = %(region)s AND
						app.technology = lower(%(dbTechnology)s) AND
						env.db_instance = %(dbInstance)s AND 
						app.app_id = env.app_id AND
						app.name = %(appName)s
 
			"""
			self.getAppIdByNameSql = "SELECT app_id FROM app.app WHERE name = %(appName)s"
			self.getAppStatusByIdSql = "SELECT status FROM app.app WHERE app_id = %(appId)s" 
			self.getAppStatusByNameSql = "SELECT status FROM app.app WHERE name = %(appName)s" 
			self.getAppEnvStatusSql = "SELECT status FROM app.app_env WHERE app_id = %(appId)s AND env = %(appEnv)s"
			self.getAppEnvStatusByNameSql = "SELECT status FROM app.app_env a, app.app b WHERE b.name = %(appName)s AND a.app_id = b.app_id" 

			# app.app
			# return app information for a given app id/app name/status
			self.getAnAppSql = "SELECT app.* FROM app.app app WHERE app.app_id = %(appId)s"
			self.getAnAppByNameSql = "SELECT app.* FROM app.app app WHERE app.name = %(appName)s"
			self.getAnApp4NameSql = "SELECT app.* FROM app.app app WHERE app.name = %(appName)s"
			self.getAllApp4StatusSql = "SELECT app.* FROM app.app app WHERE app.status = %(status)s"
			self.getDeployEnvOrderSql = "SELECT deploy_env_order FROM app.app WHERE app_id = %(appId)s"


			# app.ap_env
			# return env details for a given app id/ env/status
			self.getAllEnv4AppSql = "SELECT env.* FROM app.app_env env WHERE env.app_id = %(appId)s" 
			self.getAnEnv4AppSql = "SELECT env.* FROM app.app_env env WHERE env.app_id = %(appId)s AND env.env = %(env)s" 
			self.getAppEnv4StatusSql = "SELECT env.* FROM app.app_env env WHERE env.app_id = %(appId)s AND env.status = %(status)s" 

			# app.app_env_contact
			# returns all contacts for an app
			self.getContacts4AppSql = "SELECT contact.* FROM app.app_env_contact contact WHERE contact.app_id = %(appId)s" 
			self.getContacts4AppEnvSql = "SELECT contact.* FROM app.app_env_contact contact WHERE contact.app_id = %(appId)s AND contact.env = %(env)s" 
			# retrieve all contacts for a given app AND contact status
			self.getContacts4AppStatusSql = "SELECT contact.* FROM app.app_env_contact contact WHERE contact.app_id = %(appId)s AND contact.status = %(status)s" 
			self.getContacts4AppEnvStatusSql = "SELECT contact.* FROM app.app_env_contact contact WHERE contact.app_id = %(appId)s AND contact.env = %(env)s AND contact.status = %(status)s" 

			self.getAppEnvOwnerIds = "SELECT contact_id FROM app.app_env_contact WHERE app_id = %(appId)s AND env =%(env)s AND contact_type = 'owner'"
			self.getAppEnvAdminGrp = "SELECT contact_id FROM app.app_env_contact WHERE app_id = %(appId)s AND env =%(env)s AND contact_type = 'admin_adgrp'"
			self.getValidAppEnvOwnerIds = "SELECT contact_id FROM app.app_env_contact WHERE app_id = %(appId)s AND env = %(env)s AND contact_type = 'owner' AND status = '{validStatus}'".format(validStatus = self.Globals.STATUS_ACTIVE)
			self.getValidAppEnvAdminGrp = "SELECT contact_id FROM app.app_env_contact WHERE app_id = %(appId)s AND env = %(env)s AND contact_type = 'admin_adgrp' AND status = '{validStatus}'".format(validStatus = self.Globals.STATUS_ACTIVE)

			# retrieve all env in use for an app
			self.getAllAppEnvInUseSql = """
				SELECT env.env env 
				FROM app.app_env env, app.app 
				WHERE app.opco = %(opco)s
					AND app.region = %(region)s 
					AND app.technology = lower(%(dbTechnology)s) 
					AND app.app_id = %(appId)s 
					AND env.app_id = app.app_id
			"""
			# app.valid_approver
			# return all admin id from valid approver as app environment on boarding approval
			self.getAppEnvApproverSql = "SELECT network_id FROM app.valid_approver WHERE status = '{activeStatus}'".format(activeStatus = self.Globals.STATUS_ACTIVE)
	
			# returns all app information for a given opco/region/status
			"""
				SELECT app.app_id app_id, app.opco opco, app.region region, app.status, app_status, app.technology technology,
					env.env env, env.status env_status, env.hostname env_hostname, env.status env_status, env.conn_string connect_string, env.deploy_hours env_deploy_hours, env.notification_dl env_notification_dl,
					conact.contact_type, contact.contact_id, contact.status contact_status 
					FROM app.app app, app.app_env env, app.app_env_contact contact
					WHERE app.opco = LOWER(%(opco)s)
						AND app.region = LOWER(%(region)s)
						AND b.status = LOWER(%(status)s)
						AND b.app_id = a.app_id
						AND c.app_id = b.app_id
						AND c.env = b.env
			"""
			self.getAllApp4OpcoRegionStatusSql = """
				SELECT app.*
					FROM app.app app
					WHERE app.opco = LOWER(%(opco)s)
						AND app.region = LOWER(%(region)s)
						AND app.status = LOWER(%(status)s)
			"""
			self.getAllAppEnv4OpcoRegionStatusSql = """
				SELECT env.*
					FROM app.app app,
						app.app_env env
					WHERE app.opco = LOWER(%(opco)s)
						AND app.region = LOWER(%(region)s)
						AND app.app_id = env.app_id 
						AND env.status = LOWER(%(status)s)
			"""
			# returns all pending app for given opco/region excluding given user
			self.getAllAppExclUsrSql = """
				SELECT app.* 
					FROM app.app app, app.app_env env, app.app_env_contact contact
					WHERE app.opco = LOWER(%(opco)s)
						AND app.region = LOWER(%(region)s)
						AND app.status = LOWER(%(status)s)
						AND app.app_id in (
							SELECT DISTINCT app_id 
								FROM app.app_env_contact 
								WHERE app_id NOT IN (
									SELECT DISTINCT app_id 
										FROM app.app_env_contact 
										WHERE contact_id = %(userId)s
									)
 							)
			"""
			# return users app for a given status
			self.getMyAppByStatusSql = """
				SELECT app.*
					FROM app.app app
					WHERE   app.status = LOWER(%(status)s)
						AND app.app_id IN (
							SELECT DISTINCT app_id 
								FROM app.app_env_contact
								WHERE contact_id = %(userId)s 
									AND status = LOWER(%(status)s)
						)
			"""

			# return an users all apps
			self.getMyAppSql = """
				SELECT app.*
					FROM app.app app
					WHERE app.app_id IN (
							SELECT DISTINCT app_id FROM app.app_env_contact
								WHERE contact_id = %(userId)s
									AND status = '{validStatus}' 
							)
			""".format(validStatus = self.Globals.STATUS_ACTIVE)

			self.getMyAppEnvByStatusSql = """
				SELECT app.*, env.env as env, env.status env_status, env.db_instance as db_instance, env.db_schema as db_schema, env.notification_dl as notification_dl
					FROM app.app app, app.app_env env
					WHERE   env.status = LOWER(%(status)s)
						AND env.app_id = app.app_id
						AND (env.app_id, env.env) IN (
							SELECT DISTINCT app_id, env FROM app.app_env_contact
								WHERE contact_id = %(userId)s
									AND contacts.app_id = app.app_id
									AND status = '{validStatus}'
						)
			""".format(validStatus = self.Globals.STATUS_ACTIVE)
			
			self.getCurrIdSql = "SELECT currval(pg_get_serial_sequence(%(tableName)s, %(pkColumn)s));"

			### Deployment

			# deploy; checks if this deployment exists
			self.isDeploymentExistsSql = "SELECT COUNT(app_id) as total FROM app.deploy WHERE deploy_id = %(deployId)s"

			# checks if given db instance and schema is already in use
			#self.isDbInstSchemaInUseSql = "SELECT COUNT(app_id) as total FROM app.app_env env, app.app app WHERE env.db_instance = ALL(%(dbInstance)s) and db_schemas @> %(dbSchema)s and app.app_id = env.app_id and app.technology = lower(%(dbTechnology)s) "
			self.isDbInstSchemaInUseSql = "SELECT COUNT(DISTINCT env.app_id) as total FROM app.app_env env, app.app app WHERE env.db_instance = %(dbInstance)s AND db_schemas @>  %(dbSchema)s::VARCHAR[] and app.app_id = env.app_id and app.technology = lower(%(dbTechnology)s) "

			# deploy; checks if an user is allowed to perform deployment for given application
			self.isValidUserForDeploySql = "SELECT COUNT(DISTINCT contact._id) as total FROM app.app_env_contact contact, app.app app WHERE contact.contact_id = %(userId)s AND contact.status = '{activeStatus}' AND app.app_id = contact.app_id AND app.status = '{activeStatus}'".format(activeStatus = self.Globals.STATUS_ACTIVE)

			# deploy; find active/in-active deploy control id for a given deployment id
			self.getDeployCtrlIdSql = "SELECT deploy_ctrl_id from app.deploy_ctrl WHERE deploy_id = %(deployId)s and status = %(status)s"

			# deploy; get new task group id for a given deploy id (deploy_id_001)
			self.getNewDeployCtrlSql = "SELECT CONCAT(%(deployId)s, '_', LPAD(CAST((COUNT(DISTINCT deploy_id) + 1) AS VARCHAR),3,'0') ) new_deploy_ctrl_id FROM app.deploy_ctrl WHERE deploy_id = %(deployId)s"

			#deploy; get deployment detail
			self.getDeployDetailSql = "SELECT * FROM app.deploy WHERE deploy_id = %(deployId)s"
	
			# returns all deploy files for a given deployment id
			self.getDeployFilesSql = "SELECT * FROM app.deploy_files WHERE deploy_id = %(deployId)s and status = %(status)s"

			#deploy; update deploy ctrl id 
			self.updDeployCtrlSql = "UPDATE app.deploy SET deploy_ctrl_id = %(deployCtrlId)s WHERE deploy_id = %(deployId)s"
			self.updDeployFileCtrlSql = "UPDATE app.deploy_files SET deploy_ctrl_id = %(deployCtrlId)s WHERE deploy_id = %(deployId)s"
			self.updDeployTaskCtrlSql = "UPDATE app.deploy_tasks SET deploy_ctrl_id = %(deployCtrlId)s WHERE deploy_id = %(deployId)s"

			self.updDeployFileStatusSql = "UPDATE app.deploy_files SET status = %(status)s, comments = %(comments)s WHERE file_id = %(fileId)s"

			#deploy; invalidate all deployment files for a given deployment id
			self.updDeployCtrlStatusSql = "UPDATE app.deploy_ctrl SET status = %(status)s WHERE deploy_ctrl_id = %(deployCtrlId)s"
			self.updTaskStatusByDeployCtrlSql = "UPDATE app.deploy_tasks set status = %(status)s WHERE deploy_id = %(deployId)s and deploy_ctrl_id = %(deployCtrlId)s"

			############################# INSERT #############################

			#self.newAppSql = "INSERT into app.app(name,opco,region,technology,) values(%(appName)s, %(opco)s, %(region)s, %(dbTechnology)s) returning _id"
			self.createNewAppSql = """
				INSERT INTO app.app(app_id, name, region, opco, technology, status, deploy_env_order, requestor, requested_ts)
				values( %(appId)s, %(appName)s, %(region)s, %(opco)s, %(dbTechnology)s, %(status)s, ARRAY[%(deployEnvOrder)s], %(requestor)s, %(requestedTs)s)
				RETURNING app_id
			"""
			self.createNewAppEnvSql = """
				INSERT INTO app.app_env(app_id, env, host_name, conn_string, db_instance, db_schemas, notification_dl, status, requestor, requested_ts)
				values( %(appId)s, %(env)s, %(hostName)s, %(connString)s, %(dbInstance)s, %(dbSchemas)s, ARRAY[%(notificationDL)s], %(status)s, %(requestor)s, %(requestedTs)s )
			"""
			self.createAppEnvContactSql = """
				INSERT INTO app.app_env_contact(app_id	,env, contact_id, contact_type, status, requestor, requested_ts) 
				VALUES (%(appId)s, %(env)s, %(contactId)s, %(contactType)s, %(status)s, %(requestor)s, %(requestedTs)s )
				RETURNING app_id
			"""
			self.newEventLogSql = """
				INSERT INTO app.event_logs(ts, entity_id, entity_type, parent_entity_id, parent_entity_type, who, what, comment)
				VALUES (%(ts)s, %(entityId)s, %(entityType)s, %(parentEntityId)s, %(parentEntityType)s, %(who)s, %(what)s, %(comment)s )
				RETURNING _id
			"""

			self.newDeploySql = """
				INSERT INTO app.deploy(deploy_id,app_id,app_name,technology, deploy_ctrl_id, deploy_env_order,status,submitted_by,submitted_ts)
				VALUES (%(deployId)s, %(appId)s, %(appName)s, %(dbTechnology)s, %(deployCtrlId)s, ARRAY[%(deployEnvOrder)s], %(status)s, %(submittedBy)s ,%(submittedTs)s )
			"""

			self.newDeployCtrlSql = """
				INSERT INTO app.deploy_ctrl(deploy_ctrl_id, deploy_id, app_id, deploy_readme, status)
				VALUES(%(deployCtrlId)s, %(deployId)s, %(appId)s, %(deployReadMe)s, %(status)s)

			"""
			self.newDeployFileSql = """
				INSERT INTO app.deploy_files(file_name,file_path,deploy_id,deploy_ctrl_id,technology,seq,contents,total_tasks,parse_failed,parse_status,parse_status_msg,status,submitted_by,submitted_ts)
				VALUES (%(fileName)s, %(filePath)s, %(deployId)s, %(deployCtrlId)s, %(dbTechnology)s, %(seq)s, %(contents)s, %(totalTasks)s, %(parseFailed)s, %(parseStatus)s, %(parseStatusMsg)s, %(status)s, %(submittedBy)s ,%(submittedTs)s )
				RETURNING file_id
			"""

			self.newDeployTaskSql = """
				INSERT INTO app.deploy_tasks(
					file_id,file_name,deploy_id,app_id,technology,
					deploy_ctrl_id,task_seq,task_type,task_category,task_op,task_op_detail,
					task_obj_owner,task_obj_name,task_obj_type,task,status,parse_status,parse_status_msg
				)
				VALUES (
					%(fileId)s, %(fileName)s, %(deployId)s, %(appId)s, %(dbTechnology)s,
					%(deployCtrlId)s, %(taskSeq)s, %(taskType)s, %(taskCategory)s, %(taskOp)s, %(taskOpDetail)s, 
					%(taskObjOwner)s, %(taskObjName)s, %(taskObjType)s, %(task)s, %(status)s, %(parseStatus)s, %(parseStatusMsg)s )
				RETURNING task_id
			"""

			self.newDeployApprovalSql = """
				INSERT INTO app.deploy_approvals(deploy_id,env,approved_by,approval_ts)
				VALUES (%(deploy_id)s, %(env)s, %(aprovedBy)s, %(approvalTs)s )
				RETURNING _id
			"""

			# creating new valid approver
			self.newValidApproverSql = """
				INSERT INTO app.valid_approver(network_id, approver_name, ctfy_group, region, status, created_ts,last_updated_ts,comment)
				VALUES( lower(%(userId)s), %(approverName)s, %(ctfyGroup)s, %(region)s, %(status)s, %(createdTs)s, %(lastUpdatedTs)s, %(comment)s ) 
			"""
			# update
			self.updAppStatusSql = "UPDATE app.app SET status = %(status)s WHERE app_id = %(appId)s "
			self.updAppEnvOrderSql = "UPDATE app.app SET deploy_env_order = ARRAY[%(deployEnvOrder)s] WHERE app_id = %(appId)s "
			self.updAppStatusWApprovalSql = "UPDATE app.app SET approved_by = %(approvedBy)s, approved_ts = %(approvedTs)s, status = %(status)s WHERE app_id = %(appId)s "
			self.approveAppSql = "UPDATE app.app SET approved_by = %(approvedBy)s, approved_ts = %(ts)s, status = %(status)s "

			self.updEnvStatusSql = "UPDATE app.app_env SET status = %(status)s WHERE app_id = %(appId)s AND env = %(appEnv)s "
			self.updEnvStatusWApprovalSql = "UPDATE app.app_env SET approved_by = %(approvedBy)s, approved_ts = %(approvedTs)s, status = %(status)s WHERE app_id = %(appId)s AND env = %(appEnv)s and status = '{pending}'".format(pending = self.Globals.STATUS_PENDING)
			self.updContactStatusSql = "UPDATE app.app_env_contact SET status = %(status)s WHERE app_id = %(appId)s AND env = %(appEnv)s "
			self.updContactStatusWApprovalSql = "UPDATE app.app_env_contact SET approved_by = %(approvedBy)s, approved_ts = %(approvedTs)s, status = %(status)s WHERE app_id = %(appId)s AND env = %(appEnv)s and status = '{pending}'".format(pending = self.Globals.STATUS_PENDING)
			self.approveAppEnvContactSql = "UPDATE app.app_env_contact SET approved_by = %(approvedBy)s, approved_ts = %(ts)s, status = %(status)s "
			self.approveAppEnvSql = "UPDATE app.app_env SET approved_by = %(approvedBy)s, approved_ts = %(ts)s, status = %(status)s "


		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	"""
	***** CICD Repo method (data change) starts
	"""
	def onBoardCicdApp(self, securityToken, jiraIssueId, appId, appName, region, opco, dbTechnology, env, hostName, connString, dbInstance, dbSchemas, ownerIdList, notificationDL, userId):
		try:
			
			#self.LOGGER.debug("got arguments >>> {args}".\
			#	format(args = "".join([securityToken, ',', appName, ',', region, ',', opco, dbTechnology, ',', env, ',', connString, ',', \
			#		dbInstance, ',', dbSchemas, ',', ownerIdList, ',', notificationDL, ',', userId])))
			
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', str(jiraIssueId), ',', str(appId), ',', appName, ',', region, ',', opco, dbTechnology, ',', env, ',', hostName, ',', connString, ',', \
					dbInstance, ',', str(dbSchemas), ',', str(ownerIdList), ',', str(notificationDL), userId])))

			myModule = sys._getframe().f_code.co_name

			myDBSchemas = [dbSchemas] if not isinstance(dbSchemas, list) else self.util.getACopy(dbSchemas)
			myNotifyList = [notificationDL] if not isinstance(notificationDL, list) else self.util.getACopy(notificationDL)

			self.sec.validateSecToken(securityToken)

			self.LOGGER.info('user {user} requested onboarding application >>> {app}'.format(user = userId, app = ''.join([region, '.', opco, '.', dbTechnology, '.', appName])))

			self.LOGGER.info('validating on board app arguments')

			self.__validateOnboardAppEnvArgs(securityToken, appId, appName, region.lower(), opco.lower(), dbTechnology, env, hostName, connString, dbInstance, myDBSchemas, ownerIdList, myNotifyList, userId)

			# instantiating jira class for given jira issue id			
			myJiraCls = JiraUtility(securityToken, jiraIssueId)

			# will create new app if it does not exists
			#def __createAppMetadata(self, securityToken, appId, appName, region, opco, dbTechnology, env, userId):

			myAppId = self.__createAppMetadata(securityToken, appId, appName, region.lower(), opco.lower(), dbTechnology, env, userId)

			# validation
			"""
			there must be atleast 1 lower env on boarded before on boarding 'prod' environment
			if requested env is prod, get total env on boarded, if total count is 0, do not allow this prod environmet to be 
			onboarded
			"""
			# creating environment metadata for this application
			#self.__createAppEnvMetadata(securityToken, myAppId, env, connString, dbInstance, dbSchemas, deployHours, notificationDL)
			self.__createAppEnvMetadata(securityToken, myAppId, env, hostName, connString, dbInstance, myDBSchemas, myNotifyList, userId)
			
			# creating contact list for this application and environment
			myOwnerIdList = [owner.lower() for owner in ownerIdList]
			self.__createAppEnvContacts(securityToken, myAppId, env, myOwnerIdList, dbTechnology, userId.lower())

			# commiting work
			self.pg.commit(securityToken, self.PG_CONN)

			#return self.util.buildResponse(self.Globals.success, self.Globals.success, {"appId" : myAppId})

			myJiraCls.addAComment(securityToken, "app {appId} env {env} has been created (pending approval) using args >>> {args}".\
				format(appId = myAppId, env = env, args = "".join([securityToken, ',', str(appId), ',', appName, ',', region, ',', opco, dbTechnology, ',', env, ',', hostName, ',', connString, ',', \
					dbInstance, ',', str(dbSchemas), ',', str(ownerIdList), ',', str(notificationDL), userId])))

			return {"appId" : myAppId}

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __validateOnboardAppEnvArgs(self, securityToken, appId, appName, region, opco, dbTechnology, env, hostName, connString, dbInstance, dbSchemas, ownerIdList, notificationDLList, userId):
		"""
		validate all arguments passed to on board env
			1. all arg must not be empty
			2. Must not exceed the max app in pending threshold for a given user
			3. app name and env must not be on boarded
			4. Ensure other app is not using same db instance and schema (dbinstance, dbTechnology and schema must not exist)
			5. Validate connection string (must be able to perform connectivity to target database)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', str(appId), ',', appName, ',', region, ',', opco, dbTechnology, ',', env, ',', hostName, ',', connString, ',', \
					dbInstance, ',', str(dbSchemas), ',', str(ownerIdList), ',', str(notificationDLList), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			"""
			# 1. all arg must not be empty
			if not (appId or appName or region or opco or dbTechnology or env or connString or dbInstance or dbSchema or ownerIdList or notificationDLList or userId):
				raise ValueError('mandatory arguments appName/region/opco/dbTechnology/env/hostName/connString/dbInstance/dbSchema/ownerIdList/notificationDLList (one of the required argument is missing or contains null/empty value) !!! ')
			"""
			myArgValidationList = [
				{"arg" : "appId", "type" : int, "value" : appId}, 
				{"arg" : "appName", "type" : str, "value" : appName}, 
				{"arg" : "region", "type" : str, "value" : region},
				{"arg" : "opco", "type" : str, "value" : opco},
				{"arg" : "dbTechnology", "type" : str, "value" : dbTechnology},
				{"arg" : "env", "type" : str, "value" : env},
				{"arg" : "hostName", "type" : str, "value" : hostName},
				{"arg" : "connString", "type" : str, "value" : connString},
				{"arg" : "dbInstance", "type" : str, "value" : dbInstance},
				{"arg" : "dbSchemas", "type" : list, "value" : dbSchemas},
				{"arg" : "ownerIdList", "type" : list, "value" : ownerIdList},
				{"arg" : "notificationDLList", "type" : list, "value" : notificationDLList},
				{"arg" : "userId", "type" : str, "value" : userId}
			]

			self.util.valArguments2(myArgValidationList, [])
			"""
			if not (isinstance(ownerIdList, list) and isinstance(notificationDLList, list) and isinstance(dbSchemas, list)):
				raise ValueError('Invalid args; ownerIdList/notificationIdList/dbSchemas/hostName value must be an array !!!')
			"""

			"""
			app validation 
				(this validation is not good, user can request to onboard additional env of an app which is 
					already onboarded)
			we need app env validation (commenting app validation)
			"""	

			"""
			if self.isAppExists(securityToken, appId):
				raise ValueError('Invalid args; duplicate app id  < {app} > (app is already on boarded) !!!'.format(app = str(appId)))

			if self.isAppExistsByName(securityToken, appName):
				raise ValueError('Invalid args; duplicate app name < {app} >  (app is already on boarded) !!!'.format(app = appName))
			"""
			# 2. Must not exceed the max app in pending threshold for a given user
			myPendingApp = self.getMyPendingApp(securityToken, userId)

			myPendingAppIds = [app["app_id"] for app in myPendingApp]

			if len(myPendingAppIds) > self.MAX_PENDING_APP_PER_USER:
				raise ValueError("""
					MAximum {pendingAppThreshold} app is allowed to be in pending state per user
					total {tot} app found in pending state for user {user} 
					Pls get approval on pending app 
					>>> 
					    {pendingApp}
					""".format(pendingAppThreshold = self.MAX_PENDING_APP_PER_USER, tot = len(myPendingAppIds), pendingApp = str(myPendingApp)))

			# 3. app name and env must not be on boarded
			if self.isAppEnvExistsByName(securityToken, appName, env):
				raise ValueError('Invalid args; app name and its env < {appEnv} > is already in-use !!!'.format(appEnv = ''.join([appName, '.', env])))

			#4. Ensure other app is not using same db instance and schema (dbinstance, dbTechnology and schema must not exist)
			if not self.isValidDBSchema(securityToken, opco, region, appName, hostName, dbTechnology, dbInstance, dbSchemas, env):
				raise ValueError('Invalid db instance/schema {dbInstSchema}!!!'.format(dbInstSchema = "".join([hostName,".",dbInstance, ".", str(dbSchemas)])))

			if self.isDbInstSchemaInUse(securityToken, dbInstance, dbSchemas, dbTechnology):
				raise ValueError('DB instance and db schema < {dbInstSchema} > is already in-use !!!'.format(dbInstSchema = ''.join([dbTechnology, '.', dbInstance, '.', dbSchema])))

			# 5. Validate connection string (must be able to perform connectivity to target database)
			self.validateDBUri(securityToken, dbTechnology, connString, env)

		except Exception as error:
			self.LOGGER.error('an error occurred while validating uri >>> {error}'.format(error = str(error)))
			raise error

	def __createAppMetadata(self, securityToken, appId, appName, region, opco, dbTechnology, env, userId):
		# will create new app metadata, if app already exists will return app id (app_id) for this app 
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(jiraCls), ',', str(appId), appName, ',', region, ',', opco, ',', dbTechnology, ',', env, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not self.isAppExistsByName(securityToken, appName):
				# new app does not exists, creatng new one
				myAppData = {
					"appId" : appId,
					"appName" : appName, 
					"opco" : opco, 
					"region" : region, 
					"status" : self.Globals.STATUS_PENDING, 
					"dbTechnology" : dbTechnology,
					"deployEnvOrder" : env,
					"requestor" : userId.lower(),
					"requestedTs" : self.util.lambdaGetCurrDateTime()
				}
				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.createNewAppSql, myAppData)

				self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("an error occurred while creating metadata for application for >>> {app}".format(app = appName))

				myAppId = myDBResult["data"][0]["app_id"]

				self.__newEventLog(securityToken, myAppId, 'app', myAppId, 'app', userId, 'new.app', \
					'created app {appName} with app id {id} as requested by user {user}'.format(appName = appName, id = str(myAppId), user = userId))
			else:
				myAppId = self.getAppIdByName(securityToken, appName)

				if not myAppId:
					raise ValueError("could not retrieve app id for app >>> {app}".format(app = appName))

			return myAppId

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __createAppEnvMetadata(self, securityToken, appId, env, hostName, connString, dbInstance, dbSchema, notificationDL, userId):
		# will create new app env metadata 
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env, ',', hostName, ',', connString, ',', dbInstance, ',', str(dbSchema), ',', str(notificationDL), ',', userId ])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			#self.__newEventLog(securityToken, appId, 'APP', 'request.newapp.env', userId, 'user requested to create new app env')

			if not self.isAppEnvExists(securityToken, appId, env):
				# app env does not exists, creating

				#myNotificatinDlList = [notificationDL] if not isinstance(notificationDL, list) else myNotificatinDlList = self.util.getACopy(notificationDL)
				#myHostList = [hostNames] if not isinstance(hostNames, list) else self.util.getACopy(hostNames)
				myDBSchemaList = [schemaList] if not isinstance(dbSchema, list) else self.util.getACopy(dbSchema)

				myAppEnvData = {
					"appId" : appId, 
					"env" : env,
					"hostName" : hostName,
					"connString" : connString, 
					"dbInstance" : dbInstance, 
					"dbSchemas" : myDBSchemaList, 
					"notificationDL" : notificationDL, 
					"status" : self.Globals.STATUS_PENDING,
					"requestor" : userId.lower(), 
					"requestedTs" : self.util.lambdaGetCurrDateTime() 
				}

				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.createNewAppEnvSql, myAppEnvData)

				self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("an error occurred while creating metadata for application for >>> {app}".format(app = appName))

				# adding this env to end of app.deplo_env_order
				myAppEnvOrder = self.getDeployEnvOrder(securityToken, appId)

				if not (env.lower() in myAppEnvOrder):
					myAppEnvOrder.append(env)
					self.LOGGER.info('replacing existing deploy env order [{existing}] to [{new}'.format(existing = str(myAppEnvOrder), new = str(myAppEnvOrder)))
					self.__updAppEnvOrder(securityToken, appId, myAppEnvOrder)

				self.__newEventLog(securityToken, appId, 'app', appId, 'app', userId.lower(), 'new.app.env', \
					'new app env ({appEnv}) is created as requested by user {user}, deploy env order updated to {new}'.format(\
						appEnv = ''.join([str(appId), '.', env]), user = userId.lower(), new = str(myAppEnvOrder)))

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __addAppEnvContacts(self, securityToken, appId, env, contactType, contactList, userId):
		"""
		add new contacts for a given app and its enivornment. Contact can be OWNER/ADMIN/ADMIN_ADGRP
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env, ',', contactType, str(contactList), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			self.LOGGER.info("creating app contacts as requested by user {user} .. >>> {contact}".format(contact = "".join([contactType, '<', str(contactList), '>']), user = userId.lower()))

			if not isinstance(contactList, list):
				contactList = [contactList]

			for contactId in contactList:
				# creating this new contact

				myContactData = {
					"appId" : appId, 
					"env" : env, 
					"contactType" : contactType, 
					"requestor" : userId.lower(),
					"requestedTs" : self.util.lambdaGetCurrDateTime()
				}

				# changing contact id to lower case if its not a AD Group
				if contactType in [self.Globals.CONTACT_TYPE_ADMINGRP, self.Globals.CONTACT_TYPE_OWNER_ADGRP] :
					myContactData.update({"contactId" : contactId})
				else:
					myContactData.update({"contactId" : contactId.lower()})

				if contactType in [self.Globals.CONTACT_TYPE_ADMINGRP, self.Globals.CONTACT_TYPE_ADMIN]:
					myContactData.update({"status" : self.Globals.STATUS_ACTIVE})
				else:
					myContactData.update({"status" : self.Globals.STATUS_PENDING})

				# checking if this contact already exists
				if self.isAppEnvContactExists(securityToken, appId, env, contactType, contactId):
					# this contact already exists, skipping
					continue

				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.createAppEnvContactSql, myContactData)

				self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))
		
				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("an error occurred while creating app env contact >>> {app}".\
						format(app = "".join([appID, ":", env, ":", contactId])))

				self.__newEventLog(securityToken, contactId, 'new.app.contact.{contactType}'.format(contactType = contactType.lower()), appId, 'app', userId.lower(), 'app.env.contact.created', \
					'new app env contact ({appContact}) is created as requested by user {user}'.format(appContact = ''.join([str(appId), '.', env, '.', contactId]), user = userId))

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __createAppEnvContacts(self, securityToken, appId, env, ownerIdList, dbTechnology, userId):
		# create new app env contact metadata 
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env, ',', str(ownerIdList), ',', dbTechnology, ',', userId ])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not isinstance(ownerIdList, list):
				myownerIdList = [self.util.getACopy(ownerIdList)]
			else:
				myownerIdList = self.util.getACopy(ownerIdList)

			# adding new contacts as requested
			self.LOGGER.info("creating app env contacts as requested .. >>> {contact}".format(contact = str(myownerIdList)))			
			
			self.__addAppEnvContacts(securityToken, appId, env, self.Globals.CONTACT_TYPE_OWNER, myownerIdList, userId)

			# adding admin group contact for this app's dbTechnology. there is a ctfy group for each db dbTechnology
			myAdminADGroup = self.ADMIN_GROUP[dbTechnology.lower()]
			self.LOGGER.info("creating ADMIN_GRP app env contacts (sys task) .. >>> {contact}".format(contact = str(myAdminADGroup)))
			self.__addAppEnvContacts(securityToken, appId, env, self.Globals.CONTACT_TYPE_ADMINGRP, myAdminADGroup, userId)

			myAllAdminIds = self.util.getAdGroupMemberIds(myAdminADGroup)
			self.LOGGER.info("creating ADMIN (admin id) app env contacts as requested (sys task).. >>> {contact}".format(contact = str(myAllAdminIds)))
			self.__addAppEnvContacts(securityToken, appId, env, self.Globals.CONTACT_TYPE_ADMIN, myAllAdminIds, userId)

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def approveAppEnv(self, securityToken, jiraIssueId, appId, env, approverId):
		# Approve Application environment by an eligible approver (admin & owner), 
		# if not admin approver id must be in valid state i.e. approved by admin
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(jiraIssueId), ',', str(appId), ',', env, ',', str(approverId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# validating arguments 
			if not (self.isAppExists(securityToken, appId)):
				raise ValueError("Invalid app id {appId} !!!".format(appId = str(appId)))

			if not self.isAppEnvExists(securityToken, appId, env):
				raise ValueError('app {app} does not exists !!!'.format(app = "".join([str(appId), ' - ', env])))

			if not self.getAppEnvStatus(securityToken, appId, env) == self.Globals.STATUS_PENDING:
				#raise ValueError('app env << {app} >> is not in pending state !!!'.format(app = "".join([str(appId), '.', appName, '.', env])))
				raise ValueError('app env << {app} >> is not in pending state !!!'.format(app = "".join([str(appId), ' - ', env])))
			
			# instantiating jira class for given jira issue id			
			myJiraCls = JiraUtility(securityToken, jiraIssueId)

			# app env exists and its waiting for approval now validating if approver is valid approverid (admin)
			myDBResult = self.getAppApproverIds(securityToken)

			self.LOGGER.info('found approverid information >>> {dbResult}'.format(dbResult = str(myDBResult)))

			myValidApproverIds = [approver["network_id"] for approver in myDBResult]

			if approverId.lower() in myValidApproverIds:
				# approver id is a valid id for current dbTechnology ad group, updating approval and setting status to APPROVED
				myApprovalData = {
					"appId" : appId,
					"appEnv" : env,
					"approvedBy" : approverId.lower(), 
					"approvedTs" : self.util.lambdaGetCurrDateTime(),
					"status" : self.Globals.STATUS_ACTIVE
				}

				self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)
				# updating all contact for given app env status to active
				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updContactStatusWApprovalSql, myApprovalData)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("error <{error}> occurred while approving app and its env".format(error = myDBResult["message"]))
					myJiraCls.addAComment(securityToken, 'an error occurred while user {userId} approving app {app}'.format(userId = approverId, app = ''.join([appId, ',', env])))

				self.__newEventLog(securityToken, appId, 'app', appId, 'app', approverId.lower(), 'app.env.contact.approve', 'app environment contacts [{appEnv}] approved by [{id}]'.format(appEnv = ''.join([str(appId), '.', env]) , id = approverId))
				
				myJiraCls.addAComment(securityToken, 'app {app} has been approved successfully, validating app status'.format(app = ''.join([appId, ',', env])))

				#self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)
				# updating given app env status to active
				#myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updEnvStatusWApprovalSql, myApprovalData)

				
				#if myDBResult["status"] == self.Globals.unsuccess:
				#	raise ValueError("error <{error}> occurred while approving app and its env contacts".format(error = myDBResult["message"]))

				self.__newEventLog(securityToken, appId, 'app', appId, 'app', approverId.lower(), 'app.env.approve', 'app environment [{appEnv}] approved by [{id}]'.format(appEnv = ''.join([str(appId), '.', env]) , id = approverId))

				# validating app status
				#self.__validateAppStatus(securityToken, appId, env)
				self.__validateAppStatus(securityToken, appId, approverId)
				
				myAppStatus = self.getAppStatusById(securityToken, appId)
			
				myDetailedStatus = self.getAppDetailedStatus(securityToken, appId)

				myJiraCls.addAComment(securityToken, 'app {app} status has been validated, current status is {status}'.format(app = ''.join([appId, ',', env]), status = ''.join([myAppStatus, ' (' , myDetailedStatus, ')'])))

				self.pg.commit(securityToken, self.PG_CONN)

				#return myDBResult
			else:
				raise ValueError('not a valid approver >>> {approver}'.format(approver = approverId.lower()))

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __updateAppEnvStatus(self, securityToken, appId, env, status, approverId):
		"""
		update app env status
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env, ',', status, ',', approverId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.LOGGER.info('updating app {app} env status to {status} '.format(app = str(appId), status = status))

			myStatusData = {
				"appId" : appId, 
				"appEnv" : env, 
				"status" : status,
			}
			
			if status in [self.Globals.STATUS_VALID, self.Globals.STATUS_ACTIVE]:
				myStatusData.update(
					{"approvedBy" : approverId, "approvedTs" : self.util.lambdaGetCurrDateTime()})
				mySql = self.updEnvStatusWApprovalSql
			else:
				mySql = updEnvStatusSql

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, mySql, myStatusData)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.__newEventLog(securityToken, appId, 'app', appId, 'app', approverId.lower(), 'modify.app_env.status', \
				'app_env.status [{app}] changed to [{status}] by [{id}]'.format(app = ''.join([str(appId),'.',env]), status = status, id = approverId))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __updateAppStatus(self, securityToken, appId, status, approverId):
		"""
		update app status
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', status, ',', approverId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.LOGGER.info('updating app {app} status to {status} '.format(app = str(appId), status = status))

			myStatusData = {"appId" : appId, "status" : status}

			if status in [self.Globals.STATUS_VALID, self.Globals.STATUS_ACTIVE]:
				# we have got status as approved (valid/active), need to inject approver details
				myStatusData.update ({
					"approvedBy" : approverId,
					"approvedTs" : self.util.lambdaGetCurrDateTime(),
				})
				mySql = self.updAppStatusWApprovalSql
			else:
				mySql = self.updAppStatusWApprovalSql

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, mySql, myStatusData)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.__newEventLog(securityToken, appId, 'app', appId, 'app', approverId.lower(), 'modify.app.status', 'app.status changed to [{status}] by [{id}]'.format(status = status, id = approverId))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __updAppEnvOrder(self, securityToken, appId, deployEnvOrder):
		"""
		update app deploy env order, replaces exisiting env order with new env order
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', str(deployEnvOrder)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.LOGGER.info('replacing app [{app}] deploy env order to [{env}] '.format(app = str(appId), env = str(deployEnvOrder)))

			myEnvOrderData = {"appId" : appId, "deployEnvOrder" : deployEnvOrder}

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updAppEnvOrderSql, myEnvOrderData)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.__newEventLog(securityToken, appId, 'app', appId, 'app', 'sys', 'modify.app.deployEnvOrder', 'updating app deploy env order to >> {envOrder}'.format(envOrder = str(deployEnvOrder)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __validateAppStatus(self, securityToken, appId, approverId):
		"""
		perform validation on app status
			1. all contcats must be 'ACTIVE' (validated)
			2. app must have 1 lower and 1 prod environment in ACTIVE state
			3. all env must be in valid/active state
		"""
		try:
			#self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', appName, ',', env])))
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', str(approverId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not (self.isAppExists(securityToken, appId)):
				raise ValueError("Invalid app id {appId} !!!".format(appId = str(appId)))

			if not (self.isValidApprover(securityToken, approverId)):
				raise ValueError("Invalid approver id {approver} !!!".format(approver = str(approverId)))

			# hardcoding rule for app status validation

			# retrieving all env for this app
			myAllEnvDetails = self.getAppEnvDetails(securityToken, appId)

			# loop thru all environment to validate/populate the status
			for env in myAllEnvDetails:

				myPendingContacts = self.getPendingAppContacts(securityToken, appId, env["env"])

				self.LOGGER.info('found pending contacts for env {env} >>> {contacts}'.format(env = env["env"], contacts = str(myPendingContacts)))

				if myPendingContacts:
					return
				else:
					self.__updateAppEnvStatus(securityToken, appId, env["env"], self.Globals.STATUS_VALID, approverId)

			# we need to find all env which is in pending state for this app
			myPendingEnv = self.getPendingEnv4App(securityToken, appId)

			self.LOGGER.info('found pending env >>> {env}'.format(env = str(myPendingEnv)))
			
			if myPendingEnv:
				return

			# all environment is in approved status, need to check if we got 1 lower and 1 prod
			# environment

			myAllEnvList = [env["env"] for env in myAllEnvDetails]
			myAppDetail = self.getAnAppDetails(securityToken, appId)

			# we need prod and atleast 1 lower environment for application to be fully approved (status = active)
			if self.Globals.ENV_PROD in myAllEnvList and any(env in myAllEnvList for env in self.Globals.ENV_LOWER):
				
				self.LOGGER.info('alll validation met, making application {app} active'.format(app = ''.join([myAppDetail["app_name"], ".", str(appId)])))

				self.__updateAppStatus(securityToken, appId, self.Globals.STATUS_ACTIVE, approverId)

			"""
			for env in myAllEnvDetails:
				if env["status"]
			myAllEnvList = [env["env"] for env in myAllEnvDetails]

			# looping thru all env, if all contacts are active/approve will mark env status as valid
			for env in myAllEnvList:

			# checking if prod env is on boarded
			if not "prod" in myAllEnsList:
				# prod env is not on boarded, markign staus 'PENDING'
				myStatus = 'PENDING'

			# prod env is onboarded, lets validate the status of all on boarded env for this app
			for env in myAllEnvDetails:
				if not(env["status"] == "APPROVED"):
					myStatus = "PENDING"
					break

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updateAppStatus, {"appId" : appId, "status" : myStatus})

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				return myDBResult["data"]
			"""

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def populateValidApprover(self, securityToken, userId):
		"""
		populated valid approver (retrieve networkId from valid CTFY group). Transaction is controlled in this method, no external commit/rollback is allowed
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			myAllCtfyGrpList = self.ADMIN_GROUP["approverGrp"]
			"""
			"approverGrp" : [
				{"region" : "nam" , "ctfyGrp" : ["CTFY-UG_NA_Marsh_dba-S-L"]},
				{"region" : "apac", "ctfyGrp" : ["CTFY-UG_APAC_Marsh_dba-S-L"]}
			]
			"""
			self.LOGGER.info('found all ctfy grp for valid approver >>> {allGrp}'.format(allGrp = str(myAllCtfyGrpList)))
			
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			for regionGrp in myAllCtfyGrpList:

				myregion = regionGrp["region"]
				myRegionCtfyGrpList = regionGrp["ctfyGrp"]
	
				for ctfyGrp in myRegionCtfyGrpList:

					myCtfyGrpUserList = self.util.getAdGroupMemberIds(ctfyGrp)

					self.LOGGER.info('found user list for ctfygrp {ctfyGrp} >>> {userList}'.format(ctfyGrp = ctfyGrp, userList = myCtfyGrpUserList))

					for user in myCtfyGrpUserList:
						#populating user if they dont exists in valid approver as valid status
						if not self.isValidApprover(securityToken, user):
							myApproverData = {
								"userId" : user,
								"approverName" : self.util.getADGrpUserName(user),
								"ctfyGroup" : ctfyGrp,
								"region" : myRegion,
								"status" : self.Globals.STATUS_ACTIVE,
								"createdTs" :  self.util.lambdaGetCurrDateTime(),
								"lastUpdatedTs" : self.util.lambdaGetCurrDateTime(),
								"comment" : 'creating new valid approver'
							}
				
							#self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

							myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newValidApproverSql, myApproverData)

							if myDBResult["status"] == self.Globals.unsuccess:
								raise ValueError(myDBResult["message"])

							# creating event log (adding user)
							self.__newEventLog(securityToken, user, 'new.approver',user, 'new.approver', user,'new.approver.created')

					self.LOGGER.info('completed populating user from ctfy group >>> {ctfygrp}'.format(ctfygrp = ctfyGrp))
				self.LOGGER.info('completed processing ctfy group for region >>> {region}'.format(region = myregion))
	
			# commiting data
			self.pg.commit(securityToken, self.PG_CONN)
			self.LOGGER.info('valid approver list populated successfully')

		except Exception as error:
			self.LOGGER.error('an error occurred while populating valid approver list >>> {error}'.format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __newEventLog(self, securityToken, entityId, entityType, parentEntityId, parentEntityType, userId, what, comment = None):
		"""
		create new event log for a given entity
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(entityId), ',', entityType, ',', str(parentEntityId), ',', parentEntityType, ',', userId, ',', what, ',', str(comment)])))

			myModuleName = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# placeholde for validating arguments
			myCurrentTs = self.util.lambdaGetCurrDateTime()
			myCurrentReadableTs = self.util.lambdaGetCurrReadableTime()

			"""
			if sysAction:
				myUser = 'user [sys] '
			else:
				myUser = 'user [{user}] '.format(user = self.USER_ID.lower())
			"""
			if comment:
				myComment = "".join([str(myCurrentReadableTs), ' - ' , userId.lower(), 'performed ', comment])
			else:
				myComment = "".join([str(myCurrentReadableTs), ' - user [', userId.lower(), '] performed ', what , ' on ', entityType, '.', entityId])

			myEventLog = {
				"ts" : myCurrentTs, 
				"entityId" : entityId, 
				"entityType" : entityType, 
				"parentEntityId" : parentEntityId, 
				"parentEntityType" : parentEntityType, 
				'who' : userId.lower(),
				"what" : what, 
				'comment' : myComment
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newEventLogSql, myEventLog)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("error < {error} > while creating new event log".format(error = myDBResult["message"]))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __createAppEnvDeployOrder(self, securityToken, appId):
		pass

	def validateDBUri(self, securityToken, dbTechnology, connString, env):
		"""
		Validate if given dbTechnology uri is a valid (will perform connectivity use credential stored in repository)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', dbTechnology, ',', connString, ',', env])))

			myModuleName = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if dbTechnology.lower() == self.Globals.TECHNOLOGY_ORACLE.lower():
				# oracle dbTechnology has 2 users 1 for prod and other for non prod, we need right env to get the credentials from bootstrap config file

				if env == self.Globals.ENV_PROD.lower():
					myEnv = env
				else:
					myEnv = self.Globals.ENV_NONPROD

				myOracleUser = self.ENVIRONMENT["boot"]["deploy"]["oracle"][myEnv]["user"]
				myOracleUserEncPass = self.ENVIRONMENT["boot"]["deploy"]["oracle"][myEnv]["userEncPass"]

				if not (myOracleUser or myOracleUserEncPass):
					raise ValueError('oracle deploy user/enc pass is missing from bootstrp config file !!!')

				self.LOGGER.info('perfoming {env} uri test with credential >>> {cred}'.format(env = env, cred = ''.join([myOracleUser,'/', myOracleUserEncPass,'@',connString])))

				try:
					from cx_Oracle import DatabaseError
					myOracle = OracleCore(securityToken)
					myOraConnArg = {"userId" : myOracleUser, "userEncPass" : myOracleUserEncPass, "dsn" :connString,"tag" : "Testing Connection"}
					myTestConnection = myOracle.newConnection(securityToken, myOraConnArg)
					myOracle.closeConnection(securityToken, myTestConnection)
					"""
					except DatabaseError as error:
						myError = error.args[0]
						if hasattr(myError,'code') and hasattr(myError, 'message'):
							if myError.code = 1017:
								raise ValueError('in valid login/password !!!')
					"""
				except Exception as error:
					raise ValueError("invalid db uri <{uri}>, error >> {error}".format(uri = connString, error = str(error)))

			elif dbTechnology.lower() == self.Globals.TECHNOLOGY_POSTGRES.lower():
				pass
				# perform postgres specific db uri validation

		except Exception as error:
			raise error

	#### Deployment

	def createNewDeployment(self, securityToken, deployId, appId, deployFilesPath, submittedBy):
		"""
		creates new deployment in repository (populate deploy, deploy_control, deploy_files and deploy_tasks)
		Arguments:
			deployId: Deployment id (Jira issue id)
			appId: Application id to which this deployment belongs to
			submittedBy: User requesting this deployment
			deployFilesPath: Path of downloaded deployment files from Jira/Bitbucket
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, str(appId), ',', deployFilesPath, ',', submittedBy])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# validate new deployment data
			#self.validateNewDeployment(securityToken, deployId, appId, submittedBy, deplo)

			# need app id, get Application detail
			myAppDetail = self.getAnAppDetails(securityToken, appId)

			# create new deployment ctrl id
			myDBResult = self.createNewDeployCtrl(securityToken, deployId, appId, deployFilesPath)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			myNewDeployCtrlId = myDBResult["data"]

			if not(myDBResult["status"] == self.Globals.success and myNewDeployCtrlId):
				raise ValueError("an error <{error}> occurred while creating new deployment ctrl id for deployment {deployId} !!!".\
					format(error = myDBResult["message"], deployId = deployId))

			# creating new deployment
			myDBResult = self.__newDeploy(securityToken, deployId, myAppDetail["app_id"], myAppDetail["name"], myAppDetail["technology"], \
				myAppDetail["deploy_env_order"], myNewDeployCtrlId, submittedBy)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("an error <{error}> occurred while saving deployment data !!!".format(error = myDBResult["message"]))

			# processing deployment files
			#				  __processDeployFiles(self, securityToken, deployId, appId, dbTechnology, deployCtrlId, deployFilesPath, submittedBy)
			myDBResult = self.__processDeployFiles(securityToken, deployId, myAppDetail["app_id"], myAppDetail["technology"], myNewDeployCtrlId, deployFilesPath, submittedBy)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("an error <{error}> occurred while saving deployment data !!!".format(error = myDBResult["message"]))

			self.LOGGER.info("deploymen saved successfully, commiting txn")

			self.pg.commit(securityToken, self.PG_CONN)

			return self.util.buildResponse(self.Globals.success, self.Globals.success)

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}, rolling back transaction !!!".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))

	def reprocessDeployFiles(self, securityToken, deployId, deployFilesPath, submittedBy):
		"""
		Reprocess deployment files, this is only allowed when deployment status is in pending state 
			(deploymen didnt start yet)
		"""
		try:

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', deployFilesPath, ',', submittedBy])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not self.isProessDeployFilesAllowed:
				raise ValueError("Deployment {id} is in-progress, reprocessing of deployment files are not allowed !!!".format(id = deployId))

			# reprocessing deployment files
			# check if there are any changes to deployment files

		except Exception as error:
			self.LOGGER.error("an error occurred while reprocessing deploy files >>> {error}, rolling back current txn".format(error = str(error)), exc_info = True)
			raise error

	def __newDeploy(self, securityToken, deployId, appId, appName, dbTechnology, deployEnvOrder, deployCtrlId, submittedBy):
		"""
		Saves new deployment in repository
		Arguments:
			deployId: Deployment id (Jira issue id)
			appId: Application id to which this deployment belongs to
			appName: Application name
			dbTechnology: database technology
			deployEnvOrder: order of deployment in env (dev,test,stg,prod)
			deployCtrlId : Deployment control id
			submittedBy: User requesting this deployment
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', appName, ',', deployId, ',', str(appId), ',', dbTechnology, ',', str(deployEnvOrder), ',', deployCtrlId, ',', submittedBy])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myDeployData = {
				"deployId" : deployId, 
				"appId" : appId, 
				"appName" : appName, 
				"dbTechnology" : dbTechnology, 
				"deployEnvOrder" : deployEnvOrder,
				"deployCtrlId" : deployCtrlId, 
				"status" : "Pending", 
				"submittedBy" : submittedBy, 
				"submittedTs" : self.util.lambdaGetCurrDateTime()
			}
	
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newDeploySql, myDeployData)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}, rolling back current txn".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __donotuse_getActiveDeployFiles(self, securityToken, deployId):
		"""
		Returns all active deployment files for a given deployment id
		Arguments:
			deployId: Deployment id (Jira issue id)
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myDeployData = {"deployId" : deployId, "status" : self.Globals.STATUS_ACTIVE}
	
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployFilesSql, myDeployData)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult and "data" in myDBResult:
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}, rolling back current txn".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def createNewDeployCtrl(self, securityToken, deployId, appId, deployFilePath):
		"""
		Description: Create new deployment control for a given deploy/app/deploy ctrl id. If an active ctrl is found
			and re processing of deployment files are allowed, existing active ctrl id will marked inactive and new ctrl id
			will be created and mark 'active'

		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appId), ',', deployFilePath])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myDeployReadmeFile = self.util.buildPath(deployFilePath, self.Globals.DEPLOY_README_FILE)

			# validation

			if not self.util.isFileExists(myDeployReadmeFile):
				raise ValueError("invalid deployment readme file {file} (does not exists) !!!".format(file = myDeployReadmeFile))

			myDeployReadmeData = self.util.readJsonFile(myDeployReadmeFile)

			if not myDeployReadmeData :
				raise ValueError("deploy readme file {file} is empty !!!".format(file = myDeployReadmeFile))

			# checking if this deployment is new deployment
			if self.isDeploymentExists(securityToken, deployId):
				# new deployment validating status

				if self.isProessDeployFilesAllowed(securityToken, deployId):
					# reprocessing of deployment files are allowed, invalidating exisiting deploy ctrl id
					myActiveDeployCtrlId = self.getActiveDeployCtrl(securityToken, deployId)
					self.__invalidteDeployCtrl(securityToken, deployId, myActiveDeployCtrlId)
			
			# generate new deployment ctrl
			myNewdeployCtrlId = self.getNewDeployCtrl(securityToken, deployId)

			self.LOGGER.debug("got new deploy ctrl id {ctrlId} proceeding with processing deployment files (readme)".format(ctrlId = myNewdeployCtrlId))

			myDeployReadmeData = {
				"deployCtrlId" : myNewdeployCtrlId,
				"deployId" : deployId,
				"appId" : appId,
				"deployReadMe" : json.dumps(myDeployReadmeData),
				"status" : self.Globals.STATUS_ACTIVE
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newDeployCtrlSql, myDeployReadmeData)
			
			self.LOGGER.debug("db results >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("an error {error} occurred while saving deploy readme file contents for deploy id {deployId}".\
					format(error = myDBResult["message"], deployId = str(deployId)))

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myNewdeployCtrlId)

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}, rolling back current txn".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __addDeployFile(self, securityToken, deployId, deployCtrlId, fileObject, submittedBy):
		"""
		Description: Saves new deployment file in repository. 
		Arguments:
			securityToken: Security token  
			deployId: Deployment id (Jira issue id)
			deployCtrlId : Deply handle id (generated during loading readme file)
			fileObjet 	: Deployment file object
			submittedBy: User requesting this deployment
		Returns: file_id
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', deployCtrlId, ',', str(fileObject), ',', submittedBy])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# we would not change the deployment which is valid/in-progress/completed, need validation
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myDeployFileWPath = self.util.buildPath(fileObject["path"], self.util.getFileName(fileObject["file"]))
			
			myDeployFileContents = self.util.readTextFile(myDeployFileWPath)

			myDeployFileData = {
				"fileName" : fileObject["file"],
				"filePath" : fileObject["path"],
				"deployId" : deployId,
				"deployCtrlId" : deployCtrlId,
				"dbTechnology" : fileObject["dbTechnology"],
				"seq" : fileObject["seq"],
				"contents" : myDeployFileContents,
				"totalTasks" : fileObject["totalTasks"],
				"parseFailed" : fileObject["failedTasks"],
				"parseStatus" : fileObject["status"],
				"parseStatusMsg" : fileObject["message"],
				"status" : self.Globals.STATUS_PENDING,
				"submittedBy" : submittedBy, 
				"submittedTs" : self.util.lambdaGetCurrDateTime()
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newDeployFileSql, myDeployFileData)
			self.LOGGER.debug("db results >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("an error {error} occurred while saving deploy file {file} for deploy id {deployId}".\
					format(error = myDBResult["message"], file = myDeployFileWPath, deployId = str(deployId)))

			myFileId = myDBResult["data"][0]["file_id"]

			self.LOGGER.info("returning >>> {result}".format(result = myFileId))

			return myFileId

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __addDeployTasks(self, securityToken, deployId, appId, deployCtrlId, taskObject, submittedBy):
		"""
		Description: Saves new deployment file in repository. 
		Arguments:
			securityToken: Str, Security token
			deployId: Str, Deployment id (Jira issue id)
			appId : Integer, Application id
			deployCtrlId : Str, Deply handle id (generated during loading readme file)
			taskObject 	: Dict, Task object (dict)
			submittedBy: Str, User requesting this deployment
		Returns: {"status", "", message" : "", "data" : <task_id>}
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appId), ',', deployCtrlId, ',', str(taskObject), ',', submittedBy])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# we would not change the deployment which is valid/in-progress/completed, need validation
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newDeployTaskSql, taskObject)

			self.LOGGER.debug("db results >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("an error {error} occurred while saving deploy file {file} for deploy id {deployId}".\
					format(error = myDBResult["message"], file = myDeployFileWPath, deployId = str(deployId)))

			myTaskId = myDBResult["data"][0]["task_id"]

			self.LOGGER.info("returning >>> {result}".format(result = myTaskId))

			return myTaskId

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __processDeployFiles(self, securityToken, deployId, appId, dbTechnology, deployCtrlId, deployFilesPath, submittedBy):
		"""
		Description: Saves new deployment in repository. Deployment must not ne in in-progress/completed state
			If there are files are already in this deployment, will invalidate them and procees with
			new set of files
		Arguments:
			deployId: Deployment id (Jira issue id)
			appId: Application id to which this deployment belongs to
			dbTechnology : Database technology
			deployCtrlId : deploy ctrl id
			deployFilesPath : location of depoyment files
			submittedBy: User requesting this deployment
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appId), ',', dbTechnology, ',', deployCtrlId, ',', deployFilesPath, ',', submittedBy])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# we would not change the deployment which is valid/in-progress/completed, need validation
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not self.util.isDirExists(deployFilesPath):
				raise ValueError("invalid deployment file path {path} (does not exists) !!!".format(path = deployFilesPath))

			myTaskList = [] # store all new tasks id 
			
			myParsedDeployFilesObj = self.parser.parseDeployFiles(securityToken, deployFilesPath, dbTechnology)

			for file in myParsedDeployFilesObj:
				# saving each file details in deploy_files
				fileObject = {
					"file" : file["file"], 
					"path" : file["path"], 
					"seq" : file["seq"],
					"dbTechnology" : dbTechnology,
					"status" : file["status"],
					"message" : file["message"],
					"totalTasks" : file["summary"]["total"],
					"failedTasks" : file["summary"]["unSuccess"]
				}

				myFileId = self.__addDeployFile(securityToken, deployId, deployCtrlId, fileObject, submittedBy)

				"""
				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("an error {error} occurred while saving deploy file for deploy id {deployId}".\
						format(error = myDBResult["message"], deployId = str(deployId)))
				
				myFileId = myDBResult["data"]
				"""
				# saving this files all task to deploy_tasks
				for task in file["tasks"]:
					myTaskData = {
						"fileId" :  myFileId,
						"fileName" : file["file"],
						"deployId" : deployId,
						"appId" : appId,
						"dbTechnology" : dbTechnology, 
						"deployCtrlId" : deployCtrlId,
						"taskSeq" : task["seq"],
						"taskType" : self.Globals.TASK_TYPE_USER,
						"taskCategory" : task["opType"],
						"taskOp" : task["op"], 
						"taskOpDetail" : "".join([task["op"], ".", task["objType"]]),
						"taskObjOwner" : task["objOwner"],
						"taskObjName" : task["objName"],
						"taskObjType" : task["objType"],
						"task" : task["opStatement"],
						"status" : self.Globals.STATUS_ACTIVE,
						"parseStatus" : task["status"],
						"parseStatusMsg" : task["message"]
					}

					# adding tasks data
					#__addDeployTasks(self, securityToken, deployId, appId, deployCtrlId, taskObject, submittedBy
					myTaskId = self.__addDeployTasks(securityToken, deployId, appId, deployCtrlId, myTaskData, submittedBy)

					"""
					if myDBResult["status"] == self.Globals.unsuccess:
						raise ValueError("an error {error} occurred while saving deploy file for deploy id {deployId}".\
							format(error = myDBResult["message"], deployId = str(deployId)))
					"""
					myTaskList.append(myTaskId)

				self.LOGGER.info("all tasks loaded for file {file} Tasks detail: > {total}, tasks > {tasks} ".format(file = file["file"], total = len(myTaskList), tasks = str(myTaskList)))

			return self.util.buildResponse(self.Globals.success, self.Globals.success)

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __invalidteDeployCtrl(self, securityToken, deployId):
		"""
		Description: Invalidate existing active deployment ctrl for a given deployment id, (updates deploy_ctrl status to in-active)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# get active deploy tasks group id for this deployment
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myActivedeployCtrlId = self.getActiveDeployCtrl(securityToken, deployId)

			# check the status of this deployment, deployment status must not have started
			myDeployStatus = self.getDeployStatus(securityToken, deployId)

			if myDeployStatus and myDeployStatus not in self.Globals.VALID_STATUS_RELOAD_DEPLOY_FILES_LIST:
				raise ValueError("Deployment invalidation is not allowed (for invalidation, a deployment must be in {expecting}, got {got}) !!! ".\
					formta(expecting = str(self.Globals.VALID_STATUS_RELOAD_DEPLOY_FILES_LIST, got = myDeployStatus)))

			if myActivedeployCtrlId:
				# updating status to inactive
				myUpdateData = {"deploy_ctrl_id" : myActivedeployCtrlId, "status" : self.Globals.STATUS_INACTIVE}

				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployCtrlStatusSql, myUpdateData)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("an error occurred while invalidating exisitng files for deploy id >>> {deployId}".format(deployId = deployId))

			"""
			for file in myActiveDeployFiles:
				# invalidating all deployment files for this deployment
				self.LOGGER.debug("invaliditng file [{file}] ".format(file = "".join([ file["file_id"], ".", file["file_name"]])))
	
				myFileUpdData = {
					"file_id" : file["file_id"],
					"status" : self.Globals.STATUS_INACTIVE, 
					"comments" : "got new files for this deployment, invalidting this files @ {time}".format(self.util.lambdaGetCurrDateTime())
				}

				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployFileStatusSql, myFileUpdData)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("an error occurred while invalidating exisitng files for deploy id >>> {deployId}".format(deployId = deployId))

				# invalidating all deployment tasks for this file
				myTaskUpdData = {
					"fileId" : file["file_id"],
					"status" : self.Globals.STATUS_INACTIVE,
					"comments" : "invalidating all task of {file}".format(file = file["file_name"])
				}

				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updTaskStatusByFileIdSql, myFileUpdData)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("an error occurred while invalidating exisitng files for deploy id >>> {deployId}".format(deployId = deployId))

			if myActiveTaskGroupId:
				# found active tasks group for this deployment, invalidating
				myUpdateData = {"deployId" : deployId, "deployCtrlId" : myActiveTaskGroupId, "status" : self.Globals.self.STATUS_INACTIVE}
				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployTaskGrpStatusSql, myUpdateData)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("an error occurred while invalidating deployment tasks for task group id >>> {taskGrpId}".format(taskGrpId = myActiveTaskGroupId))

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))
			"""

			#return self.util.buildResponse(self.Globals.success, self.Globals.success)

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def validateNewDeployment(self, securityToken, deployId, appId, submittedBy, deployfilePath):
		"""
		Description: Validates new deployment, following rules will be used for validation
			1. deployId : check if this deployment is not in use
			2. appId : Checks if this app is ready for approval 
			3. submittedBy : Checks if this app is ready for approval
			4. DeployFilePath: Path where deployment files have been downloaded 

		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myAppName = self.getAnAppDetails(securityToken, appId)

			# starting validations

			# 1. check if this deployment is not in use

			self.LOGGER.debug("validating deployment id ...")

			if self.isDeploymentExists(securityToken, deployId):
				raise ValueError("deployment id {id} is already in use !!!".format(id = deployId))

			self.LOGGER.debug("deployment id {id} id not is use, proceeding with rest of validation ")

			# 2. Checks if this app is ready for approval

			self.LOGGER.debug("validating app for deployment ...")
			self.LOGGER.debug("checking if app {app} is ready for deployment, proceeding with rest of validation ".format(app = str(appId)))

			if not self.isAppReadyForDeploy(securityToken, appId):
				raise ValueError("application {app} is not read for approval !!!".format(app = "".join([app_name, " - ", str(appId)])))

			self.LOGGER.debug("app {app} is ready for deployment, proceeding with rest of validation ".format(app = str(appId)))

			# 3. Checks if user is authorized to perform this application deployment
			self.LOGGER.debug("validating user authorization ...")

			self.LOGGER.debug("checking if user {id} is authorized to submit deployment for app {app},proceeding with rest of validation ".format(id = submittedBy, app = str(appId)))

			if not self.isValidUserForDeploy(securityToken, appId, submittedBy):
				raise ValueError("user {user} is not allowed to deploy application {app} !!!".format(user = submittedBy, app = "".join([app_name, " - ", str(appId)])))

			self.LOGGER.debug("user {id} is authorized to submit deployment for app {app}, proceeding with rest of validation ".format(id = submittedBy, app = str(appId)))

			# 4. checking if deploy readme file is present
			self.LOGGER.debug("validating deploy readme file ...")

			myDeployReadmeFile = self.util.buildPath(deployfilePath,self.Globals.DEPLOY_README_FILE)

			if not self.util.isFileExists(myDeployReadmeFile):
				raise ValueError("missing mandatory deploy readme file {file} !!!".format(file = myDeployReadmeFile))
			
			self.LOGGER.debug("deploy readme file {file} exists ".format(file = myDeployReadmeFile))
			myDeployReadme = self.util.readJsonFile(myDeployReadmeFile)

			# 5. validating readme file contents
			self.LOGGER.debug("validating deploy readme file contents ...")

			if not myDeployReadme:
				raise ValueError("deployment readme file {file} is empty".format(file = myDeployReadmeFile))

			self.LOGGER.debug("deployment readme file {file} is not empty".format(file = myDeployReadmeFile))

			if not ("app" in myDeployReadme and "dbTechnology" in myDeployReadme and \
					"preDeploy" in myDeployReadme and "checkUserConn" in myDeployReadme["preDeploy"] and \
					"backup" in myDeployReadme["preDeploy"] and "deploy" in myDeployReadme ):
				raise ValueError("deploy instruction file {file} is corrupted (missing mandatory keys) !!!".\
					format(expect = "".join([myAppId, myDeployReadme["app"]])))

			self.LOGGER.debug("found mandatory key app/dbTechnology/preDepoy/deploy etc. in file {file} ".format(file = myDeployReadmeFile))

			if not("app" in  myDeployReadme and myDeployReadme["app"] == appId):
				raise ValueError("mismatch application id, expecting {expect}, got {got} !!!".\
					format(expect = myAppId, got = myDeployReadme["app"]))

			self.LOGGER.debug("found valid app id in deploy readme file {file}".format(file = myDeployReadmeFile))

			# 6. validating deployment files

			self.LOGGER.debug("validating all deployment files listed in deploy readme")

			mySeq = 0
			myDeployFiles = self.util.sortDictInListByKey(self.util.getACopy(myDeployReadme["deploy"]), "seq", False)

			for file in myDeployFiles:
				myFiles = []
				mySeq += 1 
				#print("my seq", mySeq)
				if file["op"] == "run":
					myFiles.append(file["file"])
				elif file["op"] == "load":
					myFiles.append(file["dataFile"])
					myFiles.append(file["file"])

				missingFiles = [file for file in myFiles if not self.util.isFileExists(self.util.buildPath(deployfilePath,self.util.getFileName(file)))]

				if file["seq"] != mySeq:
					raise ValueError("invalid seq# for {file}, expecting {expect}, got {got} ".format(file = file["file"], expect = str(mySeq), got = file["seq"]))


			if missingFiles:
				raise ValueError("deployment file(s) are missing >>> {files}".format(files = str(missingFiles)))

			self.LOGGER.debug("found all deployment files")

			# validation completed		
			self.LOGGER.info("all validation completed successfully !!!")
	
		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getNewDeployCtrl(self, securityToken, deployId):
		"""
		Description: Returns new deploy control id for a given deploy id.
		Arguments: 
			securityToken : securityToken
			deployId : deployment id
			fileName : deployment file name for which task group is needed
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)
			
			myCriteria = {"deployId" : deployId}
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getNewDeployCtrlSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))
			
			if myDBResult and "data" in myDBResult:
				self.LOGGER.info("returning new deploy handle id >>> {result}".format(result = myDBResult["data"][0]["new_deploy_ctrl_id"]))
				return myDBResult["data"][0]["new_deploy_ctrl_id"]
		
		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getActiveDeployCtrl(self, securityToken, deployId):
		"""
		Description: Returns active deploy_ctrl_id for a given deployment id
		Arguments:
			securityToken: security token
			deployId : deployment id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(deployId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myActivedeployCtrlId = ""
			
			myCriteria = {"deployId" : deployId, "status" : self.Globals.STATUS_ACTIVE}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getdeployCtrlIdSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				myActivedeployCtrlId = myDBResult["data"][0]["deploy_ctrl_id"]

			self.LOGGER.info("returning >> {result}".format(result = str(myActivedeployCtrlId)))

			return myActivedeployCtrlId

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployStatus(self, securityToken, deployId):
		"""
		Description: Returns current status of a deployment
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"deployId" : deployId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployDetailSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult and "data" in myDBResult:
				return myDBResult["data"][0]["status"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isDeploymentExists(self, securityToken, deployId):
		"""
		Description: Checks if this deployment exists
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(deployId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"deployId" : deployId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isDeploymentExistsSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isValidUserForDeploy(self, securityToken, appId, submittedBy):
		"""
		Description: Checks if this user is allowed to perform the deployment for this application
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"appId" : appId, "userId" : submittedBy.strip().lower()}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isValidUserForDeploySql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isAppReadyForDeploy(self, securityToken, appId):
		"""
		Description: Checks if application is ready for deployment. (App must be in valid state and not in Blackout)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"appId" : appId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isAppReadyForDeploySql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isProessDeployFilesAllowed(securityToken, deployId):
		"""
		Description: Checks whether reprocessing or deploy files are allowed for a given deployment id
		Arguments:
		"""
		try:

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appId), ',', deployFilePath])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if self.isDeploymentExists(securityToken, deployId):
				# new deployment validating status
				myDeployStatus = self.getDeployStatus(securityToken, deployId)
				
				self.LOGGER.debug("found deployment status >> {status}".format(status = myDeployStatus))

				if myDeployStatus not in self.Globals.VALID_STATUS_RELOAD_DEPLOY_FILES_LIST:

					self.LOGGER.debug("deployment status is not in valid state to generate new deployment ctrl, expecting {expect}, got {got}, aborting !!!".\
						format(expecting = self.Globals.VALID_STATUS_RELOAD_DEPLOY_FILES_LIST, got = myDeployStatus))
					
					return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("an error occurred while checking reprocess of deployment files allowed >>> {error} !!!".format(error = str(error)), exc_info = True)
			raise error

	"""
	***** CICD Repo method (data change) ends
	"""

	"""
	***** CICD Repo method (get data) starts
	"""

	def isAppExists(self, securityToken, appId):
		"""
		checks if a given app id already exists in repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"appId" : appId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isAppExistsSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isAppExistsByName(self, securityToken, appName):
		"""
		checks if a given app name already exists in repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', appName])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"appName" : appName}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isAppExistsByNameSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isAppEnvExists(self, securityToken, appId, env):
		"""
		checks if a given app (appId) env exists in repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"appId" : appId, "appEnv" : env}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isAppEnvExistsSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isAppEnvExistsByName(self, securityToken, appName, env):
		"""
		checks if a given app (appName) env exists in repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', appName, ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"appName" : appName, "appEnv" : env}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isAppEnvExistsByNameSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isAppEnvContactExists(self, securityToken, appId, env, contactType, contactId):
		"""
		checks if a given app (appName) env exists in repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env, ',', contactType, ',', contactId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"appId" : appId, "env" : env, "contactType" : contactType, "contactId" : contactId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isAppEnvContactExistsSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isValidDBInstance(self, securityToken, opco, region, appName, hostName, dbTechnology, dbInstance, env):
		"""
		checks if db instance is valid for given opco/region/appName/hostName/dbTechnology and env
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', opco, ',', region, ',', appName, ',', hostName, ',', dbTechnology, ',', dbInstance, ',', env])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if dbTechnology.lower() == self.Globals.TECHNOLOGY_ORACLE.lower():
				myAguments = {
					"securityToken" : securityToken,
					"opco" : opco,
					"region" : region,
					"appName" : appName,
					"hostName" : hostName,
					"dbInstance" : dbInstance,
					"env" : env
				}
				return self.dbaas.isValidOraAppDBInst(**myAguments)

		except Exception as error:
			self.LOGGER.error('an error occurred >>> {error}'.format(error = str(error)), exc_info = True)
			raise error

	def isValidDBSchema(self, securityToken, opco, region, appName, hostName, dbTechnology, dbInstance, dbSchemas, env):
		"""
		checks if db instance is valid for given opco/region/appName/hostName/dbTechnology and env
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', opco, ',', region, ',', appName, ',', hostName, ',', dbTechnology, ',', dbInstance, ',', str(dbSchemas), ',', env])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if dbTechnology.lower() == self.Globals.TECHNOLOGY_ORACLE.lower():
				myAguments = {
					"securityToken" : securityToken,
					"opco" : opco,
					"region" : region,
					"appName" : appName,
					"hostName" : hostName,
					"dbInstance" : dbInstance,
					"dbSchemas" : dbSchemas,
					"env" : env
				}
				return self.dbaas.isValidOraDBSchema(**myAguments)

		except Exception as error:
			self.LOGGER.error('an error occurred >>> {error}'.format(error = str(error)), exc_info = True)
			raise error

	def isDbInstSchemaInUse(self, securityToken, dbInstance, dbSchemas, dbTechnology):
		"""
		checks if a given db instance and dbSchema is already in use by other app
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', dbInstance, ',', str(dbSchemas), ',', dbTechnology])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"dbInstance" : dbInstance, "dbSchema" : dbSchemas, 'dbTechnology' : dbTechnology}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isDbInstSchemaInUseSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	# need decorator
	def getDBSchema4OnBoarding(self, securityToken, appName, opco, region, hostName, dbInstance, dbTechnology, env):
		# Returns all db schema for a given instances which is not used by any other application (for onboarding)
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', appName, ',', opco, ',', region, ',', hostName, ',', dbInstance, ',', dbTechnology, ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# retrieving all schema for this db instance from dbaas (Oracle)
			if dbTechnology.lower() == self.Globals.TECHNOLOGY_ORACLE.lower():
				#dbaasGetOraDBSchemas(self, securityToken, appName, opco, region, hostName, dbInstance, dbTechnology, env)
				mydbaasDBSchema = self.dbaasGetOraDBSchemas(securityToken, appName, opco, region, hostName, dbInstance, dbTechnology, env)

			if not mydbaasDBSchema:
				raise ValueError('no db schema found for db instance >> {dbInstance}'.format(dbInstance = dbInstance))

			self.LOGGER.info('found schema list from dbaas for db instance {dbInstance} >>> {schemaList}'.format(dbInstance = dbInstance, schemaList = str(mydbaasDBSchema)))

			# retrieving all schema in use for this db instance from repository
			myCriteria = {
				"appName" : appName,
				"opco" : opco.lower(),
				"region" : region.lower(), 
				"dbInstance" : dbInstance, 
				"dbTechnology" : dbTechnology, 
				"env" : env.lower()
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDBSchemaInUseSql, myCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError('error while retrieving in-use schema list from repository for db instance >>> {dbInstance}'.format(dbInstance = dbInstance))

			self.LOGGER.info('found schema list in use from repository for {dbInstance} >>> {schemaList}'.format(dbInstance = dbInstance, schemaList = str(myDBResult["data"])))

			# available schema for onboarding
			if myDBResult["data"]:
				mySchemaInUseList = myDBResult["data"][0]
			else:
				mySchemaInUseList = []

			print('dbaas schema >>>', mydbaasDBSchema)
			print('in use schema >>>', mySchemaInUseList)

			myAvailableSchemaList = list(set([schema['SCHEMA'] for schema in mydbaasDBSchema]) - set([schema['db_schema'] for schema in mySchemaInUseList]))

			self.LOGGER.info('returning available schema list for {dbInstance} >>> {schemaList}'.format(dbInstance = dbInstance, schemaList = str(myAvailableSchemaList)))

			return myAvailableSchemaList

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAllApps4OnBoarding(self, securityToken, opco, region, userId):
		"""
		retrieves list of application which is available for on boarding
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', opco, ',', region, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# retrieving all application lists from dbaas
			myAlldbaasApplists = self.dbaasGetAllApps(securityToken, opco, region)

			# retrieving all app which is on boarded and approved (need to exclude them from top list)

			myAllApprovedAppLists = self.getAllAppDetail(securityToken, opco, region, self.Globals.STATUS_ACTIVE)
			myApprovedAppIds = [app["app_id"] for app in myAllApprovedAppLists]

			self.LOGGER.info("found application list which is already on boarded and approved >>> {result}".format(result = str(myApprovedAppIds)))

			# retrieving other users (except this users) pending app (also filter the application which is in pending state on boarded by other user)			
			myAllExclPendingApp = self.getAllPendingAppExclMe(securityToken, opco, region, userId)
			myOtherUserPendingAppIds = [app["app_id"] for app in myAllExclPendingApp]

			self.LOGGER.info("found application list which is in pending state but does not belong to this user >>> {result}".format(result = str(myOtherUserPendingAppIds)))

			# retrieving this users pending app (will remove from main list and add this to on boarding list)
			myPendingApp = self.getMyPendingApp(securityToken, userId)
			myPendingAppIds = [app["app_id"] for app in myPendingApp]

			self.LOGGER.info("found this users application list which is in pending state >>> {result}".format(result = str(myPendingAppIds)))

			myExclAppIds = list(set(myApprovedAppIds + myOtherUserPendingAppIds))

			self.LOGGER.info("final exclusion app id list >>> {exclList}".format(exclList = str(myExclAppIds)))

			# removing all exclusion list from main dbaas app list
			myOnBoardingApp = []
			for app in myAlldbaasApplists:
				if not(app["APP_ID"] in myExclAppIds) :
					if app["APP_ID"] in myPendingAppIds:
						myStatus = "Pending"
						myReason = self.getAppDetailedStatus(securityToken, app["APP_ID"])
					else:
						myStatus = "Available"
						myReason = ""
					app.update({"STATUS" : myStatus, "reason" : myReason})
					myOnBoardingApp.append(app)
					self.LOGGER.info("adding app to on boarding list >>> {app}".format(app = str(app)))

			self.LOGGER.info("total {tot} app is ready for on boarding, returning app list >>> {result}".format(tot = str(len(myOnBoardingApp)), result = str(myOnBoardingApp)))

			return myOnBoardingApp

		except Exception as error:
			self.LOGGER.error("an error occurred while retrieving application list for on boarding >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAllAppEnvInUse(self, securityToken, opco, region, dbTechnology, appId):
		"""
		retrieves list of application and env which is either in process of on boarding or has been successfully onboarded
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"opco" : opco.lower(), "region" : region.lower(), "dbTechnology" : dbTechnology.lower(), "appId" : appId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAllAppEnvInUseSql, myCriteria)

			self.LOGGER.info("db result >>> {result}".format(result = myDBResult))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("an error {error} occurred while retrieving env list in use for app {app} !!!".\
					format(error = myDBResult["message"], app = str(appId)))

			return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error occurred while retrieving application env in use >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAllAppsEnv4OnBoarding(self, securityToken, opco, region, dbTechnology, appName, userId):
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', appName, ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myAllAppEnvFromDbaas = self.dbaasGetAllAppEnvs(securityToken, opco, region, dbTechnology, appName)

			if self.isAppExistsByName(securityToken, appName):
				
				myAppId = self.getAppIdByName(securityToken, appName)

				myAppEnvInUse = self.getAllAppEnvInUse(securityToken, opco, region, dbTechnology, myAppId)

				myAppEnvInUseList = [env["env"] for env in myAppEnvInUse]

			else:
				myAppEnvInUseList = []

			self.LOGGER.debug("env from dbaas <{dbaasEnv}>, env in use in CICD repo <{env}>".format(dbaasEnv = str(myAllAppEnvFromDbaas), env = str(myAppEnvInUseList)))

			myAvailableEnv = [env for env in myAllAppEnvFromDbaas if env["ENV"].lower() not in myAppEnvInUseList]

			self.LOGGER.info("returning >> {result}".format(result = str(myAvailableEnv)))

			return myAvailableEnv

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAllAppDetail(self, securityToken, opco, region, status):
		# Returns all app for a given opco, region and status from CICD repository
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', opco, ',', region, ',', status])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"opco" : opco.lower(), "region" : region.lower(), "status" : status}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAllApp4OpcoRegionStatusSql, myCriteria)

			self.LOGGER.info("got dbresult >>> {result}".format(result = str(myDBResult)))
			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("error retrieving app details for app >>> {appId}".format(appId = str(appId)))
			
			myAppDetails = []
			
			for app in myDBResult["data"]:
				myApp = app
				myApp.update({"env" : []})
				# retrieving all env for this app
				myAllEnvs = self.getAppEnvDetails(securityToken, app["app_id"])

				self.LOGGER.info("env details found for app {app} >>> {result}".format(app = str(app["app_id"]), result = str(myAllEnvs)))

				#if myDBResult["status"] == self.Globals.unsuccess:
				#	raise ValueError("error retrieving app details for app >>> {appId}".format(appId = str(app["_id"])))

				myAppEnv = []
				for env in myAllEnvs:
					# retrieving all contacts for this app env
					myAllContacts = self.getAnEnvContactDetails(securityToken, app["app_id"], env["env"])
					
					self.LOGGER.info("env contact details found for app {app} >>> {result}".format(app = "".join([str(app["app_id"]), ".", env["env"]]), result = str(myAllContacts)))

					myEnv = env
					# removing app_id from myEnv
					myEnv.pop("app_id")
					# removing app_id and env from cotacts
					[contact.pop("app_id") for contact in myAllContacts]
					[contact.pop("env") for contact in myAllContacts]
					myEnv.update({"contacts" : myAllContacts})
					myAppEnv.append(myEnv)
					print("app env >>>", myAppEnv)

				myApp["env"].append(myAppEnv)
				print("app all env >>>", myApp)
				myAppDetails.append(myApp)
				print("app all app details >>>", myAppDetails)
				
				self.LOGGER.info("found app env details >>> {envDetails}".format(envDetails = str(myEnv)))
				self.LOGGER.info("found app details >>> {appDetails}".format(appDetails = str(myAppEnv)))
				self.LOGGER.info("found all app details >>> {appDetails}".format(appDetails = str(myAppDetails)))

			return myAppDetails

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAllPendingAppExclMe(self, securityToken, opco, region, userId):
		# Returns all pending app for a given opco/region excluding given userid app
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', opco, ',', region])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"opco" : opco.lower(), "region" : region.lower(), "userId" : userId.lower(), "status" : self.Globals.STATUS_PENDING}
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAllAppExclUsrSql, myCriteria)

			if myDBResult["status"] == self.Globals.success:
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getMyPendingApp(self, securityToken, userId):
		# Returns all pending app env waiting for approval for a given userId
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"userId" : userId.lower(), "status" : self.Globals.STATUS_PENDING}
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getMyAppByStatusSql, myCriteria)

			if myDBResult["status"] == self.Globals.success:
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAppApproverIds(self, securityToken):
		"""
		Returns all approver network id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			"""
			# would need all owner approver and admin approved
			# retrieving all owner approver
			myAppEnvContactArg = {"appId" : appId, "env" : appEnv}
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getValidAppEnvOwnerIds, myAppEnvContactArg)

			myApproverIds = []

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				for id in myDBResult["data"]:
					myApproverIds.append(id["contact_id"].lower())

			# retrieving all admin id for this app
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getValidAppEnvAdminGrp, myAppEnvContactArg)
			myAdminGrpList = []
			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				for grp in myDBResult["data"]:
					myAdminGrpList.append(grp["contact_id"])

			myAdminIds = self.util.getAdGroupMemberIds(myAdminGrpList)

			[myApproverIds.append(adminId.lower()) for adminId in myAdminIds]

			#removing duplicate ids
			"""
			# pulling data from valid_approver, all id in this table can approve all apps
			myCriteria = {}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppEnvApproverSql, {})

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("an error occurred while retrieving approver id list >>> {error}".format(error = myDBResult["message"]))

			return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAppIdByName(self, securityToken, appName):
		"""
		returns app (name) id from CICD repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', appName])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppExistsByName(securityToken, appName)):
				raise ValueError("Invalid app {app}".format(app = appName))

			myCriteria = {"appName" : appName}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppIdByNameSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"][0]:
				return myDBResult["data"][0]["app_id"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAppStatusById(self, securityToken, appId):
		"""
		returns app (id) status from repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppExists(securityToken, appId)):
				raise ValueError("Invalid app {app}".format(app = appId))

			myCriteria = {"appId" : appId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppStatusByIdSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"][0]:
				return myDBResult["data"][0]["status"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAppStatusByName(self, securityToken, appName):
		"""
		returns app (name) status from repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', appName])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppExistsByName(securityToken, appName)):
				raise ValueError("Invalid app {app}".format(app = appName))

			myCriteria = {"appName" : appName}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppStatusByNameSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"][0]:
				return myDBResult["data"][0]["status"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployEnvOrder(self, securityToken, appId):
		"""
		returns app deploy env order (array) from repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppExists(securityToken, appId)):
				raise ValueError("Invalid app id {appId}".format(appId = str(appId)))

			myCriteria = {"appId" : appId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployEnvOrderSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"][0]:
				return myDBResult["data"][0]["deploy_env_order"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAppEnvStatus(self, securityToken, appId, env):
		"""
		returns app (id) env status from repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppEnvExists(securityToken, appId, env)):
				raise ValueError("Invalid app id/env {appId}".format(appId = "".join([str(appId), ",", env])))

			myCriteria = {"appId" : appId, "appEnv" : env}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppEnvStatusSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"][0]:
				return myDBResult["data"][0]["status"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAppEnvStatusByName(self, securityToken, appName, env):
		"""
		returns app (name) env status from repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', appName, ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppEnvExistsByName(securityToken, appName)):
				raise ValueError("Invalid app {app}".format(app = "".join([appName, ",", env])))

			myCriteria = {"appName" : appName, "appEnv" : env}
			
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppEnvStatusByNameSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"][0]:
				return myDBResult["data"][0]["status"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAnEnvDetails(self, securityToken, appId, env):
		"""
		returns app env details from repository for a gien app id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppEnvExists(securityToken, appId, env)):
				raise ValueError("Invalid app id/env {appId}".format(appId = "".join([str(appId), ",", env])))

			myCriteria = {"appId" : appId, "appEnv" : env}
			
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAnEnv4AppSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAppEnvDetails(self, securityToken, appId):
		"""
		returns all env details for a given app id from repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppExists(securityToken, appId)):
				raise ValueError("Invalid app id {appId}".format(appId = str(appId)))

			myCriteria = {"appId" : appId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAllEnv4AppSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def getAnEnvContactDetails(self, securityToken, appId, env):
		"""
		returns all contact information for a given app and its env
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppEnvExists(securityToken, appId, env)):
				raise ValueError("Invalid app id/env {appId}".format(appId = "".join([str(appId), ",", env])))

			myCriteria = {"appId" : appId, "env" : env}
			
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getContacts4AppEnvSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAnAppContactDetails(self, securityToken, appId):
		"""
		returns all contact details for a given app id from cicd repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppExists(securityToken, appId)):
				raise ValueError("Invalid app id {appId}".format(appId = str(appId)))

			myCriteria = {"appId" : appId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAllContacts4AppSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def getAnAppDetails(self, securityToken, appId):
		"""
		returns an app details
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppExists(securityToken, appId)):
				raise ValueError("Invalid app id {appId}".format(appId = str(appId)))

			myCriteria = {"appId" : appId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAnAppSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"][0]:
				return myDBResult["data"][0]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAnAppDetailsByName(self, securityToken, appName):
		"""
		returns an app details for given application name
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appName)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppExistsByName(securityToken, appName)):
				raise ValueError("Invalid application {app}".format(appId = str(appName)))

			myCriteria = {"appName" : appName}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAnAppByNameSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"][0]:
				return myDBResult["data"][0]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getPendingAppContacts(self, securityToken, appId, env):
		"""
		returns all app env contacts in pending state for a given app and env
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppEnvExists(securityToken, appId, env)):
				raise ValueError("Invalid app id/env {appId}".format(appId = "".join([str(appId), ",", env])))

			myCriteria = {"appId" : appId, "env" : env, "status" : self.Globals.STATUS_PENDING}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getContacts4AppEnvStatusSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"]:
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAllPendingEnv4App(self, securityToken, appId):
		"""
		returns all env in pending state for a given app
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppExists(securityToken, appId)):
				raise ValueError("Invalid app id {appId}".format(appId = str(appId)))

			myCriteria = {"appId" : appId, "status" : self.Globals.STATUS_PENDING}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppEnv4StatusSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"]:
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAppDetailedStatus(self, securityToken, appId):
		"""
		returns app with its detailed status (readable)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppExists(securityToken, appId)):
				raise ValueError("Invalid app id {appId}".format(appId = str(appId)))

			myAppStatus = self.getAppStatusById(securityToken, appId)
			if myAppStatus == self.Globals.STATUS_ACTIVE:
				return 'App is in Valid state'

			# checking if any env is in pending state
			myPendingEnvData = self.getAllPendingEnv4App(securityToken, appId)

			if myPendingEnvData:
				# we found atleast 1 app env in pending state
				myPendingEnv = [env['env'] for env in myPendingEnvData]
				return 'Env is in pedning state >> {env}'.format(env = str(myPendingEnv))

			# there are no pending env for this app, checking if we got all minimum env for this app
			myAllEnvData = self.getAppEnvDetails(securityToken, appId)
			myAllEnvList = [env['env'] for env in myAllEnvData]
			
			if not( self.Globals.ENV_PROD in myAllEnvList and all(env in myAllEnvList for env in self.Globals.ENV_LOWER)):
				# we have missing minimum env for this app (we need 1 prod and atleast 1 lower env)
				return 'Atleast 1 non-prod and prod env is required, got >> {got}'.format(got = str(myAllEnvList))

			# we reached here because app status is in pending state and app passed all validation to become active
			return 'ready for approval'

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getMyAppListWReason(self, securityToken, userId, appStatus = None):
		"""
		returns list of all app with reason (detailed status) for a given userid and status, if status is not passed will return all app
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', userId, ',', str(appStatus)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if appStatus:
				# retrieving users all app for a given status
				myCriteria = {"userId" : userId.lower(), "status" : appStatus}
				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getMyAppByStatusSql, myCriteria)				
			else:
				# retrieving users all app (all status)
				myCriteria = {"userId" : userId.lower()}
				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getMyAppSql, myCriteria)				
		
			self.LOGGER.info('got db results >>> {result}'.format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError('error {error} retrieving app list for user >>> {user}'.format(user = str(userId), error = self.Globals.message))

			if "data" in myDBResult and myDBResult["data"]:
				# found app, updating detailed status 
				for app in myDBResult["data"]:
					myDetailedStatus = self.getAppDetailedStatus(securityToken, app["app_id"])
					app.update({"status" : myDetailedStatus})

				self.LOGGER.info('returning pending app list for user {user} >>> {appLists}'.format(user = userId, appLists = str(myDBResult["data"])))
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getPendingEnv4App(self, securityToken, appId):
		"""
		returns list all env in pending state for a given app
		self.getAppEnv4StatusSql = "SELECT env.* FROM app.app_env env WHERE env.app_id = %(appId)s AND env.status = %(status)s" 

		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ",", str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"appId" : appId, "status" : self.Globals.STATUS_PENDING}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppEnv4StatusSql, myCriteria)
			
			self.LOGGER.info('got db results >>> {result}'.format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError('error {error} retrieving pending app list'.format(error = self.Globals.message))

			if "data" in myDBResult and myDBResult["data"]:
				# found env in pedning state for this app
				self.LOGGER.info('returning all pending env list for app {app} >>> {pendingList}'.format(app = str(appId), pendingList = str(myDBResult["data"])))
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getPendingEnv4OpcoRegion(self, securityToken, opco, region):
		"""
		returns list of all app and its env in pending state
		self.getAppEnv4StatusSql = "SELECT env.* FROM app.app_env env WHERE env.app_id = %(appId)s AND env.status = %(status)s" 

		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ",", opco, ",", region])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"opco" : opco.lower(), "region" : region.lower(), "status" : self.Globals.STATUS_PENDING}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAllAppEnv4OpcoRegionStatusSql, myCriteria)
			
			self.LOGGER.info('got db results >>> {result}'.format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError('error {error} retrieving pending app list'.format(error = self.Globals.message))

			if "data" in myDBResult and myDBResult["data"]:
				# found app in pedning state
				self.LOGGER.info('returning all pending app list >>> {pendingList}'.format(pendingList = str(myDBResult["data"])))
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isValidApprover(self, securityToken, userId):
		"""
		check if this network id exists in valid approver
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"userId" : userId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isValidApproverSql, myCriteria)

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			raise error

	def getMyAppForApproval(self, securityToken, opco, region, userId):
		"""
		returns all app which is available for approval for a given user id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', opco, ',', region, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# we need to validate if a given userid is valid approver, if yes will return all pending app for approval
			if self.isValidApprover(securityToken, userId):
				# this is a valid approver (approver is DBA and authorized to approve all pending app/env), returning all application in pending state
				self.LOGGER.info('approver {userId} is a valid approver'.format(userId = userId))

				myDBResult = self.getPendingEnv4OpcoRegion(securityToken, opco, region)

				self.LOGGER.info('returning pending app list for user {user} >>> {pendingList}'.format(user = userId, pendingList = str(myDBResult)))

				return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	"""
	***** CICD Repo method (get data) ends
	""" 

	""" 
	***** dbaas Method starts, these methods are wrapper for dbaas methods ***** 
	"""

	def dbaasGetAllApps(self, securityToken, opco, region):
		"""
		returns all application for a given opco/region
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', opco, ',', region ])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "opco" : opco, "region" : region}

			myDBResult = self.dbaas.getAllApplications(**mydbaasArgs)

			self.LOGGER.info("returning applications for this request >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetAllAppEnvs(self, securityToken, opco, region, dbTechnology, appName):
		"""
		returns all application for a given opco/region
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', appName ])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "opco" : opco, "region" : region, "dbTechnology" : dbTechnology, "appName" : appName}

			myDBResult = self.dbaas.getAllAppEnv(**mydbaasArgs)

			self.LOGGER.info("returning all env for application {app} >>> {result}".format(app = "".join([opco,'.',region,'.',dbTechnology,'.',appName]), result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetAllDBInst(self, securityToken, appName, opco, region, dbTechnology, env):
		"""
		returns all db for a given db region/region/dbTechnology/env
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "appName" : appName, "opco" : opco, "region" : region, "dbTechnology" : dbTechnology, "env" : env}

			myDBResult = self.dbaas.getAllDBInstances(**mydbaasArgs)

			self.LOGGER.info("returning databases for this request >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetOraDBSchemas(self, securityToken, appName, opco, region, hostName, dbInstance, dbTechnology, env):
		"""
		returns all db/schemas for a Oracle db dbTechnology, opco, region and environment using dbaas 
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', dbInstance])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			mydbaasArgs = {
				"securityToken" : securityToken, 
				"appName" : appName, 
				"opco" : opco, 
				"region" : region, 
				"hostName" : hostName, 
				"dbInstance" : dbInstance, 
				"dbTechnology" : dbTechnology, 
				"env" : env
			}

			myDBResult = self.dbaas.getOraDBSchemas(**mydbaasArgs)

			self.LOGGER.info("returning database/schemas for this request >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetAppInfo(self, securityToken, opco, region, appName):
		"""
		returns application info for a given opco/region/application name
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', opco, ',', region, ',', appName])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "opco" : opco, "region" : region, "appName" : appName}
			myDBResult = self.dbaas.getAppInfo(**mydbaasArgs)

			self.LOGGER.info("returning app id this request >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetDBInstURI(self, securityToken, hostName, dbInstance, dbTechnology):
		"""
		returns connect string for a given database/db instance 
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', hostName, ',', dbInstance, ',', dbTechnology])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "hostName" : hostName, "dbInstance" : dbInstance, "dbTechnology" : dbTechnology}
			myDBResult = self.dbaas.getDBConnectStr(**mydbaasArgs)

			self.LOGGER.info("returning connect string for this request >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetDBIURIWoHost(self, securityToken, dbInstance, dbTechnology):
		"""
		returns connect string for a given database/db instance 
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',',dbInstance, ',', dbTechnology])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "dbInstance" : dbInstance, "dbTechnology" : dbTechnology}
			
			myDBResult = self.dbaas.getDBConnectStrWoHost(**mydbaasArgs)

			self.LOGGER.info("returning connect string for this request >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetOraDBSchemaObjs(self, securityToken, dbInstance, schemaName):
		"""
		returns all Oracle schema objects for a given database/db instance and schema/dbs 
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',',dbInstance, ',', schemaName])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "dbInstance" : dbInstance, "schemaName" : schemaName}
			myDBResult = self.dbaas.getOracSchemaObjs(**mydbaasArgs)

			self.LOGGER.info("returning all schema objects for {dbSchema} >>> {result}".format(dbSchema = "".join([dbInstance, ".", schemaName]), result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetOraSchemaRoles(self, securityToken, dbInstance, schemaName):
		"""
		returns schema role for a given database/db instance and schema/dbs 
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',',dbInstance, ',', schemaName])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "dbInstance" : dbInstance, "schemaName" : schemaName}
			myDBResult = self.dbaas.getOraSchemaRoles(**mydbaasArgs)

			self.LOGGER.info("returning all schema roles for {dbSchema} >>> {result}".format(dbSchema = "".join([dbTechnology, ".", dbInstance, ".", schemaName]), result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetOraSysRoles(self, securityToken, dbInstance):
		"""
		returns sys roles for a given database/db instance 
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',',dbInstance])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "dbInstance" : dbInstance}
			myDBResult = self.dbaas.getOraSysRoles(**mydbaasArgs)

			self.LOGGER.info("returning all sys roles for {db} >>> {result}".format(db = "".join([dbInstance]), result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	""" 
	***** dbaas Method ends *****
	"""

if __name__ == "__main__":
	print("testing cicd repo class method ....")
	sec = Security()
	mySecToken = sec.authenticate('DMZPROD01\\svc-dev-deploy-app','eXokNzl5NEUzOWdXNCkp')
	repo = Repository(mySecToken)

	"""
	print("executing dbaasGetOraDBSchemas >>> ")
	myDbSchemas = repo.dbaasGetOraDBSchemas(mySecToken, myDbInstanceName)
	print("all schemas for Oracle database {dbInstance} >>> {schemas}".format(dbInstance = myDbInstanceName, schemas = str(myDbSchemas)))
	print("completed dbaasGetOraDBSchemas.")

	print("executing dbaasGetOraDBSchemaObjs >>> ")
	mySchemaObjs = repo.dbaasGetOraDBSchemaObjs(mySecToken, myDbInstanceName, mySchemaName)
	print("all schemas for database {dbInstance} >>> {schemas}".format(dbInstance = myDbInstanceName, schemas = str(mySchemaObjs)))
	print("completed dbaasGetOraDBSchemaObjs.")

	print("executing dbaasGetOraSchemaRoles >>> ")
	mySchemaRoles = repo.dbaasGetOraSchemaRoles(mySecToken, myDbInstanceName, mySchemaName)
	print("all schemas roles for database {dbInstance} >>> {schemas}".format(dbInstance = myDbInstanceName, schemas = str(mySchemaRoles)))
	print("completed dbaasGetOraSchemaRoles.")

	print("executing dbaasGetOraSysRoles >>> ")
	mySysRoles = repo.dbaasGetOraSysRoles(mySecToken, myDbInstanceName)
	print("all sys roles for database {dbInstance} >>> {result}".format(dbInstance = myDbInstanceName, result = str(mySysRoles)))
	print("completed dbaasGetOraSysRoles.")
	"""

	# create a new app
	#repo.onBoardCicdApp(mySecToken, 'Test', 'NAM', 'MARSH','Oracle','DEV','<connect_str>','oltp551')
	# connString, dbInstance, dbSchema, notificationDL, contactList, contactType	
	# approve app
	# get database name for db dbTechnology
	# get all schemas for a given dbInstance
	# get all roles for a dbInstance
	# get all roles for schema
	
	# onboard schemas

	myAppName = 'Test'
	mySchemaName = 'MWAY_ETL_TEST_OWNER'
	myRegion = 'nam'
	myOpco = 'marsh'
	myDBTechnology = 'Oracle'
	myTech = 'oracle'
	myEnv = 'dev'
	myUserId = 'u1167965'

	print('retrieving all pending app from CICD (executing getAllAppDetail)>>> {app}'.format(app = "".join([myOpco, ".", myRegion, ".", repo.Globals.STATUS_PENDING])))
	myAllAppDetails = repo.getAllAppDetail(mySecToken, myOpco, myRegion, repo.Globals.STATUS_PENDING)
	print('all app details >>>', myAllAppDetails)

	print('retrieving all app available for onboarding (executing getAllApps4OnBoarding)>>> {app}'.format(app = "".join([myOpco, ".", myRegion])))
	myAllApp4OnBoarding = repo.getAllApps4OnBoarding(mySecToken, myOpco, myRegion, myUserId)
	print('all app available for onboarding >>>', myAllApp4OnBoarding)

	myOwnerIdList = ['u107854','test.cicd']
	myNotifyDLList = ['MARSH_APP_TEST_APPOWNER_DL', 'MARSH_APP_TEST_APPSUPP_DL', 'MARSH_APP_TEST_BUSOWNER_DL']

	print("retrieving all application for >>> {} (execuring dbaasGetAllApps)".format(''.join([myOpco.upper(),'.', myRegion.upper()])))
	myAllApps = repo.dbaasGetAllApps(mySecToken, myOpco.upper(), myRegion.upper())
	print('all applications >>>', myAllApps)
	print(" <<< completed >>>")

	myCansysAppDetails = [app for app in myAllApps if app["APP_NAME"] == "CANSYS"]

	myAppName = myCansysAppDetails[0]["APP_NAME"]
	myAppId = myCansysAppDetails[0]["APP_ID"]
	myNotifyEmail = myCansysAppDetails[0]["SUPPORT_EMAIL"]

	print("retrieving all db instances for >>> {} (execuring dbaasGetAllDBInst)".format(''.join([myOpco.upper(),'.', myRegion.upper()])))
	myAllDbInstances = repo.dbaasGetAllDBInst(mySecToken, myAppName.upper(), myOpco.upper(), myRegion.upper(), myDBTechnology, myEnv.upper())

	for dbInstance in myAllDbInstances:
		print(dbInstance)
	print(" <<< completed >>>")

	myDbInstance = "OLTD147"
	myHostName = "usdfw23db26v"

	print("executing dbaasGetDBInstURI >>> ")
	myDBResult = repo.dbaasGetDBInstURI(mySecToken, myHostName, myDbInstance, myDBTechnology)
	print("db result >>>", myDBResult)
	myConnectStr = myDBResult["connectStr"]
	print("connect string for {dbInst} >>> {result}".format(dbInst = "".join([myHostName, ".", myDbInstance, ".", myDBTechnology]), result = myConnectStr))
	print(" <<< completed >>>")

	print("retrieving all db/schemas for >>> {} (execuring dbaasGetOraDBSchemas)".format(''.join([myOpco.upper(),'.', myRegion.upper(), '.', myAppName,'.', myHostName, '.', myDBTechnology, '.', myEnv, '.', myDbInstance])))
	myAllDbSchemas = repo.dbaasGetOraDBSchemas(mySecToken, myAppName.upper(), myOpco.upper(), myRegion.upper(), myHostName, myDbInstance, myDBTechnology, myEnv.upper())

	for db in myAllDbSchemas:
		print(db)
	print(" <<< completed >>>")
	
	print("executing getDBSchema4OnBoarding >>> ")
	myAvailDbSchemas = repo.getDBSchema4OnBoarding(mySecToken, myAppName, myOpco.upper(), myRegion.upper(), myHostName, myDbInstance, myDBTechnology, myEnv.upper())
	print("schemas available for Oracle database {dbInstance} >>> {schemas}".format(dbInstance = myDbInstance, schemas = str(myAvailDbSchemas)))
	print("completed getDBSchema4OnBoarding.")

	mySchemas = ['ACT','ADMIN','BINDER','CERT','CLAIM']

	print("validating db instance/schema")
	myResult = repo.isValidDBSchema(mySecToken, myOpco, myRegion, myAppName, myHostName, myDBTechnology, myDbInstance, mySchemas, myEnv)
	print('db instance/schema validation >>>', myResult)
	
	print("on boarding app >> {app}".format(app = "".join([myOpco,".",myRegion,".",myAppName, " (", str(myAppId), ") .", myDBTechnology, ".", myHostName, ".", myDbInstance, " - ", str(mySchemas) ])))
	try:
		myResult = repo.onBoardCicdApp(mySecToken, myAppId, myAppName, myRegion, myOpco, myDBTechnology, myEnv, myHostName, myConnectStr, myDbInstance, mySchemas, myOwnerIdList, [myNotifyEmail], myUserId)
		print('on boarding app result >>>', myResult)
	except Exception as error:
		print("error while onboarding >>>", error)

	print(" <<<on boarding completed >>>")

	#myAppId = myResult["appId"]
	print('performing approval for app [{app}] by user [{user}]'.format(app = myAppName, user = myUserId))
	try:
		myResult = repo.approveAppEnv(mySecToken, myAppId, myEnv, myUserId)
	except Exception as error:
		print('error >> ', error)

	print('approval result >>>', myResult)
	print(" <<< completed >>>")

	print('retrieving pending reason for app >>> {app}'.format(app = myAppId))
	myPendingReason = repo.getAppDetailedStatus(mySecToken, myAppId)
	print('reason >>', myPendingReason)
	print(" <<< completed >>>")

	print('retrieving all pending app for user >>>', myUserId)
	myPendingApp = repo.getMyAppListWReason(mySecToken, myUserId, repo.Globals.STATUS_PENDING)
	print('pending app >>', myPendingApp)

	print('retrieving all app for user >>>', myUserId)
	myAllApp = repo.getMyAppListWReason(mySecToken, myUserId)
	print('all app list >>', myAllApp)

	print('populating valid approver list')
	myResult = repo.populateValidApprover(mySecToken, myUserId)
	print('result >>>', str(myResult))

	print('retrieving all approval userid ')
	myResult = repo.getAppApproverIds(mySecToken)
	print('all approver id >>>', str(myResult))

	print('retrieving all app for approval for userid >>> {user} '.format(user = myUserId))
	myResult = repo.getMyAppForApproval(mySecToken, myOpco, myRegion, myUserId)
	print('result >>>', str(myResult))

	myAppName =- 'ADWRAP'
	print("retrieving dbaas application detail for {app}".forma(app = myAppName))
	myResult = self.getdbaasAppInfo(securityToken, myOpco, myRegion, myAppName)
	print('dbaas app detail >>', myResult)