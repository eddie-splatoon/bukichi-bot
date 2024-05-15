import discord
import logging
import os
import textwrap

from discord.ext import tasks
from datetime import datetime as dt

from bukichi_bot.components.image_creator import ImageCreator
from bukichi_bot.components.inactive_members_detector import InactiveMembersDetector
from bukichi_bot.components.log_repository import LogRepository
from bukichi_bot.components.stage_image_creator import StageImageCreator
from bukichi_bot.components.fest_image_creator import FestStageImageCreator
from bukichi_bot.components.salmon_run_stage_image_creator import SalmonRunStageImageCreator
from bukichi_bot.components.splatoon3_api_client import Splatoon3ApiClient

DISCORD_GUILD_ID = os.getenv('DISCORD_GUILD_ID')
BOT_CHANNEL_ID = os.getenv('BOT_CHANNEL_ID')

logger = logging.getLogger('discord')
log = LogRepository()


class BukichiBotClient(discord.Client):
    DEBUG = False

    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.command_tree = discord.app_commands.CommandTree(self)

    async def on_ready(self):
        logger.info(f'Logged on as {self.user}! bot_channel: {BOT_CHANNEL_ID}')
        self.guild = self.get_guild(int(DISCORD_GUILD_ID))
        self.bot_channel = self.get_channel(int(BOT_CHANNEL_ID))
        self.batch_send_stage_image.start()
        self.batch_send_salmon_run_stage_image.start()
        self.batch_detect_inactive_members.start()
        await self.command_tree.sync()
        logger.info('bukichi bot is ready.')

    async def on_message(self, message):
        if message.author.bot:
            return
        logger.info(f'[{message.channel}] Message from {message.author}: {message.content}')
        log.on_message_sent(message.author.name, message.channel.name, message.content)

        if self.DEBUG:
            await self.debug_image(message)

    async def on_message_edit(self, before, after):
        if before.author.bot:
            return
        logger.info(f'[{before.channel}] Message edited from {before.author}: {before.content} -> {after.content}')
        log.on_message_edited(before.author.name, before.channel.name,
                              f'BEFORE: {before.content}\nAFTER: {after.content}')

    async def on_message_delete(self, message):
        if message.author.bot:
            return
        logger.info(f'[{message.channel}] Message deleted from {message.author}: {message.content}')
        log.on_message_deleted(message.author.name, message.channel.name, message.content)

    async def on_bulk_message_delete(self, messages):
        for message in messages:
            if message.author.bot:
                continue
            logger.info(f'[{message.channel}] Message bulk deleted from {message.author}: {message.content}')
            log.on_message_bulk_deleted(message.author.name, message.channel.name, message.content)

    async def debug_image(self, message):
        member = message.author
        guild = member.guild

        image_creator = ImageCreator()

        names = [
            'foo',
            'テスト',
            'てすと',
            'テスト太郎',
            'Discordマン',
        ]
        for name in names:
            image = image_creator.greeting_by_name(name)
            if image != '':
                await guild.system_channel.send(file=discord.File(image))
            else:
                plain_greeting_message = await self.get_greeting_message(name)
                await guild.system_channel.send(plain_greeting_message)

    async def on_member_join(self, member):
        logger.info(f'New member joined. {member}')

        guild = member.guild
        if guild.system_channel is not None:
            # to_send = f'Welcome {member.mention} to {guild.name}!'
            # await guild.system_channel.send(to_send)
            name = member.display_name
            logger.info(f'member: {member}')
            image_creator = ImageCreator()
            image = image_creator.greeting_by_name(name)
            if image != '':
                await guild.system_channel.send(file=discord.File(image))
            else:
                plain_greeting_message = await self.get_greeting_message(name)
                await guild.system_channel.send(plain_greeting_message)

    async def get_greeting_message(self, name):
        return textwrap.dedent(f'''
                {name} さん、はじめましてでし！
                まずは #ルール をよんでね。
                ''')

    @tasks.loop(seconds=60)
    async def batch_send_stage_image(self):
        if self.should_batch_execute(['09:00', '17:00']):
            logger.info('start create stage image.')
            image_creator = StageImageCreator()
            image = image_creator.run()
            logger.info(f'created image: {image}')

            if image is not None:
                await self.bot_channel.send(file=discord.File(image))
                os.remove(image)

            logger.info('start create fest stage image.')
            fest_image_creator = FestStageImageCreator()
            fest_image = fest_image_creator.run()
            logger.info(f'created fest image: {fest_image}')

            if fest_image is not None:
                await self.bot_channel.send(file=discord.File(fest_image))
                os.remove(fest_image)

            logger.info('finish send stage image.')

    @tasks.loop(seconds=60)
    async def batch_send_salmon_run_stage_image(self):
        # NOTE: avoid midnight notification
        if self.should_batch_execute(['09:30', '17:30']):
            logger.info('start fetch salmon run stage info.')
            api_client = Splatoon3ApiClient()
            stages = await api_client.fetch_salmon_run_stages()
            logger.info('start create salmon run stage image.')
            image_creator = SalmonRunStageImageCreator()
            image = await image_creator.run(stages)
            logger.info(f'created image: {image}')

            if image is not None:
                await self.bot_channel.send(file=discord.File(image))
                os.remove(image)

            logger.info('finish send salmon run stage image.')

    @tasks.loop(seconds=60)
    async def batch_detect_inactive_members(self):
        if self.should_batch_execute(['09:34', '12:00', '21:00']):
            duration = 7
            detector = InactiveMembersDetector(self.guild)
            inactive_members = await detector.detect(days=duration)
            logger.info(f'{duration}日以上ログインしていないメンバー数: {inactive_members}')
            if inactive_members is not None and inactive_members > 0:
                await self.bot_channel.send(f'{duration}日以上ログインしていないメンバー数: {inactive_members}')

    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel:
            logger.info(f'voice state update. {member} {before} {after}')
            if before.channel is None:
                logger.info(f'{member.name} が {after.channel.name} に参加しました。')
                log.on_join(member.name, after.channel.name)
            elif after.channel is None:
                logger.info(f'{member.name} が {before.channel.name} から退出しました。')
                log.on_leave(member.name, before.channel.name)
                if len(before.channel.members) == 0:
                    await before.channel.edit(user_limit=0)
                    logger.info(f'{before.channel.name} に誰もいなくなったので人数制限を解除しました。')
                    log.on_leave('all', before.channel.name)

    @staticmethod
    def should_batch_execute(target_times):
        current_time = dt.now().strftime('%H:%M')
        for t in target_times:
            if current_time == t:
                logger.info(f'start executing batch. current_time: {current_time} target_time: {t}')
                return True
        return False
