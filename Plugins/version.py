import irc3

VER = "1.0.0"


@irc3.plugin
class Version(object):
    def __init__(self, bot):
        self.bot = bot

    @irc3.event(irc3.rfc.CTCP)
    def version(self, nick, ctcp):
        if ctcp == "VERSION":
            self.bot.ctcp_reply(nick, "AsrielBot v%s by Karunamon")
