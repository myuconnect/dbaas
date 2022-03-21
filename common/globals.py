from com.mmc.common.singleton import Singleton

import datetime, os, psutil

class Globals(object, metaclass=Singleton):
    def __init__(self):
        '''
        Deploy Status :
                Pending --> In-Progress --> UnSuccess/Success
                Rollback Ready --> Rollback, In-progress --> Rollback, Success/Rollback, UnSuccess
        '''
        """
        LDAP Config
        """
        self.LDAP_SERVER_CONFIG = {
            "CORP" : {
                "user" : "CORP\\svc-dev-deploy-app",
                "userPass" : "rSa3mc7%#sfasMBQZ"
            },
            "DMZPROD01" : {
                "user" : "DMZPROD01\\svc-prd-deploy-app",
                "userPass" : "rSa3mc7%#sfasMBQZ"            
            }
        }
        self.componentDB = [{"repository" : "mongo"}]
        self.dbTypeMongo = "mongo"
        self.DB_TYPE_MONGO = "mongo"
        self.DB_TYPE_POSTGRES = "postgres"

        self.validDbTypes = [self.DB_TYPE_MONGO, self.DB_TYPE_POSTGRES]

        self.deploy = "deploy"
        self.rollback = "rollback"
        self.removeTask = "removeTask"
        self.jira = "jira"

        self.open = "Open"
        self.closed = "Closed"
        self.frozen = "Frozen"
        self.success = 'Success'
        self.unsuccess = 'UnSuccess'
        self.ready = "Ready"
        self.inprogress = 'InProgress'
        self.pending = "Pending"
        self.buildInprogress = "BuildInprogress"
        self.error = "Error"

        self.opDeploy = "".join([self.deploy, ".", self.deploy])
        self.opRemoveTask = "".join([self.deploy, ".", self.removeTask])
        self.opRollback = "".join([self.deploy, ".", self.rollback])
        self.allDeployOperation = [self.opDeploy, self.opRemoveTask, self.opRollback]

        self.jiraInEnvStateOpen = "".join([self.jira, ".", self.open])
        self.jiraInEnvStateClosed = "".join([self.jira, ".", self.closed])
        self.jiraInEnvStateFrozen = "".join([self.jira, ".", self.frozen])

        self.deployPending = "".join([self.deploy, ".", self.pending])
        self.deployInprogress = "".join([self.deploy, ".", self.inprogress])
        self.deploySuccess = "".join([self.deploy, ".", self.success])
        self.deployUnsuccess = "".join([self.deploy, ".", self.unsuccess])
        self.successFrozen = "".join([self.success, ".", self.frozen])
        self.rollbackBuildInProg = "".join([self.rollback, ".", self.buildInprogress])
        self.rollbackReady = "".join([self.rollback, ".", self.ready])
        self.rollbackInprogress = "".join([self.rollback, ".", self.inprogress])
        self.rollbackUnsuccess = "".join([self.rollback, ".", self.unsuccess])
        self.rollbackSuccess = "".join([self.rollback, ".", self.success])
        self.grant="Grant"
        self.deny="Deny"

        self.deployValidStatus = [
                self.deployPending,
                self.deployInprogress,
                self.deploySuccess,
                self.deployUnsuccess,
                self.successFrozen,
                self.rollbackBuildInProg,
                self.rollbackReady,
                self.rollbackInprogress,
                self.rollbackUnsuccess,
                self.rollbackSuccess
                    ]

        self.defaultDateTimeMsFormat = "%Y-%m-%d %H:%M:%S.%f"
        self.defaultDateTimeFormat = "%Y-%m-%d %H:%M:%S.%f"
        #self.defaultDateTimeFormat = "%m/%d/%Y %H:%M:%S"

        self.validTaskDeployStatus = [
            self.success,
            self.unsuccess,
            self.inprogress,
            self.deployInprogress,
            self.deployUnsuccess,
            self.deploySuccess,
            self.rollbackInprogress,
            self.rollbackSuccess,
            self.rollbackUnsuccess
        ]

        self.outputStdout = "stdout"
        self.outputStdoutNFile = "both"
        self.outputFile = "file"
        self.deployTaskSchema = {
         }
        self.mongoCollection = "collection"
        self.mongoDb = "db"
        self.mongoDocument = "document"
        self.deploySchema = {
                "$schema" : "http://json-schema.org/draft-06/schema#",
                "title" : "schema for deployment validation",
                "id" : "/DeployDataMain",
                "type" : "object",
                "definitions" : {
                        "createCollection" : {
                                ""
                        }
                },
                "required" : ["changeOrder","submittedTs","scheduleWindow","prevEnvChgOrder","descriptions","targetEnv","prevEnv", "targetDBType","instType","instName","tasks"],
                "properties" : {
                        "changeOrder" : {"type" : "string"},
                        #"submittedBy" : {"type" : "string"},
                        "submittedTs" : {"type" : "string"},
                        "scheduleWindow" : {"type" : "array"},
                        "prevEnvChgOrder" : {"type" : "string"},
                        "descriptions" : {"type" : "string"},
                        "targetEnv" : {"type" : "string"},
                        "prevEnv" : {"type" : "string"},
                        "targetDBType" : {"type" : "string"},
                        "instType" : {"type" : "string"},
                        "instName" : {"type" : "string"},
                        "tasks" : {"type" : "array"}
                }
            }
        self.template = {
            "mongoURiLdapTemplate" : "mongodb://{userName}:{userPass}@{hosts}/?authMechanism=PLAIN&connectTimeoutMS=300000&serverSelectionTimeoutMS=500000&w=majority",
            "mongoUriReplTemplate" : "mongodb://{userName}:{userPass}@{hosts}/?authSource={authDb}&connectTimeoutMS=300000&serverSelectionTimeoutMS=500000&w=majority&readPreference=primary&replicaSet={replSet}",
            "mongoUriTemplate" : "mongodb://{userName}:{userPass}@{hosts}/?authSource={authDb}&authMechanism={authMech}&serverSelectionTimeoutMS=500000&w=majority&readPreference=primary",
            "response" : {
                    "status" : "unsuccess>",
                    "message" : "",
                    "data" : ""
            },
            "mongoUriReplTemplate__" : "mongodb://{userName}:{userPass}@{replSet}/{hosts}/?authSource=admin&connect=true&serverSelectionTimeoutMS={timeOutMs}&w=majority&r",
            "mongoUriTemplate_" : "mongodb://{userName}:{userPass}@{hosts}/?authSource=admin&connect=true&serverSelectionTimeoutMS={timeOutMs}&w=majority",
            "runStatsTemplate" : {
                    "ts" : "",
                    "pid" : "",
                    "arguments" : "",
                    "status" : self.inprogress,
                    "comments" : ""
            },
            "objStatsTemplate" : {
                    #env.app.dbtype.dbInstance.database.parentobject.objecttype.objectname
                    "env" : "",
                    "appName" : "",
                    "databaseType": "",
                    "dbInstance" : "",
                    "database" : "",
                    "objectType" : "",
                    "objectName" : "",
                    "parentObject" : "",
                    "additionalInfo" : "",
                    "firsChangeTS" : "",
                    "lastChangeTS" : "",
                    "changes": []
            },
            "objStatsChangeTemplate" : {
                    "JiraKey": "",
                    "deployDocId": "",
                    "deployOperation": "",
                    "taskOperation" : "",
                    "requestor": "",
                    "description" : "",
                    "beforeImage" : "",
                    "additionalInfo" : "",
                    "ts" : "",

            },
            "changeOrderTemplate" : {
                    "changeOrder" : "<change order #>",
                    #"submittedBy" : "<useer submitted change order>",
                    "submittedTs" : "<when change order was submitted>",
                    "scheduleWindow" : "<schedule_window in tuple>",
                    "prevEnvChgOrder" : "<previous change order #>",
                    "descriptions" : "<description of change order",
                    "targetEnv" : "<target env of this change order>",
                    "prevEnv" : "<which previous environment this change was deployed>",
                    "targetDBType" : "<target database type>",
                    "instType" : "<instance type (replica set/shard)",
                    "instName" : "<instance name>",
                    "tasks" : []
            },
            "deployDocSummary" : {
                    "_id": "{jiraKey}",
                    "app" : "",
                    "targetDBType" : "",
                    "description" : "{description}",
                    "status": "{status}",
                    "envState" : [{"env": "dev", "state" : "open"}],
                    "deployment" : [],
                    "deployHistory" : []
            },
            "deployStats" : {
                    "ts" : "",
                    "clientIpAddress" : "",
                    "authUser" : "",
                    "authPass" : "",
                    "arguments" : {},
                    "accessGranted" : ""
            },
            "deployDocDetail" : {
                    "_id": "{deployDocId}",
                    "jiraKey" : "{jiraKey}",
                    "requestedBy" : "{jiraUser}",
                    "jiraTs" : "{jiraTs}",
                    "appName" : "",
                    "targetDBType" : "",
                    "targetInstance" : "",
                    "description" : "{description}",
                    "changeDetail": {},
                    "status": "{status}",
                    "startTime": "{startTs}",
                    "endTime": "{endTs}",
                    "nexusSignature" : "",
                    "attempts": 0,
                    "rollback": {
                            "ts" : "",
                            "requestedBy" : "",
                            "reason" : "",
                            "status": self.rollbackBuildInProg,
                            "startTime": "",
                            "endTime": "",
                            "duration": "",
                            "tasks": []
                    },
                    "tasks" : [],
                    "eventLogs": [],
                    "attemptHistory" : [],
                    "backupDetails":[],
                    "_taskObjExistence" : False
            },
            "attemptHistory" : {
                    "attemptId": 0,
                    "requestedBy" : "",
                    "executedBy" : "",
                    "status": "",
                    "startTime": "",
                    "endTime": "",
                    "duration": "",
                    "tasks": []
            },
            "rollBackTask" : {
                    "taskId" : "",
                    "ts" : "",
                    "status" : "",
                    "waitSeconds" : "",
                    "skipOnError" : True,
                    "startTime": "",
                    "endTime": "",
                    "comment" : ""
            },
            "appTemplate" : {
                "_id": "pyament_engine",
                "appName": "Payment Engine",
                "database": [
                    {
                        "vendor": "mongo",
                        "name": "",
                        "aws": "",
                        "dbInstance": "",
                        "currentDBSize": ""
                    }
                ],
               "auth": [
                    {
                        "mongo": {
                           "adGroup": {
                                "dev": {
                                    "rADGroup": "<str, read only dev adgroup name>",
                                    "rwADGroup": "<str, read write dev adgroup name>",
                                    "whiteListIPCIDR": "array/string, list of ipaddress or CIDR allowed"
                                },
                                "uat": {
                                    "rADGroup": "<str, read only dev adgroup name>",
                                    "rwADGroup": "<str, read write uat adgroup name>",
                                    "whiteListIPCIDR": "array/string, list of ipaddress or CIDR allowed"
                                },
                                "prod": {
                                   "rADGroup": "<str, read only prod adgroup name>",
                                   "rwADGroup": "<str, read write prod adgroup name>",
                                   "whiteListIPCIDR": "array/string, list of ipaddress or CIDR allowed"
                                }
                            }
                        }
                    }
                ],
                "owner": {
                    "appOwner": "<str, application owner name>",
                    "appOwnerDL": "<str, app owner DL>",
                    "businessOwner": "<str, business owner name>",
                    "businessOwnerDL": "<str, business owner DL>",
                    "lob": "<str, line of business>"
                },
                "support": {
                    "appSupportGroup": "<str, application support group>",
                    "appSupportEmail": "<str, application support email address>",
                    "aesSupportGroupDL": "<str, AES support group email address>"
                },
                "data": {
                    "sensitiveData": "<bool>",
                    "sensitiveDataCategory": "<str, sensitive data category i.e. PHI, PCI>",
                    "backupRetentionPolicy": "<int, months>",
                    "dataRetentionPolicy": "<int, data retention policy months>",
                    "archivalDataRetentionPolicy": "<int, data retention policy months>",
                    "region": "<str, region i.e. NAM/EMEA/APAC>",
                    "expectedDBSize": "<int, in GB>",
                    "monthlyGRowth": "<int, monthly growth in percentage>"
                }
            }
        }

        self.maxDeployAttempt = 5
        # Mongo
        self.srvrSelTimeoutMS = "serverSelectionTimeoutMS"

        # lambda functions
        self.getCurrentDateTime = lambda : str(datetime.datetime.now())
        self.isvalidDir = lambda path: os.path.isdir(path)
        self.isFileExists = lambda fileName: os.path.isfile(fileName)
        self.buildPath = lambda path, fileName: os.path.join(path, fileName)
        self.getCurrentDir = lambda : os.getcwd()

        # lambda functions environment
        self.getAllEnv = lambda : os.environ
        self.getEnvKeyVal = lambda key: os.getenv(key)
        #self.setEnvKeyVal = lambda key, value: os.environ[key] = value ## cant assign value in lambda function

        # lambda process functions
        self.getCurrentPID = lambda : os.getpid()
        self.getAllPID = lambda : psutil.pids()
        self.getParentPID = lambda : psutil.Process(os.getpid()).ppid()
        self.isPidExists = lambda : psutil.pid_exists(processId)

        # return tuples (pid, name, started)
        self.getCurrentProcDetail = lambda : psutil.Process(os.getpid())

        # Mongo tools
        # staging dir >>> /var/backups/mongobackups/`date +"%m-%d-%y"`
        # delete 7 days old backup find /var/backups/mongobackups/ -mtime +7 -exec rm -rf {} \;
        '''
        "backup_mongod_base_ldap" : "{mongoBackup} -h \"{hosts}\" -u \"{userName}\" -p \"{userPass}\" --authenticationDatabase \"{authDb}\" --authentica
tionMechanism \"{authMode}\" --out \"{backupDir}\" --gzip ",
        "backup_mongod_full_ldap" : "{mongoBackup} -h \"{hosts}\" -u {userName} -p {userPass} --authenticationDatabase {authDb} --authenticationMechanis
m {authMode} --out {backupDir} --dumpDbUsersAndRoles --gzip --oplog > {logFile} 2> {errorFile}",
        "backup_mongod_db_ldap" : "{mongoBackup} -h \"{hosts}\" -u {userName} -p {userPass} --authenticationDatabase {authDb} --authenticationMechanism
{authMode} -d {dbName} --out {backupDir} --dumpDbUsersAndRoles --gzip > {logFile} 2> {errorFile}",
        "backup_mongod_collection_ldap" : "{mongoBackup} -h \"{hosts}\" -u {userName} -p {userPass} --authenticationDatabase {authDb} --authenticationMe
chanism {authMode} -d {dbName} -c {collectionName} --out {backupDir} --dumpDbUsersAndRoles --gzip --oplog > {logFile} 2> {errorFile}",
        "backup_mongod_query_ldap" : "{mongoBackup} -h \"{hosts}\" -u {userName} -p {userPass} --authenticationDatabase {authDb} --authenticationMechani
sm {authMode} -d {dbName} -c {collectionName} -q {queryJson} --out {backupDir} --dumpDbUsersAndRoles --gzip --oplog > {logFile} 2> {errorFile}",
'''
        self.mongoUtil = {
            "linux" : {
                "backup" : {
                    "backup_mongod_base" : "{mongoBackup} --host {hosts} --username {userName} --password {userPass} --authenticationDatabase {authDb} --authenticationMechanism {authMode} --out {backupDir} ",
                    "backup_mongod_full" : "{mongoBackup}  -h \"{hosts}\" -u {userName} -p {userPass} --authenticationDatabase {authDb} --authenticationMechanism {authMode} --out {backupDir} --dumpDbUsersAndRoles --gzip --oplog > {logFile} 2> {errorFile}",
                    "backup_mongod_db" : "{mongoBackup} -h \"{hosts}\" -u {userName} -p {userPass} --authenticationDatabase {authDb} --authenticationMechanism {authMode} -d {dbName} --out {backupDir} --dumpDbUsersAndRoles --gzip > {logFile} 2> {errorFile}",
                    "backup_mongod_collection" : "{mongoBackup} -h \"{hosts}\" -u {userName} -p {userPass} --authenticationDatabase {authDb} --authenticationMechanism {authMode} -d {dbName} -c {collectionName} --out {backupDir} --dumpDbUsersAndRoles --gzip --oplog > {logFile} 2> {errorFile}",
                    "backup_mongod_query" : "{mongoBackup} -h \"{hosts}\" -u {userName} -p {userPass} --authenticationDatabase {authDb} --authenticationMechanism {authMode} -d {dbName} -c {collectionName} -q {queryJson} --out {backupDir} --dumpDbUsersAndRoles --gzip --oplog > {logFile} 2> {errorFile}",
                    "backup_restore_db" : "{mongo_home}mongobackup --uri {mongo_uri} --gzip --archive --dumpDbUsersAndRoles -| {mongo_home}/.mongorestore --uri {mongo_uri} --drop ",
                    "example" : "mongodump --archive --db test --port 27017 | mongorestore --archive --port 27018"
                },
                "restore" : {
                    # restore everything from backup
                    "restore_mongod_base" : "{mongoRestore} --host {hosts} --username {userName} --password {userPass} --authenticationDatabase {authDb} --authenticationMechanism {authMode} --stopOnError",
                    "backupRestore" : {"backup_restore_cmd" : ""},
                    "backupRestore" : {
                        # restore everything from backup
                        "backup_restore_mongod_base" : "{mongoBackup} --host {hosts} --username {userName} --password {userPass} --authenticationDatabase {authDb} --authenticationMechanism {authMode} -- archive | --host {hosts} --username {userName} --password {userPass} --authenticationDatabase {authDb} --authenticationMechanism {authMode} --stopOnError"
                    }
                }
            },
            "windows" : {
                "backup" : {
                    "backup_mongod_base" : "{mongoBackup} --host \"{hosts}\" /u {userName} /password \"{userPass}\" /authenticationDatabase '{authDb}'  /authenticationMechanism {authMode} /out {backupDir} ",
                    "backup_mongod_full" : "{mongoBackup} --host \"{hosts}\" /u {userName} /p {userPass} /authenticationDatabase {authDb} --authenticationMechanism {authMode} /out {backupDir} /dumpDbUsersAndRoles /gzip /oplog > {logFile}",
                    "backup_mongod_db" : "{mongoBackup} --host \"{hosts}\" /u {userName} /p {userPass} /authenticationDatabase {authDb} --authenticationMechanism {authMode} /d {dbName} /out {backupDir} /dumpDbUsersAndRoles /gzip > {logFile}",
                    "backup_mongod_collection" : "{mongoBackup} -host \"{hosts}\" /u {userName} /p {userPass} /authenticationDatabase {authDb} --authenticationMechanism {authMode} -d {dbName} -c {collectionName} --out {backupDir} --dumpDbUsersAndRoles --gzip --oplog > {logFile}",
                    "backup_mongod_query" : "{mongoBackup} --host \"{hosts}\" /u {userName} /p {userPass} /authenticationDatabase {authDb} /authenticationMechanism {authMode} /d {dbName} -c {collectionName} -q \"{queryJson}\" /out {backupDir} > {logFile}",
                    "backup_restore_db" : "{mongo_home}mongobackup --uri {mongo_uri} --gzip --archive --dumpDbUsersAndRoles -| {mongo_home}/.mongorestore --uri {mongo_uri} --drop "
                },
                "restore" : {
                    "restore_mongod_base" : "{mongoRestore} -h {hosts} /u {userName} /p {userPass} /authenticationDatabase {authDb} /authenticationMechanism{authMode} /stopOnError /dir {dir}"
                }
            }
        }

        self.INDEX_CREATION_BACKGROUND=True
        self.BACKUP_FULL = "fullBackup"
        self.BACKUP_NS = "nsBackup"
        self.BACKUP_DB = "dbBackup"
        self.BACKUP_COLLECTION = "collBackup"
        self.BACKUP_QUERY = "queryBackup"

        self.MONGO_DEPLOY_LOAD_JSONFILE = ""

        self.MONGO_OP_COPY_DATA = "copyData"
        self.MONGO_OP_COPY_NS = "copyNameSpace"
        self.MONGO_OP_BACKUP_NS = "backupNameSpace"
        self.MONGO_OP_RESTORE_NS = "restoreNameSpace"
        self.MONGO_OP_CREATE_COLLECTION = "createCollection"
        self.MONGO_OP_RENAME_COLLECTION = "renameCollection"
        self.MONGO_OP_RENAME_COLL_FIELDS = "renameCollFields"
        self.MONGO_OP_DROP_COLLECTION = "removeCollection"
        self.MONGO_OP_TRUNCATE_COLLECTION = "truncateCollection"
        self.MONGO_OP_COPY_COLLECTION = "copyCollection"
        self.MONGO_OP_INSERT_DOCUMENT_DATAFILE = "insertDocumentDataFile"
        self.MONGO_OP_INSERT_DOCUMENT = "insertDocument"
        self.MONGO_OP_UPDATE_DOCUMENT = "updateDocument"
        self.MONGO_OP_DELETE_DOCUMENT = "deleteDocument"
        self.MONGO_OP_DELETE_DOCUMENT_DATAFILE = "deleteDocumentDataFile"
        self.MONGO_OP_BACKUP_DOCUMENT = "restoreDocument"
        self.MONGO_OP_RESTORE_DOCUMENT = "restoreDocument" # restore document from backup
        self.MONGO_OP_RENAME_DATABASE = "renameDatabase"
        self.MONGO_OP_COPY_DATABASE = "copyDatabase"
        self.MONGO_OP_DROP_DATABASE = "dropDatabase"
        self.MONGO_OP_BACKUP_DATABASE = "backupDatabase"
        self.MONGO_OP_RESTORE_DATABASE = "restoreDatabase"
        self.MONGO_OP_CREATE_INDEX = "createIndex"
        self.MONGO_OP_DROP_INDEX = "dropIndex"
        self.MONGO_OP_BACKUP_COLLECTION = "backupCollection"
        self.MONGO_OP_RESTORE_COLLECTION = "restoreCollection"
        self.MONGO_OP_CREATE_ROLE = "createRole"
        self.MONGO_OP_DO_NOTHING = "doNothing"

        self.MONGO_PLACE_HOLDER_ENV_OP = {"dev" : [self.MONGO_OP_COPY_NS]}

        self.MONGO_OP_LIST = [
                self.MONGO_OP_COPY_DATA,
                self.MONGO_OP_COPY_NS,
                self.MONGO_OP_BACKUP_NS,
                self.MONGO_OP_RESTORE_NS,
                self.MONGO_OP_CREATE_COLLECTION,
                self.MONGO_OP_RENAME_COLLECTION,
                self.MONGO_OP_RENAME_COLL_FIELDS,
                self.MONGO_OP_DROP_COLLECTION,
                self.MONGO_OP_TRUNCATE_COLLECTION,
                self.MONGO_OP_COPY_COLLECTION,
                self.MONGO_OP_INSERT_DOCUMENT_DATAFILE,
                self.MONGO_OP_INSERT_DOCUMENT,
                self.MONGO_OP_UPDATE_DOCUMENT,
                self.MONGO_OP_DELETE_DOCUMENT,
                self.MONGO_OP_DELETE_DOCUMENT_DATAFILE,
                self.MONGO_OP_RENAME_DATABASE,
                self.MONGO_OP_COPY_DATABASE,
                self.MONGO_OP_DROP_DATABASE,
                self.MONGO_OP_BACKUP_DATABASE,
                self.MONGO_OP_RESTORE_DATABASE,
                self.MONGO_OP_CREATE_INDEX,
                self.MONGO_OP_DROP_INDEX,
                self.MONGO_OP_BACKUP_COLLECTION,
                self.MONGO_OP_RESTORE_COLLECTION,
                self.MONGO_OP_DO_NOTHING,
                self.MONGO_OP_CREATE_ROLE
        ]

        self.OPERATION = {
            "mongo" : {
                self.MONGO_OP_COPY_DATA : {
                        "op" : self.MONGO_OP_COPY_DATA,
                        "backupType" : self.BACKUP_NS,
                        "comments" : "backup source database",
                        "rollbackOp" : self.MONGO_OP_RESTORE_NS
                },
                self.MONGO_OP_COPY_NS : {
                        "op" : self.MONGO_OP_COPY_NS,
                        "backupType" : self.BACKUP_NS,
                        "comments" : "backup source database",
                        "rollbackOp" : self.MONGO_OP_RESTORE_NS
                },
                self.MONGO_OP_COPY_DATABASE : {
                        "op" : self.MONGO_OP_COPY_DATABASE,
                        "backupType" : self.BACKUP_DB,
                        "comments" : "backup source database",
                        "rollbackOp" : self.MONGO_OP_BACKUP_DATABASE
                },
                self.MONGO_OP_BACKUP_DATABASE : {
                        "op" : self.MONGO_OP_BACKUP_DATABASE,
                        "backupType" : "",
                        "comments" : "backup source database, if available",
                        "rollbackOp" : ""
                },
                self.MONGO_OP_RESTORE_DATABASE : {
                        "op" : self.MONGO_OP_RESTORE_DATABASE,
                        "backupType" : self.BACKUP_DB,
                        "comments" : "restore database",
                        "rollbackOp" : self.MONGO_OP_BACKUP_DATABASE
                },
                self.MONGO_OP_COPY_COLLECTION : {
                        "op" : self.MONGO_OP_COPY_DATABASE,
                        "backupType" : self.BACKUP_COLLECTION,
                        "comments" : "backup source database",
                        "rollbackOp" : self.MONGO_OP_RESTORE_COLLECTION
                },
                self.MONGO_OP_BACKUP_COLLECTION : {
                        "op" : self.MONGO_OP_BACKUP_DATABASE,
                        "backupType" : "",
                        "comments" : "backup source database, if available",
                        "rollbackOp" : ""
                },
                self.MONGO_OP_RESTORE_COLLECTION : {
                        "op" : self.MONGO_OP_RESTORE_DATABASE,
                        "backupType" : self.BACKUP_COLLECTION,
                        "comments" : "restore database",
                        "rollbackOp" : self.MONGO_OP_BACKUP_COLLECTION
                },
                self.MONGO_OP_CREATE_COLLECTION : {
                        "op" : self.MONGO_OP_CREATE_COLLECTION,
                        "backupType" : "",
                        "comments" : "create collection",
                        "rollbackOp" : self.MONGO_OP_DROP_COLLECTION
                },
                self.MONGO_OP_RENAME_COLLECTION : {
                        "op" : self.MONGO_OP_RENAME_COLLECTION,
                        "backupType" : "",
                        "comments" : "rename collection",
                        "rollbackOp" : self.MONGO_OP_RENAME_COLLECTION
                },
                self.MONGO_OP_DROP_COLLECTION : {
                        "op" : self.MONGO_OP_DROP_COLLECTION,
                        "backupType" : self.BACKUP_COLLECTION,
                        "comments" : "drop collection",
                        "rollbackOp" : self.MONGO_OP_RESTORE_COLLECTION
                },
                self.MONGO_OP_RENAME_COLL_FIELDS : {
                        "op" : self.MONGO_OP_RENAME_COLL_FIELDS,
                        "backupType" : "",
                        "comments" : "rename collection field(s)",
                        "rollbackOp" : self.MONGO_OP_RENAME_COLL_FIELDS
                },
                self.MONGO_OP_CREATE_INDEX : {
                        "op" : self.MONGO_OP_CREATE_INDEX,
                        "backupType" : "",
                        "comments" : "create index",
                        "rollbackOp" : self.MONGO_OP_DROP_INDEX
                },
                self.MONGO_OP_INSERT_DOCUMENT : {
                        "op" : self.MONGO_OP_INSERT_DOCUMENT,
                        "backupType" : "",
                        "comment" : "insert document",
                        "rollbackOp" : self.MONGO_OP_DELETE_DOCUMENT
                },
                self.MONGO_OP_INSERT_DOCUMENT_DATAFILE : {
                        "op" : self.MONGO_OP_INSERT_DOCUMENT_DATAFILE,
                        "backupType" : "",
                        "comment" : "insert document",
                        "rollbackOp" : self.MONGO_OP_DELETE_DOCUMENT_DATAFILE
                },
                self.MONGO_OP_UPDATE_DOCUMENT : {
                        "op" : self.MONGO_OP_UPDATE_DOCUMENT,
                        "backupType" : self.BACKUP_QUERY,
                        "comment" : "update document",
                        "rollbackOp" : self.MONGO_OP_RESTORE_DOCUMENT
                },
                self.MONGO_OP_DELETE_DOCUMENT : {
                        "op" : self.MONGO_OP_DELETE_DOCUMENT,
                        "backupType" : self.BACKUP_QUERY,
                        "comment" : "delete document",
                        "rollbackOp" : self.MONGO_OP_RESTORE_DOCUMENT
                },
                self.MONGO_OP_RESTORE_DOCUMENT : {
                        "op" : self.MONGO_OP_RESTORE_DOCUMENT,
                        "backupType" : "",
                        "comment" : "restore document",
                        "rollbackOp" : ""
                }
            }
        }

        #       MongoUpdateData = "update_data"
        #self.MONGO_DELETE_DATA_OP = "delete_data"
        #self.MONGO_CREATE_INDEX_OP = "create_index"
        self.DISPLAY_TASK_HEADING_START = """"

        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ 
        Task                                                                            | Status     
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        """
        self.DISPLAY_TASK_HEADING_END =   """

        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ 
        """
        self.DBTYPE_MONGO = "mongo"
        self.VALID_DEPLOYDB_TYPE = [self.DBTYPE_MONGO]

        # deploy variable
        self.DEPLOY_VAR = {}
        self.ARG_SEP = ","

        self.MONGO_OBJ_TYPE_COLLECTION = "collection"
        self.MONGO_OBJ_TYPE_COLLECTION_CAPPED = "capped collection"
        self.MONGO_OBJ_TYPE_DB = "database"
        self.MONGO_OBJ_TYPE_INDEX = "index"

        self.devEnv = "dev"
        self.stagingEnv = "staging"
        self.uatEnv = "uat"
        self.prodEnv = "prod"

        self.allEnv = ["dev","uat","prod"]

        self.envMapping = {
                self.dbTypeMongo : {
                        "prod" : [self.uatEnv],
                        "uat" : [self.devEnv],
                        "dev" : []
                }
        }

        # we need a way to customize application's deployment workflow/envmapping

        self.jiraEnv = {
                "dev" :  {
                        "deploy.deploy" : {
                                self.success : "DEV Deploy Successful", self.unsuccess: "DEV Deploy Failed"
                        },
                        "deploy.removeTask" : {
                                self.success : "DEV Deploy Successful", self.unsuccess: "DEV Deploy Failed"
                        },
                        "deploy.rollback" : {
                                self.success : "Rollback (DEV) Success", self.unsuccess: "Rollback (DEV) Failed"
                        }
                },
                "uat" :  {
                        "deploy.deploy" : {
                                self.success : "STAGE Deploy Successful", self.unsuccess: "STAGE Deploy Failed"
                        },
                        "deploy.removeTask" : {
                                self.success : "STAGE Deploy Successful", self.unsuccess: "STAGE Deploy Failed"
                        },
                        "deploy.rollback" : {
                                self.success : "Rollback (STAGE) Success", self.unsuccess: "Rollback (STAGE) Failed"
                        }
                },
                "prod" :  {
                        "deploy.deploy" : {
                                self.success : "PROD Deploy Successful", self.unsuccess: "PROD Deploy Failed"
                        },
                        "deploy.removeTask" : {
                                self.success : "PROD Deploy Successful", self.unsuccess: "PROD Deploy Failed"
                        },
                        "deploy.rollback" : {
                                self.success : "Rollback (PROD) Success", self.unsuccess: "Rollback (PROD) Failed"
                        }
                }
        }
        """
        self.OS_CMD = {
                "GET_ALL_MONGO_CONF_FILES" : "ps -eaf | grep -i 'mongod -f ' | grep -v grep | awk '{print $10}' " ,
                "GET_CTFY_MEMBER" : "/bin/adquery group -s {ctfy_grp}",
                "GET_MEMBER_NAME" : "/bin/adquery user -A {userid} | grep -i 'displayname'  | cut -f2 -d: "
        }
        """
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

        self.OS_CMD = {
            "GET_ALL_MONGO_CONF_FILES" : "ps -eaf | grep -i 'mongod -f ' | grep -v grep | awk '{print $10}' " ,
            "GET_CTFY_MEMBER" : "/bin/adquery group -s '{ctfy_grp}'",
            "GET_MEMBER_NAME" : "/bin/adquery user -A {userid} | grep -i 'displayname' | cut -f2 -d: ",
            "LAST_PASSWORD_CHANGE_DATE" : "/usr/bin/histmongo.sh {user} | grep -i 'Last password change' | cut -d ':' -f2",
            "GET_USER_GRP_NAME" : "/bin/adquery user {userid} -a"
        }
        """
        self.OS_CMD = {
            "GET_ALL_MONGO_CONF_FILES" : "ps -eaf | grep -i 'mongod -f ' | grep -v grep | awk '{print $10}' " ,
            "GET_CTFY_MEMBER" : "/bin/adquery group -s {ctfy_grp}",
            "GET_MEMBER_NAME" : "/bin/adquery user -A {userid} | grep -i 'displayname' | cut -f2 -d: ",
            "LAST_PASSWORD_CHANGE_DATE" : "/usr/bin/histmongo.sh {user} | grep -i 'Last password change' | cut -d ':' -f2"
        }
        """
        self.MONGO_CTFY_GROUP = ["CTFY-UG_NA_Marsh_dba-S-L"]
        self.AD_GROUP_ROLE_KW = "OU=User Role Groups"

    def __repr__(self):
            return "(%s)" % (self.__class__)

    def __str__(self):
            return "(%s)" % (self.__class__)
