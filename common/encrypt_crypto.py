from getpass import getpass as GP
from Crypto.Cipher import AES
from Crypto import Random

from com.mmc.core.singleton import Singleton

import os

class encrypt_crypto(object, metaclass=Singleton):
	def __init__(self):
		pass

if __name__ == "__main__":
	#Prompts password, the default prompt if not specified is Password:
	#When use in terminal, password entered by user will not be echoed.
	password = GP(prompt='Enter password:',stream=None)
	 
	#use os.urandom() method to create a random 16 bytes string
	#convert to bytes. On this example I want to use AES-128 hence 16bytes key.
	#16, 24, 32bytes are AES-128,192 and 256 bits respectively.
	key = bytes(os.urandom(16))
	 
	#To generate an initializing vector, fixed block size is 16 bytes.
	iv = Random.new().read(AES.block_size)
	 
	#Create a cipher to use for encryption
	cipher = AES.new(key,AES.MODE_CFB,iv)
	 
	#encrypts the password entered by user
	ciphertext = cipher.encrypt(password)
	 
	#ciphertext is in bytes, so i open create a file - password.enc
	#write the bytes into this file
	with open('password.enc', 'wb') as file:
	    file.write(ciphertext)
	    file.close()
	 
	#print(ciphertext)
	 
	#Create a decipher to decrypt the ciphertext
	decipher = AES.new(key,AES.MODE_CFB,iv)
	 
	#read byte from file
	with open('password.enc', 'rb') as file:
	    ctext = file.read()
	    file.close()
	#decrypt the ciphertext
	plaintext = decipher.decrypt(ctext)
	 
	#To convert the plaintext in bytes to string, use decode "utf-8"
	#print(plaintext.decode('utf-8'))
	print(plaintext.decode('utf-8'))