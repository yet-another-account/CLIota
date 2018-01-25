from unittest import TestCase
import cliota.walletfile


class WalletFileTest(TestCase):
    def test_encrypt(self):
        encryption = cliota.walletfile.WalletEncryption()
        testdata = b'Hello, World!' * 100
        password = 'averyinsecurepassword123'
        encrypted = encryption.encrypt(testdata, password)
        decrypted = encryption.decrypt(encrypted, password)

        self.assertEqual(testdata, decrypted)
