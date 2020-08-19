import random
import json

import discord
from discord.ext import commands


class MyBot(commands.Bot):
    async def on_connect(self):
        self.emojis_json_data = json.load(open("emojis.json"))

    async def on_raw_reaction_add(self, payload):
        if payload.message_id == "message_id":
            emoji_id = str(payload.emoji.id)

            if emoji_id in self.emojis_json_data.keys():
                role = discord.utils.get(
                    payload.member.guild.roles, name=self.emojis_json_data[emoji_id]
                )

                await payload.member.add_roles(role)

    async def on_raw_reaction_remove(self, payload):
        if payload.message_id == "message_id":
            emoji_id = str(payload.emoji.id)

            if emoji_id in self.emojis_json_data.keys():
                guild = self.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                roles = guild.roles

                role = discord.utils.get(roles, name=self.emojis_json_data[emoji_id])

                await member.remove_roles(role)


bot = MyBot(command_prefix="!")

token = "token"
bot.run(token)
