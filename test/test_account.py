from unittest import TestCase
from cliota.api.account import Account
from cliota.walletfile import WalletFile


class AccountTest(TestCase):
    def test_addr_gen(self):
        acc = Account(WalletFile('wf', 'pass', seed='A' * 81), object())
        acc.cache_new_addresses(4)

        # This method only generates new addresses,
        # it doesn't populate the balance or txsin/txsout.
        expected = [
            {
                'address': 'XUERGHWTYRTFUYKFKXURKHMFEVLOIFTTCNTXOGLDPCZ9CJLKHROOPGNAQYFJEPGK9OKUQROUECBAVNXRX',
                'balance': 0,
                'txsin': 0,
                'txsout': 0
            },
            {
                'address': 'RJBYLCIOUKWJVCUKZQZCPIKNBUOGRGVXHRTTE9ZFSCGTFRKELMJBDDAKEYYCLHLJDNSHQ9RTIUIDLMUOB',
                'balance': 0,
                'txsin': 0,
                'txsout': 0
            },
            {
                'address': 'G9IBAWCWWYOSAVURTPX9JKBJLAFFBHWLOONFHTNENHJZGRLTDUDTMXTMBKYODOVHTAYKKIZBDGVAJJQJD',
                'balance': 0,
                'txsin': 0,
                'txsout': 0
            },
            {
                'address': 'LATEWUUZSHRMEVHYVGW9T9HQKRLDGHTTAEHSN9ERFCQOEBCTNTBTYZPPARUILAYCKFKERLJ9UTYPHIICY',
                'balance': 0,
                'txsin': 0,
                'txsout': 0
            }
        ]

        self.assertEqual(acc.walletdata.addresses, expected)
