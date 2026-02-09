"""Discord Raffle Bot - A raffle system for Discord servers with role-based access control.

Usage:
    !roll <item_name> <seconds> [target_role]
    !cancel <message_id>
    !logs
    !ping
    !check
"""

import discord
import os
import asyncio
import random
import json
from datetime import datetime, timedelta
from typing import Set
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv

# ============================================================================
# ENVIRONMENT & CONFIGURATION
# ============================================================================
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in .env file")

# Channel IDs for bot operations
PUBLIC_CHANNEL_ID: int = 1463855660436553729  # Where raffle messages are posted
COMMAND_CHANNEL_ID: int = 1463855919640088628  # Where commands are issued

# File for storing raffle history
LOG_FILE: str = "raffle_history.json"

# Allowed roles for raffle access
ALLOWED_VIP_ROLES: list[str] = ["Donator", "Elders", "Master"]

# ============================================================================
# INTENTS & BOT SETUP
# ============================================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Global set to track raffles that have been cancelled
cancelled_raffles: Set[int] = set()

# NEW: Track the last winner's ID to prevent streaks
last_winner_id: int = None

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def save_log(item: str, winner_name: str, role_req: str) -> None:
    """Save a completed raffle to the history log.
    
    Args:
        item: Name of the item that was raffled
        winner_name: Discord username of the winner
        role_req: Required role for the raffle
    """
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "item": item,
        "winner": winner_name,
        "role": role_req
    }

    # Load existing logs or create new list
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    # Append new entry and save
    data.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ============================================================================
# DISCORD UI COMPONENTS
# ============================================================================

class RaffleView(View):
    """Interactive raffle view with join button and participant tracking."""
    
    def __init__(self, item_name: str, duration: int, allowed_role: str) -> None:
        """Initialize the raffle view.
        
        Args:
            item_name: Name of the item being raffled
            duration: Duration in seconds before raffle ends
            allowed_role: Role required to participate (or "All")
        """
        super().__init__(timeout=duration)
        self.item_name: str = item_name
        self.allowed_role: str = allowed_role
        self.participants: Set[int] = set()

    @discord.ui.button(label="✋ Join Raffle", style=discord.ButtonStyle.primary, emoji="🎟️")
    async def join_button(self, interaction: discord.Interaction, button: Button) -> None:
        """Handle raffle join button click.
        
        Validates user roles and adds them to the raffle if eligible.
        
        Args:
            interaction: The interaction object from Discord
            button: The button object
        """
        user_role_names = [role.name for role in interaction.user.roles]

        # Check if user has VIP access (required for all raffles)
        has_vip_access = not set(user_role_names).isdisjoint(ALLOWED_VIP_ROLES)
        if not has_vip_access:
            return await interaction.response.send_message(
                "❌ **Access Denied:** You need the **Donator**, **Elders**, or **Master** role.",
                ephemeral=True
            )

        # Check if user has required role (if role-specific raffle)
        if self.allowed_role.lower() != "all":
            if self.allowed_role not in user_role_names:
                return await interaction.response.send_message(
                    f"❌ **Class Mismatch:** This item is for **{self.allowed_role}** only.",
                    ephemeral=True
                )

        # Add user to raffle or notify if already entered
        if interaction.user.id in self.participants:
            await interaction.response.send_message("✅ You are already entered in this raffle!", ephemeral=True)
        else:
            self.participants.add(interaction.user.id)
            button.label = f"✋ Join Raffle ({len(self.participants)})"
            
            # Update message with new entry count
            embed = interaction.message.embeds[0]
            embed.set_field_at(index=2, name="🎟️ Entries", value=f"**{len(self.participants)}**", inline=True)
            await interaction.response.edit_message(embed=embed, view=self)

# ============================================================================
# RAFFLE COMMANDS
# ============================================================================

