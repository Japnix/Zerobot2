import discord
from discord.ext import commands
import urllib.request
import urllib.parse
import json
import datetime
import sys
import random
import os


async def get_pre(bot, message):
    with open(os.path.dirname(__file__) + "/settings.json", 'r') as x:
        myfile = json.loads(x.read())

    return myfile[str(message.guild.id)]['prefix']

discordtoken = sys.argv[1]
stocktoken = sys.argv[2]
embedcolor = 0xed330e
settingsjson = os.path.dirname(__file__) + "/settings.json"

description = '''An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here.'''
bot = commands.Bot(command_prefix=get_pre, description=description)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    if os.path.isfile(os.path.dirname(__file__) + "/settings.json"):
        print('settings.json is here')
        with open(os.path.dirname(__file__) + "/settings.json", 'r') as myfile:
            myfile = json.loads(myfile.read())

    else:
        print('creating settings.json')
        myfile = open(os.path.dirname(__file__) + '/settings.json', 'w+')
        myjson = {}
        for x in bot.guilds:
            myjson[str(x.id)] = {'prefix': '!'}

        json.dump(myjson, myfile)
        myfile.close(myjson, myfile)

@bot.event
async def on_guild_join(ctx):
    with open(settingsjson, 'r') as myfile:
        myjson = json.load(myfile)

    myjson[str(ctx.id)] = {'prefix': '!'}

    with open(settingsjson, 'w+') as myfile:
        json.dump(myjson, myfile)


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
    with open(settingsjson, 'r') as myfile:
        myjson = json.load(myfile)

    if ctx.message.author.id == ctx.guild.owner.id:
        myjson[str(ctx.guild.id)]['prefix'] = prefix

        with open(settingsjson, 'w+') as myfile:
            json.dump(myjson, myfile)

    else:
        await ctx.channel.send('You are not the guild owner')


bot.run(discordtoken)