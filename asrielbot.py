from irc3 import IrcBot
import sys
sys.path.append('..')
IrcBot.from_argv('config.ini')
