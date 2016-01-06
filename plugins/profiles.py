import random

import irc3
from blitzdb import Document, FileBackend
from irc3 import event
from irc3.plugins.command import command, Commands
from time import sleep

from plugins import PluginConfig, MessageRetargeter


class Profile(Document):
    pass


@irc3.plugin
class Profiles(object):
    def __init__(self, bot):
        self.bot = bot
        self.cfg = PluginConfig(self)
        self.db = FileBackend(self.cfg.get('main_db'))
        mtt = MessageRetargeter(bot)
        self.msg = mtt.msg

    @command
    def learn(self, mask, target, args):
        """
        Stores information allowing for later retrieval. Names are downcased for sanity.


        Usage:
            %%learn <name> <information>...
        """
        name = args['<name>'].lower()
        info = ' '.join(args['<information>'])

        try:
            profile = self.db.get(Profile, {'name': name})
        except Profile.DoesNotExist:
            profile = Profile(
                    {
                        'name': name,
                        'owner': mask.nick.lower(),
                        'lines': [info],
                        'random': False
                    }
            )
            profile.save(self.db)
            self.db.commit()
            self.msg(mask, target, 'Your data "%s" has been stored.' % name)
            return

        except Profile.MultipleDocumentsReturned:
            self.msg(mask, target, "Found more than one %s. This is bad! Please notify the bot owner." % name)
            return

        if profile.owner == mask.nick.lower():
            lines_to_append = profile.lines
            lines_to_append.append(info)
            profile.save(self.db)
            self.db.commit()
            self.msg(mask, target, 'Your data "%s" has been updated.' % name)
            return
        else:
            self.msg(mask, target, 'You are not authorized to edit "%s". Ask %s instead.'
                     % (name, profile.owner))
            return

    @command
    def query(self, mask, target, args):
        """
        Retrieve the information associated with <name>. If the item is marked random, then one random item will be
        returned.

        Usage:
            %%query <name>
            ?? <name>
        """
        name = args['<name>'].lower()

        try:
            profile = self.db.get(Profile, {'name': name})
        except Profile.DoesNotExist:
            self.msg(mask, target, 'I cannot find "%s" in the records.' % name)
            return

        if profile.random:
            self.msg(mask, target, "(r) " + random.choice(profile.lines))
        else:
            for line in profile.lines:
                self.msg(mask, target, line)
                if len(profile.lines) >= self.cfg.get('throttle_max'):
                    sleep(self.cfg.get('throttle_time'))

    @command
    def forget(self, mask, target, args):
        """
        Delete <name> from the records. Only the person who created the item can remove it.

        Usage:
            %%forget <name>
        """
        name = args['<name>'].lower()
        try:
            profile = self.db.get(Profile, {'name': name})
        except Profile.DoesNotExist:
            self.msg(mask, target, 'I cannot find "%s" in the records.' % name)
            return

        if profile.owner == mask.nick.lower():
            self.db.delete(profile)
            self.db.commit()
            self.msg(mask, target, "%s has been deleted." % name)
        else:
            self.msg(mask, target, 'You are not authorized to delete "%s". Ask %s instead.'
                     % (name, profile.owner))

    @command(permission='admin', show_in_help_list=False)
    def rmf(self, mask, target, args):
        """
        Delete <name> from the records without checking permissions.

        Usage:
            %%rmf <name>
        """
        name = args['<name>'].lower()
        try:
            profile = self.db.get(Profile, {'name': name})
        except Profile.DoesNotExist:
            self.msg(mask, target, 'I cannot find "%s" in the records.' % name)
            return

        self.db.delete(profile)
        self.db.commit()
        self.msg(mask, target, "%s has been deleted." % name)

    @command(permission='admin', show_in_help_list=False)
    def chown(self, mask, target, args):
        """
        Change the owner of <name> to <newowner>.

        Usage:
            %%chown <name> <newowner>
        """
        name = args['<name>'].lower()
        newowner = args['<newowner>'].lower()
        try:
            profile = self.db.get(Profile, {'name': name})
        except Profile.DoesNotExist:
            self.msg(mask, target, 'I cannot find "%s" in the records.' % name)
            return
        profile.owner = newowner
        self.db.save(profile)
        self.db.commit()
        self.msg(mask, target, "%s is now owned by %s." % (name, newowner))

    @command
    def toggle_random(self, mask, target, args):
        """
        Toggle the randomness of an item, so that it shows a single random line instead of all lines when queried.

        Usage:
            %%toggle_random <name>
        """
        name = args['<name>'].lower()
        try:
            profile = self.db.get(Profile, {'name': name})
        except Profile.DoesNotExist:
            self.msg(mask, target, 'I cannot find "%s" in the records.' % name)
            return

        if profile.owner == mask.nick.lower():
            profile.random = not profile.random
            self.msg(mask, target, 'Random mode for %s is set to: %s' % (profile.name, profile.random))
            profile.save(self.db)
            self.db.commit()
        else:
            self.msg(mask, target, 'You are not authorized to edit "%s". Ask %s instead.'
                     % (name, profile.owner))
            irc3.base.logging.log(irc3.base.logging.WARN,
                                  "%s tried to edit %s, but can't since it's owned by %s" % (mask.nick, profile.name, profile.owner))

    @event("(@(?P<tags>\S+) )?:(?P<mask>\S+) PRIVMSG (?P<target>\S+) :\?\? (?P<data>.*)")
    def easy_query(self, mask, target, data):
        self.bot.get_plugin(Commands).on_command(cmd='query', mask=mask, target=target, data=data)
