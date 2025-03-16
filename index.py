import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import sqlite3
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
USER_ID = int(os.getenv('DISCORD_USER_ID'))

intents = discord.Intents.default()

class MemberOfTheWeekBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scheduler = AsyncIOScheduler()

    async def setup_hook(self) -> None:
        self.scheduler.add_job(create_poll, 'cron', day_of_week='fri', hour=0)  # Schedule poll creation every Friday at 12 AM UTC
        self.scheduler.add_job(collect_votes, 'cron', day_of_week='sun', hour=12)  # Schedule vote collection every Sunday at 12 PM UTC
        self.scheduler.start()

bot = MemberOfTheWeekBot(command_prefix='/', intents=intents)

conn = sqlite3.connect('nominations.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS nominations (
    id INTEGER PRIMARY KEY,
    nominee_id BIGINT NOT NULL,
    nominator_id BIGINT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.tree.command(description="Nominate a user for Member of the Week")
async def nominate(interaction: discord.Interaction, user: discord.User):
    if user.id == interaction.user.id:
        await interaction.response.send_message("You cannot nominate yourself.")
        return

    cursor.execute("SELECT COUNT(*) FROM nominations WHERE nominator_id = ?", (interaction.user.id,))
    count = cursor.fetchone()[0]
    if count > 0:
        await interaction.response.send_message("You have already nominated someone.")
        return

    cursor.execute("INSERT INTO nominations (nominee_id, nominator_id) VALUES (?, ?)", (user.id, interaction.user.id))
    conn.commit()
    await interaction.response.send_message(f"Successfully nominated {user.mention} for Member of the Week!")

@bot.tree.command(description="List all nominations for Member of the Week")
async def list_nominations(interaction: discord.Interaction):
    cursor.execute("SELECT nominee_id, nominator_id, timestamp FROM nominations")
    nominations = cursor.fetchall()
    if not nominations:
        await interaction.response.send_message("No nominations found.")
        return

    embed = discord.Embed(title="Current Nominations", color=discord.Color.blue())
    for nominee_id, nominator_id, timestamp in nominations:
        nominee = await bot.fetch_user(nominee_id)
        nominator = await bot.fetch_user(nominator_id)
        embed.add_field(name=f"{nominee.mention}", value=f"Nominated by {nominator.mention} at {timestamp}", inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(description="Clear all nominations (Admin only)")
@app_commands.default_permissions(administrator=True)
async def clear_nominations(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have the necessary permissions to use this command.")
        return
    cursor.execute("DELETE FROM nominations")
    conn.commit()
    await interaction.response.send_message("All nominations have been cleared.")

@bot.tree.command(description="Manually start a Member of the Week poll (Admin only)")
@app_commands.default_permissions(administrator=True)
async def runpoll(interaction: discord.Interaction):
    await interaction.response.defer()
    await create_poll()
    await interaction.followup.send("Poll has been manually started.")

@bot.tree.command(description="Manually end the poll and collect votes (Admin only)")
@app_commands.default_permissions(administrator=True)
async def endpoll(interaction: discord.Interaction):
    await interaction.response.defer()
    await collect_votes()
    await interaction.followup.send("Poll has been manually ended and votes collected.")
    
@bot.event
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You do not have the necessary permissions to use this command.")
    elif isinstance(error, app_commands.CommandInvokeError) and "no nominations found" in str(error).lower():
        await interaction.response.send_message("No nominations found.")
    else:
        await interaction.response.send_message("An error occurred.")

async def create_poll():
    channel = bot.get_channel(CHANNEL_ID)
    cursor.execute("SELECT nominee_id, COUNT(nominee_id) as count FROM nominations GROUP BY nominee_id ORDER BY count DESC LIMIT 10")
    nominees = cursor.fetchall()
    if not nominees:
        await channel.send("No nominations found.")
        return

    poll_message = "Vote for Member of the Week:\n"
    emoji_numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    for index, (nominee_id, count) in enumerate(nominees, start=1):
        nominee = await bot.fetch_user(nominee_id)
        poll_message += f"{emoji_numbers[index-1]} {nominee.mention} ({count} nominations)\n"
    poll_msg = await channel.send(poll_message)

    for emoji in emoji_numbers[:len(nominees)]:
        await poll_msg.add_reaction(emoji)

async def collect_votes():
    channel = bot.get_channel(CHANNEL_ID)
    poll_msg = None
    async for message in channel.history(limit=5):
        if message.author == bot.user and "Vote for Member of the Week" in message.content:
            time_diff = discord.utils.utcnow() - message.created_at
            if time_diff.total_seconds() < 259200:
                poll_msg = message
                break
    if not poll_msg:
        await channel.send("No poll found.")
        return

    reactions = poll_msg.reactions
    counts = [reaction.count - 1 for reaction in reactions if reaction.emoji in ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟')]
    if not counts:
        await channel.send("No votes found.")
        return

    max_votes = max(counts)
    winners = [i for i, count in enumerate(counts) if count == max_votes]

    cursor.execute("SELECT nominee_id FROM nominations GROUP BY nominee_id ORDER BY COUNT(nominee_id) DESC LIMIT 10")
    nominees = cursor.fetchall()

    if len(winners) > 1:
        tie_message = "There's a tie! The **winners** are:\n"
        tie_message += "\n".join([f"{(await bot.fetch_user(nominees[i][0])).mention}" for i in winners])
        await channel.send(tie_message)
    else:
        winner_index = winners[0]
        winner = await bot.fetch_user(nominees[winner_index][0])
        await channel.send(f"The Member of the Week is: {winner.mention}!")

    cursor.execute("DELETE FROM nominations")
    conn.commit()

bot.run(TOKEN)