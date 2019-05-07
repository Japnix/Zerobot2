import discord
from discord.ext import commands
import random
import sys

mytoken = sys.argv[1]

description = '''An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here.'''
bot = commands.Bot(command_prefix='z?', description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def announcement(ctx, *, announcement):

   channel = None

   for x in ctx.guild._channels:
       if bot.get_channel(x).name == 'announcement':
           channel = bot.get_channel(x)

   if channel is None:
       await ctx.channel.send('There is no #announcement channel in this guild')


   await channel.send(ctx.author.mention + ': ' + announcement)


bot.run(mytoken)