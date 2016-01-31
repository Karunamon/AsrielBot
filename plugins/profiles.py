import os
import random
import thread
import uuid
from time import sleep

import irc3
from blitzdb import Document, FileBackend
from flask import Flask, request
from flask.ext.mako import MakoTemplates
from flask.ext.mako import render_template
from irc3 import event
from irc3.plugins.command import command, Commands

from plugins import PluginConfig, MessageRetargeter


class Profile(Document):
    pass


class Session(Document):
    pass


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_templates')


@irc3.plugin
class Profiles(object):
    def __init__(self, bot):
        self.bot = bot

        self.cfg = PluginConfig(self)
        self.db = FileBackend(self.cfg.get('main_db'))

        mtt = MessageRetargeter(bot)
        self.msg = mtt.msg

        web = Flask(__name__, template_folder=tmpl_dir)
        mako = MakoTemplates()
        mako.init_app(web)

        # Add routes here
        web.add_url_rule('/edit_web/<args>', 'edit_web', self.edit_web, methods=['GET', 'POST'])

        thread.start_new_thread(web.run, (), {'host': '0.0.0.0'})

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

    ####
    # All web stuff below this point
    #

    @command
    def edit(self, mask, target, args):
        """
        Sends you a webpage link to edit <name>. Great for longer profiles. Make sure to keep the URL you are given
        secure, as with it, anyone can edit your profiles.

        Usage:
            %%edit <name>
        """
        # TODO: Clear any existing sessions the user has

        data = {
            'id': str(uuid.uuid4()),
            'name': mask.nick,
            'profile': args['<name>']
        }

        newses = Session(data)
        self.db.save(newses)
        self.db.commit()
        self.bot.privmsg(mask.nick,
                         "An editor has been set up for you at http://skaianet.tkware.us:5000/edit_web/%s" % str(
                                 data['id']))
        self.bot.privmsg(mask.nick, "Be very careful not to expose this address - with it, anyone can edit your stuff")

    def edit_web(self, args):
        # Web endpoint: /edit_web/<args>

        if request.method == 'GET':
            # Does the session exist?
            try:
                edit_session = self.db.get(Session, {'id': args})
            except Session.DoesNotExist:
                return render_template('youfail.html',
                                       bot=self.bot,
                                       failreason='Invalid Session',
                                       userfail=True)
            # Does the profile exist?
            name = edit_session.profile
            try:
                profile = self.db.get(Profile, {'name': name.lower()})
            except Profile.DoesNotExist:
                return render_template('youfail.html',
                                       bot=self.bot,
                                       failreason='I cannot find "%s" in the records.' % name
                                       )
            # Kick off to the edit page!
            return render_template('edit.html',
                                   bot=self.bot,
                                   profile=profile,
                                   username=edit_session.name,
                                   sessionid=edit_session.id
                                   )
        elif request.method == 'POST':
            # We have to look up the session ID one more time. Something could have happened to the profile
            # since we created the session.
            try:
                edit_session = self.db.get(Session, {'id': request.form['ID']})
            except Session.DoesNotExist:
                return render_template('youfail.html',
                                       bot=self.bot,
                                       failreason='Invalid Session',
                                       userfail=True)
            name = request.form['profile']
            try:
                profile = self.db.get(Profile, {'name': request.form['profile']})
            except Profile.DoesNotExist:
                return render_template('youfail.html',
                                       bot=self.bot,
                                       failreason='I cannot find "%s" in the records.' % name,
                                       userfail=True
                                       )

            # Now with the profile in hand, blank the lines field and rebuild it from the form.
            # Here we grab all numeric items from the submission, sort it, and one by one refill the DB object.
            lines = [item for item in request.form if item.isdigit()]
            lines.sort()
            profile.lines = []
            for item in lines:
                profile.lines.append(request.form[item])
            self.db.save(profile)
            self.db.delete(edit_session)
            self.db.commit()
            return render_template('done.html',
                                   bot=self.bot,
                                   profile=profile.name
                                   )
