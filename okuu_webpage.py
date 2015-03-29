
from okuu import BasePlugin

from urllib.parse import urlparse
import logging
import re

import requests
import bs4


logger = logging.getLogger(__name__)


class Webpage(BasePlugin):

    def check_header(self, url, response):
        self.request_url = response.url
        self.was_redirected = False
        if response.history:
            self.was_redirected = True

        content_type = response.headers.get('content-type', '')
        if content_type.strip().lower().startswith('text/html'):
            return True

    def get_url_info(self, url):
        response = requests.get(self.request_url)
        content_type = response.headers.get('content-type', '')
        if 'charset' in content_type:
            html_code = response.text
        else:
            html_code = response.content

        soup = bs4.BeautifulSoup(html_code)
        page_title = ' '.join(soup.title.text.split())

        return dict(
            name='Webpage',
            plugin='webpage',
            type=None,
            infos={
                'page_title': page_title
            }
        )