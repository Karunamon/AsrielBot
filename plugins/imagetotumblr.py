import irc3
import pytumblr
import re
from blitzdb import Document, FileBackend
from plugins import PluginConfig
from irc3.plugins.command import command


class PostedImage(Document):
    pass


class OptedOutUser(Document):
    pass


def user_is_opted_out(db, username):
    try:
        db.get(OptedOutUser, {'username': username.lower()})
    except OptedOutUser.DoesNotExist:
        return False
    else:
        return True


@irc3.plugin
class ImageToTumblr(object):
    def __init__(self, bot):
        self.cfg = PluginConfig(self)
        self.image_filetypes = self.cfg.get('image_filetypes').split(',')
        self.db = FileBackend(self.cfg.get('main_db'))
        self.anondb = FileBackend(self.cfg.get('optout_db'))
        self.bot = bot
        self.tumblr = pytumblr.TumblrRestClient(
                self.cfg.get('consumer_key'),
                self.cfg.get('consumer_secret'),
                self.cfg.get('oauth_token'),
                self.cfg.get('oauth_secret')
        )
        irc3.base.logging.log(irc3.base.logging.WARN,
                              "Tumblr poster ready! Posting all URLs with: %s" % self.image_filetypes
                              )

    def post_image(self, text, poster):
        # Strip everything but the address
        m = re.match(r'.*(?P<url>http.*)', text)
        url = m.group('url')
        poster = poster if not user_is_opted_out(self.anondb, poster) else "an anonymous person"
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
            except Exception as e:
                irc3.base.logging.log(irc3.base.logging.WARN, "Could not post to tumblr: %s" % url)
                raise e
        else:
            irc3.base.logging.log(irc3.base.logging.WARN, "Not posting duplicate image: %s" % url)
            return

    @irc3.event(irc3.rfc.PRIVMSG)  # Triggered on every message anywhere.
    def parse_image(self, target, mask, data, event):
        for extension in self.image_filetypes:
            if "." + extension.lower() in data:
                self.post_image(data, mask.nick)

    @command(public=False)
    def tumblr_optout(self, target, mask, args):
        """
        Mark yourself as opted out of Tumblr image posting. Any images you post will still end up on the site, but the
        name attached to each post will be changed to "an anonymous person".

        Usage:
            %%tumblr_optout
        """
        try:
            u = self.anondb.get(OptedOutUser, {'username': mask.nick.lower()})
        except OptedOutUser.DoesNotExist:
            d = OptedOutUser({'username': mask.nick.lower()})
            self.anondb.save(d)
            self.anondb.commit()
            self.bot.privmsg(mask.nick, "You are now opted out of tumblr image posting.")
        else:
            self.anondb.delete(u)
            self.anondb.commit()
            self.bot.privmsg(mask.nick, "You are NO LONGER opted out of tumblr image posting.")
