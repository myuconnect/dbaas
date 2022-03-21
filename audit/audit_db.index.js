db.tenant.audits.createIndex(
	{
		"ts":1,"opco":1,"env":1,"dbTechnology":1,"region":1,"tenantName":1
	},
	{
		"name":"tenantAudits_ts_opco_env_dbTech_tenantName","background":true
	}
);

db.hosts.createIndex(
	{"hostName" : 1, "opco" : 1, "env" : 1, "region" : 1, "dcLocation" : 1},
	{"name":"hosts_name_opco_env_region_dcLocation","background":true});

