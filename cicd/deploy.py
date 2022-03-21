from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.security import Security
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.common.jira_util import JiraUtility
from com.mmc.cicd.cicd_repo_pg import Repository
from com.mmc.cicd.deploy_files_parser import Parser
from com.mmc.cicd.cicd_globals import CICDGlobals
from com.mmc.database.oracle_core import OracleCore

import logging, logging.config, sys

import os, json

class Deploy(object, metaclass=Singleton):
	"""
	We need deploy.readme file for each deployment with following contents
	INIT
		backup_stru : <objects seperated by comma>,
		backup_data : <data objects seperated by comma>,
		deploy_files : <list of files with exec order> for e.g.: "1 change_struct.sql", "2 load_data.sql", "3 change data.sql" 
	JSON 
		{
			"backup" : [<mandatory,array; list of all the objects which need to be backed up>]
			"deployFiles" : [{"file" : <nadatory,str; file_name>, "execOrder" : <mandatory,int; execution order>}]
		}
	YAML
		(future)

	"""
	def __init__(self, securityToken):
		try:
			self.sec = Security()
			self.util = Utility()
			self.infra = Infrastructure()
			self.Globals = CICDGlobals()

			self.SECURITY_TOKEN=securityToken
			#self.ENVIRONMENT = self.util.getACopy(self.infra.environment)

			self.sec.validateSecToken(securityToken)

			self.repo = Repository(securityToken)
			self.ora = OracleCore(securityToken)

			self.LOGGER = logging.getLogger(__name__)
			self.LOGGER.info("instantiating Oracle core class")

			if not self.util.isDirExists(self.Globals.DEPLOY_DOWNLOAD_LOC):
				self.util.createDir(self.Globals.DEPLOY_DOWNLOAD_LOC)

			self.parser = Parser(securityToken)
			self.JiraUtil = JiraUtility(securityToken)

			self.DEPLOY_VAR = self.util.getACopy(self.infra.environment["cicd"]["deploy"])
			self.INFRA_BOOT_VAR = self.util.getACopy(self.infra.environment["boot"])

			del self.infra

		except Exception as error:
			raise ValueError(f"An error {error} occurred instantiating object Deploy")

	#def initDeploy(self, deployId, appId, userId, deployFiles, deployOrder, source):

	def __getDeployAdminUser(self, securityToken, dbTechnology, env):
		"""
		returns deploy admin user and its passwowrd for a given db technology and its environment
		"""
		try:
			self.sec.validateSecToken(securityToken)
			
			if not(env.lower() == "prod"):
			   env = "non-prod"

			if dbTechnology.lower() not in self.INFRA_BOOT_VAR["deploy"]:
				raise ValueError(f"Invalid db technology {dbTechnology} !!")

			return {
				"userId" : self.INFRA_BOOT_VAR["deploy"][dbTechnology][env]["user"], 
				"userEncPass" : self.INFRA_BOOT_VAR["deploy"][dbTechnology][env]["userEncPass"]
			}

		except Exception as error:
			raise ValueError(f"An error occurred {error} while retrieving deployment credential !!")

	def createNewDeployment(self, securityToken, jiraIssueId, deployId, appId, userId, deploySource, deploySrcData):

		"""
		Initialize the deployment. This method to be called first time when submitting the deployment. Following steps are performed
			1. Vaidation
				User is allowed to submit the deployment
				Ensure target database in not in blackout/scheduled maintenance
			2. validate Source of deployment files
			if deploySource = 'jira'
				a. ensure deploy_readme.json file is present 
				b. download deploy_readme.json file
				c. download all deployment files stated in deploy_readme.json
			if deploySource = 'bitbucket'
				a. clone url to temporary place
			3. ensure all deployment files are present 
			3. Parse Sql file
			4. Persist tasks information along with the status
			5. Update status of deploy id in Jira
			6. Create log file of validation
		Arguments:
			deployId : Deployment Id (Jira issue id)
			appID: Aplication id to which deployment would be performed
			userId: User id requesting the deployment
			deploySource: source of deployment (jira/bitbucket)
			deploySrcData: bitbucket url or Jira issue id
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', str(deployId), ',', str(appId), ',', userId, ',', deploySource, ',', deploySrcData])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# validating arguments
			if not (securityToken, deployId, appId, userId, deploySource, deploySrcData):
				raise ValueError("missing mandatory arguments, expecting valid (securityToken/deployid/appid/submittedBy/deploySource/deploySrcData), got >>> {got}".\
					format(got = "".join([securityToken, ",", deployId, ",", str(appId), ",", userId, ",", deploySource, ",", deploySrcData])))

			if deploySource not in [self.Globals.DEPLOY_SOURCE_JIRA, self.Globals.DEPLOY_SOURCE_BITBUCKET]:
				raise ValueError("deploy source (soruce arg) must be in [{validSource}], got > {got}".\
					format(validSource = "".join([self.Globals.DEPLOY_SOURCE_JIRA, ",", self.Globals.DEPLOY_SOURCE_BITBUCKET]),\
						got = deploySource))

			if self.repo.isJiraInUseForDeploy(securityToken, jiraIssueId):
				raise ValueError(f"Jira issue id {jiraIssueId} is already in use with another deployment !!")

			if self.repo.isDeploymentExists(securityToken, deployId):
				raise ValueError(f"Deployment id {dployId} already exists !!")


			self.JiraUtil.addAComment(securityToken, jiraIssueId, f"User {userId} requested creating/validating new deploymnet in repository, proceeding")

			myDownloadDir = self.util.buildPath(self.Globals.DEPLOY_DOWNLOAD_LOC, deployId)
			myDownloadArchiveDir = self.util.buildPath(myDownloadDir, '_', self.util.getCurDateTimeForDir())

			myAppDetail = self.repo.getAnAppDetails(securityToken, appId)

			myDownloadDeployFileExtn = self.Globals.CICD_INFRA_DEPLOY_VAR[myAppDetail["technology"].lower()]["deployFileExtn"]

			myResult = self.__downloadDeployFiles(securityToken, jiraIssueId, deployId, appId, deploySource, deploySrcData, myDownloadDir, userId)

			if myResult["status"] == self.Globals.unsuccess:
				return myResult

			# need 2 validation (argument and deployment files) also need to check if same jira has already been used for other deployment id
			myDBResult = self.repo.validateNewDeployment(securityToken, deployId, appId, userId)

			if myDBResult == self.Globals.unsuccess:				
				self.JiraUtil.addAComment(securityToken, jiraIssueId, myDBResult["message"])
				return myDBResult

			myDBResult = self.repo.createNewDeployment(securityToken, jiraIssueId, deployId, deploySource, deploySrcData, appId, userId)
		
			#self.JiraUtil.addAComment(securityToken, jiraIssueId, myDBResult["message"])

			return myDBResult

		except Exception as error:
			self.LOGGER.error("An error occurred while creating new deployment >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __downloadDeployFiles(self, securityToken, jiraIssueId, deployId, appId, deploySource, deploySrcData, downloadPath, userId):
		"""
		Description: Download all deployment files from source (Jira or bitbucket)
		Arguments:
			deployId : deployment id
			deploySource: source of deployment files (jira/bitbucket)
			deploySrcData: jira id or bitbucket url
			userId: user submitted this request
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', str(jiraIssueId), ',', str(deployId), ',', str(appId), ',', deploySource, ',', deploySrcData, ',', downloadPath, ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# variables
			myAppDetail = self.repo.getAnAppDetails(securityToken, appId)

			#myJira = JiraUtility(securityToken, jiraIssueId)

			#downloadPath = self.util.buildPath(self.Globals.DEPLOY_DOWNLOAD_LOC, deployId)
			myDownloadArchiveDir = self.util.buildPath(downloadPath, "".join(["archive_",self.util.getCurDateTimeForDir()]))

			print('dir download/archive', downloadPath, myDownloadArchiveDir)

			# create download dir, if directory has any existing files move them to archive directory
			self.util.createDir(downloadPath)

			self.util.archiveFolder(downloadPath, myDownloadArchiveDir)

			myDownloadDeployFileExtn = self.Globals.CICD_INFRA_DEPLOY_VAR[myAppDetail["technology"].lower()]["deployFileExtn"]

			# downloading all deployment files from source
			self.JiraUtil.addAComment(securityToken, jiraIssueId, f'downloading deployment files extn {myDownloadDeployFileExtn} from {deploySource}')
			
			if deploySource.lower() == self.Globals.DEPLOY_SOURCE_JIRA.lower():
				self.JiraUtil.downloadAttachments(securityToken, jiraIssueId, downloadPath, myDownloadDeployFileExtn)
			else:
				self.util.cloneGit(deploySrcData, self.Globals.BB_ADMIN_USER, sec._Security__decryptText(self.Globals.BB_ADMIN_USER_ENCPASS), downloadPath)

			myDownloadedFiles = self.util.getAllFilesInAFolder(downloadPath)

			# checking if we downloaded any files
			myTotalDownloadFiles = self.util.getTotalFilesInAFolder(downloadPath)

			if len(myDownloadedFiles) == 0:
				myErrorMsg = f"there are not files available to be downloaded from {deploySource}"
				self.JiraUtil.addAComment(securityToken, jiraIssueId, myErrorMsg)
				return self.util.buildResponse(self.Globals.unsuccess, myErrorMsg)
				#raise ValueError(f"there are no files ({myDownloadDeployFileExtn}) available to be deownloaded from {deploySource}")

			# download is completed, will unzip any zip file found in download location,
			myAllZipFiles = self.util.getFilesByExtn(downloadPath,[".zip"])
			
			for file in myAllZipFiles:
				self.JiraUtil.addAComment(securityToken, jiraIssueId, f"found compressed file {file}, extracting")
				self.util.unzipFile(self.util.buildPath(downloadPath,self.util.getFileName(file)), downloadPath)

			myAllFiles = self.util.getAllFilesInAFolder(downloadPath)

			self.JiraUtil.addAComment(securityToken, jiraIssueId, f"""
				Download summary >>>
					Files downloaded (total {myTotalDownloadFiles}) :
						{myDownloadedFiles} 
					Compressed files extracted :
						{myAllZipFiles}
					Files available for processing :
					 	{myAllFiles}
			""")

			return self.util.buildResponse(self.Globals.success, self.Globals.success)

		except Exception as error:
			self.LOGGER.error("an error occurred while initializing deployment >>> {error}".format(error = str(error)), exc_info = True)
			return self.util.buildResponse(self.Globals.unsuccess, str(error))
			#raise error

	def validateDeployMetadatInNexus(self, securityToken, deployId, userId):
		"""
		performs validation of deployment metadata from Nexus to CICD repository
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".format(args = "".join([securityToken, ',', deployId, ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# retrieve the deployment json file from nexus
			myNexusUrl = self.ENVIRONMENT["boot"]["nexusUrl"]
			myNexusUser = self.ENVIRONMENT["boot"]["nexusUser"]
			myNexusUserEncPass = self.ENVIRONMENT["boot"]["nexusUserEncPass"]
			myNexusUserPass = self.sec._Security__decryptText(myNexusUserEncPass)

			myDeployTasksRaw = self.util.downloadFileFromUrl(myNexusUrl, myNexusFile, myNexusUser, myNexusUserPass)

			#myPullMetadata = myDeployTasksRaw.headers
			self.LOGGER.info(f"pull task metadata (nexus) >>> {myPullMetadata}")

			#myDeployTasks = self.util.convStrToDict(myDeployTasksRaw.json()); we would not need this as this is valid json already
			myDeployTasks = myDeployTasksRaw.json()

			# we need to pull this deployment task from repository

		except Exception as error:
			self.LOGGER.error("an error occurred while initializing deployment >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def reprocessDeployFiles(self, securityToken, jiraIssueId, deployId, deploySource, deploySourceData, userId):
		"""
		Reprocess deployment files
		"""

		try:
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', jiraIssueId, ',', deployId, ',', deploySource, ',', deploySourceData, ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			# retrieving deployment data
			myDeployData = self.repo.getDeployData(securityToken, deployId)

			if not myDeployData:
				raise ValueError(f"Invalid deployment id {deployId}")

			if not myDeployData["deploy_file_location"]:
				raise ValueError("data corruption: deploy file location is empty in repository !!")

			if not(myDeployData["status"].split(".")[0] == self.Globals.validation):
				self.JiraUtil.addAComment(securityToken, jiraIssueId, f"Revalidation/Reprocessing deployment file is not allowed, deployment {deployId} is not in validation state !!")
				raise ValueError(f"Revalidation/Reprocessing deployment file is not allowed, deployment {deployId} is not in validation state !!")

			if myDeployData["validation_attempts"] >= self.Globals.MAX_DEPLOY_REVALIDATION:
				self.JiraUtil.addAComment(securityToken, jiraIssueId, f"Maximum deployment revalidation threshold {self.Globals.MAX_DEPLOY_REVALIDATION} reached, further revalidation is prohibited !!")
				raise ValueError(f"Maximum deployment revalidation threshold {self.Globals.MAX_DEPLOY_REVALIDATION} reached, further revalidation is prohibited !!")

			self.JiraUtil.addAComment(securityToken, jiraIssueId, f"User {userId} requested revalidaing/reprocessing deployment files, proceeding")

			# update the deploy data source in repository from argument
			#def updDeploySource(self, securityToken, deployId, deplySource, deploySourceData, userId)
			myDBResult = self.repo.updDeploySource(securityToken, deployId, deploySource, deploySourceData, userId)
			
			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"an error {myDBResult['message']} occurred while updating deploy source for {deployId}")

			# download the deployment files
			#__downloadDeployFiles(self, securityToken, jiraIssueId, deployId, appId, deploySource, deploySrcData, downloadPath, userId)
			myDBResult = self.__downloadDeployFiles(securityToken, jiraIssueId, deployId, myDeployData["app_id"], deploySource, deploySourceData, myDeployData["deploy_file_location"], userId)

			# commetnting, this validation is in repo.reprocessDeployFiles
			#if not (myDeployData["status"].split(".")[0] == self.Globals.validation):
			#	raise ValueError("Deployment {id} must be in validation state for revalidation/reprocess, current status is >>> {status}".format(id = deployId, status = myDeployData["status"]))

			#repo.reprocessDeployFiles(self, securityToken, jiraIssueId, deployId, appId, deployFileLocation, userId)
			try:
				myDBResult = self.repo.reprocessDeployFiles(securityToken, jiraIssueId, deployId, myDeployData["app_id"], myDeployData["deploy_file_location"], userId)

				if myDBResult["status"] == self.Globals.unsuccess:
					raise ValueError(myDBResult["message"])

				return myDBResult

			except Exception as error:
				# error while reprocessing deployment files, update the status to deployment with error message
				#def updDeployStatus(self, securityToken, deployId, status, comments = None)
				myValidationStatus = self.Globals.DEPLOY_STATUS_MAP[self.Globals.validation][self.Globals.error]
				self.repo.updDeployStatus(securityToken, deployId, myValidationStatus, str(error))
				self.repo.pg.commit(securityToken, self.repo.PG_CONN)
				raise error

		except Exception as error:
			self.LOGGER.error("an error occurred while reprocessing deployment {deployId} >>> {error}".\
				format(deployId = deployId, error = str(error)), exc_info = True)
			raise error

	def cancelDeployment(self, securityToken, jiraIssueId, deployId, userId):
		"""
		Cancel a deployment which is not yet started (still in validation phase)
		"""

		try:
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', jiraIssueId, ',', deployId, ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			# retrieving deployment data
			myDeployData = self.repo.getDeployData(securityToken, deployId)

			if not myDeployData:
				raise ValueError(f"Invalid deployment id {deployId}")

			if not(myDeployData["status"].split(".")[0] == self.Globals.validation):
				self.JiraUtil.addAComment(securityToken, jiraIssueId, f"Cancelling deployment file is not allowed, deployment {deployId} is not in validation state !!")
				raise ValueError(f"Cancelling deployment file is not allowed, deployment {deployId} is not in validation state !!")

			if self.repo.getDeploymentCtrlStatus(securityToken, myDeployData["deploy_ctrl_id"]) == self.Globals.STATUS_INACTIVE:
				raise ValueError(f"Expecting deploy control {myDeployData['deploy_ctrl_id']} status 'active' got {self.Globals.STATUS_INACTIVE} !! ")

			self.JiraUtil.addAComment(securityToken, jiraIssueId, f"User {userId} requested cancelling deployment, proceeding")

			# updating status - deploy
			myDeployStatus = self.Globals.DEPLOY_STATUS_MAP[self.Globals.validation][self.Globals.cancelled]

			#myDBResult = self.repo.updDeployStatus(securityToken, deployId, self.Globals.DEPLOY_STATUS_CANCELLED, f'user {userId} cancelled this deployment')
			myDBResult = self.repo.updDeployStatus(securityToken, deployId, myDeployStatus, f'user {userId} cancelled this deployment')

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			# updating status - deploy_ctrl
			myDBResult = self.repo.updDeployCtrlStatus(securityToken, myDeployData["deploy_ctrl_id"], self.Globals.STATUS_CANCELLED, f'user {userId} cancelled this deployment')

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			# updating status - deploy_files
			myDBResult = self.repo.updDeployFileStatusByCtrl(securityToken, myDeployData["deploy_ctrl_id"], self.Globals.STATUS_CANCELLED, f'user {userId} cancelled this deployment')

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			# updating deploy ctrl status
			myDBResult = self.repo.updDeployTaskStatusByCtrl(securityToken, myDeployData["deploy_ctrl_id"], self.Globals.STATUS_CANCELLED, f'user {userId} cancelled this deployment')

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(myDBResult["message"])

			self.repo.newEventLog(\
				securityToken, \
				deployId, 'deploy', \
				myDeployData["app_id"], 'app', \
				userId, 'cancel.deploy', \
				f'cancelling deployment as requested by user {userId}'\
			)

			self.JiraUtil.addAComment(securityToken, jiraIssueId, f"Deployment is cancelled, no further action is allowed")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred while canelling deployment >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def performDeployment(self, securityToken, jiraIssueId, deployId, appEnvId, userId, extRefDocId = None, when = None):
		"""
		Perform the deployment (creates deployment attempt and execute deployment attempt)
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', jiraIssueId, ',', deployId, ',', str(appEnvId), ',', userId, ',', str(extRefDocId), ',', str(when)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)
			
			# checking if deployment is ready to be deployed
			#myDeployData = self.repo.getDeployData(securityToken, deployId)

			if not self.repo.isDeploymentExists(securityToken, deployId):
				raise ValueError(f"Invalid deployment id {deployId}, does not exists !!")
			
			if not self.repo.isAppEnvIdExists(securityToken, appEnvId):
				raise ValueError(f"Invalid App env id {appEnvId}, does not exists !!")

			# checking if this env is ready for deployment
			# cehcking if deploy env status is ready for deployment (status must not be successful deploy.Success)
			myDeployEnvData = self.repo.getDeployEnvData(securityToken, deployId, appEnvId)

			if myDeployEnvData and myDeployEnvData["status"] == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS:
				self.JiraUtil.addAComment(securityToken, jiraIssueId, f"Deployment id {deployId} in env id {appEnvId} is already successfully deployed !!")
				raise ValueError(f"Deployment id {deployId} in env id {appEnvId} is already successfully deployed !!")

			# find deploy env order for this app
			myDeployData = self.repo.getDeployData(securityToken, deployId)
			myAppDetails = self.repo.getAnAppDetails(securityToken, myDeployData["app_id"])
			myAppEnvData = self.repo.getAnAppEnvById(securityToken, appEnvId)

			# validating deplyment env order
			myResult = self.repo.validateDeployEnvOrder(securityToken, deployId, myAppEnvData["env"].lower())
			if myResult["status"] == self.Globals.unsuccess:
				self.JiraUtil.addAComment(securityToken, jiraIssueId, myResult["message"])
				raise ValueError(myResult["message"])

			"""
			commenting as below code is replaced by above code
			# checking if deploy env order is strictly followed

			# finding the previous environment from deployment env order to check if deployment is performded in all previous environment 
			myDeployEnvOrder = myAppDetails["deploy_env_order"]
			myPassedEnv = myAppEnvData["env"].strip().lower()

			# checking if env is in deployment env order
			if not myPassedEnv in myDeployEnvOrder:
				raise ValueError("Invalid envo=ironment {myPassedEnv} is not a valid environment (env not in depployment env order) !!!")

			# retrieving previous environment
			myPreviousEnvList = myDeployEnvOrder[:myDeployEnvOrder.index(myPassedEnv)]

			# found previous environment list, checking if deployment is performed in these environments
			for env in myPreviousEnvList:
				# checking if deployment is perfored in previous environment
				myAppEnvId = self.repo.getAppEnvId(securityToken, myDeployData["app_id"], env)
				if not self.repo.isDeployEnvExists(securityToken, deployId, myAppEnvId):
					myErrorMsg = f"Deployment {deployId} must be deployed in {env} before deploying in {myPassedEnv} !!! "
					self.JiraUtil.addAComment(securityToken, jiraIssueId, myErrorMsg)
					raise ValueError(myErrorMsg)

				# checking if previous deployment was successfull and approved
				myResult = self.repo.getDeployEnvData(securityToken, deployId, myAppEnvId)

				self.LOGGER.debug(f"deploy {deployId} env {myAppEnvId} data >>> {myResult}")

				if myResult["status"] !=  self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS_APPROVED:
					myErrorMsg = f"Deployment must be successfully deployed in {env} and validated before it can be deployed in  {myAppEnvData['env']} !!"
					self.JiraUtil.addAComment(securityToken, jiraIssueId, myErrorMsg)
					raise ValueError(myErrorMsg)
				# checking if previous deployment is successfully approved
				#if myResult["status"] != self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS_APPROVED:
				#	myErrorMsg = f"Deployment must be successfully deployed in {env} and validated/approved before it can be deployed in  {myAppEnvData['env']} !!"
				#	self.JiraUtil.addAComment(securityToken, jiraIssueId, myErrorMsg)
				#	raise ValueError(myErrorMsg)
			"""
			# checking if this is prod, if it is we would need

			myDeployEnv = self.repo.getAnAppEnvById(securityToken, appEnvId)
			
			if myDeployEnv["env"].lower() == self.Globals.ENV_PROD.lower() and not extRefDocId:
				myErrorMsg = "External reference doc argument is mandatory for deployment in Prod environment !!"
				self.JiraUtil.addAComment(securityToken, jiraIssueId, myErrorMsg)
				raise ValueError(myErrorMsg)

			"""
			if myDeployData["status"] != self.Globals.DEPLOY_STATUS_VALIDATION_SUCCESS:
				raise ValueError(f"Invalid deployment status, expecting {self.Globals.DEPLOY_STATUS_VALIDATION_SUCCESS}, got myDeployData['status']")

			# need to verify if this user is allowed to perfom deployment of this application in this environment
			if not self.repo.isValidUserForDeploy(securityToken, appId, env, userId):
				raise ValueError("user {userId} is not allowed to execute this deployment !!")
			"""
			if myDeployEnv["env"].lower() != self.Globals.ENV_PROD.lower():
				myDBResult = self.repo.createDeployAttempt(securityToken, deployId, appEnvId, userId, jiraIssueId)
			else:
				myDBResult = self.repo.createDeployAttempt(securityToken, deployId, appEnvId, userId, extRefDocId)

			""" (not needed, will update start time when new env is created)
			# checking ig this is 1st attempt, if yes will update deploy env start time
			myTotalDeployEnvAttempt = self.repo.getTotalDeployAttempt(securityToken, deployId, appEnvId)
			if myTotalDeployEnvAttempt == 1:
				self.repo.updDeployEnvStartTime(securityToken, deployId, appEnvId)
			"""
			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueEror(myDBResult["message"])

			myAttemptId = myDBResult["data"]["attemptId"]
			self.JiraUtil.addAComment(securityToken, jiraIssueId, f"New attempt id {myAttemptId} is created for this deployment")

			# commiting creating new attempt txn 
			#self.repo.pg.commit(securityToken, self.repo.PG_CONN) ---> commit is already performed in repository class

			# performing a deployment attempt
			myDBResult = self.executeDeployAttempt(securityToken, jiraIssueId, deployId, appEnvId, myAttemptId, userId)

			myAttemptStatus = self.repo.getDeployAttemptStatus(securityToken, myAttemptId)

			if myAttemptStatus == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS:
				myDBResult = self.repo.newRequestForApproval(securityToken, jiraIssueId, myAttemptId, 'deploy.env.attempt','execute.env.deployment', userId)
				myRequestId = myDBResult["data"][0]["request_id"]
				myResponseData = {"status" : myAttemptStatus, "attemptId" : myAttemptId, "requestId" : myRequestId}
				myResponse = self.util.buildResponse(self.Globals.success, self.Globals.success, myResponseData)
			else:
				myResponseData = {"status" : myAttemptStatus, "attemptId" : myAttemptId}
				myResponse = self.util.buildResponse(self.Globals.unsuccess, f'Attempt {myAttemptId} executed successfully but deployment status is unsuccessful !!!', myResponseData)

			# commiting request
			self.repo.pg.commit(securityToken, self.repo.PG_CONN)

			# adding deployment output to jira
			myAttemptOutputLogFile = self.generateDeployAttemptLog(securityToken, deployId, appEnvId, myAttemptId)
			self.JiraUtil.addAttachment(securityToken, jiraIssueId, myAttemptOutputLogFile)
			self.JiraUtil.addAComment(securityToken, jiraIssueId, "Pls review deployment attempt output file {file}".format(file = self.util.getFileName(myAttemptOutputLogFile)))

			return myResponse

		except Exception as error:
			self.LOGGER.error("an error occurred while performing deployment >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def executeDeployAttempt(self, securityToken, jiraIssueId, deployId, appEnvId, attemptId, userId):
		"""
		Executes deployment, deployment attempt
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', jiraIssueId, ',', deployId, ',', str(appEnvId), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			"""
			if not self.repo.isDeployEnvAttemptExists(securityToken, deployId, appEnvId, attemptId):
				raise ValueError(f"Invalid deployment {deployId} env {appEnvId} attempt {attemptId} !!")
			"""

			# validation
			self.repo.validateDeployEnvAttempt(securityToken, deployId, appEnvId,attemptId, userId)

			self.repo.markAttemptInProg4Deploy(securityToken, deployId, appEnvId, attemptId, userId)

			myAttemptStatus = self.repo.getDeployAttemptStatus(securityToken, attemptId)
			
			if myAttemptStatus != self.Globals.DEPLOY_STATUS_DEPLOY_INPROGRESS:
				myErrorMsg = f"in consistent attempt status, expecting '{self.Globals.DEPLOY_STATUS_DEPLOY_INPROGRESS}', got '{myAttemptStatus}' !!"
				self.JiraUtil.addAComment(securityToken, jiraIssueId, myErrorMsg)
				raise ValueError(myErrorMsg)

			myDeployData = self.repo.getDeployData(securityToken, deployId)

			if myDeployData["technology"].lower() == self.Globals.TECHNOLOGY_ORACLE.lower():
				#myDeployExecResult = self.__execOracleDeployAttempt(securityToken, jiraIssueId, deployId, appEnvId, attemptId, userId)
				self.JiraUtil.addAComment(securityToken, jiraIssueId, f"This deployment is for database technology {myDeployData['technology']}")
				self.__execOracleDeployAttempt(securityToken, jiraIssueId, deployId, appEnvId, attemptId, userId)

			self.JiraUtil.addAComment(securityToken, jiraIssueId, f"Validating deployment attempt status")

			self.valDeployEnvAttemptStatus(securityToken, jiraIssueId, deployId, appEnvId, attemptId, userId)

			self.repo.pg.commit(securityToken, self.repo.PG_CONN)

			# we need to retrieve the status of this deployment attempt
			myDeployAttemptStatus = self.repo.getDeployAttemptStatus(securityToken, attemptId)
			
			if myDeployAttemptStatus == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS:
				return self.util.buildResponse(self.Globals.success, self.Globals.success)
			else:
				return self.util.buildResponse(self.Globals.unsuccess, self.Globals.unsuccess)

		except Exception as error:
			self.LOGGER.error("an error occurred while performing deployment >>> {error}".format(error = str(error)), exc_info = True)
			self.repo.pg.rollback(securityToken, self.repo.PG_CONN)
			raise error

	def valDeployEnvAttemptStatus(self, securityToken, jiraIssueId, deployId, appEnvId, attemptId, userId):
		"""
		Validates the deployment env attempt status
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', jiraIssueId, ',', deployId, ',', str(appEnvId), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not self.repo.isDeployEnvAttemptExists(securityToken, deployId, appEnvId, attemptId):
				raise ValueError(f"Invalid deployment {deployId} env {appEnvId} attempt {attemptId} !!")

			myDistinctDeployEnvAttemptTaskStatus = self.repo.getUniqueEnvAttemptTaskStatus(securityToken, deployId, appEnvId, attemptId)

			myDeployStatus = self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS

			for status in myDistinctDeployEnvAttemptTaskStatus:
				if status in [self.Globals.DEPLOY_STATUS_DEPLOY_UNSUCCESS, self.Globals.DEPLOY_STATUS_DEPLOY_PENDING, self.Globals.DEPLOY_STATUS_DEPLOY_ERROR]:
					myDeployStatus = self.Globals.DEPLOY_STATUS_DEPLOY_UNSUCCESS
					break

			"""
			if (len(myDistinctDeployEnvAttemptTaskStatus) > 1) :
				myDeployStatus = self.Globals.DEPLOY_STATUS_DEPLOY_UNSUCCESS
				## deploy attempt was unsuccessful, update the status as unsuccessful

			if len(myDistinctDeployEnvAttemptTaskStatus) == 1:
				#if myDistinctDeployEnvAttemptTaskStatus[0] == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS:
				# deploy attempt was unsuccessful, update the status as unsuccessful
				myDeployStatus = myDistinctDeployEnvAttemptTaskStatus[0]["status"]
			"""

			# update deploy_envs, deploy_attempt status metadata
			myDBResult = self.repo.updDeployEnvStatus(securityToken, deployId, appEnvId, myDeployStatus, userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"error while updating deployment {deployId} env {appEnvId} status to {myDeployStatus}")

			myDBResult = self.repo.updDeployEnvAttemptStatus(securityToken, deployId, appEnvId, attemptId, myDeployStatus, userId)

			if myDBResult["status"] == self.Globals.unsuccess:
				raise ValueError(f"error while updating deployment {deployId} env {appEnvId} attempt {attemptId} status to {myDeployStatus}")

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred while performing deployment >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __execOracleDeployAttempt(self, securityToken, jiraIssueId, deployId, appEnvId, attemptId, userId):
		"""
		Executes this attempt for Oracle deployment
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', jiraIssueId, ',', deployId, ',', str(appEnvId), ',', userId, ',', str(attemptId), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# retrieve env information

			myAppEnvData = self.repo.getAnAppEnvById(securityToken, appEnvId)

			if not myAppEnvData:
				raise ValueError(f"application env {appEnvId} is missing !!")

			# need deployment user for establishing a connection to target database
			myDeployAdminConfig = self.__getDeployAdminUser(securityToken, self.Globals.TECHNOLOGY_ORACLE.lower(), myAppEnvData["env"])

			if not myDeployAdminConfig:
				raise ValueError("uanable to retrieve deploy admin user details for Oracle !!")

			myDeployAdminConfig.update({"dsn" : myAppEnvData["conn_string"], "tag" : f"cicd.deploy.python.{myModule}.{deployId}.{userId}"})

			myOraConn = self.ora.newConnection(securityToken, myDeployAdminConfig)

			myAllAttemptTasks = self.repo.getDeployAttemptAllTask(securityToken, attemptId)

			self.JiraUtil.addAComment(securityToken, jiraIssueId, f"Total {len(myAllAttemptTasks)} task(s) found for this attempt")

			myTaskExecStatus = self.Globals.success

			for task in myAllAttemptTasks:
				# get before image of this task
				self.JiraUtil.addAComment(securityToken, jiraIssueId, f"executing task {task['task_id']} - {task['task']}")
				try:

					myResult = self.__execOraTask(securityToken, jiraIssueId, deployId, appEnvId, myOraConn, myAppEnvData["app_id"], attemptId, task, userId)
					
					if myTaskExecStatus == self.Globals.success and myResult["status"] == self.Globals.unsuccess:
						myTaskExecStatus = self.Globals.unsuccess

					# if task execution was unsuccessful and ignore_error is set to N, will stop further execution of tasks
					self.JiraUtil.addAComment(securityToken, jiraIssueId, f"task execution result --> {myResult}")

					if myResult["status"] == self.Globals.unsuccess:
						if task["ignore_error"] == "N":
							self.JiraUtil.addAComment(securityToken, jiraIssueId, "task execution was unsuccessful, Ignore error has been set to 'N', stoping further execution of remaining task !!")
							break
						else:
							self.JiraUtil.addAComment(securityToken, jiraIssueId, "task execution was unsuccessful, Ignore error has been set to 'Y', proceeding execution of remaining task !!")
					else:
						self.JiraUtil.addAComment(securityToken, jiraIssueId, "task execution was successful !!")

				except Exception as error:
					myErrorMsg = "An error occurred while executing task {task} >>> {error}".format(task = "".join(["deploy id : ", deployId, " app env id : ", str(appEnvId), " attempt id : ", str(attemptId), "task id :",str(task["task_id"])]), error = str(error))
					self.LOGGER.error(myErrorMsg, exc_info = True)		
					self.JiraUtil.addAComment(securityToken, jiraIssueId, myErrorMsg)
					if task["ignore_error"] == "N":
						self.JiraUtil.addAComment(securityToken, jiraIssueId, "Ignore error has been set to 'N', stoping further execution of remaining task !!")
						myTaskExecStatus = self.Globals.unsuccess
						break

			# this is Oracle deployment, will make an attempt to 
			if myTaskExecStatus == self.Globals.success:
				return self.util.buildResponse({self.Globals.success, self.Globals.success})
			else:
				return self.util.buildResponse({self.Globals.unsuccess, self.Globals.unsuccess})

		except Exception as error:
			self.LOGGER.error("an error occurred while performing deployment >>> {error}".format(error = str(error)), exc_info = True)
			raise error

	def __getOraBeforeImage(self, securityToken, oraConn, task):
		"""
		Returns before image for a given task
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', str(oraConn), ',', str(task) ])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not(task["task_obj_owner"] and task["task_obj_name"] and task["task_obj_type"]):
				# possible reason is alter session/alter system/create sy object
				return {"imageType" : "None", "image" : "unable to find before image, possible reason >> alter session/alter system/create <sys objects"}

			if task["task_category"].lower() in ["query","exec"]:
				return {"imageType" : "None", "image" : f"N/A (task category is {task['task_category'].lower()})"}

			# checking if this object exists in target database
			# accomodating case senestive in object name

			if not task["task_obj_name"].strip().startswith('"'):
				myObjectName = task["task_obj_name"].upper()
			else:
				myObjectName = task["task_obj_name"]

			if not self.ora.isObjExists(securityToken, oraConn, task["task_obj_owner"], task["task_obj_type"], myObjectName):
				return {"imageType" : "None", "image" : "no image found in database"} 

			if task["task_category"].lower() == "ddl"  and task["task_type"] == "user":
				if task["task_op"].lower().strip() in ["alter session","alter system"]:
					mySourceCode = ""
				else:
					mySourceCode = self.ora.execSysMethod(\
						securityToken, \
						oraConn, \
						"getDDL", \
						{\
							"OWNER" : task["task_obj_owner"], \
							"OBJECT_TYPE" : task["task_obj_type"], \
							"OBJECT_NAME" : task["task_obj_name"] \
						} \
					)

				myBeforeImage = {"imageType" : "sourceCode", "image" : mySourceCode[0]["SOURCE_CODE"]}

			elif task["task_category"].lower() == "dml" and task["task_type"].lower() == "user":
				if task["task_op"].lower() in ["delete","update"]:
					mySqlWhereClause = "1 = 1"
					mySqlSplit = task.replace("\n", "").replace("\t","").lower.split(" where ")
					if len(mySqlSplit) == 2:
						mySqlWhereClause = mySqlSplit[1]

					mySql = "".join([f"SELECT * FROM {task['task_obj_owner']}.{task['tyask_obj_name']} WHERE {mySqlWhereClause}"])
					mySqlResult = self.ora.execSelectSql(securityToken, oraConn, mySql, {})
					myBeforeImageData = mySqlResult["data"]

				elif task["task_op"].lower() == "insert":
					myBeforeImageData = ""

				myBeforeImage = {
					"imageType" : "data", 
					"image" : mySqlResult["data"]
				} 

			elif task["task_category"] == "dcl" and task["task_type"] == "user":
				if task["task_op"].lower() == "revoke":
					
					myGranteeSplit = [elem for elem in task.replace("\n","").replace("\t","").split(" from ") if elem]
					myGrantee = myGranteeSplit[1]

					myGrantedPrivsSplit = [elem for elem in revoke.lower().replace("\n","").replace("\t","").replace("revoke","").split(" from ")[0].split(" on ") if elem]
					myGrantedPrivs = myGrantedPrivsSplit[0]

					myGrantedObj = myGrantedPrivsSplit

					if len(myGrantedPrivsSplit) > 1:
						# we have object privilege
						#@myGRantedPrivsOnObj = myGrantedPrivsSplit[1]
						myGrantImage = "".join(["grant ", myGrantedPrivs, " on ", myGrantedPrivsSplit[1], " to ", myGrantee ])
					else:
						myGrantImage = "".join(["grant ", myGrantedPrivs, " to ", myGrantee ])

					myBeforeImage = {
						"imageType" : "grant", 
						"image" : myGrantImage
					} 
			else:
				myBeforeImage = {"imageType" : "not found", "image" : "".join(["not recorded for category.type >>> ", task["task_category"], ".", task["task_type"]])}

			return myBeforeImage

		except Exception as error:
			self.LOGGER.error("an error occurred while building before image >>> {error}".format(error = str(error)), exc_info = True)
			return {"imageType" : "error", "image" : str(error)} 

	def __getOraAfterImage(self, securityToken, oraConn, task):
		"""
		Returns after image for a given task
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', str(oraConn), ',', str(task)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not(task["task_obj_owner"] and task["task_obj_name"] and task["task_obj_type"]):
				# possible reason is alter session/alter system/create sy object
				return {"imageType" : "None", "image" : "unable to find before image, possible reason >> alter session/alter system/create <sys objects"}

			if task["task_category"].lower() in ["query","exec"]:
				return {"imageType" : "None", "image" : f"N/A (task category is {task['task_category'].lower()})"}

			# checking if this object exists in target database
			# accomodating case senestive in object name
			if not task["task_obj_name"].strip().startswith('"'):
				myObjectName = task["task_obj_name"].upper()
			else:
				myObjectName = task["task_obj_name"]

			if not self.ora.isObjExists(securityToken, oraConn, task["task_obj_owner"], task["task_obj_type"], myObjectName):
				return {"imageType" : "None", "image" : "no image found in database"} 

			if task["task_category"].lower() == "ddl"  and task["task_type"] == "user":
				if task["task_op"].lower().strip() in ["alter session","alter system"]:
					mySourceCode = ""
				else:
					mySourceCode = self.ora.execSysMethod(\
						securityToken, \
						oraConn, \
						"getDDL", \
						{ \
							"OWNER" : task["task_obj_owner"], \
							"OBJECT_TYPE" : task["task_obj_type"], \
							"OBJECT_NAME" : task["task_obj_name"] \
						} \
					)

				myAfterImage = {"imageType" : "sourceCode", "image" : mySourceCode[0]["SOURCE_CODE"]}

			elif task["task_category"].lower() == "dml" and task["task_type"].lower() == "user":
				if task["task_op"].lower() == "update":
					mySqlWhereClause = "1 = 1"
					mySqlSplit = task.replace("\n", "").replace("\t","").lower.split(" where ")
					if len(mySqlSplit) == 2:
						mySqlWhereClause = mySqlSplit[1]

					mySql = "".join([f"SELECT * FROM {task['task_obj_owner']}.{task['tyask_obj_name']} WHERE {mySqlWhereClause}"])
					mySqlResult = self.ora.execSelectSql(securityToken, oraConn, mySql, {})
					myBeforeImageData = mySqlResult["data"]

				elif task["task_op"].lower() == "insert":
					mySqlResult = self.ora.execSelectSql(securityToken, oraConn, task, {})
					myBeforeImageData = mySqlResult["data"]

				myAfterImage = {
					"imageType" : "data", 
					"image" : mySqlResult["data"]
				} 

			elif task["task_category"] == "dcl" and task["task_type"] == "user":
				myAfterImage = {
						"imageType" : task["op"].lower(), 
						"image" : task
					} 

			return myAfterImage

		except Exception as error:
			self.LOGGER.error("an error occurred while building before image >>> {error}".format(error = str(error)), exc_info = True)
			return {"imageType" : "error", "image" : str(error)} 

	def __execOraTask(self, securityToken, jiraIssueId, deployId, appEnvId, oraConn, appId, attemptId, task, userId):
		"""
		Execute given Oracle task
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', jiraIssueId, ',', deployId,  ',', str(appEnvId), ',', str(oraConn), ',', str(appId), ',', str(task), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			"""
			1. execute task
			2. upon success/failure
				update completed_tasks/pending_task/completed_tasks_list/pending_tasks_list in deploy_attempts and deploy_attempt_tasks
			3. update deploy_obj and deploy_obj_history
			4. update app.apps and app.app_envs tot_completed_deploy
			"""

			# Retrieving before image
			myBeforeImage = {}
			myAfterImage = {}
			myResult = ""

			myTaskStartTime = self.util.lambdaGetCurrDateTime()

			myBeforeImage = self.__getOraBeforeImage(securityToken, oraConn, task)
			myTotalRowsAffected = 0
			
			# executing tasks
			try:
				#myResult = {"data" : myData, "stats" : {"elapsed" : myFormattedElapsedTime, "rows" : myTotalRows}}
				myStartTime = self.util.lambdaGetCurrDateTime()
				if task["task_op"] == "proc.compile.invalid.objs":
					# compile invalid objects
					myAllAppSchemas = self.repo.getAnAppDetails(securityToken, appId)
					myResult = {"data" : [], "stats" : {"elapsed" : "", "rows" : 0}}
					#myResult = {"data" : []}
					for schema in myAllAppSchemas["db_schemas"]:
						#calling dbms_utility.compile_schema(schema = > 'schema', compile_all => False)
						#('dbms_utility.compile_schema',keywordParameters={"compile_all":False,"schema":"DBA_ADMIN"})
						#('dbms_utility.compile_schema',                  {'compile_all': False,'schema': 'CICD_DEV'}
						#myCompileResult = self.ora.ora.callproc(securityToken, oraConn, task["task"], [schema.upper(), False, False] )
						with oraConn.cursor() as cursor:
							myCompileResult = cursor.execute(f"begin dbms_utility.compile_schema('{schema.upper()}', FALSE, FALSE ); end; ")
							#myCompileResult = cursor.callproc('dbms_utility.compile_schema', keywordParameters = {'compile_all': False,'schema': repr(schema.upper())})
							#myCompileResult = cursor.callproc('dbms_utility.compile_schema', parameters = [repr(schema.upper()), False, False])

						myResult["data"].append({"schema" : schema,"result" : myCompileResult})
					
					myFormattedElapsedTime = self.util.formatElapsedTime(self.util.getElapsedTimeSecs(myStartTime))
					
					myResult["stats"].update({"elapsed" : myFormattedElapsedTime})

				else:
					if task["task_category"].lower() in ["ddl","dcl","txn","block","exec"]:
						myResult = self.ora.execDDLSql(securityToken, oraConn, task["task"], {})
			
					elif task["task_category"].lower() == "dml":
						myResult = self.ora.execDMLSql(securityToken, oraConn, task["task"], {})

					elif task["task_category"].lower() == "query":
						myResult = self.ora.execSelectSql(securityToken, oraConn, task["task"], {})
				
					myTotalRowsAffected = myResult["stats"]["rows"]

				# setting status as 'success'
				myDeployTaskStatus = self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS
				myTaskExecResult = self.util.buildResponse(self.Globals.success, self.Globals.success)
				myResult.update({"status" : self.Globals.success})
				# building obj history

			except Exception as error:
				self.LOGGER.error(f"an error {error} occurred while executing task {task['task_id']}", exc_info = True)
				# encountered error checking if we can safely ignore this error
				myTaskExecResult = self.util.buildResponse(self.Globals.unsuccess, str(error))

				if task["ignore_error"] == "Y":
					myDeployTaskStatus = self.Globals.DEPLOY_STATUS_DEPLOY_UNSUCCESS_IGNORE_ERROR
				else:
					myDeployTaskStatus = self.Globals.DEPLOY_STATUS_DEPLOY_UNSUCCESS

				myTotalRowsAffected = 0
				myFormattedElapsedTime = self.util.formatElapsedTime(self.util.getElapsedTimeSecs(myStartTime))
				myResult = {"status" : self.Globals.unsuccess, "data" : str(error),"stats" : {"elapsed" : myFormattedElapsedTime, "rows" : myTotalRowsAffected}}

				myAfterImage = self.__getOraAfterImage(securityToken, oraConn, task)
				self.repo.completeTask(securityToken, task["deploy_id"], task["attempt_id"], task["task_id"], self.util.encodeDictData({"status" : self.Globals.error, "data" : str(error)}), self.Globals.DEPLOY_STATUS_DEPLOY_UNSUCCESS, myTaskStartTime, myTotalRowsAffected, myBeforeImage, myAfterImage, userId)

			# get after image of this task
			myAfterImage = self.__getOraAfterImage(securityToken, oraConn, task)

			# completing task (updating task result and status)
			try:
				# populating object history if task execution was successful
				if myResult["status"] == self.Globals.success and task["task_category"] in ["ddl"] and task["task_obj_name"] and task["task_obj_owner"] and task["task_obj_type"]:
					self.__populateObjDashboard(securityToken, deployId, task, myBeforeImage, myAfterImage, appEnvId)

				self.repo.completeTask(securityToken, task["deploy_id"], task["attempt_id"], task["task_id"], self.util.encodeDictData(myResult), myDeployTaskStatus, myTaskStartTime, myTotalRowsAffected, myBeforeImage, myAfterImage, userId)

			except Exception as error:
				raise ValueError(f"An error {error} occurred while completing tasks !!!")

			#return self.util.buildResponse(self.Globals.success,self.Globals.success)
			return myTaskExecResult

		except Exception as error:
			self.LOGGER.error("an error occurred while performing deployment >>> {error}".format(error = str(error)), exc_info = True)
			#return self.util.buildResponse(self.Globals.unsuccess,str(error))
			raise error

	def __createRollbackDoc(self, securityToken, jiraIssueId, oraConn, deployId, appEnvId, userId):
		"""
		Generates rollback document and persists for a given deployment
		"""
		try:
			
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', jiraIssueId, ',', str(oraConn), ',', deployId, ',', str(appEnvId), ',', userId])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			# need to retrieve all successfult taks and to attempts this belongs to

		except Exception as error:
			self.LOGGER.error(f"an error occurred while creating rollback document for deployment {deployId} in env {appEnvId} >>> {error}", exc_info = True)
			raise error

	def generateDeployAttemptLog(self, securityToken, deployId, appEnvId, attemptId):
		"""
		Generates the deployment log file for last attempt of a given deployment and appenv id. Return the deplyment log file along with location
		"""
		try:
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', deployId, ',', str(appEnvId), ',', str(attemptId)])))

			# need all attempts in which the tasks were successful
			"""
			Deployment id: _______________________ 		Environment : ________________________ 	Status: _______________________

			Attempt ID: _______________________ 		Timestamp : ________________________ 	Total Attempts: ___________

			Start Time: ___________________ 			End Time : _______________________  	Duration: ___________

			
			Deployment Summary :
				File: _______________________ 		Tasks: ____________(total tasks)	Status: _____________
			
			Deployment Details :

			Tasks (Detail)
			========================================================================================================================================

			Task id :
			Task :
			Records affected: 			Start Time: 		End Time:		Duration:
			Status:
			========================================================================================================================================
			Tasks 1
			"""
			myDeployEnvData = self.repo.getDeployEnvData(securityToken, deployId, appEnvId)
			myAppEnvData = self.repo.getAnAppEnvById(securityToken, appEnvId)
			myDeployAttemptData = self.repo.getDeployAttemptData(securityToken, attemptId)
			myDeployAttemptTasks = self.repo.getDeployAttemptAllTask(securityToken, attemptId)

			myEnvironmentDetail = "".join([myAppEnvData["env"], "(", str(appEnvId), ") - ", myAppEnvData["host_name"], " : ", myAppEnvData["db_instance"]])

			myDeployReportHeader = self.Globals.deployReportHeader.format(\
				#deployId = deployId, env = myDeployEnvData["env"], deployStatus = myDeployEnvData["status"], \
				deployId = deployId, env = myEnvironmentDetail, dbUri = myAppEnvData["conn_string"], \
				deployStatus = myDeployEnvData["status"], \
				attemptId = myDeployEnvData["attempt_id"], totalAttempts = str(len(myDeployEnvData["attempt_id_list"])), attemptTs = myDeployAttemptData["start_time"],
				requestedBy = myDeployEnvData["submitted_by"], requestedTs = myDeployEnvData["submitted_ts"], \
				startTime = myDeployEnvData["start_time"], endTime = myDeployEnvData["end_time"], duration = myDeployEnvData["duration"])

			#myTaskDetailHeader = self.Globals.deployRepTaskDetailHeader

			if myDeployEnvData["status"] == self.Globals.DEPLOY_STATUS_DEPLOY_SUCCESS:
				myDeployAttemptOutFile = self.util.buildPath(self.Globals.DEPLOY_DOWNLOAD_LOC, "".join(["deploy_output_", deployId, "_", myDeployEnvData["env"], "_success_", str(self.util.getCurDateTimeForDir()),".log"]))
			else:
				myDeployAttemptOutFile = self.util.buildPath(self.Globals.DEPLOY_DOWNLOAD_LOC, "".join(["deploy_output_", deployId, "_", myDeployEnvData["env"], "_",str(attemptId), "_", str(self.util.getCurDateTimeForDir()),".log"]))

			# if file exists, overwriting it
			self.util.write2File(myDeployAttemptOutFile, myDeployReportHeader, "w")

			# attempt details
			self.util.write2File(myDeployAttemptOutFile, self.Globals.deployAttemptDetailHeader)
			
			myAttemptSeq = 0

			for attemptId in myDeployEnvData["attempt_id_list"]:
			
				myAttemptData = self.repo.getDeployAttemptData(securityToken, attemptId)
				myAttemptSeq += 1
				myAttemptMargin = "        "
				myAttemptLine = "".join([myAttemptMargin, str(myAttemptSeq).ljust(3), " | ", str(myAttemptData["start_time"]), " | ", str(myAttemptData["end_time"]), " | ", str(myAttemptData["duration"]).ljust(9), " | ", str(myAttemptData["completed_tasks"]).rjust(4), "/", str(myAttemptData["total_tasks"]).ljust(4), "| ", myAttemptData["status"], "\n"])
	
				self.util.write2File(myDeployAttemptOutFile, myAttemptLine)

			self.util.write2File(myDeployAttemptOutFile, self.Globals.deployAttemptDetailFooter)

			# task details
			self.util.write2File(myDeployAttemptOutFile, self.Globals.deployRepTaskDetailHeader)

			for task in myDeployAttemptTasks:
				print("task >>>", task)
				myTaskDetail = self.Globals.deployRepTaskDetail.format(\
					taskId = str(self.util.getDictKeyValue(task, "task_seq")), task = self.util.getDictKeyValue(task, "task"), \
					result = str(self.util.encodeDictData(self.util.getDictKeyValue(task["result"], "data"), indent = 15)), recordsAffected = self.util.getDictKeyValue(task, "records_affected"), \
					startTime = self.util.getDictKeyValue(task, "start_time"), endTime = self.util.getDictKeyValue(task, "end_time"), duration = str(task["duration"]), \
					status = self.util.getDictKeyValue(task, "status")
				)
				self.util.write2File(myDeployAttemptOutFile, myTaskDetail)
					
			self.util.write2File(myDeployAttemptOutFile, self.Globals.deployRepTaskDetailFooter)

			return myDeployAttemptOutFile

		except Exception as error:
			self.LOGGER.error(f"an error occurred while generating deployment log file for deployment id {deployId}, env {appEnvId} >>> {error}", exc_info = True)
			raise error

	def __populateObjDashboard(self, securityToken, deployId, task, beforeImage, afterImage, appEnvId):
		"""
		Populates Object dasjboard (recording changes happened in deployment)
		"""

		try:
			self.LOGGER.debug("got arguments >>> {args}".\
				format(args = "".join([securityToken, ',', deployId, ',', str(task), ',', str(beforeImage), ',', str(afterImage), ',', str(appEnvId)])))

			myModule = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			myDeployData = self.repo.getDeployData(securityToken, deployId)
			myAppEnvData = self.repo.getAnAppEnvById(securityToken, appEnvId)

			myDeployTechnology = myDeployData["technology"]
			myAppEnv = myAppEnvData["env"]
			myAppId = myAppEnvData["app_id"]
			myAppDBInstance = myAppEnvData["db_instance"]
			myDeployDBSchema = task["task_obj_owner"]
			myDeployObjType = task["task_obj_type"]
			myDeployObjName = task["task_obj_name"]			

			#myObjectId = self.repo.buildDeployObjectId(securityToken, myDeployObjName, myDeployObjType, myDeployDBSchema, str(appEnvId), myAppDBInstance, myDeployTechnology)
			#if not self.repo.isDeployObjExists(securityToken, deployId, myObjectId):
			# creatng or updating deploy object
			#createDeployObject(self, securityToken, deployObjId, deployId, appId, appEnvId, dbInstance, dbTechnology, dbSchema, objType, objName)

			myDBResult = self.repo.createDeployObject(securityToken, deployId, myAppId, appEnvId, myAppDBInstance, myDeployTechnology, myDeployDBSchema, myDeployObjType, myDeployObjName, myDeployDBSchema)
			
			myDeployObjId = self.repo.getDeployObjId(securityToken, myDeployObjName, myDeployObjType, myDeployDBSchema, myDeployDBSchema, appEnvId, myAppDBInstance, myDeployTechnology)
			#createDeployObjHist(securityToken, deployId, deployObjId, appId, appEnvId, env, beforeImage, afterImage)
			myDBResult = self.repo.createDeployObjHist(securityToken, deployId, myDeployObjId, myAppId, appEnvId, myAppEnv, beforeImage, afterImage, task["task_category"])

			return myDBResult

		except Exception as error:
			self.LOGGER.error("an error occurred while populating deployment object dashboard >>> {error}".format(error = str(error)), exc_info = True)
			raise error

if __name__ == "__main__":
	sec = Security()
	mySecToken = sec.authenticate('DMZPROD01\\svc-dev-deploy-app','eXokNzl5NEUzOWdXNCkp')
	deploy = Deploy(mySecToken)
	print("class initialized")
	myDeployId = "deploy_test" 
	myAppId = 999
	myAppEnvId = 56
	myAppName = "CICD Testing"
	myUserId = "u1167965"
	myDeploySource = "jira" 
	myDeploySourceData = "MADBD-32"
	#myJiraId = "MADBD-32"
	myJiraIssueId = "MADBD-101"

	"""
	# create new deployment testing
	result = deploy.createNewDeployment(mySecToken, myJiraIssueId, myDeployId, myAppId, myUserId, myDeploySource, myDeploySourceData)
	print("result >>>", result)	
	"""


	# testing deployment execution
	myDeployId = "20200304T080951683"
	myJiraIssueId = "MADBD-104"
	#securityToken, jiraIssueId, deployId, appEnvId, userId, when = None
	#myDBResult = deploy.performDeployment(mySecToken, myJiraIssueId, myDeployId, myAppEnvId, myUserId)
	#print("result >>>", myDBResult)
	
	# generating deployment log report
	myDBResult = deploy.generateDeployAttemptLog(mySecToken, '20200326T102438853', 56, 60)
	print('result >>>', myDBResult)
	"""
	create app 'CICD Testing'
	#app

	delete from app.app_env_contacts where app_id = 999;
	delete from app.app_envs where app_id = 999;
	delete from app.apps where app_id = 999;

	INSERT INTO app.apps
		(app_id, app_name, region, opco, technology, status, db_schemas, deploy_env_order,requested_by, requested_ts, approved_by, approved_ts)
		VALUES
		(999,'CICD Tesing','nam','marsh','oracle','valid','{"cicd_dev"}', '{"dev","test","stg","prod"}','u1167965',current_timestamp, 'u1167965',current_timestamp);
	
	INSERT INTO app.app_envs
		(app_id, env, host_name, conn_string, db_instance,db_schemas, notification_dl, requested_by, requested_ts, approved_by, approved_ts, status)
		VALUES
		(999, 'dev','oltd144', 
		'(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=usdfw23db23v.mrshmc.com)(PORT=1521))(CONNECT_DATA=(SERVER=DEDICATED)(SERVICE_NAME=oltd144)))', 
		'USDFW23DB23V','{"cicd_dev"}','{"cicd_dev_notify@marsh.com"}','u1167965', current_timestamp,'u1167965',current_timestamp,'valid');

	INSERT INTO app.app_env
		(app_id, env, host_name, conn_string, db_instance,db_schemas, notification_dl, requested_by, requested_ts, approved_by, approved_ts, status)
		VALUES
		(999, 'test','oltd144',
		'(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=usdfw23db23v.mrshmc.com)(PORT=1521))(CONNECT_DATA=(SERVER=DEDICATED)(SERVICE_NAME=oltd144)))', 
		'USDFW23DB23V','{"cicd_dev"}','{"cicd_test_notify@marsh.com"}','u1167965', current_timestamp,'u1167965',current_timestamp,'valid');

	INSERT INTO app.app_env
		(app_id, env, host_name, conn_string, db_instance,db_schemas, notification_dl, requested_by, requested_ts, approved_by, approved_ts, status)
		VALUES
		(999, 'stg','oltd144',
		'(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=usdfw23db23v.mrshmc.com)(PORT=1521))(CONNECT_DATA=(SERVER=DEDICATED)(SERVICE_NAME=oltd144)))', 
		'USDFW23DB23V','{"cicd_dev"}','{"cicd_stg_notify@marsh.com"}','u1167965', current_timestamp,'u1167965',current_timestamp,'valid');

	INSERT INTO app.app_env
		(app_id, env, host_name, conn_string, db_instance,db_schemas, notification_dl, requested_by, requested_ts, approved_by, approved_ts, status)
		VALUES
		(999, 'prod','oltd144',
		'(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=usdfw23db23v.mrshmc.com)(PORT=1521))(CONNECT_DATA=(SERVER=DEDICATED)(SERVICE_NAME=oltd144)))', 
		'USDFW23DB23V','{"cicd_dev"}','{"cicd_prod_notify@marsh.com"}','u1167965', current_timestamp,'u1167965',current_timestamp,'valid');

	INSERT INTO app.app_env_contacts
		(app_id, env, contact_id, contact_type, requested_by, requested_ts, approved_by, approved_ts, status)
		VALUES
		(999, 'dev','ctfy-ug_na_marsh_dba-s-l','owner.adgrp','u1167965', current_timestamp, 'u1167965', current_timestamp, 'valid');

	INSERT INTO app.app_env_contacts
		(app_id, env, contact_id, contact_type, requested_by, requested_ts, approved_by, approved_ts, status)
		VALUES
		(999, 'test','ctfy-ug_na_marsh_dba-s-l','owner.adgrp','u1167965', current_timestamp, 'u1167965', current_timestamp, 'valid');

	INSERT INTO app.app_env_contacts
		(app_id, env, contact_id, contact_type, requested_by, requested_ts, approved_by, approved_ts, status)
		VALUES
		(999, 'stg','ctfy-ug_na_marsh_dba-s-l','owner.adgrp','u1167965', current_timestamp, 'u1167965', current_timestamp, 'valid');

	INSERT INTO app.app_env_contact
		(app_id, env, contact_id, contact_type, requested_by, requested_ts, approved_by, approved_ts, status)
		VALUES
		(999, 'prod','ctfy-ug_na_marsh_dba-s-l','owner.adgrp','u1167965', current_timestamp, 'u1167965', current_timestamp, 'valid');
	"""
