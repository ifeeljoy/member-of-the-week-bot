import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import sqlite3
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

# Set up the bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# Connect to SQLite database
conn = sqlite3.connect('nominations.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS nominations (
    id INTEGER PRIMARY KEY,
    nominee TEXT NOT NULL,
    nominator TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

# Scheduler
scheduler = AsyncIOScheduler()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} commands')
    except Exception as e:
        print(f'Error syncing commands: {e}')
    scheduler.start()

@bot.tree.command(name="nominate", description="Nominate a user for Member of the Week")
async def nominate(interaction: discord.Interaction, user: discord.User):
    cursor.execute("INSERT INTO nominations (nominee, nominator) VALUES (?, ?)", (user.name, interaction.user.name))
    conn.commit()
    await interaction.response.send_message(f"Successfully nominated {user.name} for Member of the Week!")

@bot.tree.command(name="list_nominations", description="List all nominations for Member of the Week")
async def list_nominations(interaction: discord.Interaction):
    cursor.execute("SELECT nominee, nominator, timestamp FROM nominations")
    nominations = cursor.fetchall()
    if not nominations:
        await interaction.response.send_message("No nominations found.")
        return
    response = "Current Nominations:\n"
    for nominee, nominator, timestamp in nominations:
        response += f"- {nominee} nominated by {nominator} at {timestamp}\n"
    await interaction.response.send_message(response)

@bot.tree.command(name="clear_nominations", description="Clear all nominations (Admin only)")
@commands.has_permissions(administrator=True)
async def clear_nominations(interaction: discord.Interaction):
    cursor.execute("DELETE FROM nominations")
    conn.commit()
    await interaction.response.send_message("All nominations have been cleared.")

# Create Poll
async def create_poll():
    channel = bot.get_channel(CHANNEL_ID)
    cursor.execute("SELECT nominee FROM nominations LIMIT 10")
    nominees = cursor.fetchall()
    if not nominees:
        await channel.send("No nominations found.")
        return

    poll_message = "Vote for Member of the Week:\n"
    emoji_numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']  # Up to 10 emojis
    for index, (nominee,) in enumerate(nominees, start=1):
        poll_message += f"{emoji_numbers[index-1]} {nominee}\n"
    poll_msg = await channel.send(poll_message)
    
    # Add reactions for voting
    for emoji in emoji_numbers[:len(nominees)]:
        await poll_msg.add_reaction(emoji)

# Collect Votes and Announce Winner
async def collect_votes():
    channel = bot.get_channel(CHANNEL_ID)
    messages = [message async for message in channel.history(limit=100)]
    poll_msg = messages[0]  # Assuming the poll message is the most recent

    reactions = poll_msg.reactions
    counts = [reaction.count for reaction in reactions if reaction.emoji in ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟')]
    winner_index = counts.index(max(counts))

    cursor.execute("SELECT nominee FROM nominations LIMIT 10")
    nominees = cursor.fetchall()
    winner = nominees[winner_index][0]
    await channel.send(f"The Member of the Week is: {winner}!")

    # Clear nominations after announcing the winner
    cursor.execute("DELETE FROM nominations")
    conn.commit()

# Manually run poll command
@bot.tree.command(name="runpoll", description="Manually run a poll for Member of the Week")
@commands.has_permissions(administrator=True)
async def runpoll(interaction: discord.Interaction):
    await create_poll()
    await interaction.response.send_message("Poll has been created successfully.")

# Manually end poll command
@bot.tree.command(name="endpoll", description="Manually end the poll and announce the winner")
@commands.has_permissions(administrator=True)
async def endpoll(interaction: discord.Interaction):
    await collect_votes()
    await interaction.response.send_message("Poll has been ended and the winner has been announced.")

# Schedule Jobs
scheduler.add_job(create_poll, 'cron', day_of_week='fri', hour=12)  # Schedule poll creation every Friday at 12 PM
scheduler.add_job(collect_votes, 'cron', day_of_week='mon', hour=12)  # Schedule vote collection every Monday at 12 PM

bot.run(TOKEN)