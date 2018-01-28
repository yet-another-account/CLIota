import shlex
import json
import time
import logging
import os
from cliota.api import node_mgr
from cliota.api import account
from cliota import walletfile


logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.DEBUG)

    nodes = json.load(open('nodes.json'))
    apifactory = node_mgr.ApiFactory(nodes)

    logger.info('Nodes found.')

    os.remove('wfile.test')

    walletdata = walletfile.WalletFile('wfile.test', 'averyinsecurepassword123',
                                       seed='A' * 81)

    acc = account.Account(walletdata, apifactory)

    acc.cache_new_addresses(10)

    logger.info('addr info: ' + str(acc.walletdata.addresses))

    # sleep forever
    # temporary bodge for until we get proper CLI implemented
    while True:
        time.sleep(999)
