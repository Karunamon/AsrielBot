import irc3
import archiveis
from irc3.plugins.command import Commands, command
from Plugins import PluginConfig, MessageRetargeter


@irc3.plugin
class Archiver(object):
    def __init__(self, bot):
        self.cfg = PluginConfig(self)
        self.domains = self.cfg.get('domains').split(',')
        self.bot = bot
        irc3.base.logging.log(irc3.base.logging.WARN,
                              "Archiver ready. Auto trigger on: %s" % self.domains
                              )
        mtt = MessageRetargeter(bot)
        self.msg = mtt.msg

    @command
    def archive(self, mask, target, args):
        """
        Generate an archive.is link for a website.

        Usage:
            %%archive <URL>
        """
        self.msg(mask, target, "Saving that...")
        try:
            url = archiveis.capture(args['<URL>'])
        except KeyError:
            self.msg(mask, target, "Sorry, I couldn't get that one.")
            return
        else:
            self.msg(mask, target, args['<URL>'] + " Archived==> " + url)

    @irc3.event(irc3.rfc.PRIVMSG)  # Triggered on every message anywhere.
    def auto_archive(self, target, mask, data, event):
        del event
        for domain in self.domains:
            if domain.lower() in data:
                self.bot.get_plugin(Commands).on_command(
                    cmd='archive', mask=mask, target=target, data=data
                )
