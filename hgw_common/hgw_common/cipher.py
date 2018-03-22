# Copyright (c) 2017-2018 CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import hashlib
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature.pss import MGF1
from Cryptodome.Hash import SHA, SHA256
from Cryptodome.Cipher import AES, PKCS1_OAEP
from Cryptodome import Random

MAGIC_BYTES = b'\xdf\xbb'


class NotEncryptedMessage(Exception):
    pass


def create_cipher_from_file(file_obj, magic_bytes=MAGIC_BYTES):
    return Cipher(RSA.importKey(file_obj.read()), magic_bytes)


class Cipher(object):
    class MissingPrivateKey(Exception):
        pass

    class MissingPublicKey(Exception):
        pass

    class MissingAESKey(Exception):
        pass

    def __init__(self, public_key=None, private_key=None, aes_key=None, iv=None, magic_bytes=MAGIC_BYTES):
        """

        :param public_key: RSA object, required for encrypting
        :param private_key: RSA object, required for decrypting
        :param aes_key:  16 bytes length string for symmetric encrypting, required for encrypting
        :param iv: initialization vector (16 bytes length string), required for encrypting
        :param magic_bytes: 2 bytes length string for marking enconded message
        """

        self.public_key = public_key
        self.private_key = private_key
        self.aes_key = aes_key or Random.new().read(AES.block_size)
        self.iv = iv or Random.new().read(AES.block_size)
        self.block_size = AES.block_size
        self.magic_bytes = magic_bytes

        self.aes_hashes = {}
        self.enc_aes_key = None
        self.aes_key_hash = None
        self.base_message = None

        self.rsa_private_cipher = PKCS1_OAEP.new(self.private_key, hashAlgo=SHA256, mgfunc=self._mgf1_fun) \
            if self.private_key else None

        self.rsa_public_cipher = PKCS1_OAEP.new(self.public_key, hashAlgo=SHA256, mgfunc=self._mgf1_fun) \
            if self.public_key else None

        self.aes_cipher = AES.new(self.aes_key, AES.MODE_CBC, self.iv)

    def decrypt(self, message):
        if not self.private_key:
            raise Cipher.MissingPrivateKey()

        if self.is_encrypted(message):
            len_aes_key_hash, len_enc_aes_key, len_iv = map(ord, message[2:5].decode('utf-8'))
            len_enc_aes_key *= 128

            aes_key_hash_offset = 5 + len_aes_key_hash
            enc_aes_key_offset = aes_key_hash_offset + len_enc_aes_key
            iv_offset = enc_aes_key_offset + len_iv

            aes_key_hash = message[5:aes_key_hash_offset]
            enc_aes_key = message[aes_key_hash_offset:enc_aes_key_offset]
            iv = message[enc_aes_key_offset:iv_offset]
            enc_payload = message[iv_offset:]

            if aes_key_hash not in self.aes_hashes:
                key_dec = self.rsa_private_cipher.decrypt(enc_aes_key)
                aes_key = AES.new(key_dec, AES.MODE_CBC, iv)
                self.aes_hashes[aes_key_hash] = aes_key

            return self.unpad(self.aes_hashes[aes_key_hash].decrypt(enc_payload)).decode('utf-8')
        else:
            raise NotEncryptedMessage()

    def encrypt(self, message):
        if isinstance(message, str):
            message = message.encode('utf-8')

        if not self.public_key:
            raise Cipher.MissingPublicKey()
        if not self.aes_key:
            raise Cipher.MissingAESKey()

        if not self.enc_aes_key:
            self.aes_key_hash = hashlib.sha256(self.aes_key).digest()
            self.enc_aes_key = self.rsa_public_cipher.encrypt(self.aes_key)

        if not self.base_message:
            self.base_message = self.magic_bytes + \
                                chr(len(self.aes_key_hash)).encode('utf-8') + \
                                chr(len(self.enc_aes_key) // 128).encode('utf-8') + \
                                chr(len(self.iv)).encode('utf-8') + \
                                self.aes_key_hash + \
                                self.enc_aes_key + \
                                self.iv
        return self.base_message + self.aes_cipher.encrypt(self.pad(message))

    def is_encrypted(self, message):
        return message[:2] == self.magic_bytes

    @staticmethod
    def unpad(s):
        try:
            return s[0:-s[-1]]
        except TypeError:  # python 2 compatibility
            return s[0:-ord(s[-1])]

    @staticmethod
    def _mgf1_fun(x, y):
        return MGF1(x, y, SHA)

    def pad(self, s):
        return s + (self.block_size - len(s) % self.block_size) * chr(self.block_size - len(s) % self.block_size).encode('utf-8')
