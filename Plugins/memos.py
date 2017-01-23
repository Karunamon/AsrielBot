import datetime
from time import ctime

import humanize
import irc3
from blitzdb import FileBackend, Document
from irc3.plugins.command import command

from Plugins import PluginConfig, MessageRetargeter


class Memo(Document):
    pass


def contains_private_messages(msgset):
    """
    :param msgset: A Memo queryset
    :type msgset: blitzdb.queryset
    :return: True if any of the messages are private, False otherwise.
    :rtype: Boolean
    """
    for msg in msgset:
        if not msg.public:
            return True
    return False


@irc3.plugin
class Memos(object):
    def __init__(self, bot):
        self.bot = bot
        self.cfg = PluginConfig(self)
        self.db = FileBackend(self.cfg.get('main_db'))
        mtt = MessageRetargeter(bot)
        self.msg = mtt.msg

    @command
    def note(self, target, mask, args):
        """
        Leaves a note for <name>, containing <text>. The next time I see <name> speak, I will deliver any notes they
        have waiting.

        Notes taken in private are delivered in private, and vice versa.

        Usage:
            %%note <name> <text>...
        """
        if mask.is_channel:
            pubmsg = True
        else:
            pubmsg = False

        if args['<name>'] == self.bot.nick:
            self.msg(mask, target, "You can't leave notes for me, silly :)")

        newmemo = Memo(
                {
                    'sender': target.nick.lower(),
                    'recipient': args['<name>'].lower(),
                    'public': pubmsg,
                    'timestamp': ctime(),
                    'text': ' '.join(args['<text>'])
                }
        )
        newmemo.save(self.db)
        self.db.commit()

        confirmation_msg = "Your note for %s has been queued for delivery." % args['<name>']
        self.msg(mask, target, confirmation_msg)

    @irc3.event(irc3.rfc.PRIVMSG)  # Triggered on every message anywhere.
    def check_notes(self, target, mask, data, event):
        del data, event
        try:
            msgs = self.db.filter(Memo, {'recipient': mask.nick.lower()})
            msgword = "message" if len(msgs) < 2 else "messages"  # Fix: I have 1 messages for you!
        except Memo.DoesNotExist:
            return

        if len(msgs) == 0:
            return

        # Avoid telling people they have messages in public, if any of them are set public=False
        if contains_private_messages(msgs):
            self.msg(mask, mask.nick, "I have %s %s for you, %s!" % (len(msgs), msgword, mask.nick))
        else:
            self.msg(mask, target, "I have %s %s for you, %s!" % (len(msgs), msgword, mask.nick))

        # Actually deliver the memos
        for msg in msgs:
            # This looks ridiculous but we don't care about the timezone really, only the relative time
            # from the local system clock.
            now = datetime.datetime.strptime(ctime(), "%a %b %d %H:%M:%S %Y")
            reltime = humanize.naturaltime(now - datetime.datetime.strptime(msg.timestamp, "%a %b %d %H:%M:%S %Y"))
            message_text = "%s // %s // %s" % (msg.sender, reltime, msg.text)
            if msg.public:
                self.msg(mask, target, message_text)
                self.db.delete(msg)
            else:
                self.bot.privmsg(mask.nick, message_text)
                self.db.delete(msg)
        self.db.commit()
