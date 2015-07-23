import gevent
import requests
import logging
import json
import copy

from redis import StrictRedis
from datetime import datetime
from gevent.queue import Queue
from threading import Thread
from requests.exceptions import ConnectionError, Timeout
from time import sleep

from uptime.notifiers import SlackNotifier

log = logging.getLogger('uptime')


class Check(object):
    """
    URL Check configuration object
    """

    def __init__(self, check_json):
        defaults = {'content': None,
                    'interval': 15}

        self.url = None
        self.__dict__ = json.loads(check_json)

        # use defaults for undefined optional params
        for k, v in defaults.items():
            if k not in self.__dict__:
                self.__setattr__(k, v)

        self.check_id = str(self.check_id)
        self.name = self.check_id

        self.failures = 0
        self.notified = False

        self.last = datetime.utcnow()
        self.interval = int(self.interval)
        logging.info('loaded check %s for url %s' % (self.check_id, self.url))

    def dump_json(self):
        #  ret = json.clone(self.__dict__)
        ret = copy.copy(self.__dict__)
        del ret['last']
        return json.dumps(ret)

    def ok(self):
        """
        Method to reset failures and notify switches following successful check
        """
        self.failures = 0
        self.notified = False


class Uptime(object):
    jobs = Queue()  # TODO: Are the consequences of this intended?

    def __init__(self, config, concurrency=5):
        self.config = config
        self.source = self.config.source
        self.checks = []
        self.config_path = 'uptime_config:'
        self.results_path = 'uptime_results:' + self.source + ':'
        self.stats_path = 'uptime_stats:'

        self.concurrency = concurrency

        if self.config.slack_url:
            self.notifier = SlackNotifier(self.config.slack_url)
        else:
            log.warn('No notifiers configured')
            self.notifier = None

        self.redis = StrictRedis(host=self.config.redis_host, port=self.config.redis_port)

        if not self.redis.exists(self.stats_path):
            self.redis.set(self.stats_path + 'total_checks', 0)

        self.start()

    def start(self):
        workers = [gevent.spawn(self._check_worker) for _ in range(1, self.concurrency)]
        workers.append(gevent.spawn(self._controller))

        t = Thread(target=self._watcher)
        t.daemon = True
        t.start()

        gevent.joinall(workers)

    def _watcher(self):
        """
        Worker to poll redis for key changes, updating accordingly
        """
        while True:
            configs = self._get_configs()

            # add all checks
            for c in configs:
                self._add_check(c)

            # cleanup removed checks
            config_ids = [str(c['check_id']) for c in configs]
            for c in self.checks:
                if c.check_id not in config_ids:
                    self._remove_check(c.check_id)

            sleep(5)

    def _get_configs(self):
        pattern = self.config_path + '*'
        return [json.loads(self.redis.get(k).decode(self.config.encoding)) for
                k in self.redis.keys(pattern)]

    def _controller(self):
        """
        Controller worker. Submits any overdue checks to queue.
        """
        while True:
            now = datetime.utcnow()

            [self.jobs.put_nowait(c) for c in self.checks if
             (now - c.last).seconds > c.interval]

            gevent.sleep(0)

    def _check_worker(self):
        """
        Worker to perform url checks
        """
        logging.info('[{}] worker started'.format(id(self)))
        while True:
            while not self.jobs.empty():
                check = self.jobs.get()

                log.info('checking %s' % check.url)

                result = self._check_url(check.url, check.content)
                self.redis.incr(self.stats_path + 'total_checks')

                check.response_time = result['elapsed']

                if result['ok']:
                    check.last = datetime.utcnow()
                    check.ok()
                else:
                    check.failures += 1

                if check.failures > 3 and not check.notified and self.notifier:
                    log.info('sending notification for failed check')
                    if self.notifier:
                        self.notifier.notify(
                            'url check failure for %s -- %s' %
                            (check.url, result['reason'])
                        )

                    check.notified = True

                # after 10 failures, return to normal interval to prevent
                # excessive checks
                if check.failures > 10:
                    check.last = datetime.utcnow()

                key = self.results_path + check.check_id
                self.redis.set(key, check.dump_json())

            gevent.sleep(0)

    def _add_check(self, check):
        """
        Internal method to add a check for the controller to schedule, 
        if it exists
        params:
         - check(dict): dictionary of check config
        """
        check_id = check['check_id']
        if check_id not in [str(c.check_id) for c in self.checks]:
            self.checks.append(Check(json.dumps(check)))

    def _remove_check(self, id):
        # remove loaded check
        [self.checks.remove(c) for c in self.checks if c.check_id == id]
        # remove check from results in redis
        key = self.results_path + id
        self.redis.delete(key)

    def _check_url(self, url, content, timeout=5):
        try:
            r = requests.get(url, timeout=timeout)
        except ConnectionError as e:
            log.warn('unable to reach %s:\n%s' % (url, e))
            return {'ok': False, 'reason': e, 'elapsed': 0}
        except Timeout as e:
            log.warn('connection timed out checking %s:\n%s' % (url, e))
            return {'ok': False, 'reason': e, 'elapsed': timeout}

        log.debug('%s returned %s' % (url, r.status_code))
        if not r.ok:
            return {'ok': False,
                    'reason': r.status_code,
                    'elapsed': r.elapsed.total_seconds()}
        if content and content not in r.text:
            return {'ok': False,
                    'reason': 'content check failure',
                    'elapsed': r.elapsed.total_seconds()}

        return {'ok': True, 'elapsed': r.elapsed.total_seconds()}

