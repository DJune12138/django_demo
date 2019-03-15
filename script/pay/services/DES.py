#! /usr/bin/python
# -*- coding: utf-8 -*-

import Crypto.Cipher.DES as C_DES
import base64

class DES():
    def __init__(self, key, block_size = 8):
        self._key = base64.b64decode(key)
        self.block_size = block_size
     
    def __Pad(self, data):
        """
        Returns the data padded using PKCS5.

        For a block size B and data with N bytes in the last block, PKCS5
        pads the data with B-N bytes of the value B-N.

        @param data: data to be padded
        @type data: string

        @return: PKCS5 padded string
        @rtype: string
        """
        pad = self.block_size - len(data) % self.block_size
        return data + pad * chr(pad)

    def __UnPad(self, padded):
        """
        Returns the unpadded version of a data padded using PKCS5.

        @param padded: string padded with PKCS5
        @type padded: string

        @return: original, unpadded string
        @rtype: string
        """
        pad = ord(padded[-1])
        return padded[ : -pad]

    def Encrypt(self, data):
        desobj = C_DES.new(self._key, C_DES.MODE_CBC, self._key)
        cipher = desobj.encrypt(self.__Pad(data))
        return base64.b64encode(cipher)

    def Decrypt(self, data):
        desobj = C_DES.new(self._key, C_DES.MODE_CBC, self._key)
        res = base64.b64decode(data)
        res = desobj.decrypt(res)
        res = self.__UnPad(res)
        return res
