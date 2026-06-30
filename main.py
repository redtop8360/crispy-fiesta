import discord
from discord.ext import commands
import os

os.makedirs("data", exist_ok=True)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class RedtopBot(commands.Bot):
    async def setup_hook(self):
        cogs = [
            "cogs.basic",
            "cogs.fun",
            "cogs.games",
            "cogs.leveling",
            "cogs.moderation",
            "cogs.tickets",
            "cogs.socials",
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")

        synced = await self.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")

bot = RedtopBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="King Redtops server 👀"
        ),
        status=discord.Status.online
    )
    print(f"🤖 Logged in as {bot.user}")

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("❌ TOKEN missing.")
    print('PowerShell: $env:TOKEN="YOUR_BOT_TOKEN"')
else:
    bot.run(TOKEN)
