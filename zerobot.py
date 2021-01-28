import discord
from discord.ext import commands
import urllib.request
import urllib.parse
import json
import datetime
import sys
import random
import logging
import pymongo
import argparse


# Create argparse parser
parser = argparse.ArgumentParser(description='Run a Zerobot"')
parser.add_argument('-d', '--db', type=str ,help='mongob:// url with port', required=True)
parser.add_argument('-t', '--token', type=str, help='Discord bot token that will be used', required=True)
parser.add_argument('-s', '--stock', type=str, help='Stock API Key', required=True)
args = parser.parse_args()


MONGODB = args.db
DISCORDTOKEN = args.token
STOCKTOKEN = args.stock
EMBEDCOLOR = 0xed330e
DESCRIPTION = '''Zerobot is a discord bot written by Japnix.  Its primary use is announcements.  But has some generic
utility functions built in.'''

MYCLIENT = pymongo.MongoClient(MONGODB)
MYDB = MYCLIENT['ZerobotProd']

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

# Return prefix based on SETTINGS dict which is in memory
# TODO: Not sure why bot is required as an argument if it's
#       not used in the function.
def get_pre(bot, message):
    mycol = MYDB['settings']
    dbq = mycol.find_one({'guildid': message.guild.id})
    prefix = dbq['prefix']

    return prefix


bot = commands.Bot(command_prefix=get_pre, description=DESCRIPTION)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('Startup Time: ' + str(datetime.datetime.utcnow()))
    print('Guilds Added: ' + str(len(bot.guilds)))
    print('------')

    mycol = MYDB['settings']
    dbq = mycol.find()

    dbguilds = [doc['guildid'] for doc in dbq]
    botguilds = [guild.id for guild in bot.guilds]


    # If when we start the bot there are more guilds in settings.json then the bot see's as joined
    # we remove those bots from settings.json
    if len(dbguilds) > len(botguilds):
        for guildid in dbguilds:
            if guildid not in botguilds:
                dbq = mycol.find_one({"guildid": guildid})
                logging.info(f"Guild {dbq['name']} ({guildid}) was removed while the bot was offline.  Removing from db.")
                mycol.delete_one({'guildid': guildid})

    # Else if the bot see's more guilds than what is present in settings.json we add the missing guilds with default
    # settings
    elif len(dbguilds) < len(botguilds):
        for guildid in botguilds:
            if guildid not in dbguilds:
                guild2add = bot.get_guild(guildid)
                logging.info(f"Guild {guild2add.name} ({guild2add.id}) was added while the bot was offline.  Adding to db.")
                mycol.find_one_and_update({'guildid': guild2add.id},
                                          {'$set': {'guildid': guild2add.id, 'prefix': '?', 'name': guild2add.name}},
                                          upsert=True)


@bot.event
async def on_guild_join(ctx):
    mycol = MYDB['settings']
    mycol.find_one_and_update({'guildid': ctx.id},
                              {'$set': {'guildid': ctx.id, 'prefix': '?', 'name': ctx.name}},
                              upsert=True)


@bot.event
async def on_guild_remove(ctx):
    mycol = MYDB['settings']
    mycol.delete_one({'guildid': ctx.id})


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

    request_url = 'https://cloud.iexapis.com/stable/stock/' + urllib.parse.quote(query) + '/quote?token=' \
                    + STOCKTOKEN

    try:
        data = urllib.request.urlopen(request_url)
        content = data.read().decode('utf-8')
        data = json.loads(content)

        if len(data) == 0:
            embed = discord.Embed(title="No Stock Matches",
                                  timestamp=datetime.datetime.utcnow(),
                                  color=EMBEDCOLOR)

        else:
            symbol = data['symbol']
            company_name = data ['companyName']
            previous_close = data['previousClose']
            latest_price = data['latestPrice']
            change_percentage = f"{data['changePercent'] * 100}%"
            embed_title = f"{company_name} ({symbol})"

            embed = discord.Embed(title=embed_title,
                                  timestamp=datetime.datetime.utcnow(),
                                  color=EMBEDCOLOR)

            embed.add_field(name="Latest Price", value=latest_price)
            embed.add_field(name="Change Percent", value=change_percentage)
            embed.add_field(name="Previous Close", value= previous_close)

    except:
        embed = discord.Embed(title="Issue with stock API",
                              timestamp=datetime.datetime.utcnow(),
                              color=EMBEDCOLOR)

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
    mycol = MYDB['settings']

    if ctx.message.author.id == ctx.guild.owner_id or ctx.message.author.guild_permissions.administrator is True:
        logging.info(ctx.guild.name + ' (' + str(ctx.guild.id) + ') ' + 'changed prefix to ' + prefix)

        mycol.find_one_and_update({'guildid': ctx.guild.id}, {'$set': {'prefix': prefix}})

        embed = discord.Embed(title='Switched prefix to ' + str(prefix), color=EMBEDCOLOR,
                              timestamp=datetime.datetime.utcnow())

    else:
        embed = discord.Embed(title='You are not the guild owner or administrator.', color=EMBEDCOLOR,
                              timestamp=datetime.datetime.utcnow())
    await ctx.channel.send(embed=embed)


