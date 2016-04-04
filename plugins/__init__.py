import configparser

ini = configparser.ConfigParser()
ini.read('config.ini')


class PluginConfig:
    """
    A factory which provides easy access to the config file, based on the name
    of the calling class.
    """

    def __init__(self, klass):
        self.ini = ini
        self.cls = klass.__class__.__name__

    def get(self, value):
        return self.ini.get(self.cls, value)


class MessageRetargeter:
    """
    This is a weird class.

    Its mission in life is to accept irc3.bot objects,and provide a 'msg' method as an alternative to the bot.privmsg
    provided by irc3. The builtin method does not differentiate between whether the target you're replying to is a
    channel or a person, meaning that when using the 'target' provided by irc3.command, if you were replying to a user
    private message, the bot would message itself!
    """

    def __init__(self, bot):
        self.bot = bot

    def msg(self, mask, target, msg):
        """
        Retargets incoming messages - takes the mask and the target and determines if the original message was sent
        in private message or in a channel, and redirects appropriately. I have absolutely no idea why we have to
        check for both mask and target - you'd think since this is only ever called in the context of an irc3.command,
        that it would work the same way every time. Spooky.

        :type mask: irc3.utils.ircstring
        :type target: irc3.utils.ircstring
        :type msg: str
        """
        if mask == self.bot.nick:
            self.bot.privmsg(target.nick, msg)
        elif target == self.bot.nick:
            self.bot.privmsg(mask.nick, msg)
        elif mask.is_channel:
            self.bot.privmsg(mask, msg)
        else:
            self.bot.privmsg(target, msg)


class BotUtils:
    """
    Miscellaneous functions for use by the bot.

    :type bot: irc3.bot
    """
    def __init__(self, bot):
        self.bot = bot

    def cantfind_string(self, arg):
        """
        Returns a friendly message indicating that the bot can't find something.

        :arg arg: The thing that couldn't be found
        """



