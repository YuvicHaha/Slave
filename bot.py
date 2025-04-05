import os
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load the environment variable for the bot token
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not TOKEN:
    raise ValueError("Bot token is missing! Make sure it's set in the environment variables.")

# Setting up intents for the bot
intents = discord.Intents.default()
intents.messages = True  
intents.message_content = True  
intents.guilds = True 
intents.members = True  

bot = commands.Bot(command_prefix='!', intents=intents)

# Set of allowed domains and users
ALLOWED_DOMAINS = {"example.com", "trustedsite.com"}  # Add trusted domains here
ALLOWED_USERS = {598460565387476992, 1272478153201422420, 1279868613628657860}  # Add allowed user IDs here

# Channels to monitor for unwanted links
MONITORED_CHANNELS = {
    1317511572205342720,
    1338517376261427210,
    1342317204234047549,
    1348157548997509201
}

# Regex pattern to match URLs in the message content
LINK_PATTERN = re.compile(r"https?://(?:www\.)?([\w.-]+)")

# Store warnings for users
warnings = {}
MAX_WARNINGS = 2  # Max warnings before kicking

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check if bot has permissions to manage messages and kick members
    if not message.guild.me.guild_permissions.manage_messages:
        print(f"Bot cannot delete messages in the server.")  

    if not message.guild.me.guild_permissions.kick_members:
        print(f"Bot cannot kick members.") 

    # If the message isn't from one of the monitored channels, ignore it
    if message.channel.id not in MONITORED_CHANNELS:
        return  

    # Skip allowed users (admins, moderators, etc.)
    if message.author.id in ALLOWED_USERS:
        await bot.process_commands(message)
        return 

    # Find all links in the message content
    found_links = LINK_PATTERN.findall(message.content)
    if found_links:
        # Filter out the links that aren't in the allowed domains
        unapproved_links = [link for link in found_links if link not in ALLOWED_DOMAINS]
        
        if unapproved_links:
            print(f"Unapproved links found: {unapproved_links}")
            
            try:
                # Delete the message containing the unapproved link
                await message.delete()
                print(f"Message from {message.author} deleted.") 

                user_id = message.author.id
                # Increase the warning count for the user
                warnings[user_id] = warnings.get(user_id, 0) + 1
                print(f"User {message.author} has {warnings[user_id]} warnings.") 

                # If the user exceeds the max warnings, kick them
                if warnings[user_id] >= MAX_WARNINGS:
                    await message.author.send("You have been warned multiple times for sending unwanted links. You are now being kicked.")
                    await message.guild.kick(message.author, reason="Repeatedly sending unapproved links.")
                    del warnings[user_id]  # Remove the user's warnings after kicking them
                    print(f"{message.author} has been kicked.")  
                else:
                    await message.author.send(f"Warning {warnings[user_id]}/{MAX_WARNINGS}: Do not send unapproved links. One more and you will be kicked.")
                    await message.channel.send(f'{message.author.mention}, your message contained an unapproved link and was removed. You have been warned {warnings[user_id]}/{MAX_WARNINGS}.', delete_after=5)

            except discord.errors.Forbidden:
                print(f"Bot doesn't have permission to delete messages in {message.channel}.") 
            except discord.errors.HTTPException as e:
                print(f"HTTP error occurred while processing the message: {e}") 
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

            return  # Stop processing the message further
    
    # Continue processing other commands or events in the message
    await bot.process_commands(message)  

# Run the bot with the token from environment variables
bot.run(TOKEN)
