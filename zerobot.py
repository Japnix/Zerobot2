import discord
from discord.ext import commands
import urllib.request
import urllib.parse
import json
import datetime
import sys
import random
import os
import logging
import yaml


discordtoken = sys.argv[1]
stocktoken = sys.argv[2]
embedcolor = 0xed330e
settingsjson = os.path.dirname(__file__) + "/settings.json"
description = '''Zerobot is a discord bot written by Japnix.  It's primary use is announcements.  But has some generic
utility functions built in.'''

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')


# Read in prefix from settings.json
async def get_pre(bot, message):
    with open(os.path.dirname(__file__) + "/settings.json", 'r') as x:
        myfile = json.loads(x.read())

    return myfile[str(message.guild.id)]['prefix']


bot = commands.Bot(command_prefix=get_pre, description=description)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('Startup Time: ' + str(datetime.datetime.utcnow()))
    print('Guilds Added: ' + str(len(bot.guilds)))
    print('------')

    if os.path.isfile(os.path.dirname(__file__) + "/settings.json"):
        print('Loaded settings.json')
        with open(os.path.dirname(__file__) + "/settings.json", 'r') as myfile:
            myfile = json.loads(myfile.read())

    else:
        print('Creating settings.json')
        myfile = open(os.path.dirname(__file__) + '/settings.json', 'w+')
        myjson = {}
        for x in bot.guilds:
            myjson[str(x.id)] = {'prefix': '?'}

        json.dump(myjson, myfile)
        myfile.close()


@bot.event
async def on_guild_join(ctx):
    logging.info('Guild ' + ctx.name + ' added ' + ctx.me.display_name + '.')
    with open(settingsjson, 'r') as myfile:
        myjson = json.load(myfile)

    myjson[str(ctx.id)] = {'prefix': '?', 'name': str(ctx.name)}

    with open(settingsjson, 'w+') as myfile:
        json.dump(myjson, myfile)


@bot.event
async def on_guild_remove(ctx):
    logging.info('Guild ' + ctx.name + ' removed ' + ctx.me.display_name + '.')
    with open(settingsjson, 'r') as myfile:
        myjson = json.load(myfile)

    del myjson[str(ctx.id)]

    with open(settingsjson, 'w+') as myfile:
        json.dump(myjson, myfile)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        logging.info(str(error))


@bot.command()
async def announcement(ctx, *, msg):
    channel = None

    for x in ctx.guild.text_channels:
        if x.name == 'announcements':
            channel = x

    if channel is None:
        msg = 'There is no text channel #announcements in this guild'
    else:
        msg = ctx.author.display_name + ': ' + msg

    await channel.send(msg)


@bot.command()
async def stock(ctx, *, query):
    request_url = 'https://cloud.iexapis.com/stable/tops/last?token=' + stocktoken\
                  + '&symbols=' + urllib.parse.quote(query)

    embed = discord.Embed(title='Stock Queries',
                          timestamp=datetime.datetime.utcnow(),
                          color=embedcolor)

    try:
        data = urllib.request.urlopen(request_url)
        content = data.read().decode('utf-8')
        data = json.loads(content)

        if len(data) == 0:
            embed = discord.Embed(title="No Stock Matches",
                                  timestamp=datetime.datetime.utcnow(),
                                  color=embedcolor)

        elif len(data) == 1:
            embed.add_field(name=data[0]['symbol'], value=data[0]['price'])

        else:
            for tickers in data:
                embed.add_field(name=tickers['symbol'], value=tickers['price'])

    except:
        embed = discord.Embed(title="Issue with stock API",
                              timestamp=datetime.datetime.utcnow(),
                              color=embedcolor)

    finally:
        await ctx.channel.send(embed=embed)


@bot.command()
async def roll(ctx, dice: str):

    """Rolls a dice in NdN format."""

    try:
        rolls, limit = map(int, dice.split('d'))

    except Exception:
        await ctx.send('Format has to be in NdN!')
        return

    if 1 <= int(rolls) <= 20 and 2 <= int(limit) <= 100:
        result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))

    else:
        result = 'Outside of range.  Limit 20 rolls of D100 or less.'

    await ctx.channel.send(result)


@bot.command()
async def prefix(ctx, prefix):
    """This command allows guild owners or administrators to change the prefix used for commands.

    The default prefix is `?` EX: ?name WOL.

    Example:
        ?prefix z!

        Then...
        z!name WOL
    """

    with open(settingsjson, 'r') as myfile:
        myjson = json.load(myfile)

    if ctx.message.author.id == ctx.guild.owner.id or ctx.message.author.guild_permissions.administrator is True:
        logging.info(ctx.guild.name + ' (' + str(ctx.guild.id) + ') ' + 'changed prefix to ' + prefix)
        myjson[str(ctx.guild.id)]['prefix'] = prefix
        embed = discord.Embed(title='Switched prefix to ' + str(prefix), color=embedcolor,
                              timestamp=datetime.datetime.utcnow())

        with open(settingsjson, 'w+') as myfile:
            json.dump(myjson, myfile)

    else:
        embed = discord.Embed(title='You are not the guild owner or administrator.', color=embedcolor,
                              timestamp=datetime.datetime.utcnow())
    await ctx.channel.send(embed=embed)


