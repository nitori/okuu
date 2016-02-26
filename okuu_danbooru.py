
from okuu import BasePlugin

from collections import OrderedDict
from urllib.parse import urlparse
import logging

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

    async def check_url(self, url):
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

    async def check_header(self, url, response, session):
        if response.history:
            return await self.check_url(response.url)

    async def get_url_info(self, url, session):
        logger.info('Fetching URL info from Danbooru API.   ')
        purl = urlparse(url)

        api_url = ''
        params = {}
        if self.config.get('api-key', None) is not None and\
                self.config.get('login', None) is not None:
            params['api_key'] = self.config['api-key']
            params['login'] = self.config['login']

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
        json_data = await session.get(
            api_url,
            headers=self.headers,
            params=params).json()
        if self.type == 'direct':
            json_data = json_data[0]

        if self.type in ('post', 'direct'):
            return self._get_post_data(json_data)
        else:
            return self._get_pool_data(json_data)

    def _get_post_data(self, json_data):
        warning_tags = set(
            map(str.lower, self.config.get('warning-tags', '').split())
        )
        tags = json_data['tag_string'].split()
        # tag_string = general + artist + copyright + character
        general_tags = json_data['tag_string_general'].split()
        artists = json_data['tag_string_artist'].split()
        copyright = json_data['tag_string_copyright'].split()
        characters = json_data['tag_string_character'].split()
        rating = {
            's': 'safe',
            'q': 'questionable',
            'e': 'explicit',
        }[json_data['rating']]
        return dict(
            name='Danbooru',
            plugin='danbooru',
            type='post',
            infos=OrderedDict([
                ('width', json_data.get('image_width')),
                ('height', json_data.get('image_height')),
                ('file_url', json_data.get('file_url')),  # might be None!
                ('post_id', json_data['id']),
                ('score', json_data['score']),
                ('rating', rating),
                ('warning_tags', sorted(warning_tags.intersection(tags))),
                ('general_tags', sorted(general_tags)),
                ('artists', sorted(artists)),
                ('copyright', sorted(copyright)),
                ('characters', sorted(characters)),
            ])
        )

    def _get_pool_data(self, json_data):
        return dict(
            name='Danbooru',
            type='pool',
            infos=OrderedDict([
                ('name', json_data['name'].replace('_', ' ')),
                ('pool_id', json_data['id']),
                ('post_count', json_data['post_count']),
                ('category', json_data['category']),
                ('description', json_data['description']),
            ])
        )
