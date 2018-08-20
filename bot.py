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


async def _fetch(channel, num=1):

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


async def _bought(channel, author, *args):
    joined_args = ' '.join(args)

    try:
        name_of_item = re.findall('.+(?= for)+', joined_args)[0]
        money_string = re.sub('.+ for+ ', '', joined_args)
        money_decimal = convert_money_str_to_decimal(money_string)

    except ValueError:
        await channel.send("I don't understand.\n"
                "Usage: doggo[,] [I] bought <item> for <amount>\n"
                "You can only record between $0.01 and $5000")
    except IndexError:
        await channel.send("I don't understand.\n"
                "Usage: doggo[,] [I] bought <item> for <amount>\n"
                "You can only record between $0.01 and $5000\n"
                "It seems like you didn't specify what you bought.\n")
    else:
        row = [str(datetime.now()),
                'id{}'.format(author.id), name_of_item, str(money_decimal)]

        append(row)
        await channel.send('Ok, recorded that you spent ${} on {}'
                .format(money_decimal, name_of_item))

@bot.event
async def on_message(message):
    if not message.content.lower().startswith('doggo'):
        return

    words = message.content.split()[1:]

    if not words:
        return

    command = words[0]
    arguments = words[1:]

    if 'i' == command.lower():
        if not arguments:
            await message.channel.send('You what?')
        else:
            command = arguments[0]
            arguments = arguments[1:]

    if 'bought' in command.lower():
        await _bought(message.channel, message.author, *arguments)

    elif 'fetch' in command.lower():
        if not arguments:
            await _fetch(message.channel)
        else:
            try:
                await _fetch(message.channel, int(arguments[0]))
            except ValueError:
                await message.channel.send('Doggo is confused.')

    elif command.lower() == 'link':
        spreadsheet_id, _ = read_file('spreadsheet.txt').split()
        await message.channel.send('https://docs.google.com/spreadsheets/d/{}/'.format(spreadsheet_id))
        



def convert_money_str_to_decimal(money_str):
    word = money_str.lstrip('$').rstrip('!,.')
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
