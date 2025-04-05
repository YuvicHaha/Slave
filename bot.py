import os
import re
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not TOKEN:
    raise ValueError("Bot token is missing! Make sure it's set in the environment variables.")
else:
    print(f"Bot Token: {TOKEN}")  # Debug line to check if the token is being accessed correctly

intents = discord.Intents.default()
intents.messages = True  
intents.message_content = True  
intents.guilds = True 
intents.members = True  

bot = commands.Bot(command_prefix='!', intents=intents)

ALLOWED_DOMAINS = {"example.com", "trustedsite.com"}

ALLOWED_USERS = {598460565387476992, 1272478153201422420, 1279868613628657860}  # Replace with actual Discord user IDs

MONITORED_CHANNELS = {
    1317511572205342720,
    1338517376261427210,
    1342317204234047549,
    1348157548997509201
}

LINK_PATTERN = re.compile(r"https?://(?:www\.)?([\w.-]+)")

warnings = {}
MAX_WARNINGS = 2 

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if not message.guild.me.guild_permissions.manage_messages:
        print(f"Bot cannot delete messages in the server.")  

    if not message.guild.me.guild_permissions.kick_members:
        print(f"Bot cannot kick members.") 
    if message.channel.id not in MONITORED_CHANNELS:
        return  
    if message.author.id in ALLOWED_USERS:
        await bot.process_commands(message)
        return 

    found_links = LINK_PATTERN.findall(message.content)
    if found_links:
        unapproved_links = [link for link in found_links if link not in ALLOWED_DOMAINS]
        
        if unapproved_links:
            print(f"Unapproved links found: {unapproved_links}")
            
            try:
                await message.delete()
                print(f"Message from {message.author} deleted.") 

                user_id = message.author.id
                warnings[user_id] = warnings.get(user_id, 0) + 1
                print(f"User {message.author} has {warnings[user_id]} warnings.") 

                if warnings[user_id] >= MAX_WARNINGS:
                    await message.author.send("You have been warned multiple times for sending unwanted links. You are now being kicked.")
                    await message.guild.kick(message.author, reason="Repeatedly sending unapproved links.")
                    del warnings[user_id]  
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

            return  
    
    await bot.process_commands(message)  

bot.run(TOKEN)