@bot.command()
async def register(ctx):
    """This command assigns the message sender to the Players role to be used for online locals."""

    role = discord.utils.get(ctx.guild.roles, name='Players')

    if role:
        if ctx.guild.id == 536237827537764353 or ctx.guild.id == 235423053767639040:
            message = f"Hey {ctx.author.display_name}! Thank you for registering. To complete your registration, " \
                f"please send $6 to gametheorycards@gmail.com via PayPal, Sending to a Friend. In the Notes section " \
                f"of your transaction, please include your full name, FFTCG, and the tournament's date, formatted " \
                f"MM/DD/YY. Once you have paid, please respond in #online-locals-registration with `!paid` and you " \
                f"will be marked as paid."
            await ctx.author.send(message)

        await ctx.message.author.add_roles(role)
        await ctx.message.add_reaction('\U00002705')


    else:
        await ctx.channel.send("```Players Role does not exist in this guild```")


@bot.command()
async def paid(ctx):
    """This command assigns the message sender to the Paid role to be used for online locals."""

    role = discord.utils.get(ctx.guild.roles, name='Paid')
    players_role = discord.utils.get(ctx.guild.roles, name='Players')

    if role:
        if ctx.message.author in players_role.members:
            await ctx.message.author.add_roles(role)
            await ctx.message.add_reaction('\U00002705')
        else:
            await ctx.channel.send("```You have not registered yet```")

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
        await ctx.message.author.remove_roles(role)
        await ctx.message.add_reaction('\U00002705')

    else:
        await ctx.channel.send("```Players Role does not exist in this guild```")


@bot.command()
async def players(ctx):
    """Same as players command, however reads from YAML which contains discord id's for regular name printing"""

    mycol = MYDB['users']
    dbq = mycol.find()
    
    players = {}
    for user in dbq:
        userid = user['userid']
        players[userid] = user['name']

    role = discord.utils.get(ctx.guild.roles, name='Players')
    paid_role = discord.utils.get(ctx.guild.roles, name='Paid')

    if role:
        if role.members:
            message = '```\n'
            for x in role.members:
                if paid_role in x.roles:
                    if str(x.id) in players.keys():
                        message += players[str(x.id)] + " - Paid\n"
                    else:
                        message += x.display_name + " - Paid\n"

                else:
                    if str(x.id) in players.keys():
                        message += players[str(x.id)] + "\n"
                    else:
                        message += x.display_name + "\n"

            message += f'Total: {len(role.members)}```'

        else:
            message = '```Nobody has registered```'

        await ctx.channel.send(message)

    else:
        await ctx.channel.send("```Players Role does not exist in this guild```")


@bot.command()
async def prettyplayers(ctx):
    """Same as players command, however reads from YAML which contains discord id's for regular name printing"""

    mycol = MYDB['users']
    dbq = mycol.find()

    players = {}
    for user in dbq:
        userid = user['userid']
        players[userid] = user['name']

    role = discord.utils.get(ctx.guild.roles, name='Players')

    message = '```\n'

    if role:
        if role.members:
            for x in role.members:
                if str(x.id) in players.keys():
                    message += players[str(x.id)] + "\n"
                else:
                    message += x.display_name + "\n"

            message += f'Total: {len(role.members)}```'

        else:
            message = '```Nobody has registered```'

        await ctx.channel.send(message)

    else:
        await ctx.channel.send("```Players Role does not exist in this guild```")


bot.run(DISCORDTOKEN)
