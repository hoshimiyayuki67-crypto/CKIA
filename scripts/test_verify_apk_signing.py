import unittest
from verify_apk_signing import verify


class SignatureParsing(unittest.TestCase):
    def test_current_and_legacy_tools(self):
        fingerprint = 'ab' * 32
        for label in ('Signer #1', 'V2 Signer:', 'V3 Signer:',
                      'Signer (minSdkVersion=24, maxSdkVersion=32)'):
            verify(f'Number of signers: 1\n{label} certificate SHA-256 digest: {fingerprint}\n', fingerprint)

    def test_wrong_missing_and_multiple_signers(self):
        fingerprint = 'ab' * 32
        for output in ('Number of signers: 1\n',
                       f'Number of signers: 2\nSigner #1 certificate SHA-256 digest: {fingerprint}\n',
                       'Number of signers: 1\nV2 Signer: certificate SHA-256 digest: ' + 'cd' * 32):
            with self.assertRaises(ValueError):
                verify(output, fingerprint)


if __name__ == '__main__':
    unittest.main()
