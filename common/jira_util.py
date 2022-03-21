from com.mmc.common.singleton import Singleton
from com.mmc.common.globals import Globals
from com.mmc.common.utility import Utility
from com.mmc.common.security import Security
from com.mmc.common.infrastructure import Infrastructure

from urllib.parse import quote_plus
#from utility import Utility
from jira import JIRA, client, JIRAError

import json, os, sys, platform, psutil, datetime, time, subprocess, socket, re, uuid

import logging, logging.config, sys, inspect, warnings


class JiraUtility(object, metaclass=Singleton):
	def __init__(self, securityToken):

		# instantiating generic classes
		self.infra = Infrastructure()
		self.Globals = Globals()
		self.util = Utility()
		self.sec = Security()

		# validating security token
		self.sec.validateSecToken(securityToken)

		# instantiating sec realm protected classes
		# None

		#self.JIRA_ISSUE_KEY = jiraIssueId
		#myEnvironment = self.util.getACopy(self.infra.environment)
		self.LOGGER = self.infra.LOGGER

		mySecKeyFile = self.util.buildPath(self.infra.environment["app_config_loc"], self.infra.environment["boot"]["keyFile"])

		self.JIRA_BASE_URL = self.infra.environment["boot"]["jiraUrl"]
		self.JIRA_USER = self.infra.environment["boot"]["jiraUser"]
		self.JIRA_USER_ENC_PASS = self.infra.environment["boot"]["jiraUserEncPass"]
		self.JIRA_USER_PASS = self.__decPass(securityToken)

		self.JIRA = JIRA(auth=(self.JIRA_USER, self.JIRA_USER_PASS), options={'server': self.JIRA_BASE_URL})
		"""
		self.SEC_KEY = self.sec._Security__getKey(self.JIRA_USER, mySecKeyFile)

		#myJiraUserPass = self.sec._Security__decryptText(self.SEC_KEY, self.JIRA_USER_ENC_PASS)
		"""

		"""
		commenting below block moving it to __instantiateIssue (internal call)
		self.JIRA_USER_PASS = self.sec._Security__decryptText(self.JIRA_USER_ENC_PASS)

		# instantiating Jira object for this jira issue key
		try:
			self.JIRA_OBJ = JIRA(auth=(self.JIRA_USER, myJiraUserPass), options={'server': self.JIRA_BASE_URL})
			self.JIRA_OBJ_ATTACH = self.JIRA_OBJ.issue(jiraIssueId, expand="attachment")

			if not self.isValidIssueKey(securityToken):
				raise ValueErrir(f"invalid jira id {jiraIssueId}")

		except JIRAError as error:
			raise ValueError("an error occurred >>> {error} ".format(error = "".join([str(error.status_code) , '-', error.text])))
		"""
	def isValidIssue(self, securityToken, jiraIssueId):
		"""
		checks if passed jira issue id exists
		"""
		try:
			myIssue = self.JIRA.issue(jiraIssueId)
			return True
		except Exception as error:
			# valid jira error maximum recursion depth exceeded while calling a Python object ???
			print(error)
			return False

	def __instantiateIssue__donotuse(self, securityToken, jiraIssueId):
		"""
		Instantiate jira issue key for a given (Pending we dont want jira class to be instantiated along with a given jira issue key)
		all jira class should internally call the method and all call to jira must have jira issue id
		"""
		try:
			from jira import JIRA
			#options = {'server':self.JIRA_BASE_URL}
			#jira = JIRA(options, basic_auth=('UN', 'PW')) 
			myJiraObj = JIRA(auth=(self.JIRA_USER, self.JIRA_USER_PASS), options={'server': self.JIRA_BASE_URL})
			#myJiraObjAttatch = self.JIRA_OBJ.issue(jiraIssueId, expand="attachment")

			if not myJiraObj.issue(jiraIssueId):
				raise ValueError("Invalid Jira issue Id >>> {id}".format(id = jiraIssueId))

			return myJiraObj

		except JIRAError as error:
			raise ValueError("an error occurred >>> {error} ".format(error = "".join([str(error.status_code) , '-', error.text])))

	def __decPass(self, securityToken):
		try:
			self.sec.validateSecToken(securityToken)
			#myJiraUserPass = self.sec._Security__decryptText(self.SEC_KEY, self.JIRA_USER_ENC_PASS)
			myJiraUserPass = self.sec._Security__decryptText(self.JIRA_USER_ENC_PASS)

			if isinstance(myJiraUserPass, bytes):
				myJiraUserPass = myJiraUserPass.decode()

			return myJiraUserPass

		except Exception as error:
			self.LOGGER.error("error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def downloadAttachments(self, securityToken, jiraIssueId, targetLoc, filter_ = []):
		"""
			Download all attachments for a given jira key to a target location with given filter on extension
			Arguments:
				securityToken (mandatory): securityToken
				jiraIssueId (mandatory): Jira issue key
				targetLoc (mandatory): attachment download location
				filter_ (optional) : file extension filter (must be an array), e.g.: ['sql','json'] (this will download all files which has file extenstion .sql /.json)
		"""
		try:

			self.LOGGER.debug("arg received >>> {arg} ".format(arg = "".join([str(securityToken), "," , jiraIssueId, ',', targetLoc, ',', str(filter_) ])))

			myModuleName = sys._getframe().f_code.co_name
			self.sec.validateSecToken(securityToken)

			if not (jiraIssueId and filter_ and targetLoc):
				raise ValueError("jiraIssueId/tragetLoc/filter is mandatory arguments !!!")

			if not self.isValidIssue(securityToken, jiraIssueId):
				raise ValueError("Invalid Jira issue Id >>> {id}".format(id = jiraIssueId))

			# retrieving jira user pass
			#myJiraUserPass = self.__decPass(securityToken)

			#jira = JIRA(auth=(self.JIRA_USER, myJiraUserPass), options={'server': self.JIRA_BASE_URL})
			#myJiraObj = self.__instantiateIssue(securityToken, jiraIssueId)
			myJiraObjAttatch = self.JIRA.issue(jiraIssueId, expand="attachment")

			#jiraIssue = self.JIRA.issue(jiraIssueId, expand="attachment")

			self.LOGGER.info("jira issue {id} attachments >>> {issue} ".format(id = jiraIssueId, issue = str(myJiraObjAttatch)))
			self.LOGGER.info("found attachments >>> {attachments} ".format(attachments = str(myJiraObjAttatch.fields.attachment)))

			self.util.createDir(targetLoc)
			
			myFilter = [filter.replace("*.",".") for filter in filter_]
			for attachment in  myJiraObjAttatch.fields.attachment:

				image = attachment.get()  
				jiraFileName = attachment.filename

				# will create target location if it doesnt exists
				self.util.createDir(targetLoc)

				# aplying filter (download files with extention as passed in filter_ array, skip file if not matched)
				if filter_ :
					myJiraFileExtn = self.util.getFileExtn(jiraFileName)
					if not(myJiraFileExtn in myFilter):
						continue

				self.LOGGER.info("downloading attachment {file} to {loc}".format(file = jiraFileName, loc = targetLoc))

				# adding target location path to file name
				myDownloadFileWPath = self.util.buildPath(targetLoc, jiraFileName)

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
			self.LOGGER.error("error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def downloadAnAttachment(self, securityToken, jiraIssueId, targetLoc, fileName):
		#https://community.atlassian.com/t5/Jira-questions/Downloading-attachments-via-jira-module-in-python/qaq-p/449195
		"""
			Download all attachments for a given jira key to a target location with given filter on extension
			Arguments:
				securityToken (mandatory): securityToken
				targetLoc (mandatory): attachment download location
				fileName (optional): file name which need to be downloaded)
		"""
		try:

			self.LOGGER.debug("arg received >>> {arg} ".format(arg = "".join([str(securityToken), "," , jiraIssueId, ',', targetLoc, ',', fileName ])))

			myModuleName = sys._getframe().f_code.co_name
			self.sec.validateSecToken(securityToken)

			if not (jiraIssueId and fileName and targetLoc):
				raise ValueError("jiraIssueId/tragetLoc/fileName is mandatory arguments !!!")

			if not self.isValidIssue(securityToken, jiraIssueId):
				raise ValueError("Invalid Jira issue id {id} !!!".format(id = jiraIssueId))

			# retrieving jira user pass
			#myJiraUserPass = self.__decPass(securityToken)

			#jira = JIRA(auth=(self.JIRA_USER, myJiraUserPass), options={'server': self.JIRA_BASE_URL})
			#jiraIssue = jira.issue(jiraIssueId, expand="attachment")

			#jiraIssue = self.JIRA.issue(jiraIssueId, expand="attachment")

			#myJiraObj = self.__instantiateIssue(securityToken, jiraIssueId)
			myJiraObjAttatch = self.JIRA.issue(jiraIssueId, expand="attachment")

			self.LOGGER.info("jira issue {key} attachments >>> {issue} ".format(key = jiraIssueId, issue = str(myJiraObjAttatch)))
			self.LOGGER.info("found attachments >>> {attachments} ".format(attachments = str(myJiraObjAttatch.fields.attachment)))

			# will create target location if it doesnt exists
			self.util.createDir(targetLoc)

			for attachment in  myJiraObjAttatch.fields.attachment:

				image = attachment.get()  
				jiraFileName = attachment.filename

				# will download file passed in argument only, ignore rest of them
				if fileName and not(fileName == jiraFileName):
					continue

				self.LOGGER.info("downloading attachment {file} to {loc}".format(file = jiraFileName, loc = targetLoc))

				# adding target location path to file name
				myDownLoadFileWPath = self.util.buildPath(targetLoc, jiraFileName)

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
			self.LOGGER.error("error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise error

	def addAttachment(self, securityToken, jiraIssueId, fileName):
		"""
			Add attachment for a given jira key to a target location with given filter on extension
			Arguments:
				securityToken (mandatory): securityToken
				fileName (mandatory): file name which need to be attached to issue (filename must include path)
		"""
		try:
			self.LOGGER.debug("arg received >>> {arg} ".format(arg = "".join([str(securityToken), "," , jiraIssueId, ',', fileName ])))

			myModuleName = sys._getframe().f_code.co_name
			
			self.sec.validateSecToken(securityToken)

			if not (jiraIssueId and fileName):
				raise ValueError("jiraIssueId/fileName is mandatory arguments !!!")

			if not self.util.isFileExists(fileName):
				raise ValueError("invalid file {file} (file is missing) !!".format(file = fileName))

			if not self.isValidIssue(securityToken, jiraIssueId):
				raise ValueError("Invalid Jira issue id {id} !!!".format(id = jiraIssueId))

			# retrieving jira user pass
			myJiraUserPass = self.__decPass(securityToken)

			#from jira.client import JIRA
			#from jira.client import JIRA

			#jira = client.JIRA(basic_auth=(self.JIRA_USER, myJiraUserPass), options={'server': self.JIRA_BASE_URL})
			#issue = jira.issue(jiraIssueId)

			#jiraIssue = self.JIRA.issue(jiraIssueId)

			#myJiraObj = self.__instantiateIssue(securityToken, jiraIssueId)
			#myJiraObjAttatch = self.JIRA.issue(jiraIssueId, expand="attachment")

			self.LOGGER.info("adding attachment {file} to jira key {id} ".format(file = fileName, id = jiraIssueId))
			#self.addAComment(securityToken, jiraIssueId, "uploading file {file}".format(file = fileName))

			#file = open(fileName, 'rb')
			
			#myResult = myJiraObj.add_attachment(jiraIssueId,file)

			with open(fileName, 'rb') as file:
				myResult = self.JIRA.add_attachment(issue = jiraIssueId, attachment=file)

			self.LOGGER.info("returning response >>> {response}".format(response = str(myResult)))

			return myResult

		except Exception as error:
			self.LOGGER.error("error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise

	def removeAttachment(self, securityToken, jiraIssueId, fileName):
		"""
			Remove an attachment for a given jira key
			Arguments:
				securityToken (mandatory): securityToken
				jiraIssueId (mandatoy) : jira issue id
				fileName (mandatory): attached file name need to be removed from issue
		"""
		try:
			self.LOGGER.debug("arg received >>> {arg} ".format(arg = "".join([str(securityToken), "," , jiraIssueId, ',', fileName ])))

			myModuleName = sys._getframe().f_code.co_name
			
			self.sec.validateSecToken(securityToken)

			if not (jiraIssueId and fileName):
				raise ValueError("jiraIssueId/fileName is mandatory arguments !!!")

			if self.util.isFileExists(fileName):
				raise ValueError("invalid file {file} (file is missing) !!".format(file = fileName))

			if not self.isValidIssue(securityToken, jiraIssueId):
				raise ValueError("Invalid Jira issue Id >>> {id}".format(id = jiraIssueId))

			# retrieving jira user pass
			# myJiraUserPass = self.__decPass(securityToken)

			#from jira.client import JIRA
			#from jira.client import JIRA

			#jira = client.JIRA(basic_auth=(self.JIRA_USER, myJiraUserPass), options={'server': self.JIRA_BASE_URL})
			#issue = jira.issue(jiraKey)

			#jiraIssue = self.JIRA.issue(jiraIssueId)

			#myJiraObj = self.__instantiateIssue(securityToken, jiraIssueId)
			myJiraObjAttatch = self.JIRA.issue(jiraIssueId, expand="attachment")

			self.LOGGER.info("removing attachment {attach} for jira issue key {id} ".format(attach = fileName, id = jiraIssueId))

			for indx, attachment in  myJiraObjAttatch.fields.attachment:

				if fileName == attachment.filename:
					# file found, delete and exit from here (we got our job done)
					myJiraObjAttatch.fields.attachment[indx].delete()
					myJiraObjAttatch.update()					
					break

		except Exception as error:
			self.LOGGER.error("error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise

	def addAComment(self, securityToken, jiraIssueId, commentText):
		"""
			Add a comment to issue key
			Arguments:
				securityToken (mandatory): securityToken
				jiraIssueId (mandatory): attachment download location
				commentText (mandatory): comment text)
		"""
		try:
			self.LOGGER.debug("arg received >>> {arg} ".format(arg = "".join([str(securityToken), "," , jiraIssueId, ',', commentText ])))

			myModuleName = sys._getframe().f_code.co_name
			
			self.sec.validateSecToken(securityToken)

			if not (jiraIssueId and commentText):
				raise ValueError("jiraIssueId/commentText is mandatory arguments !!!")

			if not self.isValidIssue(securityToken, jiraIssueId):
				raise ValueError("Invalid Jira issue Id >>> {id}".format(id = jiraIssueId))

			# retrieving jira user pass
			#myJiraUserPass = self.__decPass(securityToken)

			#jira = JIRA(basic_auth=(self.JIRA_USER, myJiraUserPass), options={'server': self.JIRA_BASE_URL})

			#jiraIssue = self.JIRA.issue(jiraIssueId)

			#myJiraObj = self.__instantiateIssue(securityToken, jiraIssueId)
			#myJiraObjAttatch = myJiraObj.issue(jiraIssueId, expand="attachment")

			self.LOGGER.info("adding a comment to jira issue id {id} >>> {comment} ".format(id = jiraIssueId, comment = commentText))

			myResult = self.JIRA.add_comment(jiraIssueId, commentText)

			self.LOGGER.info("returning response >>> {response}".format(response = str(myResult)))

			return myResult

		except Exception as error:
			self.LOGGER.error("error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise

	def changeIssueTransition(self, securityToken, jiraIssueId, env, operation, outcome):
		"""
			change transition of an issue key
			Arguments:
				securityToken (mandatory): securityToken
				jiraIssueId (mandatory) : jira issue id
				env (mandatory): environment in which issue key is deployed
				operation (mandatory) : deployment operation
				outcome (mandatory) : outcome of deployment Success/UnSuccess
		"""
		try:
			self.LOGGER.debug("arg received >>> {arg} ".format(arg = "".join([str(securityToken), ',', jiraIssueId, ',', env, ',', operation, ',', outcome])))

			myModuleName = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not self.isValidIssue(securityToken, jiraIssueId):
				raise ValueError("Invalid Jira issue Id >>> {id}".format(id = jiraIssueId))

			# retrieving jira user pass
			#myJiraUserPass = self.__decPass(securityToken)

			#jira = JIRA(basic_auth=(self.JIRA_USER, myJiraUserPass), options={'server': self.JIRA_BASE_URL})

			self.LOGGER.info("determining transition state for this outcome")

			#myJiraObj = self.__instantiateIssue(securityToken, jiraIssueId)

			myTransitionState = self.getJiraEnvOutcmeTransition(securityToken, env, operation, outcome)

			myAllowedTransition = self.getAllowedTransition(securityToken, jiraIssueId, jiraIssueId)

			self.LOGGER.info("validating transition state >>> {state}".format(state = myTransitionState))

			'''
			'Rollback (DEV) Success', 
			'Rollback (DEV) Failed'] got 
			'Rollback (DEV) Failed
			'''
			if not(myTransitionState in myAllowedTransition):
				raise ValueError("Invalid transition for issue id {id}, expecting {expect} got {got} ".format(id = jiraIssueId, expect = str(myAllowedTransition), got = str(myTransitionState)))

			self.LOGGER.info("changing issue id {id} transition state to {state}".format(id = jiraIssueId, state = myTransitionState))

			myResult = myJiraObj.transition_issue(jiraIssueId, myTransitionState, comment = "transition performed by 'auto deploy process' @ {time}".format(time = self.util.lambdaGetCurrReadableTime()))

			self.LOGGER.info("returning response >>> {response}".format(response = str(myResult)))

		except Exception as error:
			self.LOGGER.error("error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise

	def getJiraEnvOutcmeTransition(self, securityToken, env, operation, outcome):
		"""
			returns jira status for a given env and its execution outcome
			Arguments:
				securityToken (mandatory): securityToken
				env (mandatory): env in which deployment is performed
				operation (mandatory) : deployment operation 
				outcome (mandatory) : outcome of deployment (Success/UnSuccess)
		"""
		try:
			self.LOGGER.debug("arg received >>> {arg} ".format(arg = "".join([str(securityToken), ",", env, ",",operation, ",", outcome])))

			myModuleName = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			if not (env in self.Globals.allEnv):
				raise ValueError("Invalid env !!! (env must be in >>> {validEnv})".format(validEnv = self.Globals.allEnv))

			if not (operation in self.Globals.allDeployOperation):
				raise ValueError("Invalid operation !!! (Operaiton must be in >>> {validOp})".format(validOp = self.Globals.allDeployOperation))

			self.LOGGER.info("retrieving transition state for this issue key")

			myTransition = self.Globals.jiraEnv[env][operation][outcome]

			self.LOGGER.info("returning response >>> {response}".format(response = str(myTransition)))

			return myTransition

		except Exception as error:
			self.LOGGER.error("error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise

	def getAllowedTransition(self, securityToken, jiraIssueId):
		"""
			Retrieve allowed transition of a given Jira issue ket
			Arguments:
				securityToken (mandatory): securityToken
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name
			self.sec.validateSecToken(securityToken)
			self.LOGGER.debug("arg received >>> {arg} ".format(arg = "".join([str(securityToken, ',', jiraIssueId)])))

			self.LOGGER.info("retrieving jira issue valid transitions for jira issue key {id} ".format(id = jiraIssueId))

			if not self.isValidIssue(securityToken, jiraIssueId):
				raise ValueError("Invalid Jira issue Id >>> {id}".format(id = jiraIssueId))

			#myJiraObj = self.__instantiateIssue(securityToken, jiraIssueId)

			myJiraTransResponse = self.JIRA.transitions(jiraIssueId)

			self.LOGGER.info("jira transitions response for {id} >>> {response}".format(id = jiraIssueId, response = str(myJiraTransResponse)))

			allowedTransitions = [trans["name"] for trans in myJiraTransResponse]

			self.LOGGER.info("allowed transition for issue id {id} >>> {allowed}".format(id = jiraIssueId, allowed = str(allowedTransitions)))

			return allowedTransitions

		except Exception as error:
			self.LOGGER.error("error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise

	def getIssue__testing(self, securityToken):
		"""
			Returns the status of an issue from Jira
			Arguments:
				securityToken (mandatory): securityToken
		"""
		try:
			myModuleName = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.LOGGER.debug("arg received >>> {arg} ".format(arg = "".join([str(securityToken)])))

			return myJiraObj.fields()
			return myJiraObj.issue(jiraIssueId)


		except Exception as error:
			self.LOGGER.error("error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise

	def getIssueDetails(self, securityToken, jiraIssueId):
		"""
			retrieves all issue details
			Arguments:
				securityToken (mandatory): securityToken
		"""
		try:
			self.LOGGER.debug("arg received >>> {arg} ".format(arg = "".join([str(securityToken), ',', jiraIssueId])))

			myModuleName = sys._getframe().f_code.co_name

			self.sec.validateSecToken(securityToken)

			self.LOGGER.info("retrieving jira issue details for {id} ".format(id = jiraIssueId))

			myJiraObj = self.__instantiateIssue(securityToken, jiraIssueId)

			myIssue = myJiraObj.issue(jiraIssueId)

			self.LOGGER.info("returning response >>> {response}".format(response = str(myIssue)))

			return myIssue
			#for field_name in issue.raw['fields']:
    		#	print ("Field:", field_name, "Value:", issue.raw['fields'][field_name])

		except Exception as error:
			self.LOGGER.error("error [{error}] occurred ".format(error = str(error)) , exc_info = True)
			raise


if __name__ == "__main__":
	import time
	#from com.mmc.core.security import Security
	#sec = Security()
	#secToken = sec.authenticate ("us02p01\\u1167965","gAAAAABcXZBb2wx4rIvScd5fxzYM1G83KIwOPYkcaxQlHxcbvS9AJQY4w-l-aATT9b0Mix0VeMcyAva18tYhlkrev9yRVliGKg==", "SrzgFG4C7L2YB25TOv6Bl2YHBsSHpkhFIgeQmTFgycw=")
	sec = Security()
	mySecToken = sec.authenticate('DMZPROD01\\svc-dev-deploy-app','eXokNzl5NEUzOWdXNCkp')
	jira = JiraUtility(mySecToken, 'MADBD-99')
	print(jira.getIssueDetails(mySecToken))
	#print(jira.getIssue__testing(mySecToken))

	#jira.downloadAttachments(mySecToken, 'p:\\app\\cicd\\deploy\\jira_download',['sql','json'] )

	# add attachment
	#response = jira.addAttachment(secToken, file)
	#print("response >>>", response)

	# download attachment (all)

	'''
	print("downloading all attachments")
	response = jira.downloadAttachments(secToken, '/opt/ansible/deploy/logs/jira_download')
	print("response >>>", response)

	print("downloading attachment ", file)
	response = jira.downloadAnAttachment(secToken, '/opt/ansible/deploy/logs/jira_download/download_temp', file)
	print("response >>>", response)
	'''

	# adding comment
	'''
	print("adding comment ", file)
	response = jira.addAComment(secToken, 'this is test @ {now}'.format(now = time.ctime()))
	print("response >>>", response)
	'''
	"""
	# change state
	allTransitions = jira.getAllowedTransition(secToken)
	print('transictions >>>', str(allTransitions))
	myResult = jira.changeIssueTransition(secToken, 'STAGE Deploy Successful')
	# change status
	"""