import asyncio
import os

import discord
import dotenv
from discord.ext import tasks

from helper import get_specific_semester, what_lastest_semester
from scrapper import KHSScraper

dotenv.load_dotenv()


class MyClient(discord.Client):
    THUMBNAIL_URL = "https://cdn.discordapp.com/attachments/1193421624041541732/1193421675006533674/avatar.jpg?ex=65aca78c&is=659a328c&hm=cd33ced74d377d7cd234dff56244eefbca830e3798956bb675d06199a2368db2&"
    FOOTER_TEXT = "Developed by @helmy_lh"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scraper = KHSScraper()
        self.data = {}
        self.status_init_data = False
        self.cache_lastest_semester = None

    async def on_ready(self):
        print("Bot has logged in as", self.user)
        embed = self.create_embed(
            "Bot is Online!",
            "Hello, I'm a bot designed to scrape and provide your college study grades. Use `\\help` to see the available commands.",
            discord.Color.green(),
        )
        for guild in self.guilds:
            await guild.text_channels[0].send(embed=embed)
        try:
            self.data = await asyncio.get_event_loop().run_in_executor(
                None, self.scraper.run
            )
            if self.data:
                self.status_init_data = True
                self.cache_lastest_semester = get_specific_semester(
                    self.data, what_lastest_semester(self.data)
                )
                embed = self.create_embed(
                    "Success",
                    "Initial data scraping is done",
                    discord.Color.green(),
                )
                for guild in self.guilds:
                    await guild.text_channels[0].send(embed=embed)
                self.fetch_latest_semester_info.start()

        except Exception as e:
            print(f"Failed to start bot: {e}")
            embed = self.create_embed(
                "Bot failed to start",
                "The bot failed to start due to an error during the initial data scraping. Please check the logs for more details.",
                discord.Color.red(),
            )
            for guild in self.guilds:
                await guild.text_channels[0].send(embed=embed)
            await self.close()

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith("\\"):
            command = message.content.split(" ")[0][1:].lower()
            if command == "refresh":
                await self.refresh_data(message)
            elif command == "semester":
                await self.get_semester_data(message)
            elif command == "help":
                await self.show_help(message)
            else:
                await self.unknown_command(message)

    @tasks.loop(minutes=15)
    async def fetch_latest_semester_info(self):
        if not self.status_init_data:
            return

        self.data = await asyncio.get_event_loop().run_in_executor(
            None, self.scraper.run
        )
        if self.cache_lastest_semester != get_specific_semester(
            self.data, what_lastest_semester(self.data)
        ):
            self.cache_lastest_semester = get_specific_semester(
                self.data, what_lastest_semester(self.data)
            )
            embed = self.create_embed(
                "New Semester Data",
                "There is a new semester data available",
                discord.Color.green(),
            )
            for guild in self.guilds:
                await guild.text_channels[0].send(embed=embed)

    async def refresh_data(self, message):
        if not self.status_init_data:
            embed = self.create_embed(
                "Wait for a moment", "Data is getting scraped", discord.Color.blue()
            )
            await message.channel.send(embed=embed)
            return

        embed = self.create_embed("Loading", "Scraping data...", discord.Color.blue())
        loading_message = await message.channel.send(embed=embed)
        self.data = await asyncio.get_event_loop().run_in_executor(
            None, self.scraper.run
        )
        embed = self.create_embed("Success", "Data scraped", discord.Color.green())

    async def get_semester_data(self, message):
        semester = (
            message.content.split(" ")[1]
            if len(message.content.split(" ")) > 1
            else None
        )
        if not semester:
            embed = self.create_embed(
                "Error", "Semester is not specified", discord.Color.red()
            )
            await message.channel.send(embed=embed)
            return

        if not self.status_init_data:
            embed = self.create_embed(
                "Wait for a moment", "Data is getting scraped", discord.Color.blue()
            )
            await message.channel.send(embed=embed)
            return

        if not self.data:
            embed = self.create_embed(
                "Error", "Data is not scraped yet", discord.Color.red()
            )
            await message.channel.send(embed=embed)
            return

        try:
            semester_data = get_specific_semester(self.data, semester)
            table = "```"
            table += f"{'Nama MK':<40}{'Nilai':<15}\n"
            for data in semester_data:
                table += f"{data['nm_mk']:<40}{data['nilai_huruf']:<15}\n"
            table += "```"
            embed = self.create_embed(
                f"Semester {semester}", table, discord.Color.green()
            )
            await message.channel.send(embed=embed)
        except KeyError:
            embed = self.create_embed(
                "Error", "Semester is not available", discord.Color.red()
            )
            await message.channel.send(embed=embed)

    async def show_help(self, message):
        embed = self.create_embed(
            "Help",
            "Here are the available commands:\n- `\\semester <semester:int>`: Fetches data for a specific semester\n- `\\refresh`: Refreshes the data\n- `\\help`: Displays this help message",
            discord.Color.blue(),
        )
        await message.channel.send(embed=embed)

    async def unknown_command(self, message):
        embed = self.create_embed(
            "Error",
            "Command not recognized. Please use `\\help` for a list of valid commands.",
            discord.Color.red(),
        )
        await message.channel.send(embed=embed)

    async def on_guild_join(self, guild):
        if len(self.guilds) > 1:
            await guild.leave()
        else:
            embed = self.create_embed("Hi!", "Hi, I'm a bot", discord.Color.green())
            await guild.text_channels[0].send(embed=embed)

    def create_embed(self, title, description, color):
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_thumbnail(url=self.THUMBNAIL_URL)
        embed.set_footer(text=self.FOOTER_TEXT)
        return embed


if __name__ == "__main__":
    intents = discord.Intents.default().all()
    client = MyClient(intents=intents)
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN is not set in .env file")
    client.run(token)
