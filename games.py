import discord
from discord.ext import commands
from discord import app_commands
import random

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rps", description="Play rock paper scissors")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Rock", value="rock"),
        app_commands.Choice(name="Paper", value="paper"),
        app_commands.Choice(name="Scissors", value="scissors"),
    ])
    async def rps(self, interaction: discord.Interaction, choice: app_commands.Choice[str]):
        user = choice.value
        bot_choice = random.choice(["rock", "paper", "scissors"])

        if user == bot_choice:
            result = "It's a tie!"
        elif (user == "rock" and bot_choice == "scissors") or (user == "paper" and bot_choice == "rock") or (user == "scissors" and bot_choice == "paper"):
            result = "You win!"
        else:
            result = "I win!"

        await interaction.response.send_message(f"🎮 You chose **{user}**\nI chose **{bot_choice}**\n🏆 {result}")

    @app_commands.command(name="guess", description="Guess a number from 1 to 10")
    async def guess(self, interaction: discord.Interaction, number: int):
        if number < 1 or number > 10:
            return await interaction.response.send_message("❌ Pick 1-10.", ephemeral=True)
        winning = random.randint(1, 10)
        if number == winning:
            await interaction.response.send_message(f"🎯 Correct! It was **{winning}**.")
        else:
            await interaction.response.send_message(f"❌ Wrong. It was **{winning}**.")

    @app_commands.command(name="slots", description="Play slots")
    async def slots(self, interaction: discord.Interaction):
        symbols = ["🍒", "🍋", "🍇", "⭐", "💎"]
        roll = [random.choice(symbols) for _ in range(3)]
        if roll[0] == roll[1] == roll[2]:
            result = "JACKPOT! 🎉"
        elif len(set(roll)) == 2:
            result = "Small win! ✨"
        else:
            result = "No win."
        await interaction.response.send_message(f"🎰 {' | '.join(roll)}\n{result}")

async def setup(bot):
    await bot.add_cog(Games(bot))
