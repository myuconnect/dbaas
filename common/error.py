from com.mmc.common.singleton import Singleton

class InvalidArguments(Exception, metaclass=Singleton):
	def __init__(self, message, errors):
		super(InvalidArguments, self).__init__(message)
		# log the error if thats possible to current log
		self.errors = errors
		self.message = message
	

