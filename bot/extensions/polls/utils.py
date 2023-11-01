import discord

emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "9️⃣", "🔟"]


def poll_check(message: discord.Message, bot: discord.ClientUser):
    if not message.embeds:
        return False

    embed = message.embeds[0]
    if str(embed.footer.text).count("Poll by") == 1:
        return message.author == bot
