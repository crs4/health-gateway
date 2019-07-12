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
import os

import unittest

from Cryptodome.PublicKey import RSA

from hgw_common.cipher import Cipher, NotEncryptedMessage


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class CipherTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(CipherTest, cls).setUpClass()
        private_key = RSA.generate(2048)
        public_key = private_key.publickey()
        cls.cipher = Cipher(public_key=public_key, private_key=private_key)

    def test_encrypt(self):
        message = "Lorem ipsum..."
        enc_message = self.cipher.encrypt(message)
        self.assertEqual(message, self.cipher.decrypt(enc_message))

        # second encoding for covering aes hash management
        message = "dolor sit amet"
        enc_message = self.cipher.encrypt(message)
        self.assertEqual(message, self.cipher.decrypt(enc_message))

        message = b"Lorem ipsum"
        enc_message = self.cipher.encrypt(message)
        self.assertEqual(message.decode('utf-8'), self.cipher.decrypt(enc_message))

    def test_is_encrypted(self):
        message = 'message'
        self.assertFalse(self.cipher.is_encrypted(message))
        self.assertTrue(self.cipher.is_encrypted(self.cipher.encrypt(message)))

    def test_decrypt_not_encrypted(self):
        self.assertRaises(NotEncryptedMessage, self.cipher.decrypt, 'not_encrypted_message')

    def test_decrypt_msg_from_java(self):
        with open(os.path.join(BASE_DIR, 'rsa_privatekey_2048'), 'rb') as f:
            pri_rsa_key = f.read()
        rsa_pri_key = RSA.importKey(pri_rsa_key)

        cipher = Cipher(private_key=rsa_pri_key)
        msg = b'\xdf\xbb \x02\x10\xccn\xfeWH\xc6V\x1c\x90\xcf\xf35\ry\xa8\x93jg?\xf1!o\xab\x1d\x96\x8f\x8d\xb3\xd2\xf1tK[\x8el"\xbbgr(\xaf\xe9S\x9c\xda\xc2O\xe3NGGP:\x87\xe0\'\x8e\x80\x81M\x80\xe2\x1a{\x15\xaf\xf1+?+\x99{5%\xbd\xd3\xb5\x14\x1d\xfc\xbeLVX\xedTO\xfb\x04\xc3\x00^\xb1_\x0e\xfb*f>?}\xeb\xfb\xd5J%\xde0\xb2\xa7\x9f3~\x00\xbe\xa7\xecs\x80\xd5\x88&\xc4\x96\xda\xdbN:\xa7\xfb\x00e\xa2\x05\xe0\xb8\xbc\xeaR\x1f9#\xa3\x05\xea\x0f`\x0b\xfd\x9f\x0e\xfay\xdcH\x1b\x86C}\xa5\x0cTb\xe5\n\xc0\x94\x82Y\x86\xd9\xf9\xa9&\xdd\xe7Xl\xad\xe6\x1c\xf0\xf1(\xbc\x15\xeb0\x1f\x00\xb1\xaf\xbdy\xb5d\x1a\xac0R\xe2,\x8a\xf5a\xf7d\x1a\xd0v\x9c\x83L>vq\xd6\xb2\x04E\xbdD\x13\x8f\x9e\xf0\xa2\xde\xd1p\x97\xa2\x85\x042\xa5\x84\xd3\xe3W\r\x1c\xe9$\x86\x92\xf9\x8bE&\x15\xb1\xc4\x1a\xcd\xa5\xd0\xb1\x98\x19Nu\xecQ\x1c\x7fH\xac\x7f\xc5u6_T\xf5\x9c\x83\x04\xc9\x8c\x11\xcc)\xc1L\x84\x07j!u\xb8\xec\x93\xe8d\xc3\xdd\xeb\xae^\xa5\xacA\xbc6\x8c\x19\x950\xce\xa1\x84}\x1b\xfcxB\x9am%'

        # For some reason, dumping the message on a file makes decrypting fail. Back slashes are escaped, but using
        # msg_from_file.decode('string-escape') does not work.

        self.assertTrue(cipher.decrypt(msg), 'MaurettoD&LRio$')  # it's not my fault


if __name__ == '__main__':
    unittest.main()