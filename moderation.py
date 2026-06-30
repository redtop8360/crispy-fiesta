import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "bot_data.db")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS cases (
    case_id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL
)
""")
conn.commit()

def add_case(guild_id: int, user_id: int, mod_id: int, action: str, reason: str):
    c.execute("INSERT INTO cases (guild_id, user_id, moderator_id, action, reason) VALUES (?, ?, ?, ?, ?)", (guild_id, user_id, mod_id, action, reason))
    conn.commit()
    return c.lastrowid

def get_case(case_id: int):
    c.execute("SELECT case_id, guild_id, user_id, moderator_id, action, reason FROM cases WHERE case_id = ?", (case_id,))
    return c.fetchone()

def get_user_cases(user_id: int):
    c.execute("SELECT case_id, action, reason, moderator_id FROM cases WHERE user_id = ? ORDER BY case_id DESC LIMIT 15", (user_id,))
    return c.fetchall()

def can_manage(interaction: discord.Interaction, member: discord.Member):
    bot_member = interaction.guild.me
    if member == interaction.user:
        return False, "You cannot moderate yourself."
    if member == bot_member:
        return False, "I cannot moderate myself."
    if member.top_role >= interaction.user.top_role and interaction.guild.owner_id != interaction.user.id:
        return False, "That user has a role equal to or higher than yours."
    if member.top_role >= bot_member.top_role:
        return False, "That user has a role equal to or higher than my bot role."
    return True, None

async def safe_dm(member: discord.Member, msg: str):
    try:
        await member.send(msg)
    except Exception:
        pass

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="warn", description="Warn a user and create a case")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ Missing permission: Moderate Members", ephemeral=True)
        allowed, msg = can_manage(interaction, member)
        if not allowed:
            return await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        case_id = add_case(interaction.guild.id, member.id, interaction.user.id, "WARN", reason)
        await safe_dm(member, f"⚠️ You were warned in **{interaction.guild.name}**\nCase #{case_id}\nReason: {reason}")
        embed = discord.Embed(title=f"Case #{case_id} - Warn", color=discord.Color.red())
        embed.add_field(name="User", value=member.mention, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warnings", description="View user cases")
    async def warnings_cmd(self, interaction: discord.Interaction, member: discord.Member):
        rows = get_user_cases(member.id)
        if not rows:
            return await interaction.response.send_message(f"✅ {member.mention} has no cases.")
        text = "\n".join([f"**Case #{case_id}** — {action}: {reason}" for case_id, action, reason, mod_id in rows])
        embed = discord.Embed(title=f"Cases for {member}", description=text, color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="case", description="View a case by number")
    async def case_view(self, interaction: discord.Interaction, case_id: int):
        row = get_case(case_id)
        if not row:
            return await interaction.response.send_message("❌ Case not found.", ephemeral=True)
        case_id, guild_id, user_id, mod_id, action, reason = row
        embed = discord.Embed(title=f"Case #{case_id}", color=discord.Color.red())
        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="User", value=f"<@{user_id}>", inline=True)
        embed.add_field(name="Moderator", value=f"<@{mod_id}>", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unwarn", description="Remove a case by number")
    async def unwarn(self, interaction: discord.Interaction, case_id: int):
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ Missing permission: Moderate Members", ephemeral=True)
        if not get_case(case_id):
            return await interaction.response.send_message("❌ Case not found.", ephemeral=True)
        c.execute("DELETE FROM cases WHERE case_id = ?", (case_id,))
        conn.commit()
        await interaction.response.send_message(f"🧹 Removed Case #{case_id}.")

    @app_commands.command(name="mute", description="Timeout a user")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str):
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ Missing permission: Moderate Members", ephemeral=True)
        if not interaction.guild.me.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ Bot missing permission: Moderate Members", ephemeral=True)
        allowed, msg = can_manage(interaction, member)
        if not allowed:
            return await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        case_id = add_case(interaction.guild.id, member.id, interaction.user.id, "MUTE", reason)
        try:
            await member.timeout(timedelta(minutes=minutes), reason=reason)
        except discord.Forbidden:
            return await interaction.response.send_message("❌ I cannot mute that user. Check my role position.", ephemeral=True)
        await safe_dm(member, f"🔇 You were muted in **{interaction.guild.name}**\nCase #{case_id}\nDuration: {minutes} minutes\nReason: {reason}")
        await interaction.response.send_message(f"🔇 Case #{case_id} - Muted {member.mention} for {minutes} minutes.")

    @app_commands.command(name="unmute", description="Remove timeout")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ Missing permission: Moderate Members", ephemeral=True)
        case_id = add_case(interaction.guild.id, member.id, interaction.user.id, "UNMUTE", "Manual unmute")
        try:
            await member.timeout(None)
        except discord.Forbidden:
            return await interaction.response.send_message("❌ I cannot unmute that user. Check my role position.", ephemeral=True)
        await interaction.response.send_message(f"🔊 Case #{case_id} - Unmuted {member.mention}")

    @app_commands.command(name="kick", description="Kick a user")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        if not interaction.user.guild_permissions.kick_members:
            return await interaction.response.send_message("❌ Missing permission: Kick Members", ephemeral=True)
        if not interaction.guild.me.guild_permissions.kick_members:
            return await interaction.response.send_message("❌ Bot missing permission: Kick Members", ephemeral=True)
        allowed, msg = can_manage(interaction, member)
        if not allowed:
            return await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        case_id = add_case(interaction.guild.id, member.id, interaction.user.id, "KICK", reason)
        await safe_dm(member, f"👢 You were kicked from **{interaction.guild.name}**\nCase #{case_id}\nReason: {reason}")
        try:
            await member.kick(reason=reason)
        except discord.Forbidden:
            return await interaction.response.send_message("❌ I cannot kick that user. Check my role position.", ephemeral=True)
        await interaction.response.send_message(f"👢 Case #{case_id} - Kicked {member}")

    @app_commands.command(name="ban", description="Ban a user")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message("❌ Missing permission: Ban Members", ephemeral=True)
        if not interaction.guild.me.guild_permissions.ban_members:
            return await interaction.response.send_message("❌ Bot missing permission: Ban Members", ephemeral=True)
        allowed, msg = can_manage(interaction, member)
        if not allowed:
            return await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        case_id = add_case(interaction.guild.id, member.id, interaction.user.id, "BAN", reason)
        await safe_dm(member, f"🔨 You were banned from **{interaction.guild.name}**\nCase #{case_id}\nReason: {reason}")
        try:
            await member.ban(reason=reason)
        except discord.Forbidden:
            return await interaction.response.send_message("❌ I cannot ban that user. Check my role position.", ephemeral=True)
        await interaction.response.send_message(f"🔨 Case #{case_id} - Banned {member}")

    @app_commands.command(name="clear", description="Delete messages")
    async def clear(self, interaction: discord.Interaction, amount: int):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ Missing permission: Manage Messages", ephemeral=True)
        if not interaction.guild.me.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ Bot missing permission: Manage Messages", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
