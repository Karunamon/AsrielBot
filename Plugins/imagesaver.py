import re
import sys
import urllib.request
from urllib import error

import irc3

from plugins import PluginConfig


@irc3.plugin
class ImageSaver(object):
    def __init__(self, bot):
        self.cfg = PluginConfig(self)
        self.image_filetypes = self.cfg.get('image_filetypes').split(',')
        self.bot = bot
        irc3.base.logging.log(irc3.base.logging.WARN,
                              "Image downloader ready! Triggering on: %s" % self.image_filetypes
                              )
        self.dlpath = self.cfg.get('download_path')

    def grab_image(self, text, poster):
        # Strip everything but the address
        m = re.match(r'.*(?P<url>http.*)', text)
        url = m.group('url')
        # noinspection PyTypeChecker
        filename = url.split('/')[-1]

        irc3.base.logging.log(irc3.base.logging.WARN, "Downloading image by %s: %s" % (poster, url))

        try:
            urllib.request.urlretrieve(url, self.dlpath + filename)

        except urllib.error.HTTPError:
            irc3.base.logging.log(irc3.base.logging.ERROR, "Error: %s" % sys.exc_info()[0])

    @irc3.event(irc3.rfc.PRIVMSG)  # Triggered on every message anywhere.
    def parse_image(self, target, mask, data, event):
        for extension in self.image_filetypes:
            if "." + extension.lower() in data:
                self.grab_image(data, mask.nick)
