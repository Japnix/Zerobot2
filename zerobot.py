import discord
from discord.ext import commands
import urllib.request
import json
import datetime
import sys

discordtoken = sys.argv[1]
stocktoken = sys.argv[2]

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
        await ctx.channel.send('There is no text channel #announcements in this guild')
    else:
        await channel.send(ctx.author.display_name + ': ' + msg)


@bot.command()
async def stock(ctx, *, query):
    request_url = 'https://cloud.iexapis.com/stable/tops/last?token=' + stocktoken + '&symbols=' + query
    embed = discord.Embed(title='Stock Queries',
                          timestamp=datetime.datetime.utcnow())

    try:
        data = urllib.request.urlopen(request_url)
        content = data.read().decode('utf-8')
        data = json.loads(content)

        if len(data) == 0:
            await ctx.channel.send(embed=discord.Embed(title="No Stock Matches", timestamp=datetime.datetime.utcnow()))
        elif len(data) == 1:
            embed.add_field(name=data[0]['symbol'], value=data[0]['price'])
            await ctx.channel.send(embed=embed)
        else:
            for tickers in data:
                embed.add_field(name=tickers['symbol'], value=tickers['price'])
            await ctx.channel.send(embed=embed)
    except:
        return

bot.run(discordtoken)