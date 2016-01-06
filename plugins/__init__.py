import ConfigParser
import irc3

ini = ConfigParser.ConfigParser()
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
        :param mask:
        :type mask: irc3.IrcString
        :param target:
        :type target: irc3.IrcString
        :param msg:
        :type msg: str
        :type self: irc3.bot
        """
        if target == self.bot.nick:
            newtarget = mask.nick
            self.bot.privmsg(newtarget, msg)
        elif mask.is_channel:
            self.bot.privmsg(mask, msg)
        else:
            self.bot.privmsg(target, msg)
