from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.security import Security
from com.mmc.common.infrastructure import Infrastructure
#from com.mmc.common.globals import Globals
from com.mmc.cicd.cicd_globals import CICDGlobals
from com.mmc.common.jira_util import JiraUtility

from com.mmc.database.postgres_core import PGCore
from com.mmc.database.oracle_core import OracleCore
from com.mmc.database.mongo_core import MongoCore
from com.mmc.database.dbaas import Dbaas

from com.mmc.cicd.deploy_files_parser import Parser

import logging, logging.config, sys, json

class Repository(object, metaclass=Singleton):

	def __init__(self, securityToken):
		# need pg_background_worker extension of autonomou transaction
		# software url: https://github.com/vibhorkum/pg_background
		# example: https://blog.dalibo.com/2016/08/19/Autonoumous_transactions_support_in_PostgreSQL.html
		try:
			self.util = Utility()
			self.sec = Security()
			self.infra = Infrastructure()
			self.Globals = CICDGlobals()
			#self.Globals = ()

			self.sec.validateSecToken(securityToken)

			self.parser = Parser(securityToken)

			self.LOGGER = logging.getLogger(__name__)

			#self.ENVIRONMENT = self.util.getACopy(self.infra.environment)
			self.ADMIN_GROUP = self.util.getACopy(self.infra.environment["boot"]["adminSrvcGroup"])
			self.MAX_PENDING_APP_PER_USER = self.Globals.CICD_INFRA_ONBOARD_VAR["maxOnboardingAppPerUser"]

			self.ENV = self.util.getEnvKeyVal("ENV")

			# we would need to determine env type either its prod or non-prod, we have got dev/prod. changing it to pro/non-prod
			if self.ENV == "prod":
				myPGEnv = self.ENV
			else:
				myPGEnv = "non-prod"

			# we need repostory info to instantiate PG class
			# https://www.postgresql.org/docs/9.3/libpq-connect.html
			self.PG_REPO = {
				"user" : self.infra.environment["boot"]["repository"][myPGEnv]["user"],
				"userEncPass" : self.infra.environment["boot"]["repository"][myPGEnv]["userEncPass"],
				"host" : self.infra.environment["boot"]["repository"][myPGEnv]["host"],
				"port" : self.infra.environment["boot"]["repository"][myPGEnv]["port"],
				"database" : self.infra.environment["boot"]["repository"][myPGEnv]["db"]
			}
			self.LOGGER.info(f"pg repo connection arg built for env {myPGEnv} >>> {self.PG_REPO}")
			#self.pg = PGCore(securityToken, self.PG_REPO["user"], self.PG_REPO["encPass"],self.PG_REPO["host"], self.PG_REPO["port"], self.PG_REPO["db"])

			self.pg = PGCore(securityToken)
			self.PG_CONN = self.pg.newConnection(securityToken, self.PG_REPO)

			self.dbaas = Dbaas(securityToken)

			self.__initPGRepoSql(securityToken)

			"""
			Following class instatiatioin will return following error, if svc-dev-deploy-app or any service account password is not changed
			in cicd bootstrap.json
				2021-02-18 11:07:57,390 - ERROR - flask_main.post:308:an error occurred while initiating session, error >> An error maximum recursion depth exceeded while calling a Python object occurred instantiating object Repository !!!
				Traceback (most recent call last):
					File "/opt/ansible/app/source/com/mmc/cicd/cicd_repo_pg.py", line 69, in __init__
					self.JiraUtil = JiraUtility(securityToken)
			"""
			self.JiraUtil = JiraUtility(securityToken)

		except Exception as error:
			raise ValueError(f"An error {error} occurred instantiating object Repository")

	def __initPGRepoSql(self, securityToken):
		# initialized all repository sql
		try:
			#select
			trustProxyTab = "app.trusted_proxies"
			sessionTokenTab = "app.session_tokens"
			sessionRequestTab = "app.session_requests"
			appTab = "app.apps"
			appEnvTab = "app.app_envs"
			appEnvContactTab = "app.app_env_contacts"
			approvalTab = "app.approvals"
			eventLogTab = "app.event_logs"
			deployTab = "app.deploy"
			deployCtrlTab = "app.deploy_ctrl"
			deployFilesTab = "app.deploy_files"
			deployTasksTab = "app.deploy_tasks"
			deployEnvTab = "app.deploy_envs"
			deployAttemptsTab = "app.deploy_attempts"
			deployAttemptTasksTab = "app.deploy_attempt_tasks"
			deployObjTab = "app.deploy_objects"
			deployObjHistTab = "app.deploy_obj_history"

			validStatus = self.Globals.STATUS_VALID
			activeStatus = self.Globals.STATUS_ACTIVE
			pendingStatus = self.Globals.STATUS_PENDING

			self.getTrustedProxiesSql = f"SELECT remote_address from {trustProxyTab}"
			self.getSessionDetailsSql = f"""
				SELECT token.session_id session_id, 
					token.user_id user_id,
					token.ts ts,
					token.access_route access_route,
					token.security_token security_token,
					token.status status,
					request.request,
					request.request_end_ts request_end_ts,
					request.elapsed elapsed
				FROM {sessionTokenTab} token, 
					{sessionRequestTab} request 
				WHERE token.session_id = %(sessionId)s 
					AND request.session_id = token.session_id
			"""
			self.isAppExistsSql = f"SELECT COUNT(app_id) as total FROM {appTab} WHERE app_id = %(appId)s" 
			self.isAppExistsByNameSql = f"SELECT COUNT(app_id) as total FROM {appTab} WHERE app_name = %(appName)s" 
			#self.isAppExistsByTagSql = "SELECT COUNT(app_id) as total FROM app.app WHERE app_tag = %(appTag)s" 
			self.isAppEnvExistsSql = f"SELECT COUNT(env.app_id) as total FROM {appEnvTab} env, {appTab} app WHERE app.app_id = %(appId)s AND env.app_id = app.app_id AND env.env = LOWER(%(env)s)" 
			self.isAppEnvIdExistsSql = f"SELECT COUNT(env.app_env_id) as total FROM {appEnvTab} env WHERE env.app_env_id = %(appEnvId)s" 
			self.isAppEnvExistsByNameSql = f"SELECT COUNT(env.app_id) as total FROM {appEnvTab} env, {appTab} app WHERE app.app_name = %(appName)s AND env.app_id = app.app_id AND env.env = LOWER(%(env)s)" 
			#self.isAppEnvExistsByTagSql = "SELECT COUNT(env.app_id) as total FROM app.app_env env, app.app app WHERE app.app_tag = %(appTag)s AND env.app_id = app.app_id AND env.env = %(appEnv)s" 
			self.isAppEnvContactExistsSql = f"SELECT COUNT(app_id) as total FROM {appEnvContactTab} WHERE app_id = %(appId)s AND app_env_id = %(appEnvId)s AND contact_type = LOWER(%(contactType)s) AND contact_id = %(contactId)s "

			# checks if approver exists in valid approver table
			self.isValidApproverSql = "SELECT COUNT(network_id) as total FROM app.valid_approver WHERE network_id = lower(%(userId)s) AND status = '{activeStatus}'".format(activeStatus = self.Globals.STATUS_ACTIVE)

			# checks if this app is ready for approval
			#self.isAppReadyForDeploySql = "SELECT COUNT(app.app_id) as total FROM app.app app WHERE app.app_id = %(appId)s AND app.status = '{activeStatus}'".format(activeStatus = self.Globals.STATUS_ACTIVE)

			# checks if given db instance and schema is already in use
			#self.isDbInstSchemaInUseSql = "SELECT COUNT(app_id) as total FROM app.app_env env, app.app app WHERE env.db_instance = ALL(%(dbInstance)s) and db_schemas @> %(dbSchema)s and app.app_id = env.app_id and app.technology = lower(%(dbTechnology)s) "
			self.isDbInstSchemaInUseSql = f"SELECT COUNT(DISTINCT env.app_id) as total FROM {appEnvTab} env, {appTab} app WHERE env.db_instance = %(dbInstance)s AND env.db_schemas @>  %(dbSchema)s::VARCHAR[] and app.app_id = env.app_id and app.technology = lower(%(dbTechnology)s) "
			# app.app and app.app_env both have db schemas ????
			#self.isDbInstSchemaInUseSql_new = "SELECT COUNT(DISTINCT env.app_id) as total FROM app.app_env env, app.app app WHERE env.db_instance = %(dbInstance)s AND db_schemas @>  %(dbSchema)s::VARCHAR[] and app.app_id = env.app_id and app.technology = lower(%(dbTechnology)s) "

			# returns all available db schema for a given db instance which is not being used by anyother app (not used in on boarding)
			self.getDBSchemaInUseSql = f"""
				SELECT app.db_schemas as db_schemas 
					FROM {appTab} app 
					WHERE app.app_id = %(appId)s
						AND app.opco = LOWER(%(opco)s)
						AND app.region = LOWER(%(region)s)
						AND app.technology = LOWER(%(dbTechnology)s)
			"""
			self.getAppIdByNameSql = f"SELECT app_id FROM {appTab} WHERE app_name = %(appName)s"
			#self.getAppIdByTagSql = "SELECT app_id FROM app.app WHERE app_tag = %(appTag)s"
			self.getAppStatusByIdSql = f"SELECT status FROM {appTab} WHERE app_id = %(appId)s" 
			self.getAppStatusByNameSql = f"SELECT status FROM {appTab} WHERE app_name = %(appName)s" 
			#self.getAppStatusByTagSql = "SELECT status FROM app.app WHERE app_tag = %(appTag)s" 
			self.getAppEnvStatusSql = f"SELECT status FROM {appEnvTab} WHERE app_id = %(appId)s AND env = LOWER(%(env)s)"
			self.getAppEnvIdSql = f"SELECT app_env_id from {appEnvTab} WHERE app_id = %(appId)s and env = LOWER(%(env)s)"

			# app.app
			# return app information for a given app id/app name/status
			self.getAnAppSql = f"SELECT app.* FROM {appTab} app WHERE app.app_id = %(appId)s"
			self.getAnAppByNameSql = f"SELECT app.* FROM {appTab} app WHERE app.app_name = %(appName)s"
			#self.getAnAppByTagSql = "SELECT app.* FROM app.app app WHERE app.app_tag = %(appTag)s"
			#self.getAppListByExtAppIdSql = "SELECT app.* FROM app.app WHERE app.ext_app_id = %(extAppId)s"
			self.getAllApp4StatusSql = f"SELECT app.* FROM {appTab} app WHERE app.status = %(status)s"
			self.getDeployEnvOrderSql = f"SELECT deploy_env_order FROM {appTab} WHERE app_id = %(appId)s"

			# app.app_env
			# return env details for a given app id/ env/status
			self.getAppEnvCount = f"SELECT count(*) FROM {appEnvTab} env WHERE env.app_id = %(appId)s AND env.status in {self.Globals.VALID_STATUS_TUPLE}"

			self.getAllEnv4AppSql = f"SELECT env.* FROM {appEnvTab} env WHERE env.app_id = %(appId)s and env.status in {self.Globals.VALID_STATUS_TUPLE}" 
			self.getAnEnv4AppSql = f"SELECT env.* FROM {appEnvTab} env WHERE env.app_id = %(appId)s AND env.env = LOWER(%(env)s) and env.status in {self.Globals.VALID_STATUS_TUPLE}" 
			self.getAnAppEnvByIdSql = f"SELECT env.* FROM {appEnvTab} env WHERE app_env_id = %(appEnvId)s" 
			self.getAppEnv4StatusSql = f"SELECT env.* FROM {appEnvTab} env WHERE env.app_id = %(appId)s AND env.status = %(status)s" 
			self.getAppPendingEnvSql = f"SELECT env.* FROM {appEnvTab} env WHERE env.app_id = %(appId)s AND LOWER(env.status) like %(pendingKW)s" 
			self.getAppEnvStatusByIdSql = f"SELECT status FROM {appEnvTab} env WHERE env.app_env_id = %(appEnvId)s" 
			
			self.getInactiveEnvCount = f"SELECT COUNT(*) as total FROM {appEnvTab} where app_id = %(appId)s and env like %(inActiveEnv)s"

			# app.app_env_contact
			# returns all contacts for an app
			self.getContacts4AppSql = f"SELECT contact.* FROM {appEnvContactTab} contact WHERE contact.app_id = %(appId)s" 
			self.getContacts4AppEnvSql = f"SELECT contact.* FROM {appEnvContactTab} contact WHERE contact.app_id = %(appId)s AND contact.app_env_id = %(appEnvId)s" 
			#self.getEnvContactOwner = f"SELECT contact.* FROM {appEnvContactTab} contact WHERE contact.app_id = %(appId)s AND contact.app_env_id = %(appEnvId)s AND" 			
			# retrieve all contacts for a given app AND contact status
			self.getContacts4AppStatusSql = f"SELECT contact.* FROM {appEnvContactTab} contact WHERE contact.app_id = %(appId)s AND contact.status = %(status)s" 
			self.getContacts4AppEnvStatusSql = f"SELECT contact.* FROM {appEnvContactTab} contact WHERE contact.app_id = %(appId)s AND contact.app_env_id = %(appEnvId)s AND contact.status = %(status)s" 
			self.getPendingContacts4EnvSql = f"SELECT contact.* FROM {appEnvContactTab} contact WHERE contact.app_id = %(appId)s AND contact.app_env_id = %(appEnvId)s AND lower(contact.status) like %(pendingKW)s" 

			self.getAppEnvContactByType = f"SELECT * FROM {appEnvContactTab} WHERE app_env_id = %(appEnvId)s AND contact_type like %(contactType)s"
			self.getAppEnvAdminGrp = f"SELECT contact_id FROM {appEnvContactTab} WHERE app_id = %(appId)s AND app_env_id = %(appEnvId)s AND contact_type = 'admin_adgrp'"
			self.getValidAppEnvOwnerIds = f"SELECT contact_id FROM {appEnvContactTab} WHERE app_id = %(appId)s AND app_env_id = %(appEnvId)s AND contact_type = 'owner' AND status = '{validStatus}'".format(validStatus = self.Globals.STATUS_VALID)
			self.getValidAppEnvAdminGrp = f"SELECT contact_id FROM {appEnvContactTab} WHERE app_id = %(appId)s AND app_env_id = %(appEnvId)s AND contact_type = 'admin_adgrp' AND status = '{validStatus}'".format(validStatus = self.Globals.STATUS_VALID)

			self.getDeployDataSql = f"SELECT * FROM {deployTab} WHERE deploy_id = %(deployId)s"

			# retrieve all env in use for an app
			self.getAllAppEnvInUseSql = f"""
				SELECT env.env env 
				FROM {appEnvTab} env, {appTab} app 
				WHERE app.app_id = %(appId)s 
					AND env.app_id = app.app_id
					AND env.status NOT IN {self.Globals.INVALID_STATUS_TUPLE} 
			"""
			## approals
			# (converting value to string using cast function it could be done as value::<datatype> as well)
			self.getApprovalRequestIdSql = f"SELECT request_id FROM {approvalTab} WHERE entity_id = CAST( %(entityId)s AS VARCHAR)  and entity_type = %(entityType)s and request_type = %(requestType)s"
			self.getApprovalReqIdsSql = f"SELECT request_id FROM {approvalTab} WHERE ext_reference_id = %(extReferenceId)s AND status = %(status)s" 
			self.getApprovalReqDetailSql = f"SELECT * FROM {approvalTab} WHERE request_id = %(requestId)s"
	
			# app.valid_approver
			# return all admin id from valid approver as app environment on boarding approval
			self.getAppEnvApproverSql = f"SELECT network_id FROM app.valid_approver WHERE status = '{activeStatus}'"
	
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
			self.getAllApp4OpcoRegionTechStatusSql = f"""
				SELECT app.*
					FROM {appTab} app
					WHERE app.opco = LOWER(%(opco)s)
						AND app.region = LOWER(%(region)s)
						AND app.technology = LOWER(%(dbTechnology)s)
						AND app.status = LOWER(%(status)s)
			"""
			self.getAllAppEnv4OpcoRgnTechStatusSql = f"""
				SELECT env.*
					FROM {appTab} app,
						{appEnvTab} env
					WHERE app.opco = LOWER(%(opco)s)
						AND app.region = LOWER(%(region)s)
						AND app.technology = LOWER(%(dbTechnology)s)
						AND app.app_id = env.app_id 
						AND env.status = LOWER(%(status)s)
			"""
			self.getAllPendingAppEnvSql = f"""
				SELECT env.*
					FROM {appTab} app,
						{appEnvTab} env
					WHERE app.opco = LOWER(%(opco)s)
						AND app.region = LOWER(%(region)s)
						AND app.technology = LOWER(%(dbTechnology)s)
						AND app.app_id = env.app_id 
						AND lower(env.status) like LOWER(%(pendingKW)s)
			"""
			# returns all app for given opco/region/technology/status excluding given user's app
			self.getAllAppExclUsrSql = f"""
				SELECT app.* 
					FROM {appTab} app
					WHERE app.opco = LOWER(%(opco)s)
						AND app.region = LOWER(%(region)s)
						AND app.status = LOWER(%(status)s)
						AND app.technology = LOWER(%(dbTechnology)s)
						AND not exists (
							SELECT 'x' 
								FROM {appEnvContactTab} contact
									WHERE app.app_id = contact.app_id AND 
									contact.contact_id IN  %(adGroupArray)s
						)
			"""
			# return users app for a given status
			self.getMyAppByStatusSql = f"""
				SELECT app.*
					FROM {appTab} app
					WHERE app.status = LOWER(%(status)s)
						AND app.opco = LOWER(%(opco)s)
						AND app.region = LOWER(%(region)s)
						AND app.technology = LOWER(%(dbTechnology)s)
						AND app.app_id IN (
							SELECT DISTINCT app_id 
								FROM {appEnvContactTab}
								WHERE contact_id IN %(contactIdList)s 
									AND status = LOWER(%(status)s)
						)
			"""

			# return an users all apps
			self.getMyAppSql = f"""
				SELECT app.*
					FROM {appTab} app
					WHERE app.opco = LOWER(%(opco)s)
						AND app.region = LOWER(%(region)s)
						AND app.technology = LOWER(%(dbTechnology)s)
						AND app.app_id IN (
							SELECT DISTINCT app_id FROM {appEnvContactTab}
								WHERE contact_id IN %(lower(contactIdList))s
							)
			"""

			self.getMyAppEnvByStatusSql = f"""
				SELECT app.*, env.env as env, env.status env_status, env.db_instance as db_instance, env.db_schemas as db_schemas, env.notification_dl as notification_dl
					FROM {appTab} app, {appEnvTab} env
					WHERE   env.status = LOWER(%(status)s)
						AND env.app_id = app.app_id
						AND env.app_env_id IN (
							SELECT DISTINCT app_env_id FROM {appEnvContactTab} contact
								WHERE contact.contact_id = %(userId)s
									AND contact.app_id = app.app_id
									AND contact.status = '{validStatus}'
						)
			"""
			
			self.getCurrIdSql = "SELECT currval(pg_get_serial_sequence(%(tableName)s, %(pkColumn)s));"

			### Deployment

			# deploy; checks if this deployment exists
			self.isDeploymentExistsSql = f"SELECT COUNT(deploy_id) as total FROM {deployTab} deploy WHERE deploy_id = %(deployId)s"
			self.isJiraInUseForDeploySql = f"SELECT COUNT(jira_issue_id) as total FROM {deployTab} deploy WHERE jira_issue_id = %(jiraIssueId)s"

			# deploy; checks if this deployment ctrl exists
			self.isDeploymentCtrlExistsSql = f"SELECT COUNT(deploy_ctrl_id) as total FROM {deployCtrlTab} deploy WHERE deploy_ctrl_id = %(deployCtrlId)s"

			# deploy; checks if deploy object id exists
			self.isDeployObjIdExistsSql = f"SELECT COUNT(deploy_obj_id) as total from {deployObjTab} WHERE deploy_obj_id = %(deployObjId)s"
			self.isDeployObjExistsSql = f"SELECT COUNT(deploy_obj_id) as total from {deployObjTab} WHERE obj_name = %(objName)s AND obj_type = %(objType)s AND obj_owner = %(objOwner)s AND schema = %(schema)s AND env = %(env)s AND db_instance = %(dbInstance)s AND db_technology = %(dbTechnology)s"
			self.getDeployObjIdSql = f"SELECT deploy_obj_id from {deployObjTab} WHERE obj_name = %(objName)s AND obj_type = %(objType)s AND obj_owner = %(objOwner)s AND schema = %(schema)s AND env = %(env)s AND db_instance = %(dbInstance)s AND db_technology = %(dbTechnology)s"
			self.getDeployObjIdInfoSql = f"SELECT * from {deployObjTab} WHERE deploy_obj_id = %(deployObjId)s"

			# checks if given db instance and schema is already in use
			#self.isDbInstSchemaInUseSql = "SELECT COUNT(app_id) as total FROM app.app_env env, app.app app WHERE env.db_instance = ALL(%(dbInstance)s) and db_schemas @> %(dbSchema)s and app.app_id = env.app_id and app.technology = lower(%(dbTechnology)s) "
			self.isDbInstSchemaInUseSql = f"SELECT COUNT(DISTINCT env.app_id) as total FROM {appEnvTab} env, {appTab} app WHERE env.db_instance = %(dbInstance)s AND env.db_schemas @>  %(dbSchema)s::VARCHAR[] and app.app_id = env.app_id AND env.status IN {self.Globals.VALID_STATUS_TUPLE} AND app.technology = lower(%(dbTechnology)s) "

			# deploy; find active/in-active deploy control id for a given deployment id
			self.getDeployCtrlIdSql = f"SELECT deploy_ctrl_id from {deployCtrlTab} ctrl WHERE deploy_id = %(deployId)s and status = %(status)s"

			# deploy; get deploy control data
			self.getDeployCtrlSql = f"SELECT * FROM {deployCtrlTab} ctrl where deploy_ctrl_id = %(deployCtrlId)s"

			# deploy; get deploy control status
			self.getDeployCtrlStatusSql = f"SELECT status FROM {deployCtrlTab} ctrl where deploy_ctrl_id = %(deployCtrlId)s"

			# deploy; get new task group id for a given deploy id (deploy_id_001)
			self.getNewDeployCtrlSql = f"SELECT CONCAT(%(deployId)s, '_', LPAD(CAST((COUNT(deploy_id) + 1) AS VARCHAR),3,'0') ) new_deploy_ctrl_id FROM {deployCtrlTab} WHERE deploy_id = %(deployId)s"

			#deploy; get deployment detail
			self.getDeployDetailSql = f"SELECT * FROM {deployTab} deploy WHERE deploy_id = %(deployId)s"
	
			# returns all deploy files for a given deployment id
			self.getDeployFilesSql = f"SELECT * FROM {deployFilesTab} WHERE deploy_id = %(deployId)s and status = %(status)s"

			# deploy; deploy_envs, get deployment environment data 
			self.getDeployEnvDataSql = f"SELECT * FROM {deployEnvTab} WHERE deploy_id = %(deployId)s AND app_env_id = %(appEnvId)s"
			self.getDeployEnvStatusSql = f"SELECT status FROM {deployEnvTab} WHERE deploy_id = %(deployId)s AND app_env_id = %(appEnvId)s"

			# deploy; check if this delploy env exists
			self.isDeployEnvExistsSql = f"SELECT COUNT(deploy_id) as total FROM {deployEnvTab} WHERE deploy_id = %(deployId)s and app_env_id = %(appEnvId)s"

			# deploy; get all deploy ctrl tasks
			self.getDeployCtrlTasksSql = f"SELECT * FROM {deployTasksTab} WHERE deploy_id = %(deployId)s and deploy_ctrl_id = %(deployCtrlId)s"

			# deploy; deploy_envs
			self.getDeployEnvAttemptIdsSql = f"SELECT attempt_id_list, attempt_id, total_attempts FROM {deployEnvTab} WHERE deploy_id = %(deployId)s and app_env_id = %(appEnvId)s"

			# deploy; deploy_attempt
			self.getDeployAttemptDataSql = f"SELECT * FROM {deployAttemptsTab} WHERE attempt_id = %(attemptId)s"
			self.getTotalDeployAttemptSql = f"SELECT count(attempt_id) as total FROM {deployAttemptsTab} WHERE deploy_id = %(deployId)s AND app_env_id = %(appEnvId)s"
			self.getDeployAttemptStatusSql = f"SELECT status FROM {deployAttemptsTab} WHERE attempt_id = %(attemptId)s"
			self.getDeployAttempt4DeployIdSql = f"SELECT * FROM {deployAttemptsTab} WHERE deploy_id = %(deployId)s"
			self.getDeployAttempt4EnvSql = f"SELECT * FROM {deployAttemptsTab} WHERE deploy_id = %(deployId) AND app_env_id = %(app_env_id)s"
			self.getDeployAttempt4StatusSql = f"SELECT * FROM {deployAttemptsTab} WHERE deploy_id = %(deployId) AND app_env_id = %(app_env_id)s AND status = %(status)s"
			self.getDeployAttemptAllTaskSql =  f"SELECT * FROM {deployAttemptTasksTab} WHERE attempt_id = %(attemptId)s ORDER BY task_seq"
			self.getDeployAttemptTaskSql = f"SELECT * FROM {deployAttemptTasksTab} WHERE attempt_id = %(attemptId)s AND task_id = %(taskId)s"
			self.isDeployEnvAttemptExistsSql = f"SELECT count(attempt_id) as total FROM {deployAttemptsTab} WHERE attempt_id = %(attemptId)s AND deploy_id = %(deployId)s AND app_env_id = %(appEnvId)s"
			#self.getUniqueEnvAttemptTaskStatusSql = f"SELECT distinct status status FROM {deployAttemptTasksTab} WHERE attempt_id = %(attemptId)s AND task_id = %(taskId)s"
			self.getUniqueEnvAttemptTaskStatusSql = f"SELECT distinct status status FROM {deployAttemptTasksTab} WHERE deploy_id = %(deployId)s AND app_env_id = %(appEnvId)s AND attempt_id = %(attemptId)s"

			#deploy; get all pending tasks for a given deployment id and app envid
			self.getDeployEnvPendingTasksSql = f"""
				SELECT task.task_id as task_id, deploy.deploy_id as deploy_id, deploy.app_id as app_id, deploy.technology as technology, deploy.deploy_ctrl_id as deploy_ctrl_id, 
					task.task_seq as task_seq, task.task_type as task_type, task_category as task_category, task.task_op as task_op, task.task_op_detail as task_op_detail, 
					task.task_obj_owner as task_obj_owner, task.task_obj_name as task_obj_name, task.task_obj_type as task_obj_type, task.task as task, 
					task.status as status, task.parse_status as parse_status, task.parse_status_msg as parse_status_msg
				FROM {deployTasksTab} task, {deployTab} deploy, {deployEnvTab} deploy_env 
				WHERE deploy.deploy_id = %(deployId)s 
					AND deploy.deploy_ctrl_id = task.deploy_ctrl_id 
					AND deploy_env.deploy_id = deploy.deploy_id
					AND deploy_env.app_env_id = %(appEnvId)s
					AND NOT EXISTS (
						SELECT 'x' 
							FROM {deployAttemptTasksTab} 
							WHERE attempt_id = deploy_env.attempt_id 
								AND task_id = task.task_id
								AND status = '{self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS}')
			"""
			self.getDeployTasksSql = f"""
				SELECT task.task_id as task_id, deploy.deploy_id as deploy_id, deploy.app_id as app_id, deploy.technology as technology, deploy.deploy_ctrl_id as deploy_ctrl_id, 
					task.task_seq as task_seq, task.task_type as task_type, task_category as task_category, task.task_op as task_op, task.task_op_detail as task_op_detail, 
					task.task_obj_owner as task_obj_owner, task.task_obj_name as task_obj_name, task.task_obj_type as task_obj_type, task.task as task, 
					task.status as status, task.parse_status as parse_status, task.parse_status_msg as parse_status_msg,
					task.ignore_error as ignore_error
				FROM {deployTasksTab} task, {deployTab} deploy 
				WHERE deploy.deploy_id = %(deployId)s 
					AND deploy.deploy_ctrl_id = task.deploy_ctrl_id 
			"""
			self.getAttemptPendingTasksSql = f"""
				SELECT task.task_id as task_id, deploy.deploy_id as deploy_id, deploy.app_id as app_id, deploy.technology as technology, deploy.deploy_ctrl_id as deploy_ctrl_id, 
					task.task_seq as task_seq, task.task_type as task_type, task.task_category as task_category, task.task_op as task_op, task.task_op_detail as task_op_detail, 
					task.task_obj_owner as task_obj_owner, task.task_obj_name as task_obj_name, task.task_obj_type as task_obj_type, task.task as task, 
					task.status as status, task.parse_status as parse_status, task.parse_status_msg as parse_status_msg,
					task.ignore_error as ignore_error
				FROM {deployTab} deploy, {deployAttemptTasksTab} attempt_task, {deployTasksTab} task  
				WHERE attempt_task.attempt_id = %(attemptId)s
					AND attempt_task.status in ('{self.Globals.DEPLOY_STATUS_DEPLOY_ERROR}','{self.Globals.DEPLOY_STATUS_DEPLOY_PENDING}','{self.Globals.DEPLOY_STATUS_DEPLOY_UNSUCCESS}') 
					AND deploy.deploy_id = attempt_task.deploy_id 
					AND task.task_id = attempt_task.task_id
			"""

			self.getDeploymentServerSql = f"""
				SELECT env.host_name as host, env.conn_string uri   
				FROM {appEnvTab} env, {deployTab} deploy
				WHERE deploy.jira_issue_id = %(jiraIssueId)s
					AND env.app_id = deploy.app_id 
					AND env.env = %(env)s
					AND env.status = '{self.Globals.STATUS_VALID}' 
			"""
			#deploy; update deploy ctrl id 
			self.updDeployCtrlSql = f"UPDATE {deployTab} SET deploy_ctrl_id = %(deployCtrlId)s, comments = CONCAT(comments, '\n ', %(comments)s) WHERE deploy_id = %(deployId)s"
			self.updDeployFileCtrlSql = f"UPDATE {deployFilesTab} SET deploy_ctrl_id = %(deployCtrlId)s WHERE deploy_id = %(deployId)s"
			self.updDeployTaskCtrlSql = f"UPDATE {deployTasksTab} SET deploy_ctrl_id = %(deployCtrlId)s WHERE deploy_id = %(deployId)s"

			# deploy; update deploy status
			self.updDeployStatusSql = f"UPDATE {deployTab} SET status = %(status)s, comments = CONCAT(comments, '\n ', %(comments)s) WHERE deploy_id = %(deployId)s"
			self.updDeployFileStatusSql = f"UPDATE {deployFilesTab} SET status = %(status)s, CONCAT(comments, '\n ', %(comments)s) WHERE file_id = %(fileId)s"
			self.updDeployFileStatusByCtrlSql = f"UPDATE {deployFilesTab} SET status = %(status)s, comments = CONCAT(comments, '\n ', %(comments)s) WHERE deploy_ctrl_id = %(deployCtrlId)s"
			self.updDeployTaskStatusByCtrlSql = f"UPDATE {deployTasksTab} SET status = %(status)s, comments = CONCAT(comments, '\n ', %(comments)s) WHERE deploy_ctrl_id = %(deployCtrlId)s"

			#deploy; invalidate all deployment files for a given deployment id
			self.updDeployCtrlStatusSql = f"UPDATE {deployCtrlTab} SET status = %(status)s, comments = CONCAT(comments, '\n ', %(comments)s) WHERE deploy_ctrl_id = %(deployCtrlId)s"
			self.updTaskStatusByDeployCtrlSql = f"UPDATE {deployTasksTab} set status = %(status)s WHERE deploy_id = %(deployId)s and deploy_ctrl_id = %(deployCtrlId)s"

			# deploy; update deploy parse data in deploy_ctrl
			self.updDeployCtrlParseDataSql = f"""
				UPDATE {deployCtrlTab}
				SET parse_timestamp = %(parseTs)s,
					deploy_file_stats = %(deployFileStats)s,
					deploy_parse_file_data = %(deployParseFileData)s, 
					deploy_parse_file = %(deployParseFile)s, 
					total_tasks = %(totalTasks)s, 
					parse_status = %(status)s 
				WHERE deploy_ctrl_id = %(deployCtrlId)s
			"""

			self.updDeployValidationAttemptSql = f"""
				UPDATE {deployTab}
					SET validation_attempts = %(validationAttempts)s,
						last_validation_by = %(lastValidationBy)s,
						last_validation_ts  = %(lastValidationTs)s,
						comments = CONCAT(comments, '\n ', %(comments)s) 
					WHERE deploy_id = %(deployId)s
			"""

			self.updDeploySourceSql = f"""
				UPDATE {deployTab}
					SET deploy_source = %(deploySource)s,
						deploy_source_id = %(deploySourceId)s,
						comments = CONCAT(comments, '\n ', %(comments)s)
					WHERE deploy_id = %(deployId)s

			"""
			# deploy; update deploy environment status
			self.updDeployEnvStatusSql = f"""
				UPDATE {deployEnvTab}
				SET status = %(status)s, end_time = %(endTime)s, duration = %(duration)s, comments = CONCAT(comments, '\n ', %(comments)s)
				WHERE deploy_id = %(deployId)s
					AND app_env_id = %(appEnvId)s
			"""
			self.updDeployEnvAttemptIdSql =	f"""
				UPDATE {deployEnvTab} 
				SET attempt_id_list = %(attemptIdList)s, attempt_id = %(attemptId)s, 
					total_attempts = %(totalAttempts)s, comments = CONCAT(comments, '\n ', %(comments)s) 
				WHERE deploy_id = %(deployId)s AND app_env_id = %(appEnvId)s
			"""
			self.updDeployEnvTaskStatsSql = f"""
				UPDATE {deployEnvTab} 
					SET completed_tasks = %(completedTasks)s, completed_tasks_list = %(completedTasksList)s, pending_tasks = %(pendingTasks)s, pending_tasks_list = %(pendingTasksList)s
					WHERE deploy_id = %(deployId)s
						AND app_env_id = %(appEnvId)s
			"""
			self.updDeployAttempTaskStatsSql = f"""
				UPDATE {deployAttemptsTab} 
					SET completed_tasks = %(completedTasks)s, completed_tasks_list = %(completedTasksList)s, pending_tasks = %(pendingTasks)s, pending_tasks_list = %(pendingTasksList)s
					WHERE deploy_id = %(deployId)s
						AND attempt_id = %(attemptId)s
			"""
			self.approveDeployEnvSql = f"""
				UPDATE {deployEnvTab} 
					SET status = %(status)s, approved_by = %(approvedBy)s, approved_ts = %(approvedTs)s, comments = CONCAT(comments, '\n ', %(comments)s)
					WHERE deploy_id = %(deployId)s
						AND app_env_id = %(appEnvId)s
			"""
			# deploy; update deploy attempt task status
			self.updDeployAttemptTaskStatusSql = f"UPDATE {deployAttemptTasksTab} SET status = %(status)s WHERE deploy_id = %(deployId)s AND task_id = %(taskId)s AND app_env_id = %(appEnvId)s AND task_id = %(taskId)s"
			self.updDeployAttemptTaskResultSql = f"""
				UPDATE {deployAttemptTasksTab} 
					SET result = %(result)s, 
						status = %(status)s, 
						start_time = %(startTime)s, 
						end_time = %(endTime)s, 
						duration = %(duration)s,
						records_affected = %(recordsAffected)s, 
						before_deploy_image = %(beforeDeployImage)s, 
						after_deploy_image = %(afterDeployImage)s 
					WHERE deploy_id = %(deployId)s 
						AND attempt_id = %(attemptId)s 
						AND task_id = %(taskId)s
			"""
			# deploy;
			self.updDeployEnvAttemptStatusSql = f"""
				UPDATE {deployAttemptsTab} 
					SET status = %(status)s, end_time = %(endTime)s, duration = %(duration)s
					WHERE attempt_id = %(attemptId)s 
						AND deploy_id = %(deployId)s 
						AND app_env_id = %(appEnvId)s
			"""
			self.startDeployAttemptTaskSql = f"UPDATE {deployAttemptTasksTab} SET status = %(status)s, start_time = %(startTime)s, before_deploy_image = %(beforeImage)s, comments = CONCAT(comments, '\n ', %(comments)s) WHERE attempt_id = %(attemptId)s AND task_id = %(taskId)s"
			self.finishDeployAttemptTaskSql = f"UPDATE {deployAttemptTasksTab} SET end_time = %(endTime)s, duration = %(duration)s, status = %(status)s, records_affected = %(recordsAffected)s, result = %(result)s, comments = CONCAT(comments, '\n ', %(comments)s) WHERE attempt_id = %(attemptId)s AND task_id = %(taskId)s"

			############################# INSERT #############################

			#self.newAppSql = "INSERT into app.app(name,opco,region,technology,) values(%(appName)s, %(opco)s, %(region)s, %(dbTechnology)s) returning _id"

			self.createNewAppSql = f"""
				INSERT INTO {appTab} (app_id, app_name, app_desc, region, opco, technology, status, db_schemas, requested_by, requested_ts)
				values( %(appId)s, %(appName)s, %(appDesc)s, %(region)s, %(opco)s, %(dbTechnology)s, %(status)s, %(dbSchemas)s, %(requestedBy)s, %(requestedTs)s)
				RETURNING app_id
			"""
			self.createNewAppEnvSql = f"""
				INSERT INTO {appEnvTab} (app_id, env, host_name, conn_string, db_instance, db_schemas, notification_dl, status, requested_by, requested_ts)
				values( %(appId)s, LOWER(%(env)s), %(hostName)s, %(connString)s, %(dbInstance)s, %(dbSchemas)s, %(notificationDL)s, %(status)s, %(requestedBy)s, %(requestedTs)s )
				RETURNING app_env_id
			"""
			self.createAppEnvContactSql = f"""
				INSERT INTO {appEnvContactTab} (app_id, app_env_id, env, contact_id, contact_type, status, requested_by, requested_ts) 
				VALUES (%(appId)s, %(appEnvId)s, LOWER(%(env)s), %(contactId)s, %(contactType)s, %(status)s, %(requestedBy)s, %(requestedTs)s )
				RETURNING app_id
			"""
			self.newAppEnvOwnerSql = f"""
				INSERT INTO app.app_env_owner(app_id, env, ad_group, user_id, user_name,ts)
				VALUES(%(appId)s, %(env)s, %(adGrp)s, %(userId)s, %(userName)s, %(ts)s)
				RETURNING _id
			"""
			self.newRequestForApprovalSql = f"""
				INSERT into {approvalTab}  (ext_reference_id, entity_id, entity_type, request_type, requested_by,requested_ts, comments)
				VALUES (%(extReferenceId)s, %(entityId)s, %(entityType)s, %(requestType)s, %(requestedBy)s,  %(requestedTs)s, %(comments)s)
				RETURNING request_id
			"""
			self.newEventLogSql = f"""
				INSERT INTO {eventLogTab} (ts, entity_id, entity_type, parent_entity_id, parent_entity_type, who, what, comment)
				VALUES (%(ts)s, %(entityId)s, %(entityType)s, %(parentEntityId)s, %(parentEntityType)s, %(who)s, %(what)s, %(comment)s )
				RETURNING _id
			"""
			#deployment
			self.newDeploySql = f"""
				INSERT INTO {deployTab} (deploy_id, deploy_source, deploy_source_id, jira_issue_id, app_id, app_name, technology, deploy_ctrl_id, deploy_file_location, deploy_env_order,status, submitted_by,submitted_ts, comments)
				VALUES (%(deployId)s, %(deploySource)s, %(deploySourceId)s, %(jiraIssueId)s, %(appId)s, %(appName)s, %(dbTechnology)s, %(deployCtrlId)s, %(deployFileLocation)s, ARRAY[%(deployEnvOrder)s], %(status)s, %(submittedBy)s ,%(submittedTs)s, %(comments)s )
			"""
			self.newDeployCtrlSql = f"""
				INSERT INTO {deployCtrlTab} (deploy_ctrl_id, deploy_id, app_id, ts, deploy_readme, status, comments)
				VALUES(%(deployCtrlId)s, %(deployId)s, %(appId)s, %(ts)s, %(deployReadMe)s, %(status)s, %(comments)s )

			"""
			self.newDeployFileSql = f"""
				INSERT INTO {deployFilesTab} (
					file_name,file_path,deploy_id,deploy_ctrl_id,technology,seq,contents, ignore_error, total_tasks,
					parse_failed,parse_status,parse_status_msg,status,submitted_by,submitted_ts, comments)
				VALUES (
					%(fileName)s, %(filePath)s, %(deployId)s, %(deployCtrlId)s, %(dbTechnology)s, %(seq)s, %(contents)s, 
					%(ignoreError)s, %(totalTasks)s, %(parseFailed)s, %(parseStatus)s, %(parseStatusMsg)s, %(status)s, 
					%(submittedBy)s ,%(submittedTs)s, %(comments)s )
				RETURNING file_id
			"""
			self.newDeployTaskSql = f"""
				INSERT INTO {deployTasksTab} (
					file_id,file_name,deploy_id,app_id,technology,
					deploy_ctrl_id,task_seq,task_type,task_category,task_op,task_op_detail,
					task_obj_owner,task_obj_name,task_obj_type,task,status,parse_status,parse_status_msg, ignore_error, comments
				)
				VALUES (
					%(fileId)s, %(fileName)s, %(deployId)s, %(appId)s, %(dbTechnology)s,
					%(deployCtrlId)s, %(taskSeq)s, %(taskType)s, %(taskCategory)s, %(taskOp)s, %(taskOpDetail)s, 
					%(taskObjOwner)s, %(taskObjName)s, %(taskObjType)s, %(task)s, %(status)s, %(parseStatus)s, %(parseStatusMsg)s, 
					%(ignoreError)s, %(comments)s )
				RETURNING task_id
			"""
			self.newDeployEnvsSql = f"""
				INSERT INTO {deployEnvTab} (
					deploy_id, app_id, env, app_env_id, status, submitted_by, submitted_ts, scheduled_ts,
					total_tasks, pending_tasks, tasks_list, pending_tasks_list, referenced_doc, start_time, comments
				)
				VALUES (
					%(deployId)s, %(appId)s, %(env)s, %(appEnvId)s, %(status)s, %(submittedBy)s, %(submittedTs)s, %(scheduledTs)s,
					%(totalTasks)s, %(pendingTasks)s, %(tasksList)s, %(pendingTasksList)s, %(referencedDoc)s, %(startTime)s, %(comments)s
				)
			"""
		
			self.newAttemptSql = f"""
				INSERT INTO {deployAttemptsTab} (
					deploy_id, app_id, env, app_env_id, requested_by, total_tasks, pending_tasks, tasks_list, pending_tasks_list, start_time, status, comments)
				VALUES (
					%(deployId)s, %(appId)s, %(env)s, %(appEnvId)s, %(requestedBy)s, %(totalTasks)s, %(pendingTasks)s, %(tasksList)s, %(pendingTasksList)s, %(startTime)s, %(status)s, %(comments)s
				)
				RETURNING attempt_id
			"""

			self.newDeployAttemptTasksSql = f"""
				INSERT INTO {deployAttemptTasksTab} (
					attempt_id, task_id, deploy_id, app_env_id, deploy_ctrl_id, task_seq, task_type, task_category, 
					task_op, task_op_detail, task_obj_owner,task_obj_name,task_obj_type, task, ignore_error, status,comments)
				VALUES (
					%(attempt_id)s, %(task_id)s, %(deploy_id)s, %(app_env_id)s, %(deploy_ctrl_id)s, %(task_seq)s, 
					%(task_type)s, %(task_category)s, %(task_op)s, %(task_op_detail)s, 
					%(task_obj_owner)s, %(task_obj_name)s, %(task_obj_type)s, %(task)s, %(ignore_error)s, 
					%(status)s, %(comments)s
				)
			"""

			self.newDeployObjSql = f"""
				INSERT INTO {deployObjTab} (
					app_id, db_instance, db_technology, env, schema, obj_type, obj_name, obj_owner, first_deploy_id, first_deploy_date,
					last_deploy_id, last_deploy_date, total_deployment)
				VALUES (
					%(appId)s, %(dbInstance)s, %(dbTechnology)s, %(env)s, %(schema)s, %(objType)s, %(objName)s, %(objOwner)s, 
					%(firstDeployId)s, %(firstDeployDate)s, %(lastDeployId)s, %(lastDeployDate)s, %(totalDeployment)s
				)
				RETURNING deploy_obj_id
			"""

			self.newDeployObjHistSql = f"""
				INSERT INTO {deployObjHistTab} (
					deploy_obj_id, deploy_id, app_id, app_env_id, env, deployment_date, before_deploy_image, after_deploy_image, deployment_category)
				VALUES (
					%(deployObjId)s, %(deployId)s, %(appId)s, %(appEnvId)s, %(env)s, %(deploymentDate)s, %(beforeDeployImage)s, %(afterDeployImage)s, 
					%(deploymentCategory)s
				)
				returning _id
			"""
			self.newManyDeployAttemptTasksSql__orig = f"""
				INSERT INTO {deployAttemptTasksTab} (
					attempt_id, task_id, deploy_id, deploy_ctrl_id, task_seq, task_type, task_category, task_op, task_op_detail, task_obj_owner,task_obj_name,task_obj_type,    
					task, status, comments)
				SELECT unnest( %(attemptId)s ), unnest( %(taskId)s ), unnest( %(deployId)s ), unnest( %(deployCtrlId)s ), unnest( %(taksSeq)s ), unnest( %(taskType)s ), 
					unnest( %(taskCategory)s ), unnest( %(taskOp)s ), unnest( %(taskOpDetail)s ), unnest( %(taskObjOwner)s ), unnest( %(taskObjName)s ), unnest( %(taskObjType)s ), 
					unnest( %(task)s ), unnest( %(status)s ), unnest( %(comments)s)
				)
			"""

			self.newManyDeployAttemptTasksSql = f"""
				INSERT INTO {deployAttemptTasksTab} (
					attempt_id, task_id, deploy_id, deploy_ctrl_id, task_seq, task_type, task_category, task_op, task_op_detail, task_obj_owner,task_obj_name,task_obj_type,    
					task, status, comments)
				SELECT unnest( %(s)s as (attemptId, taskId, deployId, deployCtrlId, taksSeq, taskType, taskCategory, taskOp, taskOpDetail, taskObjOwner, taskObjName, taskObjType, 
					task, status, comments)
				)
			"""

			self.newDeployApprovalSql = f"""
				INSERT INTO {approvalTab} (deploy_id,env,approved_by,approval_ts)
				VALUES (%(deploy_id)s, %(env)s, %(aprovedBy)s, %(approvalTs)s )
				RETURNING request_id
			"""
			
			# creating new valid approver
			self.newValidApproverSql = f"""
				INSERT INTO app.valid_approver(network_id, approver_name, ctfy_group, region, status, created_ts,last_updated_ts,comment)
				VALUES( lower(%(userId)s), %(approverName)s, %(ctfyGroup)s, %(region)s, %(status)s, %(createdTs)s, %(lastUpdatedTs)s, %(comment)s ) 
			"""
			# create new session token
			self.newSessionTokenSql = f"""
				INSERT into {sessionTokenTab} (session_id, ts, user_id, session_auth, access_route, security_token, status, comments)
				VALUES (%(sessionId)s, %(ts)s, %(userId)s, %(sessionAuth)s, %(accessRoute)s, %(securityToken)s,  %(status)s, %(comments)s)
				RETURNING session_id
			""" 
			# create new session request
			self.newSessionRequestSql = f"""
				INSERT into {sessionRequestTab} (session_id, ts, user_id, request, request_raw, status)
				VALUES (%(sessionId)s, %(ts)s, %(userId)s, %(request)s, %(requestRaw)s, %(status)s)
			""" 
			# create new session request

			# update
			self.updSessionTokenCompleteSql = f"UPDATE {sessionTokenTab} SET status = %(status)s WHERE session_id = %(sessionId)s"
			self.updSessionRequestCompleteSql = f"UPDATE {sessionRequestTab} SET request_end_ts = %(requestEndTs)s, elapsed = %(elapsed)s, status = %(status)s WHERE session_id = %(sessionId)s"

			self.updAppStatusSql = f"UPDATE {appTab} SET status = %(status)s WHERE app_id = %(appId)s "
			self.updAppEnvOrderSql = f"UPDATE {appTab} SET deploy_env_order = %(deployEnvOrder)s WHERE app_id = %(appId)s "
			self.updAppStatusWApprovalSql = f"UPDATE {appTab} app SET approved_by = %(approvedBy)s, approved_ts = %(approvedTs)s, status = %(status)s WHERE app_id = %(appId)s "
			self.approveAppSql = f"UPDATE {appTab} SET approved_by = %(approvedBy)s, approved_ts = %(ts)s, status = %(status)s "

			self.updEnvStatusSql = f"UPDATE {appEnvTab} SET status = %(status)s WHERE app_env_id = %(appEnvId)s "
			self.markAppEnvInactiveSql = f"UPDATE {appEnvTab} SET env = %(inActiveEnv)s, status = 'inactive' WHERE app_env_id = %(appEnvId)s "
			#self.updEnvStatusWApprovalSql = f"UPDATE {appEnvTab} SET approved_by = %(approvedBy)s, approved_ts = %(approvedTs)s, status = %(status)s WHERE app_env_id = %(appEnvId)s and status = '{pendingStatus}'"
			self.updEnvStatusWApprovalSql = f"UPDATE {appEnvTab} SET approved_by = %(approvedBy)s, approved_ts = %(approvedTs)s, status = %(status)s WHERE app_env_id = %(appEnvId)s "
			self.updContactStatusSql = f"UPDATE {appEnvContactTab} SET status = %(status)s WHERE app_env_id = %(appEnvId)s "
			#self.updContactStatusWApprovalSql = f"UPDATE {appEnvContactTab} SET approved_by = %(approvedBy)s, approved_ts = %(approvedTs)s, status = %(status)s WHERE app_id = %(appId)s AND app_env_id = %(appEnvId)s and status = '{pendingStatus}'"
			self.updContactStatusWApprovalSql = f"UPDATE {appEnvContactTab} SET approved_by = %(approvedBy)s, approved_ts = %(approvedTs)s, status = %(status)s WHERE app_env_id = %(appEnvId)s"

			# update db schemas 
			self.updAppDBSchemaSql = f"UPDATE {appTab} SET db_schemas = %(dbSchemas)s WHERE app_id = %(appId)s"
			self.updAppEnvDBSchemaSql = f"UPDATE {appEnvTab} SET db_schemas = %(dbSchemas)s WHERE app_id = %(appId)s"

			# update deploy objects
			self.updateDeployObjSql = f"UPDATE {deployObjTab} SET last_deploy_id = %(lastDeployId)s, last_deploy_date = %(lastDeployDate)s, total_deployment = total_deployment + 1 WHERE deploy_obj_id = %(deployObjId)s"

			# approvals
			self.completeApprovalRequestSql = f"UPDATE {approvalTab} SET approved_by = %(approvedBy)s, approved_ts = %(approvedTs)s, status = %(status)s, comments = %(comments)s WHERE request_id = %(requestId)s"

			self.updAllAppEnvStatusSql = f"UPDATE {appEnvTab} SET status = %(status)s WHERE app_id = %(appId)s "
			self.updAllAppEnvContactStatusSql = f"UPDATE {appEnvContactTab} SET status = %(status)s WHERE app_id = %(appId)s "

			#self.updAppEnvIdStatusSql = f"UPDATE {appEnvTab} SET status = %(status)s WHERE app_env_id = %(appEnvId)s "

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	"""
	***** CICD Repo method (data change) starts
	"""
	"""
	Session detail
	"""
	def genNewSessionId(self, securityToken, userId, requestHostName):
		pass

	def getSessionDetails(self, securityToken, sessionId):
		"""
		Retrieves session information for a given session id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(sessionId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# get start time of this session request

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getSessionDetailsSql, {"sessionId" : sessionId})

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"An error occurred while retrieving details for session id >>> {sessionId}")

			if "data" in myDBResult and myDBResult["data"][0]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]}")
				return myDBResult["data"][0]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def startSession(self, securityToken, userId, sessionAuth, accessRoute, request, comments):
		"""
		Starts session, Create new sesion id and tracks the usage of each request and its metadata
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', userId, ',', str(sessionAuth), ',', str(accessRoute), ',', comments])))

			myModule = sys._getframe().f_code.co_name

			# we are not validating security token because it has not yet been updated in our table
			mySessionId = self.__createNewSessionToken(securityToken, userId, sessionAuth, accessRoute,comments)
			myDBResult = self.__createNewSessionRequest(securityToken, mySessionId, userId, request, comments)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("unable to create session for this request !!!")
			
			self.pg.commit(securityToken, self.PG_CONN)

			return mySessionId

		except Exception as error:
			self.pg.rollback(securityToken, self.PG_CONN)
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def completeSession(self, securityToken, sessionId, elapsedSecs, status):
		"""
		Complete session (update states as completed)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(sessionId), ',', str(elapsedSecs), status ])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# get start time of this session request

			#mySessionDetails = self.getSessionDetails(securityToken, sessionId)
			
			#mySessionStartTime = mySessionDetails["start_ts"]

			# will perform rollback if status is unsuccess, Postgres always creates a transaction even for select, if we got an error transaction may have not been rolled back

			if status == self.Globals.unsuccess:
				self.pg.rollback(securityToken, self.PG_CONN)
				self.pg.commit(securityToken, self.PG_CONN)

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updSessionTokenCompleteSql, {"sessionId" : sessionId, "status" : status})

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updSessionRequestCompleteSql, {"sessionId" : sessionId, "requestEndTs" : self.util.lambdaGetCurrDateTime(), "elapsed" : elapsedSecs, "status" : status})

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("An error {error} occurred while completing session".format(error =myDBResult["message"]))

			self.pg.commit(securityToken, self.PG_CONN)

			return myDBResult

		except Exception as error:
			self.pg.rollback(securityToken, self.PG_CONN)
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getTrustedProxies(self, securityToken):
		"""
		returns trusted prcxies from database
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myTrustedProxies = self.pg.execSql(securityToken, self.PG_CONN, self.getTrustedProxiesSql,{})

			return myTrustedProxies

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __createNewSessionToken(self, securityToken, userId, sessionAuth, accessRoute, comments):
		"""
		Creates a new session entry in repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', userId, ',', str(sessionAuth), ',', str(accessRoute), ',', comments])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			from secrets import token_urlsafe
			mySessionId = token_urlsafe(32)

			mySessionTokenData = {
				"sessionId" : mySessionId,
				"ts" : self.util.lambdaGetCurrDateTime(),
				"userId" : userId,
				"sessionAuth" : sessionAuth,
				"accessRoute" : accessRoute,
				"securityToken" : securityToken,
				"status" : self.Globals.STATUS_INPROGRESS,
				"comments" : comments
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newSessionTokenSql, mySessionTokenData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			return mySessionId

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __createNewSessionRequest(self, securityToken, sessionId, userId, request, comments):
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(sessionId), ',', userId, ',', str(request)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySessionRequestData = {
				"sessionId" : sessionId,
				"ts" : self.util.lambdaGetCurrDateTime(),
				"userId" : userId,
				"request" : request["method"],
				"requestRaw" : request,
				"status" : self.Globals.STATUS_INPROGRESS,
				"comments" : comments
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newSessionRequestSql, mySessionRequestData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	"""
	On Boarding
	"""
	def onBoardCicdApp(self, securityToken, jiraIssueId, appId, appName, appDesc, opco, region, dbTechnology, deployEnvOrder, env, hostName, dbInstance, connString, dbSchemas, ownerIdList, notificationDL, userId):
		"""
		Onboard application environment
		Arguments:
			securityToekn 		: string (security token generated during authentication)
			jiraIssueId			: string (Jira issue id, from Jira)
			appId 				: integer (applicarion id)
			appName 			: string (application Name)
			appDesc 			: string (application description)
			opco 				: string (opco -> marsh/gc/mercer/ow)
			region 				: string (region -> nam/emea/apac/latm)
			dbTechnology 		: string (database technology -> oracle/postgrs/mongo/mysql)
			deployEnvOrder 		: array (order of deploymnet in env i.e. [dev,uat,prod])
			env  				: string (application environment)
			hostName 			: string (hostname where this environment is housed)
			dbInstance 			: string (database/dbinstance name oracle-> dbname, postgres-> instance name (host:port), mongo-> rsname, mysql -> instance name)
			connctString 		: string (connect string/db uri to connect to this environment db instance)
			dbSchemas 			: array (list of schemas or database of this application)
			ownerIdList 		: array (list of owner (adgroup) of this application env, owner of this environment is allowed to perform deployment in this environment )
			notificationDL      : array (list of notification dl to whom notificication to be sent during an event occurs in this environment)
			userId 				: string (use submitting this request)
		"""
		try:
			
			#self.LOGGER.debug("got arguments >>> {args}".\
			#	format(args = "".join([securityToken, ',', appName, ',', region, ',', opco, dbTechnology, ',', env, ',', connString, ',', \
			#		dbInstance, ',', dbSchemas, ',', ownerIdList, ',', notificationDL, ',', userId])))
			
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', str(jiraIssueId), ',', str(appId), ',', appName, ',', appDesc, ',', region, ',', opco, ',', \
					dbTechnology, ',', str(deployEnvOrder), ',', env, ',', hostName, ',', connString, ',', \
					dbInstance, ',', str(dbSchemas), ',', str(ownerIdList), ',', str(notificationDL), userId])))

			myModule = sys._getframe().f_code.co_name

			myDBSchemas = [dbSchemas] if not isinstance(dbSchemas, list) else self.util.getACopy(dbSchemas)
			myNotifyList = [notificationDL] if not isinstance(notificationDL, list) else self.util.getACopy(notificationDL)
			myDeployEnvOrder = [deployEnvOrder] if not isinstance(deployEnvOrder, list) else self.util.getACopy(deployEnvOrder)

			myDeployenvOrder = [env.lower() for env in myDeployEnvOrder]

			self.sec.validateSecToken(securityToken)

			self.LOGGER.info('user {user} requested onboarding application >>> {app}'.format(user = userId, app = ''.join([region, '.', opco, '.', dbTechnology, '.', appName])))

			self.LOGGER.info('validating on board app arguments')

			#__validateOnboardAppEnvArgs(self, securityToken, appId, appName, appDesc, region, opco, dbTechnology, deployEnvOrder, env, hostName, connString, dbInstance, dbSchemas, ownerIdList, notificationDLList, userId)
			self.__validateOnboardAppEnvArgs(securityToken, appId, appName, appDesc, opco.lower(), region.lower(), dbTechnology.lower(), myDeployEnvOrder, env, hostName.lower(), dbInstance, connString, myDBSchemas, ownerIdList, myNotifyList, userId)

			# instantiating jira class for given jira issue id			
			#myJira = JiraUtility(securityToken, jiraIssueId)

			# will create new app if it does not exists

			#def __createAppMetadata(self, securityToken, appId, appName, appDesc, region, opco, dbTechnology, deployEnvOrder, dbSchemas, userId):
			myAppId = self.__createAppMetadata(securityToken, appId, appName, appDesc, opco.lower(), region.lower(), dbTechnology.lower(), dbSchemas, userId)

			# validation
			"""
			there must be atleast 1 lower env on boarded before on boarding 'prod' environment
			if requested env is prod, get total env on boarded, if total count is 0, do not allow this prod environmet to be 
			onboarded
			"""
			# creating environment metadata for this application
			#self.__createAppEnvMetadata(securityToken, myAppId, env, connString, dbInstance, dbSchemas, deployHours, notificationDL)
			myDBResult = self.__createAppEnvMetadata(securityToken, appId, env, hostName.lower(), connString, dbInstance, myDBSchemas, myNotifyList, userId)
			
			myAppEnvId = myDBResult["data"][0]["app_env_id"]

			# creating contact list for this application and environment
			myOwnerIdList = [owner.lower() for owner in ownerIdList]

			#myOwnerIdList.append(userId.lower())
			self.__createAppEnvContacts(securityToken, appId, env, myAppEnvId, myOwnerIdList, dbTechnology.lower(), userId.lower())

			myDBResult = self.__updAppDeployEnvOrder(securityToken, appId, myDeployEnvOrder, userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			# adding this request for approval
			#def newRequestForApproval(self, securityToken, entityId, entityType, requestType, userId)
			myDBResult = self.newRequestForApproval(securityToken, jiraIssueId, myAppEnvId, 'app.env','onboard.new.app.env', userId)

			myRequestId = myDBResult["data"][0]["request_id"]

			# commiting work
			self.pg.commit(securityToken, self.PG_CONN)

			#return self.util.buildResponse(self.Globals.success, self.Globals.success, {"appId" : myAppId})

			self.JiraUtil.addAComment(securityToken, jiraIssueId, "app [{app}] has been created (pending approval with request id [{id}] ) using args >>> {args}".\
				format(app = "".join([str(myAppEnvId), '.',env]), id = str(myRequestId), args = "".join([str(appId), ',', appName, ',', appDesc, ',', region, ',', opco, dbTechnology, ',', env, ',', hostName, ',', connString, ',', \
					dbInstance, ',', str(dbSchemas), ',', str(ownerIdList), ',', str(notificationDL), userId])))

			return {"appId" : appId, "appEnvId" : myAppEnvId}

		except Exception as error:
			self.pg.rollback(securityToken, self.PG_CONN)
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __validateOnboardAppEnvArgs(self, securityToken, appId, appName, appDesc, opco, region, dbTechnology, deployEnvOrder, env, hostName, dbInstance, connString, dbSchemas, ownerIdList, notificationDLList, userId):
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
				format(args = "".join([securityToken, ',', str(appId), ',', appName, ',', appDesc, ',', region, ',', opco, dbTechnology, ',', \
					str(deployEnvOrder), ',', env, ',', hostName, ',', connString, ',', \
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
				{"arg" : "appDesc", "type" : str, "value" :appDesc},
				{"arg" : "region", "type" : str, "value" : region},
				{"arg" : "opco", "type" : str, "value" : opco},
				{"arg" : "dbTechnology", "type" : str, "value" : dbTechnology},
				{"arg" : "deployEnvOrder", "type" : list, "value" : deployEnvOrder},
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

			# 2. Must not exceed the max app in pending threshold for a given user
			myPendingApp = self.getMyPendingApp(securityToken, opco, region, dbTechnology, userId)

			myPendingAppIds = [app["app_id"] for app in myPendingApp]

			if len(myPendingAppIds) > self.MAX_PENDING_APP_PER_USER:
				raise ValueError("""
					MAximum {pendingAppThreshold} app is allowed to be in pending state per user,
					total {tot} app found in pending state for user {user} 
					Pls get approval on pending app 
					>>> 
					    {pendingApp}
					""".format(pendingAppThreshold = self.MAX_PENDING_APP_PER_USER, tot = len(myPendingAppIds), pendingApp = str(myPendingApp)))

			# 3. app name and env must not be on boarded
			if self.isAppEnvExistsByName(securityToken, appName, env):
				raise ValueError('Application <{app}> environment <{env}> has already been onboarded !!! '.format(app = appName, env = env))

			#4. Ensure other app is not using same db instance and schema (dbinstance, dbTechnology and schema must not exist)
			if not self.isValidDBSchema(securityToken, opco, region, appId, hostName, dbTechnology, dbInstance, dbSchemas, env):
				raise ValueError('Invalid db instance/schema {dbInstSchema}!!!'.format(dbInstSchema = "".join([hostName,".",dbInstance, ".", str(dbSchemas)])))

			if self.isDbInstSchemaInUse(securityToken, dbInstance, dbSchemas, dbTechnology):
				raise ValueError('DB instance and db schema < {dbInstSchema} > is already in-use !!!'.format(dbInstSchema = ''.join([dbTechnology, '.', dbInstance, '.', str(dbSchemas)])))

			# 5. Validate connection string (must be able to perform connectivity to target database)
			self.validateDBUri(securityToken, dbTechnology, connString, env)

		except Exception as error:
			self.LOGGER.error('an error occurred while validating uri >>> {error}'.format(error = str(error)))
			raise error

	def __genNewCicdAppId__donotuse(self,securityToken, extAppId):
		"""
		generates new app id for a given external app id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(extAppId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myDBResult = self.pg.execSql(securityToken,self.PG_CONN, self.getTotExtAppIdCntSql, {"extAppId" : extAppId})
			
			print('result >', myDBResult)

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"][0]:
				
				print("data >", myDBResult["data"][0]["total"])
				myTotalExtAppIdCnt = myDBResult["data"][0]["total"] + 1

				myAppId = "".join([str(extAppId),f'{myTotalExtAppIdCnt:05}'])

				return myAppId

		except Exception as error:
			self.LOGGER.error('an error occurred while generating new app id >>> {error}'.format(error = str(error)))
			raise error

	def __createAppMetadata(self, securityToken, appId, appName, appDesc, opco, region, dbTechnology, dbSchemas, userId):
		# will create new app metadata, if app already exists will return app id (app_id) for this app 
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), appName, ',', appDesc, ',', region, ',', opco, ',', dbTechnology, ',', str(dbSchemas), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			#myDeployEnvOrderList = [deployEnvOrder] if not isinstance(deployEnvOrder, list) else self.util.getACopy(deployEnvOrder)
			#myDBSchemasList = [dbSchemas] if not isinstance(dbSchemas, list) else self.util.getACopy(dbSchemas)

			if not self.isAppExists(securityToken, appId):

				# new app does not exists, creatng new one (for external app id )
				# myNewAppId = self.genNewCicdAppId(securityToken, appId)

				#if not myNewAppId:
				#	raise ValueError("could not generate new app id for >> {app}".format(app = "".join([str(appId), ".", appTag])))

				myAppData = {
					"appId" : appId,
					"appName" : appName,
					"appDesc" : appDesc,
					#"appTag" : appTag,
					"opco" : opco, 
					"region" : region, 
					"dbTechnology" : dbTechnology,
					#"deployEnvOrder" : deployEnvOrder,
					"dbSchemas" : dbSchemas,
					"status" : self.Globals.STATUS_ONBOARD_ADD_ENV_APPROVAL_PENDING, 
					"requestedBy" : userId.lower(),
					"requestedTs" : self.util.lambdaGetCurrDateTime()
				}

				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.createNewAppSql, myAppData)

				self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("An error occurred while creating metadata for application for >>> {app}".format(app = appName))

				#myAppId = myDBResult["data"][0]["app_id"]
				#newEventLog(self, securityToken, entityId, entityType, parentEntityId, parentEntityType, userId, what, comment = None)
				self.newEventLog(\
					securityToken, \
					appId, 'app', \
					appId, 'app', \
					userId, 'new.app', \
					f'created mew app {appName} with app id {appId} as requested by user {userId}'\
				)
			else:
				# would need to update application's deploy env order

				#myDBResult = self.__updAppDeployEnvOrder(securityToken, appId, deployEnvOrder, userId)

				#if myDBResult["status"] == self.Globals.unsuccess:
				#	raise ValueError(myDBResult["message"])
				pass				
			#return myAppId

		except Exception as error:
			self.pg.rollback(securityToken, self.PG_CONN)
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __createAppEnvMetadata(self, securityToken, appId, env, hostName, connString, dbInstance, dbSchemas, notificationDLs, userId):
		"""
		Create new app env metadata in CICD repository
		Arguments:
			securityToken : String - security token
			appId : Integer - applicartion Id
			env: String - application environment (dev/test/stg/perf/prod)
			hostName : String - host name
			connString : String - connection string /dbURI
			dbInstance : String - db instance name 
			dbSchemas : Array - database schema(s)
			notificationDLs : Array - notification dl
			userId: String - User id submitting this request
		"""
		#  

		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env, ',', hostName, ',', connString, ',', dbInstance, ',', str(dbSchemas), ',', str(notificationDLs), ',', userId ])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			#self.newEventLog(securityToken, appId, 'APP', 'request.newapp.env', userId, 'user requested to create new app env')

			if not self.isAppEnvExists(securityToken, appId, env):
				# app env does not exists, creating

				#myNotificatinDlList = [notificationDL] if not isinstance(notificationDL, list) else myNotificatinDlList = self.util.getACopy(notificationDL)
				#myHostList = [hostNames] if not isinstance(hostNames, list) else self.util.getACopy(hostNames)

				myDBSchemaList = [dbSchemas] if not isinstance(dbSchemas, list) else self.util.getACopy(dbSchemas)
				myNotficationDlList = [notificationDLs] if not isinstance(notificationDLs, list) else self.util.getACopy(notificationDLs)

				myAppEnvData = {
					"appId" : appId, 
					"env" : env,
					"hostName" : hostName,
					"connString" : connString, 
					"dbInstance" : dbInstance, 
					"dbSchemas" : myDBSchemaList, 
					"notificationDL" : myNotficationDlList, 
					"status" : self.Globals.STATUS_ONBOARD_ADD_ENV_APPROVAL_PENDING,
					"requestedBy" : userId.lower(), 
					"requestedTs" : self.util.lambdaGetCurrDateTime() 
				}

				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.createNewAppEnvSql, myAppEnvData)

				self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("An error occurred while creating metadata for application for >>> {app}".format(app = appName))

				myAppEnvId = myDBResult["data"][0]["app_env_id"]

				"""
				# adding this env to end of app.deplo_env_order
				myAppEnvOrder = self.getDeployEnvOrder(securityToken, appId)

				if not (env.lower() in myAppEnvOrder):
					myAppEnvOrder.append(env)
					self.LOGGER.info('replacing existing deploy env order [{existing}] to [{new}'.format(existing = str(myAppEnvOrder), new = str(myAppEnvOrder)))
					self.__updAppEnvOrder(securityToken, appId, myAppEnvOrder)
				"""

				#newEventLog(self, securityToken, entityId, entityType, parentEntityId, parentEntityType, userId, what, comment = None)
				self.newEventLog(\
					securityToken, 
					myAppEnvId, 'app.env', \
					appId, 'app', \
					userId, 'new.app.env', \
					f'creating new environment {env} for app {appId}' \
				)

				return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __addAppEnvContacts(self, securityToken, appId, env, appEnvId, contactType, contactId, requestedBy):
		"""
		add new contacts for a given app and its enivornment.
		arguments:
			securiytToken : securityToken
			appId: Application id
			env: Application environment
			contactType: Contact type (owner.id, owner.adgrp, support etc)
			contactId : Contact id (id or group)
			requestedBy : user requesting on boarding app

		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env, ',', str(appEnvId), ',', contactType, ',', contactId, ',', requestedBy])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			self.LOGGER.info("creating app contacts as requested by user {user} .. >>> {contact}".format(contact = "".join([contactType, '<', contactId, '>']), user = requestedBy.lower()))

			"""
			if not isinstance(contactList, list):
				contactList = [contactList]requestedBy
			"""
			myContactData = {
				"appId" : appId, 
				"env" : env, 
				"appEnvId" : appEnvId,
				"contactType" : contactType, 
				"requestedBy" : requestedBy.lower(),
				"requestedTs" : self.util.lambdaGetCurrDateTime()
			}

			# changing contact id to lower case if its not a AD Group
			if contactType == self.Globals.ALL_CONTACT_TYPE_ADGRP_LIST:
				myContactData.update({"contactId" : contactId})
			else:
				myContactData.update({"contactId" : contactId.lower()})

			if contactType in [self.Globals.CONTACT_TYPE_ADMIN_ADGRP, self.Globals.CONTACT_TYPE_ADMIN_ID]:
				myContactData.update({"status" : self.Globals.STATUS_VALID})
			else:
				myContactData.update({"status" : self.Globals.STATUS_ONBOARD_ADD_ENV_APPROVAL_PENDING})

			# checking if this contact already exists
			if self.isAppEnvContactExists(securityToken, appId, env, contactType, contactId):
				# this contact already exists, skipping
				self.LOGGER.info("contact {contact} already exisits for app {app} !!!".format(\
					contact = "".join([contactType, '.', contactId]), app = "".join([str(appId), ' - ', env]) )
				)
				return

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.createAppEnvContactSql, myContactData)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))
	
			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("An error occurred while creating app env contact >>> {app}".\
					format(app = "".join([appID, ":", env, ":", contactId])))

			#newEventLog(self, securityToken, entityId, entityType, parentEntityId, parentEntityType, userId, what, comment = None)
			self.newEventLog(\
				securityToken, 
				contactId, f'app.env.contact.{contactType}', \
				appId, 'app', \
				requestedBy, 'new.app.env.contact', \
				f'new contact {contactId} - {contactType} created for app env {appId} {env}' \
			)

			return myDBResult

		except Exception as error:
			self.pg.rollback(securityToken, self.PG_CONN)
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __createAppEnvContacts(self, securityToken, appId, env, appEnvId, ownerIdList, dbTechnology, userId):
		# create new app env contact metadata 
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env, ',', str(appEnvId), str(ownerIdList), ',', dbTechnology, ',', userId ])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not isinstance(ownerIdList, list):
				myownerIdList = [self.util.getACopy(ownerIdList)]
			else:
				myownerIdList = self.util.getACopy(ownerIdList)

			# adding new contacts as requested
			self.LOGGER.info("creating app env contacts as requested .. >>> {contact}".format(contact = str(myownerIdList)))			

			for contactId in ownerIdList:
				if self.util.isAdGroup(contactId):
					myContactType = self.Globals.CONTACT_TYPE_OWNER_ADGRP # "owner.adgrp"
				else:
					myContactType = self.Globals.CONTACT_TYPE_OWNER_ID # "owner.id"

				self.__addAppEnvContacts(securityToken, appId, env, appEnvId, myContactType, contactId.lower(), userId)

			# adding admin group contact for this app's dbTechnology. there is a ctfy group for each db dbTechnology
			# we need dba admin ctfy group to be added so all app is available for approval (onboarding/deployment) and deployment

			myAdminADGroup = self.ADMIN_GROUP[dbTechnology.lower()]
			self.LOGGER.info("creating ADMIN_GRP app env contacts (sys task) .. >>> {contact}".format(contact = str(myAdminADGroup)))
			for adminContact in myAdminADGroup:
				self.__addAppEnvContacts(securityToken, appId, env, appEnvId, self.Globals.CONTACT_TYPE_ADMIN_ADGRP, adminContact, userId)

			"""
			commenting below block, we would not be storing admin id rather fetch all member of id as needed

			myAllAdminIds = self.util.getAdGroupMemberIds(myAdminADGroup)
			self.LOGGER.info("creating ADMIN (admin id) app env contacts as requested (sys task).. >>> {contact}".format(contact = str(myAllAdminIds)))
			self.__addAppEnvContacts(securityToken, appId, env, self.Globals.CONTACT_TYPE_ADMIN, myAllAdminIds, userId)
			"""

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __approveAppEnv(self, securityToken, jiraIssueId, appEnvId, userId):
		"""
		Approve Application environment by an eligible approver (admin & owner), 
		if not admin approver id must be in valid state i.e. approved by admin
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(jiraIssueId), ',', str(appEnvId), ',', str(userId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# validating arguments
			if not self.isAppEnvIdExists(securityToken, appEnvId):
				raise ValueError(f"Invalid app env id {appEnvId} !!!")

			myAppEnvDetails = self.getAnAppEnvById(securityToken, appEnvId)
			
			#print('env details >', myAppEnvDetails)

			if not myAppEnvDetails["status"]:
				raise ValueError(f'Invlaid app environment status for {appId}, expecting a vlaid status, got none !!!')

			if not(myAppEnvDetails["status"].split(".")[-1:][0].lower() == self.Globals.STATUS_PENDING.lower()):
				raise ValueError('expecting app env {app} in pending state, got >> {got} !!!'.\
					format(app = "".join([str(myAppEnvDetails["app_id"]), ' - ', myAppEnvDetails["env"]]), got = myAppEnvDetails["status"]))

			# retrieving app details
			myAppDetail = self.getAnAppDetails(securityToken, myAppEnvDetails["app_id"])

			# app env exists and its waiting for approval now validating if approver is valid userId (admin)
			myApproverIdList = self.getAppApproverIds(securityToken, myAppDetail["technology"])
			myApproverIdList = [approverId.lower() for approverId in myApproverIdList]

			self.LOGGER.debug(f'found approverid information >>> {myApproverIdList}')

			if userId.lower() not in myApproverIdList:
				raise ValueError('not a valid approver >>> {approver}'.format(approver = userId.lower()))

			myDBResult = self.__updateAppEnvContactStatus(securityToken, myAppEnvDetails["app_id"], myAppEnvDetails["env"], self.Globals.STATUS_APPROVED_MAP[myAppEnvDetails["status"]], userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				myMessage = "An error <{error}> occurred while updating app env contact status during approval !!!".format(error = myDBResult["message"])
				
				self.JiraUtil.addAComment(securityToken, jiraIssueId, myMessage)
				
				raise ValueError(myMessage)

			myDBResult = self.__updateAppEnvStatus(securityToken, myAppEnvDetails["app_id"], myAppEnvDetails["env"], self.Globals.STATUS_APPROVED_MAP[myAppEnvDetails["status"]], userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				myMessage = "An error <{error}> occurred while updating app env contact status during approval !!!".format(error = myDBResult["message"])

				self.JiraUtil.addAComment(securityToken, jiraIssueId, myMessage)

				raise ValueError(myMessage)

			self.JiraUtil.addAComment(securityToken, jiraIssueId, \
				f"User {userId} approved app {myAppEnvDetails['app_id']} environment {myAppEnvDetails['env']} successfully !!!")

			self.newEventLog(securityToken,\
				myAppEnvDetails["app_env_id"], \
				"app.env", \
				myAppEnvDetails["app_id"], \
				"app", \
				userId.lower(), \
				"app.env.approve", \
				"User {user} approved app {app} environment {env} successfully".format(user = userId, app = myAppEnvDetails['app_id'], env = myAppEnvDetails['env'])
			)

			# validating app status
			self.__validateAppStatus(securityToken, myAppEnvDetails["app_id"], userId)
			
			"""
			myAppStatus = self.getAppStatusById(securityToken, myAppEnvDetails["app_id"])
			myDetailedStatus = self.getAppDetailedStatus(securityToken, myAppEnvDetails["app_id"])

			self.JiraUtil.addAComment(securityToken, jiraIssueId, 'app {app} status has been validated, current status is {status}'.\
				format(app = ''.join([str(myAppEnvDetails["app_id"]), ',', myAppEnvDetails["env"]]), status = ''.join([myAppStatus, ' (' , myDetailedStatus, ')'])))
			"""

			return

		except Exception as error:
			self.pg.rollback(securityToken, self.PG_CONN)
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __approveApp(self, securityToken, jiraIssueId, appId, userId):
		"""
		Approve Application changes add/del schema, update deployent order, 
		if not admin approver id must be in valid state i.e. approved by admin
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(jiraIssueId), ',', str(appId), ',', str(userId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# validating arguments 
			if not (self.isAppExists(securityToken, appId)):
				raise ValueError("Invalid app id {appId} !!!".format(appId = str(appId)))

			# retrieving app details
			myAppDetail = self.getAnAppDetails(securityToken, appId)
		
			if not myAppDetail["status"]:
				raise ValueError('Invlaid app status for {app}, expecting a vlaid status, got none !!!'.format(app = str(appId)))

			if not(myAppDetail["status"].split(".")[-1:][0] == self.Globals.STATUS_PENDING):
				raise ValueError('expecting app {app} in pending state, got >> {got} !!!'.format(app = str(appId), got = myAppDetail["status"]))

			myAllAppEnnv = self.getAllPendingEnv4App(securityToken, appId)

			# looping thru all environments found for a given app

			for env in myAllAppEnnv:
				# approving this env
				#def __approveAppEnv(self, securityToken, jiraIssueId, appEnvId, userId)
				self.__approveAppEnv(securityToken, jiraIssueId, env["app_env_id"], userId)

			"""
			# validating app status
			self.__validateAppStatus(securityToken, appId, userId)

			myAppStatus = self.getAppStatusById(securityToken, myAppEnvDetails["app_id"])
			myDetailedStatus = self.getAppDetailedStatus(securityToken, myAppEnvDetails["app_id"])

			self.JiraUtil.addAComment(securityToken, jiraIssueId, 'app {app} status has been validated, current status is {status}'.\
				format(app = ''.join([str(myAppEnvDetails["app_id"]), ',', myAppEnvDetails["env"]]), status = ''.join([myAppStatus, ' (' , myDetailedStatus, ')'])))
			"""

			return

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __approveDeploy(self, securityToken, jiraIssueId, deployId, appEnvId, attemptId, userId):
		"""
		Approve successfull deployment attempt in a given environment 
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', jiraIssueId, ',', deployId, ',', str(appEnvId), ',', attemptId, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# validating arguments 
			if not (self.isDeployEnvAttemptExists(securityToken, deployId, appEnvId, attemptId)):
				raise ValueError(f"Invalid deployment {deployId} env {appEnvId} attempt {attemptId} !!!")

			myAppEnvData = self.getAnAppEnvById(securityToken, appEnvId)

			myDeployEnvData = self.getDeployEnvData(securityToken, deployId, appEnvId)
			
			# checking if deployment is successful
			if myDeployEnvData["status"] != self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS:
				raise ValueError(f"Deployment {deployId} status must be {self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS} in env {myAppEnvData['env']} !!")

			# checking if this deployment is alreadya approved
			if self.isDeployEnvApproved(securityToken, deployId, appEnvId):
				#if myDeployEnvData["status"] == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS_APPROVED:
				raise ValueError(f"Deployment {deployId} has already been approved in env {myAppEnvData['env']} !!")

			if myDeployEnvData["status"] == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS_ROLLBACK:
				raise ValueError(f"Deployment {deployId} has already been rolledback in env {myAppEnvData['env']}, no further action is allowed !!")

			# ensuring if this user is allowed to perform approval for this deployment attempt in this environment
			if not self.isValidUserForDeploy(securityToken, myAppEnvData["app_id"], myAppEnvData["env"], userId):
				raise ValueError(f"User {user} is not authorize to validate/approve deployment {deploy} in {env}  !!!".format(user = userId, deploy = deployId, env = myAppEnvData['env']))

			# approving this deployment in env
			# update status and approved by and approved ts 
			myDeployApprovalData = {
				"deployId" : deployId,
				"appEnvId" : appEnvId,
				"status" : self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS_APPROVED,
				"approvedBy" : userId,
				"approvedTs" : self.util.lambdaGetCurrDateTime(),
				#"status" : APPROVAL_STATUS_APPROVED,
				#"comments" : f"{self.util.lambdaGetCurrDateTime()} - user approved deployment with attempt id {attemptId} "
				"comments" : "{ts} - user approved deployment with attempt id {id} ".format(ts = str(self.util.lambdaGetCurrDateTime()), id = str(attemptId))
			}

			self.JiraUtil.addAComment(securityToken, jiraIssueId, f"User {userId} approved deployment id {deployId} in {myAppEnvData['env']} !!")
			
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.approveDeployEnvSql, myDeployApprovalData)

			self.newEventLog(securityToken,\
				appEnvId, \
				"deploy.env", \
				deployId, \
				"deploy", \
				userId.lower(), \
				"deploy.env.approve", \
				#f"User {userId} approved deployment {deployId} in environment {myAppEnvData['env']} successfully"
				"User {user} approved deployment {deploy} in environment {env} successfully".format(user = userId, deploy = deployId, env = myAppEnvData['env'])
			)
			
			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def approveChanges(self, securityToken, jiraIssueId, userId):
		"""
		perform validation on app status
			1. all contcats must be 'ACTIVE' (validated)
			2. app must have 1 lower and 1 prod environment in ACTIVE state
			3. all env must be in valid/active state
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(jiraIssueId), ',', str(userId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myRequestIds = self.getApprovalReqIds(securityToken, jiraIssueId, self.Globals.APPROVAL_STATUS_PENDING)

			if not myRequestIds:
				raise ValueError(f"invalid jira issue id {jiraIssueId} (no approval request found for this jira issue id) !!!")

			for request in myRequestIds:

				myRequestDetail = self.getApprovalReqDetail(securityToken, request["request_id"])

				#for request in myRequestDetail:
				if myRequestDetail["entity_type"] == "app":
					# request is app, approving app
					""" no need to check approved by as data is filtered on status
					if not (myRequestDetail["approved_by"] and myRequestDetail["approved_ts"]):
					"""
					self.__approveApp(securityToken, jiraIssueId, myRequestDetail["entity_id"], userId)
					myAppId = myRequestDetail["entity_id"]
				
				elif myRequestDetail["entity_type"] == "app.env":
					# request is app, approving app
					self.__approveAppEnv(securityToken, jiraIssueId, myRequestDetail["entity_id"], userId)
					myAppEnvDetails = self.getAnAppEnvById(securityToken, myRequestDetail["entity_id"])
					myAppId = myAppEnvDetails["app_id"]

				elif myRequestDetail["entity_type"] == "deploy.env.attempt":
					# request is approving deployment for a given attempt in env
					# retrieving deployment data for this request
					myAttemptId = myRequestDetail["entity_id"]
					myDeployAttemptData = self.getDeployAttemptData(securityToken, myAttemptId)
					myDeployId = myDeployAttemptData["deploy_id"]
					myDeployAppEnvId = myDeployAttemptData["app_env_id"]
					
					del myDeployAttemptData

					self.__approveDeploy(securityToken, jiraIssueId, myDeployId, myDeployAppEnvId, myAttemptId, userId)

				# validating status if entity belongs to app
				if myRequestDetail["entity_type"].split(".")[:1] == ["app"]:
					myAppStatus = self.getAppStatusById(securityToken, myAppId)
					myDetailedStatus = self.getAppDetailedStatus(securityToken, myAppId)
					myValidationMsg = 'app {app} status has been validated, current status is {status}'.format(app = str(myAppId), status = ''.join([myAppStatus, ' (' , myDetailedStatus, ')']))
					
					self.JiraUtil.addAComment(securityToken, jiraIssueId, myValidationMsg)

					self.newEventLog(securityToken,\
						myRequestDetail["entity_id"], \
						'app', \
						myRequestDetail["entity_id"], \
						'app', \
						userId.lower(), \
						'app.validate', \
						myValidationMsg
					)

				# marking this request as approved
				self.completeApprovalRequest(securityToken, myRequestDetail["request_id"], userId)

			# commiting changes
			self.pg.commit(securityToken, self.PG_CONN)

		except Exception as error:
			self.pg.rollback(securityToken, self.PG_CONN)
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getApprovalReqDetail(self, securityToken, requestId):
		"""
		Retrieves approval request detail for a given requestId
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(requestId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getApprovalReqDetailSql, {"requestId" : requestId})

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["status"])

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]}")
				return myDBResult["data"][0]

		except Exception as error:
			self.LOGGER.error("An error occurred while executing {module} >>> {error}".format(error = str(error), module = myModule), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __updateAppStatus(self, securityToken, appId, status, userId):
		"""
		update app status
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', status, ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.LOGGER.info('updating app {app} status to {status} '.format(app = str(appId), status = status))

			myStatusData = {"appId" : appId, "status" : status}

			if status in [self.Globals.STATUS_VALID, self.Globals.STATUS_ACTIVE]:
				# we have got status as approved (valid/active), need to inject approver details
				myStatusData.update ({
					"approvedBy" : userId,
					"approvedTs" : self.util.lambdaGetCurrDateTime(),
				})
				mySql = self.updAppStatusWApprovalSql
			else:
				#mySql = self.updAppStatusWApprovalSql
				mySql = self.updAppStatusSql

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, mySql, myStatusData)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.newEventLog(securityToken, appId, 'app', appId, 'app', userId.lower(), 'modify.app.status', 'app.status changed to [{status}] by [{id}]'.format(status = status, id = userId))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __updateAppEnvStatus(self, securityToken, appId, env, status, userId):
		"""
		update app env status
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env, ',', status, ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.LOGGER.info('updating app {app} env status to {status} '.format(app = str(appId), status = status))

			myAppEnvId = self.getAppEnvId(securityToken, appId, env)

			myStatusData = {
				"appEnvId" : myAppEnvId, 
				"status" : status
			}
			
			if status in [self.Globals.STATUS_VALID, self.Globals.STATUS_ACTIVE]:
				myStatusData.update(
					{"approvedBy" : userId, "approvedTs" : self.util.lambdaGetCurrDateTime()})
				mySql = self.updEnvStatusWApprovalSql
			else:
				mySql = self.updEnvStatusSql

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, mySql, myStatusData)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.newEventLog(securityToken, appId, 'app', appId, 'app', userId.lower(), 'modify.app_env.status', \
				'app_env.status [{app}] changed to [{status}] by [{id}]'.format(app = ''.join([str(appId),'.',env]), status = status, id = userId))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			#self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __updateAppEnvContactStatus(self, securityToken, appId, env, status, userId):
		"""
		update app env contact status for a given app and its environment
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env, ',', status, ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.LOGGER.info('updating app {app} env contact status to {status} '.format(app = str(appId), status = status))

			myAppEnvId = self.getAppEnvId(securityToken, appId, env)

			myStatusData = {
				#"appId" : appId,
				"appEnvId" : myAppEnvId,
				"status" : status
			}			

			if status in [self.Globals.STATUS_VALID, self.Globals.STATUS_ACTIVE]:
				myStatusData.update(
					{"approvedBy" : userId, "approvedTs" : self.util.lambdaGetCurrDateTime()})
				mySql = self.updContactStatusWApprovalSql
			else:
				mySql = self.updContactStatusSql

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, mySql, myStatusData)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.newEventLog(securityToken, appId, 'app', appId, 'app', userId.lower(), 'app.env.contact.approve', 'app environment contacts [{appEnv}] approved by [{id}]'.format(appEnv = ''.join([str(appId), '.', env]) , id = userId))
			
			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			#self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __validateAppStatus(self, securityToken, appId, userId):
		"""
		perform validation on app status
			1. all contcats must be 'ACTIVE' (validated)
			2. app must have 1 lower and 1 prod environment in ACTIVE state
			3. all env must be in valid/active state
		"""
		try:
			#self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', appName, ',', env])))
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', str(userId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not (self.isAppExists(securityToken, appId)):
				raise ValueError("Invalid app id {appId} !!!".format(appId = str(appId)))

			#if self.getAppStatusById(securityToken, appId) not in [self.Globals.STATUS_DELETED, self.Globals.STATUS_VALID]:
				# app status is already valid
			#	return

			myAppStatus = self.getAppStatusById(securityToken, appId)

			if not (myAppStatus.split(".")[-1:][0].lower() == self.Globals.STATUS_PENDING):
				# app is not in pending state, nothing to be vaidates
				raise ValueError(f"App status is not in pending state, expecting pending state, got {myAppStatus}")

			if not (self.isValidApprover(securityToken, userId)):
				raise ValueError("Invalid approver id {approver} !!!".format(approver = str(userId)))

			# hardcoding rule for app status validation

			# retrieving all env for this app
			myAllEnvDetails = self.getAppEnvDetails(securityToken, appId)

			# we need to find all env which is in pending state for this app
			myPendingEnv = self.getAllPendingEnv4App(securityToken, appId)

			if myPendingEnv:
				self.LOGGER.info('found pending env for app {app} >>> {env}'.format(app = str(appId), env = str(myPendingEnv))) 
				return

			# checking for any pending contacts for each env of this application
			myAllEnvPendingContacts = []
			for env in myAllEnvDetails:
				myPendingContacts = self.getPendingAppContacts(securityToken, appId, env["env"])

				if myPendingContacts:
					myAllEnvPendingContacts.append({"env" : env["env"], "pendingContacts" : myPendingContacts})

			if myAllEnvPendingContacts:
				self.LOGGER.info('found pending contacts for app {app} >>> {contacts}'.format(app = str(appId), contacts = str(myAllEnvPendingContacts)))
				return

			"""
			# loop thru all environment to validate/populate the status
			for env in myAllEnvDetails:

				myPendingContacts = self.getPendingAppContacts(securityToken, appId, env["env"])

				self.LOGGER.info('found pending contacts for env {env} >>> {contacts}'.format(env = env["env"], contacts = str(myPendingContacts)))

				if myPendingContacts:
					return
			"""

			# all environment is in approved status, need to check if we got 1 lower and 1 prod
			# environment

			# building environment list and removing environment which might have been marked as inactive/del
			#myAllEnvList = [env["env"].lower() for env in myAllEnvDetails if len(env["env"].lower().split(".")) == 1 ]
			myAllEnvList = [env["env"].lower() for env in myAllEnvDetails ]
			
			#myAppDetail = self.getAnAppDetails(securityToken, appId)

			"""
			commenting below code, we would rather validate against dbaas (all env recorded in dbaas must be onboarded in CICD)
			# we need prod and atleast 1 lower environment for application to be fully approved (status = active)
			if self.Globals.ENV_PROD in myAllEnvList and any(env in myAllEnvList for env in self.Globals.ENV_LOWER):
				
				self.LOGGER.info('alll validation met, making application {app} active'.format(app = ''.join([myAppDetails["app_name"], ".", str(appId)])))

				self.__updateAppStatus(securityToken, appId, self.Globals.STATUS_VALID, userId)
			"""

			# we need to check if all the env as recorded in dbass hs been on boarded, replace above with this
			myAppDetails = self.getAnAppDetails(securityToken, appId)

			myDBResult = self.dbaasGetAllUniqueEnvs(\
					securityToken, \
					myAppDetails["opco"], \
					myAppDetails["region"], \
					myAppDetails["technology"], \
					myAppDetails["app_id"]
			)

			#print('dbaas all env >', myDBResult)
			myAllAppEnvFromDbaas = [env["ENV"].lower() for env in myDBResult]

			self.LOGGER.debug(f"env onboarded > {myAllEnvList}, env recorded in dbaas > {myAllAppEnvFromDbaas}")

			if self.util.isListItemExistsInAList(myAllAppEnvFromDbaas, myAllEnvList):
			#if self.Globals.ENV_PROD in myAllEnvList and set(myAllEnvList) == set(myAllAppEnvFromDbaas):
				myMessage = 'all validation met, making application {app} status active (ready for deployment) '.format(app = ''.join([myAppDetails["app_name"], ".", str(appId)]))
				self.__updateAppStatus(securityToken, appId, self.Globals.STATUS_VALID, userId)
			else:
				myMessage = 'all env recorded in dbaas is not on boarded for app >> {app} !!'.format(app = ''.join([myAppDetails["app_name"], ".", str(appId)]))

			self.LOGGER.info(myMessage)

			self.newEventLog(securityToken,\
				myAppDetails["app_id"], \
				'app', \
				myAppDetails["app_id"], \
				'app', \
				userId.lower(), \
				'app.status.validate', \
				f'validation msg : {myMessage}'
			)


		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def refreshAppAdminApprover(self, securityToken, userId):
		"""
		populated valid approver DBA Admin (retrieve networkId from valid CTFY group). 
		Transaction is controlled in this method, no external commit/rollback is allowed
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
							self.newEventLog(securityToken, user, 'new.approver',user, 'new.approver', user,'new.approver.created')

					self.LOGGER.info('completed populating user from ctfy group >>> {ctfygrp}'.format(ctfygrp = ctfyGrp))
				self.LOGGER.info('completed processing ctfy group for region >>> {region}'.format(region = myregion))
	
			# commiting data
			self.pg.commit(securityToken, self.PG_CONN)
			self.LOGGER.info('valid approver list populated successfully')

		except Exception as error:
			self.LOGGER.error('an error occurred while populating valid approver list >>> {error}'.format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def refreshAppDeployApprover(self, securityToken, userId):
		"""
		we would not need this for now
		populated valid app deployment approver (app_env_owner) (retrieve networkId from valid CTFY group).
		find all ad group from app_env_contact and get its userid from ad group 
		Transaction is controlled in this method, no external commit/rollback is allowed
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
						
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# retrieve all app env contacts (app which is not in pending state)
			#[contact["contacts"] for contact in [env for env in [app for app in myAllValidApp]["env"]]]
			
			# we need another wrapper on getAllAppDetails to get all app for all opco/region/technology ? or pass param (opco/region/tech) on this method

			myAllValidApp = self.getAllAppDetail(securityToken, opco, region, dbTechnology, self.Globals.STATUS_VALID)
			# retrieving all contacts for all valid apps which need to be processed
			
			for app in myAllValidApp:
				for env in app["env"]:
					for contact in env["contacts"]:
						if contact["contact_type"] == self.Globals.CONTACT_TYPE_OWNER_ADGRP:
							self.LOGGER.debug("app env contact is AD group, processing  >>> {app}".format(app = "".join([contact["app_id"], ".", contact["env"], ".", contact["contact_id"]])))

							myUserIds = self.util.getAdGroupMemberIds([adGrp])					

							for userId in myAppEnvUserIds:
								myAppEnvOwnerData.append({
									"app_id" : contact["app_id"],
									"env" : contact["env"],
									"ad_group" : contact["contact_id"],
									"user_id" : userId,
									"user_name" : self.util.getADGrpUserName(userId),
									"ts" :  self.util.lambdaGetCurrDateTime()
								})
		
							myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newAppEnvOwnerSql, myAppEnvOwnerData)

							if myDBResult["status"] == self.Globals.unsuccess:
								raise ValueError(myDBResult["message"])
							else:
								self.LOGGER.debug("new app owner id {id} is created ".format(id = str(myDBResult["data"])))
						else:
							self.LOGGER.debug("app env contact is not AD group, skipping >>> {app}".format(app = "".join([contact["app_id"], ".", contact["env"], ".", contact["contact_id"]])))

			self.LOGGER.info("all app env contact processed successfully, commiting data")
	
			# commiting data
			self.pg.commit(securityToken, self.PG_CONN)
			self.LOGGER.info('app env owner populated successfully !!!')

		except Exception as error:
			self.LOGGER.error('an error occurred while populating app env owner list >>> {error}'.format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def newEventLog(self, securityToken, entityId, entityType, parentEntityId, parentEntityType, userId, what, comment = None):
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
				myComment = "".join([str(myCurrentReadableTs), ' - user [' , userId.lower(), '] - ', comment])
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
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __markAppPending(self, securityToken, appId, pendingStatus, userId):
		"""
		Mark application in pending state. Update app.apps/app.app_envs/app.app_env_contacts status to Pending
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			self.LOGGER.info('updating app {app} status to {pending} '.format(app = str(appId), pending = self.Globals.STATUS_PENDING))

			myStatusData = {"appId" : appId, "status" : pendingStatus}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updAppStatusSql, myStatusData)

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updAllAppEnvStatusSql, myStatusData)

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updAllAppEnvContactStatusSql, myStatusData)
		
			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.newEventLog(securityToken, appId, 'app', appId, 'app', userId.lower(), 'modify.app.status', \
				'user {userId} requested application {app} and its all environment and contacts to be marked Pending'.format(app = str(appId), userId = userId))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			#self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __markAppEnvPending(self, securityToken, appId, appEnvId, pendingStatus, userId):
		"""
		Mark application env in pending state. Update app.apps/app.app_envs/app.app_env_contacts status to Pending
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			self.LOGGER.info(f'updating app {appId} appenv {appEnvId} status to {self.Globals.STATUS_PENDING} ')

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updAppStatusSql, {"appId" : appId, "status" : pendingStatus})

			#myStatusData = {"appEnvId" : appEnvId, "status" : pendingStatus}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updEnvStatusSql, {"appEnvId" : appEnvId, "status" : pendingStatus})

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updContactStatusSql, {"appEnvId" : appEnvId, "status" : pendingStatus})
		
			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.newEventLog(securityToken, appId, 'app', appId, 'app', userId.lower(), 'modify.app.status', \
				'user {userId} requested application {app} and its all environment and contacts to be marked Pending'.format(app = str(appId), userId = userId))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			#self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	# modifying on boarded app

	# any changes to onboading app needs approval, 
	# changes to an exisitng app would force the status to Pending and its relevant environment
	# create a new process to approve this change based on appId

	# getAllOnboardedApp --> self.getMyAppList

	def getAppDeployOrder(self, securityToken, appId):
		"""
		returns deployment env order for a given cicd application
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
						
			if self.isAppExists(securityToken, appId):
				myAppDetail = self.getAnAppDetails(securityToken, appId)
				return myAppDetail["deploy_env_order"]

		except Exception as error:
			self.LOGGER.error('an error occurred while retrieving application deploy environment order >>> {error}'.format(error = str(error)), exc_info = True)
			#self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def getOnboardedAppSchema(self, securityToken, appId):
		"""
		returns on boarded schema for a given app
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
						
			if self.isAppExists(securityToken, appId):
				myAppDetail = self.getAnAppDetails(securityToken, appId)
				return myAppDetail["db_schemas"]

		except Exception as error:
			self.LOGGER.error('an error occurred while retrieving application deploy environment order >>> {error}'.format(error = str(error)), exc_info = True)
			#self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def getDBSchema2Add2App(self, securityToken, opco, region, dbTechnology, appId):
		"""
		Returns alll available schema(s) for onboarding, pull all schemas which is present in all environment in 
		DBAAS repository and substract the schemas which is already onboarded.
		For e.g. 
			DBAAS
				App : CANSYS
					DEV (schema) : ACT, CERT, ACTIVITY
					STG (schema) : ACT, CERT
					PROD (schema) : ACT, CERT

			CICD App : CANSYS
					DEV (schema) : ACT

			Should return CERT schema to be added

		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', opco, ',', region, ',', dbTechnology, ',', str(appId) ])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# retrieving available schema from dbaas

			if dbTechnology.lower() == self.Globals.TECHNOLOGY_ORACLE.lower():
				#def dbaasGetOraDBCommonSchemas(securityToekn, opco, region, dbTechnology, appId)
				mydbaasDBSchema = self.dbaasGetOraDBCommonSchemas(securityToken, opco, region, dbTechnology, appId)
			else:
				return

			self.LOGGER.info('found schema list from dbaas for app {app} >>> {schemaList}'.format(app = str(appId), schemaList = str(mydbaasDBSchema)))

			if not mydbaasDBSchema:
				return

			# retrieving all schema in use for this db instance from repository

			myCriteria = {
				"appId" : appId,
				"opco" : opco.lower(),
				"region" : region.lower(), 
				#"dbInstance" : dbInstance, 
				"dbTechnology" : dbTechnology.lower()
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDBSchemaInUseSql, myCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError('error while retrieving in-use schema list from repository for app >>> {app}'.format(app = str(appId)))

			self.LOGGER.info('found schema list in use from CICD repository for app {app} >>> {schemaList}'.format(app = str(appId), schemaList = str(myDBResult["data"])))

			# available schema for onboarding
			if myDBResult["data"]:
				mySchemaInUseList = myDBResult["data"][0]["db_schemas"]
			else:
				mySchemaInUseList = []

			#print('dbaas schema >>>', mydbaasDBSchema)
			#print('in use schema >>>', mySchemaInUseList)

			myAvailableSchemaList = list(set([schema['SCHEMA'] for schema in mydbaasDBSchema]) - set(mySchemaInUseList))

			self.LOGGER.info('returning available schema list for {app} >>> {schemaList}'.format(app = str(appId), schemaList = str(myAvailableSchemaList)))

			return myAvailableSchemaList

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDBSchema4OnBoardingByAppId(self, securityToken, appId, userId):
		"""
		returns all available schema for onboarding for a given app id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myDbaasAppInfo = self.dbaasGetAppInfoByAppId(securityToken, appId)

			if myDbaasAppInfo:
				#getDBSchema4OnBoarding(self, securityToken, opco, region, dbTechnology, appId)
				myDBResult = self.getDBSchema4OnBoarding(securityToken, myDbaasAppInfo["OPCO"], myDbaasAppInfo["REGION"], myDbaasAppInfo["DB_TECHNOLOGY"], appId)
				return myDBResult

		except Exception as error:
			self.LOGGER.error('an error occurred while retrieving application schema for onborading for a given app id >>> {error}'.format(error = str(error)), exc_info = True)
			#self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	# Add schemas
	#	1. App and its env to 'Pending' state
	# Remove Schema
	#	1. App and its env status to 'Pending' state
	# remove env
	#	1. change app status to Pending

	def addNewSchema2App(self, securityToken, jiraIssueId, appId, schemaList, userId):
		"""
		add new schema to an onboarded app (would not change the status of application)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', jiraIssueId, ',', str(appId), ',', str(schemaList)])))
			
			myModule = sys._getframe().f_code.co_name

			if not isinstance(schemaList, list):
				raise ValueError("Invalid arguments (schemaList argument must be type of array) !!!")

			self.sec.validateSecToken(securityToken)
			
			if not self.isAppExists(securityToken, appId):
				raise ValueError("Invalid app {appId} !!!".format (app = str(appId)))

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)
			# need to perform validation, (check if any application is in-progress) 

			myAppDetail = self.getAnAppDetails(securityToken, appId)

			myExistingSchema = myAppDetail["db_schemas"]

			#print("exisitng schema >>", myExistingSchema)

			#self.LOGGER.debug("got exisitng schema list for this app {id} >> {schema}".format(id = str(appId), schema = str(myExistingSchema)))
			myExistingSchema.extend(schemaList)

			#print("new schema >>", myExistingSchema)

			myNewSchmeaList = list(set(myExistingSchema))

			#print("new schema (after removing duplicate) >>", myNewSchmeaList)

			myUpdateData = {"appId" : appId, "dbSchemas" : myNewSchmeaList}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updAppDBSchemaSql, myUpdateData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise (myDBResult["message"])

			# updating all application environment db schemas
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updAppEnvDBSchemaSql, myUpdateData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise (myDBResult["message"])

			# changing applicarion status to 'Pending'
			myDBResult = self.__markAppPending(securityToken, appId, self.Globals.STATUS_ONBOARD_ADD_SCHEMA_APPROVAL_PENDING, userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise (myDBResult["message"])

			# logging this event
			#self.newEventLog(securityToken, appId, 'app', appId, 'app', userId.lower(), 'add.app.schema', \
			#	f'user {userId} requested to add {schemaList} to application {appId}')

			# adding this to our request for approval			
			myDBResult = self.newRequestForApproval(securityToken, jiraIssueId, appId, 'app','onboard.new.app.schema', userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise (myDBResult["message"])

			myRequestId = myDBResult["data"][0]["request_id"]

			self.LOGGER.info("new request {id} is created for approving this task".format(id = str(myRequestId)))

			self.JiraUtil.addAComment(securityToken, jiraIssueId, f"Schema ({schemaList}) added to application {appId} pending approval ")

			# logging event
			#newEventLog(self, securityToken, entityId, entityType, parentEntityId, parentEntityType, userId, what, comment = None)
			self.newEventLog(\
				securityToken, 
				appId, 'aap', \
				appId, 'app', \
				userId.lower(), 'new.app.schema', \
				f'added new schema {schemaList} to application {appId} as requested by {userId}' \
			)

			return myDBResult

		except Exception as error:
			self.pg.rollback(securityToken, self.PG_CONN)
			self.LOGGER.error('an error occurred while updating db schemas for app {app} >>> {error}'.format(app = str(appId), error = str(error)), exc_info = True)
			raise error

	def validateAppSchemaInEnv(securityToken, opco, region, dbTechnology, appId, schemaList):
		"""
		Validates existence of schema in all environment for a given application (this method should be called before persisting application and its schema relation
		, especially in onboarsapp, addSchema2App, removeSchemaFromApp)
		"""
		pass

	def removeSchemaFromApp(self, securityToken, jiraIssueId, appId, schemaList, userId):
		"""
		remove an exisitng schema from an onboarded app (would not change the status of application)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', jiraIssueId, ',', str(appId), ',', str(schemaList), ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			if not isinstance(schemaList, list):
				raise ValueError("Invalid arguments (schemaList argument must be type of array) !!!")

			if not self.isAppExists(securityToken, appId):
				raise ValueError("Invalid app {appId} !!!".format (app = str(appId)))

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)
			# need to perform validation, (check if any application is in-progress) 
			myAppDetail = self.getAnAppDetails(securityToken, appId)
			
			myExistingSchema = myAppDetail["db_schemas"]

			myNewSchmeaList = list(set([schema for schema in myExistingSchema if schema not in schemaList]))

			if not myNewSchmeaList:
				raise ValueError("Schema list can not be empty, an applicstion must have atleast 1 schmea !!!")

			myUpdateData = {"appId" : appId, "dbSchemas" : myNewSchmeaList}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updAppDBSchemaSql, myUpdateData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise (myDBResult["message"])

			# updating all application environment db schemas

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updAppEnvDBSchemaSql, myUpdateData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise (myDBResult["message"])

			# changing applicarion status to 'Pending'
			myDBResult = self.__markAppPending(securityToken, appId, self.Globals.STATUS_ONBOARD_DEL_SCHEMA_APPROVAL_PENDING, userId)
			if myDBResult["status"] == self.Globals.unsuccess:
				raise (myDBResult["message"])

			# logging this event
			#self.newEventLog(securityToken, appId, 'app', appId, 'app', userId.lower(), 'onboard.del.app.schema', \
			#	f'user {userId} requested to remove {schemaList} from application {appId}')

			# adding this to our request for approval
			myDBResult = self.newRequestForApproval(securityToken, jiraIssueId, appId, 'app','onboard.del.app.schema', userId)
			if myDBResult["status"] == self.Globals.unsuccess:
				raise (myDBResult["message"])

			myRequestId = myDBResult["data"][0]["request_id"]
			self.LOGGER.info("new request {id} is created for approving this task".format(id = str(myRequestId)))

			self.JiraUtil.addAComment(securityToken, jiraIssueId, f"Schema ({schemaList}) removed from application {appId} pending approval ")

			# logging event
			#newEventLog(self, securityToken, entityId, entityType, parentEntityId, parentEntityType, userId, what, comment = None)
			self.newEventLog(\
				securityToken, 
				appId, 'aap', \
				appId, 'app', \
				userId.lower(), 'del.app.schema', \
				f'removed schema {schemaList} from application {appId} as requested by {userId}' \
			)

			return myDBResult

		except Exception as error:
			self.pg.rollback(securityToken, self.PG_CONN)
			self.LOGGER.error('an error occurred while updating db schemas for app {app} >>> {error}'.format(app = str(appId), error = str(error)), exc_info = True)
			raise error

	def removeAppEnv(self, securityToken, jiraIssueId, appId, env, newDeployEnvOrder, userId):
		"""
		remove an exisitng application environment from CICD repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', jiraIssueId, ',', str(appId), ',', env, ',', str(newDeployEnvOrder), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			#myJiraCls = JiraUtility(securityToken, jiraIssueId)

			if not self.isAppEnvExists(securityToken, appId, env):
				raise ValueError("Invalid app env {appEnv} !!!".format(appEnv = "".join([str(appId), ".", env])))

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)
			# need to perform validation, (check if any application is in-progress) 
			myAppDetail = self.getAnAppDetails(securityToken, appId)
			
			# will update the status to inactive and update the env to env.inactive
			# remove env from deploy env order, mark the app to pending and submit this request to approval queue (app.app_approvals)

			# we need to find total env for this app, minumum 1 env is needed for a given app

			myAppEnvId = self.getAppEnvId(securityToken, appId, env)

			# getting inactive count
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getInactiveEnvCount, {"appId" : appId, "inActiveEnv" : "".join([env,".inactive"])})
			myInactiveCount = myDBResult["data"][0]["total"]
			myInactiveCount += 1

			myUpdateData = {"appEnvId" : myAppEnvId, "inActiveEnv" : "".join([env,'.del.', str(myInactiveCount).zfill(3)])}
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.markAppEnvInactiveSql, myUpdateData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise (myDBResult["message"])

			#myDeployEnvOrder = self.getAppDeployOrder(securityToken, appId)
			
			#self.LOGGER.debug(f"found deploy env order {myDeployEnvOrder}, pop {env}")
		
			#myDeployEnvOrder = [myEnv for myEnv in myDeployEnvOrder if myEnv.lower() not in env.lower()]

			myDBResult = self.__updAppDeployEnvOrder(securityToken, appId, newDeployEnvOrder, userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise (myDBResult["message"])

			# changing applicarion status to 'Pending'
			myDBResult = self.__markAppEnvPending(securityToken, appId, myAppEnvId, self.Globals.STATUS_ONBOARD_DEL_ENV_APPROVAL_PENDING, userId)
			if myDBResult["status"] == self.Globals.unsuccess:
				raise (myDBResult["message"])

			# logging this event
			#self.newEventLog(securityToken, appId, 'app', appId, 'app', userId.lower(), 'del.app.schema', \
			#	f'user {userId} requested to remove {env} for this application {appId}')

			# adding this to our request for approval
			myDBResult = self.newRequestForApproval(securityToken, jiraIssueId, myAppEnvId, "app.env","onboard.del.app.env", userId)
			if myDBResult["status"] == self.Globals.unsuccess:
				raise (myDBResult["message"])

			myRequestId = myDBResult["data"][0]["request_id"]
			self.LOGGER.info("new request {id} is created for approving this task".format(id = str(myRequestId)))

			self.JiraUtil.addAComment(securityToken, jiraIssueId, "Application environment ({appEnv}) removed pending approval ".format(appEnv = "".join([str(appId), ".", env])))

			# logging event
			#newEventLog(self, securityToken, entityId, entityType, parentEntityId, parentEntityType, userId, what, comment = None)
			self.newEventLog(\
				securityToken, 
				myAppEnvId, 'aap.env', \
				appId, 'app', \
				userId.lower(), 'del.app.env', \
				f'removed env {env} ({myAppEnvId} from application {appId} as requested by {userId}' \
			)

			return myDBResult

		except Exception as error:
			self.pg.rollback(securityToken, self.PG_CONN)
			self.LOGGER.error('an error occurred while updating db schemas for app {app} >>> {error}'.format(app = str(appId), error = str(error)), exc_info = True)
			raise error

	def __updAppDeployEnvOrder(self, securityToken, appId, deployEnvOrder, userId):
		"""
		update app deploy env order, replaces exisiting env order with new env order
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', str(deployEnvOrder), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.LOGGER.info('replacing app [{app}] deploy env order to [{env}] '.format(app = str(appId), env = str(deployEnvOrder)))

			myDeployEnvOrder = [deployEnvOrder] if not isinstance(deployEnvOrder, list) else self.util.getACopy(deployEnvOrder)
			myDeployEnvOrder = [env.lower() for env in myDeployEnvOrder]

			# validating
			for env in myDeployEnvOrder:
				if not self.isAppEnvExists(securityToken, appId, env.lower()):
					raise ValueError(f"invalid environment {env} for app {appId} (env stated in deployment env order is missing from cicd repository) !!!")

			myEnvOrderData = {"appId" : appId, "deployEnvOrder" : myDeployEnvOrder}

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)
			
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updAppEnvOrderSql, myEnvOrderData)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.newEventLog(\
				securityToken, 
				appId, 'app', \
				appId, 'app', \
				userId.lower(), 'upd.app.deployEnvOrder', \
				f'deploy env order updated for app {appId} as requested by {userId}, new deployment order is -> {myDeployEnvOrder}' \
			)

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def updAppDeployEnvOrder(self, securityToken, jiraIssueId, appId, deployEnvOrder, userId):
		"""
		wraper for updAppDeployEnvOrder, we are making this request to go thru approval process
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', jiraIssueId, str(appId), ',', str(deployEnvOrder), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myDBResult = self.__updAppDeployEnvOrder(securityToken, appId, deployEnvOrder, userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			# pending this application so changes can be approved
			myDBResult = self.__markAppPending(securityToken, appId, self.Globals.STATUS_ONBOARD_UPD_DEPLOYORDER_APPROVAL_PENDING, userId)
			if myDBResult["status"] == self.Globals.unsuccess:
				raise (myDBResult["message"])

			self.JiraUtil.addAComment(securityToken, jiraIssueId, f"Application {appId} deployment env order changed to {deployEnvOrder}")

			myDBResult = self.newRequestForApproval(securityToken, jiraIssueId, appId, "app","onboard.upd.app.deployOrder", userId)
			if myDBResult["status"] == self.Globals.unsuccess:
				raise (myDBResult["message"])

			myRequestId = myDBResult["data"][0]["request_id"]
			self.LOGGER.info("new request {id} is created for approving this task".format(id = str(myRequestId)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	# request for approval

	def newRequestForApproval(self, securityToken, jiraIssueId, entityId, entityType, requestType, userId):
		"""
		Adds a request for approval for following request type
			requestType			enityId 		entityType
			==========================================================
			new.app.env 		<appEnvId> 		app.env
			remove.app.env      <appEnvId>      app.env
			new.deploy 			<deployId>		deploy
			deploy.????
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', jiraIssueId, ',', str(entityId), ',', entityType, ',', requestType, ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myRequestData = {
				"extReferenceId" : jiraIssueId, 
				"entityId" : entityId, 
				"entityType" : entityType, 
				"requestType" : requestType, 
				"requestedBy" : userId, 
				"requestedTs" : self.util.lambdaGetCurrDateTime(),
				"comments" : "".join([self.util.lambdaGetCurrReadableTime(), f" - new request for approval [{requestType}, {jiraIssueId}] is created by {userId} "])
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newRequestForApprovalSql, myRequestData)

			self.LOGGER.info("returning >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error('an error occurred while creating new request for approval (request: {request})>>> {error}'.\
				format(request = "".join([entityType, ".", str(entityId), " - ", requestType, " ext ref id -> ", jiraIssueId]), error = str(error)), exc_info = True)
			raise error

	def getApprovalRequestId(self, securityToken, entityType, entityId, requestType):
		"""
		Retrieves request id for a given entity type, entity id and requesttype (may return multiple rows)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', entityType, ',', str(entityId), ',', requestType ])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myRequestCriteria = {"entityType" : entityType, "entityId" : entityId, "requestType" : requestType}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getApprovalRequestIdSql, myRequestCriteria)

			self.LOGGER.info("db result >>> {result}".format(result = str(myDBResult)))

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['request_id']}")
				return myDBResult["data"][0]["request_id"]

		except Exception as error:
			self.LOGGER.error('an error occurred while retrieving approval request {request} >>> {error}'.\
				format(request = "".join([str(entityId), ".", entityType, " - ", requestType]), error = str(error)), exc_info = True)
			raise error

	def getApprovalReqIds(self, securityToken, extReferenceId, status):
		"""
		Retrieves pending approval request ids (there may be multiple request pending) for a given external reference id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', extReferenceId ])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myRequestCriteria = {"extReferenceId" : extReferenceId, "status" : status}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getApprovalReqIdsSql, myRequestCriteria)

			self.LOGGER.info("db result >>> {result}".format(result = str(myDBResult)))

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data']}")
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error('an error occurred while retrieving approval request {request} >>> {error}'.\
				format(request = "".join([str(entityId), ".", entityType, " - ", requestType]), error = str(error)), exc_info = True)
			raise error

	def completeApprovalRequest(self, securityToken, requestId, approvedBy):
		"""
		approve given request id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(requestId), ',', approvedBy ])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myApprovalData = {
				"requestId" : requestId, 
				"approvedBy" : approvedBy, 
				"approvedTs": self.util.lambdaGetCurrDateTime(),
				"status" : self.Globals.APPROVAL_STATUS_APPROVED,
				"comments" : "".join([self.util.lambdaGetCurrReadableTime(), f" - request approved by user {approvedBy}"])
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.completeApprovalRequestSql, myApprovalData)

			self.LOGGER.info("returning >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error('an error occurred while approving request {request} >>> {error}'.format(request = str(requestId), error = str(error)), exc_info = True)
			raise error

	"""
	1. modifying (add/remove) db schema for onboarded app
		def getAppSchemaFromCICD(self, securityToken, appId):

		def getDBSchema4OnBoardingByAppId(self, securityToken, appId):
			Returns all application schema available for onboarding (called from modify in jira) (need to get app details from CICD and call
			getDBSchema4OnBoarding)

		def appSchema2App(self, securityToken, appId, schemaList):
			Add a new schema to an already onboarded app

		def removeSchemaFromApp(self, securityToken, appId, schemaList):
			Remove schema from already onboarded app (make it inactive)

	2. Remove an env for onboarded app
		1. Get list of all the environment onboarded for this app (appId)
		2. Remove an environment from existing app
			Remove environment and update deployenvorder
			delAppEnv(securityToken, appId, env, deployEnvOrder)
	3. Change Deploy Env Order
	"""
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

				myOracleUser = self.infra.environment["boot"]["deploy"]["oracle"][myEnv]["user"]
				myOracleUserEncPass = self.infra.environment["boot"]["deploy"]["oracle"][myEnv]["userEncPass"]

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

	def createNewDeployment(self, securityToken, jiraIssueId, deployId, deploySource, deploySourceId, appId, userId):
		"""
		creates new deployment in repository (populate deploy, deploy_control, deploy_files and deploy_tasks)
		Arguments:
			deployId: Deployment id (Jira issue id)
			appId: Application id to which this deployment belongs to
			userId: User requesting this deployment
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', jiraIssueId, ',', deployId, str(appId), ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# validate new deployment data
			#self.validateNewDeployment(securityToken, deployId, appId, userId, deplo)

			# need app id, get Application detail
			myAppDetail = self.getAnAppDetails(securityToken, appId)
			#myJira = JiraUtility(securityToken, jiraIssueId)

			# create new deployment ctrl id
			myDeployFileLocation = self.util.buildPath(self.Globals.DEPLOY_DOWNLOAD_LOC, str(deployId))

			#__createNewDeployCtrl(self, securityToken, deployId, appId, deployFileLocation, userId)
			myDBResult = self.__createNewDeployCtrl(securityToken, deployId, appId, myDeployFileLocation, userId)

			self.LOGGER.info("create new deploy ctrl db result >> {result}".format(result = str(myDBResult)))

			myNewDeployCtrlId = myDBResult["data"]

			if not(myDBResult["status"] == self.Globals.success and myNewDeployCtrlId):
				raise ValueError("An error <{error}> occurred while creating new deployment ctrl id for deployment {deployId} !!!".\
					format(error = myDBResult["message"], deployId = deployId))

			# creating new deployment
			#__newDeploy(self, securityToken, deployId, deploySource, deploySourceId, jiraIssueId, appId, appName, dbTechnology, deployEnvOrder, deployCtrlId, deployFileLocation, userId)
			myDBResult = self.__newDeploy(securityToken, deployId, deploySource, deploySourceId, jiraIssueId, myAppDetail["app_id"], myAppDetail["app_name"], myAppDetail["technology"], \
				myAppDetail["deploy_env_order"], myNewDeployCtrlId, myDeployFileLocation, userId)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("An error <{error}> occurred while saving deployment data !!!".format(error = myDBResult["message"]))

			# processing deployment files
			#__processDeployFiles(self, securityToken, deployId, appId, dbTechnology, deployCtrlId, deployFileLocation, userId)
			myParseResult = self.__processDeployFiles(securityToken, deployId, myAppDetail["app_id"], myAppDetail["technology"], myNewDeployCtrlId, myDeployFileLocation, userId)

			#if myDBResult["status"] == self.Globals.unsuccess:
			#	raise ValueError("An error <{error}> occurred while saving deployment data !!!".format(error = myDBResult["message"]))

			myParsedFile = myParseResult["data"]
			
			# updating deployment attempt, this is 1st attempt
			myDBResult = self.__updDeployValidationAttempt(securityToken, jiraIssueId, deployId, 1, userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"An error {myDBResult['message']} occurred while updating validation attempt !!!")

			# attaching parsed output file for review in jira
			self.JiraUtil.addAttachment(securityToken, jiraIssueId, myParsedFile)

			self.LOGGER.info(f"deployment created successfully, parse result >> ( {myParseResult['status']}, {myParseResult['message']} ), commiting txn")

			self.pg.commit(securityToken, self.PG_CONN)
			
			myParsedFileWOPath = self.util.getFileName(myParsedFile)

			self.JiraUtil.addAComment(securityToken, jiraIssueId, f"New deployment created successfully, parse result >> ( {myParseResult['status']}, {myParseResult['message']} ), pls verify deployment parse file {myParsedFileWOPath}")

			#self.JiraUtil.addAComment(securityToken, jiraIssueId, "deployment created successfully")

			return self.util.buildResponse(myParseResult["status"], myParseResult["message"])

		except Exception as error:
			# rollback
			self.pg.rollback(securityToken, self.PG_CONN)
			
			self.JiraUtil.addAComment(securityToken, jiraIssueId,"An error {error} occurred while creating/validating deployment for {jira}".format(error = str(error), jira = jiraIssueId))

			self.LOGGER.error("An error occurred >>> {error}, rolling back transaction !!!".format(error = str(error)), exc_info = True)
			
			return self.util.buildResponse(self.Globals.unsuccess, str(error))

	def reprocessDeployFiles(self, securityToken, jiraIssueId, deployId, appId, deployFileLocation, userId):
		"""
		Reprocess deployment files, this is only allowed when deployment status is in pending state 
			(deploymen didnt start yet)
		Arguments:
			securityToken: security token
			jiraIssueId : Jira issue id
			deployId : deployment id
			appId : application id
			userId : user requesting revalidating this deploymenty
		"""
		try:

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', jiraIssueId, ',', deployId, ',', str(appId), ',', deployFileLocation, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not self.isProessDeployFilesAllowed(securityToken, deployId):
				raise ValueError(f"Reprocessing deployment {deployId} is is prohibited !!!")
			
			#self.JiraUtil.addAComment(securityToken, jiraIssueId, f"User {userId} requested revalidaing/reprocessing deployment files, proceeding")

			myActiveDeployCtrlData = self.getDeployCtrl(securityToken, self.getActiveDeployCtrlId(securityToken, deployId))

			# we need to download the files 
			if self.isDeployFilesChanged(securityToken, deployId, deployFileLocation):
		
				#self.JiraUtil.addAComment(securityToken, jiraIssueId, "found new deploy files, processing ...")

				# need app id, get Application detail
				myAppDetail = self.getAnAppDetails(securityToken, appId)

				# create new deployment ctrl id

				#__createNewDeployCtrl(self, securityToken, deployId, appId, deployFileLocation, userId)
				myDBResult = self.__createNewDeployCtrl(securityToken, deployId, appId, deployFileLocation, userId)

				self.LOGGER.info("create new deploy ctrl db result >> {result}".format(result = str(myDBResult)))

				myNewDeployCtrlId = myDBResult["data"]

				if not(myDBResult["status"] == self.Globals.success and myNewDeployCtrlId):
					raise ValueError("An error <{error}> occurred while creating new deployment ctrl id for deployment {deployId} !!!".\
						format(error = myDBResult["message"], deployId = deployId))

				myNewDeployCtrlId = myDBResult["data"]
				
				#def __processDeployFiles(self, securityToken, deployId, appId, dbTechnology, deployCtrlId, deployFileLocation, userId)
				myParseResult = self.__processDeployFiles(securityToken, deployId, appId, myAppDetail["technology"], myNewDeployCtrlId, deployFileLocation, userId)
	
				#if myDBResult["status"] == self.Globals.unsuccess:
				#	raise ValueError(myDBResult["message"])

				myParsedFile = myParseResult["data"]

				# updating revalidation/reprocessing attempt counter
				myDeployData = self.getDeployData(securityToken, deployId)

				#updDeployValidationAttempt(self, securityToken, jiraIssueId, deployId, revalidationAttempt, userId)
				self.__updDeployValidationAttempt(securityToken, jiraIssueId, deployId, myDeployData["validation_attempts"]+1, userId)

				# updating new deploy ctrl id to deployment
				
				#def updDeployCtrl(self, securityToken, deployId, deployCtrlId)
				self.updDeployCtrl(securityToken, deployId, myNewDeployCtrlId)

				# should we remove previous parsed attachment

				self.JiraUtil.addAttachment(securityToken, jiraIssueId, myParsedFile)

				self.JiraUtil.addAComment(securityToken, jiraIssueId, f"All Deployment files revalidated successfully, parse result >> ( {myParseResult['status']}, {myParseResult['message']} ), pls verify deployment parsed file {self.util.getFileName(myParsedFile)}")

				self.pg.commit(securityToken, self.PG_CONN)

				return self.util.buildResponse(myParseResult["status"], myParseResult["message"])

			else:
				myMessage = "deployment file(s) are not changed, skipping processing"
				self.LOGGER.debug(myMessage)

				self.JiraUtil.addAComment(securityToken, jiraIssueId, myMessage)

				return self.util.buildResponse(self.Globals.success, myMessage)

			# reprocessing deployment files
			# check if there are any changes to deployment files

		except Exception as error:
			self.pg.rollback(securityToken, self.PG_CONN)

			self.LOGGER.error("An error {error} occurred while reprocessing deploy files, rolling back current txn".format(error = str(error)), exc_info = True)

			self.JiraUtil.addAComment(securityToken, jiraIssueId,"An error {error} occurred while reprocessing deploy files, rolling back current txn".format(error = str(error)))

			raise error

	def __newDeploy(self, securityToken, deployId, deploySource, deploySourceId, jiraIssueId, appId, appName, dbTechnology, deployEnvOrder, deployCtrlId, deployFileLocation, userId):
		"""
		Saves new deployment in repository
		Arguments:
			deployId: Deployment id (Jira issue id)
			deploySource: Source of deployment (Jira/Bitbucket)
			deploySourceId: ID of source of deployment
			jiraIssueId: Jira issue idjiraIssueId
			appId: Application id to which this deployment belongs to
			appName: Application name
			dbTechnology: database technology
			deployEnvOrder: order of deployment in env (dev,test,stg,prod)
			deployCtrlId : Deployment control id
			deployFileLocation : Deployment file location 
			userId: User requesting this deployment
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', deploySource, ',', deploySourceId, ',', jiraIssueId, ',', str(appId), ',', appName, ',', deployId, ',', str(appId), ',', dbTechnology, ',', str(deployEnvOrder), ',', deployCtrlId, ',', deployFileLocation, ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myDeployData = {
				"deployId" : deployId,
				"deploySource" : deploySource,
				"deploySourceId" : deploySourceId,
				"jiraIssueId" : jiraIssueId,
				"appId" : appId, 
				"appName" : appName, 
				"dbTechnology" : dbTechnology, 
				"deployEnvOrder" : deployEnvOrder,
				"deployCtrlId" : deployCtrlId,
				"deployFileLocation" : deployFileLocation,
				"status" : self.Globals.DEPLOY_STATUS_VALIDATION_PENDING, 
				"submittedBy" : userId, 
				"submittedTs" : self.util.lambdaGetCurrDateTime(),
				"comments" : "".join([self.util.lambdaGetCurrReadableTime(), " - ", f"user {userId} created this deployment"])
			}
	
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newDeploySql, myDeployData)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}, rolling back current txn".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __updDeployValidationAttempt(self, securityToken, jiraIssueId, deployId, validationAttempt, userId):
		"""
		Add deploy revalidation attempt by 1 for this deployment
		Arguments:
			securityToken : Security token
			jiraIssueId : jiraIssueId
			deployId: Deployment id (Jira issue id)
			validationAttempt : validation attempts
			userId: User requesting this deployment
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', jiraIssueId, ',', deployId, ',', str(validationAttempt), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myValidationAttemptData = {
				"deployId" : deployId,
				"validationAttempts" : validationAttempt,
				"lastValidationBy" : userId,
				"lastValidationTs" : self.util.lambdaGetCurrDateTime(),
				"comments" : "".join([self.util.lambdaGetCurrReadableTime(), " - ", f"user {userId} performed revalidation of deployment file, current validation attempt {validationAttempt}"])
			}
	
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployValidationAttemptSql, myValidationAttemptData)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}, rolling back current txn".format(error = str(error)), exc_info = True)
			#self.pg.rollback(securityToken, self.PG_CONN)
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
			self.LOGGER.error("An error occurred >>> {error}, rolling back current txn".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __createNewDeployCtrl(self, securityToken, deployId, appId, deployFileLocation, userId):
		"""
		Description: Create new deployment control for a given deploy/app/deploy ctrl id. If an active ctrl is found
			and re processing of deployment files are allowed, existing active ctrl id will marked inactive and new ctrl id
			will be created and mark 'active'

		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appId), ',', deployFileLocation, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myDeployReadmeFile = self.util.buildPath(deployFileLocation, self.Globals.DEPLOY_README_FILE)

			# validation

			if not self.util.isFileExists(myDeployReadmeFile):
				raise ValueError("Deployment readme file {file} does not exists !!!".format(file = myDeployReadmeFile))

			myDeployReadmeData = self.util.readJsonFile(myDeployReadmeFile)

			if not myDeployReadmeData :
				raise ValueError("deploy readme file {file} is empty !!!".format(file = myDeployReadmeFile))

			# checking if this deployment is new deployment
			if self.isDeploymentExists(securityToken, deployId):

				# deployment exists, checking if we are allowed to reprocess deployment files
				if not self.isProessDeployFilesAllowed(securityToken, deployId):

					# reprocessing files not allowed, throwing error to caller
					raise ValueError(f"reprocessing deployment files prohibited for deployment {deployId}")

				# reprocessing of deployment files are allowed, invalidating exisiting deploy ctrl id

				# retrieving active deploy control id for this deployment id
				#myActiveDeployCtrlId = self.getActiveDeployCtrlId(securityToken, deployId)
				self.__invalidteDeployCtrl(securityToken, deployId, userId)
				
			# generate new deployment ctrl
			myNewdeployCtrlId = self.getNewDeployCtrl(securityToken, deployId)

			self.LOGGER.debug("got new deploy ctrl id {ctrlId} proceeding with processing deployment files (readme)".format(ctrlId = myNewdeployCtrlId))

			myDeployReadmeData = {
				"deployCtrlId" : myNewdeployCtrlId,
				"deployId" : deployId,
				"appId" : appId,
				"ts" : self.util.lambdaGetCurrDateTime(),
				#"deployFileLocation" : deployFileLocation,
				"deployReadMe" : self.util.encodeDictData(myDeployReadmeData),
				"status" : self.Globals.STATUS_ACTIVE,
				"comments" : "".join([self.util.lambdaGetCurrReadableTime(), " - ", f"creating new deploy control for deploy id {deployId} as requested by user {userId}"])
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newDeployCtrlSql, myDeployReadmeData)
			
			self.LOGGER.debug("db results >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("An error {error} occurred while saving deploy readme file contents for deploy id {deployId}".\
					format(error = myDBResult["message"], deployId = str(deployId)))

			return self.util.buildResponse(self.Globals.success, self.Globals.success, myNewdeployCtrlId)

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}, rolling back current txn".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __addDeployFile(self, securityToken, deployId, deployCtrlId, fileObject, userId):
		"""
		Description: Saves new deployment file in repository. 
		Arguments:
			securityToken: Security token  
			deployId: Deployment id (Jira issue id)
			deployCtrlId : Deploy handle id (generated during loading readme file)
			fileObjet 	: Deployment file object
			userId: User requesting this deployment
		Returns: file_id
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', deployCtrlId, ',', str(fileObject), ',', userId])))

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
				"ignoreError" : fileObject["ignoreError"],
				"totalTasks" : fileObject["totalTasks"],
				"parseFailed" : fileObject["failedTasks"],
				"parseStatus" : fileObject["status"],
				"parseStatusMsg" : fileObject["message"],
				"status" : self.Globals.STATUS_VALID,
				"submittedBy" : userId, 
				"submittedTs" : self.util.lambdaGetCurrDateTime(),
				"comments" : "".join([self.util.lambdaGetCurrReadableTime(), " - ", f"adding deploy file for deploy control id {deployCtrlId} as requested by user {userId} during creation of new deployment "])
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newDeployFileSql, myDeployFileData)
			self.LOGGER.debug("db results >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("An error {error} occurred while saving deploy file {file} for deploy id {deployId}".\
					format(error = myDBResult["message"], file = myDeployFileWPath, deployId = str(deployId)))

			myFileId = myDBResult["data"][0]["file_id"]

			self.LOGGER.info("returning >>> {result}".format(result = myFileId))

			return myFileId

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __addDeployTasks(self, securityToken, deployId, appId, deployCtrlId, taskObject, userId):
		"""
		Description: Saves new deployment file in repository. 
		Arguments:
			securityToken: Str, Security token
			deployId: Str, Deployment id (Jira issue id)
			appId : Integer, Application id
			deployCtrlId : Str, Deploy handle id (generated during loading readme file)
			taskObject 	: Dict, Task object (dict)
			userId: Str, User requesting this deployment
		Returns: {"status", "", message" : "", "data" : <task_id>}
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appId), ',', deployCtrlId, ',', str(taskObject), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# we would not change the deployment which is valid/in-progress/completed, need validation
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# adding comments
			taskObject.update({"comments" : "".join([self.util.lambdaGetCurrReadableTime(), " - ", f"creating new deployment task from parsing {deployId} as requested by user {userId}"])})

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newDeployTaskSql, taskObject)

			self.LOGGER.debug("db results >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("An error {error} occurred while saving deploy file {file} for deploy id {deployId}".\
					format(error = myDBResult["message"], file = myDeployFileWPath, deployId = str(deployId)))

			myTaskId = myDBResult["data"][0]["task_id"]

			self.LOGGER.info("returning >>> {result}".format(result = myTaskId))

			return myTaskId

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __updDeployCtrlParseData(self, securityToken, deployCtrlId, deployParseData):
		"""
		Description: Saves new deployment in repository. Deployment must not ne in in-progress/completed state
			If there are files are already in this deployment, will invalidate them and procees with
			new set of files
		Arguments:
			deployCtrlId : deploy ctrl id
			deployParseData : Json data (output of parser)
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployCtrlId, ',', str(deployParseData)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# updating parse data of deployment files
			myDeployFileStats = self.util.encodeDictData([self.util.getFileStats(self.util.buildPath(deployParseData["path"], file["file"])) for file in deployParseData["parseSummary"]["deployFiles"] ])
			#print('file stats > ', myFileStats)
		
			# assuming we have only one path where all the files are downloaded thus picking 1st path from deployment files to get location of deployment readme file
			#myDeployDownLoadLoc = [for deploy in deployParseData["parseSummary"]["deployFiles"]]
			# adding readme json file for this deployment
			#myDeployReadmeFileStats = self.util.getFileStats(self.util.buildPath(deployParseData["path"], file["file"])) for file in deployParseData["parseSummary"]["deployFiles"] ])

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployCtrlParseDataSql, \
				{
					#"parseTs" : self.util.convertStrDate2DateTime(deployParseData["ts"], self.Globals.DEFAULT_TS_ISO_FORMAT)
					"parseTs" : self.util.convertIsoDateStr2Date(deployParseData["ts"]),
					"deployFileStats": myDeployFileStats,
					"deployParseFileData" : self.util.encodeDictData(deployParseData),
					"deployParseFile" : deployParseData["parseFile"],
					"totalTasks" : deployParseData["parseSummary"]["tasks"]["total"],
					"parseStatus" : deployParseData["parseSummary"]["tasks"]["status"],
					"status" : self.Globals.STATUS_VALID if deployParseData["parseSummary"]["tasks"]["status"] == self.Globals.success else self.Globals.STATUS_ERROR,
					"deployCtrlId" : deployCtrlId
				}
			)

			return myDBResult
			
			#if myDBResult["status"] == self.Globals.unsuccess:
			#	raise ValueError("An error {error} occurred while updating deployment parse data in deploy control !!!".format(error = myDBResult["message"]))

		except Exception as error:
			self.LOGGER.error("An error {error} occurred while saving parsed data (deploy_ctrl), aboritng !!!".format(error = str(error)), exc_info = True)
			raise error

	def __processDeployFiles(self, securityToken, deployId, appId, dbTechnology, deployCtrlId, deployFileLocation, userId):
		"""
		Description: Saves new deployment in repository. Deployment must not ne in in-progress/completed state
			If there are files are already in this deployment, will invalidate them and procees with
			new set of files
		Arguments:
			deployId: Deployment id (Jira issue id)
			appId: Application id to which this deployment belongs to
			dbTechnology : Database technology
			deployCtrlId : deploy ctrl id
			userId: User requesting this deployment
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appId), ',', dbTechnology, ',', deployCtrlId, ',', deployFileLocation, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not self.util.isDirExists(deployFileLocation):
				raise ValueError("invalid deployment file path, {path} (does not exists) !!!".format(path = deployFileLocation))

			myAppDetails = self.getAnAppDetails(securityToken, appId)

			# parsing deployment files, will get parsed file generated by praser
			myPrasedFile = self.parser.parseDeployFiles(securityToken, deployId, myAppDetails, deployCtrlId, dbTechnology, deployFileLocation)

			myParsedData = self.util.readJsonFile(myPrasedFile)

			if not myParsedData:
				raise ValueError("Parse file {file} is empty, aborting !!! ".format(file = myPrasedFile))

			# fetching parse status
			myParseStatus = myParsedData["parseSummary"]["tasks"]["status"]
			myTotalPrasedTasks = myParsedData["parseSummary"]["tasks"]["total"]
			myTotalSuccessTasks = myParsedData["parseSummary"]["tasks"]["success"]
			myTotalUnsuccessTasks = myParsedData["parseSummary"]["tasks"]["unSuccess"]

			# updating deploy parsed data to deploy control table
			myDBResult = self.__updDeployCtrlParseData(securityToken, deployCtrlId, myParsedData)
			
			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("An error {error} occurred while updating deployment parse data (deploy control) !!!".format(error = myDBResult["message"]))
			
			# creating deploy_files
			for file in myParsedData["parseSummary"]["deployFiles"]:
				
				fileObject = {
					"file" : file["file"], 
					"path" : myParsedData["path"],
					"seq" : file["seq"],
					"dbTechnology" : dbTechnology,
					"status" : file["status"],
					"message" : file["message"],
					"totalTasks" : file["totalTasks"],
					"failedTasks" : file["unSuccessTasks"],
					"ignoreError" : file["ignoreError"]				
				}

				myFileId = self.__addDeployFile(securityToken, deployId, deployCtrlId, fileObject, userId)

				#if file["unSuccessTasks"] > 0:
				#	myParseStatus = self.Globals.DEPLOY_STATUS_VALIDATION_UNSUCCESS

				# updating file id, which will be used during creation of tasks
				file.update({"fileId" : myFileId})			

			# creating tasks for this deployment
			
			myAllTaskList = []
			mySuccessTasksList = []
			myUnSuccessTasksList = []


			for task in myParsedData["tasks"]:

				myTaskData = {
					"fileId" :  [file["fileId"] for file in myParsedData["parseSummary"]["deployFiles"] if file["file"] == task["deployFile"]][0],
					"fileName" : task["deployFile"],
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
					"status" : self.Globals.STATUS_VALID,
					"parseStatus" : task["status"],
					"parseStatusMsg" : task["message"],
					"ignoreError" : task["ignoreError"]
				}

				# adding tasks data
				#__addDeployTasks(self, securityToken, deployId, appId, deployCtrlId, taskObject, userId
				myTaskId = self.__addDeployTasks(securityToken, deployId, appId, deployCtrlId, myTaskData, userId)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("An error {error} occurred while saving deploy file for deploy id {deployId}".\
						format(error = myDBResult["message"], deployId = str(deployId)))

				# building success/unsuccess/total tasks list
				if task["status"] == self.Globals.success:
					mySuccessTasksList.append(myTaskId)
				elif  task["status"] == self.Globals.unsuccess:
					myUnSuccessTasksList.append(myTaskId)

				myAllTaskList.append(myTaskId)

			# update the deployment status based on outcome of parsing

			if myParseStatus == self.Globals.success:
				myParsedComments = f"Completed parsing, parse status is {myParseStatus}, tasks (success/total) : {myTotalSuccessTasks}/{myTotalPrasedTasks}"
			else:
				myParsedComments = f"Completed parsing, parse status is {myParseStatus}, tasks (success/total) : {myTotalSuccessTasks}/{myTotalPrasedTasks},  total unsuccess tasks >  {len(myUnSuccessTasksList)}"

			if myParseStatus == self.Globals.success:
				myParsedMessage = f"Total {myTotalSuccessTasks}/{myTotalPrasedTasks} tasks parsed successfully"
			else:
				myParsedMessage = f"Total {myTotalSuccessTasks}/{myTotalPrasedTasks} tasks parsed successfully, total unsuccess tasks >  {len(myUnSuccessTasksList)}"
				#myParsedMessage = f"Total {myTotalSuccessTasks}/{myTotalPrasedTasks} tasks parsed successfully"
			
			#myParsedMessage = f"Total {myTotalSuccessTasks}/{myTotalPrasedTasks} tasks parsed successfully"

			myValidationStatus = self.Globals.DEPLOY_STATUS_MAP[self.Globals.validation][myParseStatus]

			self.updDeployStatus(securityToken, deployId, myValidationStatus, myParsedComments)

			self.LOGGER.info("all tasks loaded for file {file} Tasks detail: > {total}, tasks > {tasks} ".format(file = file["file"], total = len(myAllTaskList), tasks = str(myAllTaskList)))

			#return self.util.buildResponse(self.Globals.success, self.Globals.success, myAllTaskList)
			return self.util.buildResponse(myParseStatus, myParsedMessage, myPrasedFile)

		except Exception as error:
			self.LOGGER.error("An error {error} occurred while saving parsed data, aboritng !!!".format(error = str(error)), exc_info = True)
			raise error

	def __invalidteDeployCtrl(self, securityToken, deployId, userId):
		"""
		Description: Invalidate existing active deployment ctrl for a given deployment id, (updates deploy_ctrl status to in-active)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# get active deploy tasks group id for this deployment
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myActivedeployCtrlId = self.getActiveDeployCtrlId(securityToken, deployId)

			# check the status of this deployment, deployment status must not have started
			myDeployStatus = self.getDeployStatus(securityToken, deployId)

			if myDeployStatus and myDeployStatus not in self.Globals.VALID_STATUS_RELOAD_DEPLOY_FILES_LIST:
				raise ValueError("Deployment invalidation is not allowed (for invalidation, a deployment must be in {expecting}, got {got}) !!! ".\
					formta(expecting = str(self.Globals.VALID_STATUS_RELOAD_DEPLOY_FILES_LIST, got = myDeployStatus)))

			if myActivedeployCtrlId:
				# updating status to inactive
				myUpdateData = {"deployCtrlId" : myActivedeployCtrlId, "status" : self.Globals.STATUS_INACTIVE}

				myDBResult = self.updDeployCtrlStatus(\
					securityToken, myActivedeployCtrlId, self.Globals.STATUS_INACTIVE, \
					"".join([self.util.lambdaGetCurrReadableTime(), " - ", f"making deploy ctrl id {myActivedeployCtrlId} in active for deploy id {deployId} as requested by user {userId}"])
				)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("An error occurred while invalidating exisitng files for deploy id >>> {deployId}".format(deployId = deployId))

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
					raise ValueError("An error occurred while invalidating exisitng files for deploy id >>> {deployId}".format(deployId = deployId))

				# invalidating all deployment tasks for this file
				myTaskUpdData = {
					"fileId" : file["file_id"],
					"status" : self.Globals.STATUS_INACTIVE,
					"comments" : "invalidating all task of {file}".format(file = file["file_name"])
				}

				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updTaskStatusByFileIdSql, myFileUpdData)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("An error occurred while invalidating exisitng files for deploy id >>> {deployId}".format(deployId = deployId))

			if myActiveTaskGroupId:
				# found active tasks group for this deployment, invalidating
				myUpdateData = {"deployId" : deployId, "deployCtrlId" : myActiveTaskGroupId, "status" : self.Globals.self.STATUS_INACTIVE}
				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployTaskGrpStatusSql, myUpdateData)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError("An error occurred while invalidating deployment tasks for task group id >>> {taskGrpId}".format(taskGrpId = myActiveTaskGroupId))

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))
			"""

			#return self.util.buildResponse(self.Globals.success, self.Globals.success)

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def updDeployStatus(self, securityToken, deployId, status, comments = None):
		"""
		Description: Update deployment status
			Status : 
				Pending 
				valid.Success
				valid.unSuccess
				cancelled
				deploy.inProgress
				deploy.unSuccess
				deploy.success
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', status, ',', str(comments)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not self.isDeploymentExists(securityToken, deployId):
				raise ValueError(f"Invalid deployment id {deployId} !!!")

			# checking if we got a valid status
			if not (status in self.Globals.DEPLOY_ALL_STATUS):
				raise ValueError(f"invalid deployment status {status} !!!")

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myUpdateData = {"deployId" : deployId, "status" : status}

			if comments:
				myUpdateData.update({"comments" : "".join([self.util.lambdaGetCurrReadableTime(), ' - ', comments])})
			else:
				myUpdateData.update({"comments" : comments})

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployStatusSql, myUpdateData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"error while updating deploymnet id {deployId} status to {status}")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def updDeployCtrl(self, securityToken, deployId, deployCtrlId):
		"""
		Description: update deploy control id in deploy 
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', deployCtrlId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not self.isDeploymentExists(securityToken, deployId):
				raise ValueError(f"Invalid deployment id {deployId} !!!")

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myUpdateData = {"deployId" : deployId, "deployCtrlId" : deployCtrlId}

			myUpdateData.update({"comments" : "".join([self.util.lambdaGetCurrReadableTime(), ' - ', f'updating new deploy ctrl id to {deployCtrlId}'])})

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployCtrlSql, myUpdateData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"error while updating deploymnet {deployId}'s ctrl id {deployCtrlId} ")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def updDeploySource(self, securityToken, deployId, deploySource, deploySourceData, userId):
		"""
		Description: Update deployment source and data
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', deploySource, ',', deploySourceData, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not self.isDeploymentExists(securityToken, deployId):
				raise ValueError(f"Invalid deployment id {deployId} !!!")

			if not (deploySource in self.Globals.ALL_DEPLOY_SOURCE):
				raise ValueError(f"Expecting deploy source to be one of the value from {self.Globals.ALL_DEPLOY_SOURCE}, got {deploySource}")

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myUpdateData = {
				"deployId" : deployId, 
				"deploySource" : deploySource, 
				"deploySourceId" : deploySourceData,
				"comments" : "".join([self.util.lambdaGetCurrReadableTime(), " - ", f"user {userId} requested to change deploy source and data fro reprocessing dployment files"])
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeploySourceSql, myUpdateData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"error while updating deploy source {deployId} status to {status}")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def updDeployCtrlStatus(self, securityToken, deployCtrlId, status, comments = None):
		"""
		Description: Update deployment ctrl status
			Status : 
				active
				inactive
				cancelled
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployCtrlId, ',', status, ',', str(comments)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myDeployCtrlData = self.getDeployCtrl(securityToken, deployCtrlId)

			if not myDeployCtrlData:
				raise ValueError(f"Invalid deployment control id {deployCtrlId}")

			# checking if we got a valid status
			if not (status in self.Globals.DEPLOY_CTRL_ALL_STATUS):
				raise ValueError(f"invalid deployment status {status} !!!")

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myUpdateData = {"deployCtrlId" : deployCtrlId, "status" : status}

			if comments:
				myUpdateData.update({"comments" : "".join([self.util.lambdaGetCurrReadableTime(), ' - ', comments])})
			else:
				myUpdateData.update({"comments" : comments})

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployCtrlStatusSql, myUpdateData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"error while updating deploymnet ctrl id {deployCtrlId} status to {status}")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def updDeployFileStatusByCtrl(self, securityToken, deployCtrlId, status, comments = None):
		"""
		Description: Update deployment ctrl status
			Status : 
				valid
				cancelled
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployCtrlId, ',', status])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myDeployCtrlData = self.getDeployCtrl(securityToken, deployCtrlId)

			if not myDeployCtrlData:
				raise ValueError(f"Invalid deployment control id {deployCtrlId}")

			# checking if we got a valid status
			if not (status in self.Globals.DEPLOY_FILES_ALL_STATUS):
				raise ValueError(f"invalid deployment status {status} !!!")

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myUpdateData = {"deployCtrlId" : deployCtrlId, "status" : status}

			if comments:
				myUpdateData.update({"comments" : "".join([self.util.lambdaGetCurrReadableTime(), ' - ', comments])})
			else:
				myUpdateData.update({"comments" : comments})

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployFileStatusByCtrlSql, myUpdateData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"error while updating deploymnet ctrl id {deployCtrlId} status to {status}")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def updDeployTaskStatusByCtrl(self, securityToken, deployCtrlId, status, comments = None):
		"""
		Description: Update deployment ctrl status
			Status : 
				valid
				cancelled
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployCtrlId, ',', status])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myDeployCtrlData = self.getDeployCtrl(securityToken, deployCtrlId)

			if not myDeployCtrlData:
				raise ValueError(f"Invalid deployment control id {deployCtrlId}")

			# checking if we got a valid status
			if not (status in self.Globals.DEPLOY_TASKS_ALL_STATUS):
				raise ValueError(f"invalid deployment status {status} !!!")

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myUpdateData = {"deployCtrlId" : deployCtrlId, "status" : status}

			if comments:
				myUpdateData.update({"comments" : "".join([self.util.lambdaGetCurrReadableTime(), ' - ', comments])})
			else:
				myUpdateData.update({"comments" : comments})

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployTaskStatusByCtrlSql, myUpdateData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"error while updating deploymnet ctrl id {deployCtrlId} status to {status}")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	#### performing deployment
	"""	
		check if deployment is ready for deployment (status = validation.success)
		IF deployment exists in env:
			check if there are any attempts
			if any attempt is found, get the last attempt and check the status of that attempt  
			#???check the status of active attempt
			if unsuccess:
				invalidate previous active attempt, create a new attempt for this deployment with pending tasks (if no pending tasks ???)
			Follow deploy task
		ELSE (if deployment env does not exists)
			Is prev env exists?
				1. Check if previus deployment was succesful
				2. check if previus deployment is approved
			Create deployment env and attempt along with the tasks

		PERFORM DEPLOYMENT
		1. deploy each task for this attempt
		2. update status of each task along with result and before/after image
		3. once completed, udate status of this deployment
		4. if outcome is successful, create a request for this deployment and jira id which need to be approved

	"""
	def createDeployAttempt(self, securityToken, deployId, appEnvId, userId, extReferenceId = None):
		"""
		Create deployment attempt 
			create data in deploy_envs if it does not exists
			if this is 1st deployment, create a new deployment attempt and all task from deploy_tasks for this deployment
			
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myDeployData = self.getDeployData(securityToken, deployId)

			if not myDeployData:
				raise ValueError(f"Invalid deployment id {deployId} !!!")

			if not (myDeployData["status"] == self.Globals.DEPLOY_STATUS_VALIDATION_SUCCESS):
				raise ValueError("deployment must validate successfully before it can be deployed in environment")

			# validation
			self.validateDeployEnv(securityToken, deployId, appEnvId, userId)

			# checking if this deployment is ready to be moved to this environment
			if not self.isDeployEnvExists(securityToken, deployId, appEnvId):
				# deployment does not exist in this environment, deployment is in valid state
				# checking if this deployment was successfully deployed in previous environment
				myDBResult = self.__createNewDeployEnv(securityToken, deployId, appEnvId, userId, extReferenceId)

			myDeployEnvData = self.getDeployEnvData(securityToken, deployId, appEnvId)

			# cehcking if deploy env status is ready for deployment (status must not be successful deploy.Success)
			if myDeployEnvData["status"] == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS:
				raise ValueError(f"Deployment id {deployId} in env id {appEnvId} is already successfully deployed !!!")

			# checking if any other deployment attempt is in-progress for this deployment
			if myDeployEnvData["attempt_id"]:
				myDeployAttemptStatus = self.getDeployAttemptStatus(securityToken, myDeployEnvData["attempt_id"])

				if myDeployAttemptStatus == self.Globals.DEPLOY_STATUS_DEPLOY_READY:
					# found this attempt in rady state, returning this attempt id
					# not performing commit as we have neither created a new deploy env nor an attempt
					return self.util.buildResponse(self.Globals.success, self.Globals.success, {"attemptId" : myDeployEnvData["attempt_id"]})

				if myDeployAttemptStatus == self.Globals.DEPLOY_STATUS_DEPLOY_INPROGRESS:
					raise ValueError(f"Another deployment attempt {myDeployEnvData['attempt_id']} is in-progress !!!")

			# we have deployment created in this environment, good to proceed with creating a new attempt for this deployment
			myDBResult = self.__createNewDeployEnvAttempt(securityToken, deployId, appEnvId, userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.pg.commit(securityToken, self.PG_CONN)

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __createNewDeployEnv(self, securityToken, deployId, appEnvId, userId, extReferenceId = None):
		"""
		Create new deployment for a given env with status Pending 
			
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId), ',', userId, ',', str(extReferenceId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myDeployData = self.getDeployData(securityToken, deployId)

			myAppEnvData = self.getAnAppEnvById(securityToken, appEnvId)

			if not myDeployData:
				raise ValueError(f"Invalid deployment id {deployId} !!!")

			if not (myDeployData["status"] == self.Globals.DEPLOY_STATUS_VALIDATION_SUCCESS):
				raise ValueError("deployment must validate successfully before it can be deployed in environment")

			# checking if this deploy exists in environment
			if not self.isDeployEnvExists(securityToken, deployId, appEnvId):

				# validating previous deployment env order
				myValResult = self.validateDeployEnvOrder(securityToken, deployId, myAppEnvData['env'])
				if myValResult["status"] == self.Globals.unsuccess:
					raise ValueError(myValResult["message"])

				self.LOGGER.debug(f"all validation met, proceeding with creating of deployment data in env {myAppEnvData['env']}")

				# retrieving all deploy tasks
				myDeployTasks = self.getDeployCtrlTasks(securityToken, deployId)
				
				myAllDeployTasks = [task["task_id"] for task in myDeployTasks]

				self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

				myNewDeployEnvData = {
					"deployId" : deployId,
					"appId" : myDeployData["app_id"],
					"appEnvId" : appEnvId,
					"env" : myAppEnvData["env"],
					"status" : self.Globals.DEPLOY_STATUS_DEPLOY_PENDING,
					"submittedBy" : userId,
					"submittedTs" : self.util.lambdaGetCurrDateTime(),
					"scheduledTs" : self.util.lambdaGetCurrDateTime(),
					"totalTasks" : len(myAllDeployTasks),
					"pendingTasks" : len(myAllDeployTasks),
					"completedTasks" : 0,
					#"pendingTasksList" : ",".join(map(str,myAllDeployTasks)),
					#"tasksList" : ",".join(map(str,myAllDeployTasks))
					"pendingTasksList" : myAllDeployTasks,
					"tasksList" : myAllDeployTasks,
					"startTime" : self.util.lambdaGetCurrDateTime(),
					"comments" : f"{self.util.lambdaGetCurrDateTime()} - Creating new deployment env as requested by {userId}"
				}

				if myAppEnvData["env"] == self.Globals.ENV_PROD:
					myNewDeployEnvData.update({"referencedDoc" : extReferenceId})
				else:
					myNewDeployEnvData.update({"referencedDoc" : None})

				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newDeployEnvsSql, myNewDeployEnvData)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError(myDBResult["message"])

				return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred while creating new deployment env >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __createNewDeployEnvAttempt(self, securityToken, deployId, appEnvId, userId):
		"""
		Create a new attempt for a given deployment and its environment. 
		Requirements: Deployment must be created in tis environment 
			
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# retrieving deployment data
			myDeployData = self.getDeployData(securityToken, deployId)

			# validation
			if not myDeployData:
				raise ValueError(f"Invalid deployment id {deployId} !!!")

			if not (myDeployData["status"] == self.Globals.DEPLOY_STATUS_VALIDATION_SUCCESS):
				raise ValueError("Deployment must validated successfully before it can be deployed in environment")

			getDeployEnvStatus = self.getDeployEnvData(securityToken, deployId, appEnvId)

			if getDeployEnvStatus in [self.Globals.DEPLOY_STATUS_DEPLOY_INPROGRESS, self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS]:
				raise ValueError("Deployment is either in-progress or completed successfully !!!")
			
			# checking status of current attempt of this deployment in env
			myDeployEnvAttemptIdData = self.getDeployEnvAttemptIds(securityToken, deployId, appEnvId)

			if myDeployEnvAttemptIdData["attempt_id"]:
				# found current attempt id for this deployment in env
				# checking staus of this attempt, will not proceed if this attempt is in Ready or in-progress state 
				myAttemptStatus = self.getDeployAttemptStatus(securityToken, myDeployEnvAttemptIdData["attempt_id"])

				if myAttemptStatus == self.Globals.DEPLOY_STATUS_DEPLOY_READY:
					# this attempt is not started, sending back this attempt id
					return self.util.buildResponse(self.Globals.success, self.Globals.success, {"attemptId" : myNewAttemptId})

				if myAttemptStatus == self.Globals.DEPLOY_STATUS_DEPLOY_INPROGRESS:
					# this attempt is not started, sending back this attempt id
					raise ValueError(f"This deployment {deployId} in env {appEnvId} is already in progress with attempt id {myDeployEnvAttemptIdData['attempt_id']}, Pls wait for this attempt to be completed !!!")

			# retrieving app env details
			myAppEnvData = self.getAnAppEnvById(securityToken, appEnvId)

			# checking if this deploy exists in environment
			if not self.isDeployEnvExists(securityToken, deployId, appEnvId):
				raise ValueError(f"deployment {deployId} env {appEnvId} data is missing !!!")

			# check the status of this deployment in this env, if succesfull, will raise error (cant create an atttempt to deploy)
			# retrieving all pending tasks for this deployment
			myAllPendingTasks = self.getDeployEnvPendingTasks(securityToken, deployId, appEnvId)
			myPendingTasksList = [task["task_id"] for task in myAllPendingTasks]

			if not myAllPendingTasks:
				raise ValueError("No pending tasks are available to be deployed !!!")

			# we have atleast 1 pending task, creating a new attempt so pending task(s) can be processed
			myNewAttemptData = {
				"deployId" : deployId,
				"appId" :  myDeployData["app_id"],
				"env" :   myAppEnvData["env"],
				"appEnvId" : appEnvId,
				"requestedBy" : userId,
				"totalTasks"  : len(myPendingTasksList),
				"pendingTasks" : len(myPendingTasksList),
				"tasksList" : myPendingTasksList,
				"pendingTasksList" : myPendingTasksList,
				"startTime" : self.util.lambdaGetCurrDateTime(),
				"status" : self.Globals.DEPLOY_STATUS_DEPLOY_PENDING,
				"comments" : "".join([self.util.lambdaGetCurrReadableTime(), f" - creating new attempt with total tasks {len(myPendingTasksList)} requested by {userId}"])
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newAttemptSql, myNewAttemptData)
			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			myNewAttemptId = myDBResult["data"][0]["attempt_id"]

			# adding pending tasks to this attempt
			myRemovePendingTasksKetLists = ["status", "parse_status", "parse_status_msg"]

			for task in myAllPendingTasks:
				self.util.removeKeysFromDict(task, myRemovePendingTasksKetLists)
				# adding missing key required for task
				task.update({
					"attempt_id" : myNewAttemptId,
					"app_env_id" : appEnvId,
					"status" : self.Globals.DEPLOY_STATUS_DEPLOY_PENDING, 
					"comments" : "".join([self.util.lambdaGetCurrReadableTime(), " - creating tasks for this attempt"])
				})

			for task in myAllPendingTasks:
				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newDeployAttemptTasksSql, task)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError(myDBResult["message"])

			# assigning this attempt to deployment env and changing status to in-progress
			myDBResult = self.__markAttemptReady4Deploy(securityToken, deployId, appEnvId, myNewAttemptId, userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])
			
			return self.util.buildResponse(self.Globals.success, self.Globals.success, {"attemptId" : myNewAttemptId})

		except Exception as error:
			self.LOGGER.error("An error occurred while creating new deployment env >>> {error}".format(error = str(error)), exc_info = True)
			raise error
	
	def __markAttemptReady4Deploy(self, securityToken, deployId, appEnvId, attemptId, userId):
		"""
		Assign given attempt to deployment in an environment, deployment env must be in Pending state
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId), ',', str(attemptId), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myDeployEnvStatus = self.getDeployEnvStatus(securityToken, deployId, appEnvId)

			if not self.isDeployEnvAttemptExists(securityToken, deployId, appEnvId, attemptId):
				raise ValueError(f"deployment {depoyId} env {appEnvId} attempt id {attemptId} does not exists !!!")

			if myDeployEnvStatus not in [self.Globals.DEPLOY_STATUS_DEPLOY_PENDING, self.Globals.DEPLOY_STATUS_DEPLOY_UNSUCCESS]:
				raise ValueError(f"Attempt {attemptId} can not be used for deployment, expecting deployment {deployId} env {appEnvId} status >> [{self.Globals.DEPLOY_STATUS_DEPLOY_PENDING}, {self.Globals.DEPLOY_STATUS_DEPLOY_UNSUCCESS}], got {myDeployEnvStatus}")

			myDeployAttemptStatus = self.getDeployAttemptStatus(securityToken, attemptId)

			if not (myDeployAttemptStatus == self.Globals.DEPLOY_STATUS_DEPLOY_PENDING):
				raise ValueError(f"Deployment attempt {attemptId} is not in valid state, expecting {self.Globals.DEPLOY_STATUS_DEPLOY_PENDING}, got {myDeployAttemptStatus}")

			# changing deployment env status to in-progress and assigning this attempt id
			#updDeployEnvStatus(self, securityToken, deployId, appEnvId, status, userId, attemptId = None)
			myDBResult = self.updDeployEnvStatus(securityToken, deployId, appEnvId, self.Globals.DEPLOY_STATUS_DEPLOY_READY, userId, attemptId)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			myDBResult = self.updDeployEnvAttemptStatus(securityToken, deployId, appEnvId, attemptId, self.Globals.DEPLOY_STATUS_DEPLOY_READY, userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred while marking attempt {attemptId} ready for deployment >>> {error}".format(attemptId = str(attemptId), error = str(error)), exc_info = True)
			raise error

	def validateDeployEnv(self, securityToken, deployId, appEnvId, userId):
		"""
		Validates the deployment attempts
		1. Ensure deployment has been validate successfully
		2. Ensure user is allowed to perform the deployment
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.LOGGER.debug("validating deployment status...")

			myDeployData = self.getDeployData(securityToken, deployId)

			if myDeployData["status"] != self.Globals.DEPLOY_STATUS_VALIDATION_SUCCESS:
				raise ValueError(f"Invalid deployment status, expecting {self.Globals.DEPLOY_STATUS_VALIDATION_SUCCESS}, got myDeployData['status']")

			self.LOGGER.debug(f'deployment {deployId} status is validated successfully ')

			self.LOGGER.debug("validating user authorization ...")
			self.LOGGER.debug(f'checking if user {userId} is authorized to perform deployment {deployId} in env {appEnvId}')

			myAppEnvData = self.getAnAppEnvById(securityToken, appEnvId)

			# need to verify if this user is allowed to perfom deployment of this application in this environment
			if not self.isValidUserForDeploy(securityToken, myAppEnvData["app_id"], myAppEnvData["env"], userId):
				raise ValueError(f"user {userId} is not allowed to execute this deployment !!!")

			self.LOGGER.debug("Validation completed successfully, proceeding")

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def validateDeployEnvAttempt(self, securityToken, deployId, appEnvId, attemptId, userId):
		"""
		Validates the deployment env attempts
		1. Ensure deployment has been validate successfully
		2. Ensure attemptid exists for deployid and appenvId
		3. Ensure user is allowed to perform the deployment
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.LOGGER.debug("validating deployment status...")

			myDeployData = self.getDeployData(securityToken, deployId)

			if myDeployData["status"] != self.Globals.DEPLOY_STATUS_VALIDATION_SUCCESS:
				raise ValueError(f"Invalid deployment status, expecting {self.Globals.DEPLOY_STATUS_VALIDATION_SUCCESS}, got myDeployData['status']")

			self.LOGGER.debug(f"deployment {deployId} status is validated successfully ")

			self.LOGGER.debug(f"validating deployment env attempt ids ")

			if not self.isDeployEnvAttemptExists(securityToken, deployId, appEnvId, attemptId):
				raise ValueError(f"Invalid deployment {deployId} env {appEnvId} attempt {attemptId} !!!")

			self.LOGGER.debug(f"Attempt {attemptId} exists for this deployment {deployId} and env {appEnvId} ")

			self.LOGGER.debug("validating user authorization ...")
			self.LOGGER.debug(f'checking if user {userId} is authorized to perform deployment {deployId} in env {appEnvId}')

			myAppEnvData = self.getAnAppEnvById(securityToken, appEnvId)

			# need to verify if this user is allowed to perfom deployment of this application in this environment
			if not self.isValidUserForDeploy(securityToken, myAppEnvData["app_id"], myAppEnvData["env"], userId):
				raise ValueError(f"user {userId} is not allowed to execute this deployment !!!")

			self.LOGGER.debug("Validation completed successfully, proceeding")

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def markAttemptInProg4Deploy(self, securityToken, deployId, appEnvId, attemptId, userId):
		"""
		Update deployment attempt metadata to inprogress
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myDeployEnvStatus = self.getDeployEnvStatus(securityToken, deployId, appEnvId)

			if not self.isDeployEnvAttemptExists(securityToken, deployId, appEnvId, attemptId):
				raise ValueError(f"deployment {depoyId} env {appEnvId} attempt id {attemptId} does not exists !!!")

			if not (myDeployEnvStatus == self.Globals.DEPLOY_STATUS_DEPLOY_READY):
				raise ValueError(f"Deployment attempt {attemptId} can not be started, expecting deployment {deployId} env {appEnvId} status >> '{self.Globals.DEPLOY_STATUS_DEPLOY_READY}', got '{myDeployEnvStatus}' !!!")

			myDeployAttemptStatus = self.getDeployAttemptStatus(securityToken, attemptId)

			if not (myDeployAttemptStatus == self.Globals.DEPLOY_STATUS_DEPLOY_READY):
				raise ValueError(f"Deployment attempt {attemptId} is not in valid state, expecting '{self.Globals.DEPLOY_STATUS_DEPLOY_READY}', got '{myDeployAttemptStatus}' !!!")

			# changing deployment env status to in-progress and assigning this attempt id
			# updDeployEnvStatus(self, securityToken, deployId, appEnvId, status, userId, attemptId = None)
			myDBResult = self.updDeployEnvStatus(securityToken, deployId, appEnvId, self.Globals.DEPLOY_STATUS_DEPLOY_INPROGRESS, userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			myDBResult = self.updDeployEnvAttemptStatus(securityToken, deployId, appEnvId, attemptId, self.Globals.DEPLOY_STATUS_DEPLOY_INPROGRESS, userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred while updating attempt {attemptId} status to inprogress for deployment >>> {error}".format(attemptId = str(attemptId), error = str(error)), exc_info = True)
			raise error

	def updDeployEnvStatus(self, securityToken, deployId, appEnvId, status, userId, attemptId = None):
		"""
		Updates deployment env status and assign attempt id (optional) to this deployment environmetn 
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId), ',', status, ',', userId, ',', str(attemptId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myDeployEnvData = self.getDeployEnvData(securityToken, deployId, appEnvId)
			#myDeployEnvStatus = self.getDeployEnvStatus(securityToken, deployId, appEnvId)

			if not myDeployEnvData:
				raise ValueError("Deployment {deployId} env {appEnvId} metadata missing !!!")

			# we need mapping validation where current status and future status can be passed to see if this update is allowed
			# pending -> in-progress -> success/unsuccess, success-> rollback.success/unsuccess

			if status not in self.Globals.DEPLOY_ATTEMPT_ALL_STATUS:
				raise ValueError(f"Invalid deployment env status '{status}', allowed status {self.Globals.DEPLOY_ATTEMPT_ALL_STATUS} !!!")

			myUpdData = {
				"deployId" : deployId, 
				"appEnvId" : appEnvId, 
				"status" : status, 
				"comments" : "".join([self.util.lambdaGetCurrReadableTime(), f" - changing status to {status} "])
			}
			
			if status == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS:
				myDeployEnvEndTime = self.util.lambdaGetCurrDateTime()
				# removing TZ offset last 3 char stored (at the end of timestamp tz e.g. "-05") in postgres timestamp tz 
				"""
				myDeployEnvData["start_time"]
				from dateutil import parser, tz
				
				myUtcTZ = tz.gettz('UTC')
				myStartTime = parser.parse(myDeployEnvData["start_time"]).astimezone(myUtcTZ).replace(tzinfo=None)
				myDeployEnvDuration = self.util.getElapsedTime(myStartTime)
				"""
				#myDeployEnvDuration = self.util.getElapsedTime(self.util.convertIsoDateStr2Date(myStartTimeStr[:-3]))
				myStartTime = myDeployEnvData["start_time"].replace(tzinfo=None)
				#myDeployEnvDuration = self.util.getElapsedTime(self.util.convertIsoDateStr2Date(myStartTime))
				myDeployEnvDuration = self.util.getElapsedTime(myStartTime)
				myUpdData.update({"endTime" : myDeployEnvEndTime, "duration" : myDeployEnvDuration})
			else:
				myUpdData.update({"endTime" : None, "duration" : None})

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployEnvStatusSql, myUpdData)

			# checking if attempt id was passed, if yes perform the validation and attach attemptid to this deployment environment

			if attemptId:
				if not self.isDeployEnvAttemptExists(securityToken, deployId, appEnvId, attemptId):
					raise ValueError("Invalid deployment {deployId} env {appEnvId} attmept {attemptId} !!!")

				if myDeployEnvData["status"] not in [self.Globals.DEPLOY_STATUS_DEPLOY_PENDING, self.Globals.DEPLOY_STATUS_DEPLOY_UNSUCCESS]:
					raise ValueError(f"Deployment env status must be either in peding or unsuccess state to change attempt id, got {myDeployEnvData['status']} !!!")

				myAttemptStaus = self.getDeployAttemptStatus(securityToken, attemptId)
				if myAttemptStaus != self.Globals.DEPLOY_STATUS_DEPLOY_PENDING:
					raise ValueError(f"Attempt {attemptId} must be in pending state to be assigned to a deployment environment, got {myAttemptStatus} !!!")
				
				myDeployEnvAttemptIdData = self.getDeployEnvAttemptIds(securityToken, deployId, appEnvId)
				#myDeployEnvAttemptIdArg = {"deployId" : deployId, "appEnvId" : appEnvId}
				#myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployEnvAttemptIdsSql, myDeployEnvAttemptIdArg )

				#if myDBResult["status"] == self.Globals.unsuccess:
				#	raise ValueError(f"an erorr occurred {myDBResult['message']} while retrieving deploy {deployId} env {appEnvId} attempt data")

				#myAttemptData = myDBResult

				if myDeployEnvAttemptIdData["attempt_id_list"]:
					myAttemptIdList = myDeployEnvAttemptIdData["attempt_id_list"]
					myAttemptIdList.append(attemptId)
				else:
					myAttemptIdList = [attemptId]

				myAttemptUpdData = {
					"deployId" : deployId, 
					"appEnvId" : appEnvId, 
					"attemptIdList" : myAttemptIdList, 
					"attemptId" : attemptId, 
					"totalAttempts" : len(myAttemptIdList), 
					"comments" : "".join([self.util.lambdaGetCurrReadableTime(), f" - assigning attempt {attemptId}"])
				}

				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployEnvAttemptIdSql, myAttemptUpdData)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError(f"an erorr occurred {myDBResult['message']} while updating attempt data for deployment {deployId} in env {appEnvId}")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred while updating deployment {deployId} env {appEnvId} status {status} >>> {error}".\
				format(deployId = deployId, appEnvId = str(appEnvId), status = status, error = str(error)), exc_info = True)
			raise error

	def updDeployEnvAttemptStatus(self, securityToken, deployId, appEnvId, attemptId, status, userId):
		"""
		Description: Update deployment environment attempt status
			Status : 
				deploy.inProgress
				deploy.unSuccess
				deploy.success
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId), ',', str(attemptId), ',', status, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# checking if we got a valid status
			if not (status in self.Globals.DEPLOY_ATTEMPT_ALL_STATUS):
				raise ValueError(f"invalid deployment attempt status {status} !!!")

			if not self.isDeployEnvAttemptExists(securityToken, deployId, appEnvId, attemptId):
				raise ValueError("Invalid deployment {deployId} env {appEnvId} attempt {attemptId}")

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myAttemptData = self.getDeployAttemptData(securityToken, attemptId)

			myUpdData = {"deployId" : deployId, "appEnvId" : appEnvId, "attemptId" : attemptId, "status" : status}

			myAttemptEndTime = self.util.lambdaGetCurrDateTime()

			myAttemptStartTime = myAttemptData["start_time"].replace(tzinfo=None)

			myAttemptDuration = self.util.getElapsedTime(myAttemptStartTime)

			myUpdData.update({"endTime" : myAttemptEndTime, "duration" : myAttemptDuration})

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployEnvAttemptStatusSql, myUpdData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"error while updating deploymnet id {deployId} environment {env} status to {status}")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def updDeployAttemptTaskStatus(self, securityToken, deployId, env, taskId, status):
		"""
		Description: Update deployment environment task status
			Status : 
				Pending 
				deploy.inProgress
				deploy.unSuccess
				deploy.success
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', env, ',', str(taksId), ',', status])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# checking if we got a valid status
			if not (status in self.Globals.ALL_DEPLOY_STATUS):
				raise ValueError(f"invalid deployment status {status} !!!")

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myUpdData = {"deployId" : deployId, "env" : env, "task_id" : taskId, "status" : status}
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployEnvTaskStatusSql, myUpdData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"error while updating deploymnet id {deployId} environment {env} taks {taskId} status to {status}")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def completeTask(self, securityToken, deployId, attemptId, taskId, result, status, startTime, recordsAffected, beforeImage, afterImage, userId):
		"""
		Description: 
			Update deployment attempt task result in deploy_attempt_tasks
				(status, starttime, endtime, durarion, recordsAffected, result, before image, afterimage)
				Status : 
					Pending 
					deploy.inProgress
					deploy.unSuccess
					deploy.success
			Update deploy env to pending/completed tasks list

		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(attemptId), ',', str(taskId), ',', str(result), ',', status, ',', str(startTime), ',', str(recordsAffected), ',', str(beforeImage), ',', str(afterImage), ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myTaskStatus = self.getDeployAttemptTaskStatus(securityToken, attemptId, taskId)

			if myTaskStatus == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS:
				raise ValueError("Task {taskId} is already deployed, further change is prohibited !!!")

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myTaskCompletionTime = self.util.lambdaGetCurrDateTime()
			myTaskDuration = self.util.getElapsedTime(startTime)

			myUpdData = {
				"deployId" : deployId, 
				"attemptId" : attemptId, 
				"taskId" : taskId, 
				"result" : result, 
				"status" : status,
				"startTime" : startTime,
				"endTime" : myTaskCompletionTime,
				"duration" : myTaskDuration,
				"recordsAffected" : recordsAffected, 
				"beforeDeployImage" : beforeImage, 
				"afterDeployImage" : afterImage}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployAttemptTaskResultSql, myUpdData)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"error while updating deployment {deployId} attempt {attemptId} taks {taskId} result !!!")

			# updating deploy env and deploy attempt (completed/pending task) if task execution was successful
			if status == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS:
				# task execution was successful, updating deploy env completed/pending task stats
				myDeployAttemptData = self.getDeployAttemptData(securityToken, attemptId)

				myDeployEnvId = myDeployAttemptData["app_env_id"]
				myDeployAppId = myDeployAttemptData["app_id"]

				del myDeployAttemptData

				myDeployEnvData = self.getDeployEnvData(securityToken, deployId, myDeployEnvId)
				
				myCompletedTasks = 1 if not myDeployEnvData["completed_tasks"] else myDeployEnvData["completed_tasks"] + 1
				myPendingTasks = 0 if not myDeployEnvData["pending_tasks"] else myDeployEnvData["pending_tasks"] - 1
				
				myCompletedTasksList = self.util.getACopy(myDeployEnvData["completed_tasks_list"])
				myPendingTasksList = self.util.getACopy(myDeployEnvData["pending_tasks_list"])

				# adding to completed tasks list
				if not myCompletedTasksList:
					myCompletedTasksList = []
					myCompletedTasksList.append(taskId)
				else:
					myCompletedTasksList.append(taskId)

				# removing from pending tasks list
				if not myPendingTasksList:
					myPendingTasksList = []
				else:
					self.util.delElemFromList(myPendingTasksList, taskId)

				myDeployEnvUpdateData = {
					"deployId" : deployId,
					"appEnvId" : myDeployEnvId,
					"completedTasks" : myCompletedTasks,
					"completedTasksList" : myCompletedTasksList,
					"pendingTasks" : myPendingTasks,
					"pendingTasksList" : myPendingTasksList
				}

				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployEnvTaskStatsSql, myDeployEnvUpdateData)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError(f"error while updating deployment {deployId} env {myDeployEnvId} taks {taskId} stats !!!")

				# updating deploy_attempt
				myDeployAttemptData = self.getDeployAttemptData(securityToken, attemptId)

				myCompletedTasks = 1 if not myDeployAttemptData["completed_tasks"] else myDeployAttemptData["completed_tasks"] + 1
				myPendingTasks = 0 if not myDeployAttemptData["pending_tasks"] else myDeployAttemptData["pending_tasks"] - 1

				myCompletedTasksList = self.util.getACopy(myDeployAttemptData["completed_tasks_list"])
				myPendingTasksList = self.util.getACopy(myDeployAttemptData["pending_tasks_list"])

				# adding to completed tasks list
				if not myCompletedTasksList:
					myCompletedTasksList = []
					myCompletedTasksList.append(taskId)
				else:
					myCompletedTasksList.append(taskId)

				# removing from pending tasks list
				if not myPendingTasksList:
					myPendingTasksList = []
				else:
					self.util.delElemFromList(myPendingTasksList, taskId)

				myDeployAttemptUpdateData = {
					"deployId" : deployId,
					"attemptId" : attemptId,
					"completedTasks" : myCompletedTasks,
					"completedTasksList" : myCompletedTasksList,
					"pendingTasks" : myPendingTasks,
					"pendingTasksList" : myPendingTasksList
				}

				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updDeployAttempTaskStatsSql, myDeployAttemptUpdateData)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError(f"error while updating deployment {deployId} attempt {attemptId} taks {taskId} stats !!!")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def startDeployAttemptTask(securityToken, deployId, attemptId, taskId, beforeImage, userId):
		"""
		Starts execution of task, updates following attribute to task 
			status : in-progress
			star_time: current time
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', attemptId, ',', str(taksId), ',', str(beforeImage), ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# get task status from repository, status must be in pending state
			# checking if we got a valid status
			myDeployEnvTaskStatus = self.getDeployAttemptTaskStatus(securityToken, attemptId, taskId)

			if not (myDeployEnvTaskStatus == self.Globals.DEPLOY_STATUS_DEPLOY_PENDING):
				raise ValueError(f"Deployment task status must be in pending state, got {myDeployEnvTaskStatus}")

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myUpdArguments = {
				"attemptId" : attemptId, 
				"taskId": taskId, 
				"status" : self.Globals.DEPLOY_STATUS_DEPLOY_INPROGRESS,
				"beforeImage" : beforeImage,
				"startTime" : self.util.lambdaGetCurrDateTime(), 
				"comments": "".join([self.util.lambdaGetCurrReadableTime(), f" - starting task requested by user {userId}"])
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.startDeployAttemptTaskSql, myUpdArguments)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"error while starting (updating) deployment task {attemptId} - {taskId} !!!")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def createDeployObject(self, securityToken, deployId, appId, appEnvId, dbInstance, dbTechnology, dbSchema, objType, objName, objOwner):
		"""
		creates deployment object
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appId), ',', str(appEnvId), ',', dbInstance, ',', dbTechnology, ',', dbSchema, ',', objType, ',', objName])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)
			#isDeployObjExists(self, securityToken, objName, objType, objOwner, schema, env, dbInstance, dbTechnology)
			myDeployObjId = self.getDeployObjId(securityToken, objName, objType, objOwner, dbSchema, appEnvId, dbInstance, dbTechnology)

			#if not self.isDeployObjExists(securityToken, objName, objType, objOwner, dbSchema, appEnvId, dbInstance, dbTechnology):
			if not myDeployObjId:
				newDeployObjData = {
					"appId" : appId,
					"dbInstance" : dbInstance,
					"dbTechnology" : dbTechnology,
					"env" : appEnvId,
					"schema" : dbSchema,
					"objType" : objType,
					"objName" : objName,
					"objOwner" : objOwner,
					"firstDeployId" : deployId,
					"firstDeployDate" : self.util.lambdaGetCurrDateTime(),
					"lastDeployId": deployId,
					"lastDeployDate" : self.util.lambdaGetCurrDateTime(),
					"totalDeployment" : 1
				}
				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newDeployObjSql, newDeployObjData)

			else:
				# updating deploy obj stats
				myDeployObjUpdateData = {
					"deployObjId" : myDeployObjId,
					"lastDeployId" : deployId,
					"lastDeployDate" : self.util.lambdaGetCurrDateTime()
				}

				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.updateDeployObjSql, myDeployObjUpdateData)

			self.LOGGER.debug(f"execution result >>> {myDBResult}")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred while creaeting/updating deployment object >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def createDeployObjHist(self, securityToken, deployId, deployObjId, appId, appEnvId, env, beforeImage, afterImage, category):
		"""
		creates deployment object history
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(deployObjId), ',', str(appId), ',', str(appEnvId), ',', env, ',', str(beforeImage), ',', str(afterImage), ',', category ])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not self.isDeployObjIdExists(securityToken, deployObjId):
				raise ValueError(f"Deployment object {deployObjId} does not exists !!!")

			myNewDeployObjHistory = {
				"deployObjId" : deployObjId,
				"deployId" : deployId,
				"appId" : appId,
				"appEnvId" : appEnvId,
				"env" : env,
				"deploymentDate" : self.util.lambdaGetCurrDateTime(),
				"beforeDeployImage" : beforeImage,
				"afterDeployImage" : afterImage,
				"deploymentCategory" : category
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.newDeployObjHistSql, myNewDeployObjHistory)

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred while creaeting deployment object history >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __finishDeployAttemptTask_donotuse(securityToken, deployId, attemptId, taskId, result, afterImage = None, recordsAffected = None):
		"""
		Pending !!!
		Completes execution of task, updates following attribute to task 
			status : in-progress
			star_time: current time
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', attemptId, ',', str(taksId), ',', str(result), ',', str(recordsAffected)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# get task status from repository, status must be in pending state
			# checking if we got a valid status
			myDeployEnvTaskStatus = self.getDeployAttemptTaskStatus(securityToken, attemptId, taskId)

			if not (myDeployEnvTaskStatus == self.Globals.DEPLOY_STATUS_DEPLOY_INPROGRESS):
				raise ValueError(f"Deployment task status must be {self.Globals.DEPLOY_STATUS_DEPLOY_INPROGRESS}, got {myDeployEnvTaskStatus}")

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myUpdArguments = {
				"attemptId" : attemptId, 
				"taskId": taskId, 
				"status" : self.Globals.DEPLOY_STATUS_DEPLOY_INPROGRESS, 
				"afterImage" : afterImage,
				"endTime" : endTime,
				"duration" : duration,
				"recordsAffected" : recordsAffected,
				"result" : result,  
				"comments": "".join([self.util.lambdaGetCurrReadableTime(), f" - task completed"])
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.finishDeployAttemptTaskSql, myUpdArguments)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"error while finishing (updating) deployment task {attemptId} - {taskId} !!!")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isDeployEnvAttemptExists(self, securityToken, deployId, appEnvId, attemptId):
		"""
		Check if this deployment env attempt exists
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId), ',', str(attemptId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"deployId" : deployId, "appEnvId" : appEnvId, "attemptId" : attemptId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isDeployEnvAttemptExistsSql, mySqlCriteria)

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isDeployEnvExists(self, securityToken, deployId, appEnvId):
		"""
		Check if this deployment exists in deploy_envs table
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"deployId" : deployId, "appEnvId" : appEnvId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isDeployEnvExistsSql, mySqlCriteria)

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isDeployApprovedInEnv(self, securityToken, deployId, appEnvId):
		"""
		checking if this deploy env has been approved
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myDeployEnvData = self.getDeployEnvData(securityToken, deployId, appEnvId, userId)
			
			if myDeployEnvData and \
				myDeployEnvData["status"] == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS and myDeployEnvData["approved_by"]:
				return True
			else:
				return False

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isDeploymentSuccessInPrevEnv(self, deployId, appId, nextAppEnvId, userId):
		"""
		checking if this deployment was successful in previous environment before it can be deployed to next environment
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', env, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myAppDetails = self.getAnAppDetails(securityToken, appId)

			myDeployEnvOrder = myAppDetails["deploy_env_order"]

			myAppEnvDetails = self.getAppEnvDetails(securityToken, appId)

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def buildDeployObjectId(self, securityToken, objectName, objectType, dbSchema, env, dbInstance, dbTechnology):
		"""
		Builds object id which would need to be stored for Object dashboard
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', objectName, ',', objectType, ',', dbSchema, ',', env, ',', dbInstance, ',', dbTechnology])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			return "".join([objectName, ".", objectType, ".", env, ".", dbSchema, ".", dbInstance, ".", dbTechnology])

		except Exception as error:
			self.LOGGER.error("An error occurred while building object id for dashboard >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isDeployObjIdExists(self, securityToken, deployObjId):
		"""
		checks whether given deployment object exists
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(deployObjId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"deployObjId" : deployObjId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isDeployObjIdExistsSql, mySqlCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("An error occurred while building object id for dashboard >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployObjIdInfo(self, securityToken, deployObjId):
		"""
		checks whether given deployment object exists
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(deployObjId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"deployObjId" : deployObjId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployObjIdInfoSql, mySqlCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if "data" in myDBResult and myDBResult["data"]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]}")
				return myDBResult["data"][0]

		except Exception as error:
			self.LOGGER.error("An error occurred while building object id for dashboard >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isDeployObjExists(self, securityToken, objName, objType, objOwner, schema, appEnvId, dbInstance, dbTechnology):
		"""
		checks whether given deployment object exists
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', objName, ',', objType, ',', objOwner, ',', schema, ',', str(appEnvId), ',', dbInstance, ',', dbTechnology])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"objName" : objName, "objType" : objType, "objOwner" : objOwner, "schema" : schema, "env" : appEnvId, "dbInstance" : dbInstance, "dbTechnology" :dbTechnology}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isDeployObjExistsSql, mySqlCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("An error occurred while building object id for dashboard >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployObjId(self, securityToken, objName, objType, objOwner, schema, appEnvId, dbInstance, dbTechnology):
		"""
		Returns deploy object id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', objName, ',', objType, ',', objOwner, ',', schema, ',', str(appEnvId), ',', dbInstance, ',', dbTechnology])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"objName" : objName, "objType" : objType, "objOwner" : objOwner, "schema" : schema, "env" : appEnvId, "dbInstance" : dbInstance, "dbTechnology" :dbTechnology}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployObjIdSql, mySqlCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['deploy_obj_id']}")
				return myDBResult["data"][0]["deploy_obj_id"]

		except Exception as error:
			self.LOGGER.error("An error occurred while building object id for dashboard >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getPrevAppEnv4Deploy(self, securityToken, appId, env):
		"""
		Return previous app env for a given app and its env (env or appEnvId must be passed)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not (env and appId):
				raise ValueError(f"missing mandatory arguments (appId/env) !!! ")

			if not self.isAppEnvExists(securityToken, appId, env):
				raise ValueError(f"Invalid app {apId} env {env} (does not exists) !!! ")

			myAppDetails = self.getAnAppDetails(securityToken, appId)
			
			myDeployEnvOrder = myAppDetails["deploy_env_order"]
			"""
			if env:
				if not self.isAppEnvExists(securityToken, appId, env):
					raise ValueError(f"app {appId} env {env} does not exists !!!")
				myCurrentEnv = env

			if appEnvId:
				if not self.isAppEnvIdExists(securityToken, appId, appEnvId):
					raise ValueError(f"app app {appId} env id {appEnvId} does not exists !!!")
				
				myAppEnvDetails = self.getAppEnvDetails(securityToken, appId)
				myCurrentEnv = [env["env"] for env in myAppEnvDetails if env["app_env_id"] == app_env_id]
				myCurrentEnv = myCurrentEnv[0]
			"""
			# validating if current env is part of deployment env order
			if env not in myDeployEnvOrder:
				raise ValueError(f"Invalid env {env} for app {appId} (env does not exisrs) !!!")

			#we have current env, need to find previous env
			myCurrentEnvPos = myDeployEnvOrder.index(env)
			if myCurrentEnvPos == 0:
				# no previous env exisits returning
				return
			else:
				# index position is more than 1 means we have previous env for this app
				return myDeployEnvOrder[myCurrentEnvPos - 1]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getNextAppEnv4Deploy(self, securityToken, appId, env = None):
		"""
		Return next app env for a given and its env (if env is not passed, return 1st app env)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', str(env)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not appId:
				raise ValueError("missing mandatory arguments (appId) !!! ")

			if env and self.isAppEnvExists(securityToken, appId, env):
				raise ValueError(f"Invalid app {apId} env {env} (does not exists) !!! ")

			myAppDetails = self.getAnAppDetails(securityToken, appId)
			
			myDeployEnvOrder = myAppDetails["deploy_env_order"]

			if not env:
				# env is not passed, returning 1st env from deploy order
				return myDeployEnvOrder[0]

			# validating if current env is part of deployment env order
			if env not in myDeployEnvOrder:
				raise ValueError(f"Invalid env {env} for app {appId} (env does not exists) !!!")

			#we have current env, need to find next env
			myCurrentEnvPos = myDeployEnvOrder.index(env)
			if myCurrentEnvPos == len(myDeployEnvOrder):
				# there are no next environment available, returning
				return
			else:
				# index position is less than length of deploy env order, returning next env
				return myDeployEnvOrder[myCurrentEnvPos + 1]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getTotalDeployAttempt(self, securityToken, deployId, appEnvId):
		"""
		return deployment attempt count for a given deployment and its env
		Arguments:
			attemptId : app environment id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken,',', deployId, ',', str(appEnvId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"deployId" : deployId, "appEnvId" : appEnvId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getTotalDeployAttemptSql, mySqlCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if not myDBResult["data"][0]:
				raise ValueError(f"Invalid deployment {deployId} env {appEnvId} !!!")

			self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['total']}")
			return myDBResult["data"][0]["total"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployAttemptStatus(self, securityToken, attemptId):
		"""
		return deployment attempt status for a given attemt id
		Arguments:
			attemptId : app environment id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken,',', str(attemptId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"attemptId" : attemptId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployAttemptStatusSql, mySqlCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if not myDBResult["data"][0]:
				raise ValueError(f"Invalid deployment attempt {attemptId} !!!")

			self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['status']}")
			return myDBResult["data"][0]["status"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployAttempt4Status(self, securityToken, deployId, apEnvId, status):
		"""
		return deployment attempt details for a given deployment, environment and status
		Arguments:
			deployId: deployment id
			appEnvId : application environment id
			status : 
				deploy.pending, deploy.in-progress, deploy.success and deploy.unsuccess
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', apEnvId, ',', status])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if status not in self.Globals.DEPLOY_ATTEMPT_ALL_STATUS:
				raise ValueError(f"Invalid status, expecting one of value from {self.Globals.DEPLOY_ATTEMPT_ALL_STATUS}, got {status}")

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"deployId" : deployId, "appEnvId" : appEnvId, "status" : status}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployAttempt4StatusSql, mySqlCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __getDeployAttempt4Status__donotuse_dup(self, securityToken, deployId, apEnvId, status):
		"""
		return deployment attempt details for a given deployment, environment and status
		Arguments:
			deployId: deployment id
			appEnvId : application environment id
			status : 
				deploy.pending, deploy.in-progress, deploy.success and deploy.unsuccess
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', appEnvId, ',', status])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if status not in self.Globals.DEPLOY_ATTEMPT_ALL_STATUS:
				raise ValueError(f"Invalid status, expecting one of value from {self.Globals.DEPLOY_ATTEMPT_ALL_STATUS}, got {status}")

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"deployId" : deployId, "appEnvId" : appEnvId, "status" : status}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployAttempt4StatusSql, mySqlCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployAttemptData(self, securityToken, attemptId):
		"""
		return deployment attempt data for a given attempt id
		Arguments:
			attemptId: attempt id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(attemptId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"attemptId" : attemptId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployAttemptDataSql, mySqlCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]}")
				return myDBResult["data"][0]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployEnvData(self, securityToken, deployId, appEnvId):
		"""
		returns deployment environment data
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"deployId" : deployId, "appEnvId" : appEnvId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployEnvDataSql, mySqlCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]}")
				return myDBResult["data"][0]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployEnvPendingTasks(self, securityToken, deployId, appEnvId):
		"""
		Returns all pending tasks for given deployment and its app env id. Will check if we have an attempt for this
		deployment in env. if an attempt found, will return all unsuccess task from that attempt else will return all
		task for this deployment
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not self.isDeployEnvExists(securityToken, deployId, appEnvId):
				raise ValueError(f"Deployment id {deployId} and env {appEnvId} does not exists !!!")

			myDeployEnvAttemptData = self.getDeployEnvAttemptIds(securityToken, deployId, appEnvId)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if myDeployEnvAttemptData["attempt_id"]:
				# we have an attempt, retrieving all unsuccess task for this attempt
				mySqlCriteria = {"attemptId" : myDeployEnvAttemptData["attempt_id"]}
				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAttemptPendingTasksSql, mySqlCriteria)
			else:
				# no attempt found returning all task for this deployment
				mySqlCriteria = {"deployId" : deployId}
				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployTasksSql, mySqlCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.LOGGER.debug(f"returning pending tasks >>> {myDBResult['data']}")
			
			return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error <<{error}>> occurred while retrieving pending tasks for deployment id {deployId} and env {env} ".\
				format(error = str(error), deployId = str(deployId), env = str(appEnvId)), exc_info = True)
			raise error

	def getDeployAttemptTask(self, securityToken, attemptId, taskId):
		"""
		returns deploy env task data from {deployAttemptTask}
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(attemptId), ',', str(taskId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"attemptId" : attemptId, "taskId" : taskId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployAttemptTaskSql, mySqlCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]}")
			return myDBResult["data"][0]

		except Exception as error:
			self.LOGGER.error("An error <<{error}>> occurred while retrieving pending tasks for deployment id {deployId} and env {env} ".\
				format(error = str(error), deployId = str(deployId), env = str(appEnvId)), exc_info = True)
			raise error

	def getDeployAttemptAllTask(self, securityToken, attemptId):
		"""
		returns all task for a given attempt from {deployAttemptTask}
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(attemptId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"attemptId" : attemptId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployAttemptAllTaskSql, mySqlCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error <<{error}>> occurred while retrieving pending tasks for deployment id {deployId} and env {env} ".\
				format(error = str(error), deployId = str(deployId), env = str(appEnvId)), exc_info = True)
			raise error

	def getDeployAttemptTaskStatus(self, securityToken, attemptId, taskId):
		"""
		returns deploy attempt task status for a given attempt and task id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(attemptId), ',', str(taskId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myAttemptTaskData = self.getDeployAttemptTask(securityToken, attemptId, taskId)

			if myAttemptTaskData:
				return myAttemptTaskData["status"]

		except Exception as error:
			self.LOGGER.error("An error <<{error}>> occurred while retrieving pending tasks for deployment id {deployId} and env {env} ".\
				format(error = str(error), deployId = str(deployId), env = str(appEnvId)), exc_info = True)
			raise error

	def getDeployEnvStatus(self, securityToken, deployId, appEnvId):
		"""
		Returns the deployment status in a given environment
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"deployId" : deployId, "appEnvId" : appEnvId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployEnvStatusSql, mySqlCriteria)
	
			if not myDBResult["data"]:
				raise ValueError(f"Invalid deployment {deployId} env {appEnvId} !!!")

			self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['status']}")

			return myDBResult["data"][0]["status"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployEnvAttemptIds(self, securityToken, deployId, appEnvId):
		"""
		Returns deployment attempts in environment
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"deployId" : deployId, "appEnvId" : appEnvId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployEnvAttemptIdsSql, mySqlCriteria)
	
			if not myDBResult["data"]:
				raise ValueError(f"Invalid deployment {deployId} env {appEnvId} !!!")

			self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]}")

			return myDBResult["data"][0]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isDeploySuccessfulInEnv(self, securityToken, deployId, appEnvId):
		"""
		checking if this deploy env has been deployed successfully in this environment
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myDeployEnvStatus = self.getDeployEnvStatus(securityToken, deployId, appEnvId)
			
			if myDeployEnvStatus == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS:
				return True
			else:
				return False

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isDeployEnvApproved(self, securityToken, deployId, appEnvId):
		"""
		checking if this deploy env has been deployed successfully in this environment
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myDeployEnvStatus = self.getDeployEnvStatus(securityToken, deployId, appEnvId)
			
			if myDeployEnvStatus == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS_APPROVED:
				return True
			else:
				return False

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getUniqueEnvAttemptTaskStatus(self, securityToken, deployId, appEnvId, attemptId):
		"""
		Retrieve distinct status for a given
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			mySqlCriteria = {"deployId" : deployId, "appEnvId" : appEnvId, "attemptId" : attemptId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getUniqueEnvAttemptTaskStatusSql, mySqlCriteria)
	
			if not myDBResult["data"]:
				raise ValueError(f"Invalid deployment {deployId} env {appEnvId} attempt {attemptId} !!!")

			myDistinctStatus = tuple([status["status"] for status in myDBResult["data"]])

			return myDistinctStatus

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error
	### Perform deployment ends

	def isDeployFilesChanged(self, securityToken, deployId, deployFileLocation):
		"""
		checks if new deployment files or any changes in exisiting deployment files are found in download location for given deployment id
		Arguments:
			1. securityToken : security token
			2. deployId : deployment id
		"""
		try:

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', deployFileLocation])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			#myDeployDownloadLoc = self.util.buildPath(self.Globals.DEPLOY_DOWNLOAD_LOC, deployId)

			myDeployReadmeFile = self.util.buildPath(deployFileLocation, self.Globals.DEPLOY_README_FILE)

			# returning False if deployment download location is empty for this deployment
			if self.util.isDirEmpty(deployFileLocation):
				self.LOGGER.debug("deploy download loc is empty, rturning false !")
				return False

			# deployment download location is not empty

			# get activeDeployControlId for this deployment
			myActiveDeployCtrlId = self.getActiveDeployCtrlId(securityToken, deployId)

			# returning true, if no active deployment control id found and we have some deployment files (checked earlier)
			if not myActiveDeployCtrlId: 
				self.LOGGER.debug("no active deploy ctrl found, rturning true !")
				return True

			# we have active deployment control, need to get the file stats
			myDeployFileStats = self.getDeployCtrlFileStats(securityToken, myActiveDeployCtrlId)
			self.LOGGER.debug("deploy file stats from repository >> {stats}".format(stats = str(myDeployFileStats)))

			# returning true, if file stats not found and we have some deployment files (checked earlier) 
			if not myDeployFileStats: 
				self.LOGGER.debug("active deploy ctrl found but file stats is empty, rturning true")
				return True

			# loading deploy readme file to get deployment files
			myDeployReadmeData = self.util.readJsonFile(myDeployReadmeFile)
			
			myFilesAtDownloadLoc = [self.util.buildPath(deployFileLocation,file["file"]) for file in myDeployReadmeData["deploy"] ]

			# adding deployment files to download location list
			myFilesAtDownloadLoc.append(self.util.buildPath(deployFileLocation,myDeployReadmeFile))

			myFilesInRepository = [file["file"] for file in myDeployFileStats]
			
			self.LOGGER.info(f"files found from repository {myFilesInRepository}")
			self.LOGGER.info(f"files downloaded from source {myFilesAtDownloadLoc}")
			
			# returning True if we got new files added or any existing files are removed
			if set(myFilesAtDownloadLoc) != set(myFilesInRepository):
				self.LOGGER.debug("deployment files downloaded at location <{download}> and deployment files stored in repository <{stats}> not marching, returing true !"\
					.format(download = str(myFilesAtDownloadLoc), stats = str(myFilesInRepository)))
				return True

			self.LOGGER.info("there are no changes in total # of deployment files, validating of any changes in downloaded files (size, modify time etc.) ")
			# we have same set of files which is already present in repository and in download loc, checking if modified time has been changed for any of the file
			myDeployFilesChanged = False

			for file in myFilesAtDownloadLoc:
				myDeployFileInRepoStats = [stats for stats in myDeployFileStats if stats["file"] == file] 
				
				if myDeployFileInRepoStats: myDeployFileInRepoStats = myDeployFileInRepoStats[0]

				myDownloadedFileStats = self.util.getFileStats(self.util.buildPath(deployFileLocation, file))
				
				self.LOGGER.info("download file {file} stats >> {stats}".format(file = file, stats = str(myDownloadedFileStats)))
				self.LOGGER.info("repository file {file} stats >> {stats}".format(file = file, stats = str(myDeployFileInRepoStats)))

				"""
				if not (self.util.convertIsoDateStr2Date(myDeployFileInRepoStats["create_time"]) == myDownloadedFileStats["create_time"] and \
					self.util.convertIsoDateStr2Date(myDeployFileInRepoStats["modify_time"]) == myDownloadedFileStats["modify_time"] and \
					myDeployFileInRepoStats["size_bytes"] == myDownloadedFileStats["size_bytes"]):
				"""
				if not (self.util.convertIsoDateStr2Date(myDeployFileInRepoStats["modify_time"]) == myDownloadedFileStats["modify_time"] and \
					int(myDeployFileInRepoStats["size_bytes"]) == int(myDownloadedFileStats["size_bytes"])):

					self.LOGGER.info("size/modify {stats}is not matching for file {file}, deployment files are changed".\
						format(file = file, \
							stats = "".join([ \
								"modify time (", \
										"repo:", str(self.util.convertIsoDateStr2Date(myDeployFileInRepoStats["modify_time"])), \
										" download: ", str(myDownloadedFileStats["modify_time"]), \
										")", \
								"size (", \
										"repo:", str(myDeployFileInRepoStats["size_bytes"]), \
										" download: ", str(myDownloadedFileStats["size_bytes"])\
							])
					))

					# found files changed
					myDeployFilesChanged = True

					break
			
			self.LOGGER.debug(f"returning >>> {myDeployFilesChanged}")
			return myDeployFilesChanged

		except Exception as error:
			self.LOGGER.error("An error occurred while reprocessing deploy files >>> {error}, rolling back current txn".format(error = str(error)), exc_info = True)
			raise error

	def validateNewDeployment(self, securityToken, deployId, appId, userId):
		"""
		Description: Validates new deployment, following rules will be used for validation
			1. check if this deployment is not in use
			2. Checks if this app is ready for approval 
			3. Checks if this app is ready for approval
			4. Path where deployment files have been downloaded 

		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', str(appId), ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myAppName = self.getAnAppDetails(securityToken, appId)
			myDeployFilePath = self.util.buildPath(self.Globals.DEPLOY_DOWNLOAD_LOC, str(deployId))

			# starting validations

			# 1. check if this deployment already exists
			myValidationStep = "1"

			self.LOGGER.debug("validating deployment id ...")

			if self.isDeploymentExists(securityToken, deployId):
				#raise ValueError("deployment id {id} is already in use !!!".format(id = deployId))
				myValidationMsg = f"Validation error {myValidationStep} - deploymen id {deployId} is already in use !!!"

				self.LOGGER.error(myValidationMsg)

				return self.util.buildResponse(self.Globals.unsuccess, myValidationMsg)

			self.LOGGER.debug("deployment id {id} id not is use, proceeding with rest of validation ")

			# 2. Checks if this app is ready for approval
			myValidationStep = "2"

			self.LOGGER.debug("validating app for deployment ...")
			self.LOGGER.debug("checking if app {app} is ready for deployment ".format(app = str(appId)))

			if not self.isAppReadyForDeploy(securityToken, appId):
				#raise ValueError("application {app} is not ready for deployment, app status must be in {valStatus}) !!!".\
				#	format(app = "".join([app_name, " - ", str(appId)]), valStatus = str(self.Globals.VALID_APP_STATUS_4_DEPLOYMENT) ))

				myValidationMsg = f"Validation error {myValidationStep} - application {app} is not ready for deployment, app status must be in {self.Globals.VALID_APP_STATUS_4_DEPLOYMENT}) !!!"

				self.LOGGER.error(myValidationMsg)

				return self.util.buildResponse(self.Globals.unsuccess, myValidationMsg)

			self.LOGGER.debug("app {app} is ready for deployment, proceeding with rest of validation ".format(app = str(appId)))

			# 3. Checks if user is authorized to perform this application deployment
			myValidationStep = "3"

			self.LOGGER.debug('retrieving env where user is allowed to submit the deployment for this application')
			
			#myAppEnv4Deployment = self.getUserDeploy1stEnv(securityToken, appId)
			#getNextAppEnv4Deploy(self, securityToken, appId, env = None)
			myAppEnv4Deployment = self.getNextAppEnv4Deploy(securityToken, appId)

			self.LOGGER.debug('found env {env} where user can submit the deployment of this app'.format(env = myAppEnv4Deployment))

			self.LOGGER.debug("validating user authorization ...")

			self.LOGGER.debug("checking if user {id} is authorized to submit deployment for app {app} ".format(id = userId, app = str(appId)))

			if not self.isValidUserForDeploy(securityToken, appId, myAppEnv4Deployment, userId):
				#raise ValueError("user {user} is not authorized to perform deployment of application {app} in {env} !!!".format(\
				#	user = userId, app = str(appId), env = myAppEnv4Deployment))

				myValidationMsg = f"Validation error {myValidationStep} - user {userId} is not authorized to perform deployment of application {appId} in {myAppEnv4Deployment} !!!"

				self.LOGGER.error(myValidationMsg)

				return self.util.buildResponse(self.Globals.unsuccess, myValidationMsg)

			self.LOGGER.debug("user {id} is authorized to submit deployment for app {app}, proceeding with rest of validation ".format(id = userId, app = str(appId)))

			# 4.1 checking if deploy readme file is present
			myValidationStep = "4.1"

			self.LOGGER.debug("validating deploy readme file ...")

			myDeployReadmeFile = self.util.buildPath(myDeployFilePath,self.Globals.DEPLOY_README_FILE)

			if not self.util.isFileExists(myDeployReadmeFile):
				#raise ValueError("missing mandatory deployment readme file {file} !!!".format(file = myDeployReadmeFile))
				myValidationMsg = f"Validation error {myValidationStep} - missing mandatory deployment readme file {myDeployReadmeFile} !!!"

				self.LOGGER.error(myValidationMsg)

				return self.util.buildResponse(self.Globals.unsuccess, myValidationMsg)
			
			self.LOGGER.debug("deployment readme file {file} exists ".format(file = myDeployReadmeFile))
			myDeployReadme = self.util.readJsonFile(myDeployReadmeFile)

			# 4.2 validating readme file contents
			myValidationStep = "4.2"

			self.LOGGER.debug("validating deploy readme file contents ...")

			if not myDeployReadme:
				#raise ValueError("deployment readme file {file} is empty".format(file = myDeployReadmeFile))
				myValidationMsg = f"Validation error {myValidationStep} - deployment readme file {myDeployReadmeFile} is empty !!!"

				self.LOGGER.error(myValidationMsg)

				return self.util.buildResponse(self.Globals.unsuccess, myValidationMsg)

			self.LOGGER.debug("deployment readme file {file} is not empty".format(file = myDeployReadmeFile))

			# 5.1 key value validation
			myValidationStep = "5.1"

			if not ("app" in myDeployReadme and "dbTechnology" in myDeployReadme and \
					"preDeploy" in myDeployReadme and "checkUserConn" in myDeployReadme["preDeploy"] and \
					"backup" in myDeployReadme["preDeploy"] and "deploy" in myDeployReadme ):

				#raise ValueError("deploy instruction file {file} is corrupted (missing mandatory keys) !!!".\
				#	format(expect = "".join([appId, myDeployReadme["app"]])))

				myValidationMsg = f"Validation error {myValidationStep} - deploy instruction file {file} is corrupted (missing mandatory keys app/dbTechnology/deploy/preDeploy.checkuserConn/backup) !!!"

				self.LOGGER.error(myValidationMsg)

				return self.util.buildResponse(self.Globals.unsuccess, myValidationMsg)

			self.LOGGER.debug("found mandatory key app/dbTechnology/preDepoy/deploy etc. in file {file} ".format(file = myDeployReadmeFile))

			# 5.2 app/appid validation
			myValidationStep = "5.2"

			if not("app" in  myDeployReadme and myDeployReadme["app"] == appId):
				#raise ValueError("mismatch application id in deployment readme file {file}, expecting {expect}, got {got} !!!".\
				#	format(expect = str(appId), got = myDeployReadme["app"], file = myDeployReadmeFile))

				myValidationMsg = f"Validation error {myValidationStep} - mismatch application id in deployment readme file {myDeployReadmeFile}, expecting {appId}, got {myDeployReadme['app']} !!!"

				self.LOGGER.error(myValidationMsg)

				return self.util.buildResponse(self.Globals.unsuccess, myValidationMsg)
			
			self.LOGGER.debug("found valid app id in deploy readme file {file}".format(file = myDeployReadmeFile))

			# 6. validating deployment files
			myValidationStep = "6"

			self.LOGGER.debug("validating all deployment files listed in deploy readme")

			mySeq = 0
			myDeployFiles = self.util.sortDictInListByKey(self.util.getACopy(myDeployReadme["deploy"]), "seq", False)

			myValidationError = False

			for file in myDeployFiles:
				myFiles = []
				mySeq += 1 
				#print("my seq", mySeq)
				if file["op"] == "run":
					myFiles.append(file["file"])
				elif file["op"] == "load":
					myFiles.append(file["dataFile"])
					myFiles.append(file["file"])

				missingFiles = [file for file in myFiles if not self.util.isFileExists(self.util.buildPath(myDeployFilePath,self.util.getFileName(file)))]

				if missingFiles:
					myValidationMsg = f"Validstion error {myValidationStep} - deployment file(s) are missing >>> {missingFiles}"
					myValidationError = True
					break

				if file["seq"] != mySeq:
					myValidationMsg = f"Validation error {myValidationStep} - invalid seq# for {file['file']}, expecting seq# {mySeq}, got seq# {file['seq']} !!!" 
					myValidationError = True
					break
					#raise ValueError("invalid seq# for {file}, expecting {expect}, got {got} ".format(file = file["file"], expect = str(mySeq), got = file["seq"]))


			#if missingFiles:
			#	raise ValueError("deployment file(s) are missing >>> {files}".format(files = str(missingFiles)))
			if myValidationError:
				self.LOGGER.error(f"deployment validation error {myValidationMsg}")				
				return self.util.buildResponse(self.Globals.unsuccess, myValidationMsg)

			self.LOGGER.debug("found all deployment files")

			# validation completed		
			self.LOGGER.info("all validation completed successfully !!!")
	
		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployData(self, securityToken, deployId):
		"""
		Returns deployment data (detialed) for a given deploymentId
		Arguments:
			1. securityToken : security token
			2. deployId: deployment id
		"""
		try:

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployDataSql, {"deployId" : deployId})

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.LOGGER.info(f"result >>> {myDBResult}")

			if myDBResult["data"]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]}")
				return myDBResult["data"][0]
			else:
				return

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployCtrlTasks(self, securityToken, deployId):
		"""
		Returns all tasks for a given deploy ctrl id
		Arguments:
			1. securityToken : security token
			2. deployId: deployment id
		"""
		try:

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# retrieving deployment ctrl id for this deployment
			myActiveDeployCtrlId = self.getActiveDeployCtrlId(securityToken, deployId)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployCtrlTasksSql, {"deployId" : deployId, "deployCtrlId" : myActiveDeployCtrlId})

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.LOGGER.info(f"result >>> {myDBResult}")

			if myDBResult["data"]:
				return myDBResult["data"]
			else:
				return

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployCtrl(self, securityToken, deployCtrlId):
		"""
		Returns deploy ctrl data
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployCtrlId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)
			
			myCriteria = {"deployCtrlId" : deployCtrlId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployCtrlSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))
			
			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				self.LOGGER.info("returning deploy ctrl data >>> {result}".format(result = str(myDBResult["data"][0])))
				return myDBResult["data"][0]
		
		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployCtrlFileStats(self, securityToken, deployCtrlId):
		"""
		Returns deploy ctrl data
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployCtrlId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			myDeployCtrlData = self.getDeployCtrl(securityToken, deployCtrlId)

			if myDeployCtrlData and "deploy_file_stats" in myDeployCtrlData:
				return myDeployCtrlData["deploy_file_stats"]
		
		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getActiveDeployCtrlId(self, securityToken, deployId):
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

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployCtrlIdSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				myActivedeployCtrlId = myDBResult["data"][0]["deploy_ctrl_id"]

			self.LOGGER.info("returning >> {result}".format(result = str(myActivedeployCtrlId)))

			return myActivedeployCtrlId

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['status']}")
				return myDBResult["data"][0]["status"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isJiraInUseForDeploy(self, securityToken, jiraIssueId):
		"""
		Description: Checks if given jira issue id is in use for any other deployment
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', jiraIssueId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"jiraIssueId" : jiraIssueId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isJiraInUseForDeploySql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isDeploymentCtrlExists(self, securityToken, deployCtrlId):
		"""
		Description: Checks if this deployment control exists
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(deployCtrlId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"deployCtrlId" : deployCtrlId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isDeploymentCtrlExistsSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeploymentCtrlStatus(self, securityToken, deployCtrlId):
		"""
		Description: Returns deployment control status from app.deploy_ctrl
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(deployCtrlId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"deployCtrlId" : deployCtrlId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeployCtrlStatusSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["data"][0]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['status']}")
				return myDBResult["data"][0]["status"]
			else:
				return

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getValidAppEnvUserList(self, securityToken, appId, env):
		"""
		Returns all valid user for a given app id and its environment. If contact type is stored as AD group, return all user fo that ad group
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			# need contactid for this app and env
			myDBResult = self.getAnEnvContactDetails(securityToken, appId, env)
			
			myAllUserLists = []

			if not myDBResult:
				raise ValueError(f"data corruption, no contact details found for {appId} and env {env}") 

			for contact in myDBResult:
				if contact["contact_type"] in self.Globals.ALL_CONTACT_TYPE_ADGRP_LIST and contact["status"] in self.Globals.VALID_STATUS_LIST:
					# we got ad group, need to get all member of this group
					myAllUserIds = self.util.getAdGroupMemberIds(contact["contact_id"])
					[myAllUserLists.append(user.lower()) for user in myAllUserIds]
				else:
					myAllUserLists.append(contact["contact_id"].lower())

			return myAllUserLists

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isValidUserForDeploy(self, securityToken, appId, env, userId):
		"""
		Description: Checks if this user is allowed to perform the deployment for this application and its environment
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myAllValidUsersList = self.getValidAppEnvUserList(securityToken, appId, env)

			self.LOGGER.info("all valid users for app >> {result}".format(app = ''.join([str(appId), '-', env]), result = str(myAllValidUsersList)))

			if userId.lower() in myAllValidUsersList:
				return True
			else:
				return False

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isAppReadyForDeploy(self, securityToken, appId):
		"""
		Description: Checks if application is ready for deployment. (App must be in valid state and not in Blackout)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			#self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myAppStatus = self.getAppStatusById(securityToken, appId)

			#myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppStatusByIdSql, myCriteria)

			if myAppStatus in self.Globals.VALID_STATUS_LIST:
				return True
			else:
				return False
			#self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			#if myDBResult["status"] == self.Globals.unsuccess:
			#	raise ValueError(myDBResult["message"])

			#if myDBResult["data"][0]["total"] == 0:
			#	return False
			#else:
			#	return True

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isProessDeployFilesAllowed(self, securityToken, deployId):
		"""
		Description: Checks whether reprocessing or deploy files are allowed for a given deployment id
		Arguments:
		"""
		try:

			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if self.isDeploymentExists(securityToken, deployId):
				# new deployment validating status
				myDeployStatus = self.getDeployStatus(securityToken, deployId)
				
				self.LOGGER.debug("found deployment status >> {status}".format(status = myDeployStatus))

				if myDeployStatus not in self.Globals.VALID_STATUS_RELOAD_DEPLOY_FILES_LIST:

					self.LOGGER.debug("deployment status is not in valid state to generate new deployment ctrl, expecting {expect}, got {got}, aborting !!!".\
						format(expect = self.Globals.VALID_STATUS_RELOAD_DEPLOY_FILES_LIST, got = myDeployStatus))
					
					return False
				else:
					return True
			else:
				return True

		except Exception as error:
			self.LOGGER.error("An error occurred while checking reprocess of deployment files allowed >>> {error} !!!".format(error = str(error)), exc_info = True)
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

			myCriteria = {"appId" : str(appId)}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isAppExistsSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __isAppExistsByTag__donotuse(self, securityToken, appTag):
		"""
		checks if a given app name already exists in repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', appTag])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"appTag" : appTag}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isAppExistsByTagSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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

			myCriteria = {"appId" : appId, "env" : env}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isAppEnvExistsSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isAppEnvExistsByName(self, securityToken, appName, env):
		"""
		checks if a given app (app name) env exists in CICD repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', appName, ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"appName" : appName, "env" : env}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isAppEnvExistsByNameSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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

			myAppEnvId = self.getAppEnvId(securityToken, appId, env)

			myCriteria = {"appId" : appId, "appEnvId" : myAppEnvId, "contactType" : contactType, "contactId" : contactId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isAppEnvContactExistsSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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
				return self.dbaas.isValidOraDBInst(**myAguments)

		except Exception as error:
			self.LOGGER.error('an error occurred >>> {error}'.format(error = str(error)), exc_info = True)
			raise error

	def isValidDBSchema(self, securityToken, opco, region, appId, hostName, dbTechnology, dbInstance, dbSchemas, env):
		"""
		checks if db instance is valid for given opco/region/appName/hostName/dbTechnology and env
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = ''.join([securityToken, ',', opco, ',', region, ',', str(appId), ',', hostName, ',', dbTechnology, ',', dbInstance, ',', str(dbSchemas), ',', env])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if dbTechnology.lower() == self.Globals.TECHNOLOGY_ORACLE.lower():
				myAguments = {
					"securityToken" : securityToken,
					"opco" : opco,
					"region" : region,
					"appId" : appId,
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
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	# need decorator
	def getDBSchema4OnBoarding(self, securityToken, opco, region, dbTechnology, appId):
		"""
		Returns alll available schema(s) for onboarding, pull all schemas which is present in all environment in 
		DBAAS repository. If this is 1st environment return all env received from DBAAS else return the schema list which has already been onboarded
		For e.g. 
			DBAAS
				App : CANSYS
				DEV (schema) : ACT, CERT, ACTIVITY
				STG (schema) : ACT, CERT
				PROD (schema) : ACT, CERT

			During 1st time onboarding (1st env), returns ACT, CERT from DBAAS
			Consecutive onboarding return schema list from app.app.dbschemas

		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', opco, ',', region, ',', dbTechnology, ',', str(appId) ])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# checking if this application has been onboarded regardless of its state, if onboarded return db_schemas from CICD repository

			if self.isAppExists(securityToken, appId):
				myAppDetails = self.getAnAppDetails(securityToken, appId)

				self.LOGGER.info('found schema list from CICD repository for app {app} >>> {schemaList}'.format(app = appId, schemaList = str(myAppDetails["db_schemas"])))

				return myAppDetails["db_schemas"]

			# this app is not onboarded, retrieving available schema from dbaas

			if dbTechnology.lower() == self.Globals.TECHNOLOGY_ORACLE.lower():
				#def dbaasGetOraDBCommonSchemas(securityToekn, opco, region, dbTechnology, appId)
				mydbaasDBSchema = self.dbaasGetOraDBCommonSchemas(securityToken, opco, region, dbTechnology, appId)
			else:
				return

			self.LOGGER.info('found schema list from dbaas for app {app} >>> {schemaList}'.format(app = str(appId), schemaList = str(mydbaasDBSchema)))

			if not mydbaasDBSchema:
				return

			# retrieving all schema in use for this db instance from repository

			myCriteria = {
				"appId" : appId,
				"opco" : opco.lower(),
				"region" : region.lower(), 
				#"dbInstance" : dbInstance, 
				"dbTechnology" : dbTechnology.lower()
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDBSchemaInUseSql, myCriteria)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError('error while retrieving in-use schema list from repository for app >>> {app}'.format(app = str(appId)))

			self.LOGGER.info('found schema list in use from CICD repository for app {app} >>> {schemaList}'.format(app = str(appId), schemaList = str(myDBResult["data"])))

			# available schema for onboarding
			if myDBResult["data"]:
				mySchemaInUseList = myDBResult["data"][0]["db_schemas"]
			else:
				mySchemaInUseList = []

			#print('dbaas schema >>>', mydbaasDBSchema)
			#print('in use schema >>>', mySchemaInUseList)

			myAvailableSchemaList = list(set([schema['SCHEMA'] for schema in mydbaasDBSchema]) - set(mySchemaInUseList))

			self.LOGGER.info('returning available schema list for {app} >>> {schemaList}'.format(app = str(appId), schemaList = str(myAvailableSchemaList)))

			return myAvailableSchemaList

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAllApps4OnBoarding(self, securityToken, opco, region, dbTechnology, userId):
		"""
		retrieves list of application which is available for on boarding
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# retrieving all application lists from dbaas
			myAlldbaasApplists = self.dbaasGetAllApps(securityToken, opco, region, dbTechnology)
			self.LOGGER.debug('found {total} application(s) from dbass'.format(total = len(myAlldbaasApplists)))
			# retrieving all app which is on boarded and approved (need to exclude them from top list)

			myAllApprovedAppLists = self.getAllAppDetail(securityToken, opco, region, dbTechnology, self.Globals.STATUS_ACTIVE)
			myApprovedAppIds = [app["app_id"] for app in myAllApprovedAppLists]

			self.LOGGER.info("found application list which is already on boarded and approved >>> {result}".format(result = str(myApprovedAppIds)))

			# retrieving other users (except this users) pending app (also filter the application which is in pending state on boarded by other user)			
			myAllExclPendingApp = self.getAllPendingAppExclMe(securityToken, opco, region, dbTechnology, userId)
			myOtherUserPendingAppIds = [app["app_id"] for app in myAllExclPendingApp]

			self.LOGGER.info("found application list which is in pending state but does not belong to this user >>> {result}".format(result = str(myOtherUserPendingAppIds)))

			# retrieving this users pending app (will remove from main list and add this to on boarding list)
			myPendingApp = self.getMyPendingApp(securityToken, opco, region, dbTechnology, userId)
			myPendingAppIds = [app["app_id"] for app in myPendingApp]

			self.LOGGER.info("found this users application list which is in pending state >>> {result}".format(result = str(myPendingAppIds)))

			# building exclusion list, exclude app... 
			# 1. app which is on boarded in active state
			# 2. app which is onboarded by other user and in pending state

			myExclAppIds = list(set(myApprovedAppIds + myOtherUserPendingAppIds))

			self.LOGGER.info("final exclusion app id list >>> {exclList}".format(exclList = str(myExclAppIds)))

			# removing all exclusion list from main dbaas app list
			myOnBoardingApp = []

			for app in myAlldbaasApplists:
				if not(app["APP_ID"] in myExclAppIds) :
					# app is not in exlusion, will check if this external app id has any associated app in pending state. if found, will add them to list

					# an app can have multiple entries (this is possible because we may have multiple suppprt team for a given app)
					# if app already exist in list of app which will be returned, will add support team to an existing support team
					"""
					will return
					[{"APP_ID" : ....., "SUPPORT_TEAM" : []}]
					"""
					if self.util.isDictKeyValueExistsInList(myOnBoardingApp, "APP_ID", app["APP_ID"]):
						self.LOGGER.info("adding app support team {supportTeam} to on boarding app >>> {app}".format(\
							app = str(app), supportTeam = app["SUPPORT_TEAM"]))
						
						for boardingApp in myOnBoardingApp:
							if boardingApp["APP_ID"] == app["APP_ID"]:
								boardingApp["SUPPORT"]["TEAM"].append(app["SUPPORT_TEAM"])
								boardingApp["SUPPORT"]["EMAIL"].append(app["SUPPORT_EMAIL"])
					else:
						self.LOGGER.info("adding app to on boarding list >>> {app}".format(app = str(app)))
						# making support team as an array
						app.update({"SUPPORT" : {"TEAM" : [app["SUPPORT_TEAM"]], "EMAIL" : [app["SUPPORT_EMAIL"]]}})
						#final_dict = {key: t[key] for key in t if key not in [key1, key2]}
						myFinalAppDict = self.util.removeKeysFromDict(app, ["SUPPORT_TEAM","SUPPORT_EMAIL"])
						myOnBoardingApp.append(myFinalAppDict)

			"""
			we dont need to add pending app 
			# processing pending app (adding them to onboarding list)
			for pendingApp in myPendingApp:
				# found app associated with this external app in pending state, 
				# adding all assocated pedning app to the list
				mySupportTeam = [app["SUPPORT_TEAM"] for app in myAlldbaasApplists if app["APP_ID"] == pendingApp["ext_app_id"]]
				mySupportEmail = [app["SUPPORT_EMAIL"] for app in myAlldbaasApplists if app["APP_ID"] == pendingApp["ext_app_id"]]
				pendingApp.update({"SUPPORT" : {"TEAM" : mySupportTeam, "EMAIL" : mySupportEmail}})
				myOnBoardingApp.append(pendingApp)

			# add app_id of apps which is already onboarded by this user, need to update the app_tag
			"""

			self.LOGGER.info("total {tot} app is ready for on boarding, returning app list >>> {result}".format(tot = str(len(myOnBoardingApp)), result = str(myOnBoardingApp)))

			#removing duplicate app which might be due to multiple notification dl
			return myOnBoardingApp

		except Exception as error:
			self.LOGGER.error("An error occurred while retrieving application list for on boarding >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAllAppEnvInUse(self, securityToken, appId):
		"""
		retrieves list of application and env which is either in process of on boarding or has been successfully onboarded
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"appId" : appId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAllAppEnvInUseSql, myCriteria)

			# we need to remove the env which might have been deleted or marked as inactive
			# for e.g. env.del.**, env.inactive
			myAllEnv = [{"env" : env["env"]} for env in myDBResult["data"] if len(env["env"].lower().split(".")) == 1 ]

			self.LOGGER.info("db result >>> {result}".format(result = myDBResult))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("An error {error} occurred while retrieving env list in use for app {app} !!!".\
					format(error = myDBResult["message"], app = str(appId)))

			#return myDBResult["data"]
			return myAllEnv

		except Exception as error:
			self.LOGGER.error("An error occurred while retrieving application env in use >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAllAppsEnv4OnBoarding(self, securityToken, opco, region, dbTechnology, appId, userId):
		"""
		returns all environment from dbaas for a given opco/region/technology and app name
		"""
		try:
			self.LOGGER.debug('got arguments >>> {args}'.format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', str(appId), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myAllAppEnvFromDbaas = self.dbaasGetAllUniqueEnvs(securityToken, opco, region, dbTechnology, appId)

			if self.isAppExists(securityToken, appId):
				# app tag exists, will substract env which is on boarded
				#myAppId = self.getAppIdByTag(securityToken, appName)

				myAppEnvInUse = self.getAllAppEnvInUse(securityToken, appId)

				myAppEnvInUseList = [env["env"] for env in myAppEnvInUse]

			else:
				# this is new app tag, will return all available env fro dbaas, 
				# we should also remove env fo whom all schema has been on boarded **** (Pending)
				myAppEnvInUseList = []

			self.LOGGER.debug("env from dbaas <{dbaasEnv}>, env in use in CICD repo <{env}>".format(dbaasEnv = str(myAllAppEnvFromDbaas), env = str(myAppEnvInUseList)))

			myAvailableEnv = [env for env in myAllAppEnvFromDbaas if env["ENV"].lower() not in myAppEnvInUseList]

			self.LOGGER.info("returning >> {result}".format(result = str(myAvailableEnv)))

			return myAvailableEnv

		except Exception as error:
			myErrorMsg = 'an error occurred >>> {error}'.format(error = str(error))
			self.LOGGER.error(myErrorMsg, exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)

	def getAllAppDetail(self, securityToken, opco, region, dbTechnology, status):
		# Returns all app for a given opco, region, dbTechnology  and status from CICD repository
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', status])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"opco" : opco.lower(), "region" : region.lower(), "dbTechnology" : dbTechnology, "status" : status}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAllApp4OpcoRegionTechStatusSql, myCriteria)

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
				if myAllEnvs:
					# we may have an app which does not have any env (this is remote possibility but accomodating this scenario)
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
						self.LOGGER.info("found app env details >>> {envDetails}".format(envDetails = str(myEnv)))
						myAppEnv.append(myEnv)
						print("app env >>>", myAppEnv)

					myApp["env"].append(myAppEnv)
					#print("app all env >>>", myApp)
				myAppDetails.append(myApp)
				#print("app all app details >>>", myAppDetails)
				
				self.LOGGER.info("found app details >>> {appDetails}".format(appDetails = str(myAppEnv)))
				self.LOGGER.info("found all app details >>> {appDetails}".format(appDetails = str(myAppDetails)))

			return myAppDetails

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAllPendingAppExclMe(self, securityToken, opco, region, dbTechnology, userId):
		# Returns all pending app for a given opco/region excluding given userid app
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# since ad group is stored as a valid onwer/contact for all app and its environment, we need ad group for this user
			myAllAdGrpTuple = tuple([adgrp.lower() for adgrp in self.util.getUserAdGrp(userId)])

			if not myAllAdGrpTuple: myAllAdGrpTuple = ('')

			myCriteria = {"opco" : opco.lower(), "region" : region.lower(), "dbTechnology" : dbTechnology, "adGroupArray" : myAllAdGrpTuple, "status" : self.Globals.STATUS_PENDING}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAllAppExclUsrSql, myCriteria)

			if myDBResult["status"] == self.Globals.success:
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getMyPendingApp(self, securityToken, opco, region, dbTechnology, userId):
		# Returns all pending app env waiting for approval for a given userId
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# retrieving all ad group of this user id
			myADGrpList = [adgrp.lower() for adgrp in self.util.getUserAdGrp(userId)]
			
			myADGrpTuple = ('')

			if myADGrpList: myADGrpTuple = tuple(myADGrpList)

			myCriteria = {
				"contactIdList" : myADGrpTuple,
				"opco" : opco.lower(), 
				"region" : region.lower(), 
				"dbTechnology" : dbTechnology, 
				"status" : self.Globals.STATUS_PENDING
			}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getMyAppByStatusSql, myCriteria)

			if myDBResult["status"] == self.Globals.success:
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAppApproverIds(self, securityToken, dbTechnology):
		"""
		Returns all approver network id for a given database technology
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', dbTechnology])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			#self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			"""
			# would need all owner approver and admin approved
			# retrieving all owner approver
			myAppEnvContactArg = {"appId" : appId, "env" : appEnv}
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getValidAppEnvOwnerIds, myAppEnvContactArg)

			myApproverIds = []

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				for id in myDBResult["data"]:
					myApproverIds.append(id["contact_id"].lower())

			#retrieving all admin id for this app
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getValidAppEnvAdminGrp, myAppEnvContactArg)
			myAdminGrpList = []
			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				for grp in myDBResult["data"]:
					myAdminGrpList.append(grp["contact_id"])

			"""
			self.LOGGER.debug("ad group list >>> {adgrp}".format(adgrp = str(self.ADMIN_GROUP[dbTechnology.lower()])))
			myAdminIds = self.util.getAdGroupMemberIds(self.ADMIN_GROUP[dbTechnology.lower()])
			self.LOGGER.debug(f"got admin ids >>> {myAdminIds}")

			myApproverIds = [adminId.lower() for adminId in myAdminIds]

			#removing duplicate ids
			"""
			# pulling data from valid_approver, all id in this table can approve all apps
			myCriteria = {}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppEnvApproverSql, {})

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError("An error occurred while retrieving approver id list >>> {error}".format(error = myDBResult["message"]))

			return myDBResult["data"]
			"""
			self.LOGGER.debug(f"returning >>> {myApproverIds}")
			return myApproverIds

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAppIdByName(self, securityToken, appName):
		"""
		returns app id for a given applicaiton Name from CICD repository
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
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['app_id']}")
				return myDBResult["data"][0]["app_id"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['status']}")
				return myDBResult["data"][0]["status"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['status']}")
				return myDBResult["data"][0]["status"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getUserDeploy1stEnv(self, securityToken, appId):
		"""
		returns app deploy env order (array) from repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			#self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppExists(securityToken, appId)):
				raise ValueError("Invalid app id {appId}".format(appId = str(appId)))

			myAllAppDeployEnv = self.getDeployEnvOrder(securityToken, appId)

			return myAllAppDeployEnv[0]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['deploy_env_order']}")
				return myDBResult["data"][0]["deploy_env_order"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAppEnvId(self, securityToken, appId, env):
		"""
		Returns app env id for a given app and env
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppEnvExists(securityToken, appId, env)):
				raise ValueError("Invalid app id/env {appId}".format(appId = "".join([str(appId), ",", env])))

			myCriteria = {"appId" : appId, "env" : env}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppEnvIdSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"][0]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['app_env_id']}")
				return myDBResult["data"][0]["app_env_id"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAnAppEnvById(self, securityToken, appEnvId):
		"""
		Returns app env details for a given app env id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appEnvId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppEnvIdExists(securityToken, appEnvId)):
				raise ValueError(f"Invalid app env id {appEnvId}")

			myCriteria = {"appEnvId" : appEnvId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAnAppEnvByIdSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]}")
				return myDBResult["data"][0]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def isAppEnvIdExists(self, securityToken, appEnvId):
		"""
		Checks if given app env id exists
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appEnvId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"appEnvId" : appEnvId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.isAppEnvIdExistsSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult["data"][0]["total"] == 0:
				return False
			else:
				return True

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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

			myCriteria = {"appId" : appId, "env" : env}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppEnvStatusSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"][0]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['status']}")
				return myDBResult["data"][0]["status"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]}")
				return myDBResult["data"][0]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAppEnvStatusById(self, securityToken, appEnvId):
		"""
		returns app (id) env status from repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appEnvId) ])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppEnvIdExists(securityToken, appEnvId)):
				raise ValueError("Invalid appEnvId {appEnvId}".format(appEnvId = "".join([str(appEnvId)])))

			myCriteria = {"appEnvId" : appEnvId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppEnvStatusByIdSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"][0]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['status']}")
				return myDBResult["data"][0]["status"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAppEnvStatusByName(self, securityToken, appName, env):
		"""
		returns app (name) env status from repository for given app tag
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', appName, ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppEnvExistsByTag(securityToken, appName)):
				raise ValueError("Invalid app {app}".format(app = "".join([appName, ",", env])))

			myCriteria = {"appName" : appName, "env" : env}
			
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppEnvStatusByTagSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"][0]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]['status']}")
				return myDBResult["data"][0]["status"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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

			myCriteria = {"appId" : appId, "env" : env}
			
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAnEnv4AppSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				# we ust have only one record thus returning as dict (1st record from list)
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]}")
				return myDBResult["data"][0]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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
				self.LOGGER.debug(f"returning >>> {myDBResult['data']}")
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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

			myAppEnvId = self.getAppEnvId(securityToken, appId, env)

			myCriteria = {"appId" : appId, "appEnvId" : myAppEnvId}
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getContacts4AppEnvSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data']}")
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getAnEnvContactByType(self, securityToken, appId, env, contactType):
		"""
		returns all contact information for a given app and its env
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appId), ',', env, ',', contactType])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppEnvExists(securityToken, appId, env)):
				raise ValueError("Invalid app id/env {appId}".format(appId = "".join([str(appId), ",", env])))

			myAppEnvId = self.getAppEnvId(securityToken, appId, env)

			myCriteria = {"appEnvId" : myAppEnvId,"contactType" : contactType}
			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppEnvContactByType, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data']}")
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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
				self.LOGGER.debug(f"returning >>> {myDBResult['data']}")
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			self.pg.rollback(securityToken, self.PG_CONN)
			raise error

	def __getAppListByExtAppId__donotuse(self, securityToken, extAppId):
		"""
		returns an app details for a given external applicartion id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(extAppId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"extAppId" : extAppId}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppListByExtAppIdSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data']}")
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __getAnAppDetailsByTag__donotuse(self, securityToken, appTag):
		"""
		returns an app details for given application tag
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', str(appTag)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			if not(self.isAppExistsByTag(securityToken, appTag)):
				raise ValueError("Invalid application {app}".format(appId = str(appTag)))

			myCriteria = {"appTag" : appTag}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAnAppByTagSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"][0]:
				self.LOGGER.debug(f"returning >>> {myDBResult['data'][0]}")
				return myDBResult["data"][0]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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

			myAppEnvId = self.getAppEnvId(securityToken, appId, env)

			myCriteria = {"appId" : appId, "appEnvId" : myAppEnvId, "pendingKW" : "".join(["%",self.Globals.STATUS_PENDING])}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getPendingContacts4EnvSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"]:
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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

			myCriteria = {"appId" : appId, "pendingKW" : "".join(["%",self.Globals.STATUS_PENDING])}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAppPendingEnvSql, myCriteria)

			self.LOGGER.info("db result >> {result}".format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			if myDBResult and "data" in myDBResult and myDBResult["data"] and myDBResult["data"]:
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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
			if myAppStatus == self.Globals.STATUS_VALID:
				return 'app is in Valid state'

			# checking if any env is in pending state
			myPendingEnvData = self.getAllPendingEnv4App(securityToken, appId)

			if myPendingEnvData:
				# we found atleast 1 app env in pending state
				myPendingEnv = [env['env'] for env in myPendingEnvData]
				return 'env {env} is in pedning state  '.format(env = str(myPendingEnv))

			"""
			commenting below block, we rather need to check if all env recorded in dbaas is onboarded
			# checking if we got 1 lower and 1 prod environment
			myAllEnvData = self.getAppEnvDetails(securityToken, appId)
			myAllEnvList = [env['env'] for env in myAllEnvData]
			
			if not( self.Globals.ENV_PROD in myAllEnvList and all(env in myAllEnvList for env in self.Globals.ENV_LOWER)):
				# we have missing minimum env for this app (we need 1 prod and atleast 1 lower env)
				return 'Atleast 1 non-prod and prod env is required, got >> {got}'.format(got = str(myAllEnvList))
			"""

			# there are no pending env for this app, checking if we got all env on boarded as recorded in dbaas

			myAllEnvData = self.getAppEnvDetails(securityToken, appId)
			myAllEnvList = [env['env'].lower() for env in myAllEnvData]

			myAppDetails = self.getAnAppDetails(securityToken, appId)

			myDBResult = self.dbaasGetAllUniqueEnvs(\
					securityToken, \
					myAppDetails["opco"], \
					myAppDetails["region"], \
					myAppDetails["technology"], \
					myAppDetails["app_id"]
			)

			#myAllAppEnvFromDbaas = [env ["ENV"].lower() for env in myDBResult]
			myAllAppEnvFromDbaas = [env["ENV"].lower() for env in myDBResult]

			self.LOGGER.debug(f"env onboarded > {myAllEnvList}, env recorded in dbaas > {myAllAppEnvFromDbaas}")

			if self.Globals.ENV_PROD.lower() not in myAllAppEnvFromDbaas: myAllAppEnvFromDbaas.append(self.Globals.ENV_PROD.lower())

			myRemainingEnvList = list(set(myAllAppEnvFromDbaas) - set(myAllEnvList))

			if myRemainingEnvList:
				return 'remaining env [{remainingEnv}] need to be onboarded for this app >> {app} !!!'.\
					format(remainingEnv = str(myRemainingEnvList), app = ''.join([myAppDetails["app_name"], ".", str(appId)]))
			else:
				if myAppDetails["status"].split(".")[-1:] == self.Globals.STATUS_PENDING:
					return 'all criteria met for this app to be in valid state, need force validation, Pls contact DBA !!!'
				else:
					return myAppDetails["status"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getMyAppList(self, securityToken, opco, region, dbTechnology, userId, appStatus = None):
		"""
		returns list of all app with status (detailed status) for a given userid and status, if status is not passed will return all app
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', userId, ',', str(appStatus)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myAdGrpList = [adgrp.lower() for adgrp in self.util.getUserAdGrp(userId)]
			
			myAdGrpTuple = ('')

			if myAdGrpList: myAdGrpTuple = tuple(myAdGrpList)

			myCriteria = {"opco" : opco, "region" : region, "dbTechnology" : dbTechnology, "contactIdList" : myAdGrpTuple}

			if appStatus:
				# retrieving users all app for a given status
				myCriteria.update({"status" : appStatus})

				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getMyAppByStatusSql, myCriteria)
			else:
				myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getMyAppSql, myCriteria)
		
			self.LOGGER.info('got db results >>> {result}'.format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError('error {error} retrieving app list for user >>> {user}'.format(user = str(userId), error = myDBResult["message"]))

			if "data" in myDBResult and myDBResult["data"]:
				# found app, updating detailed status 
				for app in myDBResult["data"]:
					myDetailedStatus = self.getAppDetailedStatus(securityToken, app["app_id"])
					app.update({"status" : myDetailedStatus})

				self.LOGGER.info('returning app list for user {user} >>> {appLists}'.format(user = userId, appLists = str(myDBResult["data"])))
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getPendingEnv4OpcoRegion(self, securityToken, opco, region, dbTechnology):
		"""
		returns list of all app and its env in pending state for a given opco/region/dbTechnology
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ",", opco, ",", region, ',', dbTechnology])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			myCriteria = {"opco" : opco.lower(), "region" : region.lower(), "dbTechnology" : dbTechnology, "pendingKW" : "".join(["%",self.Globals.STATUS_PENDING])}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getAllPendingAppEnvSql, myCriteria)
			
			self.LOGGER.info('got db results >>> {result}'.format(result = str(myDBResult)))

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError('error {error} retrieving pending app list'.format(error = myDBResult["message"]))

			if "data" in myDBResult and myDBResult["data"]:
				# found app in pedning state
				self.LOGGER.info('returning all pending app list >>> {pendingList}'.format(pendingList = str(myDBResult["data"])))
				return myDBResult["data"]

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
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

	def getMyAppForApproval(self, securityToken, opco, region, dbTechnology, userId):
		"""
		returns all app which is available for approval for a given user id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, userId])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# we need to validate if a given userid is valid approver, if yes will return all pending app for approval
			if self.isValidApprover(securityToken, userId):
				# this is a valid approver (approver is DBA and authorized to approve all pending app/env), returning all application in pending state
				self.LOGGER.info('approver {userId} is a valid approver'.format(userId = userId))

				myDBResult = self.getPendingEnv4OpcoRegion(securityToken, opco, region, dbTechnology)

				self.LOGGER.info('returning pending app list for user {user} >>> {pendingList}'.format(user = userId, pendingList = str(myDBResult)))

				return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def getDeployServerDetails(self, securityToken, jiraIssueId, env):
		"""
		Returns server details for a given jira id and environment
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', jiraIssueId, ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			self.LOGGER.debug(f"retrieving server details for jira id {jiraIssueId}, env {env}")

			myCriteria = {"jiraIssueId" : jiraIssueId, "env" : env}

			myDBResult = self.pg.execSql(securityToken, self.PG_CONN, self.getDeploymentServerSql, myCriteria)

			self.LOGGER.info(f'returning server details for jira id {jiraIssueId}, env {env} >>> {myDBResult}')

			if myDBResult and "data" in myDBResult:
				return myDBResult["data"]
			else:
				return []

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def validateDeployEnvOrder(self, securityToken, deployId, env):
		"""
		Validates the deployment environment to ensure that env stated in application's deployment environment order is maintained
			1. Deployment in previous must be successfully deployed/approved
			2. Next environment in which deployment is performed marching the deployment order for this app 
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.PG_CONN = self.pg.validateConn(securityToken, self.PG_REPO, self.PG_CONN)

			# retrieving deloyment and environment details
			myDeployData = self.getDeployData(securityToken, deployId)
			myAppDetails = self.getAnAppDetails(securityToken, myDeployData["app_id"])
			myAppEnvId = self.getAppEnvId(securityToken, myDeployData["app_id"], env)
			myAppEnvData = self.getAnAppEnvById(securityToken, myAppEnvId)
			myDeployEnvOrder = myAppDetails["deploy_env_order"]

			""" 
			1. checking if this deployment is already performed in this environment
			"""
			myDeployEnvData = self.getDeployEnvData(securityToken, deployId, myAppEnvId)

			if myDeployEnvData and myDeployEnvData["status"] == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS:
				return self.util.buildResponse(self.Globals.unsuccess, f"Deployment id {deployId} in env {env} is already successfully deployed !!")

			"""
			2. checking if deployment is performed successfully and approved in previous environment 
				checking if there is any previous environment exists and if dployment was successful and approved in that environment
			"""
			myPrevEnv = self.getPrevAppEnv4Deploy(securityToken, myDeployData["app_id"], myAppEnvData["env"])

			if myPrevEnv:
				# previous environment found, validating previous environment deployment

				self.LOGGER.debug(f"Found previus deployment env {myPrevEnv}, will ensure deployment to be successful and approved in this environment")

				myPrevEnvDetails = self.getAnEnvDetails(securityToken, myDeployData["app_id"], myPrevEnv)

				myDeployEnvStatus = self.getDeployEnvStatus(securityToken, deployId, myPrevEnvDetails["app_env_id"])

				if myDeployEnvStatus != self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS_APPROVED:
					return self.util.buildResponse(self.Globals.unsuccess, f"Deployment id {deployId} has not been deployed successfully deployed/approved in previous environment [{myPrevEnvDetails['env']}] !!!")

			"""
			3. checking if deployment has been successfully performed in all previous environment, not sure if we need this
				as step 2 should suffice this 
			"""
			# retrieving previous environment lists
			myPreviousEnvList = myDeployEnvOrder[:myDeployEnvOrder.index(env.strip().lower())]

			# found previous environment list, checking if deployment is performed in these environments
			for prevEnv in myPreviousEnvList:
				# checking if deployment is perfored in previous environment

				# retrieving appenv id for this environment (env found in previous environment list)
				myPrevAppEnvId = self.getAppEnvId(securityToken, myDeployData["app_id"], prevEnv)

				if not self.isDeployEnvExists(securityToken, deployId, myPrevAppEnvId):
					return self.util.buildResponse(self.Globals.unsuccess, \
						f"Deployment id {deployId} has not been successfully deployed/approved in previous environment {prevEnv} !!!")

				# checking if previous deployment was successfull and approved
				
				# retreving deployment data for this env (environment found in previous environment)
				myResult = self.getDeployEnvData(securityToken, deployId, myPrevAppEnvId)

				self.LOGGER.debug(f"result for deployment {deployId} in previous env {myPrevAppEnvId} >>> {myResult}")

				if myResult["status"] !=  self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS_APPROVED:
					return self.util.buildResponse(self.Globals.unsuccess, \
						f"Deployment {deployId} must be successfully deployed in {prevEnv} and validated before it can be deployed in  {env} !!!")

			self.LOGGER.debug(f"all validation met for deployment {deployId} to be performed in env {env}")

			return self.util.buildResponse(self.Globals.success, self.Globals.success)

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error		
	"""
	***** CICD Repo method (get data) ends
	""" 

	""" 
	***** dbaas Method starts, these methods are wrapper for dbaas methods ***** 
	"""

	def dbaasGetAllApps(self, securityToken, opco, region, dbTechnology):
		"""
		returns all application for a given opco/region/technology
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology ])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "opco" : opco, "region" : region, 'dbTechnology' : dbTechnology}

			myDBResult = self.dbaas.getAllApplications(**mydbaasArgs)

			self.LOGGER.info("returning applications for this request >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetAllUniqueEnvs(self, securityToken, opco, region, dbTechnology, appId):
		"""
		returns all application for a given opco/region
			[{'ENV': '<env1>'}, {'ENV': '<env2>'}, {'ENV': '<envN>'}]
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', str(appId) ])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "opco" : opco, "region" : region, "dbTechnology" : dbTechnology, "appId" : appId}

			myDBResult = self.dbaas.getAllAppEnv(**mydbaasArgs)

			# removing duplicate env, we might have got it due to multiple db instances for each env
			myAllEnvironment = [env["ENV"] for env in myDBResult]
			myAllEnvironment = list(set(myAllEnvironment))
			myAllEnvironment = [{"ENV": env} for env in myAllEnvironment]

			self.LOGGER.info("returning all env for application {app} >>> {result}".format(app = "".join([opco,'.',region,'.',dbTechnology,'.',str(appId)]), result = str(myDBResult)))

			return myAllEnvironment

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetAllDBInst(self, securityToken, opco, region, dbTechnology, appId, env):
		"""
		returns all db for a given db region/region/dbTechnology/env
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', str(appId), ',', env])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "opco" : opco, "region" : region, "dbTechnology" : dbTechnology, "appId" : appId, "env" : env}

			myDBResult = self.dbaas.getAllDBInstances(**mydbaasArgs)

			self.LOGGER.info("returning databases for this request >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetOraDBCommonSchemas(self, securityToken, opco, region, dbTechnology, appId):
		"""
		returns all db/schemas for a Oracle db dbTechnology, opco, region and environment using dbaas 
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {
				"securityToken" : securityToken, 
				"opco" : opco, 
				"region" : region, 
				"dbTechnology" : dbTechnology, 
				"appId" : appId, 
			}

			myDBResult = self.dbaas.getOraDBCommonShemas(**mydbaasArgs)

			self.LOGGER.info("returning common (available in all env) database/schemas for this request >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetOraDBSchemas(self, securityToken, opco, region, dbTechnology, appId, env, hostName, dbInstance):
		"""
		returns all db/schemas for a Oracle db dbTechnology, opco, region and environment using dbaas 
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', str(appId), ',', env, ',', hostName, ',', dbInstance])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {
				"securityToken" : securityToken, 
				"opco" : opco, 
				"region" : region, 
				"dbTechnology" : dbTechnology, 
				"appId" : appId, 
				"env" : env,				
				"hostName" : hostName, 
				"dbInstance" : dbInstance
			}

			myDBResult = self.dbaas.getOraDBSchemas(**mydbaasArgs)

			self.LOGGER.info("returning database/schemas for this request >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetAppInfo(self, securityToken, opco, region, dbTechnology, appId):
		"""
		returns application info for a given opco/region/application name
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "opco" : opco, "region" : region, "dbTechnology" : dbTechnology, "appId" : appId}
			myDBResult = self.dbaas.getAppInfo(**mydbaasArgs)

			self.LOGGER.info("returning app id this request >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetAppInfoByAppId(self, securityToken, appId):
		"""
		returns application info for a given application Id
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, str(appId)])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "appId" : appId}
			myDBResult = self.dbaas.getAppInfoByAppId(**mydbaasArgs)

			self.LOGGER.info("returning app id this request >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetDBInstURI(self, securityToken, opco, region, dbTechnology, hostName, dbInstance):
		"""
		returns connect string for a given database/db instance 
		"""
		try:
			self.LOGGER.debug('got arguments >>>{args}'.format(args = "".join([securityToken, ',', opco, ',', region, ',', dbTechnology, ',', hostName, ',', dbInstance ])))
			
			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			mydbaasArgs = {"securityToken" : securityToken, "opco" : opco, "region" : region, "dbTechnology" : dbTechnology, "hostName" : hostName, "dbInstance" : dbInstance}
			myDBResult = self.dbaas.getDBConnectStr(**mydbaasArgs)

			if not myDBResult:
				raise ValueError("could not find connect string from dbaas for (opco.region.dbTechnology.hostName.dbInstance) >>> {app}".format(app = "".join([opco, ".", region, ".", dbTechnology, ".", hostName, ".", dbInstance])))

			self.LOGGER.info("returning connect string for this request >>> {result}".format(result = str(myDBResult)))

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def dbaasGetDBIURIWoHost(self, securityToken, opco, region, dbTehnology, dbInstance):
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
			self.LOGGER.error("An error occurred >>> {error}".format(error = str(error)), exc_info = True)
			raise error


	""" 
	***** dbaas Method ends *****
	"""

if __name__ == "__main__":
	print("testing cicd repo class method ....")
	sec = Security()
	mySecToken = sec.authenticate('DMZPROD01\\svc-dev-deploy-app','eXokNzl5NEUzOWdXNCkp')
	repo = Repository(mySecToken)

	# testing new session
	"""
	myRequest = {
		"encKey" : "eXokNzl5NEUzOWdXNCkp",
		"userId" : "u1167965",
		"method" : "getAllAppEnvFromDbaas",
		"args" : {
			"region" : "NAM",
			"opco" : "MARSH",
			"dbTechnology" : "Oracle",
	 		"appId" : 207
		}
	}

	# startSession(self, securityToken, userId, sessionAuth, accessRoute, request, comments)
	myStartTime = repo.util.getStartTimeSecs()
	mySessionId = repo.startSession(mySecToken, "svc-dev-deploy-app",{"auth" : "AD authentication"}, ["10.0.0.0","127.0.0.1"],myRequest, "new session")
	repo.util.sleep(10)
	myElapsed = repo.util.getElapsedTime(myStartTime)
	repo.completeSession(mySecToken, mySessionId, myElapsed)
	"""
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
	
	# onboard application
	#myAppName = 'Test'

	mySchemaName = 'MWAY_ETL_TEST_OWNER'
	myRegion = 'nam'
	myOpco = 'marsh'
	myDBTechnology = 'Oracle'
	#myTech = 'oracle'
	myEnv = 'DEV'
	myUserId = 'u1167965'
	myIssueId = 'MADBD-32'

	print('retrieving all pending app from CICD (executing getAllAppDetail)>>> {app}'.format(app = "".join([myOpco, ".", myRegion, ".", myDBTechnology, ".", repo.Globals.STATUS_PENDING])))
	myAllAppDetails = repo.getAllAppDetail(mySecToken, myOpco, myRegion, myDBTechnology, repo.Globals.STATUS_PENDING)
	print('all app details >>>', myAllAppDetails)

	print('retrieving all app available for onboarding (executing getAllApps4OnBoarding)>>> {app}'.format(app = "".join([myOpco, ".", myRegion, ".", myDBTechnology])))
	myAllApp4OnBoarding = repo.getAllApps4OnBoarding(mySecToken, myOpco, myRegion, myDBTechnology, myUserId)
	print('total app available for onboarding >>>', len(myAllApp4OnBoarding))

	#myOwnerIdList = ['u107854','test.cicd']
	myOwnerIdList = ['ctfy-ug_na_marsh_dba-s-l']
	myNotifyDLList = ['MARSH_APP_TEST_APPOWNER_DL', 'MARSH_APP_TEST_APPSUPP_DL', 'MARSH_APP_TEST_BUSOWNER_DL']

	print("retrieving all application for >>> {} (executing dbaasGetAllApps)".format(''.join([myOpco.upper(),'.', myRegion.upper(), ".", myDBTechnology])))
	myAllApps = repo.dbaasGetAllApps(mySecToken, myOpco.upper(), myRegion.upper(), myDBTechnology)
	print('all applications count >>>', len(myAllApps))

	print(" <<< completed >>>")

	myApp = "CANSYS"
	myAppDetails = [app for app in myAllApps if app["APP_NAME"] == myApp]

	myAppName = myAppDetails[0]["APP_NAME"]
	myAppDesc = myAppDetails[0]["APP_DESC"]
	#myAppTag = "Cansys 001"
	myAppId = myAppDetails[0]["APP_ID"]
	myNotifyEmail = myAppDetails[0]["SUPPORT_EMAIL"]
	#myDeployEnvOrder = ["dev","prod"]

	print("retrieving all env for >>> {} (execuring dbaasGetAllDBInst)".format(''.join([myOpco.upper(),'.', myRegion.upper()])))
	#def dbaasGetAllUniqueEnvs(self, securityToken, opco, region, dbTechnology, appId):
	myAllEnv = repo.dbaasGetAllUniqueEnvs(mySecToken, myOpco, myRegion, myDBTechnology, myAppId)
	print("all environments for app {appId} >>>".format(appId = str(myAppId)), myAllEnv)
	myDeployEnvOrder = [env["ENV"] for env in myAllEnv]
	print("retrieving all db instances for >>> {} (execuring dbaasGetAllDBInst)".format(''.join([myOpco.upper(),'.', myRegion.upper()])))
	#def dbaasGetAllDBInst(self, securityToken, opco, region, dbTechnology, appId, env):
	myAllDbInstances = repo.dbaasGetAllDBInst(mySecToken, myOpco, myRegion, myDBTechnology, myAppId, myEnv)

	for dbInstance in myAllDbInstances:
		print(dbInstance)

	print(" <<< completed >>>")

	myDbInstance = "OLTD147"
	myHostName = "usdfw23db26v"

	print("executing dbaasGetDBInstURI >>> ")
	#dbaasGetDBInstURI(self, securityToken, opco, region, dbTehnology, hostName, dbInstance)
	myDBResult = repo.dbaasGetDBInstURI(mySecToken, myOpco, myRegion, myDBTechnology, myHostName, myDbInstance)
	print("db result >>>", myDBResult)
	myConnectStr = myDBResult["connectStr"]
	print("connect string for {dbInst} >>> {result}".format(dbInst = "".join([myHostName, ".", myDbInstance, ".", myDBTechnology]), result = myConnectStr))
	print(" <<< completed >>>")

	print("retrieving all db/schemas for >>> {} (execuring dbaasGetOraDBSchemas)".format(''.join([myOpco.upper(),'.', myRegion.upper(), '.', str(myAppId),'.', myHostName, '.', myDBTechnology, '.', myEnv, '.', myDbInstance])))
	#dbaasGetOraDBSchemas(self, securityToken, opco, region, dbTechnology, appId, env, hostName, dbInstance)
	myAllDbSchemas = repo.dbaasGetOraDBSchemas(mySecToken, myOpco, myRegion, myDBTechnology, myAppId, myEnv, myHostName, myDbInstance)

	for db in myAllDbSchemas:
		print(db)
	print(" <<< completed >>>")

	"""
	testing dbschemas for on boarding
from com.mmc.cicd.cicd_repo_pg import Repository
from com.mmc.common.security import Security
sec = Security()
mySecToken = sec.authenticate('DMZPROD01\\svc-dev-deploy-app','eXokNzl5NEUzOWdXNCkp')
repo = Repository(mySecToken)
repo.getDBSchema4OnBoarding(mySecToken, 'marsh', 'nam', 'Oracle', '20700001', 'MOD', 'usdfw23db26v', 'OLTD147')
	"""

	print("executing getDBSchema4OnBoarding >>> ")
	#getDBSchema4OnBoarding(self, securityToken, opco, region, dbTechnology, appId):
	myAvailDbSchemas = repo.getDBSchema4OnBoarding(mySecToken, myOpco, myRegion, myDBTechnology, myAppId)
	print("schemas available for app {app} >>> {schemas}".format(app = str(myAppId), schemas = str(myAvailDbSchemas)))
	print("completed getDBSchema4OnBoarding.")

	mySchemas = ['ACT','ADMIN','BINDER','CERT','CLAIM']

	print("validating db instance/schema")
	myResult = repo.isValidDBSchema(mySecToken, myOpco, myRegion, myAppId, myHostName, myDBTechnology, myDbInstance, mySchemas, myEnv)
	print('db instance/schema validation >>>', myResult)
	
	print("on boarding app >> ")
	myAppInfo = """
		app Id   : {appId}		issue (jira) : {issueId}
		opco     : {opco}
		region   : {region} 
		app Name : {appName}
		app Desc : {appDesc}
		DB Technology : {dbTechnology}
		deploy env order : {deployEnvOrder}
		env      : {env}
		host     : {host} 
		DB (inst) : {dbInst}
		DB/Schemas : {dbSchemas}
	""".format(issueId = myIssueId, appId = str(myAppId), opco = myOpco, region = myRegion, appName = myAppName, appDesc = myAppDesc, \
		dbTechnology = myDBTechnology, deployEnvOrder = myDeployEnvOrder, \
		env = myEnv, host = myHostName, dbInst = myDbInstance, dbSchemas = mySchemas)

	try:
		#def onBoardCicdApp(self, securityToken, jiraIssueId, appId, appName, appDesc, opco, region, dbTechnology, deployEnvOrder, env, hostName, dbInstance, connString, dbSchemas, ownerIdList, notificationDL, userId):
		myResult = repo.onBoardCicdApp(mySecToken, myIssueId, myAppId, myAppName, myAppDesc, myOpco, myRegion, myDBTechnology, myDeployEnvOrder, myEnv, myHostName, myDbInstance, myConnectStr, mySchemas, myOwnerIdList, [myNotifyEmail], myUserId)
		print('on boarding app result >>>', myResult)
	except Exception as error:
		print("error while onboarding >>>", error)
		raise error

	print(" <<<on boarding completed >>>")

	#myCICDAppId = myResult["appId"]
	print('performing approval for app [{app}] by user [{user}]'.format(app = str(myAppId), user = myUserId))

	try:
		#approveAppEnv(self, securityToken, jiraIssueId, appId, env, approverId)
		#myResult = repo.approveAppEnv(mySecToken, myIssueId, myAppId, myEnv, myUserId)
		myResult = repo.approveChanges(mySecToken, myIssueId, myAppId, myUserId)
	except Exception as error:
		print('error >> ', error)
		raise error

	print('approval result >>>', myResult)
	print(" <<< completed >>>")

	print('retrieving pending reason for app >>> {app}'.format(app = myAppId))
	myPendingReason = repo.getAppDetailedStatus(mySecToken, myAppId)
	print('reason >>', myPendingReason)
	print(" <<< completed >>>")

	print('retrieving all (pending) app for user >>>', myUserId)
	#getMyAppList(self, securityToken, opco, region, dbTechnology, userId, appStatus = None)
	myPendingApp = repo.getMyAppList(mySecToken, myOpco, myRegion, myDBTechnology, myUserId, repo.Globals.STATUS_PENDING)
	print('pending app >>', myPendingApp)

	print('retrieving all app (approved) for user >>>', myUserId)
	# getMyAppList(self, securityToken, opco, region, dbTechnology, userId, appStatus = None)	
	myApprovedApp = repo.getMyAppList(mySecToken, myOpco, myRegion, myDBTechnology, myUserId)
	print('all app list >>', myApprovedApp)

	#print('populating valid approver list')
	#myResult = repo.populateValidApprover(mySecToken, myUserId)
	#print('result >>>', str(myResult))

	print('retrieving all approval userid ')
	myResult = repo.getAppApproverIds(mySecToken, myDBTechnology)
	print('all approver id >>>', str(myResult))

	print('retrieving all app for approval for userid >>> {user} '.format(user = myUserId))
	#getMyAppForApproval(self, securityToken, opco, region, dbTechnology, userId
	myResult = repo.getMyAppForApproval(mySecToken, myOpco, myRegion, myDBTechnology, myUserId)
	print('result >>>', str(myResult))

	#myAppName = 'ADWRAP'
	print("retrieving dbaas application detail for {app}".format(app = myAppName))
	# dbaasGetAppInfo(self, securityToken, opco, region, dbTechnology, appId)
	myResult = repo.dbaasGetAppInfo(mySecToken, myOpco, myRegion, myDBTechnology, myAppId)
	print('dbaas app detail >>', myResult)

	print("retrieving dbaas common schema (available in all env) for {app}".format(app = myAppName))
	#dbaasGetOraDBCommonSchemas(self, securityToken, opco, region, dbTechnology, appId)
	myResult = repo.dbaasGetOraDBCommonSchemas(mySecToken, myOpco, myRegion, myDBTechnology, myAppId)
	print('common schemas >>', myResult)

	print("retrieving dbaas common schema (available in all env) for {app}".format(app = myAppName))
	#dbaasGetOraDBCommonSchemas(self, securityToken, opco, region, dbTechnology, appId)
	myResult = repo.dbaasGetOraDBCommonSchemas(mySecToken, 'MARSH', 'nam', 'Oracle', 181)
	print('common schemas >>', myResult)

	"""
	## app status validation
	repo._Repository__validateAppStatus(mySecToken, 181, 'u1167965')
	repo.pg.commit(mySecToken, repo.PG_CONN)
	repo.refreshAppDeployApprover(mySecToken, myUserId)
	"""

	# deployment method testing
	# deployment (new deployment)
	"""
	myAppId = 999
	myUserId = "u1167965"
	myDeployId = "deploy_test"
	#print(f"creating new deployment for app {myAppId} as requested by {myUserId}")
	#myResult = repo.createNewDeployment(mySecToken, myDeployId, appId, userId)
	#print('new deployment result >>> ', myResult)

	print(f"retrieving active deploy control for >>> {myDeployId}")
	myActiveDeployCtrlId = repo.getActiveDeployCtrlId(mySecToken,myDeployId)
	print("found active deploy control id >>> {active}".format(active = myActiveDeployCtrlId))

	print(f"retrieveing deploy control file stats for >>> {myActiveDeployCtrlId}")
	myDeployCtrlData = repo.getDeployCtrlFileStats(mySecToken, myActiveDeployCtrlId)

	print(f"deploy ctrl file stats >>> {myDeployCtrlData}")

	print(f"checking if there are any changes in deployment files of {myDeployId}...")
	print("results >>> ", repo.isDeployFilesChanged(mySecToken, myDeployId))
	"""