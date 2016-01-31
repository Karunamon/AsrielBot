import traceback

import irc3
from irc3.plugins.command import command


@irc3.plugin
class Admin(object):
    def __init__(self, bot):
        self.bot = bot

    @command(permission='admin', show_in_help_list=False)
    def dumpstate(self, mask, target, args):
        del target, args
        """
        Dump's the bot object's configuration state

        Usage:
            %%dumpstate
        """
        self.bot.privmsg(mask.nick, str(self.bot.__dict__))

    @command(permission='admin', show_in_help_list=False)
    def ev(self, mask, target, args):
        del mask
        """
        Evaluate the python code provided. This is a MASSIVE security hole - choose your admins carefully.

        Usage:
            %%ev <code>...

        """
        try:
            self.bot.privmsg(target, str(eval(' '.join(args['<code>']))))
        except Exception as e:
            self.bot.privmsg(target, traceback.format_exc(e))
            raise e
