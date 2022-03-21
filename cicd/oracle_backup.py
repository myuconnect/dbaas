from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.security import Security
from com.mmc.common.infrastructure import Infrastructure
from com.mmc.common.globals import Globals

import logging, logging.config, sys

import os, json

class OraBackup(object, metaclass=Singleton):
	def __init__(self, securityToken, ):
		self.sec = Security()
		self.util = Utility()
		#self.infra = Infrastructure()
		self.Globals = Globals()

		self.SECURITY_TOKEN=securityToken
		#self.ENVIRONMENT = self.util.getACopy(self.infra.environment)

		self.sec.validateSecToken(securityToken)

		"""
		An ocp tool stands for "Oracle Copy" and written exactly for the purpose of copying dump files back and forth from/to a 
		database server. It is available here: https://github.com/maxsatula/ocp/releases/download/v0.1/ocp-0.1.tar.gz 
		That is a source distribution, so once downloaded and unpacked, run ./configure && make
		ocp <connection_string> DATA_PUMP_DIR:remote_file_name.dmp local_file_name.dmp
		"""
		
	def bkpExpDpSchemaAPI(self, connection, securityToken, dirObj, logfile, dumpFile, schema, filter):
		try:
			
		except Exception as error:
			raise error