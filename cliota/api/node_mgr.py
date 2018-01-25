import logging
import random
import iota
import timeout_decorator
import threading


logger = logging.getLogger(__name__)


class RefreshApisThread(threading.Thread):
    def __init__(self, apifactory, event, interval):
        threading.Thread.__init__(self)
        self.stopped = event
        self.interval = interval
        self.apifactory = apifactory
        self.daemon = True

    def run(self):
        logger.debug('API Refresh Thread started.')
        while not self.stopped.wait(self.interval):
            self.apifactory.check_apis()


class ApiFactory:
    def __init__(self, nodes):
        self.nodes = nodes
        self.apilocal = iota.Iota('http://0.0.0.0:0')
        self.apis = self.get_apis(num=4)

        self.stopevent = threading.Event()
        self.refreshthread = RefreshApisThread(self, self.stopevent, 15)

        self.refreshthread.start()

    def check_apis(self):
        """ Check that none of our nodes have fallen out of order """

        logger.debug('Checking node health.')
        refresh = []
        for api in self.apis:
            if type(api.adapter) is iota.adapter.HttpAdapter:
                refresh.append(api.adapter.get_uri())

        self.apis = self.get_apis(len(self.apis), refresh=refresh)

    def get_apis(self, num, exclude=[], refresh=[]):
        """ Get Iota instances of synced nodes """
        apis = []

        random.shuffle(self.nodes)

        self.nodes = refresh + self.nodes

        for url in self.nodes:
            if url in exclude:
                continue

            try:
                api = iota.Iota(url)
                nodeinfo = self.__node_info(api)
                if not nodeinfo:
                    continue

                if nodeinfo['latestMilestoneIndex'] != nodeinfo['latestSolidSubtangleMilestoneIndex']:
                    logger.debug('Node %s is not synced!', url)
                    continue

                logger.info('Added node %s (LM: %d)!', url,
                            nodeinfo['latestMilestoneIndex'])

                # TODO: some efficient binary search insert thing
                apis.append((api, nodeinfo['latestMilestoneIndex']))

                apis.sort(key=lambda n: n[1], reverse=True)

                threshold = 2

                while len(apis) >= 2 and apis[-1][1] + threshold < apis[-2][1]:
                    logger.info('Dropped node %s from list (not up to sync)!',
                                apis[-1][0])
                    del apis[-1]

                if len(apis) >= num:
                    break

            except timeout_decorator.TimeoutError:
                logger.debug('Connection to node %s timed out!', url)

        return [a[0] for a in apis]

    @timeout_decorator.timeout(0.3, use_signals=False)
    def __node_info(self, api):
        try:
            return api.get_node_info()
        except Exception:
            logger.debug('Connection to node %s failed!',
                         api.adapter.get_uri())
            return None
