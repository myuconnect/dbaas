from com.mmc.common.singleton import Singleton
from secrets import token_urlsafe
from ldap3 import Server, Connection


import base64, os, getpass, json, sys

# we want to log as how many times encryption methods are called ???

class Security(object):
	def __init__(self):
		self.SECURITY_TOKEN = ""
		self.AD_REALM = ""
		self.AD_SERVER_PORT = "usdfw1.ldap.corp.mmco.int:389"
		self.TEMP_SEC_TOKEN = "23$$#$#$!feeRSsdafsdfl%$"

	def __repr__(self):
		return "(%s, %s)" % (self.__class__)

	def __str__(self):
		return "(%s, %s)" % (self.__class__)

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

	def authenticate(self, userName, userEncPass):
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
			
			userPass = self.__decryptText(userEncPass)

			if isinstance(userPass, bytes):
				userPass = userPass.decode()

			if isinstance(userName, bytes):
				userName = userName.decode()

			conn = Connection(self.AD_SERVER_PORT, userName, password = userPass, authentication='NTLM', raise_exceptions=True)
			# we must resolve bind call
			#conn.start_tls()
			#conn.bind()
			
			'''
			conn = ldap.initialize("".join(["ldap://",self.AD_SERVER_PORT]))
			conn.protocol_version = 3
			conn.set_option(ldap.OPT_REFERRALS,0)
			conn.simple_bind_s(userName, userPass)
			'''
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
			if securityToken == 'SDFASDFL@#FSDFSDFFWQRT%LKSGKSA:G%_!@#%@#@#FSDGFASDF?<?><:)_+**SDF':
				# we need to persist this sec token and check passed sec token agains it
				return

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
