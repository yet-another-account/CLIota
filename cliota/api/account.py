import iota
from iota.crypto.addresses import AddressGenerator
from cliota.parallel import parmap
import random
import logging
import threading


logger = logging.getLogger(__name__)


class RefreshAddrsThread(threading.Thread):
    def __init__(self, account, event, interval):
        threading.Thread.__init__(self)
        self.stopped = event
        self.interval = interval
        self.account = account
        self.daemon = True

    def run(self):
        logger.debug('Address Refresh Thread started.')
        while not self.stopped.wait(self.interval):
            self.account.refresh_addresses()

            THRESHOLD_GEN = 3
            NEW_ADDRS = 5

            # generate new addresses is number of fresh addresses is low
            if len(self.unused_addrs()) <= THRESHOLD_GEN:
                self.account.cache_new_addresses(NEW_ADDRS)


class Account:
    """ Hooks for API """

    def __init__(self, walletfile, apifactory):
        # this api instance is used for non-node calls only
        self.walletdata = walletfile
        self.apifactory = apifactory

        self.seed = self.walletdata.seed
        self.api = iota.Iota('http://0.0.0.0:0', seed=self.seed)
        self.addrgen = AddressGenerator(self.seed)

        self.stopevent = threading.Event()
        self.refreshthread = RefreshAddrsThread(self, self.stopevent, 15)
        self.refreshthread.start()

    def balance(self):
        """ Get balance of Account """
        bal = 0

        for addr in self.walletdata.addresses:
            bal += addr['balance']

        return bal

    def transactions(self):
        """ Get bundles in/out associated with address """
        """ Return: [{bundlehash, amount}] """
        return []

    def send(self, to, amount):
        """ Send iotas """
        """ Return: (bundlehash, tailtx)"""
        return ("", "")

    def addresses(self):
        """ Get a list of addresses; may be from cache """
        """ Return: (receive, change) with [{address, balance, txcount}] """
        return ([], [])

    def receive(self):
        """ Get first unused receive address """
        for a in self.walletdata.addresses:
            if not a['txs']:
                return a['address']

    def check_address(self, addr):
        """ Fetch address info """
        """ Return: (balance, txs) """

        for a in self.walletdata.addresses:
            if a['address'] == addr:
                return (a['balance'], a['txs'])

    def cache_new_addresses(self, count):
        """ Generate new addresses and add them to walletfile """
        addrgen = AddressGenerator(self.seed)

        def generate_address(index):
            return str(addrgen.get_addresses(index)[0])

        addrs = parmap(generate_address,
                       range(len(self.walletdata.addresses),
                             len(self.walletdata.addresses) + count))

        for address in addrs:
            self.walletdata.addresses.append({
                'address': address,
                'balance': 0,
                'txs': []
            })

        # save changes
        self.walletdata.save()

    def refresh_addr(self, index):
        addr = self.walletdata.addresses[index]['address']

        logger.debug("Refreshing address %s", addr)

        # TODO: Also keep tx info
        txs = self.apifactory.find_transactions(addresses=[
            addr
        ])['hashes']

        bal = self.apifactory.get_balances([
            iota.Address(addr)
        ])['balances'][0]

        self.walletdata.addresses[index]['txs'] = [str(x) for x in txs]
        self.walletdata.addresses[index]['balance'] = bal

        # save changes
        self.walletdata.save()

    def refresh_addresses(self, P_chk_used=0.1, P_chk_unused=0.8):
        torefresh = []
        for i in range(len(self.walletdata.addresses)):
            if len(self.walletdata.addresses[i]['txs']) == 0:
                if random.uniform(0, 1) < P_chk_unused:
                    torefresh.append(i)
            else:
                if random.uniform(0, 1) < P_chk_used:
                    torefresh.append(i)

        logger.debug('Refreshing %d addresses', len(torefresh))

        def refresh_addr(index):
            self.refresh_addr(index)
        parmap(refresh_addr, torefresh, nprocs=10)

    def unused_addrs(self):
        return [addr['address'] for addr in self.walletdata.addresses
                if not addr['txs']]