#@bot.command()
#async def newrole(ctx, role_name):
#    role_color = discord.Colour(0x00FF00)
#
#    await ctx.guild.create_role(name=role_name, color=role_color)


@bot.command()
async def register(ctx):
    """This command assigns the message sender to the Players role to be used for online locals."""

    role = discord.utils.get(ctx.guild.roles, name='Players')

    if role:
        if ctx.guild.id == 536237827537764353 or ctx.guild.id == 235423053767639040:
            message = f"Hey {ctx.author.display_name}! Thank you for registering. To complete your registration, please send $6 to gametheorycards@gmail.com, Sending to a Friend. In the Notes section of your transaction, please include your full name, FFTCG, and the tournament's date, formatted MM/DD/YY."
            await ctx.author.send(message)

        await ctx.message.author.add_roles(role)
        #await ctx.channel.send(f"```{ctx.message.author.display_name} has registered```")
        await ctx.message.add_reaction('\U00002705')


    else:
        await ctx.channel.send("```Players Role does not exist in this guild```")


@bot.command()
async def paid(ctx):
    """This command assigns the message sender to the Paid role to be used for online locals."""

    role = discord.utils.get(ctx.guild.roles, name='Paid')

    if role:
        await ctx.message.author.add_roles(role)
        #await ctx.channel.send(f"```{ctx.message.author.display_name} has registered```")
        await ctx.message.add_reaction('\U00002705')

    else:
        await ctx.channel.send("```Paid Role does not exist in this guild```")


@bot.command()
async def clearplayers(ctx):
    """This command clears all members of the Players role used for online locals"""

    roles = [discord.utils.get(ctx.guild.roles, name='Players'),
             discord.utils.get(ctx.guild.roles, name='Paid')]

    if roles and ctx.message.author.guild_permissions.administrator is True:
        for role in roles:
            for x in role.members:
                await x.remove_roles(role)

        await ctx.channel.send("```Players + Paid roles have been emptied```")

    elif ctx.message.author.guild_permissions.administrator is False:
        await ctx.channel.send("```You are not an administrator```")

    else:
        await ctx.channel.send("```Players + Paid roles does not exist in this guild```")


@bot.command()
async def unregister(ctx):
    """This command removes the message sender to the Players role to be used for online locals."""

    role = discord.utils.get(ctx.guild.roles, name='Players')

    if role:
        await ctx.message.author.remove_roles(players_role)
        #await ctx.channel.send(f"```{ctx.message.author.display_name} has unregistered```")
        await ctx.message.add_reaction('\U00002705')

    else:
        await ctx.channel.send("```Players Role does not exist in this guild```")


@bot.command()
async def players(ctx):
    """This command lists all players currently registered for online locals"""

    role = discord.utils.get(ctx.guild.roles, name='Players')
    paid_role = discord.utils.get(ctx.guild.roles, name='Paid')

    if role:
        if role.members:
            message = '```\n'
            for x in role.members:
                if paid_role in x.roles:
                    message += x.display_name + ' - Paid\n'
                else:
                    message += x.display_name + '\n'

            message += '```'

        else:
            message = '```Nobody has registered```'

        await ctx.channel.send(message)

    else:
        await ctx.channel.send("```Players Role does not exist in this guild```")


@bot.command()
async def paidplayers(ctx):
    """Same as players command, however reads from YAML which contains discord id's for regular name printing"""

    with open(os.path.dirname(__file__) + '/players.yml', 'r') as f:
        players = yaml.safe_load(f)

    role = discord.utils.get(ctx.guild.roles, name='Players')
    paid_role = discord.utils.get(ctx.guild.roles, name='Paid')

    if role:
        if role.members:
            message = '```\n'
            for x in role.members:
                if paid_role in x.roles:
                    if x.id in players.keys():
                        message += players[x.id] + " - Paid\n"
                    else:
                        message += x.display_name + " - Paid\n"

                else:
                    if x.id in players.keys():
                        message += players[x.id] + "\n"
                    else:
                        message += x.display_name + "\n"


            message += '```'

        else:
            message = '```Nobody has registered```'

        await ctx.channel.send(message)

    else:
        await ctx.channel.send("```Players Role does not exist in this guild```")


@bot.command()
async def prettyplayers(ctx):
    """Same as players command, however reads from YAML which contains discord id's for regular name printing"""

    with open(os.path.dirname(__file__) + '/players.yml', 'r') as f:
        players = yaml.safe_load(f)

    role = discord.utils.get(ctx.guild.roles, name='Players')

    message = '```\n'

    if role:
        if role.members:
            for x in role.members:
                if x.id in players.keys():
                    message += players[x.id] + "\n"
                else:
                    message += x.display_name + "\n"

            message += '```'

        else:
            message = '```Nobody has registered```'

        await ctx.channel.send(message)

    else:
        await ctx.channel.send("```Players Role does not exist in this guild```")


bot.run(discordtoken)