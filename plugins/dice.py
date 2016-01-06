# -*- coding: utf-8 -*-
import random

import irc3
from irc3.dec import event
from irc3.plugins.command import Commands, command

from plugins import PluginConfig


def count_shadowrun(arg):
    glitches = 0
    hits = 0
    critical_threshold = len(arg) / 2 if len(arg) % 2 == 0 else len(arg) / 2 + 1
    for n in arg:
        if n == 1:
            glitches += 1
        elif n == 5 or n == 6:
            hits += 1

    if glitches >= critical_threshold and hits == 0:
        result = "(CRIT GLITCH! %s hits, %s glitches)" % (hits, glitches)
    elif glitches >= critical_threshold and hits > 0:
        result = "(Glitch with hits: %s hits, %s glitches)" % (hits, glitches)
    else:
        result = "(%s hits, %s glitches)" % (hits, glitches)

    return result


@irc3.plugin
class Dice(object):
    def __init__(self, bot):
        self.bot = bot
        self.rng = random.SystemRandom()
        self.cfg = PluginConfig(self)

    @command
    def roll(self, mask, target, args):
        """
        Rolls dice. "<dice>" Can be understood as d notation like 2d20 or 1d6.

        Usage:
            %%roll <dice>
            %%roll <dice> [<description_text>...]
            %%roll <dice> [-s] [<description_text>...]

        Options:
            -s, --shadowrun  Outputs dice in Shadowrun action format.
        """
        d = args['<dice>'].split("d")
        count = int(d[0])
        sides = int(d[1])

        if sides > 100:
            self.bot.privmsg(target, "That's an absurd number of sides.")
            irc3.base.logging.log(irc3.base.logging.WARN,
                                  "%s in %s tried to roll a %d sided dice" % (mask.nick, target, sides))
            return
        if count > 100:
            self.bot.privmsg(target, "That's too many dice!")
            irc3.base.logging.log(irc3.base.logging.WARN,
                                  "%s in %s tried to roll %d dice" % (mask.nick, target, count))
            return

        dice = []
        result = ""

        for n in range(0, count):
            dice.append(self.rng.randint(1, sides))

        if args["<description_text>"]:
            result += (" %s" % ' '.join(args["<description_text>"]))

        if args["-s"]:
            result += (" %s" % count_shadowrun(dice))

        self.bot.privmsg(target, str(dice) + result)

    # NOTE: Use this pattern later for aliasing commands
    @event("(@(?P<tags>\S+) )?:(?P<mask>\S+) PRIVMSG (?P<target>\S+) :(?P<data>\d+d\d+.*)")
    def easy_roll(self, mask, target, data):
        self.bot.get_plugin(Commands).on_command(cmd='roll', mask=mask, target=target, data=data)
