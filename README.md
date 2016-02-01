# AsrielBot - A utility IRC bot for role playing channels


AsrielBot is an all-around utility bot for gaming or roleplay channels. It
includes a number of helpful functions such as a dice roller, information
retrieval, and so forth.

## History

This is a continuation of an IRC bot project which was
originally written in mIRC Scripting Language (known as
[reibot-mirc](https://github.com/Karunamon/mirc-reibot)), and then again in Ruby
([as rbreibot](https://github.com/Karunamon/reibot)), and now, in its third
generation, and as homage to one of my favorite games, it's been rewritten in
Python and named AsrielBot.

I did not ditch Ruby, mind you. It's still one of my favorite general purpose
languages, but I needed a reason to pick up Python for professional purposes.
What better way than using it heavily in a hobby project?

With a new language comes a change of frameworks, and instead of the
[Cinch](https://github.com/cinchrb/cinch) IRC framework used by Reibot,
AsrielBot uses the [irc3](https://github.com/gawel/irc3) framework.

## Features and usage info


AsrielBot has the same feature list as Reibot, with some slight usage
differences.

### Note system

The note system allows you to leave notes for users who are not active or even
offline. The next time a user joins the bot's channel (or speaks, if they never
left), the bot will deliver all messages a person has waiting for them. This is
super helpful on busy channels, and unlike the MemoServ system provided by most
IRC service packages, you can leave notes for people who are not registered.

Here's an example session

    <SomeGuy> ?note TomFubar Hey remember to check the status of the Gonkulator when you get back, thanks!
    <AsrielBot> Your note for TomFubar has been queued for delivery.
    ** TomFubar has joined #test
    <AsrielBot> TomFubar, I have 1 memo for you!
    <AsrielBot> SomeGuy // 2 hours ago // Hey remember to check the status of the Gonkulator when you get back, thanks!

Messages are delivered in the context they were left - so if you leave a note in
private message to the bot, the bot will deliver the message in private to the
user, and if you leave the note in a channel, the bot will deliver the message
wherever the recipient speaks first.

## Definitions (profiles) system

This is AsrielBot's main feature.

The definitions system allows you to store and retrieve arbitrary data. In
AsrielBot's home server, this functionality is used to store character profiles
for role playing purposes. Any information can be stored though - think of
anything you need to display repetitively, such as channel rules, or the address
for your clan's TF2 server, or a particularly funny quote that someone has
inadvertently made...

### Basic Usage

To store information, you use **?learn (name) (associated info)**, and then
**?? (name)** to retrieve it:

    <you> ?learn Rules Don't whizz on the electric fence!
    <AsrielBot> Your info "Rules" has been stored.
    ** Newbie has joined #test
    <you> Hi Newbie, make sure you read the server rules!
    <newbie> ?? rules
    <AsrielBot> Don't whizz on the electric fence!

Additionally, if you ?learn on something that already exists, the text you enter
will be appended to that info as another line.

Lines can be deleted by **?forget (name)**, but only either by the bot owner
(who's set as admin in the config file), or by the person who created it. Note
this system only checks nicknames, not hostmasks (as most sane servers have
systems to prevent squatting on nicknames.)

### Random Lines

Let's say you want to save quotes, or some other information where you want a
different line to come back every time? **?learn** the info as normal, adding
as many lines as you please, then do **?toggle_random** on that item. From then
on, the bot will retrieve a random item whenever an item is **??**'d.

### Web Editing

Furthermore, a web editing system exists. A user can type **?edit (name)** on 
something they own, and they will receive a randomly-generated URL to edit
the profile in a graphical environment.
## Dice roller

AsrielBot's dice roller allows you to roll arbitrary combinations of dice with
arbitrary mathematical functions carried out on the results. The command looks
like:

    (number of dice)d(number of sides per dice)(math modifier)(options)(text)

That looks really complicated, but here are some examples:

    <someguy> 2d20+5 TomFubar to hit
    <AsrielBot> [9, 5]=> 14+5 ==> 19, TomFubar to hit

This would roll two 20-sided dice, and add 5 to the overall result.

Other types of dice are supported as well, but you must use **?roll** rather
than just speaking a dice expression.

### Shadowrun:

Use the -s flag to **?roll**:

    ?roll (number of dice)d6 -s (text)
    <SomeGuy> ?roll 10d6 -s Hacking the gibson
    <AsrielBot> [4, 2, 2, 1, 4, 6, 6, 2, 6, 5]=> 38 (4 hits, 1 glitches) (hacking the gibson)

## Tumblr Image Poster

This requires configuration. You must register an app on Tumblr, and obtain
Oauth configuration data (this is your consumer key and secret, and your Oauth
token and secret)

Enter those into the appropriate areas of your config.ini, uncomment the plugin.

Then, every time someone in your channel mentions an image link, it will be
submitted to the Tumblr blog your credentials reference.

A database is used to prevent duplicate images (really duplicate addresses)
from being reposted.

## Requirements

* Python 2.7.x (*NOT* 3.x - sorry!)
* Pip

## Installing and getting started

- Clone the repo
- Install the requirements: `pip -r requirements.txt`
- Edit the `config.ini` file to meet your needs
- Start the bot with `python asrielbot.py`

## License


Copyright 2016 Michael Parks, TKWare Enterprises.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use the software in this repository except in compliance with the
License. You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