@bot.command(name="roll")
async def roll(ctx: commands.Context, item_name: str, seconds: int, target_role: str = "All") -> None:
    """Start a new raffle.
    
    Usage:
        !roll <item_name> <seconds> [target_role]
    
    Args:
        ctx: Command context
        item_name: Name of the item being raffled
        seconds: Duration of the raffle in seconds
        target_role: Required role to participate (default: All)
    """
    # Only allow command in specified channel
    if ctx.channel.id != COMMAND_CHANNEL_ID:
        return

    # Get public channel
    public_channel = bot.get_channel(PUBLIC_CHANNEL_ID)
    if not public_channel:
        await ctx.send("❌ **Error:** Cannot find the public channel. Check channel IDs.")
        return

    # Normalize role name
    if target_role.lower() != "all":
        target_role = target_role.capitalize()

    # Determine ping message based on target role
    if target_role.lower() == "all":
        ping_message = "@everyone"
    else:
        role_found = discord.utils.get(ctx.guild.roles, name=target_role)
        ping_message = role_found.mention if role_found else f"**Attention {target_role}s!**"

    # Calculate finish time
    finish_time = datetime.now() + timedelta(seconds=seconds)
    timestamp_code = int(finish_time.timestamp())

    # Create raffle view and embed
    view = RaffleView(item_name, seconds, target_role)
    embed = discord.Embed(
        title="⚔️ **LEGEND OF YMIR RAFFLE**",
        description=f"### {item_name}",
        color=0xFFD700 if target_role.lower() == "all" else 0x9B59B6,
        timestamp=datetime.now()
    )

    if bot.user and bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)

    embed.add_field(name="⏰ Ends In", value=f"<t:{timestamp_code}:R>", inline=True)
    embed.add_field(name="🛡️ Requirement", value=f"`{target_role}`", inline=True)
    embed.add_field(name="🎟️ Entries", value="**0**", inline=True)
    embed.set_footer(text="Click the button to join • Donator+ Only")

    # Send raffle to public channel
    message = await public_channel.send(content=ping_message, embed=embed, view=view)

    # Confirm in command channel
    await ctx.send(
        f"✅ **Raffle started:** {item_name}\n"
        f"🆔 **Raffle ID:** `{message.id}`\n"
        f"📝 Type `!cancel {message.id}` to cancel this raffle"
    )

    # Wait for raffle duration
    await asyncio.sleep(seconds)

    # Check if raffle was manually cancelled
    if message.id in cancelled_raffles:
        cancelled_raffles.discard(message.id)
        return

    # Disable join button
    for child in view.children:
        child.disabled = True
        child.label = "Raffle Ended"
        child.style = discord.ButtonStyle.secondary

    # Handle no participants case
    if len(view.participants) == 0:
        embed.color = 0x95a5a6
        embed.description = f"### {item_name}\n❌ **Ended: No Entries**"
        embed.set_field_at(0, name="⏰ Status", value="**Ended**", inline=True)

        try:
            await message.edit(embed=embed, view=view)
            await public_channel.send(f"📉 **Raffle ended with no entries** for {item_name}")
        except discord.NotFound:
            pass
    else:
        # --- NEW FAIRNESS LOGIC ---
        global last_winner_id
        
        # Create a list of potential winners
        pool = list(view.participants)

        # If the previous winner is in the list, and there are other people too...
        if last_winner_id in pool and len(pool) > 1:
            pool.remove(last_winner_id) # Remove them from this draw
            print(f"Removed previous winner {last_winner_id} from pool to prevent streak.")

        # Select winner from the remaining pool
        winner_id = random.choice(pool)
        
        # Update the last winner for next time
        last_winner_id = winner_id
        # ---------------------------

        winner = await bot.fetch_user(winner_id)

        save_log(item_name, winner.name, target_role)

        embed.color = 0x2ecc71
        embed.description = f"### {item_name}\n🎉 **Winner:** <@{winner_id}>"
        embed.set_field_at(0, name="⏰ Status", value="**Ended**", inline=True)
        embed.set_field_at(2, name="🎟️ Final Entries", value=f"**{len(view.participants)}**", inline=True)

        try:
            await message.edit(embed=embed, view=view)
            await public_channel.send(f"🎉 **CONGRATULATIONS!** <@{winner_id}> has won **{item_name}**!")
        except discord.NotFound:
            pass 

@bot.command(name="cancel")
async def cancel(ctx: commands.Context, message_id: int) -> None:
    """Cancel an active raffle.
    
    Usage:
        !cancel <message_id>
    
    Args:
        ctx: Command context
        message_id: ID of the raffle message to cancel
    """
    # Only allow in command channel
    if ctx.channel.id != COMMAND_CHANNEL_ID:
        return

    # Add to cancelled list
    cancelled_raffles.add(message_id)

    try:
        public_channel = bot.get_channel(PUBLIC_CHANNEL_ID)
        if not public_channel:
            await ctx.send("❌ **Error:** Cannot find the public channel.")
            return

        msg = await public_channel.fetch_message(message_id)
        await msg.delete()
        await ctx.send(f"✅ **Cancelled:** Raffle `{message_id}` has been deleted.")
    except discord.NotFound:
        await ctx.send(f"⚠️ **Note:** Cancelled raffle logic for `{message_id}`, but message was already deleted.")
    except Exception as e:
        await ctx.send(f"❌ **Error:** {str(e)}")

@bot.command(name="logs")
async def logs(ctx: commands.Context) -> None:
    """Display the last 10 raffle results.
    
    Usage:
        !logs
    
    Args:
        ctx: Command context
    """
    if ctx.channel.id != COMMAND_CHANNEL_ID:
        return

    if not os.path.exists(LOG_FILE):
        await ctx.send("📜 **No raffle history yet.**")
        return

    try:
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        await ctx.send("❌ **Error:** Could not read raffle history.")
        return

    recent_logs = data[-10:][::-1]
    embed = discord.Embed(title="📜 **Raffle History (Last 10)**", color=0x3498db)

    log_text = ""
    for entry in recent_logs:
        log_text += f"`{entry['timestamp'][5:16]}` | **{entry['winner']}** won **{entry['item']}**\n"

    embed.description = log_text if log_text else "No entries yet."
    await ctx.send(embed=embed)


@bot.command(name="ping")
async def ping(ctx: commands.Context) -> None:
    """Check bot latency.
    
    Usage:
        !ping
    
    Args:
        ctx: Command context
    """
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 **Pong!** ({latency}ms)")


@bot.command(name="check")
async def check(ctx: commands.Context) -> None:
    """Get the current channel ID.
    
    Usage:
        !check
    
    Args:
        ctx: Command context
    """
    await ctx.send(f"📍 **Channel ID:** `{ctx.channel.id}`")

# ============================================================================
# EVENT HANDLERS
# ============================================================================

@bot.event
async def on_ready() -> None:
    """Handle bot ready event."""
    print(f'✅ Logged in as {bot.user}')
    print(f'📍 Bot ID: {bot.user.id}')


# ============================================================================
# BOT STARTUP
# ============================================================================

if __name__ == "__main__":
    bot.run(TOKEN)