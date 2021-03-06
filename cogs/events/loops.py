import asyncio
import os
import sys
from datetime import datetime
from os.path import dirname, join
import re

import discord
import psycopg2
from discord.ext import commands, tasks
from dotenv import load_dotenv
import dropbox

from def_list import data_upload

sys.path.append("../")

try:
    import tokens
    local = True
except ModuleNotFoundError:
    local = False

if local:
    SQLpath = tokens.PostgreSQL
    dropbox_token = tokens.DB_URL
else:
    SQLpath = os.environ["DATABASE_URL"]
    dropbox_token = os.environ["DB_URL"]

db = psycopg2.connect(SQLpath)
cur = db.cursor()

dbx = dropbox.Dropbox(dropbox_token)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_num = 0
        self.loop2.start()
        self.check_seichi.start()
        self.change_status.start()

    @tasks.loop(seconds=60)
    async def loop2(self):
        client = self.bot
        await client.wait_until_ready()
        hm = datetime.now().strftime("%H:%M")
        if hm == "23:58":
            await data_upload(self)
            await asyncio.sleep(5)
            cur.execute("SELECT ranking_data FROM daily_ranking ORDER BY date DESC;")
            ch = self.bot.get_channel(698486078503649280)
            data = cur.fetchone()
            await ch.send(f"```{data[0]}```")

    @tasks.loop(seconds=60)
    async def check_seichi(self):
        await self.bot.wait_until_ready()
        hm = datetime.now().strftime("%H:%M")
        if hm == "23:50":
            ch = self.bot.get_channel(706322916060692571)
            async for msg in ch.history():
                if msg.author == self.bot.user:
                    last_record = await ch.fetch_message(msg.id)
                    last_record_list = last_record.content.splitlines()
                    break

            mcid_uuid_dic = {
                "shibatanienn_ts": "f63f13d9-ea1d-43f9-a0c7-46bb9445625d",
                "takosan_ykz": "4303b357-30ca-4209-a6c9-d96bafc60cf0",
                "chorocra": "438ed7bf-cbcf-40d9-a672-aacc2868e267",
                "ranzumu": "45578816-9dab-49fc-bef0-0525e0a57289",
                "kakkoiihito": "24eeb1a3-ed4a-444e-828c-5318122f4e4a",
                "nekorobi_0": "d6be1561-47c1-4e67-9829-2aca48f9be39",
                "chorocra_19800": "10cf3d97-a6aa-4ef0-8c27-a917e5cb59d8",
                "kaerusan82433413": "9cec894e-9ae3-4a25-97c5-b7a6c55c1376"  # todo 8月になったら外す
            }

            msg = ""
            for i, mcid in enumerate(mcid_uuid_dic.keys()):
                uuid = mcid_uuid_dic[mcid]
                if len(last_record_list) < i:
                    data = self.bot.get_mined_block(uuid)
                    msg += f"{mcid}の整地量>>>{data}(前日比:0)\n"
                    continue
                last_user_record = int(re.sub(r'\(前日比:\d+\)', '', last_record_list[i].split('>>>')[1]))

                data = self.bot.get_mined_block(uuid)

                data_difference = data - last_user_record
                msg += f"{mcid}の整地量>>>{data}(前日比:{data_difference})\n"
                await asyncio.sleep(2)
            await ch.send(msg)

    @tasks.loop(minutes=3)
    async def change_status(self):
        await self.bot.wait_until_ready()
        if self.status_num == 0:
            await self.bot.change_presence(activity=discord.Game(f"{len(list(self.bot.get_all_members()))}人を監視中"))
            self.status_num += 1
        elif self.status_num == 1:
            await self.bot.change_presence(activity=discord.Game(f"{len(self.bot.guilds)}サーバー"))
            self.status_num += 1
        else:
            await self.bot.change_presence(activity=discord.Game("カスタムprefixを実装"))
            self.status_num = 0


def setup(bot):
    bot.add_cog(Loops(bot))
