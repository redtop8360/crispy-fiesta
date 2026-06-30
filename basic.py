import discord
from discord.ext import commands
from discord import app_commands

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🏓 Pong! `{round(self.bot.latency * 1000)}ms`")

    @app_commands.command(name="hello", description="Say hello")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"👋 Hello {interaction.user.mention}")

    @app_commands.command(name="userinfo", description="Show user info")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        created = int(member.created_at.timestamp())
        joined = int(member.joined_at.timestamp()) if member.joined_at else None

        embed = discord.Embed(title="User Info", color=discord.Color.blurple())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=str(member.id), inline=False)
        embed.add_field(name="Name", value=str(member), inline=False)
        embed.add_field(name="Nickname", value=member.nick if member.nick else "None", inline=False)
        embed.add_field(name="Joined Discord", value=f"<t:{created}:F> (<t:{created}:R>)", inline=False)
        if joined:
            embed.add_field(name="Joined Server", value=f"<t:{joined}:F> (<t:{joined}:R>)", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Show server info")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title="Server Info", color=discord.Color.green())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Server", value=guild.name, inline=True)
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Owner", value=str(guild.owner), inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Basic(bot))
