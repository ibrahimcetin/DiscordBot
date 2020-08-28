import asyncio
import random
import json
import time

import discord
from discord.ext import commands

from restdb import RestDB


START = time.time()

JSON_DATA = json.load(open("data.json"))


class MyRestDB(RestDB):
    def __init__(self):
        super().__init__()

    async def memberInfo(self, member_id):
        resp_data = await self.getDocument(member_id)

        if resp_data:
            member_info = {}
            member_info["member_id"] = resp_data["member_id"]
            member_info["xp"] = resp_data["xp"]
            member_info["level"] = resp_data["level"]

            return member_info

        else:
            return False

    async def newMember(self, member_id: str):
        data = {"member_id": member_id, "xp": 0, "level": 1}
        resp_data = await self.newDocument(data)

        return resp_data


    async def updateMemberInfo(self, member_id: str, data: dict):
        resp_data = await self.getDocument(member_id)

        if resp_data:
            resp = await self.updateDocument(resp_data["_id"], data)
            return resp
        else:
            return False

    async def deleteMember(self, member_id: str):
        resp_data = await self.getDocument(member_id)

        if resp_data:
            resp = await self.deleteDocument(resp_data["_id"])
            return resp
        else:
            return False


class MyContext(commands.Context):
    async def helpMessage(self):
        help_text = JSON_DATA["help_message"]

        await self.send(f"""```diff
{help_text}```""")

    async def sendUserAvatar(self, user):
        embed = discord.Embed(description=f"{user.mention} avatarı", color=0x2F3136)
        embed.set_image(url=user.avatar_url)

        await self.send(embed=embed)

    async def sendUserInfo(self, user, requested_by):
        embed = discord.Embed(title=f"**{user.name}** Üye Bilgisi", description=f"Kullanıcı ID'si | {user.id}", color=0x6675FF)
        embed.set_footer(text=f"{requested_by.name} tarafından istendi | {requested_by.id}")
        embed.set_thumbnail(url=user.avatar_url)

        roles = [role.mention for role in user.roles if not role.name == '@everyone']
        roles_text = " ".join(roles) if roles else user.roles[0].name
        embed.add_field(
            name="Roller",
            value=roles_text,
            inline=False
        )

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

        msj = await self.send("Duyuru yapıldı!")
        await asyncio.sleep(3)
        await msj.delete()

        if failed:
            print(failed)

    async def sendDatabaseInfo(self):
        start = time.time()
        await self.bot.db.getDocument()
        delay = (time.time() - start) * 1000

        if delay <= 1000:
            connection_text = ":green_circle: İyi"
            embed_color = discord.Colour.green()
        elif 1000 < delay <= 3000:
            connection_text = ":orange_circle: Normal"
            embed_color = discord.Colour.orange()
        else:
            connection_text = ":red_circle: Kötü"
            embed_color = discord.Colour.red()

        embed = discord.Embed(
            title="Veritabanı Bilgisi",
            color=embed_color,
        )

        embed.add_field(
            name="Bağlantı",
            value=connection_text
        )

        embed.add_field(
            name="Cevap Süresi",
            value=f"{int(delay)}ms"
        )

        await self.send(embed=embed)

class MyBot(commands.Bot):
    async def on_connect(self):
        self.db = MyRestDB()
        self.db.connect(
            url=JSON_DATA["database_url"],
            api_key=JSON_DATA["database_api_key"]
        )

    async def on_ready(self):
        self.guild = self.get_guild(JSON_DATA["guild_id"])
        self.get_roles_from_guild()

        print("Her şey hazır!")

    async def on_message(self, message):
        if message.author.bot or message.type.name == "new_member":
            pass

        elif message.content.startswith("!"):
            await self.process_commands(message)

        else:
            member_id = str(message.author.id)
            member_info = await self.db.memberInfo(member_id)

            if member_info:
                member_xp = member_info["xp"]
                member_level = member_info["level"]

                message_len = len(message.content.replace(" ", ""))
                _message_xp = message_len // 20
                message_xp = 1 if _message_xp <= 0 else _message_xp

                member_xp += message_xp
                level_max_xp = 50*(2**member_level)

                if (member_xp > level_max_xp) and (role := self.roles.get(f"Level {member_level+1}", False)):
                    member_xp -= level_max_xp

                    await message.author.remove_roles(self.roles[f"Level {member_level}"])
                    member_level += 1
                    await message.author.add_roles()
                    await message.channel.send(JSON_DATA["level_up_message"].format(name=message.author.mention, level=member_level))

                elif (member_xp > level_max_xp) and not (role := self.roles.get(f"Level {member_level+1}", False)):
                    member_xp = level_max_xp

                await self.db.updateMemberInfo(member_id, {"xp": member_xp, "level": member_level})

            else:
                await self.on_member_join(message.author)

    async def on_member_join(self, member):
        await member.send(JSON_DATA["welcome_message_dm"])

        if success := await self.db.newMember(str(member.id)):
            await member.add_roles(self.roles["Level 1"])

    async def on_member_remove(self, member):
        if success := await self.db.deleteMember(str(member.id)):
            pass

    async def on_raw_reaction_add(self, payload):
        message_id = str(payload.message_id)
        if message_id in JSON_DATA["auto_roles"].keys():
            emoji_name = str(payload.emoji.name)

            if emoji_name in JSON_DATA["auto_roles"][message_id].keys():
                role_name = JSON_DATA["auto_roles"][message_id][emoji_name]

                await payload.member.add_roles(self.roles[role_name])

    async def on_raw_reaction_remove(self, payload):
        message_id = str(payload.message_id)
        if message_id in JSON_DATA["auto_roles"].keys():
            emoji_name = str(payload.emoji.name)

            if emoji_name in JSON_DATA["auto_roles"][message_id].keys():
                member = self.guild.get_member(payload.user_id)

                role_name = JSON_DATA["auto_roles"][message_id][emoji_name]

                await member.remove_roles(self.roles[role_name])

    async def get_context(self, message, *, cls=MyContext):
        return await super().get_context(message, cls=cls)

    def get_roles_from_guild(self):
        self.roles = {}
        for role in self.guild.roles:
            self.roles[role.name] = role

    """
    async def on_command_error(self, ctx, error):
        pass
    """


bot = MyBot(command_prefix=JSON_DATA["prefix"])


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
        requested_by = ctx.message.author
        await ctx.sendUserInfo(user, requested_by)


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
async def make_announcement(ctx, *, message):
    if ctx.guild.owner.id == ctx.message.author.id:
        await ctx.makeAnnouncement(message)


@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_user(ctx):
    user = ctx.message.mentions[0]
    user_name = user.name

    await user.kick()
    await ctx.send(f"@{user_name} sunucudan atıldı!")


@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_user(ctx):
    user = ctx.message.mentions[0]
    user_name = user.name

    await user.ban()
    await ctx.send(f"@{user.name} sunucudan yasaklandı!")


@bot.command(name="temizle")
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, arg):
    deleted = await ctx.channel.purge(limit=int(arg))

    msg = await ctx.send(f"{len(deleted)} mesaj temizlendi!")

    await asyncio.sleep(3)
    await msg.delete()


@bot.command(name="db")
async def database_status(ctx):
    await ctx.sendDatabaseInfo()


@bot.command(name="slowmode")
async def set_slowmode(ctx, delay):
    if delay == "off":
        delay = 0

    await ctx.channel.edit(slowmode_delay = int(delay))


"""
async def arange(count):
    for i in range(count):
        yield i
"""


token = JSON_DATA["token"]
bot.run(token)
