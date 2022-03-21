db.tenant.audits.createIndex(
	{
		"ts":1,"opco":1,"env":1,"dbTechnology":1,"region":1,"tenantName":1
	},
	{
		"name":"tenantAudits_ts_opco_env_dbTech_tenantName","background":true
	}
);

db.tenant.audits.createIndex(
	{
		"ts":1,"tenantName":1
	},
	{
		"name":"tenantAudits_ts_tenantName",
		"background":true
	}
);

db.tenant.auth.audits.createIndex(
	{
		"ts":1,
	},
	{
		"name":"tenantAuthAud_tls_ts_3months",
		"expireAfterSeconds" : 7890000,
		"background":true
	}
);

db.hosts.createIndex(
	{"hostName" : 1, "opco" : 1, "env" : 1, "region" : 1, "dcLocation" : 1},
	{"name":"hosts_name_opco_env_region_dcLocation","background":true});


use admin
db.adminCommand({setParameter: 1, internalQueryExecMaxBlockingSortBytes: 335544320})
