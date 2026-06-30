import discord
from discord.ext import commands
from discord import app_commands
import random

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="random", description="Generate a random number")
    async def random_num(self, interaction: discord.Interaction, minimum: int, maximum: int):
        if minimum > maximum:
            return await interaction.response.send_message("❌ Minimum cannot be bigger than maximum.", ephemeral=True)
        await interaction.response.send_message(f"🎲 `{random.randint(minimum, maximum)}`")

    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip(self, interaction: discord.Interaction):
        await interaction.response.send_message(random.choice(["Heads 🪙", "Tails 🪙"]))

    @app_commands.command(name="dice", description="Roll a dice")
    async def dice(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🎲 You rolled **{random.randint(1, 6)}**")

    @app_commands.command(name="eightball", description="Ask the magic 8ball")
    async def eightball(self, interaction: discord.Interaction, question: str):
        answers = ["Yes 👍", "No 👎", "Maybe 🤔", "Definitely 🔥", "Ask again later ⏳", "Not likely ❌"]
        await interaction.response.send_message(f"🎱 **Question:** {question}\n👉 **Answer:** {random.choice(answers)}")

    @app_commands.command(name="joke", description="Get a random joke")
    async def joke(self, interaction: discord.Interaction):
        jokes = [
            "Why do programmers hate nature? Too many bugs 🐛",
            "My code works… I just don’t know why 😂",
            "Discord bots don’t sleep — they just timeout 💀"
        ]
        await interaction.response.send_message(random.choice(jokes))

    @app_commands.command(name="say", description="Make the bot say something")
    async def say(self, interaction: discord.Interaction, message: str):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Administrator only.", ephemeral=True)
        await interaction.channel.send(message)
        await interaction.response.send_message("✅ Sent.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Fun(bot))
