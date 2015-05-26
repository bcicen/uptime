import gevent,requests,logging,json,etcd,jsontree,os
from datetime import datetime
from gevent.queue import Queue
from threading import Thread
from requests.exceptions import ConnectionError
from socket import getfqdn
from notifiers import SlackNotifier
from config import Config

logging.basicConfig(level=logging.WARN)
log = logging.getLogger('uptime')

class Check(object):
    """
    URL Check configuration object
    """
    def __init__(self,id,check_json):
        defaults = { 'content'  : None,
                     'interval' : 15 }

        self.__dict__ = jsontree.loads(check_json)

        #use defaults for undefined optional params
        for k,v in defaults.iteritems():
            if not self.__dict__.has_key(k):
                self.__setattr__(k,v)

        self.id = id
        self.name = id
        self.last = datetime.utcnow()
        self.failures = 0
        self.notified = False
        print('loaded check %s for url %s' % (self.id,self.url))
        log.debug(self.json())

    def json(self):
        ret = jsontree.clone(self.__dict__)
        del ret['last']
        return json.dumps(ret)

    def ok(self):
        """
        Method to reset failures and notify switches following successful check
        """
        self.failures = 0
        self.notified = False

class Uptime(object):
    jobs = Queue()

    def __init__(self,etcd_host='localhost',etcd_port=4001,concurrency=5):
        if Config.__dict__.has_key('SOURCE'):
            self.source = Config.SOURCE
        else:
            self.source = getfqdn()

        self.checks = []
        self.check_path = '/checks'
        self.results_path = self.check_path + '/results/' + self.source
        self.concurrency = concurrency

        if Config.__dict__.has_key('SLACK_URL'):
            self.notifier = SlackNotifier(Config.SLACK_URL)
        else:
            log.warn('No notifiers configured')
            self.notified = None

        self.etcd = etcd.Client(host=etcd_host,port=etcd_port)

        #create checks dir if not exist
        for path in '/', '/config', '/results', self.results_path:
            try:
                self.etcd.write(self.check_path + path,None,dir=True)
            except etcd.EtcdNotFile:
                pass

        self.start()

    def start(self):
        workers = [ gevent.spawn(self._check_worker) for \
                    n in range(1,self.concurrency) ]
        workers.append(gevent.spawn(self._controller))

        t = Thread(target=self._watcher)
        t.daemon = True
        t.start()

        gevent.joinall(workers)

    def _watcher(self):
        """
        Worker to watch etcd for key changes, updating accordingly
        """
        path = self.check_path + '/config'
        for event in self._etcd_events:
            if event.action == 'set':
                self._add_check(event.key,event.value)
            if event.action == 'delete':
                self._remove_check(event.key)

    def _controller(self):
        """
        Controller worker. Submits any overdue checks to queue.
        """
        while True:
            now = datetime.utcnow()

            [ self.jobs.put_nowait(c) for c in self.checks if \
                (now - c.last).seconds > c.interval ]

            gevent.sleep(0)

    def _check_worker(self):
        """
        Worker to perform url checks
        """
        print('worker started')
        while True:
            while not self.jobs.empty():
                check = self.jobs.get()
            
                log.info('checking %s' % check.url)

                result = self._check_url(check.url,check.content)
            
                check.response_time = result['elapsed']

                if result['ok']:
                    check.last = datetime.utcnow()
                    check.ok()
                else:
                    check.failures += 1 
                
                if check.failures > 3 and not check.notified and self.notifier:
                    log.info('sending notification for failed check')
                    self.notifier.notify('url check failure for %s -- %s' % \
                            (check.url,result['reason']))

                    check.notified = True

                #after 10 failures, return to normal interval to prevent
                #excessive checks
                if check.failures > 10:
                    check.last = datetime.utcnow()

                path = self.results_path + '/' + check.id
                self.etcd.set(path,check.json())

            gevent.sleep(0)

    def _etcd_events(self,path):
        """
        Generator to yield events from etcd watch
        """
        while True:
            event = self.etcd.watch(path, recursive=True)
            yield event

    def _add_check(self,key,value):
        id = os.path.basename(key)
        self.checks.append(Check(id,value))

    def _remove_check(self,key):
        id = os.path.basename(key)
        [ self.checks.remove(c) for c in self.checks if c.id == id ]

    def _check_url(self,url,content):
        try:
            r = requests.get(url)
        except ConnectionError as e:
            log.warn('unable to reach %s:\n%s' % (url,e))
            return { 'ok':False,'reason':e }

        log.debug('%s returned %s' % (url,r.status_code))
        if not r.ok:
            return { 'ok':False,
                     'reason': r.status_code,
                     'elapsed':r.elapsed.total_seconds() } 
        if content and not content in r.text:
            return { 'ok':False,
                     'reason': 'content check failure',
                     'elapsed':r.elapsed.total_seconds() }
        
        return { 'ok':True,'elapsed':r.elapsed.total_seconds() }

if __name__ == '__main__':
    ut = Uptime()
