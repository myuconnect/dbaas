from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.globals import Globals

class PGSqlRepo(object, metaclass=Singleton):
	def __init__(self, securityToken):
		"""
		Commented block excluded from sql
		GET_ALLDATABASE_SQL
			CASE 
				WHEN pg_catalog.has_database_privilege(d.datname, 'CONNECT')
				#THEN pg_catalog.pg_size_pretty(pg_catalog.pg_database_size(d.datname))
				THEN pg_catalog.pg_database_size(d.datname)
				#ELSE 'No Access'
				ELSE 0
			END as "size",
			pg_catalog.shobj_description(d.oid, 'pg_database') as "description"

		columns for pg_tablespace: be careful using in sql, if this doesnt return a value entire role will not be returned
			pg_catalog.pg_get_userbyid((aclexplode(tbs.spcacl)).grantor) as "tbs_grantor",
			pg_catalog.pg_get_userbyid((aclexplode(tbs.spcacl)).grantee) as "tbs_grantee",
			(aclexplode(tbs.spcacl)).is_grantable as "tbs_is_grantable"

		"""
		self.util = Utility()
		self.Globals = Globals()

		self.GET_CURRENT_TXID_SQL = "SELECT txid_current()"
		self.GET_AN_EXTN_DETAILS_SQL = "SELECT * from pg_extension where extname = %(extension)s"

		# MONITORING
		# 	Blocking
		self.GET_BLOCKED_BLOCKING_SQL = """
			SELECT blocked_locks.pid     AS blocked_pid,
				blocked_activity.usename  AS blocked_user,
				blocking_locks.pid     AS blocking_pid,
				blocking_activity.usename AS blocking_user,
				blocked_activity.query    AS blocked_statement,
				blocking_activity.query   AS current_statement_in_blocking_process
			FROM  pg_catalog.pg_locks         blocked_locks
				JOIN pg_catalog.pg_stat_activity blocked_activity  ON blocked_activity.pid = blocked_locks.pid
				JOIN pg_catalog.pg_locks         blocking_locks 
					ON blocking_locks.locktype = blocked_locks.locktype
					AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
					AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
					AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
					AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
					AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
					AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
					AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
					AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
					AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
					AND blocking_locks.pid != blocked_locks.pid
				JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
			WHERE NOT blocked_locks.granted;
		"""
		self.GET_CONNECTION_STATS_SQL = """
			SELECT max_conn, used, reserved_for_super, max_conn - reserved_for_super conn_available 
				FROM (SELECT count(*) used FROM pg_stat_activity) t1,
					(SELECT setting::int reserved_for_super FROM pg_settings WHERE name ='superuser_reserved_connections') t2,
					(SELECT setting::int max_conn FROM pg_settings WHERE name = 'max_connections') t3
		"""   		
		# Session
		self.GET_USER_SESSION_STATS = """
			SELECT usename,client_addr,client_hostname,state, count(*) 
				FROM pg_stat_activity 
				WHERE usename IS NOT NULL 
				GROUP BY usename,client_addr,client_hostname,state
		"""
		self.GET_USER_SESSION_DETAILS = "SELECT * FROM pg_stat_activity WHERE usename = %(username)s"

		self.GET_SESSION_SQL = """
			SELECT pid as "process_id", usename as "username", datname as "database_name", client_addr as "client_address", application_name,
				backend_start,	state, state_change, pg_blocking_pids(pid) as blocked_by, query as blocked_query
			FROM pg_catalog.pg_stat_activity
		"""
		#where cardinality(pg_blocking_pids(pid)) > 0;
		self.GET_LOCK_SQL = """
			SELECT pid as "process_id", usename as "username", datname as "database_name", client_addr as "client_address", application_name,
				backend_start,	state, state_change, pg_blocking_pids(pid) as blocked_by, query as blocked_query
			FROM pg_catalog.pg_stat_activity
			WHERE pid in (
				SELECT pid 
				FROM pg_catalog.pg_locks lock
					JOIN pg_catalog.pg_class class ON class.oid = lock.relation and class.relkind = 'r'
			)
		"""

		# Bloating
		self.GET_BLOATING_SQL = """
			SELECT current_database(), schemaname, tablename, /*reltuples::bigint, relpages::bigint, otta,*/
				ROUND((CASE WHEN otta=0 THEN 0.0 ELSE sml.relpages::float/otta END)::numeric,1) AS tbloat,
				CASE WHEN relpages < otta THEN 0 ELSE bs*(sml.relpages-otta)::BIGINT END AS wastedbytes,
				iname, /*ituples::bigint, ipages::bigint, iotta,*/
				ROUND((CASE WHEN iotta=0 OR ipages=0 THEN 0.0 ELSE ipages::float/iotta END)::numeric,1) AS ibloat,
				CASE WHEN ipages < iotta THEN 0 ELSE bs*(ipages-iotta) END AS wastedibytes
			FROM (
				SELECT schemaname, tablename, cc.reltuples, cc.relpages, bs,
					CEIL((cc.reltuples*((datahdr+ma-
						(CASE WHEN datahdr%ma=0 THEN ma ELSE datahdr%ma END))+nullhdr2+4))/(bs-20::float)) AS otta,
					COALESCE(c2.relname,'?') AS iname, COALESCE(c2.reltuples,0) AS ituples, COALESCE(c2.relpages,0) AS ipages,
					COALESCE(CEIL((c2.reltuples*(datahdr-12))/(bs-20::float)),0) AS iotta -- very rough approximation, assumes all cols
				FROM (
					SELECT ma,bs,schemaname,tablename,
						(datawidth+(hdr+ma-(case when hdr%ma=0 THEN ma ELSE hdr%ma END)))::numeric AS datahdr,
						(maxfracsum*(nullhdr+ma-(case when nullhdr%ma=0 THEN ma ELSE nullhdr%ma END))) AS nullhdr2
				FROM (
					SELECT schemaname, tablename, hdr, ma, bs,
						SUM((1-null_frac)*avg_width) AS datawidth,
						MAX(null_frac) AS maxfracsum,
						hdr+(
							SELECT 1+count(*)/8
							FROM pg_stats s2
							WHERE null_frac<>0 AND s2.schemaname = s.schemaname AND s2.tablename = s.tablename
						) AS nullhdr
					FROM pg_stats s, (
						SELECT
							(SELECT current_setting('block_size')::numeric) AS bs,
								CASE WHEN substring(v,12,3) IN ('8.0','8.1','8.2') THEN 27 ELSE 23 END AS hdr,
								CASE WHEN v ~ 'mingw32' THEN 8 ELSE 4 END AS ma
							FROM (SELECT version() AS v) AS foo
					) AS constants
					GROUP BY 1,2,3,4,5
				) AS foo
			) AS rs
			JOIN pg_class cc ON cc.relname = rs.tablename
			JOIN pg_namespace nn ON cc.relnamespace = nn.oid AND nn.nspname = rs.schemaname AND nn.nspname <> 'information_schema'
			LEFT JOIN pg_index i ON indrelid = cc.oid
			LEFT JOIN pg_class c2 ON c2.oid = i.indexrelid
			) AS sml
			ORDER BY wastedbytes DESC
		"""

		# REPLICATION PRIMARY
		self.IS_PRIMARY_SQL = "SELECT pg_is_in_recovery()"		
		self.GET_REPL_STAT_SQL = "SELECT * from pg_stat_replication"
		self.GET_REPL_SLOTS_SQL = "SELECT * from pg_replication_slots"
		self.GET_ARCHIVER_STATS_SQL = "SELECT * from pg_stat_archiver"
		self.GET_REPLICATION_SLOTS_SQL = "SELECT * FROM pg_replication_slots"
		self.GET_REPL_LAG_STAT_SQL = """
			SELECT pg_last_wal_receive_lsn() receive, 
				pg_last_wal_replay_lsn() replay,
				(extract(epoch FROM now()) - extract(epoch FROM pg_last_xact_replay_timestamp()))::int lag
		"""
		self.GET_REPL_LAG_STAT_v9_SQL = """
			SELECT pg_last_xlog_replay_location() receive, 
				pg_last_xlog_replay_location() replay,
				(extract(epoch FROM now()) - extract(epoch FROM pg_last_xact_replay_timestamp()))::int lag
		"""
		self.CONV_LSN2WAL_FILE_SQL = "select pg_walfile_name()"
		self.GET_CURR_WAL_LSN_SQL = "select pg_current_wal_lsn()"
		self.GET_CURR_WAL_LSN_v9_SQL = "select pg_current_xlog_location()"
		self.GET_PRIMARY_REP_DETAILS = """
			SELECT client_hostname, application_name, state, 
				sent_lsn as "last_lsn_sent", cfg.setting || '/pg_wal/' || pg_walfile_name(sent_lsn) as "last_walfile_sent", 
				pg_current_wal_lsn() as "current_lsn", 
				cfg.setting || '/pg_wal/' || pg_walfile_name(pg_current_wal_lsn()) as "current_wal_file" 
			FROM pg_stat_replication rep, pg_settings cfg where cfg.name='data_directory'
		"""
		self.GET_PRIMARY_REP_DETAILS = """
			SELECT
				client_addr AS client, usename AS user, application_name AS name,
				state, sync_state AS mode,
				(pg_wal_lsn_diff(pg_current_wal_lsn(),sent_lsn) / 1024)::bigint as pending,
				(pg_wal_lsn_diff(sent_lsn,write_lsn) / 1024)::bigint as write,
				(pg_wal_lsn_diff(write_lsn,flush_lsn) / 1024)::bigint as flush,
				(pg_wal_lsn_diff(flush_lsn,replay_lsn) / 1024)::bigint as replay,
				(pg_wal_lsn_diff(pg_current_wal_lsn(),replay_lsn))::bigint / 1024 as total_lag
				FROM pg_stat_replication
		"""
		self.GET_WAL_FILE_NAME_FROM_REC_LSN_SQL = "SELECT pg_walfile_name(pg_last_wal_receive_lsn())"
		self.GET_WAL_FILE_NAME_FROM_REPLAY_LSN_SQL = "SELECT pg_walfile_name(pg_last_wal_replay_lsn())"

		# REPLICATION SECONDARY
		self.GET_REPL_WAL_RECEIVER_STAT_SQL = "SELECT * FROM pg_stat_wal_receiver"
		self.GET_REPL_WAL_RECEIVER_STAT_SQL = "SELECT * FROM pg_stat_wal_receiver"
		self.GET_REPL_RECOVERY_STATUS_SQL = "SELECT pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn(), pg_last_xact_replay_timestamp()"
		self.GET_REPL_LAG_SECS_SQL = "SELECT now()-pg_last_xact_replay_timestamp() as replication_lag"
		self.GET_PRIMARY_SERVER_AKA_WAL_RECEIVER_SQL = "SELECT * FROM pg_stat_wal_receiver"

		# DB SCAN
		self.GET_CURRENT_DBNAME_SQL = "SELECT current_database()"
		self.GET_PG_SETTINGS_SQL = "SELECT * FROM pg_settings"
		self.GET_PG_FILE_SETTINGS_SQL = "SELECT * FROM pg_file_settings"
		self.GET_A_CONFIG_SETTING_SQL = "SELECT * setting FROM pg_settings where name = %(config_name)s"
		self.GET_PG_HBA_FILE_RULE_SQL = "SELECT * FROM pg_hba_file_rules"
		self.GET_RECOVERY_FILE_CONTENT_SQL = "SELECT * FROM pg_read_file('recovery.conf')"
		self.GET_DB_VERSION_SQL = "SELECT current_setting('server_version') as server_version"

		"""
		select pg_current_wal_lsn();
		select pg_wal_location_diff('32/1B000028','32/1B0000D0');
		"""		
		self.GET_DBUSER_ROLE_SQL = """
			SELECT r.rolname as "user_role", r.rolsuper as "super", r.rolinherit as "inherit", r.rolcreaterole as "is_create_role", 
				r.rolcreatedb as "is_create_db", r.rolcanlogin as "is_login",r.rolconnlimit as "conn_limit", 
				r.rolvaliduntil as "valid_until",
				ARRAY( SELECT b.rolname
					FROM pg_catalog.pg_auth_members m
						JOIN pg_catalog.pg_roles b ON (m.roleid = b.oid)
					WHERE m.member = r.oid) as memberof, 
				r.rolreplication, 
				r.rolbypassrls
			FROM pg_catalog.pg_roles r
			WHERE r.rolname !~ '^pg_'
			ORDER BY 1
		"""
		self.GET_ALL_DATABASES_SQL = """
			SELECT db.datname as "name",
				pg_catalog.pg_get_userbyid(db.datdba) as "owner",
				pg_catalog.pg_encoding_to_char(db.encoding) as "encoding",
				db.datcollate as "collation",
				db.datctype as "ctype",
				pg_catalog.array_to_string(db.datacl, E'\n') AS "access_privileges",
				CASE 
					WHEN pg_catalog.has_database_privilege(db.datname, 'CONNECT')
					THEN pg_catalog.pg_database_size(db.datname)
					ELSE 0
				END as "size",
			FROM pg_catalog.pg_database db
			ORDER BY 1
		"""
		self.GET_ALL_DATABASES_TBS_SQL = """
			SELECT db.datname as "db_name",
				pg_catalog.pg_get_userbyid(db.datdba) as "db_owner",
				pg_catalog.pg_encoding_to_char(db.encoding) as "db_encoding",
				db.datcollate as "db_collation",
				db.datctype as "db_ctype",
				pg_catalog.array_to_string(db.datacl, E'\n') AS "db_access_privileges",
				CASE 
					WHEN pg_catalog.has_database_privilege(db.datname, 'CONNECT')
					THEN pg_catalog.pg_database_size(db.datname)
					ELSE 0
				END as "db_size",
				tbs.spcname as "tbs_name",
				pg_catalog.pg_tablespace_location(tbs.oid) AS "tbs_loc",
				pg_catalog.pg_tablespace_size(tbs.oid) AS "tbs_size"
			FROM pg_catalog.pg_database db
				JOIN pg_catalog.pg_tablespace tbs on db.dattablespace = tbs.oid
			ORDER BY 1
		"""
		#pg_catalog.pg_tablespace_size(spcname) AS "size1",
		self.GET_ALL_TABLESPACES_SQL = """
			SELECT spcname AS "tablespace_name",
				pg_catalog.pg_get_userbyid(spcowner) AS "owner",
				pg_catalog.pg_tablespace_location(oid) AS "location",
				pg_catalog.array_to_string(spcacl, E'\n') AS "access_privilege",
				spcoptions AS "options",
				pg_catalog.pg_size_pretty(pg_catalog.pg_tablespace_size(oid)) AS "pretty_size",
				pg_catalog.pg_tablespace_size(oid) AS "size",
				pg_catalog.shobj_description(oid, 'pg_tablespace') AS "description"
			FROM pg_catalog.pg_tablespace
			ORDER by 1
		"""
		self.GET_A_DB_TABLESPACE_SQL = """
			SELECT db.datname as "db_name",
				pg_catalog.pg_get_userbyid(db.datdba) as "db_owner",
				pg_catalog.pg_encoding_to_char(db.encoding) as "db_encoding",
				db.datcollate as "db_collation",
				db.datctype as "db_ctype",
				pg_catalog.array_to_string(db.datacl, E'\n') AS "db_access_privileges",
				CASE 
					WHEN pg_catalog.has_database_privilege(db.datname, 'CONNECT')
					THEN pg_catalog.pg_database_size(db.datname)
					ELSE 0
				END as "db_size",
				tbs.spcname as "tbs_name",
				pg_catalog.pg_tablespace_location(tbs.oid) AS "tbs_loc",
				pg_catalog.pg_tablespace_size(tbs.oid) AS "tbs_size"
			FROM pg_catalog.pg_database db
				JOIN pg_catalog.pg_tablespace tbs on db.dattablespace = tbs.oid
			WHERE db.datname = %(db_name)s
			ORDER BY 1		
		"""
		self.GET_SCHEMA_STATS_SQL_OLD = """
			SELECT nspace.nspname AS "name",
				pg_catalog.pg_get_userbyid(nspace.nspowner) AS "owner",
				pg_catalog.array_to_string(nspace.nspacl, E'\n') AS "access_privs",
				pg_catalog.obj_description(nspace.oid, 'pg_namespace') AS "description",
				pg_catalog.pg_relation_size(class.oid)
			FROM pg_catalog.pg_namespace nspace
				JOIN pg_catalog.pg_class class
					ON nspace.oid = class.relnamespace
			WHERE nspace.nspname !~ '^pg_' AND nspace.nspname <> 'information_schema'
			ORDER BY 1
		"""
		self.GET_SCHEMA_STATS_SQL = """		
			WITH recursive all_elements AS (
				SELECT 'base/' || l.filename AS path, x.*
				FROM pg_ls_dir('base/') AS l (filename),
					LATERAL pg_stat_file( 'base/' || l.filename) AS x
				UNION ALL
				SELECT 'pg_tblspc/' || l.filename AS path, x.*
				FROM pg_ls_dir('pg_tblspc/') AS l (filename),
					LATERAL pg_stat_file( 'pg_tblspc/' || l.filename) AS x
				UNION ALL
				SELECT u.path || '/' || l.filename, x.*
				FROM all_elements u,
					lateral pg_ls_dir(u.path) AS l(filename),
					lateral pg_stat_file( u.path || '/' || l.filename ) AS x
				WHERE u.isdir
			), 
			all_files AS (
				SELECT path, SIZE 
				FROM all_elements WHERE NOT isdir), 
			interesting_files AS (
				SELECT regexp_replace(regexp_replace(file.path, '.*/', ''),'\.[0-9]*$','') AS filename, SUM( file.size )
				FROM pg_database db,
					all_files file
				WHERE db.datname = current_database() AND
					file.path ~ ( '/' || db.oid || E'/[0-9]+(\\.[0-9]+)?$' )
				GROUP BY filename
			)
			SELECT
				nspace.nspname AS schema_name,
				pg_catalog.array_to_string(nspace.nspacl, E'\n') AS "access_privs",
				pg_catalog.obj_description(nspace.oid, 'pg_namespace') AS "description",    
				pg_catalog.pg_get_userbyid(nspace.nspowner) AS "owner",
				SUM( file.sum ) AS size
			FROM interesting_files file
				JOIN pg_class class ON file.filename::oid = class.relfilenode
				LEFT OUTER JOIN pg_class dtc ON dtc.reltoastrelid = class.oid AND class.relkind = 't'
				JOIN pg_namespace nspace ON COALESCE( dtc.relnamespace, class.relnamespace ) = nspace.oid
			GROUP BY nspace.nspname,
				pg_catalog.array_to_string(nspace.nspacl, E'\n'),
				pg_catalog.obj_description(nspace.oid, 'pg_namespace'),
				pg_catalog.pg_get_userbyid(nspace.nspowner)
			ORDER BY size DESC
		"""
		self.GET_ALL_SCHEMA_OBJECTS_STATS_SQL = """
			SELECT nspace.nspname as schema_name,
				CASE class.relkind
					WHEN 'r' THEN 'table'
					WHEN 'v' THEN 'view'
					WHEN 'i' THEN 'index'
					WHEN 'S' THEN 'sequence'
					WHEN 's' THEN 'special'
					WHEN 'm' THEN 'materialized_view'
					WHEN 'f' THEN 'foreign table'
				END as object_type,
				count(1) as object_count,
				sum(class.reltuples) est_tuples_count,
				sum(pg_catalog.pg_total_relation_size(class.oid)) as size
			FROM pg_catalog.pg_class class
				LEFT JOIN pg_catalog.pg_namespace nspace ON nspace.oid = class.relnamespace
			WHERE class.relkind IN ('r','v','i','S','s','m','f') AND
				nspace.nspname !~ '^pg_' AND nspace.nspname <> 'information_schema'
			GROUP BY  nspace.nspname,
				class.relkind
			ORDER BY 1,2
		"""
		self.GET_A_SCHEMA_OBJECTS_STATS_SQL = """
			SELECT nspace.nspname as schema_name,
				CASE class.relkind
					WHEN 'r' THEN 'table'
					WHEN 'v' THEN 'view'
					WHEN 'i' THEN 'index'
					WHEN 'S' THEN 'sequence'
					WHEN 's' THEN 'special',
					WHEN 'm' THEN 'materialized_view',
					WHEN 'f' THEN 'foreign table'
				END as object_type,
				count(1) as object_count,
				sum(class.reltuples) est_tuples_count,
				sum(pg_catalog.pg_total_relation_size(class.oid)) as size				
			FROM pg_catalog.pg_class class
				LEFT JOIN pg_catalog.pg_namespace nspace ON nspace.oid = class.relnamespace
			WHERE class.relkind IN ('r','v','i','S','s','m','f') AND
				nspace.nspname !~ '^pg_' AND nspace.nspname <> 'information_schema' AND
				nspace.nspname = %(schema_name)s
			GROUP BY  nspace.nspname,
				class.relkind
			ORDER BY 1,2
		"""
		self.GET_ALL_SCHEMA_OBJECTS_SQL = """
			SELECT nspace.nspname as schema_name,
				pg_catalog.pg_get_userbyid(class.relowner) as "owner",
				CASE class.relkind
					WHEN 'r' THEN 'table'
					WHEN 'v' THEN 'view'
					WHEN 'i' THEN 'index'
					WHEN 'S' THEN 'sequence'
					WHEN 's' THEN 'special'
					WHEN 'm' THEN 'materialized_view'
					WHEN 'f' THEN 'foreign table'
				END as object_type,
				class.relname as "object_name",
				class.reltuples as "est_tuple_count",				
				pg_catalog.pg_total_relation_size(class.oid) as "size"
				FROM pg_catalog.pg_class class
					LEFT JOIN pg_catalog.pg_namespace nspace ON nspace.oid = class.relnamespace
				WHERE class.relkind IN ('r','v','i','S','s','m','f') AND
					nspace.nspname !~ '^pg_' AND nspace.nspname <> 'information_schema'
				ORDER BY 1,2
		"""
		self.GET_USER_OBJECTS_SQL = """
			SELECT nsp.nspname as SchemaName,
				cls.relname as ObjectName,
				rol.rolname as ObjectOwner,
				case cls.relkind
			        when 'r' then 'TABLE'
			        when 'm' then 'MATERIALIZED_VIEW'
			        when 'i' then 'INDEX'
			        when 'S' then 'SEQUENCE'
			        when 'v' then 'VIEW'
			        when 'c' then 'TYPE'
			        else cls.relkind::text
			    end as ObjectType,
				class.reltuples as "est_tuple_count",				
				pg_catalog.pg_total_relation_size(class.oid) as "size"			    
			FROM pg_class cls
			JOIN pg_roles rol 
				on rol.oid = cls.relowner
			JOIN pg_namespace nsp 
				on nsp.oid = cls.relnamespace
			WHERE nsp.nspname not in ('information_schema', 'pg_catalog')
			    AND nsp.nspname not like 'pg_toast%'
			    AND rol.rolname = %(user_name)s
			ORDER BY nsp.nspname, cls.relname
		"""
		self.GET_ALL_EXTENSIONS_DETAIL_SQL = """		
			SELECT extn.oid as "oid", extn.extname as "extension_name", pg_catalog.pg_describe_object(depend.classid, depend.objid, 0) AS "description"
			FROM pg_catalog.pg_extension extn
				JOIN pg_catalog.pg_depend depend on depend.refclassid = 'pg_catalog.pg_extension'::pg_catalog.regclass AND
					depend.refobjid = extn.oid AND depend.deptype = 'e'
			ORDER by 2
		"""

		#current_setting('ssl_library') as "ssl_library", only available after version 12
		self.GET_DB_SERVER_CONFIG_SQL = """
			SELECT current_setting('block_size') as "block_size",
				current_setting('data_checksums') as "is_data_chksum_enabled",
				current_setting('data_directory_mode') as "data_dir_mode",
				current_setting('debug_assertions') as "is_debug_assert_enabled",
				current_setting('integer_datetimes') as "is_64bit_int_datetime",
				current_setting('lc_collate') as "collation",
				current_setting('lc_ctype') as "ctype",
				current_setting('max_function_args') as "max_function_args",
				current_setting('max_identifier_length') as "max_identifier_length",
				current_setting('max_index_keys') as "max_index_keys",
				current_setting('segment_size') as "segment_size",
				current_setting('server_encoding') as "server_encoding",
				current_setting('server_version') as "server_version",
				current_setting('server_version_num') as "server_version_num",
				current_setting('wal_block_size') as "wal_block_size",
				current_setting('wal_segment_size') as "wal_segment_size"
		"""

		# get all slave information
		self.GET_ALL_SLAVE_DETAILS_SQL = "SELECT * FROM pg_stat_replication"
		self.GET_PRIMARY_DETAILS_SQL = "SELECT * FROM pg_stat_wal_receiver"

		self.CREATE_PG_AUDIT_LOG_TABLE_SQL = """
			CREATE TABLE postgres_log
				(
					log_time timestamp(3) with time zone,
					user_name text,
					database_name text,
					process_id integer,
					connection_from text,
					session_id text,
					session_line_num bigint,
					command_tag text,
					session_start_time timestamp with time zone,
					virtual_transaction_id text,
					transaction_id bigint,
					error_severity text,
					sql_state_code text,
					message text,
					detail text,
					hint text,
					internal_query text,
					internal_query_pos integer,
					context text,
					query text,
					query_pos integer,
					location text,
					application_name text,
					PRIMARY KEY (session_id, session_line_num)
				)
		"""
		# objects		
		self.GET_ALL_PROCS = """
			SELECT n.nspname as schema_name,
				p.proname as specific_name,
				l.lanname as language,
				case 
					when l.lanname = 'internal' then p.prosrc
					else pg_get_functiondef(p.oid)
				end as definition,
				pg_get_function_arguments(p.oid) as arguments
			from pg_proc p
				left join pg_namespace n on p.pronamespace = n.oid
				left join pg_language l on p.prolang = l.oid
				left join pg_type t on t.oid = p.prorettype 
			where n.nspname not in ('pg_catalog', 'information_schema') and p.prokind = 'p'
			order by schema_name, specific_name
		"""
