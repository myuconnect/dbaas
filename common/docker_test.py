import json, os, sys, datetime, time, subprocess
class Utility(object):
	def __init__(self):
		pass
		#lambda functions

	# file functions
	def __repr__(self):
		return "(%s)" % (self.__class__)

	def __str__(self):
		return "(%s)" % (self.__class__)

	def execOSCmdRetResult(self, osCmd):
		#print('os >>>', osCmd)
		processHandle = subprocess.Popen(osCmd, shell=True, stdout=subprocess.PIPE)
		result = processHandle.communicate()
		# result is tuple, 1st value is data and 2nd value is error
		return result

if __name__ == "__main__":
	util = Utility()

	# testing docker
	#getMongoDockerContainerCmd = "/bin/docker ps --format {{.Names}} {{.Command}} | grep -i \"mongod -f\" | awk '{print $1}'"
	getMongoDockerContainerCmd = "/bin/docker ps --format \"{{.Names}} {{.Command}}\" | grep -i \"mongod -f\" "
	getDockerConfigCmd = "/bin/docker inspect {container}"

	myResult = util.execOSCmdRetResult(getMongoDockerContainerCmd)
	myDockerContainerResult = myResult[0]

	for result in myDockerContainerResult.splitlines():
		#print("container result", result)
		
		container = result.decode("utf-8").split(" ")[0]

		mongoConfFile = result.decode("utf-8").split(" ")[1]
		
		dockerConfig = util.execOSCmdRetResult(getDockerConfigCmd.format(container=container))
		#dockerConfigDict = util.convStrToDict(dockerConfig)
		dockerConfig = dockerConfig[0] 
		dockerConfigDict = json.loads(dockerConfig)
		myMonngoConfInDockerConfig = dockerConfigDict[0]["Args"][1]

		myMongoConfResult = [bind.split(":")[0] for bind in dockerConfigDict[0]["HostConfig"]["Binds"] if myMonngoConfInDockerConfig in bind]
		myMongoConfFile = myMongoConfResult[0] 
		print("container - ", container.decode("utf-8"), ", mongo conf file >>> ", myMongoConfFile.decode("utf-8"))
