import discord
import os

import logging

from bukichi_bot.bukichi_bot import BukichiBotClient
from bukichi_bot.components.inactive_members_detector import InactiveMembersDetector

logger = logging.getLogger('discord')


def main():
    DISCORD_APP_TOKEN = os.getenv('DISCORD_APP_TOKEN')
    ADMIN_ROLE_ID = os.getenv('ADMIN_ROLE_ID')

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guilds = True
    intents.voice_states = True
    intents.guild_messages = True

    client = BukichiBotClient(intents=intents)

    @client.command_tree.command(name='limit', description='VCに人数制限をかけるでし')
    async def limit(interaction: discord.Interaction, value: int):
        if value > 20:
            value = 20

        voice_state = interaction.user.voice

        if voice_state:
            await voice_state.channel.edit(user_limit=value)
            await interaction.response.send_message(f'チャンネルの人数制限を {value} に変更したでし。')
            logger.info(f'{voice_state.channel} limit changed to {value}')
        else:
            await interaction.response.send_message('VCじゃないと使えないでし。')
            logger.info('VCじゃないと使えないでし。')

    @client.command_tree.command(name='inactives', description='指定期間以上ログインしていないメンバーを表示するでし')
    async def inactives(interaction: discord.Interaction, days: int = 30):
        def is_admin(user):
            roles = user.roles
            for r in roles:
                if r.id == int(ADMIN_ROLE_ID):
                    logger.info(f'is_admin: {r.name}')
                    return True
            return False

        name = interaction.user.name
        role = interaction.user.top_role

        logger.info(
            f'未活動メンバーの検出コマンドが実行されました。 name: {name} top role: {role.name} is_admin: {is_admin(interaction.user)} days: {days}')

        is_admin = is_admin(interaction.user)
        if is_admin is False:
            await interaction.response.send_message('管理者権限がないと使えないでし。')
            logger.info('管理者権限がないと使えないでし。')
            return

        guild = interaction.guild
        detector = InactiveMembersDetector(guild)
        inactive_members = await detector.detect(days=days)
        await interaction.response.send_message(f'{days}日以上ログインしていないメンバー数: {inactive_members}')
        logger.info(f'{days}日以上ログインしていないメンバー数: {inactive_members}')

    @client.command_tree.command(name='ping', description='pongを返すでし')
    async def ping(interaction: discord.Interaction):
        await interaction.response.send_message('pong')

    client.run(DISCORD_APP_TOKEN)
