import discord

import logging

logger = logging.getLogger('discord')


class InactiveMembersDetector:
    def __init__(self, guild: discord.Guild):
        self.guild = guild

    async def detect(self, days: int = 30):
        logger.info(f'detecting inactive members...guild: {self.guild.name} days: {days}')
        estimated = await self.guild.estimate_pruned_members(days=days)
        logger.info(f'estimated pruned members: {estimated}')

        return estimated
