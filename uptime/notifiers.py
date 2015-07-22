import logging
import json

import requests

log = logging.getLogger('uptime')


class SlackNotifier(object):
    def __init__(self, webhook_url, username="uptime"):
        self.url = webhook_url
        self.username = username

    def notify(self, msg, channel="#system-alerts"):
        # noinspection PyPep8,PyPep8,PyPep8,PyPep8,PyPep8
        payload = {"channel": channel,
                   "username": self.username,
                   "text": msg,
                   "icon_emoji": ":code:"}
        r = requests.post(self.url, data=json.dumps(payload))
        log.info('sent slack message: %s' % r.status_code)
