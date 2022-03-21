from com.mmc.common.singleton import Singleton
from com.mmc.common.utility import Utility
from com.mmc.common.error import *
from com.mmc.common.security import Security
from com.mmc.common.infrastructure import Infrastructure

from com.mmc.audit.aud_globals import AuditGlobals
from com.mmc.audit.mongo_repo import Repository
from com.mmc.audit.audit_reports import Reports

import logging, logging.config, sys, importlib

class Scheduler(object, metaclass=Singleton):
	def __init__(self, userId, userEncPass):
		try:
			self.util = Utility()
			self.infra = Infrastructure()
			self.sec = Security()

			# authenticating
			self.SECURITY_TOKEN = self.sec.authenticate(userId, userEncPass)
			self.USER_ID = userId.split("\\")[-1]

			self.sec.validateSecToken(self.SECURITY_TOKEN)

			self.Globals = AuditGlobals(self.SECURITY_TOKEN)
			self.report = Reports(self.SECURITY_TOKEN)
			self.repo = Repository(self.SECURITY_TOKEN)
			#mySchedConfigFile = self.util.buildPath(self.util.getEnvKeyVal("APP_CONFIG"),"audSchedConfig.json")

			#if not self.util.isFileExists(mySchedConfigFile):
			#	raise ValueError(f"Audit scheduler config file {mySchedConfigFile} is missing !!!")
			#getAllSchedules(self, securityToken, opco = "ALL", dbTechnology = "ALL", status = self.Globals.activeStatus)
			self.SCHED_CONF_DATA = self.repo.getAllSchedules(self.SECURITY_TOKEN)

		except Exception as error:
			raise error

	def processScheduler(self, securityToken, userId):
		try:
			print(f"{self.util.lambdaGetCurrDateTime()} - executing Audit frame work scheduler")
			for schedule in self.SCHED_CONF_DATA:

				print(f"{self.util.lambdaGetCurrDateTime()} - processing scheudle '[{schedule['name']}]'")

				# checking if this process needs to be run today
				myStartDate = self.util.removeTimeFromDate(self.util.getDateFromSched(schedule["schedule"]))
				print(f"{self.util.lambdaGetCurrDateTime()} - today is '{self.util.getCurrentDate()}', process start date >>> {myStartDate}")

				if myStartDate != self.util.getCurrentDate():
					# start date is not today for this process, skipping
					print(f"{self.util.lambdaGetCurrDateTime()} - process is not set to be run today, skipping")
					continue
				
				print(f"{self.util.lambdaGetCurrDateTime()} - scheudle '[{schedule['name']}]' is set to be run today, processing ...")

				if schedule["status"] != self.Globals.STATUS_ACTIVE:
					print(f"{self.util.lambdaGetCurrDateTime()} - scheudle '[{schedule['name']}]' is set to {schedule['status']}, skipping")

				if not("command" in schedule and schedule["command"]):
					print(f"{self.util.lambdaGetCurrDateTime()} - scheudle '[{schedule['name']}]' command is empty/missing, skipping")

				if not("program" in schedule and schedule["program"]):
					print(f"{self.util.lambdaGetCurrDateTime()} - scheudle '[{schedule['name']}]' program is empty/missing, skipping")

				if not("recepient" in schedule and schedule["recepient"]):
					print(f"{self.util.lambdaGetCurrDateTime()} - scheudle '[{schedule['name']}]' recepient is empty/missing, skipping")

				mySchedule = self.util.getACopy(schedule["schedule"])
				mySchedule.pop("return")

				myCurrentDay = self.util.getDayName4Date(self.util.getCurrentDate())

				# retrieving start and end date for a given schedule
				myCurrentWeek = self.util.getCurWeekOfYear(self.util.getCurrentDate())

				myStartDate = self.util.getDateFromSched(schedule["schedule"])

				# checking if this report is due to be sent today
				if not (self.util.removeTimeFromDate(myStartDate) == self.util.getCurrentDate()):
					print(f"{self.util.lambdaGetCurrDateTime()} - scheudle '[{schedule['name']}]' is not scheduled for today, skipping ")

				if schedule["schedule"]["freq"].lower() == "daily":
					myStartDate = self.util.getCurrentDate()
					myEndDate = self.util.getCurrentDate()

				if schedule["schedule"]["freq"].lower() == "weekly":
					myStartDate, myEndDate = self.util.getWeekStartEndDate(self.util.lambdaGetCurrDateTime())

				if schedule["schedule"]["freq"].lower() == "monthly":
					myEndDate = self.util.getMonthEndDate(myStartDate)

				if schedule["schedule"]["freq"].lower() == "quarterly":
					myEndDate = self.util.getQtrEndDate(myStartDate)

				if schedule["schedule"]["freq"].lower() == "yearly":
					myEndDate = self.util.getYearEndDate(myStartDate)

				if "program" in schedule and schedule["program"] == "python":
					# Python program needs to be executed
					if schedule["command"]["argType"] == "kw":
						# keyword arguments is needed, building arguments
						myArguments = {"securityToken" : securityToken, "recepient" : schedule["recepient"], "userId" : userId}

						# building arguments ...
						for arg in schedule["command"]["arguments"]:
							if arg["argValSource"] == "static":
								myArguments.update({arg["argKey"] : arg["argValue"]})
							elif arg["argValSource"] == "var":
								if arg["argKey"].lower() == "startdate":
									if arg["argDataType"] == "string":
										myArguments.update({arg["argKey"] : str(myStartDate)})
									else:
										myArguments.update({arg["argKey"] : myStartDate})
								if arg["argKey"].lower() == "enddate":
									if arg["argDataType"] == "string":
										myArguments.update({arg["argKey"] : str(myEndDate)})
									else:
										myArguments.update({arg["argKey"] : myEndDate})
					else:
						# positional arguments needed, we would need to sort the argument based on positional order
						myPosArguments = self.util.sortDictInListByKey(schedule["command"]["arguments"], "position")
						myArgList = [securityToken]
						for arg in myPosArguments:
							if arg["valSource"] == "static":
								myArgList.append(arg["argValue"])
						
						myArgList.append(schedule["recepient"])
						myArgList.append(userId)
						myArguments = tuple(myArgList)

					# built the arguments, now instantiating the module and class
					myModule = importlib.import_module(schedule["command"]["module"])
					myClsInstance = getattr(myModule, schedule["command"]["class"])(securityToken)
					myFactoryMethod = getattr(myClsInstance, schedule["command"]["method"])

					print("factory method >>> ", myFactoryMethod)
					print("arguments >>> ", myArguments)

					# calling requested program
					if schedule["command"]["argType"] == "kw":
						myResult = myFactoryMethod(**myArguments)
					else:
						myResult = myFactoryMethod(*myArguments)						

					print("result >> {myResult}")

				elif "program" in schedule and schedule["program"] == "os":
					# os command needs to be executed
					pass
		except Exception as error:
			raise error

if __name__ == "__main__":
	sched = Scheduler("DMZPROD01\\svc-dev-deploy-app","eXokNzl5NEUzOWdXNCkp")
	results = sched.processScheduler(sched.SECURITY_TOKEN, sched.USER_ID)
	print(results)