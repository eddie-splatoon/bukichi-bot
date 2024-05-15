import logging
import os

from datetime import datetime as dt
from PIL import Image, ImageDraw, ImageFont

from bukichi_bot.components.stage_image_creator import StageImageCreator

logger = logging.getLogger('discord')


class SalmonRunStageImageCreator(StageImageCreator):

    async def run(self, stages):
        filtered = stages['results']

        logger.info('creating salmon run image...')
        created_img = self.make_stages_image(filtered)

        if created_img is None:
            logger.info('no salmon run image created.')
            return None

        logger.info('saving image...')
        current_time = dt.now().strftime('%Y%m%d%H')
        save_to = f'{current_time}.png'
        created_img.save(save_to)

        return save_to

    @staticmethod
    def to_datetime(t_str):
        return dt.strftime(dt.strptime(t_str, '%Y-%m-%dT%H:%M:%S+09:00'), '%Y/%m/%d %H:%M')

    def append_stage_image(self, background_img, draw, pos_x, pos_y, data):
        delta_y = 20
        text_color = (255, 255, 255)

        is_big_run = data['is_big_run']
        start_at = self.to_datetime(data['start_time'])
        end_at = self.to_datetime(data['end_time'])
        stage = data['stage']
        stage_name = stage['name']
        stage_name_kana = self.PATTERN_KANA.findall(stage_name)[0].replace('いぶし', '').strip()
        boss_name = data['boss']['name'].replace('：', '-')
        weapons = data['weapons']

        # stage name
        draw.text((pos_x + 8, pos_y - 60), stage_name_kana, fill=text_color, font=self.FONT_JAPANESE)
        # term
        draw.text((pos_x + 350, pos_y - 72), f'{start_at}-{end_at}', fill=text_color, font=self.FONT_ENGLISH)
        # boss
        draw.text((pos_x + 1400, pos_y - 60), f'{boss_name}', fill=text_color, font=self.FONT_JAPANESE)

        stage_img = self.download_stage_image(f"{stage_name_kana}.png", stage['image'], 0.76)
        background_img.paste(stage_img, (pos_x, pos_y + delta_y))
        os.remove(f"{stage_name_kana}.png")

        pos_x = 780
        delta_y += 50
        weapon_img_size = 256
        for i, w in enumerate(weapons):
            logger.info(w)
            weapon_name = w['name']
            weapon_img_save_to = f"{weapon_name}.png".replace('/', '_')
            weapon_img = self.download_stage_image(weapon_img_save_to, w['image'], None, weapon_img_size,
                                                   weapon_img_size)
            background_img.paste(weapon_img, (pos_x, pos_y + delta_y))
            os.remove(weapon_img_save_to)
            pos_x += 300

    @staticmethod
    def check_if_schedule_changed(filtered):
        first = filtered[0]
        start_at = dt.strftime(dt.strptime(first['start_time'], '%Y-%m-%dT%H:%M:%S+09:00'), '%Y%m%d_%H%M')

        cache_dir = 'cache/salmonrun'
        cache_file = f'{cache_dir}/{start_at}'

        if os.path.isfile(cache_file):
            return False
        else:
            for f in os.listdir(cache_dir):
                os.remove(os.path.join(cache_dir, f))

        logger.info(f'Salmon Run schedule changed. start_at: {start_at}')
        try:
            with open(cache_file, 'x') as f:
                f.write(start_at)
        except:
            return False

        return True

    def make_stages_image(self, filtered):
        if not self.check_if_schedule_changed(filtered):
            return

        background_img = self.get_background_img(suffix='salmon_run')
        draw = ImageDraw.Draw(background_img)

        pos_x = 100
        pos_y = 0

        logger.info(f'start creating background_img: {background_img}')

        for data in filtered:
            # initial position
            if pos_y == 0:
                pos_y = 200
            else:
                pos_y += 500

            self.append_stage_image(background_img, draw, pos_x, pos_y, data)
            # pos_x += 730

        logger.info(f'created background_img: {background_img}')
        return background_img
