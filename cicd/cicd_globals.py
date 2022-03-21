from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
#from com.mmc.common.error import *
from com.mmc.common.infrastructure import Infrastructure
#from com.mmc.common.globals import Globals

import logging, logging.config, sys, json

class CICDGlobals(object, metaclass=Singleton):

    def __init__(self):
        self.infra = Infrastructure()
        self.util = Utility()

        self.CICD_INFRA_ONBOARD_VAR = self.util.getACopy(self.infra.environment["cicd"]["onBoarding"])
        self.CICD_INFRA_DEPLOY_VAR = self.util.getACopy(self.infra.environment["cicd"]["deploy"])

        del self.infra

        #self.CICD_INFRA_ORA_PRE_DEPLOY_VAR = self.util.getACopy(self.infra.environment["cicd"]["deploy"])
        #print(self.CICD_INFRA_ONBOARD_VAR)
        #print(self.CICD_INFRA_DEPLOY_VAR)
        
        self.deployReportHeader = """
        DEPLOYMENT LOG REPORT
        =====================

        Summary
        -------

                        Deployment id:      [{deployId}]                   
                        Status:             [{deployStatus}]
                        Environment:        [{env}]
                        DB URI:             [{dbUri}]                 
                        Total Attempts:     [{totalAttempts}]
                        Current Attempt:    [{attemptId} @ {attemptTs}] 
                        Requested By/Ts:    [{requestedBy} - {requestedTs}]
                        Start Time:         [{startTime}]                     
                        End Time :          [{endTime}]                    
                        Duration:           [{duration}]
        
        """
        #Seq Start Time                                End Time                                 Tasks       | Status 
        #xxx 012345678901234567890123456789012345678 | 01234567890123456789012345678901234567 | 01234/01234 | 

        self.deployAttemptDetailHeader = """
        Attempt Details
        ---------------

        Seq | Start Time                       | End Time                         |  Duration | Tasks    | Status 
        ----+----------------------------------+----------------------------------+-----------+----------+----------------------
"""

        self.deployAttemptDetailFooter = """
        -------------------------------------------------------------------------------------------------------------------------------------------------------

        """
        self.deployRepTaskDetailHeader = """
        Task Details
        ------------
        """
        self.deployRepTaskDetail = """
            Task id : [{taskId}]
            Task : [{task}]
            Result : [{result}]
            Records affected: [{recordsAffected}]
            Start Time: [{startTime}]       End Time: [{endTime}]     
            Duration: [{duration}]          
            Status: [{status}]
        --------------------------------------------------------------------------------------------------------------------------------------------------------
        """
        self.deployRepTaskDetailFooter = """
        ===================================Deployment Log Report Ends============================================================================================
        """
        self.deployReportFileSummary= """ """
        self.deployReportTaskDetail= """ """
        self.open = "Open"
        self.closed = "Closed"
        self.completed = "Completed"
        self.frozen = "Frozen"
        self.success = 'Success'
        self.unsuccess = 'UnSuccess'
        self.ready = "Ready"
        self.inprogress = 'InProgress'
        self.pending = "Pending"
        self.APPROVAL_STATUS_PENDING = self.pending
        self.APPROVAL_STATUS_APPROVED = "Approved"
        self.buildInprogress = "BuildInprogress"
        self.error = "Error"
        self.validation = "validation"
        self.deploy = "deploy"
        self.cancelled = "cancelled"

        # request
        self.REQ_ONBOARD_NEW_APP_ENV = "onboard.new.app.env"
        self.REQ_ONBOARD_DEL_APP_ENV = "onboard.del.app.env"
        self.REQ_ONBOARD_NEW_APP_SCHEMA = "onboard.new.app.schema"
        self.REQ_ONBOARD_DEL_APP_SCHEMA = "onboard.del.app.schema"
        self.REQ_DEPLOY_NEW_DEPLOY_ENV = "deploy.new.env"
        self.REQ_DEPLOY_NEW_DEPLOY_ENV = "deploy.new.env"

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

        self.INIT_VALIDATION_ATTEMPTS = 1

        self.STATUS_PENDING = "pending"
        self.STATUS_INPROGRESS = "in-progress"
        self.STATUS_COMPLETED = "completed"
        self.STATUS_ERROR = "error"
        self.STATUS_ACTIVE = "active"
        self.STATUS_INACTIVE = "in-active"
        self.STATUS_APPROVED = "valid"
        self.STATUS_SUCCESS = self.success
        self.STATUS_UNSUCCESS = self.unsuccess
        self.STATUS_VALID = "valid"
        self.STATUS_PENDING_ACTIVE = 'both'
        self.STATUS_EXISTS = "exists"
        self.STATUS_DELETED = 'deleted'
        self.STATUS_CANCELLED = 'cancelled'

        self.ENV_DEV = 'dev'
        self.ENV_TEST = 'test'
        self.ENV_UAT = 'uat'
        self.ENV_STAGING = 'stg'
        self.ENV_PERF = 'perf'
        self.ENV_PROD = 'prod'
        self.ENV_NONPROD = 'non-prod'
        self.ENV_LOWER = [self.ENV_DEV,self.ENV_TEST,self.ENV_UAT,self.ENV_STAGING]

        self.TASK_TYPE_USER = 'user'
        self.TASK_TYPE_SYS = 'system'
        self.TASK_TYPE_ROLLBACK = 'rollback'

        self.DEFAULT_TS_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%f" # this format is needed to convert date stored in json to date obj
        self.DEFAULT_TSTZ_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

        self.ORACLE_DATA_LOAD = "ora.load"

        self.MAX_ONBOARDING_APP_PER_USER = self.CICD_INFRA_ONBOARD_VAR["maxOnboardingAppPerUser"]
        self.MAX_DEPLOY_REVALIDATION = self.CICD_INFRA_DEPLOY_VAR["deployMaxRevalidation"]
        self.DEPLOY_MAX_ATTEMPTS = self.CICD_INFRA_DEPLOY_VAR["deployMaxAttempts"]
        self.MAX_DEPLOY_PER_USER = self.CICD_INFRA_DEPLOY_VAR["maxDeployPerUser"]
        self.DEPLOY_DOWNLOAD_LOC = self.CICD_INFRA_DEPLOY_VAR["deployFilePath"]
        self.DEPLOY_README_FILE = self.CICD_INFRA_DEPLOY_VAR["deployReadmeFile"]
        self.DEPLOY_PARSE_OUT_FILE = self.CICD_INFRA_DEPLOY_VAR["deployParseOutFile"]
        self.DEPLOY_SOURCE_JIRA = self.CICD_INFRA_DEPLOY_VAR["deploySourceJira"]
        self.DEPLOY_SOURCE_BITBUCKET = self.CICD_INFRA_DEPLOY_VAR["deploySourceBB"]

        self.ALL_DEPLOY_SOURCE = [
            self.DEPLOY_SOURCE_JIRA,
            self.DEPLOY_SOURCE_BITBUCKET            
        ]
        #self.DEPLOY_DOWNLOAD_FILE_EXTN = self.CICD_INFRA_DEPLOY_VAR["deployFileExtn"]
        self.ALLOWED_USER_DEPLOY_STMT = {
            self.TECHNOLOGY_ORACLE : [
                "create.table","create.sequence","create.synonym","create.view","create.index","create.materialized view","create.procedure","create.function","create.package","create.package body","create.trigger",
                "rename.table",
                "alter.session","alter.table","alter.sequence","alter.view","alter.index","alter.materialized view","alter.procedure","alter.function","alter.package","alter.package body","alter.trigger",
                "drop.table","drop.sequence","drop.view","drop.index","drop.materialized view","drop.procedure","drop.function","drop.package","drop.package body","drop.trigger"
            ]
        }

        self.DEPLOY_STATUS_VALIDATION_PENDING = "".join([self.validation,".",self.pending])
        self.DEPLOY_STATUS_VALIDATION_INPROGRESS = "".join([self.validation,".",self.inprogress])
        self.DEPLOY_STATUS_VALIDATION_SUCCESS = "".join([self.validation,".",self.success])
        self.DEPLOY_STATUS_VALIDATION_UNSUCCESS = "".join([self.validation,".",self.unsuccess])
        self.DEPLOY_STATUS_VALIDATION_ERROR = "".join([self.validation,".",self.error])
        self.DEPLOY_STATUS_CANCELLED = "".join([self.validation,".",self.cancelled])
        self.DEPLOY_STATUS_DEPLOY_PENDING = "".join([self.deploy,".",self.pending])
        self.DEPLOY_STATUS_DEPLOY_READY = "".join([self.deploy,".",self.ready])
        self.DEPLOY_STATUS_DEPLOY_INPROGRESS = "".join([self.deploy,".",self.inprogress])
        self.DEPLOY_STATUS_DEPLOY_SUCCESS = "".join([self.deploy,".",self.success])
        self.DEPLOY_STATUS_DEPLOY_UNSUCCESS = "".join([self.deploy,".",self.unsuccess])
        self.DEPLOY_STATUS_DEPLOY_ERROR = "".join([self.deploy,".",self.error])
        self.DEPLOY_STATUS_DEPLOY_SUCCESS_APPROVED = "".join([self.DEPLOY_STATUS_DEPLOY_SUCCESS,".approved"])
        self.DEPLOY_STATUS_DEPLOY_SUCCESS_ROLLBACK = "".join([self.DEPLOY_STATUS_DEPLOY_SUCCESS,".rollback"])
        self.DEPLOY_STATUS_DEPLOY_UNSUCCESS_IGNORE_ERROR = "".join([self.deploy,".",self.unsuccess,".ignoreError"])
        self.DEPLOY_STATUS_DEPLOY_COMPLETED = "".join([self.deploy,".",self.completed])


        # status in whhich deployment files can be added/reprocessed
        self.VALID_STATUS_RELOAD_DEPLOY_FILES_LIST = [
            self.DEPLOY_STATUS_VALIDATION_PENDING, 
            self.DEPLOY_STATUS_VALIDATION_SUCCESS, 
            self.DEPLOY_STATUS_VALIDATION_UNSUCCESS, 
            self.DEPLOY_STATUS_VALIDATION_ERROR
        ]

        self.DEPLOY_ALL_STATUS = [
            self.DEPLOY_STATUS_VALIDATION_PENDING,
            self.DEPLOY_STATUS_VALIDATION_INPROGRESS,
            self.DEPLOY_STATUS_VALIDATION_SUCCESS,
            self.DEPLOY_STATUS_VALIDATION_UNSUCCESS,
            self.DEPLOY_STATUS_VALIDATION_ERROR,
            self.DEPLOY_STATUS_CANCELLED,
            self.DEPLOY_STATUS_DEPLOY_INPROGRESS,
            self.DEPLOY_STATUS_DEPLOY_SUCCESS,
            self.DEPLOY_STATUS_DEPLOY_UNSUCCESS
        ]

        self.DEPLOY_ATTEMPT_ALL_STATUS = [
            self.DEPLOY_STATUS_DEPLOY_READY,
            self.DEPLOY_STATUS_DEPLOY_INPROGRESS,
            self.DEPLOY_STATUS_DEPLOY_SUCCESS,
            self.DEPLOY_STATUS_DEPLOY_UNSUCCESS
        ]
        self.DEPLOY_CTRL_ALL_STATUS = [
            self.STATUS_ACTIVE,
            self.STATUS_INACTIVE,
            self.STATUS_CANCELLED
        ]

        self.DEPLOY_FILES_ALL_STATUS = [
            self.STATUS_VALID,
            self.STATUS_CANCELLED
        ]

        self.DEPLOY_TASKS_ALL_STATUS = [
            self.STATUS_SUCCESS,
            self.STATUS_UNSUCCESS,
            self.STATUS_VALID,
            self.STATUS_CANCELLED
        ]

        self.DEPLOY_STATUS_MAP = {
            self.validation : {
                self.success : self.DEPLOY_STATUS_VALIDATION_SUCCESS,
                self.unsuccess : self.DEPLOY_STATUS_VALIDATION_UNSUCCESS,
                self.error : self.DEPLOY_STATUS_VALIDATION_ERROR,
                self.cancelled : self.DEPLOY_STATUS_CANCELLED
            },
            self.deploy : {
                self.inprogress : self.DEPLOY_STATUS_DEPLOY_INPROGRESS,
                self.success : self.DEPLOY_STATUS_DEPLOY_SUCCESS,
                self.unsuccess : self.DEPLOY_STATUS_DEPLOY_UNSUCCESS,
                self.completed : self.DEPLOY_STATUS_DEPLOY_COMPLETED
            }
        }

        self.VALID_STATUS_LIST = [self.STATUS_ACTIVE, self.STATUS_VALID]

        # ?? what if this request is rejected, we need to come up with different status mechanism
        # should we allow all changes to be done only if a request is being approved or rejected or just approved
        self.STATUS_ONBOARD_ADD_ENV_APPROVAL_PENDING = "onboard.add.env.approval.pending" 
        self.STATUS_ONBOARD_DEL_ENV_APPROVAL_PENDING = "onboard.del.env.approval.pending"
        self.STATUS_ONBOARD_ADD_SCHEMA_APPROVAL_PENDING = "onboard.add.schema.approval.pending"
        self.STATUS_ONBOARD_DEL_SCHEMA_APPROVAL_PENDING = "onboard.del.schema.approval.pending"
        self.STATUS_ONBOARD_UPD_DEPLOYORDER_APPROVAL_PENDING = "onboard.upd.deporder.approval.pending"

        self.STATUS_APPROVED_MAP = {
            self.STATUS_ONBOARD_ADD_ENV_APPROVAL_PENDING : self.STATUS_VALID,
            self.STATUS_ONBOARD_DEL_ENV_APPROVAL_PENDING : self.STATUS_INACTIVE,
            self.STATUS_ONBOARD_ADD_SCHEMA_APPROVAL_PENDING : self.STATUS_VALID,
            self.STATUS_ONBOARD_DEL_SCHEMA_APPROVAL_PENDING : self.STATUS_VALID,
            self.STATUS_ONBOARD_UPD_DEPLOYORDER_APPROVAL_PENDING : self.STATUS_VALID
        }

        self.VALID_STATUS_TUPLE = (self.STATUS_ACTIVE, self.STATUS_VALID)
        self.INVALID_STATUS_TUPLE = (self.STATUS_INACTIVE, self.STATUS_DELETED)

        self.ALL_REGION = [self.REGION_NAM, self.REGION_EMEA, self.REGION_APAC, self.REGION_LATM]
        self.ALL_OPCO = [self.OPCO_MARSH, self.OPCO_MERCER, self.OPCO_GC]
        self.ALL_TECHNOLOGY = [self.TECHNOLOGY_ORACLE, self.TECHNOLOGY_MSSQL, self.TECHNOLOGY_MONGO, self.TECHNOLOGY_POSTGRES] 

        # contact type is owner/support/admin
        self.CONTACT_TYPE_OWNER_ID = 'owner.id'
        self.CONTACT_TYPE_OWNER_ADGRP = 'owner.adgrp'
        self.CONTACT_TYPE_ADMIN_ID = 'admin.id'
        self.CONTACT_TYPE_ADMIN_ADGRP = 'admin.adgrp'
        self.CONTACT_TYPE_SUPPORT_ID = 'support.id'
        self.CONTACT_TYPE_SUPPORT_ADGRP = 'support.adgrp'
        self.ALL_CONTACT_TYPE_ADGRP_LIST = [self.CONTACT_TYPE_OWNER_ADGRP, self.CONTACT_TYPE_ADMIN_ADGRP, self.CONTACT_TYPE_SUPPORT_ADGRP]


    def __repr__(self):
        return "(%s)" % (self.__class__)

    def __str__(self):
        return "(%s)" % (self.__class__)
if __name__ == "__main__":
    glob = CICDGlobals()
    print(dir(glob))