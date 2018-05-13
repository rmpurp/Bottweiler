import discord
from discord.ext import commands
from collections import deque
import sqlite3 as sql

AUTH_FILE = "auth.txt"
DATABASE_FILE = "data.db"

bot = commands.Bot(command_prefix='doggo, ', description='A very good doggo')
db = sql.Connection(DATABASE_FILE)

def create_table():
    db.execute("create table if not exists messages(m_id UNIQUE, c_id, author, time, text);")  
    db.commit()

def read_file(filename):
    with open(filename) as f:
        return f.read().strip()

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def fetch(ctx, num=1):
    channel = ctx.message.channel

    if num < 1:
        await channel.send("Doggo is confused")
        return
    if num > 5:
        await channel.send("Doggo gets too tired fetching that much")
        return

    query = 'select author, text from messages where c_id = ? order by time desc limit ?'
    res = db.execute(query, (channel.id, num)).fetchall()
    if not res[0][0]:
        await channel.send("Could not find anything.")
    else:
        to_send = []
        for message in res[::-1]:
            author, text = message[0: 2]
            to_send.append("{}: {}".format(author, text))
        await channel.send('\n\n'.join(to_send))

@bot.command()
async def add(ctx, i=1):
    await ctx.message.channel.send(str(i))

@bot.event
async def on_message_edit(before, after):
    channel = before.channel
    probe = db.execute("select text from messages where m_id = ?", (before.id,))
    if not probe.fetchall():
        db.execute("insert into messages values (?, ?, ?, ?, ?)", (
            before.id,
            channel.id,
            before.author.display_name,
            before.created_at.timestamp(), 
            before.content + " \n--> " + after.content))
    else:
        db.execute("update messages set text = text || ? where m_id = ?", 
                (" \n--> " + after.content, before.id))
    db.commit()

create_table()

bot.run(read_file(AUTH_FILE))
