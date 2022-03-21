from com.mmc.common.singleton import Singleton
from secrets import token_urlsafe
from ldap3 import Server, Connection


import base64, os, getpass, json, sys, datetime

# we want to log as how many times encryption methods are called ???

class Security(object, metaclass=Singleton):
#class Security(object):
	def __init__(self):
		self.SECURITY_TOKEN = ""
		self.AD_REALM = ""
		self.AD_SERVER_PORT = "usdfw1.ldap.corp.mmco.int:389"
		self.TEMP_SEC_TOKEN = "23$$#$#$!feeRSsdafsdfl%$"
		self.RESTAPI_URL="http://usdfw21as383v:8000/api/audit/processRequest"
		# loading the api key VAULT

		# building VAULT file name
		try:
			#myAppCfgKey = "".join([os.getenv("APP_NAME").upper(),"_CONFIG"])
			myAppCfgLoc = os.getenv("APP_CONFIG")

			"""
			if not myAppCfgLoc:
				raise ValueError(f"Could not find Security Vault file location, ensure {myAppCfgKey} env variable is set !!!")

			#print("cfg loc >>>", myAppCfgLoc)
			"""
			if myAppCfgLoc:
				self.APIVAULT_FILE = os.path.join(myAppCfgLoc ,"api_vault.json")

				if not os.path.exists(self.APIVAULT_FILE):
					self.APIVAULT_FILE = ""
					#raise ValueError(f"Security vault file {self.APIVAULT_FILE} is missing !!!")

		except Exception as error:
			raise ValueError(f"An error '{error}'' occurred while load security vault !!!")
		#self.APIKEY_VAULT = []
		#self.APIKEY_VAULT = self.loadApiKey(self.APIVAULT_FILE)

	def __repr__(self):
		return "(%s, %s)" % (self.__class__)

	def __str__(self):
		return "(%s, %s)" % (self.__class__)

	def convertDT2IsoFormat(self, dateTimeObj):
		"""
		converts date time object stored in a string to a date time object. Used in json dumps to convert dt str to dt object
		"""
		if isinstance(dateTimeObj, (datetime.datetime, datetime.date)):
			return  dateTimeObj.isoformat()

	def saveApiKey(self, userId, userPass):
		"""
		authenticate the user, if successful create apikey, store and return api key
		"""
		try:
			#authenticating user
			conn = Connection(self.AD_SERVER_PORT, userId, password = userPass, authentication='NTLM', raise_exceptions=True)
			# binding to check to see if we have valid credentials, once bind is successful, we can start tls tunnerl to perform
			# further action
			if not conn.bind():
				raise ValueError("unsuccessful bind for credential provided !!!")

			# user is authenticated, creating api key
			myDomain = userId.split("\\")[0]
			myUserId = userId.split("\\")[1]
			myApiKey = token_urlsafe(64)

			userApiKeyData = {
				"ts" : datetime.datetime.now(),
				"domain" : myDomain,
				"userId" : myUserId,
				"apiKey" : myApiKey,
				"status" : "active"
			}

			# loading existing data
			myAllApiKeyData = self.loadApiKey(self.APIVAULT_FILE)
			if not myAllApiKeyData:
				myAllApiKeyData = []

			if not isinstance(myAllApiKeyData, list):
				myAllApiKeyData = [myAllApiKeyData]

			myAllApiKeyData.append(userApiKeyData)

			if os.path.exists(self.APIVAULT_FILE):
				raise ValueError(f"Security vault file '{self.APIVAULT_FILE}' is missing !!!")
			
			# saving user apikey
			with open(self.APIVAULT_FILE, 'w') as file:
				# using convertDT2IsoFormat to convert datetime to isoformat in str
				json.dump(myAllApiKeyData, file, indent = 3, default=self.convertDT2IsoFormat)

			return myApiKey

		except Exception as error:
			raise error

	def loadApiKey(self, apiKeyFile):
		"""
		Load api key
		"""
		try:
			myAllApiKeyInVAULT = []
			if os.path.exists(apiKeyFile):
				with open(apiKeyFile) as file:
					myAllApiKeyInVAULT = json.load(file)
			
			return myAllApiKeyInVAULT

		except Exception as error:
			raise error

	def isValidApiKey(self, userId, userApiKey):
		"""
		checks if passed userid and api key exists
		"""
		try:
			apiKeyFound = False
			myAllApiKeyInVault = self.loadApiKey(self.APIVAULT_FILE)

			if not myAllApiKeyInVault:
				print(f"unable to validate api key since api vault is empty, switching to LDAP auth")
				return apiKeyFound

			myDomain = userId.split("\\")[0].strip()
			myUserId = userId.split("\\")[-1].strip()

			myUserApiKey = userApiKey.strip()

			"""
			if not myAllApiKeyInVault:
				# we have got an empty vault file, will check if we can authenticate using rest api
				#remove domain if passed
			"""
			#print(f"vault >>> {myAllApiKeyInVault}")
			print(f"validting data >>> domain : '{myDomain}', userId : '{myUserId}', apiKey : '{myUserApiKey}' ")

			for key in myAllApiKeyInVault:
				print(f"processing >>> domain : '{key['domain']}', userId : '{key['userId']}', apiKey : '{key['apiKey']}', status : '{key['status']}' ")
				#if key["domain"] == myDomain and key["userId"] == myUserId and key["apiKey"] == myUserApiKey and key["status"].lower() == "active":
				if key["userId"].lower() == myUserId.lower() and key["apiKey"] == myUserApiKey and key["status"].lower() == "active":
					apiKeyFound = True
					break

			return apiKeyFound

		except Exception as error:
			raise error

	def __genSHA256Key(self, passPhrase):
		try:
			myModuleName = sys._getframe().f_code.co_name
			
			myPassPhrase = passPhrase.encode()
			mySalt = os.urandom(16)
			kdf = PBKDF2HMAC(
				algorithm=hashes.SHA256(),
				length=32,
				salt=mySalt,
				iterations=100000,
				backend=default_backend()
				)
			return base64.urlsafe_b64encode(kdf.derive(myPassPhrase))
		except Exception as error:
			raise error
		#return Fernet.generate_key(passPhraseKey)

	def __encryptText(self, secretText):
		#return Fernet(key).encrypt(text.encode())
		try:
			return (base64.b64encode(secretText.encode()))
		except Exception as error:
			raise error

	def __decryptText(self, encryptText):
		try:
			#if not isinstance(encryptText, bytes):
			#	myEncryptText = encryptText.encode('utf-8')
			#else:
			#	myEncryptText = encryptText

			myDecryptText = base64.b64decode(encryptText)

			if isinstance(myDecryptText, bytes):
				return myDecryptText.decode()
			else:
				return myDecryptText.decode()

		except Exception as error:
			# we got error here, returning passed encryptText
			return encryptText

	def __getKey(self, nameSpace, keyFile):
		try:
			myModuleName = sys._getframe().f_code.co_name

			with open(keyFile) as file:
				allKeys = json.load(file)
			#print(allKeys)
			if allKeys and nameSpace in allKeys:
				return allKeys[nameSpace]
			else:
				raise ValueError("{module} >>> missing sec key in key store for namespace [{ns}] !!!".format(module = myModuleName, ns = nameSpace))
		except Exception as error:
			raise error

	def authenticate(self, userName, apiKeyEncPass):
		'''
		purpose: Authenticate user credential (username, encrypted password) with security key to AD server and return security token
				this method will invalidate any exisiting token for current session.
		arguments:
			userName: username (user principal name as it exists, use whoami /upn to get the fully qualified name)
			userEncPass : encrypted password
			secKey: secKey to decrypt the encrypted password

		'''
		try:
			myModuleName = sys._getframe().f_code.co_name
			
			# decrypting password if it was encrypted
			userPass = self.__decryptText(apiKeyEncPass)

			if isinstance(userPass, bytes):
				userPass = userPass.decode()

			if isinstance(userName, bytes):
				userName = userName.decode()

			# checking if this is apikey passed as userEncPass
			try:
				# checking if this user's api key exists in VAULT
				print(f"checking if passed arg is apikey, user >>> {userName}, appKey >>> {apiKeyEncPass}")
				if not self.isValidApiKey(userName, apiKeyEncPass):

					# could not validate apikey, validating the password as passed
					try:
						print(f"passed cred is not validated as apikey, validating password in ldap user >>> {userName}")
						conn = Connection(self.AD_SERVER_PORT, userName, password = apiKeyEncPass, authentication='NTLM', raise_exceptions=True)
						if not conn.bind():
							print("invalid credentials !!!")
							# passed arg is not good, using decrypted pass 
							print(f"passed cred is not validated as apikey, validating decrypted password in ldap user >>> {userName}")
							conn = Connection(self.AD_SERVER_PORT, userName, password = userPass, authentication='NTLM', raise_exceptions=True)
							if not conn.bind():
								print("invalid credentials !!!")
								raise ValueError("authentication failed !!")
							else:
								print("decryptd credential is validated")
						else:
							print("passed credential is validated")
					except Exception as error:
						raise ValueError("authentication failed !!!")

			except Exception as error:
				raise ValueError("authentication failed !!!")

			# we must resolve bind call
			#conn.start_tls()
			#conn.bind()
			
			'''
			conn = ldap.initialize("".join(["ldap://",self.AD_SERVER_PORT]))
			conn.protocol_version = 3
			conn.set_option(ldap.OPT_REFERRALS,0)
			conn.simple_bind_s(userName, userPass)
			'''
			# we are here because either we have authenticated userid/password or apikey is validated
			if not self.SECURITY_TOKEN:
				self.SECURITY_TOKEN = token_urlsafe(64) 

			#print("security token generated >>", self.SECURITY_TOKEN)
			return self.SECURITY_TOKEN

		except Exception as error:
			print("error",str(error))
			raise error

	def invalidateExistingToken(self):
		self.SECURITY_TOKEN=""

	def validateSecToken(self, securityToken):
		try:
			myModuleName = sys._getframe().f_code.co_name
			#print("type >>>", type(securityToken), type(self.SECURITY_TOKEN))
			#print("got token for validation >>>", securityToken)
			#print("token for this session >>>", self.SECURITY_TOKEN)

			'''
			if securityToken == "sadjkfh7#3238":
				#print("got testing sec token")
				return 
				# this block must be removed when going to production
			'''
			"""
			if securityToken == 'SDFASDFL@#FSDFSDFFWQRT%LKSGKSA:G%_!@#%@#@#FSDGFASDF?<?><:)_+**SDF':
				# we need to persist this sec token and check passed sec token agains it
				return
			"""

			if not self.SECURITY_TOKEN:
					raise ValueError("Security token is not yet generated, Pls authenticate your credential to generate new security token")

			if not (securityToken == self.SECURITY_TOKEN):
				raise ValueError("{module} >>> invalid security token {token}".format(module = myModuleName, token = securityToken))

		except Exception as error:
			raise error


if __name__ == "__main__":
	sec = Security()
	import getpass
	#passPhrase = input("Pls enter your secret pass phrase >>> ")
	'''
	text = input ("Pls enter your password >>> ")
	#key = sec.generateKey(passPhrase)
	key, encPass = sec.__encryptText__(text)
	print("Secret Key is >>> ".format(key = key))
	print("Encrypted password is >>> [{key}>>{enc_pass}]".format(key = key, enc_pass = encPass))
	userEncPass = input("Pls enter your encrypted pass >>> ")
	key = input("Pls enter your secret key >>> ").encode()
	decPass = sec.__decryptText__(key, userEncPass)
	print("Dec >>>", decPass)
	'''
	myPass = getpass.getpass(prompt = "Pls enter text (password) to be encrypted >>> ", stream=None)
	#key = sec.generateKey(passPhrase)
	encPass = sec._Security__encryptText(myPass)
	#print("Secret Key is >>> {key}".format(key = key))
	print("Encrypted text is >>> {enc_pass}".format(enc_pass = encPass))
