from com.mmc.common.singleton import Singleton
from com.mmc.comm.globals import Globals

class sqlRepo(object, metaclass=Singleton):
	"""
	This class should contain all sqls used by all RDBMS technology (sys call like, sessio/user/db info). Also,
	all the sqls used by a components for e.g. dbaas --> oracle/postgres/mysql, cicd --> oracle/postgres/mysql
	Status : Not completed (Pending)
	"""
	def __init__(self):
		self.Globals = Globals()

		"""
		Following table is used when retrieving Oracle soure code.
		returns object source code as requested in objDetail
		Arguments:
			securityToken : Security token
			objDetails : Object details (arrarys
				[{objType, objName, objOwner}]

			In the attributes column, 
				S represents a schema object, 
				N represents a named object, 
				D represents a dependent object, 
				G represents a granted object, 
				and H represents a heterogeneous object.

			Type Name					Meaning														Attributes	Notes
			========================================================================================================================
			AQ_QUEUE 					queues  													SND   Dependent on table
			AQ_QUEUE_TABLE 				additional metadata for queue tables 						ND Dependent on table
			AQ_TRANSFORM 				transforms 													SN None 
			ASSOCIATION 				associate statistics 										D None
			AUDIT 						audits of SQL statements 									DG 
			AUDIT_OBJ 					audits of schema objects 									D None
			CLUSTER 					clusters 													SN None
			COMMENT 					comments 													D None
			CONSTRAINT 					constraints 												SND 
			CONTEXT 					application contexts 										N None
			DATABASE_EXPORT 			all metadata objects in a database 							H Corresponds to a full database export
			DB_LINK 					database links 												SN Modeled as schema objects because they have owners. For public links, the owner is PUBLIC. For private links, the creator is the owner.
			DEFAULT_ROLE 				default roles 												G Granted to a user by ALTER USER
			DIMENSION 					dimensions 													SN None
			DIRECTORY 					directories 												N None
			FGA_POLICY 					fine-grained audit policies 								D Not modeled as named object because policy names are not unique.
			FUNCTION 					stored functions 											SN None
			INDEX_STATISTICS 			precomputed statistics on indexes 							D The base object is the index's table.
			INDEX 						indexes 													SND None
			INDEXTYPE 					indextypes 													SN None
			JAVA_SOURCE 				Java sources 												SN None
			JOB 						jobs 														S None
			LIBRARY 					external procedure libraries 								SN None
			MATERIALIZED_VIEW 			materialized views 											SN None
			MATERIALIZED_VIEW_LOG 		materialized view logs 										D None
			OBJECT_GRANT 				object grants 												DG None
			OPERATOR 					operators 													SN None
			PACKAGE 					stored packages 											SN By default, both package specification and package body are retrieved. See "SET_FILTER Procedure".
			PACKAGE_SPEC 				package specifications 										SN None
			PACKAGE_BODY 				package bodies 												SN None
			PROCEDURE 					stored procedures 											SN None
			PROFILE 					profiles 													N None
			PROXY 						proxy authentications 										G Granted to a user by ALTER USER
			REF_CONSTRAINT 				referential constraint 										SND None
			REFRESH_GROUP 				refresh groups 												SN None
			RESOURCE_COST 				resource cost info None
			RLS_CONTEXT 				driving contexts for enforcement of fine-grained access-control policies D Corresponds to the DBMS_RLS.ADD_POLICY_CONTENT procedure
			RLS_GROUP 					fine-grained access-control policy groups 					D Corresponds to the DBMS_RLS.CREATE_GROUP procedure
			RLS_POLICY 					fine-grained access-control policies 						D Corresponds to DBMS_RLS.ADD_GROUPED_POLICY. Not modeled as named objects because policy names are not unique.
			RMGR_CONSUMER_GROUP 		resource consumer groups 									SN Data Pump does not use these object types. Instead, it exports resource manager objects as procedural objects.
			RMGR_INTITIAL_CONSUMER_GROUP assign initial consumer groups to users 					G None
			RMGR_PLAN 					resource plans 												SN None
			RMGR_PLAN_DIRECTIVE 		resource plan directives 									D Dependent on resource plan
			ROLE 						roles 														N None
			ROLE_GRANT 					role grants 												G None
			ROLLBACK_SEGMENT 			rollback segments 											N None
			SCHEMA_EXPORT 				all metadata objects in a schema 							H Corresponds to user-mode export.	
			SEQUENCE 					sequences 													SN None
			SYNONYM 					synonyms Private synonyms are schema objects. Public synonyms are not, but for the purposes of this API, their schema name is PUBLIC. The name of a synonym is considered to be the synonym itself. For example, in CREATE PUBLIC SYNONYM FOO FOR BAR, the resultant object is considered to have name FOO and schema PUBLIC.
			SYSTEM_GRANT 				system privilege grants 									G None
			TABLE 						tables 														SN None
			TABLE_DATA 					metadata describing row data for a table, nested/partition 	SND 		For partitions, the object name is the partition name. For nested tables, the object name is the storage table name. The base object is the top-level table to which the table data belongs. For nested tables and partitioning, this is the top-level table (not the parent table or partition). For nonpartitioned tables and non-nested tables this is the table itself.
			TABLE_EXPORT 				metadata for a table and its associated objects 			H Corresponds to table-mode export
			TABLE_STATISTICS 			precomputed statistics on tables 							D None
			TABLESPACE 					tablespaces 												N None
			TABLESPACE_QUOTA 			tablespace quotas 											G Granted with ALTER USER
			TRANSPORTABLE_EXPORT 		metadata for objects in a transportable tablespace set 		H Corresponds to transportable tablespace export
			TRIGGER 					triggers 													SND None
			TRUSTED_DB_LINK 			trusted links 												N None
			TYPE 						user-defined types 											SN By default, both type and type body are retrieved. See "SET_FILTER Procedure".
			TYPE_SPEC 					type specifications 										SN None
			TYPE_BODY 					type bodies 												SN None
			USER 						users 														N None
			VIEW 						views 														SN None
			XMLSCHEMA 					XML schema 													SN The object's name is its URL (which may be longer than 30 characters). Its schema is the user who registered it.
			XS_USER 					Real Application Security (RAS) user 						N Corresponds to RAS users
			XS_ROLE 					Real Application Security (RAS) role 						N Corresponds to RAS roles
			XS_ROLESET 					Real Application Security (RAS) rolesets 					N Corresponds to RAS rolesets
			XS_ROLE_GRANT 				Real Application Security (RAS) role grants 				N Corresponds to RAS role grants
			XS_SECURITY_CLASS 			Real Application Security (RAS) security class 				SN Corresponds to RAS security classes
			XS_DATA_SECURITY 			Real Application Security (RAS) data security policy 		SN Corresponds to RAS data security policies
			XS_ACL 						Real Application Security (RAS) ACL 						SN Corresponds to RAS access control lists (ACLs) and associated access control entries (ACEs)
			XS_ACL_PARAM 				Real Application Security (RAS) ACL parameter 				N Corresponds to RAS access control lists (ACL) parameters
			XS_NAMESPACE 				Real Application Security (RAS) namespace 					N Corresponds to RAS namespaces.
		"""
		self.ORA_SQLS = {
			# oracle sys call sql
			# objects/schema
			"isSchemaObjExists" : {
				"default" :  "SELECT object_name FROM dba_objects WHERE owner = :OWNER AND object_name = :OBJECT_NAME AND object_Type = :OBJECT_TYPE", 
				"criteria" : ["OWNER","OBJECT_NAME","OBJECT_TYPE"], 
				"return" : "EXISTENCE",
				"sqlType" : "select"
			},
			"getSchemaObj" : {
				"default" :  "SELECT object_type, object_name FROM dba_objects WHERE owner = :OWNER", 
				"criteria" : ["OWNER"], 
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getObjectDetails" :{
				"default" : "SELECT * FROM DBA_OBJECTS WHERE OWNER = :OWNER AND OBJECT_TYPE = :OBJECT_TYPE AND OBJECT_NAME :OBJECT_NAME", 
				"criteria" : ["OWNER","OBJECT_TYPE","OBJECT_NAME"], 
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getObjectSizeMB" : {
				"default" : "SELECT SUM(bytes)/(1024*1024) FROM DBA_SEGMENTS WHERE owner = :OWNER AND object_type = :OBJECT_TYPE AND object_name = :OBJECT_NAME",
				"criteria" : ["OWNER","OBJECT_TYPE","OBJECT_NAME"], 
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllUserObj" : {
				"default" : "SELECT * FROM dba_objects WHERE owner = :OWNER",
				"criteria" : ["OWNER"], 
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAnUserObjInfo" : {
				"default" : "SELECT * FROM dba_objects WHERE owner = :OWNER AND object_type = :OBJECT_TYPE AND object_name :OBJECT_NAME",
				"criteria" : ["OWNER","OBJECT_TYPE","OBJECT_NAME"], 
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllUserObjByType" : {
				"default" : "SELECT * FROM dba_objects WHERE owner = :OWNER, object_type = :OBJECT_TYPE",
				"criteria" : ["OWNER","OBJECT_TYPE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllUserObjSummary" : {
				"default" : "SELECT object_type, status, count(*) as TOTAL FROM dba_objects WHERE owner = :OWNER group by object_type, status",
				"criteria" : ["OWNER"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllUserObjSummaryByStatus" : {
				"default" : "SELECT object_type, count(*) as TOTAL FROM dba_objects WHERE owner = :OWNER group by object_type",
				"criteria" : ["OWNER","STATUS"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getUserObjCnt" : {
				"default" : "SELECT COUNT(*) as TOTAL FROM dba_objects WHERE owner = :OWNER",
				"criteria" : ["OWNER"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getUserObjCntByType" : {
				"default" : "SELECT OBJECT_TYPE, COUNT(*) as TOTAL FROM dba_objects WHERE owner = :OWNER group by OBJECT_TYPE",
				"criteria" : ["OWNER","OBJECT_TYPE","OBJECT_TYPE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getUserObjectsByStatus" : {
				"default" : "SELECT OBJECT_TYPE, OBJECT_NAME FROM dba_objects WHERE owner = :OWNER AND status = :STATUS",
				"criteria" : ["OWNER","STATUS"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getSchemaSizeMB" : {
				"default" : "SELECT SUM(bytes)/(1024*1024) as SIZE_MB FROM DBA_SEGMENTS WHERE owner = :OWNER",
				"criteria" : ["OWNER"],
				"return" : "RESULT",
				"sqlType" : "select"
			},

			# roles/privilege
			"isRoleExists" : {
				"default" : "SELECT role FROM dba_roles WHERE role = :ROLE",
				"criteria" : ["ROLE"],
				"return" : "EXISTENCE",
				"sqlType" : "select"
			},
			"getRoleInfo" : {
				"default" : "SELECT * FROM dba_roles WHERE role = :ROLE",
				"criteria" : ["ROLE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllRoles" : {
				"default" :  "SELECT role_name FROM dba_roles",
				"criteria" : [],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllUserRole" : {
				"default" :  "SELECT role as ROLE FROM role_tab_privs WHERE owner = :OWNER",
				"criteria" : ["OWNER"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getSysPrivsGrantedTo" : {
				"default" : "SELECT * FROM dba_sys_privs WHERE grantee = :GRANTEE",
				"criteria" : ["GRANTEE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getTabPrivsGrantedTo" : {
				"default" : "SELECT * FROM dba_tab_privs WHERE grantee = :GRANTEE",
				"criteria" : ["GRANTEE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getRoleGrantedTo" : {
				"default" : "SELECT * FROM dba_role_privs WHERE grantee = :GRANTEE",
				"criteria" : ["GRANTEE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},

			# tablespaces
			"getAllTbsInfo" : {
				"default" : "SELECT * FROM dba_tablespaces",
				"criteria" : [],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getTBSDBFiles" : {"default" : "SELECT * FROM dba_datafiles WHERE tablespace_name = :TABLESPACE_NAME",
				"criteria" : ["TABLESPACE_NAME"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getTBSSizeInfoMB" : {
				"default" :  """
					SELECT tablespace_name, SUM(dbfiles.bytes)/(1024*1024) AS SIZE_MB, SUM(free.bytes)/(1024*1024*1024) AS FREE_MB
						FROM dba_data_files dbfiles, 
							dba_free_space free
						WHERE dbfiles.tablespace_name = DECODE(:TABLESPACE_NAME,'ALL',dbfiles.tablespace_name, :TABLESPACE_NAME) 
							AND dbfiles.tablespace_name = free.tablespace_name
						GROUP BY tablespace_name
				""",
				"criteria" : ["TABLESPACE_NAME"],
				"return" : "RESULT"				,
				"sqlType" : "select"
			},

			# database/instances/sessions
			"getDBVer" : {
				"default" : "SELECT version as VERSION from v$instance",
				"criteria" : [""],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getDBDetails" : {
				"default" : "SELECT * FROM v$database",
				"criteria" : [""],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllInstDetails" : {
				"default" :  "SELECT * FROM gv$instance",
				"criteria" : [""],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getDBTimeStamp" : {
				"default" : "SELECT SYSTIMESTAMP FROM DUAL",
				"criteria" : [""],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getUserSessionDetail": {
				"default" : "SELECT * FROM v$session where username = :USERNAME",
				"criteria" : ["USERNAME"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getUserSessionDetailByStatus": {
				"default" : "SELECT * FROM v$session where username = :USERNAME AND status = :STATUS",
				"criteria" : ["USERNAME","STATUS"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getSessCntByUserStatus": {
				"default" : "SELECT count(*) as TOTAL FROM v$session where status = :STATUS AND username = :USERNAME",
				"criteria" : ["STATUS","USERNAME"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getSessCntByMachine": {
				"default" : "SELECT status, count(*) as TOTAL FROM v$session where machine = :MACHINE group by status",
				"criteria" : ["MACHINE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getSessCntByUserMachine": {
				"default" : "SELECT status, count(*) as TOTAL FROM v$session where username = :USERNAME AND machine = :MACHINE",
				"criteria" : ["MACHINE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},

			# source code
			"getDDL" : {
				"default" : "SELECT DBMS_METADATA.GET_DDL(:OBJECT_TYPE, :OBJECT_NAME, :OBJ_OWNER) FROM DUAL",
				"criteria" : ["OWNR","OBJECT_TYPE","OBJECT_NAME"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getDependentDDL" : {
				"default" : "SELECT DBMS_METADATA.GET_DEPENDENT_DDL(:OBJECT_TYPE, :OBJECT_NAME, :OBJ_OWNER) FROM DUAL",
				"criteria" : ["OWNR","OBJECT_TYPE","OBJECT_NAME"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getGrantedDDL" : {
				"default" : "SELECT DBMS_METADATA.GET_GRANTED_DDL(:GRANT_TYPE, :GRANTEE) FROM DUAL",
				"criteria" : ["GRANT_TYPE","GRANTEE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},

			# user/profile
			"isUserExists" : {
				"default" : "SELECT username FROM dba_users WHERE username = :USER_NAME",
				"criteria" : ["USER_NAME"],
				"return" : "EXISTENCE",
				"sqlType" : "select"
			},
			"isProfileExists" : {
				"default" : "SELECT PROFILE FROM dba_profiles WHERE profile = :PROFILE",
				"criteria" : ["PROFILE"],
				"return" : "EXISTENCE",
				"sqlType" : "select"
			},
			"isSysPrivsGrantedTo" : {
				"default" : "SELECT privilege FROM dba_sys_privs WHERE GRANTEE = :GRANTEE AND privilege = :PRIVILEGE",
				"criteria" : ["GRANTEE","PRIVILEGE"],
				"return" : "EXISTENCE",
				"sqlType" : "select"
			},
			"isObjPrivsGrantedTo" : {
				"default" : "SELECT privilege FROM dba_tab_privs WHERE GRANTEE = :GRANTEE AND owner = :OWNER AND object_name = :OBJECT_NAME and privilege = :PRIVILEGE",
				"criteria" : ["GRANTEE","PRIVILEGE","OWNER","OBJECT_NAME"],
				"return" : "EXISTENCE",
				"sqlType" : "select"
			},
			"getAllSchema" : {
				"default" : "SELECT distinct owner FROM dba_objects",
				"criteria" : [],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllUsers" : {
				"default" : "SELECT owner, count(*) as TOTAL_OBJECTS FROM dba_objects group by owner",
				"criteria" : [],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllSchemaObjSummary" : {
				"default" : "SELECT owner, object_type, status, count(*) as TOTAL FROM dba_objects group by owner, object_type, status",
				"criteria" : [],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getUserInfo" : {
				"default" : "SELECT * FROM dba_users WHERE username = :USER_NAME",
				"criteria" : ["USER_NAME"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getUserExtInfo" : {
				"default" : "SELECT * FROM sys.user$ WHERE name = :USER_NAME",
				"criteria" : ["USER_NAME"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getProfileInfo" : {
				"default" : "SELECT * FROM dba_profiles WHERE profile = :PROFILE",
				"criteria" : ["PROFILE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},

			# change user/profile
			"newUser" : {
				"default" : "CREATE USER :USER_NAME IDENTIFIED BY :PASSWORD",
				"criteria" : ["USER_NAME","PASSWORD"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"changeUserPass" : {
				"default" : "ALTER USER :USER_NAME IDENTIFIED BY :PASSWORD",
				"criteria" : ["USER_NAME","PASSWORD"],
				"return" : "RESULT",
				"sqlType" : "ddl"
			},
			"changeUserProfile" : {
				"default" : "ALTER USER :USER_NAME PROFILE :PROFILE",
				"criteria" : ["USER_NAME","PROFILE"],
				"return" : "RESULT",
				"sqlType" : "ddl"
			},
			"lockUserAccount" : {
				"default" : "ALTER USER USER :USER_NAME ACCOUNT LOCK",
				"criteria" : ["USER_NAME"],
				"return" : "RESULT",
				"sqlType" : "ddl"
			},
			"unLockUserAccount" : {
				"default" : "ALTER USER USER :USER_NAME IDENTIFIED BY :PASSWORD ACCOUNT UNLOCK",
				"criteria" : ["USER_NAME","PASSWORD"],
				"return" : "RESULT",
				"sqlType" : "ddl"
			},
			"dropUser" : {
				"default" : "DROP USER :USER_NAME",
				"criteria" : ["USER_NAME"],
				"return" : "RESULT",
				"sqlType" : "dcl"
			},
			"grantSysPrivs2User" : {
				"default" : "GRANT :SYS_PRIVILEGE TO :GRANTEE",
				"criteria" : ["GRANTEE","SYS_PRIVILEGE"],
				"return" : "RESULT",
				"sqlType" : "dcl"
			},
			"grantObjPrivs2User" : {
				"default" : "GRANT :OBJ_PRIVILEGE ON :OBJECT TO :GRANTEE",
				"criteria" : ["GRANTEE","OBJ_PRIVILEGE","OBJECT"],
				"return" : "RESULT",
				"sqlType" : "dcl"
			},
			"revokeSysPrivsFromUser" : {
				"default" : "REVOKE :SYS_PRIVILEGE FROM :GRANTEE",
				"criteria" : ["GRANTEE","SYS_PRIVILEGE"],
				"return" : "RESULT",
				"sqlType" : "dcl"
			},
			"revokeObjPrivsFromUser" : {
				"default" : "REVOKE :OBJ_PRIVILEGE ON :OBJECT FROM :GRANTEE",
				"criteria" : ["GRANTEE","OBJ_PRIVILEGE","OBJECT"],
				"return" : "RESULT",
				"sqlType" : "dcl"
			}
		self.DBAAS_SQL = {
			"repository": {
				"oracle" : {
					"getAciveAdminList" :{
						"default" : "SELECT * FROM  DB_MON_OWNER.VALID_DBA_LIST WHERE end_date is null",
						"criteria" : [],
						"return" : "result",
						"sqlType" : "select"
					},
					"getAciveAdminListForDbTech" :{
						"default" : "SELECT * FROM  DB_MON_OWNER.VALID_DBA_LIST WHERE end_date is null AND db_platform = INITCAP(:DB_TECHNOLOGY)",
						"criteria" : [],
						"return" : "result",
						"sqlType" : "select"
					},
					"getAppId" : {
						"default" : "SELECT application_id APP_ID, application_name APP_NAME, application_desc APP_DESC, application_region region, application_opco OPCO FROM db_mon_owner.application_info where application_opco = UPPER(:OPCO) AND application_region = UPPER(:REGION) AND application_name = :APP_NAME",
						"criteria" : ["OPCO","REGION","APP_NAME"],
						"return" : "result",
						"sqlType" : "select"						
					},
					"isValidOraDBInstance" : {
						"default" : "SELECT COUNT(1) TOTAL FROM DB_MON_OWNER.DATABASE_DATA_WINDOW WHERE DB_NAME = :DB_INSTANCE_NAME",
						"criteria" : ["DB_INSTANCE_NAME"],
						"return" : "existence",
						"sqlType" : "select"
					},
					"isValidOraDBInst" : {
						"default" : """
						SELECT COUNT(DISTINCT DB_INSTANCE) TOTAL 
							FROM db_mon_owner.cicd_application_info cicd 
							WHERE cicd.app_id = :APP_ID
								AND cicd.opco = UPPER(:OPCO)
								AND cicd.region = UPPER(:REGION)
								AND cicd.db_technology = INITCAP(:DB_TECHNOLOGY)
								AND cicd.env = UPPER(:ENV)
								AND cicd.host_name = :HOST_NAME
						"""
					},
					"isValidOraDBSchema" : {
						"default" : """
						SELECT COUNT(DISTINCT SCHEMA) TOTAL 
							FROM db_mon_owner.cicd_application_info cicd 
							WHERE cicd.app_id = :APP_ID
								AND cicd.opco = UPPER(:OPCO)
								AND cicd.region = UPPER(:REGION)
								AND cicd.db_technology = INITCAP(:DB_TECHNOLOGY)
								AND cicd.db_instance = UPPER(:DB_INSTANCE)
								AND cicd.env = UPPER(:ENV)
								AND cicd.host_name = :HOST_NAME
								AND cicd.schema = UPPER(:SCHEMA_NAME)
						"""
					},			
					"getInactiveAdminList" : {
						"default" : """
							SELECT DISTINCT
								a.db_name DB_INSTANCE_NAME,
								a.host_name HOST_NAME,
								a.db_platform DB_PLATFORM,
								a.db_type DB_TYPE,
								a.opco OPCO,
								a.db_region REGION,
								decode(a.db_type, 'PROD', 'PROD','NONPROD') ENV,
								b.username USER_NAME,
								'USER ' || b.username || ' is not on the valid DBA list as of ' || to_char(trunc(sysdate), 'MM/DD/YYYY') EVAL
							FROM db_mon_owner.database_data_window a,
									db_mon_owner.user_data_window b
							WHERE a.db_name = b.db_name
								AND a.opco = b.opco
								AND a.db_region = b.db_region
								AND a.db_type = b.db_type
								AND a.db_platform = b.db_platform
								AND a.host_name = b.host_name
								AND a.instance_number = (
									SELECT MIN(db_min.instance_number)
									FROM db_mon_owner.database_data_window db_min
									WHERE a.db_name = db_min.db_name
									AND a.opco = db_min.opco
									AND a.db_region = db_min.db_region
									AND a.db_type = db_min.db_type
									AND a.db_platform = db_min.db_platform
								)
								AND b.dba_flag = 'Y'
								AND b.username NOT IN (
									SELECT DISTINCT
										s1.DBA_USERID
										FROM db_mon_owner.VALID_DBA_LIST s1
										WHERE s1.db_platform = b.db_platform
											AND s1.start_date < b.process_date
											AND nvl(s1.end_date, sysdate + 50) > b.process_date
											AND (s1.support_regions = 'GLOBAL' or s1.support_regions like '%' || b.db_region || '%')
											AND (s1.opco = 'ALL' or s1.opco like '%' || b.opco || '%')
								) 
							"""
					},
					"getAllPendingInactiveAdminListByTech" : {
						"default" : """
							SELECT DISTINCT
								a.db_name DB_INSTANCE_NAME,
								a.host_name HOST_NAME,
								a.db_platform DB_PLATFORM,
								a.db_type DB_TYPE,
								a.opco OPCO,
								a.db_region REGION,
								decode(a.db_type, 'PROD', 'PROD','NONPROD') ENV,
								b.username USER_NAME,
								'USER ' || b.username || ' is not on the valid DBA list as of ' || to_char(trunc(sysdate), 'MM/DD/YYYY') EVAL
							FROM db_mon_owner.database_data_window a,
									db_mon_owner.user_data_window b
							WHERE a.db_name = b.db_name
								AND a.opco = b.opco
								AND a.db_region = b.db_region
								AND a.db_type = b.db_type
								AND a.db_platform = b.db_platform
								AND a.host_name = b.host_name
								AND a.db_platform = INITCAP(:DB_TECHNOLOGY)
								AND a.instance_number = (
									SELECT MIN(db_min.instance_number)
									FROM db_mon_owner.database_data_window db_min
									WHERE a.db_name = db_min.db_name
									AND a.opco = db_min.opco
									AND a.db_region = db_min.db_region
									AND a.db_type = db_min.db_type
									AND a.db_platform = db_min.db_platform
								)
								AND b.dba_flag = 'Y'
								AND b.username NOT IN (
									SELECT DISTINCT
										s1.DBA_USERID
										FROM db_mon_owner.VALID_DBA_LIST s1
										WHERE s1.db_platform = b.db_platform
											AND s1.start_date < b.process_date
											AND nvl(s1.end_date, sysdate + 50) > b.process_date
											AND (s1.support_regions = 'GLOBAL' or s1.support_regions like '%' || b.db_region || '%')
											AND (s1.opco = 'ALL' or s1.opco like '%' || b.opco || '%')
								) 
						"""
					},
					# returns all applicstion for given opco/region/technology			
					"getAllApps" : {"default" : """
						SELECT DISTINCT 
							cicd.app_id APP_ID,
							cicd.app_name APP_NAME,
							cicd.app_desc APP_DESC,
							cicd.app_opco OPCO,
							cicd.app_region REGION,
							cicd.support_team SUPPORT_TEAM,
							cicd.support_email SUPPORT_EMAIL
						FROM db_mon_owner.cicd_application_info cicd
						WHERE cicd.app_opco = UPPER(:OPCO)
							AND cicd.app_region = UPPER(:REGION)
							AND cicd.db_technology = :DB_TECHNOLOGY
						ORDER BY cicd.app_name
					"""
					},
					# returns applicstion detail for given opco/region/technology/app
					"getAnAppDetail" : {"default" : """
						SELECT distinct cicd.app_id APP_ID,
							cicd.app_name APP_NAME,
							cicd.app_desc APP_DESC,
							cicd.app_opco OPCO,
							cicd.app_region REGION,
							cicd.support_team SUPPORT_TEAM,
							cicd.support_email SUPPORT_EMAIL
						FROM db_mon_owner.cicd_application_info cicd
						WHERE cicd.app_opco = UPPER(:OPCO)
							AND cicd.app_region = UPPER(:REGION)
							AND cicd.db_technology = :DB_TECHNOLOGY
							AND cicd.app_id = :APP_ID
					"""
					},
					"getAnAppDetailByAppId" : {"default" : """
						SELECT distinct cicd.app_id APP_ID,
							cicd.app_name APP_NAME,
							cicd.app_desc APP_DESC,
							cicd.app_opco OPCO,
							cicd.app_region REGION,
							cicd.db_technology DB_TECHNOLOGY,
							cicd.support_team SUPPORT_TEAM,
							cicd.support_email SUPPORT_EMAIL
						FROM db_mon_owner.cicd_application_info cicd
						WHERE cicd.app_id = :APP_ID
					"""
					},
					# returns all environment for givern opco/region/technology/app
					"getAllAppEnvFromRepo" : {
						"default": """
							SELECT DISTINCT
								cicd.opco OPCO,
								cicd.region REGION,
								cicd.db_technology DB_TECHNOLOGY,
								cicd.host_name HOST_NAME,
								cicd.db_instance DB_INSTANCE, 
								cicd.env ENV
							FROM db_mon_owner.cicd_application_info cicd
							WHERE cicd.app_opco = UPPER(:OPCO)
								AND cicd.app_region = UPPER(:REGION)
								AND cicd.db_technology = initcap(:DB_TECHNOLOGY)
								AND cicd.app_id = :APP_ID
							ORDER BY cicd.env
							"""
					},
					# returns all database (instance) for a given opco/region/technology/App/Env
					"getAppDBInstance" : {"default" : """
						SELECT DISTINCT 
							cicd.opco OPCO,
							cicd.db_instance DB_INSTANCE,
							cicd.host_name HOST_NAME,
							cicd.db_technology DB_TECHNOLOGY,
							cicd.region REGION,
							cicd.prod_nonprod PROD_NONPROD,
							cicd.env ENV
						FROM db_mon_owner.cicd_application_info cicd
						WHERE cicd.app_id = :APP_ID
							AND cicd.opco = UPPER(:OPCO)
							AND cicd.region = UPPER(:REGION)
							AND cicd.db_technology = INITCAP(:DB_TECHNOLOGY)
							AND cicd.env = UPPER(:ENV)
					"""
					},
					# returns all database schemas for a given opco/region/technology/appId/dbname/env/host
					"getDBInstSchemas" : {"default" : """
						SELECT DISTINCT 
							cicd.schema SCHEMA
						FROM db_mon_owner.cicd_application_info cicd
						WHERE cicd.app_id = :APP_ID
							AND cicd.opco = UPPER(:OPCO)
							AND cicd.region = UPPER(:REGION)
							AND cicd.db_technology = INITCAP(:DB_TECHNOLOGY)
							AND cicd.db_instance = UPPER(:DB_INSTANCE)        
							AND cicd.env = UPPER(:ENV)
							AND cicd.host_name = :HOST_NAME
					"""
					},
					## returns all db connection string for opco/region/dbTechnology(oracle)/dbInstance/hostName
					"getDBUri" : {"default" : """
						SELECT DISTINCT
							cicd.PROD_NONPROD as ENV,
							cicd.connection_info as CONNECTION_INFO
						FROM db_mon_owner.cicd_application_info cicd
						WHERE cicd.opco = UPPER(:OPCO) 
							AND cicd.region = UPPER(:REGION)
							AND cicd.db_technology = INITCAP(:DB_TECHNOLOGY)
							AND cicd.host_name = :HOST_NAME
							AND cicd.db_instance = UPPER(:DB_INSTANCE)
							AND cicd.db_instance not like 'erp%'
						"""
					},
					## returns all db connection string for opco/region/dbTechnology(oracle)/dbInstance
					"getDBUri4DBInst" : {"default" : """
						SELECT DISTINCT
							cicd.PROD_NONPROD as ENV,
							cicd.connection_info as CONNECTION_INFO
							cicd.host_name as HOST_NAME,
						FROM db_mon_owner.cicd_application_info cicd
						WHERE cicd.opco = UPPER(:OPCO) 
							AND cicd.region = UPPER(:REGION)
							AND cicd.db_technology = INITCAP(:DB_TECHNOLOGY)
							AND cicd.db_instance = UPPER(:DB_INSTANCE)
							AND cicd.db_instance not like 'erp%'
						"""
					},
					## returns all db connection string for opco/region/dbTechnology (oracle)
					"getAllDBUri" : {"default" : """ 
						SELECT DISTINCT
							cicd.PROD_NONPROD as ENV,
							cicdvw.connection_info as CONNECTION_INFO
							cicdvw.host_name as HOST_NAME,
						FROM db_mon_owner.cicd_application_info cicd
						WHERE cicd.opco = UPPER(:OPCO) 
							AND cicd.region = UPPER(:REGION)
							AND cicd.db_technology = INITCAP(:DB_TECHNOLOGY)
							AND cicd.db_instance not like 'erp%'
						"""
					},
					"getDBList" : {
						"default" : """
							SELECT 
								DB_NAME DB_INSTANCE_NAME, 
								DB_UNIQUE_NAME, 
								DB_VERSION, 
								INSTANCE_NAME, 
								INSTANCE_NUMBER,
								PLATFORM_NAME, 
								INSTANCE_VERSION
							FROM db_mon_owner.cicd_application_info cicd
							WHERE cicd.opco = UPPER(:OPCO)
								AND cicd.region = UPPER(:REGION)
								AND cicd.db_technolog = initcap(:DB_TECHNOLOGY)
								AND DB.DB_TYPE = UPPER(:PROD_NONPROD)
						"""
					},
					"getAllSchema__old" : {
						"default" : """
							SELECT DISTINCT owner as SCHEMA FROM DBA_OBJECTS WHERE OWNER IN (SELECT username FROM DBA_USERS WHERE upper(username) not like '%SYS%')",
						""",
						"default_old" : "SELECT DISTINCT owner as SCHEMA FROM DBA_OBJECTS WHERE OWNER IN (SELECT username FROM DBA_USERS WHERE upper(username) not like '%SYS%')",
						"10" : """
							SELECT DISTINCT owner as SCHEMA 
								FROM DBA_OBJECTS 
								WHERE OWNER IN 
									(SELECT username 
										FROM DBA_USERS 
										WHERE username NOT IN 
											('ANONYMOUS','APEX_040200','APEX_PUBLIC_USER','APPQOSSYS','AUDSYS',
											 'BI','CTXSYS','DBSNMP','DIP','DVF','DVSYS','EXFSYS','FLOWS_FILES',
											 'GSMADMIN_INTERNAL','GSMCATUSER','GSMUSER','HR','IX','LBACSYS','MDDATA',
											 'MDSYS','OE','ORACLE_OCM','ORDDATA','ORDPLUGINS','ORDSYS','OUTLN','PM',
											 'SCOTT','SH','SI_INFORMTN_SCHEMA','SPATIAL_CSW_ADMIN_USR',
											 'SPATIAL_WFS_ADMIN_USR','SYS','SYSBACKUP','SYSDG','SYSKM','SYSTEM','WMSYS',
											 'XDB','SYSMAN','RMAN','RMAN_BACKUP','OWBSYS','OWBSYS_AUDIT','APEX_030200','MGMT_VIEW','OJVMSYS'))
						""",
						"11" : """
							SELECT DISTINCT owner as SCHEMA 
								FROM DBA_OBJECTS 
								WHERE OWNER IN 
									(SELECT username 
										FROM DBA_USERS 
										WHERE username NOT IN 
											('ANONYMOUS','APEX_040200','APEX_PUBLIC_USER','APPQOSSYS','AUDSYS',
											 'BI','CTXSYS','DBSNMP','DIP','DVF','DVSYS','EXFSYS','FLOWS_FILES',
											 'GSMADMIN_INTERNAL','GSMCATUSER','GSMUSER','HR','IX','LBACSYS','MDDATA',
											 'MDSYS','OE','ORACLE_OCM','ORDDATA','ORDPLUGINS','ORDSYS','OUTLN','PM',
											 'SCOTT','SH','SI_INFORMTN_SCHEMA','SPATIAL_CSW_ADMIN_USR',
											 'SPATIAL_WFS_ADMIN_USR','SYS','SYSBACKUP','SYSDG','SYSKM','SYSTEM','WMSYS',
											 'XDB','SYSMAN','RMAN','RMAN_BACKUP','OWBSYS','OWBSYS_AUDIT','APEX_030200','MGMT_VIEW','OJVMSYS'))
						""",
						"12" : "SELECT DISTINCT owner as SCHEMA FROM DBA_OBJECTS WHERE OWNER IN (SELECT username FROM DBA_USERS WHERE ORACLE_MAINTAINED = 'N')" 
					}
				}

				},
				"postgres" : {
				}
			}
		}
			# cicd
		
		self.PG_SQLS = {
			# objects/schema
			"isSchemaObjExists" : {
				"default" :  "SELECT object_name FROM dba_objects WHERE owner = :OWNER AND object_name = :OBJECT_NAME AND object_Type = :OBJECT_TYPE", 
				"criteria" : ["OWNER","OBJECT_NAME","OBJECT_TYPE"], 
				"return" : "EXISTENCE",
				"sqlType" : "select"
			},
			"getSchemaObj" : {
				"default" :  "SELECT object_type, object_name FROM dba_objects WHERE owner = :OWNER", 
				"criteria" : ["OWNER"], 
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getObjectDetails" :{
				"default" : "SELECT * FROM DBA_OBJECTS WHERE OWNER = :OWNER AND OBJECT_TYPE = :OBJECT_TYPE AND OBJECT_NAME :OBJECT_NAME", 
				"criteria" : ["OWNER","OBJECT_TYPE","OBJECT_NAME"], 
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getObjectSizeMB" : {
				"default" : "SELECT SUM(bytes)/(1024*1024) FROM DBA_SEGMENTS WHERE owner = :OWNER AND object_type = :OBJECT_TYPE AND object_name = :OBJECT_NAME",
				"criteria" : ["OWNER","OBJECT_TYPE","OBJECT_NAME"], 
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllUserObj" : {
				"default" : "SELECT * FROM dba_objects WHERE owner = :OWNER",
				"criteria" : ["OWNER"], 
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAnUserObjInfo" : {
				"default" : "SELECT * FROM dba_objects WHERE owner = :OWNER AND object_type = :OBJECT_TYPE AND object_name :OBJECT_NAME",
				"criteria" : ["OWNER","OBJECT_TYPE","OBJECT_NAME"], 
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllUserObjByType" : {
				"default" : "SELECT * FROM dba_objects WHERE owner = :OWNER, object_type = :OBJECT_TYPE",
				"criteria" : ["OWNER","OBJECT_TYPE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllUserObjSummary" : {
				"default" : "SELECT object_type, status, count(*) as TOTAL FROM dba_objects WHERE owner = :OWNER group by object_type, status",
				"criteria" : ["OWNER"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllUserObjSummaryByStatus" : {
				"default" : "SELECT object_type, count(*) as TOTAL FROM dba_objects WHERE owner = :OWNER group by object_type",
				"criteria" : ["OWNER","STATUS"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getUserObjCnt" : {
				"default" : "SELECT COUNT(*) as TOTAL FROM dba_objects WHERE owner = :OWNER",
				"criteria" : ["OWNER"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getUserObjCntByType" : {
				"default" : "SELECT OBJECT_TYPE, COUNT(*) as TOTAL FROM dba_objects WHERE owner = :OWNER group by OBJECT_TYPE",
				"criteria" : ["OWNER","OBJECT_TYPE","OBJECT_TYPE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getUserObjectsByStatus" : {
				"default" : "SELECT OBJECT_TYPE, OBJECT_NAME FROM dba_objects WHERE owner = :OWNER AND status = :STATUS",
				"criteria" : ["OWNER","STATUS"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getSchemaSizeMB" : {
				"default" : "SELECT SUM(bytes)/(1024*1024) as SIZE_MB FROM DBA_SEGMENTS WHERE owner = :OWNER",
				"criteria" : ["OWNER"],
				"return" : "RESULT",
				"sqlType" : "select"
			},

			# roles/privilege
			"isRoleExists" : {
				"default" : "SELECT role FROM dba_roles WHERE role = :ROLE",
				"criteria" : ["ROLE"],
				"return" : "EXISTENCE",
				"sqlType" : "select"
			},
			"getRoleInfo" : {
				"default" : "SELECT * FROM dba_roles WHERE role = :ROLE",
				"criteria" : ["ROLE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllRoles" : {
				"default" :  "SELECT role_name FROM dba_roles",
				"criteria" : [],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllUserRole" : {
				"default" :  "SELECT role as ROLE FROM role_tab_privs WHERE owner = :OWNER",
				"criteria" : ["OWNER"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getSysPrivsGrantedTo" : {
				"default" : "SELECT * FROM dba_sys_privs WHERE grantee = :GRANTEE",
				"criteria" : ["GRANTEE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getTabPrivsGrantedTo" : {
				"default" : "SELECT * FROM dba_tab_privs WHERE grantee = :GRANTEE",
				"criteria" : ["GRANTEE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getRoleGrantedTo" : {
				"default" : "SELECT * FROM dba_role_privs WHERE grantee = :GRANTEE",
				"criteria" : ["GRANTEE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},

			# tablespaces
			"getAllTbsInfo" : {
				"default" : "SELECT * FROM dba_tablespaces",
				"criteria" : [],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getTBSDBFiles" : {"default" : "SELECT * FROM dba_datafiles WHERE tablespace_name = :TABLESPACE_NAME",
				"criteria" : ["TABLESPACE_NAME"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getTBSSizeInfoMB" : {
				"default" :  """
					SELECT tablespace_name, SUM(dbfiles.bytes)/(1024*1024) AS SIZE_MB, SUM(free.bytes)/(1024*1024*1024) AS FREE_MB
						FROM dba_data_files dbfiles, 
							dba_free_space free
						WHERE dbfiles.tablespace_name = DECODE(:TABLESPACE_NAME,'ALL',dbfiles.tablespace_name, :TABLESPACE_NAME) 
							AND dbfiles.tablespace_name = free.tablespace_name
						GROUP BY tablespace_name
				""",
				"criteria" : ["TABLESPACE_NAME"],
				"return" : "RESULT"				,
				"sqlType" : "select"
			},

			# database/instances/sessions
			"getDBVer" : {
				"default" : "SELECT version as VERSION from v$instance",
				"criteria" : [""],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getDBDetails" : {
				"default" : "SELECT * FROM v$database",
				"criteria" : [""],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllInstDetails" : {
				"default" :  "SELECT * FROM gv$instance",
				"criteria" : [""],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getDBTimeStamp" : {
				"default" : "SELECT SYSTIMESTAMP FROM DUAL",
				"criteria" : [""],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getUserSessionDetail": {
				"default" : "SELECT * FROM v$session where username = :USERNAME",
				"criteria" : ["USERNAME"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getUserSessionDetailByStatus": {
				"default" : "SELECT * FROM v$session where username = :USERNAME AND status = :STATUS",
				"criteria" : ["USERNAME","STATUS"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getSessCntByUserStatus": {
				"default" : "SELECT count(*) as TOTAL FROM v$session where status = :STATUS AND username = :USERNAME",
				"criteria" : ["STATUS","USERNAME"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getSessCntByMachine": {
				"default" : "SELECT status, count(*) as TOTAL FROM v$session where machine = :MACHINE group by status",
				"criteria" : ["MACHINE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getSessCntByUserMachine": {
				"default" : "SELECT status, count(*) as TOTAL FROM v$session where username = :USERNAME AND machine = :MACHINE",
				"criteria" : ["MACHINE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},

			# source code
			"getDDL" : {
				"default" : "SELECT DBMS_METADATA.GET_DDL(:OBJECT_TYPE, :OBJECT_NAME, :OBJ_OWNER) FROM DUAL",
				"criteria" : ["OWNR","OBJECT_TYPE","OBJECT_NAME"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getDependentDDL" : {
				"default" : "SELECT DBMS_METADATA.GET_DEPENDENT_DDL(:OBJECT_TYPE, :OBJECT_NAME, :OBJ_OWNER) FROM DUAL",
				"criteria" : ["OWNR","OBJECT_TYPE","OBJECT_NAME"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getGrantedDDL" : {
				"default" : "SELECT DBMS_METADATA.GET_GRANTED_DDL(:GRANT_TYPE, :GRANTEE) FROM DUAL",
				"criteria" : ["GRANT_TYPE","GRANTEE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},

			# user/profile
			"isUserExists" : {
				"default" : "SELECT username FROM dba_users WHERE username = :USER_NAME",
				"criteria" : ["USER_NAME"],
				"return" : "EXISTENCE",
				"sqlType" : "select"
			},
			"isProfileExists" : {
				"default" : "SELECT PROFILE FROM dba_profiles WHERE profile = :PROFILE",
				"criteria" : ["PROFILE"],
				"return" : "EXISTENCE",
				"sqlType" : "select"
			},
			"isSysPrivsGrantedTo" : {
				"default" : "SELECT privilege FROM dba_sys_privs WHERE GRANTEE = :GRANTEE AND privilege = :PRIVILEGE",
				"criteria" : ["GRANTEE","PRIVILEGE"],
				"return" : "EXISTENCE",
				"sqlType" : "select"
			},
			"isObjPrivsGrantedTo" : {
				"default" : "SELECT privilege FROM dba_tab_privs WHERE GRANTEE = :GRANTEE AND owner = :OWNER AND object_name = :OBJECT_NAME and privilege = :PRIVILEGE",
				"criteria" : ["GRANTEE","PRIVILEGE","OWNER","OBJECT_NAME"],
				"return" : "EXISTENCE",
				"sqlType" : "select"
			},
			"getAllSchema" : {
				"default" : "SELECT distinct owner FROM dba_objects",
				"criteria" : [],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllUsers" : {
				"default" : "SELECT owner, count(*) as TOTAL_OBJECTS FROM dba_objects group by owner",
				"criteria" : [],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getAllSchemaObjSummary" : {
				"default" : "SELECT owner, object_type, status, count(*) as TOTAL FROM dba_objects group by owner, object_type, status",
				"criteria" : [],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getUserInfo" : {
				"default" : "SELECT * FROM dba_users WHERE username = :USER_NAME",
				"criteria" : ["USER_NAME"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getUserExtInfo" : {
				"default" : "SELECT * FROM sys.user$ WHERE name = :USER_NAME",
				"criteria" : ["USER_NAME"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"getProfileInfo" : {
				"default" : "SELECT * FROM dba_profiles WHERE profile = :PROFILE",
				"criteria" : ["PROFILE"],
				"return" : "RESULT",
				"sqlType" : "select"
			},

			# change user/profile
			"newUser" : {
				"default" : "CREATE USER :USER_NAME IDENTIFIED BY :PASSWORD",
				"criteria" : ["USER_NAME","PASSWORD"],
				"return" : "RESULT",
				"sqlType" : "select"
			},
			"changeUserPass" : {
				"default" : "ALTER USER :USER_NAME IDENTIFIED BY :PASSWORD",
				"criteria" : ["USER_NAME","PASSWORD"],
				"return" : "RESULT",
				"sqlType" : "ddl"
			},
			"changeUserProfile" : {
				"default" : "ALTER USER :USER_NAME PROFILE :PROFILE",
				"criteria" : ["USER_NAME","PROFILE"],
				"return" : "RESULT",
				"sqlType" : "ddl"
			},
			"lockUserAccount" : {
				"default" : "ALTER USER USER :USER_NAME ACCOUNT LOCK",
				"criteria" : ["USER_NAME"],
				"return" : "RESULT",
				"sqlType" : "ddl"
			},
			"unLockUserAccount" : {
				"default" : "ALTER USER USER :USER_NAME IDENTIFIED BY :PASSWORD ACCOUNT UNLOCK",
				"criteria" : ["USER_NAME","PASSWORD"],
				"return" : "RESULT",
				"sqlType" : "ddl"
			},
			"dropUser" : {
				"default" : "DROP USER :USER_NAME",
				"criteria" : ["USER_NAME"],
				"return" : "RESULT",
				"sqlType" : "dcl"
			},
			"grantSysPrivs2User" : {
				"default" : "GRANT :SYS_PRIVILEGE TO :GRANTEE",
				"criteria" : ["GRANTEE","SYS_PRIVILEGE"],
				"return" : "RESULT",
				"sqlType" : "dcl"
			},
			"grantObjPrivs2User" : {
				"default" : "GRANT :OBJ_PRIVILEGE ON :OBJECT TO :GRANTEE",
				"criteria" : ["GRANTEE","OBJ_PRIVILEGE","OBJECT"],
				"return" : "RESULT",
				"sqlType" : "dcl"
			},
			"revokeSysPrivsFromUser" : {
				"default" : "REVOKE :SYS_PRIVILEGE FROM :GRANTEE",
				"criteria" : ["GRANTEE","SYS_PRIVILEGE"],
				"return" : "RESULT",
				"sqlType" : "dcl"
			},
			"revokeObjPrivsFromUser" : {
				"default" : "REVOKE :OBJ_PRIVILEGE ON :OBJECT FROM :GRANTEE",
				"criteria" : ["GRANTEE","OBJ_PRIVILEGE","OBJECT"],
				"return" : "RESULT",
				"sqlType" : "dcl"
			},

			# cicd
			"getAciveAdminList" :{"default" : "SELECT * FROM  DB_MON_OWNER.VALID_DBA_LIST WHERE end_date is null"},
			"getAciveAdminListForDbTech" :{"default" : "SELECT * FROM  DB_MON_OWNER.VALID_DBA_LIST WHERE end_date is null AND db_platform = INITCAP(:DB_TECHNOLOGY)"},
			"getAppId" : {"default" : "SELECT application_id APP_ID, application_name APP_NAME, application_desc APP_DESC, application_region region, application_opco OPCO FROM db_mon_owner.application_info where application_opco = UPPER(:OPCO) AND application_region = UPPER(:REGION) AND application_name = :APP_NAME"},
			"isValidOraDBInstance" : {"default" : "SELECT COUNT(1) TOTAL FROM DB_MON_OWNER.DATABASE_DATA_WINDOW WHERE DB_NAME = :DB_INSTANCE_NAME"},
			"isValidOraDBInst" : {
				"default" : """
				SELECT COUNT(DISTINCT DB_INSTANCE) TOTAL 
					FROM db_mon_owner.cicd_application_info cicd 
					WHERE cicd.app_id = :APP_ID
						AND cicd.opco = UPPER(:OPCO)
						AND cicd.region = UPPER(:REGION)
						AND cicd.db_technology = INITCAP(:DB_TECHNOLOGY)
						AND cicd.env = UPPER(:ENV)
						AND cicd.host_name = :HOST_NAME
				"""
			},
			"isValidOraDBSchema" : {
				"default" : """
				SELECT COUNT(DISTINCT SCHEMA) TOTAL 
					FROM db_mon_owner.cicd_application_info cicd 
					WHERE cicd.app_id = :APP_ID
						AND cicd.opco = UPPER(:OPCO)
						AND cicd.region = UPPER(:REGION)
						AND cicd.db_technology = INITCAP(:DB_TECHNOLOGY)
						AND cicd.db_instance = UPPER(:DB_INSTANCE)
						AND cicd.env = UPPER(:ENV)
						AND cicd.host_name = :HOST_NAME
						AND cicd.schema = UPPER(:SCHEMA_NAME)
				"""
			},			
			"getInactiveAdminList" : {
				"default" : """
					SELECT DISTINCT
						a.db_name DB_INSTANCE_NAME,
						a.host_name HOST_NAME,
						a.db_platform DB_PLATFORM,
						a.db_type DB_TYPE,
						a.opco OPCO,
						a.db_region REGION,
						decode(a.db_type, 'PROD', 'PROD','NONPROD') ENV,
						b.username USER_NAME,
						'USER ' || b.username || ' is not on the valid DBA list as of ' || to_char(trunc(sysdate), 'MM/DD/YYYY') EVAL
					FROM db_mon_owner.database_data_window a,
							db_mon_owner.user_data_window b
					WHERE a.db_name = b.db_name
						AND a.opco = b.opco
						AND a.db_region = b.db_region
						AND a.db_type = b.db_type
						AND a.db_platform = b.db_platform
						AND a.host_name = b.host_name
						AND a.instance_number = (
							SELECT MIN(db_min.instance_number)
							FROM db_mon_owner.database_data_window db_min
							WHERE a.db_name = db_min.db_name
							AND a.opco = db_min.opco
							AND a.db_region = db_min.db_region
							AND a.db_type = db_min.db_type
							AND a.db_platform = db_min.db_platform
						)
						AND b.dba_flag = 'Y'
						AND b.username NOT IN (
							SELECT DISTINCT
								s1.DBA_USERID
								FROM db_mon_owner.VALID_DBA_LIST s1
								WHERE s1.db_platform = b.db_platform
									AND s1.start_date < b.process_date
									AND nvl(s1.end_date, sysdate + 50) > b.process_date
									AND (s1.support_regions = 'GLOBAL' or s1.support_regions like '%' || b.db_region || '%')
									AND (s1.opco = 'ALL' or s1.opco like '%' || b.opco || '%')
						) 
					"""
			},
			"getAllPendingInactiveAdminListByTech" : {
				"default" : """
					SELECT DISTINCT
						a.db_name DB_INSTANCE_NAME,
						a.host_name HOST_NAME,
						a.db_platform DB_PLATFORM,
						a.db_type DB_TYPE,
						a.opco OPCO,
						a.db_region REGION,
						decode(a.db_type, 'PROD', 'PROD','NONPROD') ENV,
						b.username USER_NAME,
						'USER ' || b.username || ' is not on the valid DBA list as of ' || to_char(trunc(sysdate), 'MM/DD/YYYY') EVAL
					FROM db_mon_owner.database_data_window a,
							db_mon_owner.user_data_window b
					WHERE a.db_name = b.db_name
						AND a.opco = b.opco
						AND a.db_region = b.db_region
						AND a.db_type = b.db_type
						AND a.db_platform = b.db_platform
						AND a.host_name = b.host_name
						AND a.db_platform = INITCAP(:DB_TECHNOLOGY)
						AND a.instance_number = (
							SELECT MIN(db_min.instance_number)
							FROM db_mon_owner.database_data_window db_min
							WHERE a.db_name = db_min.db_name
							AND a.opco = db_min.opco
							AND a.db_region = db_min.db_region
							AND a.db_type = db_min.db_type
							AND a.db_platform = db_min.db_platform
						)
						AND b.dba_flag = 'Y'
						AND b.username NOT IN (
							SELECT DISTINCT
								s1.DBA_USERID
								FROM db_mon_owner.VALID_DBA_LIST s1
								WHERE s1.db_platform = b.db_platform
									AND s1.start_date < b.process_date
									AND nvl(s1.end_date, sysdate + 50) > b.process_date
									AND (s1.support_regions = 'GLOBAL' or s1.support_regions like '%' || b.db_region || '%')
									AND (s1.opco = 'ALL' or s1.opco like '%' || b.opco || '%')
						) 
				"""
			},
			# returns all applicstion for given opco/region/technology			
			"getAllApps" : {"default" : """
				SELECT DISTINCT 
					cicd.app_id APP_ID,
					cicd.app_name APP_NAME,
					cicd.app_desc APP_DESC,
					cicd.app_opco OPCO,
					cicd.app_region REGION,
					cicd.support_team SUPPORT_TEAM,
					cicd.support_email SUPPORT_EMAIL
				FROM db_mon_owner.cicd_application_info cicd
				WHERE cicd.app_opco = UPPER(:OPCO)
					AND cicd.app_region = UPPER(:REGION)
					AND cicd.db_technology = :DB_TECHNOLOGY
				ORDER BY cicd.app_name
			"""
			},
			# returns applicstion detail for given opco/region/technology/app
			"getAnAppDetail" : {"default" : """
				SELECT distinct cicd.app_id APP_ID,
					cicd.app_name APP_NAME,
					cicd.app_desc APP_DESC,
					cicd.app_opco OPCO,
					cicd.app_region REGION,
					cicd.support_team SUPPORT_TEAM,
					cicd.support_email SUPPORT_EMAIL
				FROM db_mon_owner.cicd_application_info cicd
				WHERE cicd.app_opco = UPPER(:OPCO)
					AND cicd.app_region = UPPER(:REGION)
					AND cicd.db_technology = :DB_TECHNOLOGY
					AND cicd.app_id = :APP_ID
			"""
			},
			"getAnAppDetailByAppId" : {"default" : """
				SELECT distinct cicd.app_id APP_ID,
					cicd.app_name APP_NAME,
					cicd.app_desc APP_DESC,
					cicd.app_opco OPCO,
					cicd.app_region REGION,
					cicd.db_technology DB_TECHNOLOGY,
					cicd.support_team SUPPORT_TEAM,
					cicd.support_email SUPPORT_EMAIL
				FROM db_mon_owner.cicd_application_info cicd
				WHERE cicd.app_id = :APP_ID
			"""
			},
			# returns all environment for givern opco/region/technology/app
			"getAllAppEnvFromRepo" : {
				"default": """
					SELECT DISTINCT
						cicd.opco OPCO,
						cicd.region REGION,
						cicd.db_technology DB_TECHNOLOGY,
						cicd.host_name HOST_NAME,
						cicd.db_instance DB_INSTANCE, 
						cicd.env ENV
					FROM db_mon_owner.cicd_application_info cicd
					WHERE cicd.app_opco = UPPER(:OPCO)
						AND cicd.app_region = UPPER(:REGION)
						AND cicd.db_technology = initcap(:DB_TECHNOLOGY)
						AND cicd.app_id = :APP_ID
					ORDER BY cicd.env
					"""
			},
			# returns all database (instance) for a given opco/region/technology/App/Env
			"getAppDBInstance" : {"default" : """
				SELECT DISTINCT 
					cicd.opco OPCO,
					cicd.db_instance DB_INSTANCE,
					cicd.host_name HOST_NAME,
					cicd.db_technology DB_TECHNOLOGY,
					cicd.region REGION,
					cicd.prod_nonprod PROD_NONPROD,
					cicd.env ENV
				FROM db_mon_owner.cicd_application_info cicd
				WHERE cicd.app_id = :APP_ID
					AND cicd.opco = UPPER(:OPCO)
					AND cicd.region = UPPER(:REGION)
					AND cicd.db_technology = INITCAP(:DB_TECHNOLOGY)
					AND cicd.env = UPPER(:ENV)
			"""
			},
			# returns all database schemas for a given opco/region/technology/appId/dbname/env/host
			"getDBInstSchemas" : {"default" : """
				SELECT DISTINCT 
					cicd.schema SCHEMA
				FROM db_mon_owner.cicd_application_info cicd
				WHERE cicd.app_id = :APP_ID
					AND cicd.opco = UPPER(:OPCO)
					AND cicd.region = UPPER(:REGION)
					AND cicd.db_technology = INITCAP(:DB_TECHNOLOGY)
					AND cicd.db_instance = UPPER(:DB_INSTANCE)        
					AND cicd.env = UPPER(:ENV)
					AND cicd.host_name = :HOST_NAME
			"""
			},
			## returns all db connection string for opco/region/dbTechnology(oracle)/dbInstance/hostName
			"getDBUri" : {"default" : """
				SELECT DISTINCT
					cicd.PROD_NONPROD as ENV,
					cicd.connection_info as CONNECTION_INFO
				FROM db_mon_owner.cicd_application_info cicd
				WHERE cicd.opco = UPPER(:OPCO) 
					AND cicd.region = UPPER(:REGION)
					AND cicd.db_technology = INITCAP(:DB_TECHNOLOGY)
					AND cicd.host_name = :HOST_NAME
					AND cicd.db_instance = UPPER(:DB_INSTANCE)
					AND cicd.db_instance not like 'erp%'
				"""
			},
			## returns all db connection string for opco/region/dbTechnology(oracle)/dbInstance
			"getDBUri4DBInst" : {"default" : """
				SELECT DISTINCT
					cicd.PROD_NONPROD as ENV,
					cicd.connection_info as CONNECTION_INFO
					cicd.host_name as HOST_NAME,
				FROM db_mon_owner.cicd_application_info cicd
				WHERE cicd.opco = UPPER(:OPCO) 
					AND cicd.region = UPPER(:REGION)
					AND cicd.db_technology = INITCAP(:DB_TECHNOLOGY)
					AND cicd.db_instance = UPPER(:DB_INSTANCE)
					AND cicd.db_instance not like 'erp%'
				"""
			},
			## returns all db connection string for opco/region/dbTechnology (oracle)
			"getAllDBUri" : {"default" : """ 
				SELECT DISTINCT
					cicd.PROD_NONPROD as ENV,
					cicdvw.connection_info as CONNECTION_INFO
					cicdvw.host_name as HOST_NAME,
				FROM db_mon_owner.cicd_application_info cicd
				WHERE cicd.opco = UPPER(:OPCO) 
					AND cicd.region = UPPER(:REGION)
					AND cicd.db_technology = INITCAP(:DB_TECHNOLOGY)
					AND cicd.db_instance not like 'erp%'
				"""
			},
			"getDBList" : {
				"default" : """
					SELECT 
						DB_NAME DB_INSTANCE_NAME, 
						DB_UNIQUE_NAME, 
						DB_VERSION, 
						INSTANCE_NAME, 
						INSTANCE_NUMBER,
						PLATFORM_NAME, 
						INSTANCE_VERSION
					FROM db_mon_owner.cicd_application_info cicd
					WHERE cicd.opco = UPPER(:OPCO)
						AND cicd.region = UPPER(:REGION)
						AND cicd.db_technolog = initcap(:DB_TECHNOLOGY)
						AND DB.DB_TYPE = UPPER(:PROD_NONPROD)
				"""
			},
			"getAllSchema__old" : {
				"default" : """
					SELECT DISTINCT owner as SCHEMA FROM DBA_OBJECTS WHERE OWNER IN (SELECT username FROM DBA_USERS WHERE upper(username) not like '%SYS%')",
				""",
				"default_old" : "SELECT DISTINCT owner as SCHEMA FROM DBA_OBJECTS WHERE OWNER IN (SELECT username FROM DBA_USERS WHERE upper(username) not like '%SYS%')",
				"10" : """
					SELECT DISTINCT owner as SCHEMA 
						FROM DBA_OBJECTS 
						WHERE OWNER IN 
							(SELECT username 
								FROM DBA_USERS 
								WHERE username NOT IN 
									('ANONYMOUS','APEX_040200','APEX_PUBLIC_USER','APPQOSSYS','AUDSYS',
									 'BI','CTXSYS','DBSNMP','DIP','DVF','DVSYS','EXFSYS','FLOWS_FILES',
									 'GSMADMIN_INTERNAL','GSMCATUSER','GSMUSER','HR','IX','LBACSYS','MDDATA',
									 'MDSYS','OE','ORACLE_OCM','ORDDATA','ORDPLUGINS','ORDSYS','OUTLN','PM',
									 'SCOTT','SH','SI_INFORMTN_SCHEMA','SPATIAL_CSW_ADMIN_USR',
									 'SPATIAL_WFS_ADMIN_USR','SYS','SYSBACKUP','SYSDG','SYSKM','SYSTEM','WMSYS',
									 'XDB','SYSMAN','RMAN','RMAN_BACKUP','OWBSYS','OWBSYS_AUDIT','APEX_030200','MGMT_VIEW','OJVMSYS'))
				""",
				"11" : """
					SELECT DISTINCT owner as SCHEMA 
						FROM DBA_OBJECTS 
						WHERE OWNER IN 
							(SELECT username 
								FROM DBA_USERS 
								WHERE username NOT IN 
									('ANONYMOUS','APEX_040200','APEX_PUBLIC_USER','APPQOSSYS','AUDSYS',
									 'BI','CTXSYS','DBSNMP','DIP','DVF','DVSYS','EXFSYS','FLOWS_FILES',
									 'GSMADMIN_INTERNAL','GSMCATUSER','GSMUSER','HR','IX','LBACSYS','MDDATA',
									 'MDSYS','OE','ORACLE_OCM','ORDDATA','ORDPLUGINS','ORDSYS','OUTLN','PM',
									 'SCOTT','SH','SI_INFORMTN_SCHEMA','SPATIAL_CSW_ADMIN_USR',
									 'SPATIAL_WFS_ADMIN_USR','SYS','SYSBACKUP','SYSDG','SYSKM','SYSTEM','WMSYS',
									 'XDB','SYSMAN','RMAN','RMAN_BACKUP','OWBSYS','OWBSYS_AUDIT','APEX_030200','MGMT_VIEW','OJVMSYS'))
				""",
				"12" : "SELECT DISTINCT owner as SCHEMA FROM DBA_OBJECTS WHERE OWNER IN (SELECT username FROM DBA_USERS WHERE ORACLE_MAINTAINED = 'N')" 
			}
		}
