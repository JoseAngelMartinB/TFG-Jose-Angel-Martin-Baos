#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

# BSC Thesis
#
# Author
#  - José Ángel Martín Baos

from Crypto.Cipher import AES
import hashlib
import base64

class AESCipher():
    """
    Encript a message using AES alorithm
    """
    def __init__(self, key):
        self.key = hashlib.sha256(key.encode()).digest()
        BS = 16
        self.pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS).encode()
        self.unpad = lambda s: s[:-ord(s[len(s)-1:])]

    def iv(self):
        """
        The initialization vector to use for encryption or decryption.
        """
        return chr(0) * 16

    def encrypt(self, message):
        message = message.encode()
        raw_msg = self.pad(message)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv())
        enc_msg = cipher.encrypt(raw_msg)
        return base64.b64encode(enc_msg).decode('utf-8')

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv())
        dec = cipher.decrypt(enc)
        return self.unpad(dec).decode('utf-8')
