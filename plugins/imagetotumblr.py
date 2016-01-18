import irc3
from blitzdb import Document, FileBackend
import pytumblr
from plugins import PluginConfig


class PostedImage(Document):
    pass


@irc3.plugin
class ImageToTumblr(object):
    def __init__(self, bot):
        self.cfg = PluginConfig(self)
        self.image_filetypes = self.cfg.get('image_filetypes').split(',')
        self.db = FileBackend(self.cfg.get('main_db'))
        self.tumblr = pytumblr.TumblrRestClient(
            self.cfg.get('consumer_key'),
            self.cfg.get('consumer_secret'),
            self.cfg.get('oauth_token'),
            self.cfg.get('oauth_secret')
        )
        irc3.base.logging.log(irc3.base.logging.WARN,
                              "Tumblr poster ready! Posting all URLs with: %s" % self.image_filetypes
                              )

    def post_image(self, url, poster):
        # Make sure we didn't do this one already
        try:
            self.db.get(PostedImage, {'url': url})
        except PostedImage.DoesNotExist:
            try:
                # First we post it to tumblr
                p = self.tumblr.create_photo(
                    'mmerpimages',
                    state='published',
                    source=str(url),
                    caption="Found by %s" % poster
                )
                irc3.base.logging.log(irc3.base.logging.WARN, "Posting image by %s: %s" % (poster, url))

                # And then record the fact that we did.
                self.db.save(PostedImage({'url': url}))
                self.db.commit()
            except:
                irc3.base.logging.log(irc3.base.logging.WARN, "Could not post to tumblr: %s" % url)
                return
        else:
            irc3.base.logging.log(irc3.base.logging.WARN, "Not posting duplicate image: %s" % url)

            return

    @irc3.event(irc3.rfc.PRIVMSG)  # Triggered on every message anywhere.
    def parse_image(self, target, mask, data, event):
        for extension in self.image_filetypes:
            if "." + extension in data:
                self.post_image(data, mask.nick)
