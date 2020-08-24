import asyncio
import random
import json
import time

import discord
from discord.ext import commands


START = time.time()


class MyContext(commands.Context):
    async def helpMessage(self):
        help_text = """
Yardım mesajı"""

        await self.send(f"```diff{help_text}```")

    async def sendUserAvatar(self, user):
        embed = discord.Embed(description=f"{user.mention} avatarı", color=0x2F3136)
        embed.set_image(url=user.avatar_url)

        await self.send(embed=embed)

    async def sendUserInfo(self, user):
        embed = discord.Embed(title=f"**{user.name}** Üye Bilgisi", color=0x6675FF)
        embed.set_footer(text=f"Bu havalı kullanıcının ID'si {user.id}")
        embed.set_thumbnail(url=user.avatar_url)

        j_date = user.joined_at
        embed.add_field(
            name="Sunucuya katılma tarihi",
            value=f"{j_date.day}/{j_date.month}/{j_date.year}  {j_date.hour}:{j_date.minute}",
            inline=True,
        )

        c_date = user.created_at
        embed.add_field(
            name="Hesabını açma tarihi",
            value=f"{c_date.day}/{c_date.month}/{c_date.year}  {c_date.hour}:{c_date.minute}",
            inline=True,
        )

        """
        roles = " ".join(user.roles)
        embed.add_field(name="Roller", value=roles, inline=False)
        """

        await self.send(embed=embed)

    async def sendServerInfo(self):
        embed = discord.Embed(
            title="Sunucu Bilgisi",
            description=f"Bu sunucunun sahibi {self.guild.owner.mention}",
            color=0xEB4334,
        )
        embed.set_footer(text=f"Sunucu ID'si {self.guild.id}")
        embed.set_thumbnail(url=self.guild.icon_url)

        members = self.guild.members

        online = 0
        offline = 0
        bot = 0
        dnd = 0
        idle = 0

        for m in members:
            if m.bot:
                bot += 1
            elif m.status == discord.Status.online:
                online += 1
            elif (
                m.status == discord.Status.offline
                or m.status == discord.Status.invisible
            ):
                offline += 1
            elif m.status == discord.Status.idle:
                idle += 1
            elif m.status == discord.Status.dnd:
                dnd += 1

        embed.add_field(
            name=f"__**{self.guild.member_count}** Üye__",
            value=f":green_circle: **{online}** Çevrimiçi\n:orange_circle: **{idle}** Boşta\n:red_circle: **{dnd}** Meşgul\n:white_circle: **{offline}** Çevrimdışı\n:robot: **{bot}** Bot",
        )
        embed.add_field(
            name=f"__**{len(self.guild.channels)}** Kanal__",
            value=f"Metin: **{len(self.guild.text_channels)}**\nSesli: **{len(self.guild.voice_channels)}**\nKategori: **{len(self.guild.categories)}**",
        )

        date = self.guild.created_at
        embed.add_field(
            name="__Oluşturulma tarihi__",
            value=f"{date.day}/{date.month}/{date.year}  {date.hour}:{date.minute}",
        )

        await self.send(embed=embed)

    async def makeAnnouncement(self, message):
        failed = []

        for m in self.guild.members:
            if not m.bot and m != self.guild.owner:
                try:
                    dm = await m.create_dm()
                    await dm.send(message.format(m.name))
                except:
                    failed.append(m)

        self.send("Duyuru yapıldı!")

        if failed:
            print(failed)


class MyBot(commands.Bot):
    async def on_connect(self):
        self.json_data = json.load(open("data.json"))

    async def on_ready(self):
        print("Her şey hazır!")

    async def on_message(self, message):
        await self.process_commands(message)

    async def on_raw_reaction_add(self, payload):
        message_id = str(payload.message_id)
        if message_id in self.json_data["Auto Roles"].keys():
            emoji_name = str(payload.emoji.name)

            if emoji_name in self.json_data["Auto Roles"][message_id].keys():
                role = discord.utils.get(
                    payload.member.guild.roles,
                    name=self.json_data["Auto Roles"][message_id][emoji_name],
                )

                await payload.member.add_roles(role)

    async def on_raw_reaction_remove(self, payload):
        message_id = str(payload.message_id)
        if message_id in self.json_data["Auto Roles"].keys():
            emoji_name = str(payload.emoji.name)

            if emoji_name in self.json_data["Auto Roles"][message_id].keys():
                guild = self.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                roles = guild.roles

                role = discord.utils.get(
                    roles, name=self.json_data["Auto Roles"][message_id][emoji_name]
                )

                await member.remove_roles(role)

    async def get_context(self, message, *, cls=MyContext):
        return await super().get_context(message, cls=cls)

    """
    async def on_command_error(self, ctx, error):
        pass
    """


bot = MyBot(command_prefix="!")


@bot.command(name="yardım")
async def help_message(ctx):
    await ctx.helpMessage()


@bot.command(name="avatar")
async def user_avatar(ctx):
    if len(ctx.message.mentions) != 1:
        await ctx.send(
            f"Birinin avatarını görmek için o kişiyi belirtmen gerek `!avatar @isim`"
        )
    else:
        user = ctx.message.mentions[0]
        await ctx.sendUserAvatar(user)


@bot.command(name="üye")
async def member_info(ctx):
    if len(ctx.message.mentions) != 1:
        await ctx.send(
            "Üye bilgisi görüntüleyebilmek için bir kişi seçmeniz gerekiyor. `!üye @isim`"
        )
    else:
        user = ctx.message.mentions[0]
        await ctx.sendUserInfo(user)


@bot.command(name="uptime")
async def server_uptime(ctx):
    seconds = time.time() - START

    _minute, sec = divmod(seconds, 60)
    hour, minute = divmod(_minute, 60)

    await ctx.send(
        f"Bot {int(hour)} saat, {int(minute)} dakika, {int(sec)} saniyedir açık."
    )


@bot.command(name="sunucu")
async def server_info(ctx):
    await ctx.sendServerInfo()


@bot.command(name="duyuru")
@commands.check(commands.is_owner())
async def make_announcement(ctx, *, message):
    await ctx.makeAnnouncement(message)


@bot.command(name="kick")
async def kick_user(ctx):
    if ctx.message.author.guild_permissions.kick_members:
        user = ctx.message.mentions[0]
        user_name = user.name

        await user.kick()
        await ctx.send(f"@{user_name} sunucudan atıldı!")


@bot.command(name="ban")
async def ban_user(ctx):
    if ctx.message.author.guild_permissions.ban_members:
        user = ctx.message.mentions[0]
        user_name = user.name

        await user.ban()
        await ctx.send(f"{user_name} sunucudan yasaklandı!")


@bot.command(name="sil")
async def delete_messages(ctx, arg):
    messages = await ctx.channel.history(limit=int(arg)).flatten()

    await ctx.channel.delete_messages(messages)
    msg = await ctx.send(f"{len(messages)} mesaj silindi!")

    await asyncio.sleep(3)
    await msg.delete()


token = "token"
bot.run(token)
