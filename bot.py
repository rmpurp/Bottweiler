import discord
from discord.ext import commands
import sqlite3 as sql
from decimal import Decimal, InvalidOperation
import re
from sheets_append import append
from datetime import datetime

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
    if not res or not res[0][0]:
        await channel.send("Could not find anything.")
    else:
        to_send = []
        for message in res[::-1]:
            author, text = message[0: 2]
            to_send.append("{}: {}".format(author, text))
        await channel.send('\n\n'.join(to_send))

@bot.command()
async def I(ctx, *args):
    if len(args) < 2:
        await ctx.message.channel.send('Woof?')
    else:
        await _bought(ctx, *args[1:])

@bot.command()
async def bought(ctx, *args):
    await _bought(ctx, *args)
    
def last_index(condition, itr):
    '''Return last index that satifies condition, else raise ValueError'''
    return max(loc for loc, val in enumerate(itr) if condition(itr))


async def _bought(ctx, *args):
    joined_args = ' '.join(args)

    try:
        name_of_item = re.findall('.+(?= for)+', joined_args)[0]
        money_string = re.sub('.+ for+ ', '', joined_args)
        money_decimal = convert_money_str_to_decimal(money_string)

    except ValueError:
        await ctx.message.channel.send("I don't understand.\n"
                "Usage: doggo, [I] bought <item> for <amount>\n"
                "You can only record between $0.01 and $5000")
    except IndexError:
        await ctx.message.channel.send("I don't understand.\n"
                "Usage: doggo, [I] bought <item> for <amount>\n"
                "You can only record between $0.01 and $5000\n"
                "It seems like you didn't specify what you bought.\n")
    else:
        row = [str(datetime.now()),
                'id{}'.format(ctx.author.id), name_of_item, str(money_decimal)]

        append(row)
        await ctx.message.channel.send('Ok, recorded that you spent ${} on {}'
                .format(money_decimal, name_of_item))



    

def convert_money_str_to_decimal(money_str):
    word = money_str.strip('$!,.')
    try:
        d = Decimal(word).quantize(Decimal('0.01'))
        if not 0.01 <= d <= 5000:
            raise ValueError
        return d
    except InvalidOperation:
        raise ValueError




@bot.event
async def on_message_edit(before, after):
    if before.content == after.content:
        return
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
