import iota
from iota.crypto.addresses import AddressGenerator
import multiprocessing
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
        api = random.choice(self.apifactory.apis)

        logger.debug("Refreshing address %s", addr)

        # TODO: Also keep tx info
        txs = api.find_transactions(addresses=[
            addr
        ])['hashes']

        bal = api.get_balances([
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


# parallel processing stuff

def fun(f, q_in, q_out):
    while True:
        i, x = q_in.get()
        if i is None:
            break
        q_out.put((i, f(x)))


def parmap(f, X, nprocs=multiprocessing.cpu_count()):
    q_in = multiprocessing.Queue(1)
    q_out = multiprocessing.Queue()

    proc = [multiprocessing.Process(target=fun, args=(f, q_in, q_out))
            for _ in range(nprocs)]
    for p in proc:
        p.daemon = True
        p.start()

    sent = [q_in.put((i, x)) for i, x in enumerate(X)]
    [q_in.put((None, None)) for _ in range(nprocs)]
    res = [q_out.get() for _ in range(len(sent))]

    [p.join() for p in proc]

    return [x for i, x in sorted(res)]
