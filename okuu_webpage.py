
from okuu import BasePlugin
import logging

import aiohttp
import bs4


logger = logging.getLogger(__name__)


class Webpage(BasePlugin):

    async def check_header(self, url, response, session):
        self.redirected_to_url = response.url
        self.history_urls = [r.url for r in response.history]
        content_type = response.headers.get('content-type', '')
        if content_type.strip().lower().startswith('text/html'):
            return True

    async def get_url_info(self, url, session: aiohttp.ClientSession):
        # no need to follow redirects once more
        response = await session.get(self.redirected_to_url)
        content_type = response.headers.get('content-type', '').lower()
        if 'charset' in content_type:
            # requests knows what encoding to use
            html_code = await response.text()
        else:
            # let beautifulsoup handle the decoding
            html_code = await response.content()

        soup = bs4.BeautifulSoup(html_code, 'html.parser')
        page_title = ' '.join(soup.title.text.split())

        return dict(
            name='Webpage',
            type=None,
            infos={
                'page_title': page_title,
                'history_urls': self.history_urls,
                'endpoint': self.redirected_to_url,
            }
        )