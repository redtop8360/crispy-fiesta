import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "bot_data.db")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS levels (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER NOT NULL,
    level INTEGER NOT NULL
)
""")
conn.commit()

def get_level(user_id: int):
    c.execute("SELECT xp, level FROM levels WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row is None:
        c.execute("INSERT INTO levels (user_id, xp, level) VALUES (?, ?, ?)", (user_id, 0, 1))
        conn.commit()
        return 0, 1
    return row

def add_xp(user_id: int, amount: int = 5):
    xp, level = get_level(user_id)
    xp += amount
    leveled = False
    if xp >= level * 100:
        xp = 0
        level += 1
        leveled = True
    c.execute("UPDATE levels SET xp = ?, level = ? WHERE user_id = ?", (xp, level, user_id))
    conn.commit()
    return xp, level, leveled

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        xp, level, leveled = add_xp(message.author.id, 5)
        if leveled:
            await message.channel.send(f"🎉 {message.author.mention} reached **Level {level}**!")

    @app_commands.command(name="rank", description="Check level and XP")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        xp, level = get_level(member.id)
        embed = discord.Embed(title=f"Rank for {member}", color=discord.Color.gold())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{xp}/{level * 100}", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Show top 10 users")
    async def leaderboard(self, interaction: discord.Interaction):
        c.execute("SELECT user_id, xp, level FROM levels ORDER BY level DESC, xp DESC LIMIT 10")
        rows = c.fetchall()
        if not rows:
            return await interaction.response.send_message("No leaderboard data yet.")
        text = "\n".join([f"**{idx}.** <@{uid}> — Level {level} ({xp} XP)" for idx, (uid, xp, level) in enumerate(rows, 1)])
        embed = discord.Embed(title="🏆 Leaderboard", description=text, color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
