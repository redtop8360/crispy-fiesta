import discord
from discord.ext import commands
from discord import app_commands


class Socials(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="youtube",
        description="Get Redtop's YouTube channel."
    )
    async def youtube(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📺 Redtop's YouTube",
            description="Subscribe to my YouTube channel!",
            color=discord.Color.red()
        )

        embed.add_field(
            name="🔗 Channel",
            value="https://youtube.com/@BigBoyNimtiz",
            inline=False
        )

        embed.set_footer(text="Thanks for the support!")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="twitch",
        description="Get Redtop's Twitch channel."
    )
    async def twitch(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🟣 Redtop's Twitch",
            description="Come watch me live!",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="🔗 Stream",
            value="https://twitch.tv/redtop83602",
            inline=False
        )

        embed.set_footer(text="Hope to see you in chat!")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Socials(bot))
