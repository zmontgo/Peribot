from discord.ext import commands
from cogs.utils.dataIO import dataIO
import os
import asyncio
from .utils import checks
import random
import discord


class Giveaways:
    """Giveaways."""

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json("data/giveaways/settings.json")
        self.started = False

    @commands.group(pass_context=True)
    async def giveaway(self, ctx):
        """Start or stop giveaways."""
        if not ctx.invoked_subcommand:
            await             self.bot.send_cmd_help(ctx)

    @giveaway.command(pass_context=True)
    @checks.mod_or_higher()
    async def start(self, ctx, *, settings):
        """Start a giveaway.
        TODO: Allow Mods to use this command
        Usage"
        [p]giveaway start name: <Giveaway  name>; length: <Time length>; entries: [Max entries]
        Giveaway name is mandatory.
        Length is mandatory.
        Max entries is optional.

        Example:
        [p]giveaway start name: Minecraft account; entries: 99; length: 3 days
        [p]giveaway start name: Minecraft account; length: 2 hours; entries: 42
        [p]giveaway start name: Minecraft account; length: 5 days"""
        settings = settings.split("; ")
        setdict = False
        server = ctx.message.server
        if server.id not in self.settings:
            self.settings[server.id] = {}
        # Setting all of the settings.
        for setting in settings:
            if not setdict:
                settings = {"name": "", "length": -1, 'entries': 0, "users": [], "started": True}
                setdict = True
            if setting.startswith("name: "):
                if setting[6:] in self.settings[ctx.message.server.id]:
                    await self.bot.say("There's already a giveaway running with this name.")
                    return
                else:
                    settings['name'] = setting[6:]
            elif setting.startswith("length: "):
                length = setting[7:]
                lengths = {'hour': 3600, 'day': 86400}
                if "days" in length.split() or "day" in length.split():
                    try:
                        settings['length'] = int(length.split()[0]) * lengths['day']
                    except:
                        await self.bot.say("The 'length' parameter, {}, does not start with an integer.".format(length))
                        return
                elif "hour" in length.split() or "hours" in length.split():
                    try:
                        settings['length'] = int(length.split()[0]) * lengths['hour']
                    except:
                        await self.bot.say("The 'length' parameter, {}, does not start with an integer.".format(length))
                        return
                else:
                    await self.bot.say("You can only use hours and days.")
                    return
                # Checking if mandatory settings are there.
        if settings['name'] == "":
            await self.bot.say("The 'name' parameter cannot be empty.")
            return
        if settings['length'] == -1:
            await self.bot.say("The 'length' parameter cannot be empty.")
            return
        embed = discord.Embed(title=":tada: New Giveaway Started! :tada:", description="React to this message to enter!", color=discord.Color.green())
        embed.add_field(name=f"Prize:", value=f"{settings['name']}")
        embed.add_field(name=f"Length:", value=f"{int(settings['length']) / 3600} Hours")
        embed.add_field(name=f"Sponsored by:", value=f"{ctx.message.author}")
        message = await self.bot.say(embed=embed)
        self.settings[server.id][str(message.id)] = settings
        self.save_settings()
        await self.bot.add_reaction(message, "✅")
        await self.bot.delete_message(ctx.message)

    @giveaway.command(pass_context=True)
    @checks.mod_or_higher()
    async def stop(self, ctx, message_id):
        """Stops a giveaway early so you can pick a winner.
        Example:
        [p]giveaway stop 620715054211268637"""
        server = ctx.message.server
        if server.id not in self.settings:
            await self.bot.say("There are no giveaways in this server.")
        elif message_id not in self.settings[server.id]:
            await self.bot.say(
                "That's not a valid giveaway, to see all giveaways you can do {}giveaway list".format(ctx.prefix))
        elif not self.settings[server.id][message_id]['started']:
            await self.bot.say("That giveaway's already stopped.")
        else:
            self.settings[server.id][message_id]['started'] = False
            self.save_settings()
            await self.bot.say("You can now pick a winner with {}giveaway pick <amount>".format(ctx.prefix))

    @giveaway.command(pass_context=True)
    @checks.mod_or_higher()
    async def pick(self, ctx, amount: int, giveaway_id):
        """Picks <amount> of winners for the giveaway, which usually should be 1.
        Example:
        [p]giveaway pick 5 Minecraft account (This will pick 5 winners from all the people who entered the Minecraft account giveaway)"""
        server = ctx.message.server
        if server.id not in self.settings:
            return await self.bot.say("This server does not have any giveaways yet.")
        giveaways = self.settings[server.id]
        if giveaway_id not in giveaways:
            return await self.bot.say("Sorry thats not a valid message ID!\n```\nHINT: The message ID will be found on the bot's message announcing the giveaway\n```")
        giveaway = giveaways[giveaway_id]
        status = await self.bot.say("Picking winners.")
        winnersIDs = []
        winners = []
        for i in range(amount):
            winnersIDs.append(random.choice(giveaway['users']))
        for winner in winnersIDs:
            winner = discord.utils.get(server.members, id=winner)
            while winner == None:
                winner = discord.utils.get(server.members,
                                           id=random.choice(giveaway['users']))
            winners.append(winner.mention)
        del self.settings[server.id][giveaway_id]
        self.save_settings()
        if amount == 1:
            await self.bot.edit_message(status,
                                  "And thats a wrap! The winner is: {}! Congratulations, you won {}!".format(" ".join(winners),
                                                                                           giveaway['name']))
        else:
            await self.bot.edit_message(status,
                                  "And thats a wrap! The winners are: {}! Congratulations, you won {}!".format(" ".join(winners),
                                                                                             giveaway['name']))

    async def on_reaction_add(self, reaction, user):
        """Enter a giveaway.
        Example:
        [p]giveaway enter Minecraft account."""
        server = reaction.message.server
        author_id = user.id
        message_id = reaction.message.id
        if author_id == "608824312689983488" or author_id == "484461035315527700":
            return
        if message_id in self.settings[server.id]:
            giveaway = self.settings[server.id][message_id]
            if author_id not in self.settings[server.id][message_id]['users']:
                self.settings[server.id][message_id]['users'].append(author_id)
                self.settings[server.id][message_id]['entries'] =+ 1
                self.save_settings()
                return await self.bot.send_message(user, "You have successfully entered the {} giveaway, good luck!".format(giveaway['name']))




    @giveaway.command(pass_context=True)
    async def list(self, ctx):
        """Lists all giveaways running in this server."""
        server = ctx.message.server
        if server.id not in self.settings or self.settings[server.id] == {}:
            await self.bot.say("This server has no giveaways running.")
        else:
            await self.bot.say("This server has the following giveaways running:\n\t{}".format(
                "\n\t".join(list(self.settings[server.id].keys()))))


    @giveaway.command(pass_context=True)
    async def info(self, ctx, *, giveaway):
        """Get information for a giveaway.
        Example:
        [p]giveaway info Minecraft account"""
        server = ctx.message.server
        if server.id not in self.settings:
            await self.bot.say("This server has no giveaways running.")
        elif giveaway not in self.settings[server.id]:
            await self.bot.say("That's not a valid giveaway running in this server.")
        else:
            settings = self.settings[server.id][giveaway]
            await self.bot.say("Name: **{}**\nTime left: **{}**\nMax entries: **{}**\nEntries: **{}**".format(giveaway,
                                                                                                        self.secondsToText(
                                                                                                            settings[
                                                                                                                'length']),
                                                                                                        settings[
                                                                                                            'maxentries'],
                                                                                                        len(settings[
                                                                                                                'users'])))



    def save_settings(self):
        return dataIO.save_json("data/giveaways/settings.json", self.settings)


    async def on_message(self, message):
        if not self.started:
            self.started = True
            print("Giveaways loop started.")
            while True:
                if self.bot.get_cog("Giveaways") != None:
                    await asyncio.sleep(1)
                    self.settings = dataIO.load_json("data/giveaways/settings.json")
                    for server in self.settings:
                        for giveaway in self.settings[server]:
                            if self.settings[server][giveaway]['started']:
                                self.settings[server][giveaway]['length'] -= 1
                                if self.settings[server][giveaway]['length'] == 0:
                                    self.settings[server][giveaway]['started'] = False
                    self.save_settings()
                else:
                    print("Giveaways loop stopped, cog not loaded anymore.")
                    break

    def secondsToText(self, secs):
        days = secs // 86400
        hours = (secs - days * 86400) // 3600
        minutes = (secs - days * 86400 - hours * 3600) // 60
        seconds = secs - days * 86400 - hours * 3600 - minutes * 60
        result = ("{0} day{1}, ".format(days, "s" if days != 1 else "") if days else "") + \
                 ("{0} hour{1}, ".format(hours, "s" if hours != 1 else "") if hours else "") + \
                 ("{0} minute{1}, ".format(minutes, "s" if minutes != 1 else "") if minutes else "") + \
                 ("{0} second{1}".format(seconds, "s" if seconds != 1 else "") if seconds else "")
        return result


def check_folders():
    if not os.path.exists("data/giveaways"):
        print("Creating data/giveaways folder...")
        os.makedirs("data/giveaways")


def check_files():
    if not os.path.exists("data/giveaways/settings.json"):
        print("Creating data/giveaways/settings.json file...")
        dataIO.save_json("data/giveaways/settings.json", {})


def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Giveaways(bot))
