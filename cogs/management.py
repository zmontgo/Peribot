import asyncio

from loguru import logger

import discord
import git
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord.ext.commands.errors import BadArgument

from .utils.checks import admin_or_permissions
from .utils.database import Database


class Management(commands.Cog):

    """
    Set of commands for Administration.
    """

    def __init__(self, bot):
        self.bot = bot
        self.database = Database()

    @commands.Cog.listener()
    async def on_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            return
        raise error

    @commands.Cog.listener()
    async def on_command_error(self, ctx, exception):
        if isinstance(exception, BadArgument):
            embed = discord.Embed(title=f"Error: {exception}", color=discord.Color.red())
            message = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await message.delete()

    @commands.command(name='setcolor', no_pm=True, aliases=["rolecolor", "color"])
    async def set_role_color(self, ctx, role: discord.Role, color: discord.Color):
        """
        Color the nickname of the participant. * Let there be bright colors and colors! *
        [!] In development.
        Arguments:
        color in HEX

        For example:
        !setcolor #FF0000
        """
        try:
            if not role.is_default():
                await role.edit(color=color)
                embed = discord.Embed(title=f"Changed the role color for {role.name} to {color}", color=color)
                await ctx.send(embed=embed)
                await self.database.audit_record(ctx.guild.id,
                                                 ctx.guild.name,
                                                 ctx.message.content,
                                                 ctx.message.author.id)
            else:
                embed = discord.Embed(title="Peribot cannot affect the default roles.")
                await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(title="Peribot does not have permissions to change roles." )
            await ctx.send(embed=embed)
        except discord.HTTPException:
            embed = discord.Embed(title=f"Peribot failed to update {role.name}'s color" )
            await ctx.send(embed=embed)
        except discord.InvalidArgument:
            embed = discord.Embed(title=f"Invalid Arguments!", description=f"{ctx.prefix}setcolor @Role [Hex Code or Generic Name]")
            await ctx.send(embed=embed)
        except discord.ext.commands.errors.BadArgument:
            embed = discord.Embed(title=f"Invalid Arguments!", description=f"{ctx.prefix}setcolor @Role [Hex Code or Generic Name]")
            await ctx.send(embed=embed)

    @commands.command('prefix', no_pm=True)
    @admin_or_permissions()
    async def prefix(self, ctx, prefix):
        if await self.database.update_server_settings(ctx.guild.id, prefix=prefix):
            await ctx.send("Preibot's command prefix has been updated!")
        else:
            await ctx.send("Preibot's command prefix failed to update!")

    @commands.command(name='nick', aliases=["setnick"])
    @commands.cooldown(1, 21600, commands.BucketType.user)
    async def nick(self, ctx, user: discord.Member, *, nick):
        if ctx.author.id == 309089769663496194 or ctx.author.id == 204792579881959424:
            await user.edit(nick=nick, reason="Jeep made me do it")
            await self.database.audit_record(ctx.guild.id,
                                             ctx.guild.name,
                                             ctx.message.content,
                                             ctx.message.author.id)

    @commands.command(name='gitpull')
    async def git_pull(self, ctx):
        if ctx.author.id == 204792579881959424:
            git_dir = "./"
            try:
                g = git.cmd.Git(git_dir)
                g.pull()
                embed = discord.Embed(title=":white_check_mark: Successfully pulled from repository", color=0x00df00)
                await ctx.channel.send(embed=embed)
                await self.database.audit_record(ctx.guild.id,
                                                 ctx.guild.name,
                                                 ctx.message.content,
                                                 ctx.message.author.id)
            except Exception as e:
                errno, strerror = e.args
                embed = discord.Embed(title="Command Error!",
                                      description=f"Git Pull Error: {errno} - {strerror}",
                                      color=0xff0007)
                await ctx.channel.send(embed=embed)
        else:
            await ctx.send("You don't have access to this command!")

    @commands.command(name='mute')
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, user: discord.User):
        pass

    @commands.command(name='servers')
    @commands.has_permissions(manage_messages=True)
    async def servers(self, ctx):
        servers = self.bot.guilds
        for server in servers:
            await ctx.send(server.name)


    @commands.command(name='pin')
    @commands.has_permissions(manage_messages=True)
    async def pin_message(self, ctx, *, message):
        """Copy your message in a stylish and modern frame, and then fix it!
        Arguments:
        `: message` - message
        __ __
        For example:
        ```
        !pin This text was written by the ancient Elves in the name of Discord!
        ```
        """
        embed = discord.Embed(color=ctx.message.author.top_role.color,
                              title='Pin it up!',
                              description=message)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f'{ctx.prefix}{ctx.command}')
        msg = await ctx.send(embed=embed)
        await ctx.message.delete()
        await msg.pin()
        await self.database.audit_record(ctx.guild.id,
                                         ctx.guild.name,
                                         ctx.message.content,
                                         ctx.message.author.id)

    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = 'N/A'):
        """
        `:member` - The person you are kicking
        `:reason` - Reason for kick

        """
        try:
            await member.kick(reason=reason)
        except Exception as e:
            await ctx.send("error")
            return
        embed = discord.Embed(timestamp=ctx.message.created_at, color=0x00ff00,
                              description=f'User {member.name} was kicked.\nReason: {reason}.')
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f'{ctx.prefix}{ctx.command}')
        await ctx.send(embed=embed)
        await self.database.audit_record(ctx.guild.id,
                                         ctx.guild.name,
                                         ctx.message.content,
                                         ctx.message.author.id)

    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = 'N/A', delete: int = 0):
        """
        `:member` - The person you are banning @ them
        `:reason` - Reason for kick

        """
        try:
            await member.ban(reason=reason, delete_message_days=delete)
        except discord.Forbidden:
            embed = discord.Embed(title="Command Error!", description=f"I do not have permissions to do that", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        except discord.HTTPException:
            embed = discord.Embed(title="Command Error!", description=f"Banning failed. Try again", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(timestamp=ctx.message.created_at, color=0x00ff00,
                              description=f'User {member.name} was banned.\nReason: {reason}.\nMessages Deleted: {delete} days')
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=f'{ctx.prefix}{ctx.command}')
        await ctx.send(embed=embed)
        await self.database.audit_record(ctx.guild.id,
                                         ctx.guild.name,
                                         ctx.message.content,
                                         ctx.message.author.id)

    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, member: int, *, reason: str = 'N/A'):
        """
        `:member` - The person you are unbanning (their ID)
        `:reason` - Reason for kick

        """
        for banentry in await ctx.guild.bans():
            if member == banentry.user.id:
                try:
                    await ctx.guild.unban(banentry.user, reason=reason)
                except discord.Forbidden:
                    embed = discord.Embed(title="Command Error!", description=f"I do not have permissions to do that",
                                          color=discord.Color.red())
                    await ctx.send(embed=embed)
                    return
                except discord.HTTPException:
                    embed = discord.Embed(title="Command Error!", description=f"Unbanning failed. Try again",
                                          color=discord.Color.red())
                    await ctx.send(embed=embed)
                    return
                embed = discord.Embed(timestamp=ctx.message.created_at, color=0x00ff00,
                                      description=f'User {banentry.user.name} was unbanned.\nReason: {reason}.')
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                embed.set_footer(text=f'{ctx.prefix}{ctx.command}')
                await ctx.send(embed=embed)
                await self.database.audit_record(ctx.guild.id,
                                                 ctx.guild.name,
                                                 ctx.message.content,
                                                 ctx.message.author.id)



def setup(bot):
    bot.add_cog(Management(bot))
