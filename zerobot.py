import discord
from discord.ext import commands
import urllib.request
import urllib.parse
import json
import datetime
import sys
import random


discordtoken = sys.argv[1]
stocktoken = sys.argv[2]
embedcolor = 0xed330e

description = '''An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here.'''
bot = commands.Bot(command_prefix='!', description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


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

    await ctx.channel.send(msg)


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


bot.run(discordtoken)