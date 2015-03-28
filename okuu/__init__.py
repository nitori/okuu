
import importlib
import configparser
from collections import OrderedDict
import logging

import requests

from . import utils

logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)-8s[%(asctime)-15s] %(message)s'
)
logger = logging.getLogger(__name__)


class Okuu:

    def __init__(self, configfile):
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read(configfile)
        self.plugins = []

        base_config = OrderedDict()
        for option in self.config.options('okuu'):
            value = self.config.get('okuu', option)
            base_config[option] = value if value is not None else True

        for plugin_name in self.config.options('plugins'):
            plugin_config = OrderedDict()
            plugin_config.update(base_config)
            plugin_config['name'] = plugin_name
            plugin_section = 'plugin-{}'.format(plugin_name)
            if plugin_section in self.config.sections():
                for option in self.config.options(plugin_section):
                    value = self.config.get(plugin_section, option)
                    plugin_config[option] = value if \
                        value is not None else True
            plugin = Plugin(plugin_config)
            self.plugins.append(plugin)

    def get_url_info(self, url):
        for plugin in self.plugins:
            plugin.import_module()
            handler = plugin.check_url(url)
            if handler:
                try:
                    result = handler.get_url_info(url)
                    if result is not None:
                        return result
                except Exception as e:
                    logger.exception(
                        'Handler {!r} failed getting URL infos.'
                        .format(handler.config['name'])
                    )

        response = requests.head(url, allow_redirects=True)
        for plugin in self.plugins:
            handler = plugin.check_header(url, response)
            if handler:
                try:
                    result = handler.get_url_info(url)
                    if result is not None:
                        return result
                except Exception as e:
                    logger.exception(
                        'Handler {!r} failed getting URL infos.'
                        .format(handler.config['name'])
                    )
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

    def check_url(self, url):
        for handler in self._url_handlers:
            value = handler.check_url(url)
            if value:
                return handler

    def check_header(self, url, response):
        for handler in self._url_handlers:
            value = handler.check_header(url, response)
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

    def check_url(self, url):
        pass

    def check_header(self, url, response):
        pass

    def get_url_info(self, url):
        pass
