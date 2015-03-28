
from okuu import BasePlugin

from urllib.parse import urlparse
import logging

import requests
import re

logger = logging.getLogger(__name__)


class Danbooru(BasePlugin):
    """
    # post
    http://danbooru.donmai.us/posts/1722321
    # converted to:
    http://danbooru.donmai.us/posts/1722321.json

    # direct link
    http://danbooru.donmai.us/data/6418cbad4f1e4a4706161a5a09e94d2a.png
    # converted to:
    http://danbooru.donmai.us/posts.json?tags=md5%3A6418cbad4f1e4a4706161a5a09e94d2a

    # pool
    http://danbooru.donmai.us/pools/2265
    # converted to:
    http://danbooru.donmai.us/pools/2265.json
    """
    post_pattern = re.compile(
        r'^https?://danbooru\.donmai\.us/posts/(?P<post_id>\d+)'
        r'(?:\.(?:json|xml))?'
        r'(?:(/|\?|#).*)?$'
    )
    direct_pattern = re.compile(
        r'^https?://danbooru\.donmai\.us/data/(?P<post_hash>[a-fA-F0-9]{32})'
        r'(?:\.(?:json|xml))?'
        r'\.(?:jpe?g|png|gif)'
        r'(?:(\?|#).*)?$'
    )
    pool_pattern = re.compile(
        r'^https?://danbooru\.donmai\.us/pools/(?P<pool_id>\d+)'
        r'(?:\.(?:json|xml))?'
        r'(?:(/|\?|#).*)?$'
    )

    def check_url(self, url):
        match = self.post_pattern.match(url)
        if match is not None:
            self.type = 'post'
            self.id = match.group('post_id')
            return True
        match = self.direct_pattern.match(url)
        if match is not None:
            self.type = 'direct'
            self.id = match.group('post_hash')
            return True
        match = self.pool_pattern.match(url)
        if match is not None:
            self.type = 'pool'
            self.id = match.group('pool_id')
            return True

    def check_header(self, url, response):
        if response.history:
            return self.check_url(response.url)

    def get_url_info(self, url):
        logger.info('Fetching URL info from Danbooru API.   ')
        purl = urlparse(url)

        api_url = ''
        params = {}
        if self.config.get('api-key', None) is not None:
            params['api_key'] = self.config['api-key']

        if self.type == 'post':
            api_url = '{}://danbooru.donmai.us/posts/{}.json'.format(
                purl.scheme,
                self.id
            )
        elif self.type == 'direct':
            api_url = '{}://danbooru.donmai.us/posts.json'.format(
                purl.scheme
            )
            params['tags'] = 'md5:{}'.format(self.id)
        elif self.type == 'pool':
            api_url = '{}://danbooru.donmai.us/pools/{}.json'.format(
                purl.scheme,
                self.id
            )

        json_data = requests.get(api_url, params=params).json()
        if self.type == 'direct':
            json_data = json_data[0]

        if self.type in ('post', 'direct'):
            return self._get_post_data(json_data)
        else:
            return self._get_pool_data(json_data)

    def _get_post_data(self, json_data):
        return 'post: ' + json_data['file_url']

    def _get_pool_data(self, json_data):
        return 'pool: ' + json_data['name']
