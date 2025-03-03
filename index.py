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
    # Check if the user is trying to nominate themselves
    if user.id == interaction.user.id:
        await interaction.response.send_message("You cannot nominate yourself.")
        return

    # Check if the user has already nominated someone
    cursor.execute("SELECT COUNT(*) FROM nominations WHERE nominator = ?", (interaction.user.name,))
    count = cursor.fetchone()[0]
    if count > 0:
        await interaction.response.send_message("You have already nominated someone.")
        return

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
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have the necessary permissions to use this command.")
        return
    cursor.execute("SELECT COUNT(*) FROM nominations")
    count = cursor.fetchone()[0]
    if count == 0:
        await interaction.response.send_message("No nominations to clear.")
        return
    cursor.execute("DELETE FROM nominations")
    conn.commit()
    await interaction.response.send_message("All nominations have been cleared.")

# Create Poll
async def create_poll():
    channel = bot.get_channel(CHANNEL_ID)
    cursor.execute("SELECT nominee, COUNT(nominee) as count FROM nominations GROUP BY nominee ORDER BY count DESC LIMIT 10")
    nominees = cursor.fetchall()
    if not nominees:
        await channel.send("No nominations found.")
        return

    poll_message = "Vote for Member of the Week:\n"
    emoji_numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']  # Up to 10 emojis
    for index, (nominee, count) in enumerate(nominees, start=1):
        poll_message += f"{emoji_numbers[index-1]} {nominee} ({count} nominations)\n"
    poll_msg = await channel.send(poll_message)
    
    # Add reactions for voting
    for emoji in emoji_numbers[:len(nominees)]:
        await poll_msg.add_reaction(emoji)

# Collect Votes and Announce Winner
async def collect_votes():
    channel = bot.get_channel(CHANNEL_ID)
    async for message in channel.history(limit=1):
        if message.author != bot.user or "Vote for Member of the Week" not in message.content:
            await channel.send("No poll found.")
            return
        poll_msg = message

    reactions = poll_msg.reactions
    counts = [reaction.count - 1 for reaction in reactions if reaction.emoji in ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟')]  # Subtract 1 to exclude the bot's own reaction
    if not counts:
        await channel.send("No votes found.")
        return

    max_votes = max(counts)
    winners = [i for i, count in enumerate(counts) if count == max_votes]

    cursor.execute("SELECT nominee FROM nominations GROUP BY nominee ORDER BY COUNT(nominee) DESC LIMIT 10")
    nominees = cursor.fetchall()

    if len(winners) > 1:
        tie_message = "There's a tie! The nominees with the highest votes are:\n"
        tie_message += "\n".join([f"{nominees[i][0]}" for i in winners])
        await channel.send(tie_message)
    else:
        winner_index = winners[0]
        winner = nominees[winner_index][0]
        await channel.send(f"The Member of the Week is: {winner}!")

    # Clear nominations after announcing the winner or tie
    cursor.execute("DELETE FROM nominations")
    conn.commit()

# Manually run poll command
@bot.tree.command(name="runpoll", description="Manually run a poll for Member of the Week")
@commands.has_permissions(administrator=True)
async def runpoll(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have the necessary permissions to use this command.")
        return

    # Check for existing nominations
    cursor.execute("SELECT COUNT(*) FROM nominations")
    count = cursor.fetchone()[0]
    if count == 0:
        await interaction.response.send_message("No nominations found to create a poll.")
        return

    # Check if there is already a poll running
    channel = bot.get_channel(CHANNEL_ID)
    async for message in channel.history(limit=1):
        if message.author == bot.user and "Vote for Member of the Week" in message.content:
            await interaction.response.send_message("A poll is already running.")
            return

    await create_poll()
    await interaction.response.send_message("Poll has been created successfully.")

# Manually end poll command
@bot.tree.command(name="endpoll", description="Manually end the poll and announce the winner")
@commands.has_permissions(administrator=True)
async def endpoll(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have the necessary permissions to use this command.")
        return

    channel = bot.get_channel(CHANNEL_ID)
    async for message in channel.history(limit=1):
        if message.author != bot.user or "Vote for Member of the Week" not in message.content:
            await interaction.response.send_message("No poll found to end.")
            return

    await collect_votes()
    await interaction.response.send_message("Poll has been ended and the winner has been announced.")

# Schedule Jobs
scheduler.add_job(create_poll, 'cron', day_of_week='fri', hour=12)  # Schedule poll creation every Friday at 12 PM
scheduler.add_job(collect_votes, 'cron', day_of_week='mon', hour=12)  # Schedule vote collection every Monday at 12 PM

bot.run(TOKEN)