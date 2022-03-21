from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.common.globals import Globals

import logging, logging.config, sys, json

class CICDGlobals(object, metaclass=Singleton):

	def __init__(self, securityToken):
		self.infra = Infrastructure()
		self.util = Utility()
		self.CICD_INFRA_ONBOARD_VAR = self.util.getACopy(self.infra.ENVIRONMENT["cicd"]["onBoarding"])
		self.CICD_INFRA_DEPLOY_VAR = self.util.getACopy(self.infra.ENVIRONMENT["cicd"]["onBoarding"])

        self.STATUS_PENDING = "pending"
        self.STATUS_INPROGRES = "in-progress"
        self.STATUS_COMPLETED = "completed"
        self.STATUS_ERROR = "error"
        self.STATUS_ACTIVE = "active"
        self.STATUS_INACTIVE = "in-active"
        self.STATUS_APPROVED = "valid"
        self.STATUS_VALID = "valid"
        self.STATUS_PENDING_ACTIVE = 'both'
        self.STATUS_EXISTS = "exists"

        self.VALID_STATUS_LIST = [self.STATUS_ACTIVE, self.STATUS_VALID]
        self.defaultModule = 'python'
        
        self.TECHNOLOGY_ORACLE = 'oracle'
        self.TECHNOLOGY_POSTGRES = 'postgres'
        self.TECHNOLOGY_MONGO = 'mongo'
        self.TECHNOLOGY_MSSQL = 'mssql'
        self.TECHNOLOGY_TOMCAT = 'tomcat'
        self.TECHNOLOGY_WEBLOGIC = 'weblogic'

        self.DBASS_TECHNOLOGY_ORACLE = 'Oracle'
        self.DBASS_TECHNOLOGY_POSTGRES = 'Postgres'
        self.DBASS_TECHNOLOGY_MONGO = 'Mongo'
        self.DSBASS_TECHNOLOGY_MSSQL = 'MSSql'

        self.REGION_NAM = 'nam'
        self.REGION_EMEA = 'emea'
        self.REGION_APAC = 'apac'
        self.REGION_LATM = 'latm'

        self.OPCO_MARSH = 'marsh'
        self.OPCO_MERCER = 'mercer'
        self.OPCO_GC = 'gc'

        # contact type is owner/support/admin
        self.CONTACT_TYPE_OWNER_ID = 'owner.id'
        self.CONTACT_TYPE_OWNER_ADGRP = 'owner.adgrp'
        self.CONTACT_TYPE_ADMIN_ID = 'admin.id'
        self.CONTACT_TYPE_ADMIN_ADGRP = 'admin.adgrp'
        self.CONTACT_TYPE_SUPPORT_ID = 'support.id'
        self.CONTACT_TYPE_SUPPORT_ADGRP = 'support.adgrp'
        self.ALL_CONTACT_TYPE_ADGRP_LIST = [self.CONTACT_TYPE_OWNER_ADGRP, self.CONTACT_TYPE_ADMIN_ADGRP, self.CONTACT_TYPE_SUPPORT_ADGRP]

        self.ENV_DEV = 'dev'
        self.ENV_TEST = 'test'
        self.ENV_UAT = 'uat'
        self.ENV_STAGING = 'stg'
        self.ENV_PERF = 'perf'
        self.ENV_PROD = 'prod'
        self.ENV_NONPROD = 'non-prod'
        self.ENV_LOWER = [self.ENV_DEV,self.ENV_TEST,self.ENV_UAT,self.ENV_STAGING]

        self.DEPLOY_DOWNLOAD_LOC = "p:\\app\\cicd\\deploy"
        self.DEPLOY_README_FILE = "deploy_readme.json"
        self.DEPLOY_PARSE_OUT_FILE = "parse.{suffix}.json"
        self.DEPLOY_SOURCE_JIRA = "jira"
        self.DEPLOY_SOURCE_BITBUCKET = "bitbucket"
        
        self.TASK_TYPE_USER = 'user'
        self.TASK_TYPE_SYS = 'system'
        self.TASK_TYPE_ROLLBACK = 'rollback'

        self.DEFAULT_TS_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%f" # this format is needed to convert date stored in json to date obj
        self.DEFAULT_TSTZ_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

        # status in whhich deployment files can be added
        self.VALID_STATUS_RELOAD_DEPLOY_FILES_LIST = ["pending","validation.unsuccess"]

    def __repr__(self):
            return "(%s)" % (self.__class__)

    def __str__(self):
            return "(%s)" % (self.__class__)
