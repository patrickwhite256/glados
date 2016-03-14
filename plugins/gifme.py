import random
import re
from urllib.parse import urlencode

import requests

from plugin_base import GladosPluginBase

SEARCH_URL_TPL = 'https://api.imgur.com/3/gallery/search/top.json?{0}'
MAX_BYTES      = 1024 * 1024

QUERY_RE = re.compile(r'glados,?\s+giff?(?:\s+me)?\s+(.*)', re.I)

HELP_TEXT = 'I regret everything.'


class GifMe(GladosPluginBase):
    consumes_message = True

    def setup(self):
        with open('.imgur-client-token') as f:
            self.client_id = f.read().strip()

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None
        return QUERY_RE.match(msg['text'])

    def handle_message(self, msg):
        query_str = QUERY_RE.match(msg['text']).group(1)
        query_params = {
            'q_all': query_str,
            'q_type': 'anigif'
        }

        query_url = SEARCH_URL_TPL.format(urlencode(query_params))

        headers = {
            'Authorization': 'Client-ID {0}'.format(self.client_id)
        }

        resp = requests.get(query_url, headers=headers)

        def send_fail_msg(err=None, nsfw=False):
            if err:
                print(err)
            self.send(
                'No {1}results found for "{0}"'.format(query_str,
                                                       'SFW ' if nsfw else ''),
                msg['channel']
            )

        if resp.status_code != requests.codes.ok:
            send_fail_msg()
            return

        response = resp.json()
        if not response['data']:
            send_fail_msg()
            return

        filtered_images = [_ for _ in response['data'] if not _['nsfw']]
        if not filtered_images:
            send_fail_msg(nsfw=True)
            return

        filtered_images = [_ for _ in filtered_images
                           if _.get('size', MAX_BYTES + 1) <= MAX_BYTES]

        if not filtered_images:
            send_fail_msg()
            return

        image_data = random.choice(filtered_images)

        attachments = [{
            'fallback': '[inline image]',
            'title': image_data['title'],
            'image_url': image_data['link']
        }]

        self.send('', msg['channel'], attachments)

    @property
    def help_text(self):
        return HELP_TEXT
