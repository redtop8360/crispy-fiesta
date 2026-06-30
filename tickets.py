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
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    ticket_type TEXT NOT NULL,
    status TEXT NOT NULL
)
""")
conn.commit()

CATEGORY_IDS = {
    "general": 1396485421025988671,
    "ownership": 1396485421025988672,
    "mgt": 1396485421025988673,
}

TICKET_NAMES = {
    "general": "General Support",
    "ownership": "Ownership Team",
    "mgt": "MGT",
}


class TicketDropdown(discord.ui.Select):
    def __init__(self, cog):
        self.cog = cog

        options = [
            discord.SelectOption(
                label="General Support",
                value="general",
                description="Open a general support ticket",
                emoji="📩"
            ),
            discord.SelectOption(
                label="Ownership Team",
                value="ownership",
                description="Contact ownership",
                emoji="👑"
            ),
            discord.SelectOption(
                label="MGT",
                value="mgt",
                description="Contact management",
                emoji="🛡️"
            ),
        ]

        super().__init__(
            placeholder="Select a ticket type...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await self.cog.create_ticket(interaction, self.values[0], "Created from panel")


class TicketPanel(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown(cog))


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_category(self, guild: discord.Guild, ticket_type: str):
        category = guild.get_channel(CATEGORY_IDS[ticket_type])

        if category is None:
            raise Exception("Category not found")

        return category

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str, reason: str):
        guild = interaction.guild
        user = interaction.user
        ticket_name = TICKET_NAMES[ticket_type]

        try:
            category = await self.get_category(guild, ticket_type)
        except Exception:
            return await interaction.response.send_message(
                "❌ Ticket category not found. Check your category IDs.",
                ephemeral=True
            )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True
            )
        }

        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )

        channel_name = f"{ticket_type}-{user.name}".lower().replace(" ", "-")[:90]

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"{ticket_name} ticket created by {user}"
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ I need Manage Channels permission.",
                ephemeral=True
            )

        c.execute(
            "INSERT INTO tickets (guild_id, user_id, channel_id, ticket_type, status) VALUES (?, ?, ?, ?, ?)",
            (guild.id, user.id, channel.id, ticket_name, "open")
        )
        conn.commit()

        ticket_id = c.lastrowid

        embed = discord.Embed(
            title=f"🎟️ {ticket_name} Ticket #{ticket_id}",
            description=(
                f"**Created By:** {user.mention}\n"
                f"**Type:** {ticket_name}\n"
                f"**Reason:** {reason}\n\n"
                f"Staff will assist you soon.\n"
                f"Use `/close_ticket` to close this ticket."
            ),
            color=discord.Color.blue()
        )

        await channel.send(content=user.mention, embed=embed)

        await interaction.response.send_message(
            f"✅ Your **{ticket_name}** ticket was created: {channel.mention}",
            ephemeral=True
        )

    @app_commands.command(name="ticket_panel", description="Send the ticket panel")
    async def ticket_panel(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ Administrator only.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="🎟️ Support Ticket Panel",
            description=(
                "Select a ticket type below.\n\n"
                "📩 **General Support**\n"
                "👑 **Ownership Team**\n"
                "🛡️ **MGT**"
            ),
            color=discord.Color.blue()
        )

        await interaction.channel.send(embed=embed, view=TicketPanel(self))
        await interaction.response.send_message("✅ Ticket panel sent.", ephemeral=True)

    @app_commands.command(name="ticket", description="Create a support ticket")
    @app_commands.choices(ticket_type=[
        app_commands.Choice(name="General Support", value="general"),
        app_commands.Choice(name="Ownership Team", value="ownership"),
        app_commands.Choice(name="MGT", value="mgt"),
    ])
    async def ticket(
        self,
        interaction: discord.Interaction,
        ticket_type: app_commands.Choice[str],
        reason: str = "No reason provided"
    ):
        await self.create_ticket(interaction, ticket_type.value, reason)

    @app_commands.command(name="close_ticket", description="Close the current ticket")
    async def close_ticket(self, interaction: discord.Interaction):
        c.execute(
            "SELECT ticket_id, user_id, status FROM tickets WHERE channel_id = ? ORDER BY ticket_id DESC LIMIT 1",
            (interaction.channel.id,)
        )
        row = c.fetchone()

        if not row:
            return await interaction.response.send_message(
                "❌ This is not a ticket channel.",
                ephemeral=True
            )

        ticket_id, user_id, status = row

        is_owner = interaction.user.id == user_id
        is_staff = (
            interaction.user.guild_permissions.manage_channels
            or interaction.user.guild_permissions.administrator
        )

        if not is_owner and not is_staff:
            return await interaction.response.send_message(
                "❌ You cannot close this ticket.",
                ephemeral=True
            )

        c.execute(
            "UPDATE tickets SET status = ? WHERE ticket_id = ?",
            ("closed", ticket_id)
        )
        conn.commit()

        await interaction.response.send_message("🔒 Closing ticket...")
        await interaction.channel.delete(reason=f"Ticket #{ticket_id} closed")

    @app_commands.command(name="ticket_info", description="Show ticket info")
    async def ticket_info(self, interaction: discord.Interaction):
        c.execute(
            "SELECT ticket_id, user_id, ticket_type, status FROM tickets WHERE channel_id = ? ORDER BY ticket_id DESC LIMIT 1",
            (interaction.channel.id,)
        )
        row = c.fetchone()

        if not row:
            return await interaction.response.send_message(
                "❌ This is not a ticket channel.",
                ephemeral=True
            )

        ticket_id, user_id, ticket_type, status = row

        embed = discord.Embed(
            title=f"Ticket #{ticket_id}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Owner", value=f"<@{user_id}>", inline=True)
        embed.add_field(name="Type", value=ticket_type, inline=True)
        embed.add_field(name="Status", value=status, inline=True)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Tickets(bot))
