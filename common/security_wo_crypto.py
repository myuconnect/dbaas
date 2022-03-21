from com.mmc.core.singleton import Singleton
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from secrets import token_urlsafe
from ldap3 import Server, Connection


import base64, os, getpass, json, sys

# we want to log as how many times encryption methods are called ???

class Security(object, metaclass=Singleton):
	def __init__(self):
		self.securityToken = ""
		self.AD_REALM = ""
		self.AD_SERVER_PORT = "usdfw1.ldap.corp.mmco.int:389"
		self.TEMP_SEC_TOKEN = "23$$#$#$!feeRSsdafsdfl%$"

	def __repr__(self):
		return "(%s, %s)" % (self.__class__, self.securityToken)

	def __str__(self):
		return "(%s, %s)" % (self.__class__, self.securityToken)

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
			myModuleName = sys._getframe().f_code.co_name

			myKey = self.__genSHA256Key(secretText)
			myKeyF = Fernet(myKey)
			myEncSecretText = myKeyF.encrypt(secretText.encode())
			#return (myKey.decode('utf-8'), myEncSecretText.decode('utf-8'))
			return (myKey, myEncSecretText)
		except Exception as error:
			raise error

	def __decryptText(self, key, encryptText):
		try:
			myModuleName = sys._getframe().f_code.co_name

			myKeyF = Fernet(key)
			return myKeyF.decrypt(encryptText.encode())
		except Exception as error:
			raise error

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

	#@staticmethod
	def __getUserPass(self, userName, encPass, secKey):
		'''
		purpose : get user's password in clear text
		argument(s) : 
			userName: user name
			encPass : encrypted password
			keyFile : keyfile
		usage : __getUserPass('<repository/deploy>')
		'''
		try:
			myModuleName = sys._getframe().f_code.co_name

			if not(userName and encPass and secKey):
				raise ValueError("{module} >>> invalid arguments, all arguments are mandatory !!!". format(module = myModuleName))
			myModuleName = sys._getframe().f_code.co_name
			#self.LOGGER.info("got argument(s) {args}".format(args = str([userName, userType])))
			#key = __getKey(userName, secKey)

			#self.LOGGER.info("validating arguments")
			if not isinstance(userName, str):
				raise InvalidArguments("{module} >>> Invalid userName !!!".format(module = myModuleName))

			#self.LOGGER.info("decrypting user passwod")
			decPass = self.__decryptText(secKey, encPass)

			if isinstance(decPass, bytes):
				decPass = decPass.decode()

			return decPass

		except Exception as error:
			raise error

	def authenticate(self, userName, userEncPass, secKey):
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

			if not (isinstance(userName, str) and isinstance(userEncPass, str) and isinstance(secKey, str)):
				raise ValueError("{module} >>> invalid username/encrypted password/security key arguments !!!".format(module = myModuleName))

			#print("ldap server >>>", self.AD_SERVER_PORT)
			
			userPass = self.__decryptText(secKey, userEncPass)

			if isinstance(userPass, bytes):
				userPass = userPass.decode()

			if isinstance(userName, bytes):
				userName = userName.decode()

			conn = Connection(self.AD_SERVER_PORT, userName, password = userPass, authentication='NTLM')
			conn.start_tls()
			conn.bind()
			'''
			conn = ldap.initialize("".join(["ldap://",self.AD_SERVER_PORT]))
			conn.protocol_version = 3
			conn.set_option(ldap.OPT_REFERRALS,0)
			conn.simple_bind_s(userName, userPass)
			'''
			self.SECURITY_TOKEN = token_urlsafe(32)
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
			if not self.SECURITY_TOKEN:
					raise ValueError("Security token is not yet generated, Pls authenticate using credential to generate new security token")

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
	key, encPass = sec._Security__encryptText(myPass)
	print("Secret Key is >>> {key}".format(key = key))
	print("Encrypted password is >>> {enc_pass}".format(enc_pass = encPass))

#'B9mrpgmhAckv-FkvIteYeuOmN6U63SSd0Wg4ncXKpMs='
#'gAAAAABcGlzqe7TbSid4HDqT8kPSMZS4ZNhzMfJH8rY0CUS80Vdz4LqwOpGOOmagt5Y_6QIeDZFQxEqry90h-4EhbkV4NrloRQ=='
#'gAAAAABcGlwAy_p_o61TrI8tmH2oLCt453wpVF1PDCQ9Ivez7rh1P-jw3VtysS0X4rnRL2MQ8S6Lq125e1yb8nZeTyTvLHVfxw=='
'''

from cryptography.fernet import Fernet
message = "myname".encode()
#key = Fernet.generate_key() # Store this key or get if you already have it
key = b'4P3qbReYhjjnrv3piDYEyJa-JN_qt7n70Io9zmnpeGo='
print(key)
f = Fernet(key)
encrypted = f.encrypt(message)
decrypted = f.decrypt(encrypted)
message == decrypted

'''