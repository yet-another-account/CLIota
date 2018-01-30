import logging
import random
import iota
import timeout_decorator
import threading
from cliota.parallel import parmap


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
            self.apifactory._check_apis()


class SyncedApiWrapper:
    def __init__(self, api):
        self.api = api
        self.lock = threading.Lock()

    def __getattr__(self, arg):
        def __exc(*args, **kwargs):
            with self.lock:
                return getattr(self.api, arg)(*args, **kwargs)
        return __exc


class ApiFactory:
    def __init__(self, nodes):
        self.nodes = nodes
        self.apis = self._get_apis()

        self.stopevent = threading.Event()
        self.refreshthread = RefreshApisThread(self, self.stopevent, 60)

        self.refreshthread.start()

    def __getattr__(self, cmd):
        def apicall(*args, **kwargs):
            @timeout_decorator.timeout(2, use_signals=False)
            def exc(api, cmd, *args, **kwargs):
                return getattr(api, cmd)(*args, **kwargs)

            while True:
                api = random.choice(self.apis)
                try:
                    return exc(api, cmd, *args, **kwargs)
                except timeout_decorator.TimeoutError:
                    logger.debug('Node didn\'t respond on time!')
                except iota.adapter.BadApiResponse:
                    logger.debug('Node gave bad api response!')
                    self.apis.remove(api)

        return apicall

    def _check_apis(self):
        """ Check that none of our nodes have fallen out of order """

        logger.debug('Checking node health.')
        refresh = []
        for api in self.apis:
            if type(api.adapter) is iota.adapter.HttpAdapter:
                refresh.append(api.adapter.get_uri())

        self.apis = self._get_apis()

    def _get_apis(self, exclude=[]):
        """ Get Iota instances of synced nodes """
        apis = []

        def try_connect(url):
            try:
                api = iota.Iota(url)
                nodeinfo = self.__node_info(api)
                if not nodeinfo:
                    return None

                if nodeinfo['latestMilestoneIndex'] != nodeinfo['latestSolidSubtangleMilestoneIndex']:
                    logger.debug('Node %s is not synced!', url)
                    return None

                # drop nodes not up to date
                if nodeinfo['appVersion'] != '1.4.2.1':
                    logger.debug('Node %s is not the latest version!', url)
                    return None

                logger.debug('Added node %s (LM: %d)!', url,
                             nodeinfo['latestMilestoneIndex'])

                return (url, nodeinfo['latestMilestoneIndex'])

            except timeout_decorator.TimeoutError:
                logger.debug('Connection to node %s timed out!', url)
                return None

        apis = parmap(try_connect, self.nodes, nprocs=len(self.nodes))
        apis = [a for a in apis if a]
        apis.sort(key=lambda n: n[1], reverse=True)

        threshold = 1

        i = 0
        while i < len(apis) - 1:
            if apis[i][1] - apis[i + 1][1] > threshold:
                logger.debug('Dropped node %s (LM: %d) from list (not up to sync)!',
                             apis[i + 1][0], apis[i + 1][1])
                del apis[i + 1]
                continue
            i += 1

        logger.debug('Loaded %d synced nodes!', len(apis))

        return [SyncedApiWrapper(iota.Iota(a[0])) for a in apis]

    @timeout_decorator.timeout(3, use_signals=False)
    def __node_info(self, api):
        try:
            return api.get_node_info()
        except Exception:
            logger.debug('Connection to node %s failed!',
                         api.adapter.get_uri())
            return None
