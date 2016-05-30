# coding=utf-8
import random
import re
from typing import List, Tuple

import irc3
from irc3.plugins.command import command

from plugins import MessageRetargeter
from plugins import PluginConfig


class DiceBag(object):
    def __init__(self, diceary: List[str], color: str):
        self.dicebag = diceary
        self.dicecolor = color

    def draw(self, count: int) -> Tuple[List[str], str]:
        return [random.choice(self.dicebag) for _ in range(0, count)], self.dicecolor


# def cancel(lst):
#     """
#     Return the cancellized version of a diceroll list
#     :param lst:
#     :type lst: list
#     """
#     # TODO: Value cancellation
#     # Successes [S] (explosions) canceled by failures [F] (upside down triangles?)
#     # Triumphs [!] (lightsabers) count as successes [S].
#     # Advantages [A] (wings) canceled by threats [T] (hexagrams)
#     # Despairs [X] (circled upside down triangles) [F] count as failures.
#     # Force are their own thing [D, L]
#     # Example that rolled one of every type:
#     # [SA, T, '', T, A, F, DD]
#     # As rolled, 1 success, 2 advantage, 1 failure, 2 threats.
#     # Failures cancel successes, threats cancel advantages.
#     # This roll would have a net score of zero, aside from the force dice.

# NOTE: Pay attention to the second item in the tuples - there's an ASCII ETX character
# in front of each pair of numbers that may not be visible in the font you're using.
# This is used for mIRC color codes.
dies = {
    'b': DiceBag([' ', ' ', 'AA', 'A', 'SA', 'S'], '1,11'),  # Boost
    's': DiceBag([' ', ' ', 'F', 'F', 'T', 'T'], '0,1'),  # Setback
    'a': DiceBag([' ', 'S', 'S', 'SS', 'A', 'A', 'SA', 'AA'], '1,3'),  # Ability
    'd': DiceBag([' ', 'F', 'FF', 'T', 'T', 'T', 'TT', 'TF'], '0,6'),  # Difficulty
    'p': DiceBag([' ', 'S', 'S', 'SS', 'SS', 'A', 'AS', 'AS', 'AS', 'AA', 'AA', '!'], '1,8'),  # Proficiency
    'c': DiceBag([' ', 'F', 'F', 'FF', 'FF', 'T', 'T', 'FT', 'FT', 'TT', 'TT', 'X'], '0,5'),  # Challenge
    'f': DiceBag(['D', 'D', 'D', 'D', 'D', 'D', 'DD', 'L', 'L', 'LL', 'LL', 'LL'], '1,0')  # Force
}


# TODO: Emojified variants, that is if I can get the editor to display them...


@irc3.plugin
class EoteDice(object):
    def __init__(self, bot):
        self.bot = bot
        self.rng = random.SystemRandom()
        self.cfg = PluginConfig(self)
        mtt = MessageRetargeter(bot)
        self.msg = mtt.msg

    @command
    def eote(self, mask, target, args):
        """
        Rolls EOTE narrative dice. Dice are formatted as (number)(type), where type is the first letter of each dice
        type.
        You can use (B)oost, (S)etback, (A)bility, (D)ifficulty, (P)roficiency, (C)hallenge, or (F)orce.
        An example would be '2b1s1a' - 2 boost, 1 setback, 1 ability.

        Usage:
            %%eote <dice>
        """
        dicetable = []
        result = ""
        dice = args['<dice>']
        rex = r'(\d[bsadpcf])+?'
        to_roll = re.findall(rex, dice)  # type: List[str]
        for group in to_roll:
            dicecnt = group[0]
            dicetype = group[1]
            dicetable.append(dies[dicetype].draw(int(dicecnt)))


        for roll in dicetable:
            result += roll[1]       # The color code
            result += str(roll[0])  # The roll list ['SS', 'AS']
            result += ' '          # A space, and another color code character to terminate

        self.msg(mask, target, result)
