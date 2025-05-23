import discord
import re
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the token from the environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

# Initialize the bot
bot = commands.Bot(command_prefix='!', intents=intents)

# List of allowed domains
ALLOWED_DOMAINS = {"tenor.com", "discord.com", "cdn.discordapp.com"}
# Role name that allows sending links
ALLOWED_ROLE_NAME = "link perms"  # Change this to match the actual role name

# List of channel IDs to monitor
MONITORED_CHANNELS = {
    1317511572205342720,
    1338517376261427210,
    1342317204234047549,
    1348157548997509201
}

# Log channel ID where deleted messages will be sent
LOG_CHANNEL_ID = 1358348081682321428

# Regex pattern to detect links
LINK_PATTERN = re.compile(r"https?://(?:www\.)?([\w.-]+)")

# Dictionary to track warnings
warnings = {}
MAX_WARNINGS = 2  # Number of warnings before kick

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')

@bot.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return

    # Check if the message is in one of the monitored channels
    if message.channel.id not in MONITORED_CHANNELS:
        return  # Ignore messages from other channels

    # Check if the user has the allowed role
    role_names = {role.name.lower() for role in message.author.roles}
    if ALLOWED_ROLE_NAME.lower() in role_names:
        await bot.process_commands(message)
        return  # Skip link checks for allowed roles

    # Check for links in the message content
    found_links = LINK_PATTERN.findall(message.content)
    if found_links:
        # Filter out allowed domains
        unapproved_links = [link for link in found_links if link not in ALLOWED_DOMAINS]
        
        if unapproved_links:
            print(f"Unapproved links found: {unapproved_links}")  # Debug output
            
            try:
                # Save deleted message details
                deleted_message_info = f"🚨 **Deleted Message Log** 🚨\n" \
                                       f"👤 **User:** {message.author} (ID: {message.author.id})\n" \
                                       f"📢 **Channel:** {message.channel.mention}\n" \
                                       f"📝 **Message:** {message.content}\n" \
                                       f"❌ **Unapproved Links:** {', '.join(unapproved_links)}"

                # Attempt to delete the message
                await message.delete()
                print(f"Message from {message.author} deleted.")  # Debug output

                # Send deleted message info to the log channel
                log_channel = bot.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(deleted_message_info)

                # Initialize or increment warning count
                user_id = message.author.id
                warnings[user_id] = warnings.get(user_id, 0) + 1
                print(f"User {message.author} has {warnings[user_id]} warnings.")  # Debug output

                # Handle warnings
                if warnings[user_id] >= MAX_WARNINGS:
                    await message.author.send("You have been warned multiple times for sending unwanted links. You are now being kicked.")
                    await message.guild.kick(message.author, reason="Repeatedly sending unapproved links.")
                    del warnings[user_id]  # Reset warning after kick
                    print(f"{message.author} has been kicked.")  # Debug output
                else:
                    await message.author.send(f"Warning {warnings[user_id]}/{MAX_WARNINGS}: Do not send unapproved links. One more and you will be kicked.")
                    await message.channel.send(f'{message.author.mention}, your message contained an unapproved link and was removed. You have been warned {warnings[user_id]}/{MAX_WARNINGS}.', delete_after=5)

            except discord.errors.Forbidden:
                print(f"Bot doesn't have permission to delete messages in {message.channel}.")  # Debug output
            except discord.errors.HTTPException as e:
                print(f"HTTP error occurred while processing the message: {e}")  # Debug output
            except Exception as e:
                print(f"An unexpected error occurred: {e}")  # Debug output

            return  # Stop further processing if one bad link is found
    
    await bot.process_commands(message)  # Ensure commands still work

# Command to test the bot's response
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

bot.run(DISCORD_TOKEN)  # Use the token from the .env file
