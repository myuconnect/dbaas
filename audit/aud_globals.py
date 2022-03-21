from com.mmc.common.singleton import Singleton
from com.mmc.common.security import Security

class AuditGlobals(object, metaclass = Singleton):
    def __init__(self, securityToken):

        self.sec = Security()

        # instantiating class protected with security realm
        self.sec.validateSecToken(securityToken)

        self.AD_GROUP_ROLE_KW = "CN="
        self.DB_TYPE_MONGO = "mongo"
        self.DB_TYPE_POSTGRES = "postgres"
        self.DB_TYPE_ORACLE = "oracle"
        self.DB_TYPE_SQLSERVER = "sqlserver"
        self.DB_TYPE_MYSQL = "mysql"
        self.DB_TYPE_TERADATA = "teradata"
        self.DB_TYPE_ALL = \
            [self.DB_TYPE_MONGO, self.DB_TYPE_POSTGRES, self.DB_TYPE_ORACLE, self.DB_TYPE_SQLSERVER, self.DB_TYPE_MYSQL, self.DB_TYPE_TERADATA]

        self.SEARCH_COMP_LIST=["db.config","db.users","db.roles","db.database","oplog.size","current.op","top","log","conn.stats","conn.pool.stats","replication.info","server.status","db.latest.backup","hosts.info"]
        self.DEFAULT_LIMIT_HISTORY_OUTPUT = 50
        self.success = "Success"
        self.unSuccess = "UnSuccess"
        self.unsuccess = "UnSuccess"
        self.active = "Active"
        self.revoked = "revoked"
        self.inProgress = "In-Progress"
        self.error = "Error"
        self.pending = "Pending"
        self.open = "Open"
        self.closed = "closed"
        self.scanUser = "scan"
        self.compStatusClosed = self.closed
        self.compStatusOpen = self.open
        self.compStatusWIP = self.inProgress
        self.compStatusPending = self.pending
        self.compStatusPassed = "Passed"
        self.compStatusFailed = "Failed"
        self.auditStatusOpen = self.open
        self.auditStatusWIP = self.inProgress
        self.auditStatusClosed = self.closed
        self.activeStatus = self.active
        self.revokedStatus = "Revoked"
        self.inActiveStatus = "InActive"
        self.inActiveOpenStatus = "In-Active.Open"
        self.inActivePendingStatus = "In-Active.Pending"
        #self.annual = "annual"
        #self.quarterly = "quarterly"
        #self.weekly = "weekly"
        self.DC_LOCATION_AWS="aws"
        self.opcoDomain = {"marsh" : "mrshmc.com","mercer" : "mrshmc.com.com","gc" : "gc.mrshmc.com","mgti":"mrshmc.com"}
        self.atRiskConfig = {
            "yearly" : {"days" : 90},
            "quarterly" : {"days" : 10},
            "monthly" : {"days" : 7},
            "weekly" : {"days" : 1},
            "daily" : {"days" : 0}
        }

        self.ENV_DEV = "dev"
        self.ENV_TEST = "test"
        self.ENV_STG = "stg"
        self.ENV_UAT = "uat"
        self.ENV_PERF = "perf"
        self.ENV_PROD = "prod"
        self.ALL_ENV = [self.ENV_DEV, self.ENV_TEST, self.ENV_STG, self.ENV_UAT, self.ENV_PERF,self.ENV_PROD]

        self.NON_PROD = "non-prod"
        self.NON_PROD_LIST = [self.ENV_DEV]

        self.STATS_STORAGE = "storage"
        self.EXCLUDE_FS_STATS_LIST = ["/", "/boot","/tmp"]
        self.NOTIFICATION_SERVICE_EMAIL = ('Notification Service','donotreply@marsh.com')
        self.VENDOR_RECIPIENT = "mongodbtier2@datavail.com"
        self.MARSH_LEAD_EMAIL = "anil.singh@marsh.com, pao-gen.wang@marsh.com, ricardo.lewis@marsh.com, Cherry.Gerges@marsh.com"

        self.WEEKLY_AUDIT_EMAIL_BODY = """
            <p><strong>ATTN TEAM:</strong></p>
            <p><span style="font-family: 'Calibri','sans-serif';">Pls complete following steps in attached "Weekly Mongo Audit Report".</span></p>
                <ol>
                    <li><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif';">Fill in following column details in this attached sheet </span></li>
                </ol>
                <table style="margin-left: 30.6pt; border-collapse: collapse;">
                    <tbody>
                        <tr>
                            <td style="width: 170.6pt; border: none; border-bottom: solid white 2.25pt; background: black; padding: 0in 5.4pt 0in 5.4pt;" width="227">
                                <p><strong><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif'; color: white;">Columns</span></strong></p>
                            </td>
                        </tr>
                        <tr>
                            <td style="width: 170.6pt; border: none; border-right: solid white 2.25pt; background: #365F91; padding: 0in 5.4pt 0in 5.4pt;" width="227">
                                <p><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif'; color: white;">Closed By (your network id)</span></p>
                            </td>
                        </tr>
                        <tr>
                            <td style="width: 170.6pt; border: none; border-right: solid white 2.25pt; background: #365F91; padding: 0in 5.4pt 0in 5.4pt;" width="227">
                                <p><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif'; color: white;">Closed Date (Today&rsquo;s Date)</span></p>
                            </td>
                        </tr>
                        <tr>
                            <td style="width: 170.6pt; border: none; border-right: solid white 2.25pt; background: #365F91; padding: 0in 5.4pt 0in 5.4pt;" width="227">
                                <p><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif'; color: white;">Comments </span></p>
                            </td>
                        </tr>
                        <tr>
                            <td style="width: 170.6pt; border: none; border-right: solid white 2.25pt; background: #365F91; padding: 0in 5.4pt 0in 5.4pt;" width="227">
                                <p><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif'; color: white;">Supporting Docs (Change Order #)</span></p>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <ol>
                    <li><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif';">Send updated sheet to regional lead</span></li>
                    <li><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif';">Upload &ldquo;updated sheet&rdquo; to below Sharepoint&nbsp; URL</span><span style="font-size: 11.0pt; font-family: 'Calibri','sans-serif';"> <a href="Mongo%20Audit Controls (sharepoint link)">https://sharepoint.mrshmc.com/sites/ts1/dbaportal/Audit%20Controls/Forms/AllItems.aspx?RootFolder=%2Fsites%2Fts1%2Fdbaportal%2FAudit%20Controls%2FMonthly%20Audit%20Review%20Documentation%2FNAM%2FDBA%20Account%20Reviews%2F2019%2FMongoDB&amp;InitialTabId=Ribbon%2ERead&amp;VisibilityContext=WSSTabPersistence&nbsp;</a></span></li>
                </ol>
        """

        self.MONTHLY_MONGO_ROOT_PRIVS_BODY = """
            <p>ATTN TEAM:</p>
            <p>Pls find attached "Monthly Mongo Root Privilege Report", validate all users/role in this report. Upon successful validation, upload this file to below sharepoint url.</p>
            <p><a href="Monthly%20Root Privilege Report URL">https://sharepoint.mrshmc.com/sites/ts1/dbaportal/Audit%20Controls/Forms/AllItems.aspx?RootFolder=%2Fsites%2Fts1%2Fdbaportal%2FAudit%20Controls%2FMonthly%20Audit%20Review%20Documentation%2FNAM%2FDBA%20Account%20Reviews%2F2019%2FMongoDB&amp;InitialTabId=Ribbon%2ERead&amp;VisibilityContext=WSSTabPersistence</a></p>
        """
        # email 
        self.REST_API_NOT_REACHABLE_EMAIL_BODY = """
Attn: 

REST API End point is not available.. 

Pls ensure Audit REST API is running on host {API_HOST}, port {API_PORT} and port is open from this host.
Following are the steps to troubelshooti this issue 
Stpes: 
    1. Ensure port {API_HOST}:{API_PORT} is open friom this server
    2. Login to {API_HOST}, sudo to user ansible
    3. Execute following command to check if flask is running
        $ ps -ef | grep -i flask | grep -v grep
    4. If flask is not running, start the flask process
        $ ./start_flask_api_daemon.sh
    5. If flask is running, then it might be running on different port, change the port in following files if required
        /opt/ansible/app/common/config/flask_config.json
    6. Restart the flask process; kill the pid identified in step 2 and execute task listed in step 3

\n\n PS: Pls do not reply as this email is send from an unmonitored mailbox"
        """

        self.AUDIT_SCAN_LOG_ERROR_EMAIL_BODY = """
Attn: 

Can not determine scan log location !!!

Pls ensure scan log location is either passed or being correctly set in transmitScan process

\n\n PS: Pls do not reply as this email is send from an unmonitored mailbox"
        """
        # Postgres Sql
        self.GET_ALL_ROLES = """
            SELECT r.rolname, r.rolsuper, r.rolinherit,
              r.rolcreaterole, r.rolcreatedb, r.rolcanlogin,
              r.rolconnlimit, r.rolvaliduntil,
              ARRAY(SELECT b.rolname
                    FROM pg_catalog.pg_auth_members m
                    JOIN pg_catalog.pg_roles b ON (m.roleid = b.oid)
                    WHERE m.member = r.oid) as memberof
            , r.rolreplication
            , r.rolbypassrls
            FROM pg_catalog.pg_roles r
            WHERE r.rolname !~ '^pg_'
            ORDER BY 1
        """  

        self.COMPLIANCE_LIST_COLL = "compliance.lists"
        self.COMPLIANCE_EXCEP_COLL = "compliance.exception"
        self.PRODUCT_VERSION_COLL = "product.version"
        self.BOARDING_TASK_COLL = "boarding.tasks"
        self.ADMIN_LIST_COLL = "admins.list"

        self.SCAN_COLL = "scan"

        self.HOSTS_COLL = "hosts"
        self.HOST_USERS_COLL = "host.users"
        self.HOST_SCANS_COLL = "host.scans"
        self.HOST_CONFG_CHANGES_COLL = "host.config.changes"

        self.TENANTS_COLL = "tenants"
        self.TENANT_USERS_COLL = "host.users"
        self.TENANT_SCANS = "tenant.scans"
        self.TENANT_CONFG_CHANGES = "tenant.config.changes"
        self.TENANT_USERS_COLL = "tenant.users"

        self.TENANT_COMPLIANCE_COLL = "tenant.compliance"
        self.TENANT_AUDIT_OPEN = "tenant.audit.open"
        self.TENANT_AUDIT_CLOSE = "tenant.audit.close"
        
        self.MONGO_AUDITABLE_EVENTS = ""
        self.OS_USERS = ["mongo","postgres"]

        self.SCAN_HOST_FILE = "host_scan_{host}_{dt}.json"
        self.SCAN_TENANT_AUDIT_FILE = "tenant_audit_{host}_{tenant}_{dt}.json"

        self.STATUS_ACTIVE = self.active
        self.STATUS_DECOM = "Decomm"
        self.STATUS_VALID = "Valid"
        self.STATUS_OFFBOARD = "Off Boarded"
        self.STATUS_INACTIVE = self.inActiveStatus
        self.STATUS_ALIVE="alive"
        self.STATUS_NOTALIVE="dead"
        self.ANNUAL_RESTORE_TEST_TASK = "annual.restore.test"
        self.ANNUAL_DRTEST_TASK = "annual.dr.test"
        self.ANNUAL_OSUSER_PASS_CHANGE_TASK = "annual.osuser.pass.change"
        self.ANNUAL_DBUSER_PASS_CHANGE_TASK = "annual.dbuser.pass.change"
        self.ADHOC_DB_PASS_CHANGE = "adhoc.db.version.change"
        self.VALID_TENANT_ANNUAL_COMP_TASK = [self.ANNUAL_RESTORE_TEST_TASK, self.ANNUAL_DRTEST_TASK, self.ANNUAL_DBUSER_PASS_CHANGE_TASK, self.ADHOC_DB_PASS_CHANGE]
        self.VALID_ANNUAL_COMP_TASK = [self.ANNUAL_RESTORE_TEST_TASK, self.ANNUAL_DRTEST_TASK, self.ANNUAL_OSUSER_PASS_CHANGE_TASK, self.ANNUAL_DBUSER_PASS_CHANGE_TASK, self.ADHOC_DB_PASS_CHANGE]
        self.FREQUENCY_ANNUAL = "Annual"
        self.FREQUENCY_ANNUALY = "Annually"
        self.FREQUENCY_QUARTERLY = "Quarterly"
        self.FREQUENCY_MONTHLY = "Monthly"
        self.FREQUENCY_WEEKLY = "Weekly"
        self.FREQUENCY_DAILY = "Daily"
        self.VALID_FREQUENCY = [self.FREQUENCY_ANNUAL, self.FREQUENCY_ANNUALY, self.FREQUENCY_QUARTERLY, self.FREQUENCY_MONTHLY, self.FREQUENCY_WEEKLY, self.FREQUENCY_DAILY]
        self.HOST_USER_PASS_CHG_EVENT = "host.userpass.change"
        self.DB_USER_PASS_CHG_EVENT = "db.userpass.change"
        self.DR_TEST_EVENT = "db.dr.test"
        self.RESTORE_TEST_EVENT = "db.restore.test"

        # docker
        self.DOCKER_BIN_FILE = "/bin/docker"
        self.PG_CONF_FILES = {"confFile" : "postgresql.conf", "version" : ["9","10","11"]}
        self.templates = {
            "complianceList" : {
                "_id" : "<str, compliance_id>",
                "dbVendor" : "<str, mongo/postgres/mysql>",
                "descriptions" : "<str, description of compliance>",
                "scan": "<bool, compliance to be scanned>",
                "relaitveMethod" : 	"<dict {cls, method, param>",
                "frequency" : "<str, daily, weekly, monthly, quarterly, yearly>",
                "status" :	"<str, active/in-active>",
                "startDate" : "<datetime, start date of this scan",
                "endDate" :  "<datetime, end date of this scan",
                "_history" : [
                    {
                        "ts" : "<ts, timestamp>", 
                        "who" : "<str, who changed it (networkid)", 
                        "what" : "<str, what changed"
                    }
                ]                
            },
            "complianceException" : {
                "_id" : "<str, compliance id>",
                "ts" : "<ts, timestamp when dispensation is filed>",
                "supportingDoc": "<str, detailed documentation of exception filed, for e.g. change order and other evidence>",
                "startDate": "<dateTime, when this dispensation is in effect>",
                "endDate" : "<dateTime, when this dispensation expires, this could be used when an exception filed need to be renewed>",
                "exceptionList" : []
            },
            "productVersion": {
                "_id" : "<str, product name <mongo/postgres/mysql>",
                "version" : {
                    "baseVersion" : "<str, base released version of product>",
                    "latestVersion" : "<str, latest released version>"
                },
                "_history" : [
                    {
                        "ts" : "<ts, timestamp when a change was made>",
                        "who" : "<str, networkid of a person made this change> ",
                        "what" : "<str, what changes were made>"
                    }
                ]
            },
            "boardingTasks" : {
                "_id" : "<str, boarding.(on/off).id>",
                "name" : "<str, task name>",
                "type" : "<str, on-boarding/off-boarding",
                "_history" : [
                    {
                        "ts" : "<ts, timestamp when a change was made>",
                        "who" : "<str, networkid of a person made this change> ",
                        "what" : "<str, what changes were made>"
                    }
                ]
            },
            #/bin/adquery group <ctfy_group> -s
            #/bin/adquery user -A U1167965 | grep -i "displayname"
            # adminList.status = active -> inactiv -> inactive.open -> inactive.completed
            "adminList" : {
                "_id" : "<str, networkid>",
                "region" : "<str, apac/emea/nam/sam",
                "centrifyGroup" : "<array-string, centrify group this user is part of>",
                "lastName" : "<str, last name>",
                "firstName" : "<str, first name>",
                "fullName" : "<str, full name>",
                "opco" : [
                    "<str, operating company this user belongs to >"
                ],
                "vendorOrg" : "<str, vendor/partner organization, this is applicable for consultants only>",
                "onBoardingTS" : "<ts, when this use is on boarded>",
                "offBoardingTS" : "<ts, when this use is off boarded>",
                "isActive" : "<bool, is user active>",
                "onBoardingTasks" : [
                    {
                        "taskId" : "<str, boarding task id>", 
                        "ts" : "ts, when this task was updated", 
                        "who" : "str, networkid who provided this evidence",
                        "evidenceDoc" : "<str, change order or other document id>",
                        "comments" : "str, relevant comments on this task"
                    }
                ],
                "offBoardingTasks" : [
                    {
                        "taskId" : "<str, boarding task id>", 
                        "ts" : "ts, when this task was updated", 
                        "who" : "str, networkid who provided this evidence",
                        "evidenceDoc" : "<str, change order or other document id>",
                        "comments" : "str, relevant comments on this task"
                    }
                ]
            },
            "scan" : {
                "_id" : "<str, scanid>",
                "scanDate" : "<ts, timestamp when scan started>",
                "hosts" : [
                    {
                        "hostName" : "<str, host name>",
                        "startTs" : "<ts, when this host scan started>",
                        "endTs" : "<ts, when this host scan completed>"                    
                    }
                ],
                "tenants" : [
                    {
                        "tenantName" : "<str, tenant name>",
                        "hostName" : "<str, host name>",
                        "startTs" : "<ts, when this host scan started>",
                        "endTs" : "<ts, when this host scan completed"
                    }
                ],
                "firstHostScan" : "<str, host on which first scan performed>",
                "lastHostScan" : "<str, host on which last scan performed>",
                "firstScanStartTS" : "<ts, first scan start ts>",
                "firstScanStartTS" : "<ts, first scan end ts>",
                "status" : "<str, in-progress, closed>"
            },
            "hosts" : {
                "_id" : "<str, region.opco.hostName",
                "hostName" : "<str, hostname (fqdn>)",
                "scanId" : "<str, scan id to which this scan belongs to>",
                "scanDate" : "<date, scan date>",
                #"scanStartTS" : "<ts, scan start ts>",
                "opco" : "<str, opco>",
                "region" : "<str, region>",
                "domain" : "<str, corp/dmz>",
                "dcLocation" : "<str, datacenter location>",
                "ipAddress" : "<str, ipaddress>",
                "ipv6Address" : "<str, ipv6 address>",
                "bootTime" : "<list, all recorded boot time, we need last 10 boot time recorded>",
                "dbOSUsers" : "<list, all database os users and its details including password change history>",
                "os" : "<dict, os information, version/release/system/distribution>",
                "cpu" : "<dict, cpu details (count, avgload, time statistics>",
                "memory" : "<dict, physical memory details, total, used and available>",
                "swap" : "<dict, swap memory details, total, used and available>",
                "nicDetails" : "<list, all nic enterface and its stats/iocounters>",
                "sensors" : "<dict, all sensors available on this host, for e.g. battery, fans etc. >",
                "tenants" : "<list, all tenants on this host>",
                "tenantsSummary" : "<list, all tenants summary on this host>",
                "createdTS" : "<str, creation timestamp>",
                "lastUpdatedTS" : "<str, last updated timestamp>"                
            },
            "hostUsers": {
                "_id" : "<str, hostId>",
                "userId" : "<str, user id>",
                "primaryGroup" : "<str, primary group name of user>",
                "secondaryGroup" : "<str, primary group name of user>",
                "passwdHistory" : [
                    {
                        "ts" : "<ts, when password was changed>"   
                    }
                ]
            },
            "hostScan" : {                
                "_id" : "<ts, timestamp",
                "scanDate" : "<date, scan date>",
                "hostId" : "<str, region.opco.hostName>",
                "hostName" : "<str, hostname (fqdn)>",
                "opco" : "<str, opco>",
                "region" : "<str, region>",
                "domain" : "<corp, dmz>",
                "dcLocation" : "<str, datacenter location>",
                "ipAddress" : "<str, ipaddress>",
                "nicDetails" : [],
                "cpu" : {
                    "cpus" : "<int, total # of cpu>",
                    "cores" : "<int, total cores>",
                    "avgCpuLoad" : "<int>"  
                },
                "memory" : {
                    "total" : "<int, total physical memory in gb>",
                    "free" : "<int, used physical memory in gb",
                    "used" : "<int, used memory >"
                },
                "swap" : {
                    "total" : "<int, total swap allocated>",
                    "freeMemory" : "<int, used physical memory",
                    "usedMemory" : "<int, used memory>"
                    
                },
                "fs" : {
                    "name" : "<str, file system name>",
                    "lvName" : "<str, logival volume name>",
                    "partition" : "<str, partition name>",
                    "totalSpace" : "<int, total space in GB>",
                    "usedSpace" : "<int, used space in GB>",
                    "freeSpace" : "<int, free space in GB>"
                },
                "users" : [{
                    "name" : "<str, userid>",
                    "uid" : "<int, logival volume name>",
                    "gid" : "<int, secondary group>",
                    "comments" : "<str, when this user was created>",
                    "home" : "",
                    "shell" : "",
                    "lastPasswdChangeTS" : "<ts, last time password was changed>"
                }],
                "otherHWDetails" : {}
            },
            "hostConfigChanges" : {
                "_id" : "<str, hostId",
                "Name" : "hostName",
                "year" : "<int, year in which these change are accounted for",
                "change" :[
                    {
                        "scanId" : "<str, scan id which reported the change>",
                        "scanTs" : "<ts, scan timestamp>",
                        "component" : "<str, component which changed>",
                        "previousValue" : "<str, before image>",
                        "currentValue" : "<str, current image>"
                    }
                ]
            },
            "tenants" : {
                #"_id" : "<str,hostname.prodVendor.port",
                "opco" : "<opco>",
                "region" : "<region>",
                "dbTechnology" : "<dbTechnology>",
                "env" : "<env>",
                #"tenantName" : "<str, tenant name>",
                #"tenantType" : "<str, os/db>",
                #"tenantVendor" : "<str, vendor name i.e. mongo/postgres>",
                "instanceType" : "<str, mongo-rs/mongo-sa/postg-rep/postg-clu>",
                #"instanceName" : "<str, instance name",
                "members" :[],
                #"totalCompliance" : "<int, total compliance>",
                #"passedCompliance" : "<int, total pased compliance>",
                #"failedCompliance" : "<int, total failed compliance>",
                #"compliancePerc" : "<int, passed compliance percentage",
                "version" : "",
                "rsDetails" : "",
                "users" : [],
                "roles" : [],
                "databases" : [],
                "ha" : {},
                "dr" : {},
                "backup" : {},
                "usage" : "shared",
                "uri" : "",
                "compliance" : [],
                #"restoreDrillHist" : [
                #    {"restoreDate" : "", "supportingDoc" : "", "comments" : "", "who" : "", "ts" : ""}
                #],
                #"compliance": [
                #    {
                #        "complianceId" : "<str, compliance id>",
                #        "status" : "<str, passed/failed>"                        
                #    }
                #],
                "changeHistory" : [],
                #"bootHistory" : [], # we dont need it here, boot belongs to a node and a tenant may spreac on multiple nodes
                "scanId" : "<str, scanid to which latest update belongs to>",
                "scanDate" : "<date, scanDate to which latest update belongs to>",
                "createdTS" : "<ts, creation timestamp>",
                "lastUpdatedTS" : "<ts, last timestamp infromation was updated>"
            },
            "tenantVersion" : {
                "_id" : "<tenantId with port info>",
                "tenantName" : "tenantName",
                "tenantVendor" : "<str, vendor name i.e. mongo/postgres>",
                "hostId" : "",
                "hostName" : "",
                "versionHistory" : [{
                    "version" : "",
                    "scanDate" : "",
                    "supportingDocs" : "<co# or initial scan>",
                    "buildInfo" : {},
                }]
            },
            "tenantConfig" : {
                "_id" : "<tenantId with port info>",
                "tenantName" : "tenantName",
                "tenantVendor" : "<str, vendor name i.e. mongo/postgres>",
                "hostId" : "",
                "hostName" : "",
                "history" : [{
                    "config" : "",
                    "scanDate" : "",
                    "supportingDocs" : "<co# or initial scan>"
                }]
            },
            "tenantUsers" : {
                #"_id" : "<system generated id>",
                "tenantName" : "tenantName",
                "tenantVendor" : "<str, vendor name i.e. mongo/postgres>",
                "hostId" : "",
                "hostName" : "",
                "users" : [{
                    "userId" : "",
                    "user" : "",
                    "database" : "",
                    "assignedRoles" : [],
                    "scanDate" : "",
                    "supportingDocs" : "<we need relevant CA ticket>",
                    "passChangeHist" : []
                }]
            },
            "tenantRoles" : {
                #"_id" : "<tenantId with port info>",
                "tenantName" : "tenantName",
                "tenantVendor" : "<str, vendor name i.e. mongo/postgres>",
                "hostId" : "",
                "hostName" : "",
                "roles" : [{
                    "role" : "",
                    "users" : "",
                    "database" : "",
                    "assignedRoles" : [],
                    "scanDate" : "",
                    "supportingDocs" : "<we need relevant CA ticket>"
                }]
            },
            "tenantChanges" : {
                "_id" : "tenantId",
                "tenantName" : "<str, tenant name>",
                "tenantType" : "<str, os/db>",
                "intanceType" : "<str, mongo-rs/mongo-sa/postg-rep/postg-clu>",
                "instanceName" : "<str, instance name",
                "year" : "<int, in which chnage is recorded>",
                "versionHist" : [],
                "dbConfigHist" : [],
                "change" :[
                    {
                        "scanId" : "<str, scan id which reported the change>",
                        "scanTs" : "<ts, scan timestamp>",
                        "component" : "<str, component which changed>",
                        "previousValue" : "<str, before image>",
                        "currentValue" : "<str, current image>"
                    }
                ]
            },
            "tenantScan" : {
                #"_id" : "<str,ts>",
                "hostId" : "",
                "tenantId" : "<str,hostname.dbTech.port",
                "tenantName" : "tenantName",
                "tenantVendor" : "<str, vendor name i.e. mongo/postgres>",
                "tenantType" : "<str, os/db>",
                "instanceType" : "<str, mongo-rs/mongo-sa/postg-rep/postg-clu>",
                "instanceName" : "<str, instance name",
                "config" : "<dict, all configuration item for this tenant>",
                "buildInfo" : "",
                "users" :[
                    {
                        "userId" : "<str, userid>",
                        "grantedRoles" : "<str, granted roles>",
                        "grantedPrivs" : "<str, granted privs>"
                    }
                ],
                "roles" :[
                    {
                        "userId" : "<str, userid>",
                        "grantedRoles" : "<str, granted roles>",
                        "grantedPrivs" : "<str, granted privs>"
                    }
                ],
                "databases" : [
                    {
                        "db" : "<db name>",
                        "size" : "<db size>",
                        "totalObjects" : "<int, total objects>",
                        "objects" : [
                            {
                                "name" : "<object name",
                                "type" : "<object type>",
                                "size" : "<obj size>"
                            }
                        ]
                    }
                ]
            },
            "ctfyGrpUsers" : {
                #"_id" : "", 
                "users" : []
            },
            "dbTechnologyCompliance" : { # not sure if we need this
                "_id" : "mongo/postgres",
                "frequency" : "<quarterly/monthly/weekly>"

            },            
            "tenantCompliance" : {
                "tenantId" : "<str, tenantId>",
                "tenantName" : "<str, tenant name>",
                "tenantType" : "<str, os/db>",
                "tenantVendor" : "<str, vendor>", 
                "hostName" : "<str, hostName>",
                "hostId" : "<str, hostid>",
                "opco" : "<str, opco>",
                "region" : "<str region>",
                "dcLocation" : "<str region>",
                "ts" : "<ts, compliance timestamp>",
                "weekNum" : "<date, last day of week>",
                "weekStartDate" : "",
                "weekEndDate" : "",
                "total" : "<int, total compliance>",
                "nonCompCnt" : "<int, total non compliance>",
                "nonCompList" : "<int, total non compliance>",
                "atRiskCnt" : "<int, total at risk compliance>",                
                "atRiskList" : "<int, total at risk compliance>",                
                "inCompCnt" : "<int, total compliance in compliant>",
                "inCompList" : "<int, total compliance in compliant>",
                "compliances": [
                    {
                        "complianceId" : "<str, compliance id>",
                        "reportedOn" : "<datetime, datetime>",
                        "status" : "<str, pending/passed/failed>",
                        "result" : "<str, result of compliance>",
                        "closedBy" : "<str, networkid>",
                        "closedTs" : "<ts, timestamp>",
                        "comments" : "<str, user comments>"
                    }
                ]
            },
            "tenant.audit.open" : {
                #"_id" : "<str, auditid, mmddyyyy_seq#>",
                "auditEvent" : "<str, audit event>",
                "status" : "<str, status (open --> wip --> closed)",
                "evidenceDoc" : "<str, evidence for this audit>",
            },
            "tenant.audit.close" : {},
            "tenantUsers" : {
                "userId" : "<str, userid>",
                "userCreationTS" : "<ts, user creation timestamp>",
                "privileges" :[{
                    "ts" : "<ts, when privilege is granted, if this can not be determined then scan ts shall be used>",
                    "grantedRoles" : [],
                    "grantedPrivs" : []
                }]
            }            
        }
        self.OS_CMD = {
            "GET_ALL_MONGO_CONF_FILES" : "ps -eaf | grep -i 'mongod -f ' | grep -v grep | awk '{print $10}' " ,
            "GET_EXEC_PATH" : "/bin/readlink -f /proc/{pid}/exe",
            "GET_CTFY_MEMBER" : "/bin/adquery group -s {ctfy_grp}",
            "GET_MEMBER_NAME" : "/bin/adquery user -A {userid} | grep -i 'displayname' | cut -f2 -d: ",
            "LAST_PASSWORD_CHANGE_DATE" : "/usr/bin/histmongo.sh {user} | grep -i 'Last password change' | cut -d ':' -f2",
            "FIND_ALL_MONGOD_DOCKER_CONTAINER" : "".join([self.DOCKER_BIN_FILE, ' ps --format "{{.Names}}{{.Commands}}"']),
            "GET_ALL_ALIVE_PG" : "pgrep -u postgres -fa -- -D",
            "GET_ALL_ALIVE_PG_PID" : "pgrep -u postgres -fa -- -D | awk '{print $1}'", 
            "GET_ALL_ALIVE_PG_BIN" : "pgrep -u postgres -fa -- -D | awk '{print $2}'",
            "GET_ALL_ALIVE_PG_CONF_LOC" : "pgrep -u postgres -fa -- -D | awk '{print $4}'",            
        }
        
        self.MONGO_CTFY_GROUP = [
            "CTFY-UG_NA_Marsh_dba-S-L",
            "CTFY-UG_GLB_Marsh_MGDB_Cont-S-L",
            "CTFY-UG_APAC_Marsh_dba-S-L",
            "CTFY-UG_GLB_Marsh_dba.lnt-S-L",
            "CTFY-UG_GLB_Marsh_PG_Cont-S-L"
        ]

        #self.AD_GROUP_ROLE_KW = ["OU=User Role Groups","OU=Groups - Applications","CN="]


if __name__ == "__main__":
    pass

"""
// tenant.audit.open
	_id
	auditEvent
	acknowledged
	acknowledgedBy
	suppDocs
	status	(open -> wip -> closed)
	_history [{}] 			(will store hostory of event happened to this audit events)

// tenant.audit.close
	_id
	auditEvent
	acknowledged
	acknowledgedBy
	suppDocs

	status	(open -> wip -> closed)
	_history [{}] 			(will store hostory of event happened to this audit events)

"""
