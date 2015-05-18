
from okuu import BasePlugin

from collections import OrderedDict
from urllib.parse import urlparse, parse_qs
import logging

import requests
import re

logger = logging.getLogger(__name__)


class YouTube(BasePlugin):
    """
    https://www.googleapis.com/youtube/v3/videos?id=<video-id>&key=<api-key>&part=<parts>
    """

    def check_url(self, url):
        urlp = urlparse(url)
        if urlp.netloc in ('www.youtube.com', 'youtube.com'):
            if urlp.path.startswith('/watch'):
                query = parse_qs(urlp.query)
                video_ids = query.get('v', [])
                if video_ids:
                    self.video_id = video_ids.pop(0)
                    if self.video_id:
                        return True
            elif urlp.path.startswith('/embed/'):
                _, _, self.video_id, *_ = urlp.path.split('/')
                if self.video_id:
                    return True
        elif urlp.netloc in ('youtu.be',):
            _, self.video_id, *_ = urlp.path.split('/')
            if self.video_id:
                return True

    def check_header(self, url, response):
        if response.history:
            return self.check_url(response.url)

    def get_url_info(self, url):
        logger.info('Fetching URL info from YouTube Data APIv3.   ')
        parts = [s.strip() for s in self.config['api-parts'].split(',')]
        params = {
            'id': self.video_id,
            'key': self.config['api-key'],
            'part': ','.join(parts),
        }
        json_data = requests.get(
            'https://www.googleapis.com/youtube/v3/videos',
            headers=self.headers,
            params=params).json()

        if not json_data['pageInfo']['totalResults']:
            return dict(
                name='YouTube',
                plugin='youtube',
                infos={'status': 'no-result'})

        return dict(
            name='YouTube',
            plugin='youtube',
            # type='video',
            infos=OrderedDict([
                ('status', 'ok'),
                ('result', json_data['items'][0]),
            ]),
        )