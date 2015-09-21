import logging
import json

import requests

log = logging.getLogger('uptime')


class SlackNotifier(object):
    """
    Send service notifications via Slack
    params:
     - webhook_url(str): Slack webhook URL
     - channels(list): List of channel names to send notification to
     - username(str): Optional username to send notifications as
    """
    def __init__(self, webhook_url, channels, username='uptime'):
        self.url = webhook_url
        self.username = username
        self.channels = [ '#' + c for c in channels ]

    def notify(self, msg):
        for channel in self.channels:
            payload = {"channel": channel,
                       "username": self.username,
                       "text": msg,
                       "icon_emoji": ":code:"}
            r = requests.post(self.url, data=json.dumps(payload))
            log.info('sent slack message: %s' % r.status_code)
