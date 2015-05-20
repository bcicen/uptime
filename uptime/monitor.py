import gevent,requests,logging,json,etcd,jsontree,os
from datetime import datetime
from gevent.queue import Queue
from requests.exceptions import ConnectionError
from notifiers import SlackNotifier
from time import sleep
from config import Config

logging.basicConfig(level=logging.WARN)
log = logging.getLogger('uptime')

class Check(object):
    """
    URL Check configuration object
    """
    def __init__(self,id,check_json):
        defaults = { 'content'  : None,
                     'interval' : 5 }

        self.__dict__ = jsontree.loads(check_json)

        #use defaults for undefined optional params
        for k,v in defaults.iteritems():
            if not self.__dict__.has_key(k):
                self.__setattr__(k,v)

        self.id = id
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
        self.checks = []
        self.check_path = '/checks'
        self.check_refresh = 5
        self.last_check_update = datetime(1,1,1)
        self.concurrency = concurrency

        if Config.__dict__.has_key('SLACK_URL'):
            self.notifier = SlackNotifier(Config.SLACK_URL)
        else:
            log.warn('No notifiers configured')
            self.notified = None

        self.etcd = etcd.Client(host=etcd_host,port=etcd_port)

        #create checks dir if not exist
        try:
            self.etcd.read(self.check_path)
        except KeyError:
            self.etcd.write(self.check_path, None, dir=True)

        while True:
          self.run()

    def run(self):
        now = datetime.utcnow()

        if (now - self.last_check_update).seconds > self.check_refresh:
            self.checks = self.checks + self._new_checks()
            self.last_check_update = now

        if not self.checks:
            print('no checks loaded, sleeping 5s')
            sleep(10)
            return

        [ self.jobs.put_nowait(c) for c in self.checks if \
                (now - c.last).seconds > c.interval ]

        self.launch_workers()

    def launch_workers(self):
        workers = [ gevent.spawn(self._worker) for \
                        n in range(1,self.concurrency) ]
        gevent.joinall(workers)

    def _new_checks(self):
        """
        returns a list of check objects from a path in etcd 
        if not already instantiated 
        """
        new_checks = []
        current = [ c.id for c in self.checks ]
        all_checks = { c.key:c.value for c in \
                self.etcd.read(self.check_path).children if not c.dir }

        for k,v in all_checks.iteritems():
            check_id = os.path.basename(k)
            if check_id not in current:
                new_checks.append(Check(check_id,v))

        return new_checks

    def _worker(self):
        """
        """
        while not self.jobs.empty():
            check = self.jobs.get()
            
            log.info('checking %s' % check.url)

            result = self._check_url(check.url,check.content)
            
            if result['ok']:
                check.response_time = result['elapsed']
                check.last = datetime.utcnow()
                check.ok()
            else:
                check.failures += 1 

            if check.failures > 3 and not check.notified and self.notifier:
                log.info('sending notification for failed check')
                self.notifier.notify('url check failure for %s -- %s' % \
                        (check.url,result['reason']))

                check.notified = True

            self.etcd.set('/checks/' + check.id, check.json())
            gevent.sleep(0)

    def _check_url(self,url,content):
        try:
            r = requests.get(url)
        except ConnectionError as e:
            log.warn('unable to reach %s:\n%s' % (url,e))
            return { 'ok':False,'reason':e }

        log.debug('%s returned %s' % (url,r.status_code))
        if not r.ok:
            return { 'ok':False,'reason': r.status_code } 
        if content and not content in r.text:
            return { 'ok':False,'reason': 'content check failure' }
        
        return { 'ok':True,'elapsed':r.elapsed.total_seconds() }

if __name__ == '__main__':
    um = Uptime()