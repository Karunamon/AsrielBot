import _thread
import os
import random
import uuid
from enum import Enum
from time import sleep

import irc3
from blitzdb import Document, FileBackend
from flask import Flask, request
from flask.ext.mako import MakoTemplates
from flask.ext.mako import render_template
from irc3 import event
from irc3.plugins.command import command, Commands

from Plugins import PluginConfig, MessageRetargeter


class Profile(Document):
    pass


class Session(Document):
    pass


class Action(Enum):
    edit = 1000
    fulledit = 1500
    delete = 9000


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_templates')


def is_allowed_to(action: Action, owner: str, record: Profile) -> bool:
    """
    Returns true or false depending on if the passed owner is allowed to carry out the specified Action. Note that
    this is not a granular permission system, rather a set of sane best practices. A publicly editable profile
    probably shouldn't be publicly deletable.

    When hacking on this, assume that False will be returned, and define conditions where it should be True instead.
    """
    if record.get('public', False):  # Publicly editable profiles can be changed by anyone
        if action.edit:  # But only edited, nothing else.
            return True
    elif owner.lower() == record.owner:  # The owner of a profile can do whatever they want
        return True
    else:
        return False


def get_flags(record: Profile) -> str:
    """
    Returns a small textual string for certain special profiles.
    If a profile is marked random, (r) is added.
    If a profile is marked public, (p) is added.
    """
    ret = ""
    if record.get('random', False):
        ret += "(r) "
    if record.get('public', False):
        ret += "(p) "
    return ret


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

        _thread.start_new_thread(web.run, (), {'host': '0.0.0.0'})

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
                    'random': False,
                    'public': False
                }
            )
            profile.save(self.db)
            self.db.commit()
            self.msg(mask, target, 'Your data "%s" has been stored.' % name)
            return

        except Profile.MultipleDocumentsReturned:
            self.msg(mask, target, "Found more than one %s. This is bad! Please notify the bot owner." % name)
            return

        if is_allowed_to(Action.edit, mask.nick, profile):
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
            self.msg(mask, target, get_flags(profile) + random.choice(profile.lines))
        else:
            for line in profile.lines:
                self.msg(mask, target, get_flags(profile) + line)
                if len(profile.lines) >= int(self.cfg.get('throttle_max')):
                    sleep(int(self.cfg.get('throttle_time')))

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

        if is_allowed_to(Action.delete, mask.nick, profile):
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
    def toggle_public(self, mask, target, args):
        """
        Changes whether <name> is publicly editable or not

        Usage:
            %%toggle_public <name>
        """
        name = args['<name>'].lower()
        try:
            profile = self.db.get(Profile, {'name': name})
        except Profile.DoesNotExist:
            self.msg(mask, target, 'I cannot find "%s" in the records.' % name)
            return

        if is_allowed_to(Action.edit, mask.nick, profile):
            if profile.get('public', False):
                profile.public = False
                self.msg(mask, target, '"%s" is no longer publicly editable.' % name)
            else:
                profile['public'] = True
                self.msg(mask, target, '"%s" is now publicly editable.' % name)
            self.db.save(profile)
            self.db.commit()
            return
        else:
            self.msg(mask, target, 'You are not authorized to edit "%s". Ask %s instead.'
                     % (name, profile.owner))
            return

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

        if is_allowed_to(Action.edit, mask.nick, profile):
            profile.random = not profile.random
            self.msg(mask, target, 'Random mode for %s is set to: %s' % (profile.name, profile.random))
            profile.save(self.db)
            self.db.commit()
        else:
            self.msg(mask, target, 'You are not authorized to edit "%s". Ask %s instead.'
                     % (name, profile.owner))
            irc3.base.logging.log(irc3.base.logging.WARN,
                                  "%s tried to edit %s, but can't since it's owned by %s" %
                                  (mask.nick, profile.name, profile.owner)
                                  )

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

        name = args['<name>'].lower()

        try:
            profile = self.db.get(Profile, {'name': name})
        except Profile.DoesNotExist:
            self.msg(mask, target, 'I cannot find "%s" in the records.' % name)
            return

        if is_allowed_to(Action.fulledit, mask.nick, profile):
            newses = Session(data)
            self.db.save(newses)
            self.db.commit()
            self.bot.privmsg(mask.nick,
                             "An editor has been set up for you at http://skaianet.tkware.us:5000/edit_web/%s" % str(
                                 data['id']))
            self.bot.privmsg(mask.nick,
                             "Be very careful not to expose this address - with it, anyone can edit your stuff")
        else:
            self.msg(mask, target, 'You are not authorized to webedit "%s". Ask %s instead.'
                     % (name, profile.owner))

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
