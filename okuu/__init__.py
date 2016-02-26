
import importlib
import configparser
from collections import OrderedDict
import logging

import aiohttp

from . import utils

logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)-7s [%(asctime)-15s] (%(name)s) %(message)s'
)
logger = logging.getLogger(__name__)

__version_string__ = 'Okuu URL info script'


class Okuu:

    def __init__(self, configfile):
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read(configfile)
        self.plugins = []

        self.base_config = OrderedDict()
        for option in self.config.options('okuu'):
            value = self.config.get('okuu', option)
            self.base_config[option] = value if value is not None else True

        self.headers = {
            'user-agent': self.base_config.get(
                'user-agent', __version_string__)
        }

        for plugin_name in self.config.options('plugins'):
            plugin_config = OrderedDict()
            plugin_config.update(self.base_config)
            plugin_config['name'] = plugin_name
            plugin_section = 'plugin-{}'.format(plugin_name)
            if plugin_section in self.config.sections():
                for option in self.config.options(plugin_section):
                    value = self.config.get(plugin_section, option)
                    plugin_config[option] = value if \
                        value is not None else True
            plugin = Plugin(plugin_config)
            self.plugins.append(plugin)

    async def get_url_info(self, url):
        session = aiohttp.ClientSession()

        for plugin in self.plugins:
            plugin.import_module()
            handler = await plugin.check_url(url)
            if handler:
                try:
                    result = await handler.get_url_info(url, session)
                    if result is not None:
                        result['plugin'] = plugin.config['name']
                        return result
                except Exception as e:
                    logger.exception(
                        'Handler {!r} failed getting URL infos.'
                        .format(handler.config['name'])
                    )
        logger.info('No plugin matched the URL. Trying Headers next.')

        async with session.head(url, headers=self.headers) as response:
            for plugin in self.plugins:
                handler = await plugin.check_header(url, response, session)
                response.close()
                if handler:
                    try:
                        result = await handler.get_url_info(url, session)
                        if result is not None:
                            result['plugin'] = plugin.config['name']
                            return result
                    except Exception as e:
                        logger.exception(
                            'Handler {!r} failed getting URL infos.'
                            .format(handler.config['name'])
                        )
            logger.info('No plugin matched the Headers. Returning None.')
            if response.url != url:
                logger.info('URL was: {} -> {}'.format(url, response.url))
            else:
                logger.info('URL was: {}'.format(url))
        return None


class Plugin:
    def __init__(self, config):
        self.config = config
        self._module = None
        self._url_handlers = []

    def import_module(self):
        if self._module is None:
            self._module = importlib.import_module(
                'okuu_{}'.format(self.config['name'])
            )
        for name in dir(self._module):
            obj = getattr(self._module, name)
            if isinstance(obj, type) \
                    and obj is not BasePlugin \
                    and issubclass(obj, BasePlugin):
                self._url_handlers.append(obj(self.config))

    async def check_url(self, url):
        for handler in self._url_handlers:
            value = await handler.check_url(url)
            if value:
                return handler

    async def check_header(self, url, response, session):
        for handler in self._url_handlers:
            value = await handler.check_header(url, response, session)
            if value:
                return handler

    def __repr__(self):
        return '<{}.{} {}>'.format(
            self.__module__,
            self.__class__.__name__,
            self.config['name']
        )


class BasePlugin:

    def __init__(self, config):
        self.config = config

        self.headers = {
            'user-agent': config.get('user-agent', __version_string__)
        }

    async def check_url(self, url):
        pass

    async def check_header(self, url, response, session):
        pass

    async def get_url_info(self, url, session):
        pass
