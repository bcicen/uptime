import logging
import json

import requests

log = logging.getLogger('uptime')


class SlackNotifier(object):
    """
    Send service notifications via Slack
    params:
     - webhook_url(str): Slack webhook URL
     - channel(str): channel name to send notification to
     - username(str): Optional username to send notifications as
    """
    def __init__(self, webhook_url, channel, username='uptime'):
        self.url = webhook_url
        self.username = username
        self.channel = channel

    def notify(self, msg):
        payload = {"channel": channel,
                   "username": self.username,
                   "text": msg,
                   "icon_emoji": ":code:"}
        r = requests.post(self.url, data=json.dumps(payload))
        log.info('sent slack message: %s' % r.status_code)
        if r.status_code != 200:
            log.error(r.text)
